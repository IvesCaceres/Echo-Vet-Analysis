"""F4 — Diccionario de valores clínicos (dim_valor_atributo + map_atributo_valor).

Construye el vocabulario canónico de valores clínicos observados en
silver_atributos_hallazgo, aplicando las consolidaciones aprobadas en
la auditoría pre-seed.

Idempotente: cada INSERT usa ON CONFLICT DO NOTHING.

Pasos:
  1. Lee silver_atributos_hallazgo (post-F3) y agrega por (atributo, valor_canonico).
  2. Aplica reglas de consolidación (género morfológico, sinónimos, presencia binaria).
  3. Siembra dim_valor_atributo con (atributo_id, valor_final, es_binario_true, ...).
  4. Siembra map_atributo_valor con (dim_organo_atributo_id, valor_original, valor_final, origen).
  5. Puebla silver_atributos_hallazgo.dim_valor_atributo_id via JOIN.

Consolidaciones (de F4_PRESEED_AUDIT.md):
  GÉNERO_MORFOLOGICO: OVALADO/OVALADA→OVAL, GLOBOSO/GLOBOSA→GLOBOSO, etc.
  SINONIMO: ENGROSADO→AUMENTADO (grosor_pared)
  NORMALIZACION: NO_SE_OBSERVAN→AUSENTE (presencia)
  IDENTIDAD: resto
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .models_silver import (
    dim_atributo,
    dim_organo_atributo,
    dim_valor_atributo,
    map_atributo_valor,
    silver_atributos_hallazgo,
)

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# REGLAS DE CONSOLIDACIÓN (decisiones F4_PRESEED_AUDIT)
# ═══════════════════════════════════════════════════════════════════════════

# (atributo, valor_original) → (valor_final, tipo_regla, confianza)
CONSOLIDATION_RULES: dict[tuple[str, str], tuple[str, str, float]] = {
    # ─── Género morfológico: forma ───
    ("forma", "OVALADO"):   ("OVAL", "GENERO_MORFOLOGICO", 0.95),
    ("forma", "OVALADA"):   ("OVAL", "GENERO_MORFOLOGICO", 0.95),
    ("forma", "GLOBOSO"):   ("GLOBOSO", "IDENTIDAD", 1.0),
    ("forma", "GLOBOSA"):   ("GLOBOSO", "GENERO_MORFOLOGICO", 0.95),
    ("forma", "REDONDEADO"): ("REDONDEADO", "IDENTIDAD", 1.0),
    ("forma", "REDONDEADA"): ("REDONDEADO", "GENERO_MORFOLOGICO", 0.95),

    # ─── Género morfológico: distension ───
    ("distension", "SEMI_DISTENDIDO"): ("SEMI_DISTENDIDO", "IDENTIDAD", 1.0),
    ("distension", "SEMI_DISTENDIDA"): ("SEMI_DISTENDIDO", "GENERO_MORFOLOGICO", 0.95),
    ("distension", "DISTENDIDO"):      ("DISTENDIDO", "IDENTIDAD", 1.0),
    ("distension", "DISTENDIDA"):      ("DISTENDIDO", "GENERO_MORFOLOGICO", 0.95),

    # ─── Sinónimos: grosor_pared ───
    ("grosor_pared", "ENGROSADO"): ("AUMENTADO", "SINONIMO", 0.95),

    # ─── Sinónimos: ecogenicidad (post-fix F3 AUMENTADA_DE→AUMENTADA) ───
    # Ya no aplica porque F3 lo consolidó. Pero mantenemos por si reaparece.

    # ─── Presencia binaria ───
    ("presencia", "NO_SE_OBSERVAN"): ("AUSENTE", "NORMALIZACION", 0.95),
    ("presencia", "PRESENTE"):       ("PRESENTE", "IDENTIDAD", 1.0),
}


def consolidar(valor_original: str, atributo: str) -> tuple[str, str, float]:
    """Devuelve (valor_final, tipo_regla, confianza).

    Si no hay regla explícita, retorna (valor_original, "IDENTIDAD", 1.0).
    """
    rule = CONSOLIDATION_RULES.get((atributo, valor_original))
    if rule:
        return rule
    return (valor_original, "IDENTIDAD", 1.0)


# Valores binarios cuyo estado TRUE se modela así (para `es_binario_true`)
_BINARY_TRUE_VALUES: set[str] = {
    "PRESENTE", "SI", "SI_COMPROMISO", "CON_COMPROMISO",
    "NORMAL", "CONSERVADO", "PRESERVADO", "REACTIVO",
    "ABUNDANTE", "MODERADO", "AUSENTE",  # AUSENTE=True para presencia binaria
}


def _upsert_ignore(table, rows, engine, index_elements):
    """INSERT ... ON CONFLICT DO NOTHING portable (SQLite + Postgres)."""
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    if not rows:
        return 0

    insert_fn = sqlite_insert if engine.dialect.name == "sqlite" else pg_insert
    stmt = insert_fn(table).values(rows)
    stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)

    with engine.begin() as conn:
        result = conn.execute(stmt)
        return result.rowcount or 0


# ═══════════════════════════════════════════════════════════════════════════
# SEED DIM_VALOR_ATRIBUTO
# ═══════════════════════════════════════════════════════════════════════════

def seed_dim_valor_atributo(engine: Engine) -> dict:
    """Siembra dim_valor_atributo con valores finales (post-consolidación).

    Estrategia: leer silver_atributos_hallazgo agregado por (atributo, valor_canonico),
    consolidar y agrupar por atributo. Para cada valor final único en el atributo,
    crear/actualizar fila en dim_valor_atributo.

    Returns: { "n_dim_valor": int, "n_atributos": int, "n_huérfanos": int }
    """
    # 1. Leer valores observados
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT
                a.id AS atributo_id,
                a.nombre_canonico AS atributo,
                doa.tipo_dato,
                sah.valor_canonico AS valor_original,
                COUNT(*) AS freq
            FROM silver_atributos_hallazgo sah
            JOIN dim_organo_atributo doa ON sah.dim_organo_atributo_id = doa.id
            JOIN dim_atributo a ON doa.dim_atributo_id = a.id
            WHERE sah.valor_canonico IS NOT NULL
            GROUP BY a.id, a.nombre_canonico, doa.tipo_dato, sah.valor_canonico
        """)).all()

    # 2. Consolidar + agregar
    final_freq: dict[tuple[int, str], int] = defaultdict(int)
    final_tipo_dato: dict[int, str] = {}
    for atributo_id, atributo, tipo_dato, valor_orig, freq in rows:
        final_tipo_dato[atributo_id] = tipo_dato
        valor_final, _, _ = consolidar(valor_orig, atributo)
        final_freq[(atributo_id, valor_final)] += freq

    # 3. Construir filas
    dim_rows = []
    for (atributo_id, valor), freq in final_freq.items():
        es_binario_true = valor.upper() in _BINARY_TRUE_VALUES
        es_default = valor.upper() == "NORMAL"
        dim_rows.append({
            "atributo_id": atributo_id,
            "valor": valor,
            "sinonimos": None,
            "patron_extraccion": None,
            "es_binario_true": bool(es_binario_true),
            "es_default": bool(es_default),
            "orden": 0,  # recalcular después
            "activo": True,
        })

    # 4. Ordenar (rank por freq dentro del atributo)
    by_attr: dict[int, list[dict]] = defaultdict(list)
    for r in dim_rows:
        by_attr[r["atributo_id"]].append(r)
    ordered_rows = []
    for atributo_id, group in by_attr.items():
        # Sort by freq (desc)
        group.sort(key=lambda r: -final_freq[(r["atributo_id"], r["valor"])])
        for orden, r in enumerate(group, 1):
            r["orden"] = orden
            ordered_rows.append(r)

    # 5. UPSERT
    n_inserted = _upsert_ignore(
        dim_valor_atributo, ordered_rows, engine,
        index_elements=["atributo_id", "valor"],
    )

    # 6. Verificar cobertura: ¿algún valor_canonico de silver quedó sin FK?
    with engine.begin() as conn:
        orphans = conn.execute(text("""
            SELECT COUNT(*)
            FROM silver_atributos_hallazgo sah
            JOIN dim_organo_atributo doa ON sah.dim_organo_atributo_id = doa.id
            JOIN dim_atributo a ON doa.dim_atributo_id = a.id
            LEFT JOIN dim_valor_atributo dva
              ON dva.atributo_id = a.id
              AND dva.valor = sah.valor_canonico
            WHERE sah.valor_canonico IS NOT NULL
              AND dva.id IS NULL
        """)).scalar()

    return {
        "n_dim_valor": n_inserted,
        "n_atributos": len(by_attr),
        "n_observaciones_unicas": sum(final_freq.values()),
        "n_huérfanos": orphans,
    }


