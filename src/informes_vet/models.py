"""Esquema SQLAlchemy Core para `veterinaria_raw`.

5 tablas: informes, hallazgos, conclusiones, errores_ingesta, embeddings.
Esquema portable SQLite <-> PostgreSQL. Recreable con `--reset`.
"""

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    MetaData,
    String,
    Table,
    Text,
    func,
)

metadata = MetaData()

informes = Table(
    "informes",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("archivo", String(512), nullable=False),
    Column("ruta_relativa", String(1024), nullable=False),
    Column("anio", Integer, nullable=False),
    Column("sha256", String(64), nullable=False, unique=True),
    Column("nombre", String(255)),
    Column("especie", String(128)),
    Column("raza", String(255)),
    Column("genero", String(64)),
    Column("edad", String(64)),
    Column("peso", String(64)),
    Column("tutor", String(255)),
    Column("doctor_solicitante", String(255)),
    Column("fecha", String(128)),
    Column("antecedentes", Text),
    Column("motivo", Text),
    Column("anamnesis", Text),
    Column("n_ficha", String(64)),
    Column("estudio", String(255)),
    Column("hallazgos_crudos", Text),
    Column("paciente_json", Text),
    Column("ingested_at", DateTime, server_default=func.now()),
    Index("ix_informes_anio", "anio"),
    Index("ix_informes_nombre", "nombre"),
    Index("ix_informes_especie", "especie"),
    Index("ix_informes_sha256", "sha256"),
)

hallazgos = Table(
    "hallazgos",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "informe_id",
        Integer,
        ForeignKey("informes.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("organo", String(64), nullable=False),
    Column("descripcion", Text, nullable=False),
    Column("estado", String(16)),
    Column("orden", Integer, nullable=False, default=0),
    Column("hallazgo_hash", String(64)),
    Index("ix_hallazgos_informe_id", "informe_id"),
    Index("ix_hallazgos_organo", "organo"),
    Index("ix_hallazgos_estado", "estado"),
    Index("ix_hallazgos_hash", "hallazgo_hash"),
)

conclusiones = Table(
    "conclusiones",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "informe_id",
        Integer,
        ForeignKey("informes.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("texto_completo", Text, nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
    Index("ix_conclusiones_informe_id", "informe_id"),
)

errores_ingesta = Table(
    "errores_ingesta",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("archivo", String(512)),
    Column("ruta", String(1024)),
    Column("error", Text),
    Column("traceback", Text),
    Column("created_at", DateTime, server_default=func.now()),
)

embeddings = Table(
    "embeddings",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_type", String(32), nullable=False),
    Column("source_id", Integer, nullable=False),
    Column("texto_original", Text, nullable=False),
    Column("modelo", String(64)),
    Column("dimension", Integer),
    Column("vector_json", JSON),
    Column("created_at", DateTime, server_default=func.now()),
    Index("ix_embeddings_source", "source_type", "source_id"),
    Index("ix_embeddings_modelo", "modelo"),
)

__all__ = [
    "metadata",
    "informes",
    "hallazgos",
    "conclusiones",
    "errores_ingesta",
    "embeddings",
]
