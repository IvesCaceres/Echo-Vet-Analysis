"""Bootstrap del modelo F3 (atributos clínicos).

Siembra:
- dim_atributo: 31 atributos canónicos (sin órgano)
- dim_organo_atributo: 62 pares (organo_id, atributo_id) con tipo_dato y cobertura
- dim_segmento_anatomico: 6 segmentos (duodeno_yeyuno, colon, rinon_izq/der, adrenal_izq/der)
- dim_valor_atributo: 172 valores canónicos deduplicados (atributo_id, valor)

Idempotente: cada INSERT usa ON CONFLICT DO NOTHING sobre columnas UNIQUE.
Las definiciones de pares y segmentos vienen de
docs/F3_1_CLINICAL_ATTRIBUTE_MODEL_FINAL.md.

Los valores canónicos y regex se importan desde el script de profiling para
mantener una única fuente de verdad.
"""
from __future__ import annotations

import logging
from typing import Iterable

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine

from .models_silver import (
    dim_atributo,
    dim_organo_atributo,
    dim_organo,
    dim_segmento_anatomico,
    dim_valor_atributo,
)

log = logging.getLogger(__name__)


# =============================================================================
# ATRIBUTOS CANÓNICOS (31)
# =============================================================================
# Tabla maestra de atributos clínicos. Independiente del órgano. La unión
# atributo+órgano vive en dim_organo_atributo.
#
# tipo_dato ∈ {"texto", "numerico", "binario"}
# - texto: cualquier valor canónico del catálogo (ej: Vejiga.replecion)
# - numerico: se almacena en valor_numerico (ej: Gestación.fetos)
# - binario: se modela como texto con dos valores TRUE/FALSE

_ATRIBUTOS_SEED: list[dict] = [
    # Vejiga
    {"nombre_canonico": "replecion",                   "descripcion_clinica": "Estado de llenado vesical (plejora/distensión/depleción)"},
    {"nombre_canonico": "contenido",                   "descripcion_clinica": "Tipo de contenido vesical (anecoico, hiperecogénico, etc.)"},
    {"nombre_canonico": "homogeneidad_contenido",      "descripcion_clinica": "Homogeneidad del contenido"},
    {"nombre_canonico": "bordes_internos",             "descripcion_clinica": "Regularidad de los bordes internos de la pared"},
    {"nombre_canonico": "grosor_pared",                "descripcion_clinica": "Grosor de la pared vesical (normal/engrosado/etc.)"},
    # Próstata
    {"nombre_canonico": "forma",                       "descripcion_clinica": "Forma prostática"},
    {"nombre_canonico": "lobulacion",                  "descripcion_clinica": "Lobulación prostática"},
    {"nombre_canonico": "tamano",                      "descripcion_clinica": "Tamaño prostático"},
    {"nombre_canonico": "ecogenicidad",                "descripcion_clinica": "Ecogenicidad del parénquima"},
    {"nombre_canonico": "homogeneidad",                "descripcion_clinica": "Homogeneidad del parénquima"},
    # Riñones
    {"nombre_canonico": "bordes",                      "descripcion_clinica": "Bordes renales (lisos/irregulares/etc.)"},
    {"nombre_canonico": "diferenciacion_corticomedular","descripcion_clinica": "Definición de la diferenciación córtico-medular"},
    {"nombre_canonico": "relacion_corticomedular",     "descripcion_clinica": "Relación córtico-medular (adecuada/aumentada/etc.)"},
    {"nombre_canonico": "compromiso_pelvico",          "descripcion_clinica": "Compromiso de la pelvis renal"},
    # Bazo
    {"nombre_canonico": "margenes",                    "descripcion_clinica": "Márgenes esplénicos"},
    {"nombre_canonico": "arquitectura",                "descripcion_clinica": "Arquitectura general del órgano"},
    # Estómago
    {"nombre_canonico": "distension",                  "descripcion_clinica": "Estado de distensión gástrica"},
    {"nombre_canonico": "estratificacion_pared",       "descripcion_clinica": "Estratificación de la pared gástrica"},
    # Hígado
    {"nombre_canonico": "granulado",                   "descripcion_clinica": "Granulado hepático"},
    {"nombre_canonico": "patron_vascular",             "descripcion_clinica": "Patrón vascular hepático"},
    # Vesícula
    {"nombre_canonico": "paredes",                     "descripcion_clinica": "Paredes (intestinal, vesical, gástrica según contexto)"},
    # Páncreas
    {"nombre_canonico": "preservacion",                "descripcion_clinica": "Preservación del parénquima pancreático"},
    {"nombre_canonico": "aspecto_peripancreatico",     "descripcion_clinica": "Aspecto del tejido peripancreático"},
    # Adrenales
    {"nombre_canonico": "tamanho",                     "descripcion_clinica": "Tamaño del órgano"},
    # Linfonodos
    {"nombre_canonico": "presencia",                   "descripcion_clinica": "Presencia/ausencia de linfonodos"},
    {"nombre_canonico": "compromiso",                  "descripcion_clinica": "Compromiso patológico de los linfonodos"},
    # Cavidad abdominal
    {"nombre_canonico": "liquido_libre",               "descripcion_clinica": "Presencia de líquido libre abdominal"},
    {"nombre_canonico": "masas",                       "descripcion_clinica": "Presencia de masas abdominales"},
    # Intestino (peristaltismo)
    {"nombre_canonico": "peristaltismo",               "descripcion_clinica": "Peristaltismo intestinal"},
    # Gestación
    {"nombre_canonico": "fetos",                       "descripcion_clinica": "Número de fetos visibles"},
]