# ═══════════════════════════════════════════════════════════════════════════
# SEED MAP_ATRIBUTO_VALOR
# ═══════════════════════════════════════════════════════════════════════════

def seed_map_atributo_valor(engine: Engine) -> dict:
    """Siembra map_atributo_valor por par (dim_organo_atributo, valor_original).

    Returns: { "n_map": int, "n_pairs": int }
    """
    # 1. Leer todas las combinaciones observadas
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT
                doa.id AS dim_organo_atributo_id,
                doa.dim_organo_id,
                doa.dim_atributo_id,
                doa.dim_segmento_id,
                o.nombre_canonico AS organo,
                a.nombre_canonico AS atributo,
                sah.valor_canonico AS valor_original,
                COUNT(*) AS freq
            FROM silver_atributos_hallazgo sah
            JOIN dim_organo_atributo doa ON sah.dim_organo_atributo_id = doa.id
            JOIN dim_organo o ON doa.dim_organo_id = o.id
            JOIN dim_atributo a ON doa.dim_atributo_id = a.id
            WHERE sah.valor_canonico IS NOT NULL
            GROUP BY doa.id, doa.dim_organo_id, doa.dim_atributo_id,
                     doa.dim_segmento_id, o.nombre_canonico,
                     a.nombre_canonico, sah.valor_canonico
        """)).all()

    # 2. Aplicar consolidación y construir filas
    map_rows = []
    pair_counter: set[tuple[int, str]] = set()
    for (doa_id, d_org_id, d_attr_id, d_seg_id, organo, atributo,
         valor_orig, freq) in rows:
        valor_final, tipo_regla, confianza = consolidar(valor_orig, atributo)
        map_rows.append({
            "dim_organo_atributo_id": doa_id,
            "valor_original": valor_orig,
            "valor_canonico": valor_final,
            "orden": 0,
            "origen": tipo_regla,
        })
        pair_counter.add((doa_id, valor_orig))

    # 3. Asignar orden (rank por freq dentro del par)
    by_pair: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for r in map_rows:
        by_pair[(r["dim_organo_atributo_id"], r["valor_original"])].append(r)

    ordered = []
    for (pair_id, val_orig), group in by_pair.items():
        # No reorder needed here (each pair has only 1 row per valor_original)
        for r in group:
            ordered.append(r)

    # 4. UPSERT
    n_inserted = _upsert_ignore(
        map_atributo_valor, ordered, engine,
        index_elements=["dim_organo_atributo_id", "valor_original"],
    )

    return {
        "n_map": n_inserted,
        "n_pairs_unicos": len(pair_counter),
        "n_observaciones": sum(r[-1] for r in rows),  # r[-1] = freq column
    }


# ═══════════════════════════════════════════════════════════════════════════
# APLICAR CONSOLIDACIÓN A silver.valor_canonico
# ═══════════════════════════════════════════════════════════════════════════

def apply_consolidation_to_silver(engine: Engine) -> dict:
    """Aplica consolidar() a silver_atributos_hallazgo.valor_canonico.

    Lee cada fila con valor_canonico NOT NULL, resuelve el atributo vía
    dim_organo_atributo + dim_atributo, aplica consolidar() en Python y
    hace UPDATE masivo del valor canónico al consolidado.

    Sólo actualiza filas donde el valor consolidado difiere del actual
    (idempotencia: la 2da ejecución es no-op).

    Returns: { "n_total": int, "n_changed": int, "by_rule": dict }
    """
    # 1. Leer pares (id, atributo, valor_canonico)
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT sah.id, a.nombre_canonico AS atributo, sah.valor_canonico
            FROM silver_atributos_hallazgo sah
            JOIN dim_organo_atributo doa ON doa.id = sah.dim_organo_atributo_id
            JOIN dim_atributo a ON a.id = doa.dim_atributo_id
            WHERE sah.valor_canonico IS NOT NULL
        """)).all()

    # 2. Calcular consolidado en memoria
    updates: list[tuple[int, str, str]] = []  # (id, new_canonico, regla)
    by_rule: dict[str, int] = defaultdict(int)
    for row_id, atributo, valor_actual in rows:
        valor_consolidado, tipo_regla, _conf = consolidar(valor_actual, atributo)
        if valor_consolidado != valor_actual:
            updates.append((row_id, valor_consolidado, tipo_regla))
            by_rule[tipo_regla] += 1

    # 3. UPDATE masivo (sólo si hay cambios)
    n_changed = 0
    if updates:
        dialect = "sqlite" if engine.dialect.name == "sqlite" else "postgresql"
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        insert_fn = sqlite_insert if dialect == "sqlite" else pg_insert

        # Usamos el modelo para construir la UPDATE idempotente:
        # leer silver_atributos_hallazgo y hacer updates por id.
        with engine.begin() as conn:
            for row_id, new_canonico, _regla in updates:
                result = conn.execute(
                    silver_atributos_hallazgo.update()
                    .where(silver_atributos_hallazgo.c.id == row_id)
                    .values(valor_canonico=new_canonico)
                )
                n_changed += result.rowcount or 0

    return {
        "n_total": len(rows),
        "n_changed": n_changed,
        "n_unchanged": len(rows) - n_changed,
        "by_rule": dict(by_rule),
    }


