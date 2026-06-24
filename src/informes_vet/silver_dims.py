"""Bootstrap de dimensiones base para la capa SILVER.

Idempotente: cada INSERT usa `INSERT ... ON CONFLICT DO NOTHING` (vía
`sqlite_insert`/`pg_insert`) sobre las columnas UNIQUE de cada dimensión.
Re-correr el bootstrap produce el mismo estado.

Fase 1 siembra SOLO las 6 dimensiones base:
- dim_organo           (16 filas: 15 órganos canónicos + Gestación)
- dim_especie          (9 filas canónicas)
- dim_sexo             (3 filas: Hembra/Macho/Indeterminado)
- dim_estado_reproductivo (4 filas: Entero/Castrado/OVH/No especificado)
- dim_estudio          (8 filas canónicas)
- dim_edad_categoria   (5 filas: Cachorro/Juvenil/Adulto/Maduro/Geriátrico)

Las otras dimensiones (dim_atributo, dim_organo_atributo, dim_raza) entran
en F3 (catálogo clínico) y F2 (mapas).
"""

from __future__ import annotations

import logging
from typing import Iterable

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine

from .models_silver import (
    dim_edad_categoria,
    dim_especie,
    dim_estado_reproductivo,
    dim_estudio,
    dim_organo,
    dim_sexo,
)

log = logging.getLogger(__name__)


# =============================================================================
# SEEDS
# =============================================================================

# Sistema agrupa por categoría clínica (no estricta taxonomía anatómica).
# Sirve para filtrar/organizar en Gold.
_ORGANOS_SEED: list[dict] = [
    # Tracto urinario
    {"nombre_canonico": "Vejiga",            "sistema": "urinario",       "es_gestacion_fallback": False},
    {"nombre_canonico": "Riñones",           "sistema": "urinario",       "es_gestacion_fallback": False},
    {"nombre_canonico": "Adrenales",         "sistema": "urinario",       "es_gestacion_fallback": False},
    # Reproductivo
    {"nombre_canonico": "Próstata",          "sistema": "reproductivo",   "es_gestacion_fallback": False},
    {"nombre_canonico": "Útero",             "sistema": "reproductivo",   "es_gestacion_fallback": False},
    {"nombre_canonico": "Ovarios",           "sistema": "reproductivo",   "es_gestacion_fallback": False},
    {"nombre_canonico": "Testículos",        "sistema": "reproductivo",   "es_gestacion_fallback": False},
    # Digestivo
    {"nombre_canonico": "Hígado",            "sistema": "digestivo",      "es_gestacion_fallback": False},
    {"nombre_canonico": "Vesícula",          "sistema": "digestivo",      "es_gestacion_fallback": False},
    {"nombre_canonico": "Bazo",              "sistema": "digestivo",      "es_gestacion_fallback": False},
    {"nombre_canonico": "Estómago",          "sistema": "digestivo",      "es_gestacion_fallback": False},
    {"nombre_canonico": "Intestino",         "sistema": "digestivo",      "es_gestacion_fallback": False},
    {"nombre_canonico": "Páncreas",          "sistema": "digestivo",      "es_gestacion_fallback": False},
    {"nombre_canonico": "Cavidad abdominal", "sistema": "digestivo",      "es_gestacion_fallback": False},
    # Linfático
    {"nombre_canonico": "Linfonodos",        "sistema": "linfatico",      "es_gestacion_fallback": False},
    # Fallback gestacional (caso sin órganos canónicos)
    {"nombre_canonico": "Gestación",         "sistema": "gestacional",    "es_gestacion_fallback": True},
]

_ESPECIES_SEED: list[dict] = [
    {"nombre_canonico": "Canino",  "nombre_cientifico": "Canis lupus familiaris",  "es_exotica": False, "fuente": "seed_v1"},
    {"nombre_canonico": "Felino",  "nombre_cientifico": "Felis catus",             "es_exotica": False, "fuente": "seed_v1"},
    {"nombre_canonico": "Conejo",  "nombre_cientifico": "Oryctolagus cuniculus",   "es_exotica": True,  "fuente": "seed_v1"},
    {"nombre_canonico": "Cobaya",  "nombre_cientifico": "Cavia porcellus",         "es_exotica": True,  "fuente": "seed_v1"},
    {"nombre_canonico": "Hurón",   "nombre_cientifico": "Mustela putorius furo",   "es_exotica": True,  "fuente": "seed_v1"},
    {"nombre_canonico": "Hámster", "nombre_cientifico": "Cricetinae",              "es_exotica": True,  "fuente": "seed_v1"},
    {"nombre_canonico": "Erizo",   "nombre_cientifico": "Erinaceinae",             "es_exotica": True,  "fuente": "seed_v1"},
    {"nombre_canonico": "Ratón",   "nombre_cientifico": "Mus musculus",            "es_exotica": True,  "fuente": "seed_v1"},
    {"nombre_canonico": "Cuy",     "nombre_cientifico": "Cavia porcellus",         "es_exotica": True,  "fuente": "seed_v1"},
]

_SEXO_SEED: list[dict] = [
    {"nombre_canonico": "Hembra",        "codigo": "H"},
    {"nombre_canonico": "Macho",         "codigo": "M"},
    {"nombre_canonico": "Indeterminado", "codigo": "I"},
]