# =============================================================================
# PARES (ORGANO, ATRIBUTO) — 62 totales
# =============================================================================
# Tuplas (organo_canonico, atributo_canonico, tipo_dato_efectivo, segmento_codigo_opcional)
# segmento_codigo opcional: si el atributo aplica a un segmento anatómico
# específico (ej: Intestino.contenido → duodeno_yeyuno vs colon).

_PARES_SEED: list[dict] = [
    # Vejiga (5)
    {"organo": "Vejiga",   "atributo": "replecion",                "segmento": None},
    {"organo": "Vejiga",   "atributo": "contenido",                "segmento": None},
    {"organo": "Vejiga",   "atributo": "homogeneidad_contenido",   "segmento": None},
    {"organo": "Vejiga",   "atributo": "bordes_internos",          "segmento": None},
    {"organo": "Vejiga",   "atributo": "grosor_pared",             "segmento": None},
    # Próstata (5)
    {"organo": "Próstata", "atributo": "forma",                    "segmento": None},
    {"organo": "Próstata", "atributo": "lobulacion",               "segmento": None},
    {"organo": "Próstata", "atributo": "tamano",                   "segmento": None},
    {"organo": "Próstata", "atributo": "ecogenicidad",             "segmento": None},
    {"organo": "Próstata", "atributo": "homogeneidad",             "segmento": None},
    # Riñones (8) — segmentación por lateralidad
    {"organo": "Riñones",  "atributo": "forma",                    "segmento": "rinon_derecho"},
    {"organo": "Riñones",  "atributo": "forma",                    "segmento": "rinon_izquierdo"},
    {"organo": "Riñones",  "atributo": "tamano",                   "segmento": "rinon_derecho"},
    {"organo": "Riñones",  "atributo": "tamano",                   "segmento": "rinon_izquierdo"},
    {"organo": "Riñones",  "atributo": "bordes",                   "segmento": "rinon_derecho"},
    {"organo": "Riñones",  "atributo": "bordes",                   "segmento": "rinon_izquierdo"},
    {"organo": "Riñones",  "atributo": "ecogenicidad",             "segmento": "rinon_derecho"},
    {"organo": "Riñones",  "atributo": "ecogenicidad",             "segmento": "rinon_izquierdo"},
    {"organo": "Riñones",  "atributo": "diferenciacion_corticomedular","segmento": "rinon_derecho"},
    {"organo": "Riñones",  "atributo": "diferenciacion_corticomedular","segmento": "rinon_izquierdo"},
    {"organo": "Riñones",  "atributo": "relacion_corticomedular",  "segmento": "rinon_derecho"},
    {"organo": "Riñones",  "atributo": "relacion_corticomedular",  "segmento": "rinon_izquierdo"},
    {"organo": "Riñones",  "atributo": "compromiso_pelvico",       "segmento": "rinon_derecho"},
    {"organo": "Riñones",  "atributo": "compromiso_pelvico",       "segmento": "rinon_izquierdo"},
    # Bazo (4)
    {"organo": "Bazo",     "atributo": "tamano",                   "segmento": None},
    {"organo": "Bazo",     "atributo": "forma",                    "segmento": None},
    {"organo": "Bazo",     "atributo": "margenes",                 "segmento": None},
    {"organo": "Bazo",     "atributo": "arquitectura",             "segmento": None},
    # Estómago (4)
    {"organo": "Estómago", "atributo": "distension",               "segmento": None},
    {"organo": "Estómago", "atributo": "contenido",                "segmento": None},
    {"organo": "Estómago", "atributo": "estratificacion_pared",    "segmento": None},
    {"organo": "Estómago", "atributo": "grosor_pared",             "segmento": None},
    # Hígado (7)
    {"organo": "Hígado",   "atributo": "tamano",                   "segmento": None},
    {"organo": "Hígado",   "atributo": "margenes",                 "segmento": None},
    {"organo": "Hígado",   "atributo": "bordes",                   "segmento": None},
    {"organo": "Hígado",   "atributo": "ecogenicidad",             "segmento": None},
    {"organo": "Hígado",   "atributo": "granulado",                "segmento": None},
    {"organo": "Hígado",   "atributo": "arquitectura",             "segmento": None},
    {"organo": "Hígado",   "atributo": "patron_vascular",          "segmento": None},
    # Vesícula (4)
    {"organo": "Vesícula", "atributo": "distension",               "segmento": None},
    {"organo": "Vesícula", "atributo": "contenido",                "segmento": None},
    {"organo": "Vesícula", "atributo": "bordes_internos",          "segmento": None},
    {"organo": "Vesícula", "atributo": "grosor_pared",             "segmento": None},
    # Intestino duodeno-yeyuno (3)
    {"organo": "Intestino", "atributo": "contenido",               "segmento": "duodeno_yeyuno"},
    {"organo": "Intestino", "atributo": "grosor_pared",            "segmento": "duodeno_yeyuno"},
    {"organo": "Intestino", "atributo": "estratificacion_pared",   "segmento": "duodeno_yeyuno"},
    # Intestino colon (2)
    {"organo": "Intestino", "atributo": "contenido",               "segmento": "colon"},
    {"organo": "Intestino", "atributo": "paredes",                 "segmento": "colon"},
    # Intestino peristaltismo (1) — sin segmento
    {"organo": "Intestino", "atributo": "peristaltismo",           "segmento": None},
    # Páncreas (2)
    {"organo": "Páncreas",  "atributo": "preservacion",             "segmento": None},
    {"organo": "Páncreas",  "atributo": "aspecto_peripancreatico",  "segmento": None},
    # Adrenales (6) — segmentación por lateralidad
    {"organo": "Adrenales", "atributo": "forma",                   "segmento": "adrenal_derecha"},
    {"organo": "Adrenales", "atributo": "forma",                   "segmento": "adrenal_izquierda"},
    {"organo": "Adrenales", "atributo": "tamanho",                 "segmento": "adrenal_derecha"},
    {"organo": "Adrenales", "atributo": "tamanho",                 "segmento": "adrenal_izquierda"},
    {"organo": "Adrenales", "atributo": "arquitectura",            "segmento": "adrenal_derecha"},
    {"organo": "Adrenales", "atributo": "arquitectura",            "segmento": "adrenal_izquierda"},
    # Linfonodos (2)
    {"organo": "Linfonodos","atributo": "presencia",               "segmento": None},
    {"organo": "Linfonodos","atributo": "compromiso",              "segmento": None},
    # Útero (3)
    {"organo": "Útero",     "atributo": "tamano",                  "segmento": None},
    {"organo": "Útero",     "atributo": "contenido",               "segmento": None},
    {"organo": "Útero",     "atributo": "grosor_pared",            "segmento": None},
    # Ovarios (2)
    {"organo": "Ovarios",   "atributo": "tamano",                  "segmento": None},
    {"organo": "Ovarios",   "atributo": "forma",                   "segmento": None},
    # Testículos (4)
    {"organo": "Testículos","atributo": "tamano",                  "segmento": None},
    {"organo": "Testículos","atributo": "forma",                   "segmento": None},
    {"organo": "Testículos","atributo": "ecogenicidad",            "segmento": None},
    {"organo": "Testículos","atributo": "homogeneidad",            "segmento": None},
    # Gestación (1)
    {"organo": "Gestación", "atributo": "fetos",                   "segmento": None},
    # Cavidad abdominal (2)
    {"organo": "Cavidad abdominal", "atributo": "liquido_libre",   "segmento": None},
    {"organo": "Cavidad abdominal", "atributo": "masas",           "segmento": None},
]


