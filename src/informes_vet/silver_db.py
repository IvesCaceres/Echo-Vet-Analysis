"""Engine factory, schema management y UPSERT portable para `silver.db`.

Sigue el mismo patrón que `db.py` (capa RAW): `get_engine`, `create_schema`,
`reset_schema`. Las FKs cross-DB hacia RAW son LÓGICAS, validadas por el ETL.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from .models_silver import metadata

load_dotenv()


def get_engine(project_root: Path, *, db_kind: str = "sqlite") -> Engine:
    """Devuelve un Engine para `silver.db` (SQLite, por defecto).

    Acepta `db_kind='postgres'` para que la migración a Postgres no requiera
    refactor. Si se pide postgres pero no hay `SILVER_PG_DSN` configurado,
    se lanza un error claro.
    """
    if db_kind == "sqlite":
        db_path = Path(project_root) / "silver.db"
        engine = create_engine(
            f"sqlite:///{db_path.as_posix()}",
            future=True,
        )

        @event.listens_for(engine, "connect")
        def _enable_fk(dbapi_conn, _record):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

        return engine
    if db_kind == "postgres":
        dsn = os.environ.get("SILVER_PG_DSN") or os.environ.get("PG_DSN")
        if not dsn:
            raise RuntimeError(
                "SILVER_PG_DSN (o PG_DSN) no está definido. Ver .env.example."
            )
        return create_engine(dsn, future=True, connect_args={"connect_timeout": 5})
    raise ValueError(f"db_kind inválido: {db_kind!r}")


def create_schema(engine: Engine) -> None:
    """Crea todas las tablas declaradas en `metadata` (idempotente)."""
    metadata.create_all(engine)


def reset_schema(engine: Engine) -> None:
    """DROP + CREATE en una transacción atómica."""
    with engine.begin() as conn:
        metadata.drop_all(conn)
        metadata.create_all(conn)


# =============================================================================
# MIGRACIONES v2.1 (Fase 2.1 — Data Quality)
# =============================================================================
#
# Las migraciones son idempotentes y portables SQLite <-> PostgreSQL. Cada
# migración verifica primero si el cambio ya fue aplicado (chequeando la
# existencia de la columna) y, si no, ejecuta el ALTER correspondiente.
#
# Convenir:
#   - Las migraciones NO pierden datos.
#   - Las migraciones NO usan DROP COLUMN (no es trivialmente reversible en
#     SQLite pre-3.35; para revertir hay que reset_schema completo).
#   - Las migraciones quedan registradas en silver_etl_runs (actor='migrate')
#     para auditoría.

_MIGRATIONS: list[dict] = [
    {
        # v2.1: añadir edad_parse_ok a silver_informes para distinguir "no
        # parseado" (False) de "parseado correctamente" (True). Cobertura
        # objetivo: >=99% True.
        "version": "v2.1",
        "name": "add_edad_parse_ok",
        "check": "edad_parse_ok",
        "table": "silver_informes",
        "ddl_sqlite": "ALTER TABLE silver_informes ADD COLUMN edad_parse_ok BOOLEAN NOT NULL DEFAULT 0",
        "ddl_postgres": "ALTER TABLE silver_informes ADD COLUMN edad_parse_ok BOOLEAN NOT NULL DEFAULT FALSE",
    },
    {
        # v3.0 F3: añadir columnas para soportar F3 (extracción de atributos).
        # - segmento_id: NULL para hallazgos sin segmento anatómico (la mayoría);
        #   no-NULL para Intestino (duodeno_yeyuno vs colon) y Riñones/Adrenales
        #   (izq vs der). FK lógica hacia dim_segmento_anatomico.id.
        # - lateralidad: NULL para hallazgos sin lateralidad explícita; uno de
        #   {'izquierdo', 'derecho', 'bilateral'} cuando aplica.
        # - dim_valor_atributo_id: FK opcional hacia dim_valor_atributo.id
        #   cuando se asigna un valor canónico. NULL para hallazgos pendientes
        #   de mapeo (silver_atributos_hallazgo como staging).
        "version": "v3.0",
        "name": "add_atributo_segmento_lateralidad",
        "check": "segmento_id",
        "table": "silver_atributos_hallazgo",
        "ddl_sqlite": (
            "ALTER TABLE silver_atributos_hallazgo "
            "ADD COLUMN segmento_id INTEGER"
        ),
        "ddl_postgres": (
            "ALTER TABLE silver_atributos_hallazgo "
            "ADD COLUMN segmento_id INTEGER"
        ),
    },
    {
        # v3.0 F3 (parte 2): añadir lateralidad y FK a dim_valor_atributo.
        "version": "v3.0",
        "name": "add_atributo_lateralidad_y_valor_fk",
        "check": "lateralidad",
        "table": "silver_atributos_hallazgo",
        "ddl_sqlite": (
            "ALTER TABLE silver_atributos_hallazgo "
            "ADD COLUMN lateralidad VARCHAR(16)"
        ),
        "ddl_postgres": (
            "ALTER TABLE silver_atributos_hallazgo "
            "ADD COLUMN lateralidad VARCHAR(16)"
        ),
    },
    {
        # v3.0 F3 (parte 3): dim_valor_atributo_id FK.
        "version": "v3.0",
        "name": "add_atributo_dim_valor_fk",
        "check": "dim_valor_atributo_id",
        "table": "silver_atributos_hallazgo",
        "ddl_sqlite": (
            "ALTER TABLE silver_atributos_hallazgo "
            "ADD COLUMN dim_valor_atributo_id INTEGER"
        ),
        "ddl_postgres": (
            "ALTER TABLE silver_atributos_hallazgo "
            "ADD COLUMN dim_valor_atributo_id INTEGER"
        ),
    },
    {
        # v5.0 F5: marcar el bloque "Recreate silver_conclusion_items (Opción
        # C)" para que migrate() ejecute el DROP+CREATE. La detección real de
        # "ya está aplicado" se hace comprobando la columna
        # `termino_conclusion_id`. Si existe → Opción C ya aplicada → skip.
        # Si NO existe → tabla en esquema viejo → DROP+CREATE.
        "version": "v5.0",
        "name": "recreate_silver_conclusion_items_opcion_c",
        "check": "termino_conclusion_id",
        "table": "silver_conclusion_items",
        # DDL vacío — el bloque especial al final de migrate() maneja DROP+CREATE.
        "ddl_sqlite": "",
        "ddl_postgres": "",
    },
]


def _column_exists(engine: Engine, table: str, column: str) -> bool:
    """Portable check: ¿la columna `column` existe en `table`?"""
    dialect = engine.dialect.name
    with engine.begin() as conn:
        if dialect == "sqlite":
            rows = conn.exec_driver_sql(
                f"PRAGMA table_info({table})"
            ).all()
            return any(r[1] == column for r in rows)
        # PostgreSQL
        rows = conn.exec_driver_sql(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ).params(t=table, c=column).all()
        return bool(rows)


def _index_exists(engine: Engine, index_name: str) -> bool:
    dialect = engine.dialect.name
    with engine.begin() as conn:
        if dialect == "sqlite":
            # SQLite no soporta bind params para nombres de objetos en PRAGMA
            # ni en sqlite_master. Usamos string formatting con quoting seguro.
            rows = conn.exec_driver_sql(
                f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'"
            ).all()
            return bool(rows)
        # PostgreSQL
        rows = conn.exec_driver_sql(
            "SELECT indexname FROM pg_indexes WHERE indexname = :n"
        ).params(n=index_name).all()
        return bool(rows)


def migrate(engine: Engine) -> list[dict]:
    """Aplica las migraciones pendientes de Silver.

    Devuelve lista con el resultado por migración:
    [{"version": "v3.0", "name": "...", "applied": True/False}, ...]
    """
    results: list[dict] = []
    for mig in _MIGRATIONS:
        already = _column_exists(engine, mig["table"], mig["check"])
        if already:
            results.append({
                "version": mig["version"],
                "name": mig["name"],
                "applied": False,
                "reason": "already_applied",
            })
            continue
        ddl = mig["ddl_sqlite"] if engine.dialect.name == "sqlite" else mig["ddl_postgres"]
        with engine.begin() as conn:
            conn.exec_driver_sql(ddl)
        results.append({
            "version": mig["version"],
            "name": mig["name"],
            "applied": True,
            "ddl": ddl,
        })

    # ─── UNIQUE INDEX con COALESCE para soportar NULL como "ausencia" ───
    # En SQLite/Postgres, dos NULL no son iguales bajo UNIQUE → no podemos
    # usar UNIQUE(hallazgo_id, dim_organo_atributo_id, segmento_id) directamente.
    # Solución portable: índice único sobre (hallazgo_id, dim_organo_atributo_id,
    # COALESCE(segmento_id, -1)). Si dos filas tienen el mismo (hallazgo_id,
    # dim_organo_atributo_id) y ambas segmento_id NULL, ambas tendrán
    # COALESCE=−1 y violarán el índice → exactamente el comportamiento que
    # queremos (no duplicados cuando no hay segmento).
    idx_name = "uq_silver_attr_hazgo_oatrib_seg"
    if not _index_exists(engine, idx_name):
        ddl = (
            f"CREATE UNIQUE INDEX {idx_name} "
            f"ON silver_atributos_hallazgo "
            f"(hallazgo_id, dim_organo_atributo_id, COALESCE(segmento_id, -1))"
        )
        with engine.begin() as conn:
            conn.exec_driver_sql(ddl)
        results.append({
            "version": "v3.0",
            "name": "uq_silver_attr_coalesce_segmento",
            "applied": True,
            "ddl": ddl,
        })
    else:
        results.append({
            "version": "v3.0",
            "name": "uq_silver_attr_coalesce_segmento",
            "applied": False,
            "reason": "already_applied",
        })

    # Misma idea para dim_organo_atributo: el UNIQUE(organo_id, atributo_id)
    # se reemplaza por (organo_id, atributo_id, COALESCE(segmento_id, -1))
    # para soportar pares del mismo (organo, atributo) en distintos segmentos.
    idx_name = "uq_dim_organo_atributo_seg"
    if not _index_exists(engine, idx_name):
        ddl = (
            f"CREATE UNIQUE INDEX {idx_name} "
            f"ON dim_organo_atributo "
            f"(dim_organo_id, dim_atributo_id, COALESCE(dim_segmento_id, -1))"
        )
        with engine.begin() as conn:
            conn.exec_driver_sql(ddl)
        results.append({
            "version": "v3.0",
            "name": "uq_dim_organo_atributo_coalesce_segmento",
            "applied": True,
            "ddl": ddl,
        })
    else:
        results.append({
            "version": "v3.0",
            "name": "uq_dim_organo_atributo_coalesce_segmento",
            "applied": False,
            "reason": "already_applied",
        })

    # ─── v5.0 F5 — Recreate silver_conclusion_items (Opción C) ───────────
    # Si la columna `termino_conclusion_id` NO existe, la tabla está en el
    # esquema viejo (v3.x): DROP + CREATE con el nuevo esquema.
    # Si existe → ya migrado → no-op.
    # Esta estrategia DROP+CREATE es segura porque el contenido se reconstruye
    # desde RAW en cada build_f5() (la tabla es staging derivable).
    if not _column_exists(engine, "silver_conclusion_items", "termino_conclusion_id"):
        dialect = engine.dialect.name
        if dialect == "sqlite":
            ddl_drop = "DROP TABLE IF EXISTS silver_conclusion_items"
            ddl_create = """
                CREATE TABLE silver_conclusion_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conclusion_id INTEGER NOT NULL,
                    informe_id INTEGER NOT NULL,
                    termino_conclusion_id INTEGER NOT NULL
                        REFERENCES dim_termino_conclusion(id),
                    lateralidad VARCHAR(16),
                    modificador_cualidad VARCHAR(32),
                    modificador_distribucion VARCHAR(32),
                    negado BOOLEAN NOT NULL DEFAULT 0,
                    pos_inicio INTEGER NOT NULL,
                    pos_fin INTEGER NOT NULL,
                    termino_detectado VARCHAR(128) NOT NULL,
                    confianza REAL NOT NULL DEFAULT 1.0,
                    metodo_extraccion VARCHAR(32) NOT NULL DEFAULT 'REGEX_RULE',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CHECK (lateralidad IS NULL OR lateralidad IN
                        ('bilateral','izquierdo','derecho','ambos','unilateral')),
                    CHECK (pos_fin > pos_inicio),
                    CHECK (confianza >= 0.0 AND confianza <= 1.0)
                )
            """
        else:
            ddl_drop = "DROP TABLE IF EXISTS silver_conclusion_items"
            ddl_create = """
                CREATE TABLE silver_conclusion_items (
                    id SERIAL PRIMARY KEY,
                    conclusion_id INTEGER NOT NULL,
                    informe_id INTEGER NOT NULL,
                    termino_conclusion_id INTEGER NOT NULL
                        REFERENCES dim_termino_conclusion(id),
                    lateralidad VARCHAR(16),
                    modificador_cualidad VARCHAR(32),
                    modificador_distribucion VARCHAR(32),
                    negado BOOLEAN NOT NULL DEFAULT FALSE,
                    pos_inicio INTEGER NOT NULL,
                    pos_fin INTEGER NOT NULL,
                    termino_detectado VARCHAR(128) NOT NULL,
                    confianza REAL NOT NULL DEFAULT 1.0,
                    metodo_extraccion VARCHAR(32) NOT NULL DEFAULT 'REGEX_RULE',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CHECK (lateralidad IS NULL OR lateralidad IN
                        ('bilateral','izquierdo','derecho','ambos','unilateral')),
                    CHECK (pos_fin > pos_inicio),
                    CHECK (confianza >= 0.0 AND confianza <= 1.0)
                )
            """
        with engine.begin() as conn:
            conn.exec_driver_sql(ddl_drop)
            conn.exec_driver_sql(ddl_create)
        results.append({
            "version": "v5.0",
            "name": "recreate_silver_conclusion_items_opcion_c",
            "applied": True,
            "ddl": ddl_drop + ";\n" + ddl_create,
        })
    else:
        results.append({
            "version": "v5.0",
            "name": "recreate_silver_conclusion_items_opcion_c",
            "applied": False,
            "reason": "already_applied",
        })

    # ─── v5.0 — UNIQUE INDEX para idempotencia ───────────────────────────
    # silver_conclusion_items UNIQUE INDEX:
    # (conclusion_id, termino_conclusion_id, pos_inicio, pos_fin)
    # Decisión de diseño: modificador_cualidad y modificador_distribucion
    # NO entran en la clave (pueden cambiar por re-análisis sin afectar la
    # identidad lógica del item). La clave estable es (conclusión, término,
    # posición en el texto).
    idx_name = "uq_silver_conc_items_unique"
    if not _index_exists(engine, idx_name):
        ddl = (
            f"CREATE UNIQUE INDEX {idx_name} "
            f"ON silver_conclusion_items "
            f"(conclusion_id, termino_conclusion_id, pos_inicio, pos_fin)"
        )
        with engine.begin() as conn:
            conn.exec_driver_sql(ddl)
        results.append({
            "version": "v5.0",
            "name": "uq_silver_conclusion_items",
            "applied": True,
            "ddl": ddl,
        })
    else:
        results.append({
            "version": "v5.0",
            "name": "uq_silver_conclusion_items",
            "applied": False,
            "reason": "already_applied",
        })

    return results