_ESTADO_REPRODUCTIVO_SEED: list[dict] = [
    {"nombre_canonico": "Entero",          "codigo": "ENT"},
    {"nombre_canonico": "Castrado",        "codigo": "CAS"},
    {"nombre_canonico": "OVH",             "codigo": "OVH"},
    {"nombre_canonico": "No especificado", "codigo": "NE"},
]

# dim_estudio incluye jerarquía (parent_id NULL = raíz). Las variantes
# con mayúscula inconsistente o con sufijos ('Rodilla Derecha', 'Hombro')
# se mapean a "Otro" en F2.
_ESTUDIO_SEED: list[dict] = [
    {"nombre_canonico": "Abdominal",         "abreviatura": "ABD",  "parent_nombre": None},
    {"nombre_canonico": "Gestacional",      "abreviatura": "GEST", "parent_nombre": "Abdominal"},
    {"nombre_canonico": "Reproductivo",     "abreviatura": "REPRO","parent_nombre": "Abdominal"},
    {"nombre_canonico": "Cervical",         "abreviatura": "CERV", "parent_nombre": None},
    {"nombre_canonico": "Partes blandas",   "abreviatura": "PB",   "parent_nombre": None},
    {"nombre_canonico": "Musculoesquelético", "abreviatura": "ME", "parent_nombre": None},
    {"nombre_canonico": "Ocular",           "abreviatura": "OCU",  "parent_nombre": None},
    {"nombre_canonico": "Otro",             "abreviatura": "OTRO", "parent_nombre": None},
]

_EDAD_CATEGORIA_SEED: list[dict] = [
    {"codigo": "CACH", "nombre": "Cachorro",   "min_meses": 0,   "max_meses": 12},
    {"codigo": "JUV",  "nombre": "Juvenil",    "min_meses": 12,  "max_meses": 24},
    {"codigo": "ADU",  "nombre": "Adulto",     "min_meses": 24,  "max_meses": 96},
    {"codigo": "MAD",  "nombre": "Maduro",     "min_meses": 96,  "max_meses": 132},
    {"codigo": "GER",  "nombre": "Geriátrico", "min_meses": 132, "max_meses": None},
]


# =============================================================================
# HELPERS
# =============================================================================

def _upsert_ignore(table, rows: Iterable[dict], engine: Engine, *, index_elements: list[str]) -> int:
    """Inserta filas ignorando conflictos por `index_elements`.

    Devuelve el número de filas afectadas (SQLite: 1 por insert real; PG: 1).
    Para idempotencia usamos el patrón ON CONFLICT DO NOTHING sobre el subset
    de columnas UNIQUE de cada dimensión.
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


def _upsert_estudio(engine: Engine) -> int:
    """dim_estudio tiene jerarquía (parent_id). Insertamos en dos pasadas:
    primero las raíces (parent_id NULL), luego los hijos resolviendo parent_id
    por nombre. Idempotente.
    """
    affected = 0
    # Pasada 1: raíces
    raices = [r for r in _ESTUDIO_SEED if r["parent_nombre"] is None]
    affected += _upsert_ignore(
        dim_estudio,
        [{"nombre_canonico": r["nombre_canonico"], "abreviatura": r["abreviatura"]} for r in raices],
        engine,
        index_elements=["nombre_canonico"],
    )
    # Pasada 2: hijos
    hijos = [r for r in _ESTUDIO_SEED if r["parent_nombre"] is not None]
    with engine.begin() as conn:
        for r in hijos:
            parent_id = conn.execute(
                dim_estudio.select().where(dim_estudio.c.nombre_canonico == r["parent_nombre"])
            ).first()
            if parent_id is None:
                log.warning("parent_id no resuelto para %s", r["nombre_canonico"])
                continue
            dialect = "sqlite" if engine.dialect.name == "sqlite" else "postgresql"
            insert_fn = sqlite_insert if dialect == "sqlite" else pg_insert
            stmt = insert_fn(dim_estudio).values(
                nombre_canonico=r["nombre_canonico"],
                abreviatura=r["abreviatura"],
                parent_id=parent_id[0],
            )
            stmt = stmt.on_conflict_do_nothing(index_elements=["nombre_canonico"])
            result = conn.execute(stmt)
            affected += result.rowcount or 0
    return affected


# =============================================================================
# API PÚBLICA
# =============================================================================

def bootstrap_basico(engine: Engine) -> dict[str, int]:
    """Siembra las 6 dimensiones base. Idempotente.

    Returns: dict con el número de filas insertadas (no actualizadas) por
    dimensión. Útil para logging y validación de la Fase 1.
    """
    counts: dict[str, int] = {}

    counts["dim_organo"] = _upsert_ignore(
        dim_organo, _ORGANOS_SEED, engine, index_elements=["nombre_canonico"]
    )
    counts["dim_especie"] = _upsert_ignore(
        dim_especie, _ESPECIES_SEED, engine, index_elements=["nombre_canonico"]
    )
    counts["dim_sexo"] = _upsert_ignore(
        dim_sexo, _SEXO_SEED, engine, index_elements=["nombre_canonico"]
    )
    counts["dim_estado_reproductivo"] = _upsert_ignore(
        dim_estado_reproductivo, _ESTADO_REPRODUCTIVO_SEED, engine,
        index_elements=["nombre_canonico"],
    )
    counts["dim_estudio"] = _upsert_estudio(engine)
    counts["dim_edad_categoria"] = _upsert_ignore(
        dim_edad_categoria, _EDAD_CATEGORIA_SEED, engine, index_elements=["codigo"]
    )

    return counts