# =============================================================================
# SEGMENTOS ANATÓMICOS (6)
# =============================================================================
# Codifica la dimensión anatómica para Riñones (izq/der), Adrenales (izq/der)
# e Intestino (duodeno_yeyuno/colon).

_SEGMENTOS_SEED: list[dict] = [
    {"organo": "Riñones",   "codigo": "rinon_derecho",     "nombre_canonico": "Riñón derecho",     "orden": 1},
    {"organo": "Riñones",   "codigo": "rinon_izquierdo",   "nombre_canonico": "Riñón izquierdo",   "orden": 2},
    {"organo": "Adrenales", "codigo": "adrenal_derecha",   "nombre_canonico": "Adrenal derecha",   "orden": 1},
    {"organo": "Adrenales", "codigo": "adrenal_izquierda", "nombre_canonico": "Adrenal izquierda", "orden": 2},
    {"organo": "Intestino", "codigo": "duodeno_yeyuno",    "nombre_canonico": "Duodeno yeyuno",    "orden": 1},
    {"organo": "Intestino", "codigo": "colon",             "nombre_canonico": "Colon",             "orden": 2},
]


# =============================================================================
# TIPO DE DATO POR ATRIBUTO
# =============================================================================
# Atributos cuyo dominio es binario o numérico. El resto son "texto"
# (catálogo de valores canónicos). Mantenido en sincronía con
# scripts/_profile_f3_dim_valores.py: BINARY_ATRIBUTOS + NUMERIC_ATRIBUTOS.

