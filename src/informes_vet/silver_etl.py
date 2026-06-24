"""ETL RAW -> SILVER.

Fase 1 (F1) construye `silver_informes` desde `raw.informes`. El resto de
facts (silver_hallazgos, silver_atributos_hallazgo, silver_conclusion_items)
entra en F3-F5.

Decisiones de implementación F1:

1. **Sin `map_*` formales todavía.** La resolución RAW→dim se hace con lookup
   directo contra las 6 dimensiones base. Esto es intencional: F2 introduce
   los mapas como pieza de normalización explícita, pero F1 ya deja
   `silver_informes` poblado con valores razonables.
2. **Idempotencia por PK.** `silver_informes.informe_id` es PK y mapea 1:1 a
   `raw.informes.id`. Usamos `INSERT ... ON CONFLICT DO NOTHING`. Re-correr
   el ETL no duplica.
3. **Resolución de campos ruidosos.** El campo `genero` de RAW mezcla sexo
   con estado reproductivo (ej. 'Macho entero'). Los separamos en dos
   dimensiones distintas, como manda el diseño.
4. **Parseo de fecha con tolerancia.** Cobertura típica >95%; los casos no
   parseados quedan con `fecha_parseada=NULL, fecha_confianza=0.0`.
5. **Trazabilidad operativa.** Cada ejecución se registra en `silver_etl_runs`.

Fase 2 (F2) puebla las tablas `map_*` y `dim_raza` con reglas
determinísticas; todo lo no resuelto va a `stg_valores_no_mapeados` o
`stg_razas_detectadas`. **No** se reescriben `silver_informes` ya
construidos en F1 — los maps son auditoría de las resoluciones de F1.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine

from .models import hallazgos as raw_hallazgos
from .models import informes as raw_informes
from .models_silver import (
    dim_edad_categoria,
    dim_especie,
    dim_estado_reproductivo,
    dim_estudio,
    dim_sexo,
    silver_etl_runs,
    silver_informes,
)

log = logging.getLogger(__name__)


# =============================================================================
# TABLAS DE LOOKUP (memoizadas durante una ejecución)
# =============================================================================

def _load_dim(engine: Engine, table) -> dict[str, int]:
    """Carga {nombre_canonico: id} para una dimensión."""
    with engine.begin() as conn:
        rows = conn.execute(select(table.c.id, table.c.nombre_canonico)).all()
    return {nombre: id_ for id_, nombre in rows}


# =============================================================================
# PARSERS
# =============================================================================

# Meses en español, con variantes (abreviaturas, typos comunes observados).
_MONTHS_ES: dict[str, int] = {
    "enero": 1, "ene": 1, "en": 1,
    "febrero": 2, "feb": 2,
    "marzo": 3, "mar": 3,
    "abril": 4, "abr": 4,
    "mayo": 5, "may": 5,
    "junio": 6, "jun": 6,
    "julio": 7, "jul": 7,
    "agosto": 8, "ago": 8,
    "septiembre": 9, "setiembre": 9, "sept": 9, "set": 9,
    "septiempre": 9, "septirmbre": 9, "septoembre": 9, "septirmbte": 9,
    "octubre": 10, "oct": 10,
    "noviembre": 11, "nov": 11,
    "diciembre": 12, "dic": 12,
}


def _norm_month(s: str) -> int | None:
    return _MONTHS_ES.get(s.lower().rstrip("."))


# Patrones para fecha. Orden importa: el primer match gana.
_FECHA_PATTERNS: list[tuple[re.Pattern, float]] = [
    # "14 de enero de 2025" / "21 de sept. de 23" / "1 de octubre 2023"
    (re.compile(r"(\d{1,2})\s+de\s+(\w+)\.?\s+de\s+(\d{2,4})", re.I), 1.0),
    # "11-de diciembre de 2023"
    (re.compile(r"(\d{1,2})-de\s+(\w+)\.?\s+de\s+(\d{2,4})", re.I), 0.9),
    # "24 octubre de 2023"
    (re.compile(r"(\d{1,2})\s+(\w+)\.?\s+de\s+(\d{2,4})", re.I), 0.9),
    # "26/12/2024" / "26-12-2024"
    (re.compile(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})"), 0.9),
    # "21 de sept. de 23.-" (con basura al final; ya cubierto por patrón 1)
    # "3 de septoembre 2024" — typo pero encaja con mes del dict
    (re.compile(r"(\d{1,2})\s+de\s+(\w+)\.?\s+(\d{4})", re.I), 0.7),
]


def parse_fecha(raw: str | None) -> tuple[date | None, float]:
    """Devuelve (fecha_parseada, confianza). Si no parsea, (None, 0.0)."""
    if not raw:
        return None, 0.0
    text = raw.strip()
    if not text:
        return None, 0.0
    for pat, conf in _FECHA_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        try:
            if len(m.groups()) == 3 and "/" in m.group(0):
                d_, mo, y = (int(x) for x in m.groups())
                month = mo
            else:
                d_, month_str, y = m.groups()
                d_ = int(d_)
                y = int(y)
                month = _norm_month(month_str)
                if month is None:
                    continue
            if y < 100:
                y = 2000 + y if y < 50 else 1900 + y
            return date(y, month, d_), conf
        except (ValueError, TypeError):
            continue
    return None, 0.0


# Edad en meses. Devuelve None si no se puede parsear.
_EDAD_ANIOS = re.compile(r"(\d+)\s*a[ñn]os?", re.I)
_EDAD_MESES = re.compile(r"(\d+)\s*meses?", re.I)


def parse_edad_meses(raw: str | None) -> int | None:
    if not raw:
        return None
    text = raw.strip().lower()
    if not text:
        return None
    m = _EDAD_ANIOS.search(text)
    if m:
        return int(m.group(1)) * 12
    m = _EDAD_MESES.search(text)
    if m:
        return int(m.group(1))
    return None


# =============================================================================
# PARSER DE EDAD v2 (Fase 2.1)
# =============================================================================
#
# Inventario de formatos observados en RAW (frecuencia descendente):
#   1. "3 años" / "10 años" / "2 años."           → N*12              (~2.700 filas)
#   2. "1 año" / "5 año"                           → N*12              (~5 filas)
#   3. "8 meses" / "11 meses" / "9 Meses"          → N                 (~150 filas)
#   4. "1 año 6 meses" (separado)                  → N*12 + M          (~10 filas)
#   5. "1año 6meses" / "1año3meses" / "2años6meses"→ N*12 + M compact  (~70 filas)
#   6. "5a" / "5añños" (typo)                      → N*12              (~10 filas)
#   7. "10 m" / "1 mes"                            → N                 (~5 filas)
#   8. "45 días" / "45 días aprox"                 → round(N/30)       (~3 filas)
#   9. "Dos años" (número en letras)               → 2*12              (~2 filas)
#  10. NO PARSEABLES:
#       - "N° Ficha:"    (25) — ruido del informe
#       - "Años"         (1)  — número faltante
#       - "Nina"         (1)  — nombre de paciente
#       - "Estefanía Ogaz" (1) — nombre de tutor/médico
#
# Estrategia: regex tolerante que ignora espacios/tildes/typos alrededor de
# los tokens "año" / "mes" / "día" / "a" / "m" / "d". El número se busca
# inmediatamente antes del token. Si hay un segundo número después de otro
# token, se suma (caso "1año 6meses").

_NUM_WORDS: dict[str, int] = {
    "un": 1, "uno": 1, "una": 1,
    "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
}


def _number_or_word(s: str | None) -> int | None:
    """Convierte '5' o 'cinco' a int. None si no se reconoce."""
    if not s:
        return None
    s2 = s.strip().lower().rstrip(".")
    if not s2:
        return None
    if s2.isdigit():
        return int(s2)
    return _NUM_WORDS.get(s2)


# Patrones de edad. Cada patrón es (regex, confianza) y se prueban en orden.
# El PRIMER match gana. Las regex son permisivas con espacios/tildes/typos.
_EDAD_PATTERNS: list[tuple[re.Pattern, float]] = [
    # "1 año 7 meses" / "10 años 6 meses." (separado, con mes)
    (re.compile(
        r"(\d+|\w+)\s*a[ñn]os?\.?\s+(\d+|\w+)\s*m(?:eses?)?\.?",
        re.I,
    ), 1.0),
    # "1año 6meses" / "1año3meses" / "2años6meses" (compact sin espacio)
    (re.compile(
        r"(\d+)\s*a[ñn]os?\.?\s*(\d+)\s*m(?:eses?)?\.?",
        re.I,
    ), 1.0),
    # "1año 7meses" (con espacio pero sin año final)
    #   ya cubierto por el patrón 1
    # "4 a 11 m" / "1a 7m" (compact: "a" sin "ño", "m" sin "es")
    (re.compile(
        r"(\d+)\s*a\.?\s+(\d+)\s*m\.?",
        re.I,
    ), 1.0),
    # "Dos años" (número en letras + año)
    (re.compile(
        r"(un|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\s*a[ñn]os?",
        re.I,
    ), 0.95),
    # "N años" / "N año" / "N años." / "5añños" (typo)
    (re.compile(
        r"(\d+)\s*a[ñn]+os?\.?",
        re.I,
    ), 1.0),
    # "N año" suelto (sin 's' final, ej. "2 año")
    (re.compile(
        r"(\d+)\s*a[ñn]o\.?",
        re.I,
    ), 1.0),
    # "5a" (compact, solo año)
    (re.compile(
        r"(\d+)\s*a\.?",
        re.I,
    ), 0.9),
    # "9 Meses" / "8 meses." / "1 mes"
    (re.compile(
        r"(\d+)\s*m(?:eses?)?\.?",
        re.I,
    ), 1.0),
    # "10 m" / "10 m." (compact, solo mes)
    #   ya cubierto arriba con la regex "N m" pero aseguramos m no seguido
    #   de "eses" para no capturar mes dentro de años: orden previo lo evita.
    # "45 días" / "45 días aprox"
    (re.compile(
        r"(\d+)\s*d[íi]as?",
        re.I,
    ), 0.9),
]


def parse_edad_meses_v2(raw: str | None) -> int | None:
    """Parser robusto de edad. Devuelve meses (int) o None si no parsea.

    Diferencias con `parse_edad_meses` (F1):
    - Acepta formatos compactos: "5a", "1a 7m", "1año6meses"
    - Acepta números en letras: "Dos años" → 24
    - Acepta días y convierte a meses (45 días → 1 mes)
    - Tolera typos: "añños" / "añños" → 60
    - Rechaza strings no-edad: "N° Ficha:", "Nina", "Años" → None
    """
    if not raw:
        return None
    text = raw.strip()
    if not text:
        return None
    for pat_idx, (pat, _conf) in enumerate(_EDAD_PATTERNS):
        m = pat.search(text)
        if not m:
            continue
        groups = m.groups()
        # Casos con 2 grupos: "N año M mes" → N*12 + M
        if len(groups) == 2:
            n_a = _number_or_word(groups[0])
            n_m = _number_or_word(groups[1])
            if n_a is None or n_m is None:
                continue
            return n_a * 12 + n_m
        # Patrones 0..6 son variantes de "año" → siempre *12.
        # Patrones 7..8 son variantes de "mes" o "día".
        if pat_idx <= 6:
            n = _number_or_word(groups[0])
            if n is None:
                continue
            return n * 12
        # pat_idx == 7 → meses
        if pat_idx == 7:
            n = _number_or_word(groups[0])
            if n is None:
                continue
            return n
        # pat_idx == 8 → días (convertir a meses con floor division)
        n_d = _number_or_word(groups[0])
        if n_d is None:
            continue
        return max(1, n_d // 30)
    return None


# =============================================================================
# RESOLUCIÓN DE DIMENSIONES
# =============================================================================

def _resolve_especie(raw: str | None, dim_especie_map: dict[str, int]) -> tuple[int | None, str | None]:
    """Devuelve (dim_especie_id, valor_original_limpio) o (None, raw).

    Aplica normalización: lowercase, strip de puntuación final. Si no hay
    match, devuelve None (la fila silver_informes queda con dim_especie_id=NULL).
    """
    if not raw:
        return None, raw
    cleaned = raw.strip().rstrip(".").lower()
    # Variantes comunes observadas en RAW
    alias = {
        "canino": "Canino", "canina": "Canino",
        "felino": "Felino", "frlino": "Felino",
        "conejo": "Conejo",
        "cobaya": "Cobaya",
        "huron": "Hurón", "hurón": "Hurón",
        "hamster": "Hámster", "hámster": "Hámster",
        "hamster ruso": "Hámster", "hámster ruso": "Hámster",
        "hamster sirio": "Hámster", "hámster sirio": "Hámster",
        "erizo": "Erizo", "erizo tierra": "Erizo",
        "raton": "Ratón", "ratón": "Ratón",
        "cuy": "Cuy",
    }
    canon = alias.get(cleaned)
    if canon is None:
        return None, raw
    id_ = dim_especie_map.get(canon)
    return id_, raw


def _resolve_sexo(raw: str | None, dim_sexo_map: dict[str, int]) -> tuple[int, str | None]:
    """Resuelve el sexo a partir del campo `genero` de RAW.

    'Hembra*' → Hembra (cualquier variante)
    'Macho*'  → Macho
    Otro o None → Indeterminado (id 3)

    Devuelve (id_canonico, valor_original) — el segundo se conserva para
    trazabilidad.
    """
    if not raw:
        return dim_sexo_map["Indeterminado"], raw
    text = raw.strip().lower()
    if text.startswith("hembra"):
        return dim_sexo_map["Hembra"], raw
    if text.startswith("macho") or text.startswith("mach"):
        return dim_sexo_map["Macho"], raw
    return dim_sexo_map["Indeterminado"], raw


def _resolve_estado_reproductivo(raw: str | None, dim_er_map: dict[str, int]) -> tuple[int, str | None]:
    """Resuelve el estado reproductivo a partir del campo `genero` de RAW.

    'Macho entero' / 'Macho Entero' → Entero
    'Macho castrado' / 'Macho Castrado' → Castrado
    'Hembra OVH' → OVH
    Cualquier otra cosa (incluido None y 'Hembra'/'Macho' solos) →
        No especificado (id 4)
    """
    if not raw:
        return dim_er_map["No especificado"], raw
    text = raw.strip().lower()
    if "castrad" in text:
        return dim_er_map["Castrado"], raw
    if "ovh" in text:
        return dim_er_map["OVH"], raw
    if "enter" in text:
        return dim_er_map["Entero"], raw
    return dim_er_map["No especificado"], raw


def _resolve_estudio(raw: str | None, dim_estudio_map: dict[str, int]) -> tuple[int, str | None]:
    """Resuelve el tipo de estudio. Variantes con mayúscula, puntos, sufijos,
    o combinaciones ('Abdominal/gestacional') caen en una categoría canónica
    o en 'Otro'.
    """
    if not raw:
        return dim_estudio_map["Otro"], raw
    text = raw.strip().rstrip(".").lower()
    canon = {
        "abdominal": "Abdominal",
        "gestacional": "Gestacional",
        "cervical": "Cervical",
        "reproductivo": "Reproductivo",
        "reproductiva": "Reproductivo",
        "partes blandas": "Partes blandas",
        "tejidos blandos": "Partes blandas",
        "tejido blando cervical": "Cervical",
        "musculoesqueletico": "Musculoesquelético",
        "musculoesquelético": "Musculoesquelético",
        "ocular": "Ocular",
    }
    # Combos como 'abdominal/reproductivo' → primer token
    first = text.split("/")[0].strip()
    canonical = canon.get(first, "Otro")
    id_ = dim_estudio_map.get(canonical)
    if id_ is None:
        return dim_estudio_map["Otro"], raw
    return id_, raw


def _resolve_edad_categoria(
    edad_meses: int | None, dim_ec_map: dict[str, int], dim_ec_rows: list[Any],
) -> tuple[int | None, int | None]:
    """Devuelve (dim_edad_categoria_id, edad_meses). edad_meses puede ser None
    si el campo RAW no era parseable.

    Si edad_meses es None, no se asigna categoría (NULL), preservando el
    dato RAW para revisión.
    """
    if edad_meses is None:
        return None, None
    for row in dim_ec_rows:
        id_, codigo, min_m, max_m = row[0], row[1], row[3], row[4]
        if max_m is None:
            if edad_meses >= min_m:
                return id_, edad_meses
        elif min_m <= edad_meses < max_m:
            return id_, edad_meses
    return None, edad_meses


def _load_edad_categoria_rows(engine: Engine) -> list[Any]:
    """Carga filas de dim_edad_categoria como tuplas para la resolución."""
    with engine.begin() as conn:
        rows = conn.execute(
            select(
                dim_edad_categoria.c.id,
                dim_edad_categoria.c.codigo,
                dim_edad_categoria.c.nombre,
                dim_edad_categoria.c.min_meses,
                dim_edad_categoria.c.max_meses,
            )
        ).all()
    return rows


# =============================================================================
# BUILD F1
# =============================================================================

def _insert_silver_informes(
    engine: Engine, rows: list[dict], *, on_conflict_index: list[str] | None = None,
    chunk_size: int = 50,
) -> int:
    """Bulk INSERT idempotente en silver_informes, en chunks.

    SQLite limita a 999 parámetros por statement (~50 filas de 19 cols).
    PostgreSQL acepta 65535, pero conservamos el chunking para portabilidad.

    Devuelve el rowcount acumulado (SQLite: ~1 por insert real; PG: ~1).
    """
    if not rows:
        return 0
    if on_conflict_index is None:
        on_conflict_index = ["informe_id"]
    dialect = "sqlite" if engine.dialect.name == "sqlite" else "postgresql"
    insert_fn = sqlite_insert if dialect == "sqlite" else pg_insert

    total = 0
    for start in range(0, len(rows), chunk_size):
        chunk = rows[start:start + chunk_size]
        stmt = insert_fn(silver_informes).values(chunk)
        stmt = stmt.on_conflict_do_nothing(index_elements=on_conflict_index)
        with engine.begin() as conn:
            result = conn.execute(stmt)
        total += result.rowcount or 0
    return total


def _read_raw_informes(engine: Engine) -> list[dict]:
    """Lee todas las filas de raw.informes (2.893 esperadas)."""
    with engine.begin() as conn:
        rows = conn.execute(select(raw_informes)).all()
    cols = raw_informes.c.keys()
    return [dict(zip(cols, r, strict=False)) for r in rows]


def build_f1(
    silver_engine: Engine, raw_engine: Engine, *, actor: str = "build_silver",
) -> dict[str, Any]:
    """Ejecuta la Fase 1 del ETL: silver_informes.

    Returns: métricas de la ejecución (rows_read, rows_written, duration_ms,
    parse_coverage_*, etc.).
    """
    t0 = time.monotonic()
    started_at = datetime.now()

    # Dimensiones
    dim_especie_map = _load_dim(silver_engine, dim_especie)
    dim_sexo_map = _load_dim(silver_engine, dim_sexo)
    dim_er_map = _load_dim(silver_engine, dim_estado_reproductivo)
    dim_estudio_map = _load_dim(silver_engine, dim_estudio)
    dim_ec_rows = _load_edad_categoria_rows(silver_engine)

    # Sanity checks: dims deben estar pobladas (bootstrap_basico previo)
    for nombre, m in [
        ("dim_especie", dim_especie_map),
        ("dim_sexo", dim_sexo_map),
        ("dim_estado_reproductivo", dim_er_map),
        ("dim_estudio", dim_estudio_map),
    ]:
        if not m:
            raise RuntimeError(
                f"{nombre} está vacía. Ejecutá bootstrap_basico() antes de build_f1()."
            )

    # RAW
    raw_rows = _read_raw_informes(raw_engine)
    n_raw = len(raw_rows)

    # Build
    silver_rows: list[dict] = []
    parse_coverage_fecha = 0
    parse_coverage_edad = 0
    n_skipped_no_edad = 0

    for r in raw_rows:
        informe_id = r["id"]
        fecha_parseada, fecha_confianza = parse_fecha(r.get("fecha"))
        if fecha_parseada is not None:
            parse_coverage_fecha += 1
        edad_meses = parse_edad_meses(r.get("edad"))
        if edad_meses is not None:
            parse_coverage_edad += 1
        else:
            n_skipped_no_edad += 1
        dim_ec_id, edad_meses_out = _resolve_edad_categoria(edad_meses, None, dim_ec_rows)

        dim_especie_id, _ = _resolve_especie(r.get("especie"), dim_especie_map)
        dim_sexo_id, _ = _resolve_sexo(r.get("genero"), dim_sexo_map)
        dim_er_id, _ = _resolve_estado_reproductivo(r.get("genero"), dim_er_map)
        dim_estudio_id, _ = _resolve_estudio(r.get("estudio"), dim_estudio_map)

        silver_rows.append({
            "informe_id": informe_id,
            "sha256": r["sha256"],
            "anio": r["anio"],
            "fecha_raw": r.get("fecha"),
            "fecha_parseada": fecha_parseada,
            "fecha_confianza": fecha_confianza,
            "dim_especie_id": dim_especie_id,
            "dim_raza_id": None,  # F2
            "dim_sexo_id": dim_sexo_id,
            "dim_estado_reproductivo_id": dim_er_id,
            "dim_estudio_id": dim_estudio_id,
            "dim_edad_categoria_id": dim_ec_id,
            "edad_meses": edad_meses_out,
            "edad_origen_raw": r.get("edad"),
            "edad_parse_ok": edad_meses_out is not None,
            "peso_kg": None,  # sin cobertura RAW; F+
            "nombre_paciente": r.get("nombre"),
            "tutor": r.get("tutor"),
            "doctor_solicitante": r.get("doctor_solicitante"),
            "n_ficha": r.get("n_ficha"),
        })

    rows_written = _insert_silver_informes(silver_engine, silver_rows)
    duration_ms = int((time.monotonic() - t0) * 1000)
    finished_at = datetime.now()

    metrics = {
        "rows_read": n_raw,
        "rows_written": rows_written,
        "parse_cobertura_fecha_pct": round(100 * parse_coverage_fecha / n_raw, 1) if n_raw else 0,
        "parse_cobertura_edad_pct": round(100 * parse_coverage_edad / n_raw, 1) if n_raw else 0,
        "n_sin_edad": n_skipped_no_edad,
        "duration_ms": duration_ms,
        "started_at": started_at.isoformat(timespec="seconds"),
        "finished_at": finished_at.isoformat(timespec="seconds"),
    }

    _log_run(silver_engine, "f1", started_at, finished_at, "ok",
             rows_read=n_raw, rows_written=rows_written, rows_skipped=0,
             duration_ms=duration_ms, actor=actor, notes=str(metrics))
    return metrics


# =============================================================================
# FASE 2 — NORMALIZACIÓN DE CATÁLOGOS Y TABLAS MAP
# =============================================================================

from collections import Counter, defaultdict  # noqa: E402

from .models_silver import (  # noqa: E402
    dim_raza,
    map_especie,
    map_estudio,
    map_raza,
    map_sexo,
    stg_razas_detectadas,
    stg_valores_no_mapeados,
)

# Umbral de auto-aprobación de razas. Frecuencias >= RAZA_AUTOAPPROVE_THRESHOLD
# entran a dim_raza con map_raza.estado_revision='aprobada'. El resto va a
# stg_razas_detectadas con map_raza.estado_revision='pendiente'.
RAZA_AUTOAPPROVE_THRESHOLD = 3

# Origen por defecto para todas las filas generadas por F2.
_ORIGEN_BUILD = "build_f2_v1"

# Alias canónicos de estudio (lowercase). Single source of truth para F2.
_ESTUDIO_ALIAS: dict[str, str] = {
    "abdominal": "Abdominal",
    "gestacional": "Gestacional",
    "cervical": "Cervical",
    "reproductivo": "Reproductivo",
    "reproductiva": "Reproductivo",
    "partes blandas": "Partes blandas",
    "tejidos blandos": "Partes blandas",
    "tejido blando cervical": "Cervical",
    "musculoesqueletico": "Musculoesquelético",
    "musculoesquelético": "Musculoesquelético",
    "ocular": "Ocular",
}

# Alias canónicos de especie (lowercase). Variantes de género colapsan al
# masculino canónico.
_ESPECIE_ALIAS: dict[str, str] = {
    "canino": "Canino",
    "canina": "Canino",
    "felino": "Felino",
    "conejo": "Conejo",
    "cobaya": "Cobaya",
    "huron": "Hurón",
    "hurón": "Hurón",
    "hamster": "Hámster",
    "hámster": "Hámster",
    "hamster ruso": "Hámster",
    "hámster ruso": "Hámster",
    "hamster sirio": "Hámster",
    "hámster sirio": "Hámster",
    "erizo": "Erizo",
    "erizo tierra": "Erizo",
    "raton": "Ratón",
    "ratón": "Ratón",
    "cuy": "Cuy",
}

# Identifica nombres de razas que NO son razas sino calificadores/abreviaturas.
# Van a stg_razas_detectadas con propuesta_canonica = "ABREVIATURA" o similar.
_RAZA_DESCARTADAS: set[str] = set()


def _norm_lower_punct(s: str | None) -> str:
    """Lowercase + strip + rstrip puntuación final. Vacío → ''."""
    if not s:
        return ""
    return s.strip().rstrip(".,;:").lower()


def _upsert_chunks(
    engine: Engine, table, rows: list[dict], *, index_elements: list[str],
    chunk_size: int = 50,
) -> int:
    """Bulk INSERT idempotente, en chunks, con ON CONFLICT DO NOTHING."""
    if not rows:
        return 0
    dialect = "sqlite" if engine.dialect.name == "sqlite" else "postgresql"
    insert_fn = sqlite_insert if dialect == "sqlite" else pg_insert

    total = 0
    for start in range(0, len(rows), chunk_size):
        chunk = rows[start:start + chunk_size]
        stmt = insert_fn(table).values(chunk)
        stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)
        with engine.begin() as conn:
            result = conn.execute(stmt)
        total += result.rowcount or 0
    return total


def _read_raw_distinct_column(engine: Engine, column: str) -> list[tuple[str, int]]:
    """Lee (valor, frecuencia) de raw.informes para una columna."""
    with engine.begin() as conn:
        rows = conn.execute(
            raw_informes.select().with_only_columns(
                raw_informes.c.id, getattr(raw_informes.c, column)
            )
        ).all()
    counts: Counter = Counter()
    for _, v in rows:
        if v is None:
            continue
        sv = str(v).strip()
        if not sv:
            continue
        counts[sv] += 1
    return counts.most_common()


def _infer_especie_for_raza(
    engine: Engine, raza: str,
) -> tuple[int | None, str | None]:
    """Para una raza, devuelve (dim_especie_id, especie_raw) más frecuente
    entre los informes donde aparece esa raza. None si no hay datos o no se
    puede resolver.

    Devuelve (None, especie_raw_string) — el ID se resuelve después contra
    la dimensión cargada en el silver_engine.
    """
    with engine.begin() as conn:
        rows = conn.execute(
            raw_informes.select().where(raw_informes.c.raza == raza)
        ).all()
    if not rows:
        return None, None
    esp_counts: Counter = Counter()
    for r in rows:
        esp = (r.especie or "").strip()
        if esp:
            esp_counts[esp] += 1
    if not esp_counts:
        return None, None
    esp_top, _ = esp_counts.most_common(1)[0]
    return None, esp_top


def _resolve_especie_id(silver_engine: Engine, especie_raw: str | None) -> int | None:
    """Resuelve especie_raw → dim_especie_id vía el alias determinístico."""
    if not especie_raw:
        return None
    dim_map = _load_dim(silver_engine, dim_especie)
    canon = _ESPECIE_ALIAS.get(_norm_lower_punct(especie_raw))
    return dim_map.get(canon) if canon else None


def _es_mestizo(s: str | None) -> bool:
    if not s:
        return False
    s2 = s.lower()
    return any(tok in s2 for tok in ("mestiz", "criollo", "srd", "s/c", " sin raza"))


def _is_trivial_other(text: str) -> bool:
    """True si el valor original es trivialmente 'Otro' (string vacío tras normalizar)."""
    return text in ("", "otro")


# =============================================================================
# MAP_ESPECIE
# =============================================================================

def _build_map_especie(
    silver_engine: Engine, raw_engine: Engine,
) -> tuple[list[dict], list[dict]]:
    """Puebla map_especie y devuelve (rows_ok, rows_stg)."""
    counts = _read_raw_distinct_column(raw_engine, "especie")
    dim_map = _load_dim(silver_engine, dim_especie)
    rows_ok: list[dict] = []
    rows_stg: list[dict] = []
    for val, freq in counts:
        canon = _ESPECIE_ALIAS.get(_norm_lower_punct(val))
        if canon and canon in dim_map:
            rows_ok.append({
                "valor_original": val,
                "dim_especie_id": dim_map[canon],
                "confianza": 1.0,
                "origen": _ORIGEN_BUILD,
            })
        else:
            rows_stg.append({
                "dimension": "especie",
                "valor_original": val,
                "frecuencia": freq,
                "propuesta_canonica": canon,
                "dim_destino_id": dim_map.get(canon) if canon else None,
                "estado_revision": "pendiente",
                "origen": _ORIGEN_BUILD,
                "observaciones": "no matchea alias determinístico",
            })
    return rows_ok, rows_stg


# =============================================================================
# MAP_SEXO (genero)
# =============================================================================

def _build_map_sexo(
    silver_engine: Engine, raw_engine: Engine,
) -> tuple[list[dict], list[dict]]:
    """Puebla map_sexo a partir de raw.informes.genero.

    Reglas determinísticas:
    - startswith 'hembra' → Hembra
    - startswith 'macho' o 'mach' → Macho
    - resto → Indeterminado
    """
    counts = _read_raw_distinct_column(raw_engine, "genero")
    dim_map = _load_dim(silver_engine, dim_sexo)
    rows_ok: list[dict] = []
    rows_stg: list[dict] = []
    for val, freq in counts:
        low = val.strip().lower()
        if low.startswith("hembra"):
            canon = "Hembra"
        elif low.startswith("macho") or low.startswith("mach"):
            canon = "Macho"
        else:
            canon = "Indeterminado"
        canon_id = dim_map.get(canon)
        if canon_id is None:
            rows_stg.append({
                "dimension": "sexo",
                "valor_original": val,
                "frecuencia": freq,
                "propuesta_canonica": canon,
                "dim_destino_id": None,
                "estado_revision": "pendiente",
                "origen": _ORIGEN_BUILD,
                "observaciones": "dim_sexo sin entrada canónica",
            })
            continue
        # Si era 'Edad:' u otro claramente no-sexo, lo mandamos a staging
        # ADEMÁS del map_sexo para auditoría (porque la resolución es forzada).
        if not (low.startswith("hembra") or low.startswith("macho") or low.startswith("mach")):
            rows_stg.append({
                "dimension": "sexo",
                "valor_original": val,
                "frecuencia": freq,
                "propuesta_canonica": canon,
                "dim_destino_id": canon_id,
                "estado_revision": "pendiente",
                "origen": _ORIGEN_BUILD,
                "observaciones": f"forzado a {canon}; valor no es un sexo",
            })
        rows_ok.append({
            "valor_original": val,
            "dim_sexo_id": canon_id,
            "confianza": 1.0 if canon in ("Hembra", "Macho") else 0.5,
            "origen": _ORIGEN_BUILD,
        })
    return rows_ok, rows_stg


# =============================================================================
# MAP_ESTUDIO
# =============================================================================

def _build_map_estudio(
    silver_engine: Engine, raw_engine: Engine,
) -> tuple[list[dict], list[dict]]:
    counts = _read_raw_distinct_column(raw_engine, "estudio")
    dim_map = _load_dim(silver_engine, dim_estudio)
    rows_ok: list[dict] = []
    rows_stg: list[dict] = []
    for val, freq in counts:
        text = val.strip().rstrip(".").lower()
        first = text.split("/")[0].strip()
        canon = _ESTUDIO_ALIAS.get(first, "Otro")
        canon_id = dim_map.get(canon)
        if canon_id is None:
            rows_stg.append({
                "dimension": "estudio",
                "valor_original": val,
                "frecuencia": freq,
                "propuesta_canonica": canon,
                "dim_destino_id": None,
                "estado_revision": "pendiente",
                "origen": _ORIGEN_BUILD,
                "observaciones": "dim_estudio sin entrada canónica",
            })
            continue
        # Si canon == "Otro" y el valor no es trivialmente otro, lo logueamos
        # en staging como candidato a nueva categoría.
        if canon == "Otro" and not _is_trivial_other(text):
            rows_stg.append({
                "dimension": "estudio",
                "valor_original": val,
                "frecuencia": freq,
                "propuesta_canonica": canon,
                "dim_destino_id": canon_id,
                "estado_revision": "pendiente",
                "origen": _ORIGEN_BUILD,
                "observaciones": "categorizado como Otro; revisar si merece dim propia",
            })
        rows_ok.append({
            "valor_original": val,
            "dim_estudio_id": canon_id,
            "confianza": 1.0 if canon != "Otro" else 0.6,
            "origen": _ORIGEN_BUILD,
        })
    return rows_ok, rows_stg


# =============================================================================
# DIM_RAZA + MAP_RAZA + STG_RAZAS_DETECTADAS
# =============================================================================

def _build_dim_raza(
    silver_engine: Engine, raw_engine: Engine, raza_counts: list[tuple[str, int]],
) -> dict[str, int]:
    """Crea entradas en dim_raza para razas con freq >= threshold.

    Devuelve dict {valor_original: dim_raza_id}.
    """
    dim_map = _load_dim(silver_engine, dim_raza)
    rows: list[dict] = []
    nombre_to_id: dict[str, int] = {}
    for val, freq in raza_counts:
        if freq < RAZA_AUTOAPPROVE_THRESHOLD:
            continue
        if val in dim_map:
            nombre_to_id[val] = dim_map[val]
            continue
        # Especie inferida por mayoría (lectura raw → resolución con silver dim)
        _, esp_raw = _infer_especie_for_raza(raw_engine, val)
        esp_id = _resolve_especie_id(silver_engine, esp_raw)
        rows.append({
            "nombre_canonico": val,
            "dim_especie_id": esp_id,
            "es_mestizo": _es_mestizo(val),
            "fuente": _ORIGEN_BUILD,
        })
    if rows:
        # Idempotente: on_conflict_do_nothing por (dim_especie_id, nombre_canonico)
        # (UNIQUE constraint en dim_raza).
        dialect = "sqlite" if silver_engine.dialect.name == "sqlite" else "postgresql"
        insert_fn = sqlite_insert if dialect == "sqlite" else pg_insert
        for start in range(0, len(rows), 50):
            chunk = rows[start:start + 50]
            stmt = insert_fn(dim_raza).values(chunk)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["dim_especie_id", "nombre_canonico"]
            )
            with silver_engine.begin() as conn:
                conn.execute(stmt)
    # Refrescar el mapa (incluye las recién insertadas)
    fresh = _load_dim(silver_engine, dim_raza)
    for val, freq in raza_counts:
        if freq >= RAZA_AUTOAPPROVE_THRESHOLD:
            nombre_to_id[val] = fresh.get(val)
    return nombre_to_id


def _build_map_raza(
    silver_engine: Engine, raw_engine: Engine, raza_counts: list[tuple[str, int]],
    dim_raza_map: dict[str, int],
) -> tuple[list[dict], list[dict]]:
    """Genera rows para map_raza y stg_razas_detectadas.

    map_raza: una fila por valor_original único con estado_revision
    ('aprobada' si la raza fue auto-aprobada en dim_raza; 'pendiente' si no).
    stg_razas_detectadas: filas para razas no auto-aprobadas (freq<3).
    """
    rows_map: list[dict] = []
    rows_stg: list[dict] = []
    for val, freq in raza_counts:
        is_approved = freq >= RAZA_AUTOAPPROVE_THRESHOLD and val in dim_raza_map
        # Especie inferida
        _, esp_raw = _infer_especie_for_raza(raw_engine, val)
        esp_id = _resolve_especie_id(silver_engine, esp_raw)
        if is_approved:
            rows_map.append({
                "valor_original": val,
                "dim_raza_id": dim_raza_map[val],
                "dim_especie_id": esp_id,
                "estado_revision": "aprobada",
                "frecuencia": freq,
                "confianza": 0.9,
                "origen": _ORIGEN_BUILD,
            })
        else:
            # Pendiente de revisión. dim_raza_id queda NULL hasta que se cree.
            rows_map.append({
                "valor_original": val,
                "dim_raza_id": None,
                "dim_especie_id": esp_id,
                "estado_revision": "pendiente",
                "frecuencia": freq,
                "confianza": 0.0,
                "origen": _ORIGEN_BUILD,
            })
            rows_stg.append({
                "valor_original": val,
                "frecuencia": freq,
                "dim_especie_inferida_id": esp_id,
                "propuesta_canonica": val,
                "dim_raza_propuesta_id": None,
                "estado_revision": "pendiente",
                "origen": _ORIGEN_BUILD,
                "observaciones": "freq<{} o sin especie inferida".format(
                    RAZA_AUTOAPPROVE_THRESHOLD
                ) if freq < RAZA_AUTOAPPROVE_THRESHOLD else "sin match en dim_raza",
            })
    return rows_map, rows_stg


# =============================================================================
# BUILD F2 — ORQUESTADOR
# =============================================================================

def build_f2(
    silver_engine: Engine, raw_engine: Engine, *, actor: str = "build_silver",
) -> dict[str, Any]:
    """Ejecuta la Fase 2: puebla map_* y dim_raza, deja excepciones en staging.

    Asume que F1 ya corrió (silver_informes poblado y dim_* base con seeds).
    No modifica silver_informes.
    """
    t0 = time.monotonic()
    started_at = datetime.now()

    # --- Especie ---
    map_esp_rows, stg_esp_rows = _build_map_especie(silver_engine, raw_engine)
    n_map_esp = _upsert_chunks(
        silver_engine, map_especie, map_esp_rows, index_elements=["valor_original"]
    )
    n_stg_esp = _upsert_chunks(
        silver_engine, stg_valores_no_mapeados, stg_esp_rows,
        index_elements=["dimension", "valor_original"],
    )

    # --- Sexo ---
    map_sexo_rows, stg_sexo_rows = _build_map_sexo(silver_engine, raw_engine)
    n_map_sexo = _upsert_chunks(
        silver_engine, map_sexo, map_sexo_rows, index_elements=["valor_original"]
    )
    n_stg_sexo = _upsert_chunks(
        silver_engine, stg_valores_no_mapeados, stg_sexo_rows,
        index_elements=["dimension", "valor_original"],
    )

    # --- Estudio ---
    map_est_rows, stg_est_rows = _build_map_estudio(silver_engine, raw_engine)
    n_map_est = _upsert_chunks(
        silver_engine, map_estudio, map_est_rows, index_elements=["valor_original"]
    )
    n_stg_est = _upsert_chunks(
        silver_engine, stg_valores_no_mapeados, stg_est_rows,
        index_elements=["dimension", "valor_original"],
    )

    # --- Raza (dim_raza + map_raza + stg_razas_detectadas) ---
    raza_counts = _read_raw_distinct_column(raw_engine, "raza")
    dim_raza_map = _build_dim_raza(silver_engine, raw_engine, raza_counts)
    map_raza_rows, stg_raza_rows = _build_map_raza(
        silver_engine, raw_engine, raza_counts, dim_raza_map
    )
    n_map_raza = _upsert_chunks(
        silver_engine, map_raza, map_raza_rows, index_elements=["valor_original"]
    )
    n_stg_raza = _upsert_chunks(
        silver_engine, stg_razas_detectadas, stg_raza_rows,
        index_elements=["valor_original"],
    )

    duration_ms = int((time.monotonic() - t0) * 1000)
    finished_at = datetime.now()

    metrics = {
        "map_especie": n_map_esp,
        "stg_especie": n_stg_esp,
        "map_sexo": n_map_sexo,
        "stg_sexo": n_stg_sexo,
        "map_estudio": n_map_est,
        "stg_estudio": n_stg_est,
        "dim_raza": len(dim_raza_map),
        "map_raza": n_map_raza,
        "stg_razas": n_stg_raza,
        "duration_ms": duration_ms,
    }

    _log_run(silver_engine, "f2", started_at, finished_at, "ok",
             rows_read=sum(len(c) for c in (map_esp_rows, map_sexo_rows,
                                           map_est_rows, map_raza_rows)),
             rows_written=n_map_esp + n_map_sexo + n_map_est + n_map_raza,
             rows_skipped=0, duration_ms=duration_ms,
             actor=actor, notes=str(metrics))
    return metrics


def _log_run(
    engine: Engine, phase: str, started_at: datetime, finished_at: datetime,
    status: str, *, rows_read: int, rows_written: int, rows_skipped: int,
    duration_ms: int, actor: str, notes: str | None = None,
) -> None:
    with engine.begin() as conn:
        conn.execute(silver_etl_runs.insert().values(
            phase=phase,
            started_at=started_at,
            finished_at=finished_at,
            status=status,
            rows_read=rows_read,
            rows_written=rows_written,
            rows_skipped=rows_skipped,
            rows_errored=0,
            duration_ms=duration_ms,
            actor=actor,
            notes=notes,
        ))


# =============================================================================
# FASE 2.1 — DATA QUALITY Y REFINAMIENTO DE DIMENSIONES
# =============================================================================
#
# TAREA 1 — Refactor dim_raza:
#   dim_raza debe contener exclusivamente valores canónicos. map_raza
#   contiene TODAS las variantes observadas en RAW. Se consolidan 7 grupos
#   de duplicados (mayúsculas, typos, plurales) y se renombran DPC/DPL.
#
# TAREA 2 — DPC/DPL → nombres expandidos:
#   DPC → Doméstico Pelo Corto
#   DPL → Doméstico Pelo Largo
#
# TAREA 3 — Edad estructurada:
#   silver_informes ya tiene `edad_meses`, `edad_origen_raw`. Se agrega
#   `edad_parse_ok` (migración v2.1) y se re-poesen las 2.893 filas.
#
# TAREA 4 — Cobertura >=99% de edad_meses.

# Origen para todas las filas generadas por F2.1.
_ORIGEN_F2_1 = "build_f2_1_v1"

# Alias canónicos de raza: dict[valor_original (case-sensitive)] → canónico.
# El case-sensitive es importante: "Bóxer" vs "Boxer" se tratan como dos
# entradas distintas en RAW (map_raza), pero ambas apuntan al mismo canónico.
_RAZA_CANONICAL_ALIAS: dict[str, str] = {
    # Grupo 1: Bóxer / Boxer
    "Bóxer":      "Boxer",
    # Grupo 2: Bull Dog Francés / Frances
    "Bull Dog Frances": "Bull Dog Francés",
    # Grupo 3: Rotweiler / Rottweiler
    "Rotweiler":  "Rottweiler",
    # Grupo 4: Pastor Alemán / alemán
    "Pastor alemán": "Pastor Alemán",
    # Grupo 5: Terrier Chileno / chileno
    "Terrier chileno": "Terrier Chileno",
    # Grupo 6: Mestizo / Mestiza / Mestizo.
    "Mestiza":    "Mestizo",
    "Mestizo.":   "Mestizo",
    # Grupo 7-8: DPC / DPL (rename a nombres expandidos)
    "DPC":        "Doméstico Pelo Corto",
    "DPL":        "Doméstico Pelo Largo",
}


def refactor_dim_raza(silver_engine: Engine) -> dict[str, Any]:
    """Consolida variantes duplicadas en dim_raza y aplica renames DPC/DPL.

    Pasos:
    1. Cargar dim_raza.
    2. Para cada entrada cuyo nombre está en _RAZA_CANONICAL_ALIAS, calcular
       su canónico.
    3. Agrupar por (dim_especie_id, canónico): el de menor id es el keeper.
       El resto es obsoleto.
    4. Redirigir map_raza.dim_raza_id de los obsoletos → keeper.
    5. Eliminar las filas obsoletas en dim_raza.
    6. Renombrar DPC/DPL → "Doméstico Pelo Corto/Largo" (caso especial).

    Idempotencia: si los keepers ya están consolidados y DPC/DPL ya están
    expandidos, no hace nada.

    Devuelve métricas con el conteo de consolidaciones, renames y deleciones.
    """
    metrics = {
        "merges": 0,
        "renames": 0,
        "deletes": 0,
        "map_redirects": 0,
        "already_applied": False,
    }

    with silver_engine.begin() as conn:
        # Cargar dim_raza completa
        rows = conn.execute(
            select(
                dim_raza.c.id,
                dim_raza.c.nombre_canonico,
                dim_raza.c.dim_especie_id,
            )
        ).all()

        # ¿Ya fue aplicado?
        nombres = {n for _, n, _ in rows}
        no_alias_leftover = not any(n in _RAZA_CANONICAL_ALIAS for n in nombres)
        if (
            "Doméstico Pelo Corto" in nombres
            and "Doméstico Pelo Largo" in nombres
            and no_alias_leftover
        ):
            metrics["already_applied"] = True
            return metrics

        # 1. Construir plan de consolidación: (id, esp_id, nombre_actual, canon)
        plan: list[tuple[int, int, str, str]] = []
        for did, nombre, esp_id in rows:
            canon = _RAZA_CANONICAL_ALIAS.get(nombre, nombre)
            plan.append((did, esp_id, nombre, canon))

        # 2. Agrupar por (esp_id, canon) → keeper (preferencia: nombre YA canónico
        # entre los miembros; si ninguno lo es, el de menor id) + obsoletos.
        groups: dict[tuple[int, str], list[tuple[int, str]]] = {}
        for did, esp_id, nombre, canon in plan:
            groups.setdefault((esp_id, canon), []).append((did, nombre))

        redirects: list[tuple[int, int]] = []  # (obsolete_id, keeper_id)
        renames_after_merge: list[tuple[int, str]] = []  # (keeper_id, canon) si keeper necesita rename
        for (esp_id, canon), entries in groups.items():
            if len(entries) < 2:
                continue
            # Preferir como keeper aquella entrada cuyo nombre YA ES el canónico.
            keepers_with_canon_name = [did for did, n in entries if n == canon]
            if keepers_with_canon_name:
                keeper_id = min(keepers_with_canon_name)
            else:
                keeper_id = min(did for did, _ in entries)
            # Renombrar el keeper si su nombre actual no es el canónico
            keeper_name = next(n for did, n in entries if did == keeper_id)
            if keeper_name != canon:
                renames_after_merge.append((keeper_id, canon))
            # Resto → obsoletos
            for did, _n in entries:
                if did != keeper_id:
                    redirects.append((did, keeper_id))

        # 3. Aplicar redirects en map_raza
        for obs_id, keeper_id in redirects:
            result = conn.execute(
                map_raza.update()
                .where(map_raza.c.dim_raza_id == obs_id)
                .values(dim_raza_id=keeper_id)
            )
            metrics["map_redirects"] += result.rowcount or 0
            metrics["merges"] += 1

        # 4. Renombrar keeper si es necesario
        for keeper_id, new_name in renames_after_merge:
            conn.execute(
                dim_raza.update()
                .where(dim_raza.c.id == keeper_id)
                .values(nombre_canonico=new_name)
            )
            metrics["renames"] += 1

        # 5. Eliminar obsoletos en dim_raza
        if redirects:
            obsolete_ids = [obs for obs, _ in redirects]
            conn.execute(
                dim_raza.delete().where(dim_raza.c.id.in_(obsolete_ids))
            )
            metrics["deletes"] = len(obsolete_ids)

        # 6. Renames DPC/DPL → nombres expandidos.
        #    Después de la consolidación, estos nombres ya no deben chocar
        #    con otra entrada del mismo canónico expandido.
        renames_dpc_dpl = {"DPC": "Doméstico Pelo Corto", "DPL": "Doméstico Pelo Largo"}
        for old_name, new_name in renames_dpc_dpl.items():
            row = conn.execute(
                select(dim_raza.c.id, dim_raza.c.dim_especie_id)
                .where(dim_raza.c.nombre_canonico == old_name)
            ).first()
            if row is None:
                continue
            did, esp_id = row[0], row[1]
            # ¿Ya existe la entrada con nombre nuevo?
            existing = conn.execute(
                select(dim_raza.c.id)
                .where(
                    (dim_raza.c.dim_especie_id == esp_id) &
                    (dim_raza.c.nombre_canonico == new_name)
                )
            ).first()
            if existing:
                # Merge: redirect map_raza, delete old.
                result = conn.execute(
                    map_raza.update()
                    .where(map_raza.c.dim_raza_id == did)
                    .values(dim_raza_id=existing[0])
                )
                metrics["map_redirects"] += result.rowcount or 0
                conn.execute(dim_raza.delete().where(dim_raza.c.id == did))
                metrics["deletes"] += 1
                metrics["merges"] += 1
            else:
                conn.execute(
                    dim_raza.update()
                    .where(dim_raza.c.id == did)
                    .values(nombre_canonico=new_name)
                )
                metrics["renames"] += 1

        # 7. Pase correctivo: si quedó alguna entrada con un nombre que está
        #    en _RAZA_CANONICAL_ALIAS (i.e. nunca fue renombrada), aplicar
        #    el rename ahora. Esto cubre el caso en que el keeper elegido
        #    no tenía el nombre canónico (ej. "Bóxer"→"Boxer").
        leftovers = conn.execute(
            select(dim_raza.c.id, dim_raza.c.nombre_canonico)
        ).all()
        for did, nombre in leftovers:
            canon = _RAZA_CANONICAL_ALIAS.get(nombre)
            if canon is None or canon == nombre:
                continue
            conn.execute(
                dim_raza.update()
                .where(dim_raza.c.id == did)
                .values(nombre_canonico=canon)
            )
            metrics["renames"] += 1

    return metrics


def backfill_silver_informes_edad(
    silver_engine: Engine, raw_engine: Engine,
) -> dict[str, Any]:
    """Re-calcula edad_meses y edad_parse_ok en silver_informes para los 2.893
    informes RAW. Usa parse_edad_meses_v2 (F2.1).

    Devuelve métricas: rows_updated, parse_coverage_pct, n_unparsed.
    """
    t0 = time.monotonic()
    # Cargar RAW
    with raw_engine.begin() as conn:
        raw_rows = conn.execute(
            select(raw_informes.c.id, raw_informes.c.edad)
        ).all()
    raw_edad = {rid: edad for rid, edad in raw_rows}

    rows_updated = 0
    n_parsed = 0
    n_unparsed = 0
    n_skipped_no_change = 0
    unparsed_examples: dict[str, int] = {}

    with silver_engine.begin() as conn:
        silver_rows = conn.execute(
            select(
                silver_informes.c.informe_id,
                silver_informes.c.edad_meses,
                silver_informes.c.edad_parse_ok,
            )
        ).all()

        for informe_id, current_meses, current_ok in silver_rows:
            raw = raw_edad.get(informe_id)
            new_meses = parse_edad_meses_v2(raw)
            new_ok = new_meses is not None
            if new_ok:
                n_parsed += 1
            else:
                n_unparsed += 1
                key = (raw or "").strip()
                unparsed_examples[key] = unparsed_examples.get(key, 0) + 1

            # Update sólo si cambió algo (idempotencia)
            if current_meses != new_meses or bool(current_ok) != new_ok:
                conn.execute(
                    silver_informes.update()
                    .where(silver_informes.c.informe_id == informe_id)
                    .values(
                        edad_meses=new_meses,
                        edad_origen_raw=raw,
                        edad_parse_ok=new_ok,
                    )
                )
                rows_updated += 1
            else:
                n_skipped_no_change += 1

    total = len(silver_rows)
    coverage = round(100.0 * n_parsed / total, 2) if total else 0.0
    duration_ms = int((time.monotonic() - t0) * 1000)

    return {
        "rows_scanned": total,
        "rows_updated": rows_updated,
        "rows_skipped_no_change": n_skipped_no_change,
        "n_parsed": n_parsed,
        "n_unparsed": n_unparsed,
        "parse_coverage_pct": coverage,
        "duration_ms": duration_ms,
        "unparsed_examples": unparsed_examples,
    }


def build_f2_1(
    silver_engine: Engine, raw_engine: Engine, *, actor: str = "build_silver",
) -> dict[str, Any]:
    """Ejecuta la Fase 2.1: refactor dim_raza + DPC/DPL + backfill edad.

    Asume F1 + F2 ya corrieron. Modifica dim_raza y silver_informes en sitio.
    Las tablas map_raza y stg_valores_no_mapeados NO se regeneran (se
    preservan como auditoría de F2; el refactor sólo re-direcciona FKs).
    """
    from .silver_db import migrate as _migrate

    t0 = time.monotonic()
    started_at = datetime.now()

    # 0. Migraciones pendientes (idempotente)
    migrations = _migrate(silver_engine)

    # 1. Refactor dim_raza (consolidación + DPC/DPL)
    refactor_metrics = refactor_dim_raza(silver_engine)

    # 2. Backfill silver_informes.edad_meses + edad_parse_ok
    edad_metrics = backfill_silver_informes_edad(silver_engine, raw_engine)

    duration_ms = int((time.monotonic() - t0) * 1000)
    finished_at = datetime.now()

    metrics = {
        "migrations": migrations,
        "refactor_dim_raza": refactor_metrics,
        "edad": edad_metrics,
        "duration_ms": duration_ms,
    }

    _log_run(silver_engine, "f2_1", started_at, finished_at, "ok",
             rows_read=edad_metrics["rows_scanned"],
             rows_written=edad_metrics["rows_updated"],
             rows_skipped=edad_metrics["rows_skipped_no_change"],
             duration_ms=duration_ms, actor=actor, notes=str(metrics))
    return metrics


# =============================================================================
# FASE 3 (F3) — EXTRACCIÓN DE ATRIBUTOS CLÍNICOS
# =============================================================================
#
# Modelo F3:
#   dim_atributo (31) + dim_organo_atributo (62) + dim_segmento_anatomico (6)
#   + dim_valor_atributo (172). Para cada hallazgo en silver_hallazgos:
#   - detectar segmento (Intestino duodeno_yeyuno vs colon; Riñones izq vs der)
#   - detectar lateralidad (izq/der/bilateral)
#   - extraer atributos via regex (VALUE_PROPOSALS)
#   - escribir silver_atributos_hallazgo con metodo_extraccion='regex_v1'

from collections import Counter as _Counter  # noqa: E402

from .models_silver import (  # noqa: E402
    dim_atributo,
    dim_organo,
    dim_organo_atributo,
    dim_segmento_anatomico,
    dim_valor_atributo,
    silver_atributos_hallazgo,
    silver_hallazgos,
)

# Patrones de lateralidad (orden importa: izq/der son más específicos que bilateral)
_LAT_IZQ = re.compile(
    r"\b(izquierd[oa]|izq\.?|ri[ñn][oó]n\s+izquierdo|ri[ñn][oó]n\s+izq|"
    r"adrenal\s+izquierda|adrenal\s+izq)\b",
    re.IGNORECASE,
)
_LAT_DER = re.compile(
    r"\b(derech[oa]|der\.?|ri[ñn][oó]n\s+derecho|ri[ñn][oó]n\s+der|"
    r"adrenal\s+derecha|adrenal\s+der)\b",
    re.IGNORECASE,
)
_LAT_BIL = re.compile(
    r"\b(ambos|ambas|bilateral|bi)\b",
    re.IGNORECASE,
)

# Patrones de segmento intestinal
_SEG_DUOD_YEY = re.compile(r"\b(duodeno|yeyuno|yeyunal)\b", re.IGNORECASE)
_SEG_COLON = re.compile(r"\b(colon|ciego|recto)\b", re.IGNORECASE)
_SEG_ILEON = re.compile(r"\b[ií]leon\b", re.IGNORECASE)


def _detect_segmento(desc: str, organo: str) -> str | None:
    """Devuelve el código de segmento aplicable o None.

    Sólo aplica a Intestino (duodeno_yeyuno / colon). Otros órganos devuelven None.
    """
    if organo != "Intestino":
        return None
    if _SEG_DUOD_YEY.search(desc):
        return "duodeno_yeyuno"
    if _SEG_COLON.search(desc):
        return "colon"
    if _SEG_ILEON.search(desc):
        return "duodeno_yeyuno"  # íleon se agrupa con duodeno-yeyuno
    return None


def _detect_lateralidad(desc: str, organo: str) -> str | None:
    """Devuelve 'izquierdo' / 'derecho' / 'bilateral' o None.

    Aplica a Riñones y Adrenales. Otros órganos devuelven None.
    Si el informe menciona ambos explícitamente, gana 'bilateral' (UNIFICADO).
    """
    if organo not in ("Riñones", "Adrenales"):
        return None
    izq = bool(_LAT_IZQ.search(desc))
    der = bool(_LAT_DER.search(desc))
    bil = bool(_LAT_BIL.search(desc))
    if bil and (izq or der):
        return "bilateral"
    if bil:
        return "bilateral"
    if izq and not der:
        return "izquierdo"
    if der and not izq:
        return "derecho"
    if izq and der:
        return "bilateral"
    return None


def _load_catalog() -> dict:
    """Carga VALUE_PROPOSALS desde el script de profiling (single source of truth)."""
    import importlib.util
    import sys as _sys
    from pathlib import Path as _P

    scripts_dir = _P(__file__).resolve().parent.parent.parent / "scripts"
    if "_f3_catalog" in _sys.modules:
        return _sys.modules["_f3_catalog"]

    spec = importlib.util.spec_from_file_location(
        "_f3_catalog", scripts_dir / "_profile_f3_dim_valores.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo cargar _profile_f3_dim_valores.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    _sys.modules["_f3_catalog"] = mod
    return mod


def _compile_proposals(value_proposals: dict) -> dict[tuple[str, str], list[tuple[str, "re.Pattern"]]]:
    """Pre-compila regex por (organo, atributo) para velocidad."""
    compiled: dict[tuple[str, str], list[tuple[str, "re.Pattern"]]] = {}
    for key, proposals in value_proposals.items():
        compiled[key] = [(canon, re.compile(pat, re.IGNORECASE)) for canon, pat in proposals]
    return compiled


def _build_atributos(
    silver_engine: Engine, raw_engine: Engine, *, actor: str = "build_silver",
) -> dict[str, Any]:
    """Fase 3: extrae atributos de silver_hallazgos via regex.

    Pipeline:
    1. Lee silver_hallazgos (poblado por F1/F2).
    2. Carga dim_organo, dim_organo_atributo, dim_segmento_anatomico,
       dim_valor_atributo en memoria (idempotente: asume bootstrap_f3 ya corrió).
    3. Para cada hallazgo: detecta segmento + lateralidad, luego itera sobre
       pares (organo, atributo) aplicables y extrae valores canónicos.
    4. Escribe silver_atributos_hallazgo (idempotente via UNIQUE INDEX
       coalesce-segmento).

    Asume: silver_hallazgos está poblado (F1/F2 OK) y bootstrap_f3() corrió
    (dim_atributo, dim_organo_atributo, dim_segmento_anatomico,
    dim_valor_atributo poblados).
    """
    t0 = time.monotonic()
    started_at = datetime.now()

    catalog = _load_catalog()
    VALUE_PROPOSALS = catalog.VALUE_PROPOSALS
    BINARY_ATRIBUTOS = catalog.BINARY_ATRIBUTOS
    NUMERIC_ATRIBUTOS = catalog.NUMERIC_ATRIBUTOS
    compiled_proposals = _compile_proposals(VALUE_PROPOSALS)

    # ─── Cargar dimensiones en memoria ───
    with silver_engine.begin() as conn:
        organo_id_map = {
            nombre: id_
            for id_, nombre in conn.execute(
                dim_organo.select().with_only_columns(
                    dim_organo.c.id, dim_organo.c.nombre_canonico
                )
            ).all()
        }
        # par_id_map[(organo_id, atributo_id, segmento_id|None)] = par_id
        par_id_map: dict[tuple[int, int, int | None], int] = {}
        for pid, org_id, attr_id, seg_id in conn.execute(
            dim_organo_atributo.select().with_only_columns(
                dim_organo_atributo.c.id,
                dim_organo_atributo.c.dim_organo_id,
                dim_organo_atributo.c.dim_atributo_id,
                dim_organo_atributo.c.dim_segmento_id,
            )
        ).all():
            par_id_map[(org_id, attr_id, seg_id)] = pid
        # seg_id_map[(organo_id, codigo)] = seg_id
        seg_id_map: dict[tuple[int, str], int] = {}
        for sid, org_id, codigo in conn.execute(
            dim_segmento_anatomico.select().with_only_columns(
                dim_segmento_anatomico.c.id,
                dim_segmento_anatomico.c.dim_organo_id,
                dim_segmento_anatomico.c.codigo,
            )
        ).all():
            seg_id_map[(org_id, codigo)] = sid
        # valor_id_map[(atributo_id, valor)] = valor_id
        valor_id_map: dict[tuple[int, str], int] = {}
        for vid, attr_id, valor in conn.execute(
            dim_valor_atributo.select().with_only_columns(
                dim_valor_atributo.c.id,
                dim_valor_atributo.c.atributo_id,
                dim_valor_atributo.c.valor,
            )
        ).all():
            valor_id_map[(attr_id, valor)] = vid
        # atributo_nombre_to_id
        atributo_id_map = {
            nombre: id_
            for id_, nombre in conn.execute(
                dim_atributo.select().with_only_columns(
                    dim_atributo.c.id, dim_atributo.c.nombre_canonico
                )
            ).all()
        }

    # ─── Leer silver_hallazgos ───
    with silver_engine.begin() as conn:
        hallazgos_rows = conn.execute(
            silver_hallazgos.select().with_only_columns(
                silver_hallazgos.c.hallazgo_id,
                silver_hallazgos.c.informe_id,
                silver_hallazgos.c.dim_organo_id,
                silver_hallazgos.c.descripcion,
            )
        ).all()

    organo_id_to_name = {v: k for k, v in organo_id_map.items()}

    # ─── Extraer atributos ───
    rows_to_insert: list[dict] = []
    n_hallazgos_with_attrs = 0
    n_attrs_extracted = 0
    n_unmatched: _Counter = _Counter()
    n_segmented: _Counter = _Counter()
    n_lateralidad: _Counter = _Counter()

    for hallazgo_id, informe_id, dim_organo_id, descripcion in hallazgos_rows:
        organo_nombre = organo_id_to_name.get(dim_organo_id)
        if organo_nombre is None:
            continue
        # Detectar segmento y lateralidad
        seg_codigo = _detect_segmento(descripcion, organo_nombre)
        lateralidad = _detect_lateralidad(descripcion, organo_nombre)
        if seg_codigo:
            n_segmented[seg_codigo] += 1
        if lateralidad:
            n_lateralidad[lateralidad] += 1
        seg_id = seg_id_map.get((dim_organo_id, seg_codigo)) if seg_codigo else None
        # Para Riñones/Adrenales: usar el segmento anatómico correspondiente.
        # Si no hay lateralidad explícita, asumimos bilateral (típico: "glándulas
        # de forma normal..." se aplica a ambas). Si es bilateral, expandimos a
        # 2 segmentos más abajo.
        seg_id_izq: int | None = None
        seg_id_der: int | None = None
        if organo_nombre in ("Riñones", "Adrenales"):
            cod_izq = "rinon_izquierdo" if organo_nombre == "Riñones" else "adrenal_izquierda"
            cod_der = "rinon_derecho" if organo_nombre == "Riñones" else "adrenal_derecha"
            seg_id_izq = seg_id_map.get((dim_organo_id, cod_izq))
            seg_id_der = seg_id_map.get((dim_organo_id, cod_der))
            if lateralidad == "izquierdo":
                seg_id = seg_id_izq
            elif lateralidad == "derecho":
                seg_id = seg_id_der
            # "bilateral" o None: seg_id queda None; abajo expandimos a ambos.

        # Buscar propuestas aplicables (organo_nombre, *)
        keys_to_try: list[tuple[str, str]] = [
            (organo_nombre, attr)
            for (org, attr) in compiled_proposals
            if org == organo_nombre
        ]
        if not keys_to_try:
            continue

        any_attr_extracted = False
        for organo_key, atributo_key in keys_to_try:
            attr_id = atributo_id_map.get(atributo_key)
            if attr_id is None:
                continue
            proposals = compiled_proposals[(organo_key, atributo_key)]
            for canon, pat in proposals:
                m = pat.search(descripcion)
                if not m:
                    continue
                # Resolver dim_organo_atributo_id por cada segmento a escribir.
                # Para Riñones/Adrenales bilateral: 1 row por segmento (izq + der).
                # Para unilateral: solo el seg_id resuelto arriba.
                # Para Intestino u otros: solo seg_id (puede ser None).
                segs_to_write: list[tuple[int | None, str | None]] = []
                if organo_nombre in ("Riñones", "Adrenales") and lateralidad in (None, "bilateral"):
                    if seg_id_izq is not None:
                        segs_to_write.append((seg_id_izq, "izquierdo"))
                    if seg_id_der is not None:
                        segs_to_write.append((seg_id_der, "derecho"))
                else:
                    segs_to_write.append((seg_id, lateralidad))
                # Si no hay segmentos resueltos, intentar fallback None (ej:
                # Intestino sin detección → cae en peristaltismo).
                if not segs_to_write:
                    segs_to_write = [(None, lateralidad)]
                # F3.2 fix: Intestino.peristaltismo tiene segmento=NULL en el par,
                # pero _detect_segmento siempre retorna "duodeno_yeyuno" o "colon"
                # cuando el texto los menciona. Esto impedía el lookup del par.
                # Solución: agregar fallback (None, lateralidad) para Intestino
                # además del seg_id detectado, de modo que peristaltismo (par con
                # segmento=None) siempre pueda matchear.
                if organo_nombre == "Intestino":
                    segs_to_write.append((None, lateralidad))

                texto_match = m.group(0)
                pos_inicio = m.start()
                pos_fin = m.end()
                valor_id = valor_id_map.get((attr_id, canon))
                valor_numerico = None
                if atributo_key == "fetos" and canon.isalpha():
                    num_map = {
                        "UNO": 1, "DOS": 2, "TRES": 3, "CUATRO": 4, "CINCO": 5,
                        "SEIS": 6, "SIETE": 7, "OCHO": 8, "NUEVE_O_MAS": 9,
                    }
                    valor_numerico = num_map.get(canon)

                wrote_for_this_attr = False
                for seg_for_row, lat_for_row in segs_to_write:
                    par_id = par_id_map.get((dim_organo_id, attr_id, seg_for_row))
                    if par_id is None:
                        continue
                    rows_to_insert.append({
                        "hallazgo_id": hallazgo_id,
                        "informe_id": informe_id,
                        "dim_organo_atributo_id": par_id,
                        "dim_organo_id": dim_organo_id,
                        "segmento_id": seg_for_row,
                        "lateralidad": lat_for_row,
                        "dim_valor_atributo_id": valor_id,
                        "valor_texto": canon,
                        "valor_canonico": canon,
                        "valor_numerico": valor_numerico,
                        "unidad": None,
                        "confianza": 1.0,
                        "metodo_extraccion": "regex_v1",
                        "texto_original": texto_match,
                        "pos_inicio": pos_inicio,
                        "pos_fin": pos_fin,
                    })
                    n_attrs_extracted += 1
                    wrote_for_this_attr = True
                if wrote_for_this_attr:
                    any_attr_extracted = True
                else:
                    n_unmatched[atributo_key] += 1
                break  # primer match por atributo

        if any_attr_extracted:
            n_hallazgos_with_attrs += 1

    # ─── Insert idempotente ───
    # El UNIQUE INDEX efectivo es (hallazgo_id, dim_organo_atributo_id,
    # COALESCE(segmento_id, -1)) — creado en silver_db.py/migrate(). SQLAlchemy
    # on_conflict_do_nothing requiere columnas reales (no acepta COALESCE),
    # así que delegamos al helper _upsert_ignore_coalesce que ejecuta SQL crudo.
    n_inserted = 0
    if rows_to_insert:
        from .silver_f3_dims import _upsert_ignore_coalesce
        n_inserted = _upsert_ignore_coalesce(
            silver_atributos_hallazgo, rows_to_insert, silver_engine,
            conflict_columns=["hallazgo_id", "dim_organo_atributo_id", "segmento_id"],
            null_sentinels={"segmento_id": -1},
        )

    duration_ms = int((time.monotonic() - t0) * 1000)
    finished_at = datetime.now()

    metrics = {
        "n_hallazgos_leidos": len(hallazgos_rows),
        "n_hallazgos_with_attrs": n_hallazgos_with_attrs,
        "n_atributos_extraidos": n_attrs_extracted,
        "n_atributos_insertados": n_inserted,
        "n_segmented": dict(n_segmented),
        "n_lateralidad": dict(n_lateralidad),
        "n_sin_par_resuelto": dict(n_unmatched),
        "duration_ms": duration_ms,
    }

    _log_run(silver_engine, "f3", started_at, finished_at, "ok",
             rows_read=len(hallazgos_rows),
             rows_written=n_inserted,
             rows_skipped=len(rows_to_insert) - n_inserted,
             duration_ms=duration_ms, actor=actor, notes=str(metrics))
    return metrics


# Backwards-compatible alias (build_f3 used as orchestrator below).
build_f3_extract = _build_atributos


def build_f3(
    silver_engine: Engine, raw_engine: Engine, *, actor: str = "build_silver",
) -> dict[str, Any]:
    """Orquestador F3: bootstrap dims + extracción.

    1. Aplica migraciones v3.0 pendientes (idempotente).
    2. bootstrap_f3() siembre dim_atributo, dim_organo_atributo,
       dim_segmento_anatomico.
    3. bootstrap_dim_valor_atributo() siembre dim_valor_atributo.
    4. _build_hallazgos() puebla silver_hallazgos desde raw.hallazgos
       (idempotente: INSERT ON CONFLICT DO NOTHING por hallazgo_id).
    5. _build_atributos() corre el extractor.
    """
    from .silver_db import migrate as _migrate
    from .silver_f3_dims import bootstrap_f3 as _bootstrap_f3
    from .silver_f3_dims import bootstrap_dim_valor_atributo as _bootstrap_dva

    t0 = time.monotonic()
    started_at = datetime.now()

    migrations = _migrate(silver_engine)
    bootstrap_counts = _bootstrap_f3(silver_engine)
    valor_counts = _bootstrap_dva(silver_engine)
    hallazgos_metrics = _build_hallazgos(silver_engine, raw_engine, actor=actor)
    extract_metrics = _build_atributos(silver_engine, raw_engine, actor=actor)

    duration_ms = int((time.monotonic() - t0) * 1000)
    finished_at = datetime.now()

    metrics = {
        "migrations": migrations,
        "bootstrap_dims_f3": bootstrap_counts,
        "bootstrap_dim_valor_atributo": valor_counts,
        "hallazgos": hallazgos_metrics,
        "extract": extract_metrics,
        "duration_ms": duration_ms,
    }
    return metrics


def _build_hallazgos(
    silver_engine: Engine, raw_engine: Engine, *, actor: str = "build_silver",
) -> dict[str, Any]:
    """Puebla silver_hallazgos desde raw.hallazgos.

    Idempotente (INSERT ON CONFLICT DO NOTHING por hallazgo_id).
    Resuelve organo_raw → dim_organo_id. Si el órgano no existe en dim_organo,
    crea el fallback a 'Gestación' (organo con es_gestacion_fallback=True).
    Actualiza n_atributos_extraidos al final si ya hay atributos extraídos.
    """
    t0 = time.monotonic()
    started_at = datetime.now()

    # 1. Cargar mapa organo_canonico → id
    with silver_engine.begin() as conn:
        organo_id_map: dict[str, int] = {}
        for oid, nombre in conn.execute(
            dim_organo.select().with_only_columns(
                dim_organo.c.id, dim_organo.c.nombre_canonico,
            )
        ).all():
            organo_id_map[nombre] = oid

    # 2. Leer raw.hallazgos
    with raw_engine.begin() as conn:
        raw_rows = conn.execute(
            raw_hallazgos.select().with_only_columns(
                raw_hallazgos.c.id,
                raw_hallazgos.c.informe_id,
                raw_hallazgos.c.organo,
                raw_hallazgos.c.descripcion,
                raw_hallazgos.c.estado,
                raw_hallazgos.c.orden,
                raw_hallazgos.c.hallazgo_hash,
            )
        ).all()

    # 3. Construir filas silver
    rows: list[dict] = []
    n_fallback = 0
    for hid, informe_id, organo_raw, descripcion, estado, orden, h_hash in raw_rows:
        organo_id = organo_id_map.get(organo_raw)
        es_fallback = False
        if organo_id is None:
            # Fallback a Gestación
            organo_id = organo_id_map.get("Gestación")
            es_fallback = True
            n_fallback += 1
        if organo_id is None:
            log.warning("raw hallazgo %s sin resolución de órgano: %r", hid, organo_raw)
            continue
        rows.append({
            "hallazgo_id": hid,
            "informe_id": informe_id,
            "dim_organo_id": organo_id,
            "estado": estado or "NORMAL",
            "orden": orden or 0,
            "descripcion": descripcion or "",
            "n_atributos_extraidos": 0,
            "longitud_caracteres": len(descripcion or ""),
            "hallazgo_hash": h_hash or "",
            "es_gestacion_fallback": es_fallback,
        })

    # 4. Insert idempotente
    n_inserted = 0
    if rows:
        dialect = "sqlite" if silver_engine.dialect.name == "sqlite" else "postgresql"
        insert_fn = sqlite_insert if dialect == "sqlite" else pg_insert
        chunk_size = 100
        for start in range(0, len(rows), chunk_size):
            chunk = rows[start:start + chunk_size]
            stmt = insert_fn(silver_hallazgos).values(chunk)
            stmt = stmt.on_conflict_do_nothing(index_elements=["hallazgo_id"])
            with silver_engine.begin() as conn:
                result = conn.execute(stmt)
            n_inserted += result.rowcount or 0

    duration_ms = int((time.monotonic() - t0) * 1000)
    finished_at = datetime.now()

    metrics = {
        "rows_read": len(raw_rows),
        "rows_written": n_inserted,
        "n_fallback_gestacion": n_fallback,
        "duration_ms": duration_ms,
    }

    _log_run(silver_engine, "f3_hallazgos", started_at, finished_at, "ok",
             rows_read=len(raw_rows), rows_written=n_inserted,
             rows_skipped=len(raw_rows) - n_inserted,
             duration_ms=duration_ms, actor=actor, notes=str(metrics))
    return metrics