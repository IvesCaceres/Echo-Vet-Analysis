"""Esquema SQLAlchemy Core para `veterinaria_silver`.

24 tablas del diseño (cf. `docs/SILVER_LAYER.md`) + 1 tabla operativa
(`silver_etl_runs`) para tracking de ejecuciones del ETL.

Esquema portable SQLite <-> PostgreSQL. Recreable con `--reset`.
Las FKs cross-DB hacia RAW son LOGICAS (validadas en build por el ETL).
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)

# Alias histórico: el diseño usa `Real` para floats portables.
Real = Float

metadata = MetaData()


# =============================================================================
# FACTS (4)
# =============================================================================

silver_informes = Table(
    "silver_informes",
    metadata,
    Column("informe_id", Integer, primary_key=True),
    Column("sha256", String(64), nullable=False, unique=True),
    Column("anio", Integer, nullable=False, index=True),
    Column("fecha_raw", String(128)),
    Column("fecha_parseada", Date, index=True),
    Column("fecha_confianza", Real),
    Column("dim_especie_id", Integer, ForeignKey("dim_especie.id"), index=True),
    Column("dim_raza_id", Integer, ForeignKey("dim_raza.id"), index=True),
    Column("dim_sexo_id", Integer, ForeignKey("dim_sexo.id"), nullable=False, index=True),
    Column(
        "dim_estado_reproductivo_id",
        Integer,
        ForeignKey("dim_estado_reproductivo.id"),
        nullable=False,
        index=True,
    ),
    Column("dim_estudio_id", Integer, ForeignKey("dim_estudio.id"), nullable=False, index=True),
    Column("dim_edad_categoria_id", Integer, ForeignKey("dim_edad_categoria.id"), index=True),
    Column("edad_meses", Integer),
    Column("edad_origen_raw", String(64)),
    Column("edad_parse_ok", Boolean, nullable=False, server_default="0"),
    Column("peso_kg", Real),
    Column("nombre_paciente", String(255)),
    Column("tutor", String(255)),
    Column("doctor_solicitante", String(255)),
    Column("n_ficha", String(64)),
    Column("silver_built_at", DateTime, server_default=func.now()),
)

silver_hallazgos = Table(
    "silver_hallazgos",
    metadata,
    Column("hallazgo_id", Integer, primary_key=True),
    Column("informe_id", Integer, nullable=False, index=True),
    Column("dim_organo_id", Integer, ForeignKey("dim_organo.id"), nullable=False, index=True),
    Column("estado", String(16), nullable=False, index=True),
    Column("orden", Integer, nullable=False),
    Column("descripcion", Text, nullable=False),
    Column("n_atributos_extraidos", Integer, nullable=False, default=0),
    Column("longitud_caracteres", Integer, nullable=False),
    Column("hallazgo_hash", String(64), nullable=False, index=True),
    Column("es_gestacion_fallback", Boolean, nullable=False, default=False),
    Column("silver_built_at", DateTime, server_default=func.now()),
)

silver_atributos_hallazgo = Table(
    "silver_atributos_hallazgo",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("hallazgo_id", Integer, nullable=False, index=True),
    Column("informe_id", Integer, nullable=False, index=True),
    Column("dim_organo_atributo_id", Integer, ForeignKey("dim_organo_atributo.id"), nullable=False, index=True),
    Column("dim_organo_id", Integer, ForeignKey("dim_organo.id"), nullable=False, index=True),
    Column("segmento_id", Integer, nullable=True, index=True),
    Column("lateralidad", String(16), nullable=True, index=True),
    Column("dim_valor_atributo_id", Integer, ForeignKey("dim_valor_atributo.id"), nullable=True, index=True),
    Column("valor_texto", String(255), nullable=False),
    Column("valor_canonico", String(64), index=True),
    Column("valor_numerico", Real),
    Column("unidad", String(16)),
    Column("confianza", Real, nullable=False),
    Column("metodo_extraccion", String(32), nullable=False),
    Column("texto_original", Text, nullable=False),
    Column("pos_inicio", Integer, nullable=False),
    Column("pos_fin", Integer, nullable=False),
    Column("silver_built_at", DateTime, server_default=func.now()),
    # Nota: el UNIQUE INDEX efectivo (hallazgo_id, dim_organo_atributo_id, segmento_id)
    # se crea con COALESCE en silver_db.py para tratar NULL como "sin segmento"
    # (UNIQUE estándar de SQLite trata NULL como distintos).
    Index("ix_silver_attr_informe", "informe_id"),
    Index("ix_silver_attr_canonico", "valor_canonico"),
)

silver_conclusion_items = Table(
    "silver_conclusion_items",
    metadata,
    # Identificadores
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("conclusion_id", Integer, nullable=False, index=True),
    Column("informe_id", Integer, nullable=False, index=True),
    Column(
        "termino_conclusion_id",
        Integer,
        ForeignKey("dim_termino_conclusion.id"),
        nullable=False,
        index=True,
    ),
    # Modificadores promovidos a columnas (Opción C)
    Column("lateralidad", String(16), index=True),
    Column("modificador_cualidad", String(32), index=True),
    Column("modificador_distribucion", String(32), index=True),
    # Negación
    Column("negado", Boolean, nullable=False, server_default="0"),
    # Posición y metadatos de extracción
    Column("pos_inicio", Integer, nullable=False),
    Column("pos_fin", Integer, nullable=False),
    Column("termino_detectado", String(128), nullable=False),
    Column("confianza", Real, nullable=False, server_default="1.0"),
    Column("metodo_extraccion", String(32), nullable=False, server_default="REGEX_RULE"),
    Column("created_at", DateTime, server_default=func.now()),
    # CHECK constraints (los modificadores tienen dominios cerrados)
    CheckConstraint(
        "lateralidad IS NULL OR lateralidad IN "
        "('bilateral','izquierdo','derecho','ambos','unilateral')",
        name="ck_silver_conc_items_lateralidad",
    ),
    CheckConstraint("pos_fin > pos_inicio", name="ck_silver_conc_items_pos"),
    CheckConstraint(
        "confianza >= 0.0 AND confianza <= 1.0",
        name="ck_silver_conc_items_confianza",
    ),
    # UNIQUE INDEX efectivo se crea con COALESCE en silver_db.py
    # (v5.0): (conclusion_id, termino_conclusion_id, pos_inicio, pos_fin).
    # Importante: modificador_cualidad y modificador_distribucion NO están
    # en la clave (decisión de diseño Opción C — clave lógica estable).
    Index("ix_silver_conc_items_concl_term", "conclusion_id", "termino_conclusion_id"),
)


# =============================================================================
# DIMENSIONES (10)
# =============================================================================

dim_organo = Table(
    "dim_organo",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nombre_canonico", String(64), nullable=False, unique=True),
    Column("sistema", String(32), nullable=False, index=True),
    Column("es_gestacion_fallback", Boolean, nullable=False, default=False),
    Column("created_at", DateTime, server_default=func.now()),
)

dim_atributo = Table(
    "dim_atributo",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nombre_canonico", String(64), nullable=False, unique=True),
    Column("descripcion_clinica", Text),
    Column("created_at", DateTime, server_default=func.now()),
)

dim_organo_atributo = Table(
    "dim_organo_atributo",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("dim_organo_id", Integer, ForeignKey("dim_organo.id"), nullable=False, index=True),
    Column("dim_atributo_id", Integer, ForeignKey("dim_atributo.id"), nullable=False, index=True),
    Column("dim_segmento_id", Integer, ForeignKey("dim_segmento_anatomico.id"), nullable=True, index=True),
    Column("tipo_dato", String(16), nullable=False),
    Column("unidad_default", String(16)),
    Column("valores_canonicos_csv", Text),
    Column("cobertura_corpus_pct", Real, nullable=False),
    Column("n_hallazgos_corpus", Integer, nullable=False),
    Column("orden_visualizacion", Integer, default=0),
    Column("created_at", DateTime, server_default=func.now()),
    # UNIQUE efectivo via COALESCE-based INDEX (NULL segmento = sin segmento).
    # Igual que silver_atributos_hallazgo, no podemos usar UNIQUE directo
    # porque SQLite trata NULL como distintos.
    # El índice real se crea en silver_db.py/migrate() para garantizar el
    # comportamiento portable SQLite <-> PostgreSQL.
    Index("ix_dim_organo_atributo_oatrib", "dim_organo_id", "dim_atributo_id"),
)

dim_especie = Table(
    "dim_especie",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nombre_canonico", String(64), nullable=False, unique=True),
    Column("nombre_cientifico", String(64)),
    Column("es_exotica", Boolean, nullable=False, default=False),
    Column("fuente", String(32), nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
)

dim_raza = Table(
    "dim_raza",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("dim_especie_id", Integer, ForeignKey("dim_especie.id"), nullable=False, index=True),
    Column("nombre_canonico", String(128), nullable=False),
    Column("es_mestizo", Boolean, nullable=False, default=False),
    Column("agrupacion", String(64)),
    Column("fuente", String(32), nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
    UniqueConstraint("dim_especie_id", "nombre_canonico", name="uq_dim_raza_especie_nombre"),
)

dim_sexo = Table(
    "dim_sexo",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nombre_canonico", String(32), nullable=False, unique=True),
    Column("codigo", String(1), nullable=False, unique=True),
    Column("created_at", DateTime, server_default=func.now()),
)

dim_estado_reproductivo = Table(
    "dim_estado_reproductivo",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nombre_canonico", String(32), nullable=False, unique=True),
    Column("codigo", String(8), nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
)

dim_estudio = Table(
    "dim_estudio",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nombre_canonico", String(64), nullable=False, unique=True),
    Column("abreviatura", String(16)),
    Column("parent_id", Integer, ForeignKey("dim_estudio.id")),
    Column("created_at", DateTime, server_default=func.now()),
)

dim_edad_categoria = Table(
    "dim_edad_categoria",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("codigo", String(8), nullable=False, unique=True),
    Column("nombre", String(32), nullable=False),
    Column("min_meses", Integer, nullable=False),
    Column("max_meses", Integer),
)

dim_segmento_anatomico = Table(
    "dim_segmento_anatomico",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("dim_organo_id", Integer, ForeignKey("dim_organo.id"), nullable=False, index=True),
    Column("codigo", String(32), nullable=False),
    Column("nombre_canonico", String(64), nullable=False),
    Column("orden", Integer, nullable=False, default=0),
    Column("created_at", DateTime, server_default=func.now()),
    UniqueConstraint("dim_organo_id", "codigo", name="uq_dim_segmento_organo_codigo"),
)

dim_valor_atributo = Table(
    "dim_valor_atributo",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("atributo_id", Integer, ForeignKey("dim_atributo.id"), nullable=False, index=True),
    Column("valor", String(64), nullable=False),
    Column("sinonimos", Text),
    Column("patron_extraccion", Text),
    Column("es_binario_true", Boolean, nullable=False, default=False),
    Column("es_default", Boolean, nullable=False, default=False),
    Column("orden", Integer, nullable=False, default=0),
    Column("activo", Boolean, nullable=False, default=True),
    Column("created_at", DateTime, server_default=func.now()),
    UniqueConstraint("atributo_id", "valor", name="uq_dim_valor_atributo"),
)

# dim_termino_conclusion — vocabulario canónico de términos extraíbles
# de las CONCLUSIONES (no de hallazgos). v5.0 — Opción C.
# - tipo_item ∈ {DIAGNOSTICO, ETIOLOGIA, NEGATIVO}
# - organo_asociado y categoria_clinica son opcionales (NULL para términos
#   genéricos como 'normal', 'compatible_con').
# - sinonimos y patron_extraccion almacenan las variantes textuales usadas
#   por el extractor (lista separada por '|').
# - n_menciones_corpus + frecuencia_rank se actualizan tras el primer build
#   para soportar filtros por rango de frecuencia.
dim_termino_conclusion = Table(
    "dim_termino_conclusion",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nombre_canonico", String(64), nullable=False, unique=True),
    Column(
        "tipo_item",
        String(16),
        nullable=False,
        index=True,
    ),
    Column("organo_asociado", String(32), index=True),
    Column("categoria_clinica", String(32), index=True),
    Column("sinonimos", Text),
    Column("patron_extraccion", Text),
    Column("n_menciones_corpus", Integer, nullable=False, default=0),
    Column("frecuencia_rank", Integer, index=True),
    Column("activo", Boolean, nullable=False, default=True),
    Column("created_at", DateTime, server_default=func.now()),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now()),
    CheckConstraint(
        "tipo_item IN ('DIAGNOSTICO','ETIOLOGIA','NEGATIVO')",
        name="ck_dim_termino_conclusion_tipo_item",
    ),
)


# =============================================================================
# MAPEOS (6)
# =============================================================================

map_especie = Table(
    "map_especie",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("valor_original", String(128), nullable=False, unique=True),
    Column("dim_especie_id", Integer, ForeignKey("dim_especie.id"), nullable=False, index=True),
    Column("confianza", Real, nullable=False),
    Column("origen", String(32), nullable=False),
    Column("fecha_creacion", DateTime, server_default=func.now()),
)

map_raza = Table(
    "map_raza",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("valor_original", String(255), nullable=False, unique=True),
    Column("dim_raza_id", Integer, ForeignKey("dim_raza.id"), index=True),
    Column("dim_especie_id", Integer, ForeignKey("dim_especie.id"), nullable=False, index=True),
    Column("estado_revision", String(16), nullable=False, index=True),
    Column("frecuencia", Integer, nullable=False),
    Column("confianza", Real, nullable=False),
    Column("origen", String(32), nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
)

map_sexo = Table(
    "map_sexo",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("valor_original", String(128), nullable=False, unique=True),
    Column("dim_sexo_id", Integer, ForeignKey("dim_sexo.id"), nullable=False, index=True),
    Column("confianza", Real, nullable=False),
    Column("origen", String(32), nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
)

map_estado_reproductivo = Table(
    "map_estado_reproductivo",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("valor_original", String(128), nullable=False, unique=True),
    Column("dim_estado_reproductivo_id", Integer, ForeignKey("dim_estado_reproductivo.id"), nullable=False, index=True),
    Column("confianza", Real, nullable=False),
    Column("origen", String(32), nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
)

map_estudio = Table(
    "map_estudio",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("valor_original", String(128), nullable=False, unique=True),
    Column("dim_estudio_id", Integer, ForeignKey("dim_estudio.id"), nullable=False, index=True),
    Column("confianza", Real, nullable=False),
    Column("origen", String(32), nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
)

map_atributo_valor = Table(
    "map_atributo_valor",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("dim_organo_atributo_id", Integer, ForeignKey("dim_organo_atributo.id"), nullable=False, index=True),
    Column("valor_original", String(128), nullable=False),
    Column("valor_canonico", String(64), nullable=False),
    Column("orden", Integer),
    Column("origen", String(32), nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
    UniqueConstraint("dim_organo_atributo_id", "valor_original", name="uq_map_atributo_valor"),
)


# =============================================================================
# STAGING (3)
# =============================================================================

stg_razas_detectadas = Table(
    "stg_razas_detectadas",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("valor_original", String(255), nullable=False, unique=True),
    Column("frecuencia", Integer, nullable=False, index=True),
    Column("dim_especie_inferida_id", Integer, ForeignKey("dim_especie.id")),
    Column("propuesta_canonica", String(128)),
    Column("dim_raza_propuesta_id", Integer, ForeignKey("dim_raza.id")),
    Column("estado_revision", String(16), nullable=False, index=True),
    Column("revisado_por", String(64)),
    Column("revisado_at", DateTime),
    Column("observaciones", Text),
    Column("origen", String(32), nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
)

stg_valores_no_mapeados = Table(
    "stg_valores_no_mapeados",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("dimension", String(32), nullable=False, index=True),
    Column("valor_original", String(255), nullable=False),
    Column("frecuencia", Integer, nullable=False, index=True),
    Column("propuesta_canonica", String(128)),
    Column("dim_destino_id", Integer, index=True),
    Column("estado_revision", String(16), nullable=False, index=True),
    Column("revisado_por", String(64)),
    Column("revisado_at", DateTime),
    Column("observaciones", Text),
    Column("origen", String(32), nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
    UniqueConstraint("dimension", "valor_original", name="uq_stg_valor_no_mapeado"),
)

stg_atributos_valores = Table(
    "stg_atributos_valores",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("dim_organo_atributo_id", Integer, ForeignKey("dim_organo_atributo.id"), nullable=False, index=True),
    Column("valor_original", String(255), nullable=False),
    Column("frecuencia", Integer, nullable=False, index=True),
    Column("primera_vez_visto", DateTime, nullable=False),
    Column("ultima_vez_visto", DateTime, nullable=False),
    Column("contexto_ejemplo", Text),
    Column("propuesta_canonico", String(64)),
    Column("estado_revision", String(16), nullable=False, index=True),
    Column("revisado_por", String(64)),
    Column("revisado_at", DateTime),
    Column("observaciones", Text),
    Column("created_at", DateTime, server_default=func.now()),
    UniqueConstraint("dim_organo_atributo_id", "valor_original", name="uq_stg_atributo_valor"),
)

# stg_conclusion_no_match — conclusiones sin items extraíbles. v5.0 — F5.
# Permite auditar la "zona ciega" del extractor y priorizar la ampliación
# del catálogo. Tipos no_match:
#   - 'sin_patron'    — texto sin ningún patrón conocido (probablemente texto
#                       libre como 'control' o nombres de propietario).
#   - 'solo_modificadores' — solo aparecen modificadores pero ningún
#                       diagnóstico/etiología/negativo.
#   - 'demasiado_corto' — texto con <3 palabras no clasificables.
stg_conclusion_no_match = Table(
    "stg_conclusion_no_match",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("conclusion_id", Integer, nullable=False, unique=True),
    Column("informe_id", Integer, nullable=False, index=True),
    Column("texto_no_matcheado", Text, nullable=False),
    Column("n_caracteres", Integer, nullable=False),
    Column("n_oraciones", Integer, nullable=False),
    Column("tipo_no_match", String(32), nullable=False, index=True),
    Column("created_at", DateTime, server_default=func.now()),
)


# =============================================================================
# AUDITORIA (1)
# =============================================================================

silver_revision_log = Table(
    "silver_revision_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("tabla_origen", String(64), nullable=False, index=True),
    Column("operacion", String(16), nullable=False),
    Column("valor_original", String(255), nullable=False),
    Column("valor_canonico", String(255)),
    Column("contexto_id", Integer),
    Column("motivo", Text),
    Column("actor", String(64), nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
)


# =============================================================================
# OPERATIVA: TRACKING DE EJECUCIONES ETL (1)
# =============================================================================

silver_etl_runs = Table(
    "silver_etl_runs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("phase", String(8), nullable=False, index=True),
    Column("started_at", DateTime, nullable=False, server_default=func.now()),
    Column("finished_at", DateTime),
    Column("status", String(16), nullable=False, index=True),
    Column("rows_read", Integer, nullable=False, default=0),
    Column("rows_written", Integer, nullable=False, default=0),
    Column("rows_skipped", Integer, nullable=False, default=0),
    Column("rows_errored", Integer, nullable=False, default=0),
    Column("duration_ms", Integer),
    Column("actor", String(64), nullable=False),
    Column("notes", Text),
)


__all__ = [
    "metadata",
    # facts
    "silver_informes",
    "silver_hallazgos",
    "silver_atributos_hallazgo",
    "silver_conclusion_items",
    # dimensiones
    "dim_organo",
    "dim_atributo",
    "dim_organo_atributo",
    "dim_especie",
    "dim_raza",
    "dim_sexo",
    "dim_estado_reproductivo",
    "dim_estudio",
    "dim_edad_categoria",
    "dim_segmento_anatomico",
    "dim_valor_atributo",
    "dim_termino_conclusion",
    # mapeos
    "map_especie",
    "map_raza",
    "map_sexo",
    "map_estado_reproductivo",
    "map_estudio",
    "map_atributo_valor",
    # staging
    "stg_razas_detectadas",
    "stg_valores_no_mapeados",
    "stg_atributos_valores",
    "stg_conclusion_no_match",
    # auditoria
    "silver_revision_log",
    # operativa
    "silver_etl_runs",
]