_BINARY_ATRIBUTOS: set[str] = {
    "presencia",
    "compromiso",
    "preservacion",
    "aspecto_peripancreatico",
    "liquido_libre",
    "masas",
}

_NUMERIC_ATRIBUTOS: set[str] = {
    "fetos",
}


def _tipo_dato_de(atributo_canonico: str) -> str:
    if atributo_canonico in _BINARY_ATRIBUTOS:
        return "binario"
    if atributo_canonico in _NUMERIC_ATRIBUTOS:
        return "numerico"
    return "texto"


# =============================================================================
# HELPERS
# =============================================================================

def _upsert_ignore(table, rows: Iterable[dict], engine: Engine, *, index_elements: list[str]) -> int:
    """Portable INSERT ... ON CONFLICT DO NOTHING.

    Para tablas cuya UNIQUE incluye columnas NULL (ej: dim_segmento_id en
    dim_organo_atributo), SQLite/Postgres tratan NULL != NULL y no se
    dedupica con ON CONFLICT (col1, col2, col3) directamente. Pasá
    conflict_target_sql para usar la forma con COALESCE.
    """
    rows = list(rows)
    if not rows:
        return 0
    dialect = "sqlite" if engine.dialect.name == "sqlite" else "postgresql"
    insert_fn = sqlite_insert if dialect == "sqlite" else pg_insert
    stmt = insert_fn(table).values(rows)
    stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)
    with engine.begin() as conn:
        result = conn.execute(stmt)
    return result.rowcount or 0


def _upsert_ignore_coalesce(
    table, rows: Iterable[dict], engine: Engine, *,
    conflict_columns: list[str],
    null_sentinels: dict[str, int] | None = None,
) -> int:
    """INSERT ... ON CONFLICT DO NOTHING con COALESCE en columnas NULL-able.

    Útil cuando la clave natural incluye columnas NULL que deben tratarse como
    "ausencia" (ej: dim_segmento_id IS NULL). El UNIQUE INDEX efectivo es:
        UNIQUE(col1, col2, COALESCE(col3, -1))
    y se referencia con ON CONFLICT (col1, col2, COALESCE(col3, -1)).

    Soporta SQLite (>=3.24) y PostgreSQL.
    """
    rows = list(rows)
    if not rows:
        return 0
    null_sentinels = null_sentinels or {}

    # Armar lista de columnas para ON CONFLICT. Las NULL-ables se envuelven
    # en COALESCE(col, sentinel).
    conflict_exprs: list[str] = []
    for col in conflict_columns:
        if col in null_sentinels:
            conflict_exprs.append(f"COALESCE({col}, {null_sentinels[col]})")
        else:
            conflict_exprs.append(col)
    conflict_target_sql = ", ".join(conflict_exprs)

    # Para que la PK siga funcionando, las columnas van sin COALESCE en VALUES.
    # SQLAlchemy sqlite_insert / pg_insert soportan `.on_conflict_do_nothing`
    # sin index_elements, pero NO con COALESCE crudo. Solución: ejecutar SQL
    # crudo con text() que use el nombre de tabla y las columnas presentes
    # en las filas (excluye PK autoincrement y server_default).
    table_name = table.name

    # Determinar columnas a partir de la primera fila (todas deben tener las
    # mismas keys). Excluimos id (autoincrement) y created_at (server_default).
    sample = rows[0]
    skip_cols = {"id", "created_at", "silver_built_at"}
    columns = [c for c in sample.keys() if c not in skip_cols]
    placeholders = ", ".join(f":{c}" for c in columns)
    col_list = ", ".join(columns)
    sql = (
        f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders}) "
        f"ON CONFLICT ({conflict_target_sql}) DO NOTHING"
    )

    from sqlalchemy import text
    total = 0
    with engine.begin() as conn:
        for row in rows:
            params = {c: row.get(c) for c in columns}
            result = conn.execute(text(sql), params)
            total += result.rowcount or 0
    return total


