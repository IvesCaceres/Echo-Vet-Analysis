"""Esquema SQLAlchemy Core para `gold.db`.

3 tablas denormalizadas + 2 VIEWs analíticas (gold_coocurrencias,
gold_tendencias) + 1 tabla operativa (gold_etl_runs).

Diseño:
- 100% denormalizado: nombres canónicos como TEXT (no FKs hacia dims).
- Grano: 1 fila por conclusión-item / informe / atributo-hallazgo.
- gold_coocurrencias y gold_tendencias: VIEWs SQLite puras que
  referencian SOLO las tablas gold_* (ya denormalizadas). Esto evita
  cualquier dependencia cross-DB hacia silver.db — Power BI Desktop
  consume gold.db con una sola conexión ODBC.
- Esquema portable SQLite <-> PostgreSQL. Recreable con `--reset`.
- FKs hacia Silver: NO se declaran. La coherencia se valida en
  build_gold (DELETE+INSERT transaccional desde Silver).
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
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
# TABLAS DENORMALIZADAS (3)
# =============================================================================

# gold_diagnosticos: 1 fila por conclusion_item de Silver.
# Denormaliza dim_termino_conclusion + silver_informes (anio/mes desde
# fecha_parseada).
gold_diagnosticos = Table(
    "gold_diagnosticos",
    metadata,
    Column("conclusion_item_id", Integer, primary_key=True),
    Column("informe_id", Integer, nullable=False),
    Column("termino_canonico", String(64), nullable=False, index=True),
    Column("tipo_item", String(16), nullable=False, index=True),
    Column("categoria_clinica", String(32), index=True),
    Column("organo_asociado", String(32), index=True),
    Column("lateralidad", String(16), index=True),
    Column("modificador_cualidad", String(32), index=True),
    Column("modificador_distribucion", String(32), index=True),
    Column("negado", Boolean, nullable=False, server_default="0"),
    Column("confianza", Real),
    Column("anio", Integer, nullable=False, index=True),
    Column("mes", Integer, nullable=False, index=True),
    Column("es_primario_en_informe", Boolean, nullable=False, server_default="0"),
    Column("gold_built_at", DateTime, server_default=func.now()),
    CheckConstraint(
        "tipo_item IN ('DIAGNOSTICO','ETIOLOGIA','NEGATIVO')",
        name="ck_gold_diag_tipo_item",
    ),
    CheckConstraint("mes >= 1 AND mes <= 12", name="ck_gold_diag_mes"),
    CheckConstraint(
        # Rango permisivo: Silver tiene outliers de extracción (ej: "3035").
        # Como Silver está congelado, Gold acepta el rango [1, 9999]
        # para no perder conclusion_items de informes con fechas outliers.
        # El outlier es trazable en silver_informes.fecha_parseada.
        "anio >= 1 AND anio <= 9999",
        name="ck_gold_diag_anio",
    ),
)

# gold_demografia: 1 fila por informe.
# Denormaliza dims de especie/sexo/edad/estudio/estado_reproductivo +
# cross-layer a raw.informes para raza_raw + agregaciones por informe.
gold_demografia = Table(
    "gold_demografia",
    metadata,
    Column("informe_id", Integer, primary_key=True),
    Column("fecha", Date, index=True),
    Column("anio", Integer, nullable=False, index=True),
    Column("mes", Integer, nullable=False, index=True),
    Column("trimestre", Integer, index=True),
    Column("especie_nombre", String(64), nullable=False, index=True),
    Column("sexo_nombre", String(32), index=True),
    Column("edad_categoria_nombre", String(32), index=True),
    Column("estudio_nombre", String(64), index=True),
    Column("estado_reproductivo_nombre", String(32), index=True),
    Column("raza_raw", String(255)),
    Column("nombre_paciente", String(255)),
    Column("tutor", String(255)),
    Column("n_hallazgos", Integer, nullable=False, default=0),
    Column("n_atributos_extraidos", Integer, nullable=False, default=0),
    Column("n_items_diagnostico", Integer, nullable=False, default=0),
    Column("n_items_etiologia", Integer, nullable=False, default=0),
    Column("n_items_negativo", Integer, nullable=False, default=0),
    Column("gold_built_at", DateTime, server_default=func.now()),
    CheckConstraint("mes >= 1 AND mes <= 12", name="ck_gold_demo_mes"),
    CheckConstraint(
        "trimestre >= 1 AND trimestre <= 4",
        name="ck_gold_demo_trimestre",
    ),
    CheckConstraint(
        # Rango permisivo: ver ck_gold_diag_anio (mismo motivo).
        "anio >= 1 AND anio <= 9999",
        name="ck_gold_demo_anio",
    ),
)

# gold_hallazgos: 1 fila por atributo-hallazgo.
# Denormaliza dim_organo + dim_atributo + dim_organo_atributo +
# dim_valor_atributo + dim_segmento_anatomico + silver_hallazgos.
gold_hallazgos = Table(
    "gold_hallazgos",
    metadata,
    Column("atributo_hallazgo_id", Integer, primary_key=True),
    Column("informe_id", Integer, nullable=False, index=True),
    Column("hallazgo_id", Integer, nullable=False, index=True),
    Column("organo_nombre", String(64), nullable=False, index=True),
    Column("sistema", String(32), nullable=False, index=True),
    Column("atributo_nombre", String(64), nullable=False, index=True),
    Column("valor_nombre", String(64)),
    Column("valor_canonico", String(64), index=True),
    Column("valor_numerico", Real),
    Column("segmento_nombre", String(64)),
    Column("lateralidad", String(16), index=True),
    Column("estado_hallazgo", String(16), nullable=False, index=True),
    Column("unidad", String(16)),
    Column("gold_built_at", DateTime, server_default=func.now()),
    CheckConstraint(
        "estado_hallazgo IN ('normal','anormal','no_evaluado')",
        name="ck_gold_hall_estado",
    ),
)


# =============================================================================
# ENTIDADES ANALÍTICAS (2) — VIEWs que referencian solo tablas gold_*
# =============================================================================
#
# SQLAlchemy Core no tiene soporte nativo de VIEWs (son objetos de esquema
# especiales en SQLite/PostgreSQL). Por eso las definimos como DDL strings
# portables. `gold.py:create_gold_views()` se encarga de DROP+CREATE.
#
# Decisión de diseño: las VIEWs referencian SOLO tablas gold_* (nunca
# silver.*). Razones:
# 1. Coherencia con ARCHITECTURE_FINAL.md §5.3 ("100% denormalizado").
# 2. Power BI Desktop consume gold.db con una sola conexión ODBC.
#    VIEWs con cross-DB refs (gold.db → silver.db) requieren ATTACH
#    por conexión, lo cual rompe ese modelo.
# 3. Mantenibilidad: si cambia el shape de silver, las tablas gold se
#    rebuildean con DELETE+INSERT en el mismo run; las VIEWs se
#    recrean con DROP+CREATE. Sin migraciones adicionales.

VIEW_DDL: dict[str, str] = {
    # gold_coocurrencias: pares (termino_a, termino_b) que coocurren en el
    # mismo informe, ambos tipo_item=DIAGNOSTICO. Cardinalidad esperada
    # ~22.708 filas (basado en combinatoria de términos en 2.893 informes).
    "gold_coocurrencias": """
        CREATE VIEW gold_coocurrencias AS
        SELECT
            gd_a.termino_canonico AS termino_a_nombre,
            gd_b.termino_canonico AS termino_b_nombre,
            COUNT(*) AS n_coocurrencias,
            COUNT(*) * 1.0 / (
                SELECT COUNT(DISTINCT informe_id) FROM gold_diagnosticos
            ) AS soporte
        FROM gold_diagnosticos gd_a
        JOIN gold_diagnosticos gd_b
          ON gd_a.informe_id = gd_b.informe_id
         AND gd_a.conclusion_item_id < gd_b.conclusion_item_id
        WHERE gd_a.tipo_item = 'DIAGNOSTICO'
          AND gd_b.tipo_item = 'DIAGNOSTICO'
        GROUP BY gd_a.termino_canonico, gd_b.termino_canonico
    """,
    # gold_tendencias: agregación por (año, mes, especie, diagnóstico) con
    # el conteo de informes donde aparece el término. Cardinalidad esperada
    # ~6.500 filas.
    "gold_tendencias": """
        CREATE VIEW gold_tendencias AS
        SELECT
            gd.anio,
            gd.mes,
            gdm.especie_nombre,
            gd.termino_canonico,
            COUNT(DISTINCT gd.informe_id) AS n_informes_con_termino
        FROM gold_diagnosticos gd
        JOIN gold_demografia gdm ON gdm.informe_id = gd.informe_id
        WHERE gd.tipo_item = 'DIAGNOSTICO'
        GROUP BY gd.anio, gd.mes, gdm.especie_nombre, gd.termino_canonico
    """,
}


# =============================================================================
# OPERATIVA: TRACKING DE EJECUCIONES ETL (1)
# =============================================================================

gold_etl_runs = Table(
    "gold_etl_runs",
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
    # tablas denormalizadas
    "gold_diagnosticos",
    "gold_demografia",
    "gold_hallazgos",
    # DDL de VIEWs (creadas vía gold.py:create_gold_views)
    "VIEW_DDL",
    # operativa
    "gold_etl_runs",
]