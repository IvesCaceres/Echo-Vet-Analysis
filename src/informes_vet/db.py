"""Engine factory, schema management, UPSERT portable y registro de errores."""

from __future__ import annotations

import os
import traceback
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine

from .models import errores_ingesta, metadata

load_dotenv()

# Las credenciales NO se hardcodean. Deben estar en `.env` como PG_DSN.
# Ver `.env.example` para la estructura esperada. Si no está definida y
# se usa --db postgres, se lanza un error claro.
_REQUIRED_PG_DSN_MSG = (
    "PG_DSN no está definido. Crea un archivo .env en la raíz con la "
    "variable PG_DSN=postgresql+psycopg://USER:PASS@HOST:PORT/DBNAME. "
    "Ver .env.example para la estructura."
)


def get_engine(db_kind: str, project_root: Path) -> Engine:
    """Devuelve un Engine para `db_kind` ('sqlite' o 'postgres')."""
    if db_kind == "sqlite":
        db_path = Path(project_root) / "informes.db"
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
        dsn = os.environ.get("PG_DSN")
        if not dsn:
            raise RuntimeError(_REQUIRED_PG_DSN_MSG)
        engine = create_engine(dsn, future=True, connect_args={"connect_timeout": 5})
        return engine
    raise ValueError(f"db_kind inválido: {db_kind!r}")


def create_schema(engine: Engine) -> None:
    """Crea todas las tablas declaradas en `metadata`."""
    metadata.create_all(engine)


def drop_schema(engine: Engine) -> None:
    """Borra todas las tablas. Transaccional."""
    with engine.begin() as conn:
        metadata.drop_all(conn)


def reset_schema(engine: Engine) -> None:
    """DROP + CREATE en una transacción atómica."""
    with engine.begin() as conn:
        metadata.drop_all(conn)
        metadata.create_all(conn)


def upsert_informe(conn, record: dict) -> int | None:
    """Inserta o ignora un informe por `sha256`. Devuelve el id o None si fue duplicado.

    Usa RETURNING id para distinguir inserciones reales de conflictos: si la fila
    ya existía, el INSERT ... ON CONFLICT DO NOTHING no retorna nada y devolvemos
    None. Si se insertó, RETURNING entrega el id nuevo.
    """
    informe_row = {k: v for k, v in record.items() if k not in ("hallazgos", "conclusiones_texto")}
    informes_tbl = metadata.tables["informes"]
    if conn.dialect.name == "postgresql":
        stmt = (
            pg_insert(informes_tbl)
            .values(**informe_row)
            .on_conflict_do_nothing(index_elements=["sha256"])
            .returning(informes_tbl.c.id)
        )
    else:
        stmt = (
            sqlite_insert(informes_tbl)
            .values(**informe_row)
            .on_conflict_do_nothing(index_elements=["sha256"])
            .returning(informes_tbl.c.id)
        )
    result = conn.execute(stmt)
    row = result.first()
    return int(row[0]) if row else None


def insert_hallazgos(conn, informe_id: int, hallazgos: list[dict]) -> int:
    if not hallazgos:
        return 0
    rows = [
        {
            "informe_id": informe_id,
            "organo": h["organo"],
            "descripcion": h["descripcion"],
            "estado": h.get("estado"),
            "orden": h.get("orden", 0),
            "hallazgo_hash": h["hallazgo_hash"],
        }
        for h in hallazgos
    ]
    conn.execute(metadata.tables["hallazgos"].insert(), rows)
    return len(rows)


def insert_conclusion(conn, informe_id: int, texto_completo: str) -> int:
    if not texto_completo or not texto_completo.strip():
        return 0
    conn.execute(
        metadata.tables["conclusiones"].insert().values(
            informe_id=informe_id, texto_completo=texto_completo.strip()
        )
    )
    return 1


def log_error(engine: Engine, archivo: str, ruta: str, exc: BaseException) -> None:
    """Persiste el error en la tabla `errores_ingesta` (best-effort)."""
    try:
        with engine.begin() as conn:
            conn.execute(
                errores_ingesta.insert().values(
                    archivo=archivo,
                    ruta=ruta,
                    error=f"{type(exc).__name__}: {exc}",
                    traceback=traceback.format_exc(),
                )
            )
    except Exception:
        pass