# =============================================================================
# API PÚBLICA
# =============================================================================

def bootstrap_f3(engine: Engine) -> dict[str, int]:
    """Siembra las dimensiones F3 (atributos, pares, segmentos).

    Idempotente. Asume bootstrap_basico() ya corrió (dim_organo poblado).
    Devuelve dict con conteos de filas insertadas por tabla.
    """
    counts: dict[str, int] = {}

    # 1. dim_atributo (31 filas)
    counts["dim_atributo"] = _upsert_ignore(
        dim_atributo, _ATRIBUTOS_SEED, engine, index_elements=["nombre_canonico"]
    )

    # 2. dim_segmento_anatomico (6 filas)
    # Necesita resolver organo_id por nombre. Idempotente.
    with engine.begin() as conn:
        organo_id_map = {
            nombre: id_
            for id_, nombre in conn.execute(
                dim_organo.select().with_only_columns(
                    dim_organo.c.id, dim_organo.c.nombre_canonico
                )
            ).all()
        }
    seg_rows = [
        {
            "dim_organo_id": organo_id_map[s["organo"]],
            "codigo": s["codigo"],
            "nombre_canonico": s["nombre_canonico"],
            "orden": s["orden"],
        }
        for s in _SEGMENTOS_SEED
    ]
    counts["dim_segmento_anatomico"] = _upsert_ignore(
        dim_segmento_anatomico, seg_rows, engine,
        index_elements=["dim_organo_id", "codigo"],
    )

    # 3. dim_organo_atributo (62 filas)
    # Necesita IDs de dim_organo, dim_atributo y dim_segmento_anatomico.
    with engine.begin() as conn:
        organo_id_map = {
            nombre: id_
            for id_, nombre in conn.execute(
                dim_organo.select().with_only_columns(
                    dim_organo.c.id, dim_organo.c.nombre_canonico
                )
            ).all()
        }
        atributo_id_map = {
            nombre: id_
            for id_, nombre in conn.execute(
                dim_atributo.select().with_only_columns(
                    dim_atributo.c.id, dim_atributo.c.nombre_canonico
                )
            ).all()
        }
        seg_id_map = {
            (org, cod): id_
            for id_, org, cod in conn.execute(
                dim_segmento_anatomico.select().with_only_columns(
                    dim_segmento_anatomico.c.id,
                    dim_segmento_anatomico.c.dim_organo_id,
                    dim_segmento_anatomico.c.codigo,
                )
            ).all()
        }
        org_id_to_name = {v: k for k, v in organo_id_map.items()}

    par_rows: list[dict] = []
    par_seen: set[tuple[int, int, int | None]] = set()
    for par in _PARES_SEED:
        org_id = organo_id_map.get(par["organo"])
        attr_id = atributo_id_map.get(par["atributo"])
        if org_id is None or attr_id is None:
            log.warning("par sin FK resoluble: %s", par)
            continue
        seg_id = None
        if par["segmento"]:
            seg_id = seg_id_map.get((org_id, par["segmento"]))
            if seg_id is None:
                log.warning("segmento sin FK resoluble: %s.%s", par["organo"], par["segmento"])
        key = (org_id, attr_id, seg_id)
        if key in par_seen:
            continue
        par_seen.add(key)
        # tipo_dato del atributo (lookup vía _tipo_dato_de)
        par_rows.append({
            "dim_organo_id": org_id,
            "dim_atributo_id": attr_id,
            "dim_segmento_id": seg_id,
            "tipo_dato": _tipo_dato_de(par["atributo"]),
            "unidad_default": None,
            "valores_canonicos_csv": None,  # poblado por script externo
            "cobertura_corpus_pct": 0.0,    # poblado por profiling
            "n_hallazgos_corpus": 0,        # poblado por profiling
            "orden_visualizacion": 0,
        })

    # Para ON CONFLICT, necesitamos un índice que cubra las 3 columnas con
    # COALESCE en dim_segmento_id (porque SQLite trata NULL como distinto
    # en UNIQUE estándar, lo que permite duplicados no deseados).
    counts["dim_organo_atributo"] = _upsert_ignore_coalesce(
        dim_organo_atributo, par_rows, engine,
        conflict_columns=["dim_organo_id", "dim_atributo_id", "dim_segmento_id"],
        null_sentinels={"dim_segmento_id": -1},
    )

    return counts