# ═══════════════════════════════════════════════════════════════════════════
# POBLAR FK silver_atributos_hallazgo.dim_valor_atributo_id
# ═══════════════════════════════════════════════════════════════════════════

def populate_fk_dim_valor(engine: Engine) -> dict:
    """Puebla silver_atributos_hallazgo.dim_valor_atributo_id vía JOIN.

    Asume que apply_consolidation_to_silver() ya corrió: silver.valor_canonico
    está en forma consolidada (OVAL, AUMENTADO, AUSENTE, DISTENDIDO, etc.).
    Para cada fila:
      1. Resuelve (atributo_id, valor_canonico) → dim_valor_atributo.id
      2. UPDATE la fila con ese id.

    Importante: NO filtra por `dim_valor_atributo_id IS NULL` para permitir
    re-asignación cuando silver.valor_canonico cambió (post-consolidation).
    La 2da ejecución es no-op efectivo porque el JOIN resuelve al mismo id.

    Returns: { "n_poblados": int, "n_huérfanos": int, "n_filas": int }
    """
    # 1. Contar total y huérfanos pre-update
    with engine.begin() as conn:
        n_total = conn.execute(text(
            "SELECT COUNT(*) FROM silver_atributos_hallazgo "
            "WHERE valor_canonico IS NOT NULL"
        )).scalar()

        n_orphan_pre = conn.execute(text("""
            SELECT COUNT(*)
            FROM silver_atributos_hallazgo sah
            JOIN dim_organo_atributo doa ON sah.dim_organo_atributo_id = doa.id
            LEFT JOIN dim_valor_atributo dva
              ON dva.atributo_id = doa.dim_atributo_id
              AND dva.valor = sah.valor_canonico
            WHERE sah.valor_canonico IS NOT NULL
              AND dva.id IS NULL
        """)).scalar()

        # 2. UPDATE masivo — sobre TODAS las filas con valor_canonico (no
        #    sólo las NULL), para re-asignar FKs que quedaron obsoletas tras
        #    apply_consolidation_to_silver().
        result = conn.execute(text("""
            UPDATE silver_atributos_hallazgo
            SET dim_valor_atributo_id = (
                SELECT dva.id
                FROM dim_organo_atributo doa
                JOIN dim_valor_atributo dva
                  ON dva.atributo_id = doa.dim_atributo_id
                 AND dva.valor = silver_atributos_hallazgo.valor_canonico
                WHERE doa.id = silver_atributos_hallazgo.dim_organo_atributo_id
                LIMIT 1
            )
            WHERE valor_canonico IS NOT NULL
        """))
        n_updated = result.rowcount or 0

        # 3. Contar huérfanos post-update
        n_orphan_post = conn.execute(text("""
            SELECT COUNT(*)
            FROM silver_atributos_hallazgo
            WHERE valor_canonico IS NOT NULL
              AND dim_valor_atributo_id IS NULL
        """)).scalar()

    return {
        "n_filas_con_valor": n_total,
        "n_poblados": n_updated,
        "n_huérfanos_pre": n_orphan_pre,
        "n_huérfanos_post": n_orphan_post,
    }


