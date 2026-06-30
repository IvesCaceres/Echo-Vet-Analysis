"""Engine factory, schema management y build functions para `gold.db`.

Capa Gold: 3 tablas denormalizadas + 2 VIEWs analíticas + gold_etl_runs.

Patrón idéntico a `silver_db.py`:
- `get_engine(project_root, *, db_kind)`
- `create_schema`, `reset_schema`, `drop_schema`

Build functions (cada una idempotente: DELETE + INSERT en 1 transacción):
- `build_gold_diagnosticos(conn)`: requiere ATTACH silver.db
- `build_gold_demografia(conn)`:   requiere ATTACH silver.db + raw.db
- `build_gold_hallazgos(conn)`:    requiere ATTACH silver.db
- `create_gold_views(conn)`:       NO requiere ATTACH (referencian solo gold_*)

Las funciones de build NO abren conexiones: reciben `conn` ya listo.
El CLI `scripts/build_gold.py` es responsable de:
1. Crear el engine
2. ATTACH de silver.db (y raw.db si phase incluye demografia)
3. Llamar a las build_*
4. Llamar a create_gold_views
5. DETACH / dispose
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine

from .models_gold import VIEW_DDL, metadata

load_dotenv()


# =============================================================================
# ENGINE FACTORY
# =============================================================================

def get_engine(project_root: Path, *, db_kind: str = "sqlite") -> Engine:
    """Devuelve un Engine para `gold.db` (SQLite, por defecto).

    Acepta `db_kind='postgres'` para que la migración a Postgres no requiera
    refactor. Si se pide postgres pero no hay `GOLD_PG_DSN` configurado,
    se lanza un error claro.
    """
    if db_kind == "sqlite":
        db_path = Path(project_root) / "gold.db"
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
        dsn = os.environ.get("GOLD_PG_DSN") or os.environ.get("PG_DSN")
        if not dsn:
            raise RuntimeError(
                "GOLD_PG_DSN (o PG_DSN) no está definido. Ver .env.example."
            )
        return create_engine(dsn, future=True, connect_args={"connect_timeout": 5})
    raise ValueError(f"db_kind inválido: {db_kind!r}")


# =============================================================================
# SCHEMA MANAGEMENT
# =============================================================================

def create_schema(engine: Engine) -> None:
    """Crea todas las tablas declaradas en `metadata` (idempotente).

    NO crea las VIEWs: eso lo hace `create_gold_views()`.
    """
    metadata.create_all(engine)


def drop_schema(engine: Engine) -> None:
    """Borra todas las tablas. Transaccional.

    NO borra las VIEWs automáticamente (SQLite las borra junto con las
    tablas al DROP TABLE). Llamar a `drop_gold_views()` antes si se
    quiere ser explícito.
    """
    with engine.begin() as conn:
        metadata.drop_all(conn)


def reset_schema(engine: Engine) -> None:
    """DROP + CREATE en una transacción atómica."""
    with engine.begin() as conn:
        metadata.drop_all(conn)
        metadata.create_all(conn)


# =============================================================================
# ATTACH / DETACH (cross-layer desde gold.db hacia silver.db / raw.db)
# =============================================================================

def attach_databases(
    conn,
    silver_path: Path | None = None,
    raw_path: Path | None = None,
) -> dict[str, bool]:
    """ATTACH silver.db (y opcionalmente raw.db) a la conexión actual.

    Devuelve dict {alias: attached_ok}. Es idempotente: si el alias ya está
    attachado (por una llamada previa en la misma conexión), no falla.

    IMPORTANTE: ATTACH es por-conexión en SQLite. Cuando la conexión se
    cierra, los aliases desaparecen. Power BI Desktop abre su propia
    conexión sin estos ATTACHes — por eso las VIEWs se diseñaron para
    referenciar SOLO tablas gold_* (no silver.*). Ver docstring del módulo.
    """
    results: dict[str, bool] = {}
    if silver_path is not None:
        try:
            conn.exec_driver_sql(
                f"ATTACH DATABASE '{Path(silver_path).as_posix()}' AS silver"
            )
            results["silver"] = True
        except Exception:
            # Si ya estaba attachado, SQLite lanza error. Es OK.
            results["silver"] = False
    if raw_path is not None:
        try:
            conn.exec_driver_sql(
                f"ATTACH DATABASE '{Path(raw_path).as_posix()}' AS raw"
            )
            results["raw"] = True
        except Exception:
            results["raw"] = False
    return results


def detach_databases(conn, *names: str) -> None:
    """DETACH bases de datos adjuntas (best-effort, ignora errores)."""
    for name in names:
        try:
            conn.exec_driver_sql(f"DETACH DATABASE {name}")
        except Exception:
            pass


# =============================================================================
# BUILD FUNCTIONS — DELETE + INSERT en una sola transacción
# =============================================================================

def build_gold_diagnosticos(conn) -> int:
    """Puebla gold_diagnosticos desde silver (DELETE+INSERT).

    Requiere `silver` ATTACH previo (vía `attach_databases`).
    Idempotente: borra todo antes de insertar.
    """
    conn.exec_driver_sql("DELETE FROM gold_diagnosticos")

    # ROW_NUMBER() sobre (conclusion_id, pos_inicio) marca el primer item
    # de cada conclusión como "primario en informe". Disponible en SQLite ≥ 3.25.
    sql = text("""
        INSERT INTO gold_diagnosticos (
            conclusion_item_id, informe_id, termino_canonico, tipo_item,
            categoria_clinica, organo_asociado, lateralidad,
            modificador_cualidad, modificador_distribucion, negado,
            confianza, anio, mes, es_primario_en_informe
        )
        SELECT
            sci.id,
            sci.informe_id,
            dtc.nombre_canonico,
            dtc.tipo_item,
            dtc.categoria_clinica,
            dtc.organo_asociado,
            sci.lateralidad,
            sci.modificador_cualidad,
            sci.modificador_distribucion,
            sci.negado,
            sci.confianza,
            CAST(strftime('%Y', si.fecha_parseada) AS INTEGER),
            CAST(strftime('%m', si.fecha_parseada) AS INTEGER),
            CASE WHEN ROW_NUMBER() OVER (
                PARTITION BY sci.conclusion_id ORDER BY sci.pos_inicio
            ) = 1 THEN 1 ELSE 0 END
        FROM silver.silver_conclusion_items sci
        JOIN silver.dim_termino_conclusion dtc
          ON dtc.id = sci.termino_conclusion_id
        JOIN silver.silver_informes si
          ON si.informe_id = sci.informe_id
        WHERE si.fecha_parseada IS NOT NULL
    """)
    result = conn.execute(sql)
    return int(result.rowcount or 0)


def build_gold_demografia(conn) -> int:
    """Puebla gold_demografia desde silver + raw (DELETE+INSERT).

    Requiere `silver` Y `raw` ATTACH previos. Cross-layer a raw.informes
    necesario para la columna `raza_raw` (raw no se denormaliza en Silver).
    Idempotente.
    """
    conn.exec_driver_sql("DELETE FROM gold_demografia")

    # trimestre: ((mes - 1) / 3) + 1 en INTEGER da 1..4
    sql = text("""
        INSERT INTO gold_demografia (
            informe_id, fecha, anio, mes, trimestre,
            especie_nombre, sexo_nombre, edad_categoria_nombre,
            estudio_nombre, estado_reproductivo_nombre,
            raza_raw, nombre_paciente, tutor,
            n_hallazgos, n_atributos_extraidos,
            n_items_diagnostico, n_items_etiologia, n_items_negativo
        )
        SELECT
            si.informe_id,
            si.fecha_parseada,
            CAST(strftime('%Y', si.fecha_parseada) AS INTEGER),
            CAST(strftime('%m', si.fecha_parseada) AS INTEGER),
            CAST((CAST(strftime('%m', si.fecha_parseada) AS INTEGER) - 1) / 3 + 1 AS INTEGER),
            COALESCE(de.nombre_canonico, '(sin especie)'),
            ds.nombre_canonico,
            dec.nombre,
            dest.nombre_canonico,
            der.nombre_canonico,
            ri.raza,
            si.nombre_paciente,
            si.tutor,
            COALESCE(h.cnt, 0),
            COALESCE(a.cnt, 0),
            COALESCE(d.cnt, 0),
            COALESCE(e.cnt, 0),
            COALESCE(n.cnt, 0)
        FROM silver.silver_informes si
        LEFT JOIN silver.dim_especie de ON de.id = si.dim_especie_id
        LEFT JOIN silver.dim_sexo ds ON ds.id = si.dim_sexo_id
        LEFT JOIN silver.dim_edad_categoria dec ON dec.id = si.dim_edad_categoria_id
        LEFT JOIN silver.dim_estudio dest ON dest.id = si.dim_estudio_id
        LEFT JOIN silver.dim_estado_reproductivo der
          ON der.id = si.dim_estado_reproductivo_id
        LEFT JOIN raw.informes ri ON ri.id = si.informe_id
        LEFT JOIN (
            SELECT informe_id, COUNT(*) AS cnt
            FROM silver.silver_hallazgos
            GROUP BY informe_id
        ) h ON h.informe_id = si.informe_id
        LEFT JOIN (
            SELECT informe_id, COUNT(*) AS cnt
            FROM silver.silver_atributos_hallazgo
            GROUP BY informe_id
        ) a ON a.informe_id = si.informe_id
        LEFT JOIN (
            SELECT sci.informe_id, COUNT(*) AS cnt
            FROM silver.silver_conclusion_items sci
            JOIN silver.dim_termino_conclusion dtc
              ON dtc.id = sci.termino_conclusion_id
            WHERE dtc.tipo_item = 'DIAGNOSTICO'
            GROUP BY sci.informe_id
        ) d ON d.informe_id = si.informe_id
        LEFT JOIN (
            SELECT sci.informe_id, COUNT(*) AS cnt
            FROM silver.silver_conclusion_items sci
            JOIN silver.dim_termino_conclusion dtc
              ON dtc.id = sci.termino_conclusion_id
            WHERE dtc.tipo_item = 'ETIOLOGIA'
            GROUP BY sci.informe_id
        ) e ON e.informe_id = si.informe_id
        LEFT JOIN (
            SELECT sci.informe_id, COUNT(*) AS cnt
            FROM silver.silver_conclusion_items sci
            JOIN silver.dim_termino_conclusion dtc
              ON dtc.id = sci.termino_conclusion_id
            WHERE dtc.tipo_item = 'NEGATIVO'
            GROUP BY sci.informe_id
        ) n ON n.informe_id = si.informe_id
        WHERE si.fecha_parseada IS NOT NULL
    """)
    result = conn.execute(sql)
    return int(result.rowcount or 0)


def build_gold_hallazgos(conn) -> int:
    """Puebla gold_hallazgos desde silver (DELETE+INSERT).

    Requiere `silver` ATTACH previo. Idempotente.
    """
    conn.exec_driver_sql("DELETE FROM gold_hallazgos")

    sql = text("""
        INSERT INTO gold_hallazgos (
            atributo_hallazgo_id, informe_id, hallazgo_id,
            organo_nombre, sistema, atributo_nombre,
            valor_nombre, valor_canonico, valor_numerico,
            segmento_nombre, lateralidad, estado_hallazgo, unidad
        )
        SELECT
            sah.id,
            sah.informe_id,
            sah.hallazgo_id,
            do.nombre_canonico,
            do.sistema,
            da.nombre_canonico,
            dva.valor,
            sah.valor_canonico,
            sah.valor_numerico,
            dsa.nombre_canonico,
            sah.lateralidad,
            sh.estado,
            sah.unidad
        FROM silver.silver_atributos_hallazgo sah
        JOIN silver.dim_organo do ON do.id = sah.dim_organo_id
        JOIN silver.dim_organo_atributo doa
          ON doa.id = sah.dim_organo_atributo_id
        JOIN silver.dim_atributo da ON da.id = doa.dim_atributo_id
        LEFT JOIN silver.dim_valor_atributo dva
          ON dva.id = sah.dim_valor_atributo_id
        LEFT JOIN silver.dim_segmento_anatomico dsa
          ON dsa.id = sah.segmento_id
        JOIN silver.silver_hallazgos sh
          ON sh.hallazgo_id = sah.hallazgo_id
    """)
    result = conn.execute(sql)
    return int(result.rowcount or 0)


# =============================================================================
# VIEW MANAGEMENT
# =============================================================================

def create_gold_views(conn) -> int:
    """DROP + CREATE las 2 VIEWs gold_* (idempotente).

    NO requiere ATTACH: las VIEWs referencian SOLO tablas gold_*.
    Devuelve el número de VIEWs creadas.
    """
    n_created = 0
    for view_name, ddl in VIEW_DDL.items():
        # DROP IF EXISTS primero (idempotencia)
        conn.exec_driver_sql(f"DROP VIEW IF EXISTS {view_name}")
        conn.exec_driver_sql(ddl)
        n_created += 1
    return n_created


def drop_gold_views(conn) -> int:
    """DROP las 2 VIEWs gold_* si existen. Devuelve cuántas se borraron."""
    n_dropped = 0
    for view_name in VIEW_DDL:
        result = conn.exec_driver_sql(
            f"DROP VIEW IF EXISTS {view_name}"
        )
        # rowcount no es confiable para DROP; usamos un check posterior
        n_dropped += 1
    return n_dropped


# =============================================================================
# ETL RUN LOGGING
# =============================================================================

def log_run(
    engine: Engine,
    phase: str,
    started_at: datetime,
    finished_at: datetime,
    status: str,
    *,
    rows_read: int = 0,
    rows_written: int = 0,
    rows_skipped: int = 0,
    rows_errored: int = 0,
    duration_ms: int = 0,
    actor: str = "build_gold",
    notes: str | None = None,
) -> int:
    """Registra una corrida en `gold_etl_runs`. Devuelve el id insertado."""
    sql = text("""
        INSERT INTO gold_etl_runs (
            phase, started_at, finished_at, status,
            rows_read, rows_written, rows_skipped, rows_errored,
            duration_ms, actor, notes
        ) VALUES (
            :phase, :started_at, :finished_at, :status,
            :rows_read, :rows_written, :rows_skipped, :rows_errored,
            :duration_ms, :actor, :notes
        )
    """)
    with engine.begin() as conn:
        result = conn.execute(sql, {
            "phase": phase,
            "started_at": started_at,
            "finished_at": finished_at,
            "status": status,
            "rows_read": rows_read,
            "rows_written": rows_written,
            "rows_skipped": rows_skipped,
            "rows_errored": rows_errored,
            "duration_ms": duration_ms,
            "actor": actor,
            "notes": notes,
        })
        # INSERT sin autoincrement explícito; usamos last_insert_rowid via SQL
        new_id = conn.exec_driver_sql(
            "SELECT last_insert_rowid()"
        ).scalar_one() if engine.dialect.name == "sqlite" else result.inserted_primary_key[0]
    return int(new_id)


# =============================================================================
# UTILIDADES PARA ANÁLISIS POST-BUILD
# =============================================================================

def get_table_counts(engine: Engine) -> dict[str, int]:
    """Devuelve {tabla_o_vista: n_filas} para las 5 entidades Gold."""
    counts: dict[str, int] = {}
    tables = ("gold_diagnosticos", "gold_demografia", "gold_hallazgos")
    views = ("gold_coocurrencias", "gold_tendencias")
    with engine.begin() as conn:
        for t in tables:
            counts[t] = int(conn.exec_driver_sql(
                f"SELECT COUNT(*) FROM {t}"
            ).scalar_one() or 0)
        for v in views:
            counts[v] = int(conn.exec_driver_sql(
                f"SELECT COUNT(*) FROM {v}"
            ).scalar_one() or 0)
    return counts


def get_table_exists(engine: Engine, name: str) -> bool:
    """Portable: ¿existe la tabla o vista `name`?"""
    dialect = engine.dialect.name
    with engine.begin() as conn:
        if dialect == "sqlite":
            rows = conn.exec_driver_sql(
                "SELECT type FROM sqlite_master WHERE name = :n"
            ).params(n=name).all()
            return bool(rows)
        # PostgreSQL
        rows = conn.exec_driver_sql(
            "SELECT table_type FROM information_schema.tables "
            "WHERE table_name = :n"
        ).params(n=name).all()
        return bool(rows)


__all__ = [
    # engine + schema
    "get_engine",
    "create_schema",
    "drop_schema",
    "reset_schema",
    # ATTACH
    "attach_databases",
    "detach_databases",
    # build
    "build_gold_diagnosticos",
    "build_gold_demografia",
    "build_gold_hallazgos",
    "create_gold_views",
    "drop_gold_views",
    # ops
    "log_run",
    "get_table_counts",
    "get_table_exists",
]