# =============================================================================
# dim_valor_atributo (172 valores canónicos deduplicados)
# =============================================================================
# Los datos vienen del script de profiling scripts/_profile_f3_dim_valores.py
# (única fuente de verdad). Lo importamos aquí para sembrar dim_valor_atributo.

def bootstrap_dim_valor_atributo(engine: Engine) -> dict[str, int]:
    """Siembra dim_valor_atributo con los valores canónicos deduplicados.

    Los datos vienen de scripts/_profile_f3_dim_valores.py (VALUE_PROPOSALS).
    Dedup por (atributo_id, valor) — si el mismo (atributo, valor) aparece en
    varios órganos, sólo se inserta UNA vez (modelo global).

    Returns: dict con n_filas_insertadas (no actualizadas).
    """
    import sys
    from pathlib import Path as _P
    _root = _P(__file__).resolve().parent.parent.parent
    _scripts = _root / "scripts"
    if str(_scripts) not in sys.path:
        sys.path.insert(0, str(_scripts))
    # Re-import cached
    if "_f3_catalog" in sys.modules:
        _catalog = sys.modules["_f3_catalog"]
    else:
        # Lazy import to keep import-time cost low.
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_f3_catalog", _scripts / "_profile_f3_dim_valores.py"
        )
        _catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_catalog)  # type: ignore[union-attr]
        sys.modules["_f3_catalog"] = _catalog

    VALUE_PROPOSALS = _catalog.VALUE_PROPOSALS
    BINARY_ATRIBUTOS = _catalog.BINARY_ATRIBUTOS

    # 1. Cargar mapa atributo → id
    with engine.begin() as conn:
        atributo_id_map = {
            nombre: id_
            for id_, nombre in conn.execute(
                dim_atributo.select().with_only_columns(
                    dim_atributo.c.id, dim_atributo.c.nombre_canonico
                )
            ).all()
        }

    # 2. Construir filas deduplicadas
    seen: set[tuple[int, str]] = set()
    rows: list[dict] = []
    for (_organo, atributo), proposals in VALUE_PROPOSALS.items():
        attr_id = atributo_id_map.get(atributo)
        if attr_id is None:
            log.warning("atributo %s sin FK resoluble", atributo)
            continue
        is_bin = f"{_organo}.{atributo}" in BINARY_ATRIBUTOS
        for orden, (canon, pat) in enumerate(proposals):
            key = (attr_id, canon)
            if key in seen:
                continue
            seen.add(key)
            canon_upper = canon.upper()
            es_binario_true = is_bin and canon_upper in {
                "PRESENTE", "SI", "SI_COMPROMISO", "CON_COMPROMISO",
                "NORMAL", "CONSERVADO", "PRESERVADO", "REACTIVO",
                "ABUNDANTE", "MODERADO",
            }
            es_default = canon_upper == "NORMAL"
            rows.append({
                "atributo_id": attr_id,
                "valor": canon,
                "sinonimos": None,
                "patron_extraccion": pat,
                "es_binario_true": bool(es_binario_true),
                "es_default": bool(es_default),
                "orden": orden,
                "activo": True,
            })

    return {
        "dim_valor_atributo": _upsert_ignore(
            dim_valor_atributo, rows, engine,
            index_elements=["atributo_id", "valor"],
        ),
        "n_valores_propuestos": len(rows),
    }