# ═══════════════════════════════════════════════════════════════════════════
# API PÚBLICA
# ═══════════════════════════════════════════════════════════════════════════

def build_f4(engine: Engine) -> dict:
    """Ejecuta F4 completo. Idempotente.

    Pasos:
      1. seed_dim_valor_atributo — UPSERT de valores finales consolidados.
      2. seed_map_atributo_valor — UPSERT de mappings (doa_id, original → canon).
      3. apply_consolidation_to_silver — UPDATE silver.valor_canonico a forma
         consolidada (OVALADO→OVAL, GLOBOSA→GLOBOSO, etc.).
      4. populate_fk_dim_valor — UPDATE silver.dim_valor_atributo_id vía JOIN.
    """
    metrics = {}
    log.info("[f4] seeding dim_valor_atributo...")
    metrics["dim_valor_atributo"] = seed_dim_valor_atributo(engine)
    log.info("[f4] seeding map_atributo_valor...")
    metrics["map_atributo_valor"] = seed_map_atributo_valor(engine)
    log.info("[f4] applying consolidation to silver.valor_canonico...")
    metrics["consolidation"] = apply_consolidation_to_silver(engine)
    log.info("[f4] populating FK silver_atributos_hallazgo.dim_valor_atributo_id...")
    metrics["fk"] = populate_fk_dim_valor(engine)
    return metrics
