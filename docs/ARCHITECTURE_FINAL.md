# Arquitectura Final — VetTalk

**Fecha de congelación:** 2026-06-26
**Estado:** Definitivo. Fuente única de verdad arquitectónica.
**No se discute más después de este documento.** Solo se construye funcionalidad.

---

## 0. Restricciones inmutables (no se renegocian)

Estas restricciones vienen del usuario y son **datos del proyecto**, no opiniones:

| # | Restricción | Consecuencia directa |
|---|---|---|
| R1 | Una sola veterinaria | Sin multi-tenancy, sin scoping por clínica |
| R2 | ~1.500 informes nuevos/año | Volumen trivial para cualquier RDBMS moderno |
| R3 | Estructura del informe fija por 5+ años | No se necesita flexibilidad de schema ni versionado de regex |
| R4 | Un solo desarrollador y mantenedor | Sin onboarding, sin hand-off, sin convenciones enterprise |
| R5 | Objetivo = valor clínico y analítico | Sin "infraestructura preparatoria" |
| R6 | SQLite como única DB operativa | PG queda como cambio futuro de 1 línea |
| R7 | Power BI como consumidor principal | Sin API REST, sin webhooks, sin auth |

**Si en el futuro alguna restricción cambia**, se reabre la discusión. Mientras tanto, este documento es ley.

---

## 1. Estado actual del proyecto (auditoría)

### 1.1 Inventario de archivos

**`src/informes_vet/` (6.224 LOC en 14 archivos):**

| Archivo | LOC | Rol | Veredicto |
|---|---:|---|---|
| `__init__.py` | 1 | Vacío | MANTENER |
| `analytics.py` | 9 | Stub `NotImplementedError` | **ELIMINAR** — no se usa |
| `db.py` | 142 | Engine factory RAW + UPSERT portable | MANTENER (referencia) |
| `docx_io.py` | 79 | Walk .docx + filtros basura | MANTENER |
| `extract.py` | 441 | Parser .docx → JSON | MANTENER |
| `hashutil.py` | 38 | SHA-256 | MANTENER |
| `models.py` | 124 | Schema RAW (5 tablas) | MANTENER |
| `models_silver.py` | 563 | Schema Silver (24 tablas) | MANTENER |
| `organs.py` | 392 | Clasificación de órganos | MANTENER |
| `silver_db.py` | 383 | Engine factory Silver + 5 migraciones versionadas | MANTENER (es la versión custom de "Alembic light" — sin framework) |
| `silver_dims.py` | 207 | Bootstrap dims base (F1) | MANTENER |
| `silver_etl.py` | 2.057 | Orquestador F1-F2.1 + helpers ETL | MANTENER (monolítico pero funciona) |
| `silver_f3_dims.py` | 522 | Bootstrap dims F3 + extractores | MANTENER |
| `silver_f4_values.py` | 429 | Diccionario canónico de valores (F4) | MANTENER |
| `silver_f5_conclusions.py` | 838 | Extracción conclusión (F5) | MANTENER |

**`scripts/` (8.453 LOC en 28 archivos):**

| Archivo | LOC | Rol | Veredicto |
|---|---:|---|---|
| `run_ingest.py` | 167 | Ingesta única de RAW | MANTENER |
| `build_silver.py` | 734 | Orquestador CLI F1-F5 | MANTENER |
| `verify_silver_f1.py` | 133 | Verify F1 | **FUSIONAR** en `verify_silver.py` |
| `verify_silver_f2.py` | 251 | Verify F2 | **FUSIONAR** |
| `verify_silver_f2_1.py` | 186 | Verify F2.1 | **FUSIONAR** |
| `verify_silver_f3.py` | 201 | Verify F3 | **FUSIONAR** |
| `verify_silver_f4.py` | 305 | Verify F4 | **FUSIONAR** |
| `verify_silver_f5.py` | 437 | Verify F5 | **FUSIONAR** |
| `audit_f4_preseed.py` | 651 | Auditoría pre-F4 | **ELIMINAR** (legacy) |
| `audit_f4_value_cardinality.py` | 433 | Auditoría cardinalidad F4 | **ELIMINAR** |
| `audit_f4_value_review.py` | 159 | Auditoría revisión F4 | **ELIMINAR** |
| `audit_silver_f3.py` | 497 | Auditoría F3 | **ELIMINAR** |
| `inventory_silver.py` | 166 | Inventario one-shot | **ELIMINAR** |
| `profile_silver.py` | 332 | Profiling one-shot | **ELIMINAR** |
| `_audit_f5_classify.py` | 211 | Auditoría F5 | **ELIMINAR** |
| `_audit_f5_distribution.py` | 440 | Distribución F5 | **ELIMINAR** |
| `_audit_f5_no_match.py` | 122 | No-match F5 | **ELIMINAR** |
| `_audit_f5_opcion_c.py` | 487 | Opción C F5 | **ELIMINAR** |
| `_audit_f5_precision.py` | 538 | Precisión F5 | **ELIMINAR** |
| `_profile_f3.py` | 192 | Profiling F3 | **ELIMINAR** |
| `_profile_f3_1_clinical_coverage.py` | 276 | Cobertura clínica | **ELIMINAR** |
| `_profile_f3_1_nlp.py` | 560 | NLP F3.1 | **ELIMINAR** |
| `_profile_f3_dim_valores.py` | 717 | Profiling dim valores | **ELIMINAR** |
| `_profile_f3_focused.py` | 249 | Profiling focused | **ELIMINAR** |

**Resumen scripts:**
- 3 se mantienen (run_ingest, build_silver, y uno nuevo por fusionar).
- 6 verify_silver_* se fusionan en 1.
- 19 audit/profile/_* se eliminan (legacy, ya ejecutados, ya cumplieron su rol).

**Raíz del proyecto:**

| Archivo | Tamaño | Veredicto |
|---|---:|---|
| `.env` | 96 B | MANTENER (1 línea) |
| `.env.example` | 285 B | MANTENER |
| `.gitignore` | 3.362 B | MANTENER |
| `requirements.txt` | 96 B | MANTENER |
| `README.md` | 2.335 B | ACTUALIZAR (sección §13) |
| `informes.db` | 22 MB | MANTENER (RAW) |
| `silver.db` | ~41 MB | MANTENER (Silver) |
| `gold.db` | 0 B | MANTENER (a poblar en Gold MVP) |
| `bronze.db` | 0 B | **ELIMINAR** (artefacto legacy) |
| `data.db` | 0 B | **ELIMINAR** |
| `raw.db` | 0 B | **ELIMINAR** |
| `reports.db` | 0 B | **ELIMINAR** |
| `errores_ingest.log` | 160 KB | MANTENER (log de ingesta) |
| `f5_build_log.txt` | 2.841 B | **ELIMINAR** (log one-shot de F5) |
| `f5_verify_log.txt` | 1.973 B | **ELIMINAR** |
| `_purgatorio/` | dir | **ELIMINAR** (directorio de archivos borrados) |
| `backup-20260618/` | dir | MOVER a `docs/archive/` |
| `logs/` | dir | MANTENER (log dir genérico) |
| `Ecografía YYYY/` | dirs | MANTENER (datos fuente, NO tocar) |

### 1.2 Conteo total

| Categoría | LOC hoy | LOC después de limpieza |
|---|---:|---:|
| `src/informes_vet/` productivo | 6.215 | 6.215 |
| `scripts/` productivos | 1.668 | ~1.100 (fusión verify) |
| `scripts/` audit/profile legacy | 6.029 | **0** |
| **Total** | **14.677** | **~7.315** |

**Reducción: ~50% sin perder funcionalidad.** Se eliminan ~6.000 LOC de código legacy que ya cumplió su rol.

---

## 2. Decisiones arquitectónicas

### 2.1 Lo que SÍ se mantiene

Mantenido **sin cambios**:

1. `db.py` — engine factory + UPSERT portable.
2. `silver_db.py` — engine factory Silver + `migrate()` (la versión custom de "Alembic light" sin framework).
3. `models.py`, `models_silver.py` — schema SQLAlchemy Core.
4. `silver_etl.py` + `silver_dims.py` + `silver_f3_dims.py` + `silver_f4_values.py` + `silver_f5_conclusions.py` — pipeline Silver funcional.
5. `extract.py`, `docx_io.py`, `hashutil.py`, `organs.py` — utilidades probadas.
6. `build_silver.py`, `run_ingest.py` — CLI drivers.
7. SQLite como única DB operativa.
8. UPSERT idempotente (`on_conflict_do_nothing` / `INSERT OR IGNORE`).
9. Logging vía `logging` stdlib (no structlog, no loguru).
10. Configuración vía `os.environ` + `python-dotenv`.

**Razón:** todo esto **funciona**, está verificado (19/19 verify checks Silver, 14/14 F2), y la reescritura introduce riesgo sin valor. **"Don't fix what isn't broken."**

### 2.2 Lo que se fusiona

**`verify_silver_f1.py` + `verify_silver_f2.py` + `verify_silver_f2_1.py` + `verify_silver_f3.py` + `verify_silver_f4.py` + `verify_silver_f5.py` → `verify_silver.py`**

- 6 scripts × ~250 LOC promedio = ~1.500 LOC → 1 script ~600 LOC con secciones A, B, C, D, E, F (cada sección es la verificación de una fase).
- Mantiene los mismos criterios de PASS/FAIL.
- Exit code 0 si todas las fases pasan, 1 si alguna falla.
- **Implicación para el usuario:** 1 solo comando para validar Silver end-to-end.

### 2.3 Lo que se elimina (código legacy)

**Los 19 scripts audit/profile/_* se eliminan.** Su trabajo ya está hecho:

| Script | Razón de eliminación |
|---|---|
| `_audit_f5_*` (5 archivos, ~1.800 LOC) | F5 cerrado y firmado. La auditoría fue one-shot. |
| `_profile_f3_*` (5 archivos, ~2.000 LOC) | F3 cerrado y firmado. El profiling fue one-shot. |
| `audit_f4_*` (3 archivos, ~1.250 LOC) | F4 cerrado y firmado. |
| `audit_silver_f3.py` | F3 cerrado y firmado. |
| `inventory_silver.py` | One-shot, no se re-ejecuta. |
| `profile_silver.py` | One-shot. |

**Justificación:** un script que ya cumplió su función diagnóstica no es parte de la arquitectura operativa. Si en el futuro se necesita re-auditar algo, se recrea el script in-situ (copiando la lógica de los docs `F3_*_AUDIT.md`, `F4_*_AUDIT.md`, `F5_*_AUDIT.md` que ya documentan los hallazgos).

**Archivos adicionales a eliminar:**
- `analytics.py` (9 LOC) — stub `NotImplementedError`, nunca se usó.
- `bronze.db`, `data.db`, `raw.db`, `reports.db` — archivos `.db` vacíos legacy.
- `_purgatorio/` — directorio de archivos borrados manualmente (no aporta nada).
- `f5_build_log.txt`, `f5_verify_log.txt` — logs one-shot de F5.

### 2.4 Lo que se crea (nuevo)

**Capa Gold (no existía):**

| Archivo nuevo | LOC estimada | Propósito |
|---|---:|---|
| `src/informes_vet/models_gold.py` | ~120 | Schema 3 tablas Gold + 2 vistas |
| `src/informes_vet/gold.py` | ~400 | Build functions: `build_gold_diagnosticos`, `build_gold_demografia`, `build_gold_hallazgos`, `build_gold_views` |
| `scripts/build_gold.py` | ~100 | CLI driver del ETL Gold |
| `scripts/verify_raw.py` | ~150 | Verify schema RAW + idempotencia |
| `scripts/verify_silver.py` | ~600 | Verify Silver consolidado (reemplaza los 6) |
| `scripts/verify_gold.py` | ~250 | Verify Gold |
| `docs/ARCHITECTURE_FINAL.md` | este doc | Fuente de verdad |

**Total Gold:** ~1.620 LOC. Equivale a ~2-3 días de trabajo.

### 2.5 Lo que NO se implementa nunca

Esta es la lista prohibitiva. **Cualquier PR que agregue uno de estos elementos debe rechazarse** salvo que se reabra este documento formalmente.

| Patrón / componente | Razón del rechazo |
|---|---|
| Arquitectura Hexagonal | 5 capas para 3 tablas es ruido. |
| Repository Pattern | 1 clase por tabla para envolver 1 SQL. |
| Service Layer | No hay lógica de negocio que justifique una capa. |
| Builder Pattern | Filas Gold son tuplas. |
| Domain Models (pydantic/dataclass) | Power BI lee SQL, no objetos. |
| Factories abstractas | `def build_*()` Python normal basta. |
| Adapters / Ports | SQLAlchemy ya ES el adapter. |
| Abstract Base Classes | Sin código compartido entre tablas. |
| Dependency Injection framework | Python sin framework es DI. |
| Domain Events / Event Bus | El usuario ejecutando scripts ES el event bus. |
| CQRS | Silver escribe, Gold lee. Ya está separado físicamente. |
| Unit of Work (framework) | `with engine.begin() as conn:` ya ES UoW. |
| ClockPort | Sin tests temporales. |
| FastAPI / cualquier framework web | Power BI lee SQLite directo. |
| Docker / Kubernetes | Sin deployment distribuido. |
| systemd / daemon | El usuario ejecuta scripts manualmente. |
| Watchdog (detector de archivos) | El usuario arrastra archivos al script. |
| Alembic / framework de migrations | El `migrate()` de `silver_db.py` cumple el rol con 5 migraciones declaradas como dict Python. |
| PostgreSQL (ahora) | SQLite aguanta 10 años del proyecto. PG queda para "el día que". |
| Schemas separados en PG | No aplica en SQLite; cuando se migre, se crean en 5 minutos. |
| Partitioning por año | No hay problema de escala que lo justifique. |
| DLQ automatizada | El log + revisión manual funciona para 5 archivos/día. |
| Lineage por fila | El lineage por RUN (`silver_etl_runs` + nuevo `gold_etl_runs`) basta. |
| Quality Observability Layer | `verify_*.py` es la observabilidad. |
| Drift Checker automático | El "drift" se evita construyendo Silver+Gold en sesión. |
| RazaProviderPort | El cross-layer a RAW es 1 SELECT. No requiere port. |
| Cualquier framework de configuración | `os.environ.get()` con default. |
| Logger enterprise (structlog, loguru) | `logging` stdlib con formato simple. |
| CI/CD | El usuario deploya copiando archivos. |

---

## 3. Estructura final del proyecto

### 3.1 Árbol de archivos (estado target)

```
vettalk/
├── .env                              # PG_DSN (sin usar hoy, documentado)
├── .env.example                      # plantilla
├── .gitignore
├── README.md                         # actualizado (§13)
├── requirements.txt                  # 5 dependencias
│
├── Ecografía 2022/                   # datos fuente, NO tocar
├── Ecografía 2023/
├── Ecografía 2024/
├── Ecografía 2025/
├── Ecografía 2026/
│
├── src/informes_vet/                 # paquete principal
│   ├── __init__.py                   # 1 LOC vacío
│   ├── db.py                         # engine factory + UPSERT RAW (142)
│   ├── models.py                     # schema RAW (124)
│   ├── models_silver.py              # schema Silver (563)
│   ├── models_gold.py                # NUEVO schema Gold (120)
│   ├── docx_io.py                    # walk + filtros (79)
│   ├── extract.py                    # parser .docx (441)
│   ├── hashutil.py                   # SHA-256 (38)
│   ├── organs.py                     # clasificación órganos (392)
│   ├── silver_db.py                  # engine factory Silver + migrate() (383)
│   ├── silver_dims.py                # bootstrap dims F1 (207)
│   ├── silver_etl.py                 # ETL Silver F1-F2.1 (2.057)
│   ├── silver_f3_dims.py             # F3 dims + extractores (522)
│   ├── silver_f4_values.py           # F4 values (429)
│   ├── silver_f5_conclusions.py      # F5 conclusions (838)
│   └── gold.py                       # NUEVO ETL Gold (400)
│
├── scripts/                          # CLIs operacionales
│   ├── run_ingest.py                 # ingesta única RAW (167)
│   ├── build_silver.py               # CLI Silver F1-F5 (734)
│   ├── build_gold.py                 # NUEVO CLI Gold (100)
│   ├── verify_raw.py                 # NUEVO verify RAW (150)
│   ├── verify_silver.py              # FUSIONADO verify Silver (600)
│   └── verify_gold.py                # NUEVO verify Gold (250)
│
├── logs/                             # logs rotados
│
└── docs/
    ├── ARCHITECTURE_FINAL.md         # ESTE DOCUMENTO (fuente de verdad)
    ├── SILVER_LAYER.md
    ├── RAW_LAYER.md
    ├── SILVER_FINAL_SIGNOFF.md
    ├── F2_1_COMPLETION_REPORT.md
    ├── GOLD_DESIGN_V1.md             # referencia histórica
    ├── GOLD_YAGNI_KISS_REVIEW.md     # referencia histórica
    ├── GOLD_FINAL_PRE_IMPLEMENTATION_REVIEW.md
    ├── GOLD_PRE_AUDIT_FINAL.md
    ├── GOLD_READINESS_AUDIT.md
    ├── GOLD_QUESTION_CATALOG.md
    ├── F3_*_*.md                     # docs de implementación F3
    ├── F4_*_*.md                     # docs F4
    ├── F5_*_*.md                     # docs F5
    ├── F2_*_*.md                     # docs F2
    ├── archive/                      # backups antiguos movidos aquí
    └── ...
```

### 3.2 Conteo final

| Categoría | Cantidad | LOC |
|---|---:|---:|
| `src/informes_vet/` productivos | 15 archivos | ~7.000 |
| `scripts/` productivos | 6 archivos | ~2.000 |
| **Total código productivo** | **21 archivos** | **~9.000** |
| `docs/` (referencia histórica) | ~40 archivos | — |
| Datos fuente (NO tocar) | 5 carpetas | — |

**Comparado con el estado pre-limpieza:** se eliminan ~6.000 LOC de audit/profile legacy.

---

## 4. Responsabilidades por archivo

### 4.1 Capa RAW (extract + load)

#### `src/informes_vet/db.py` (142 LOC) — **MANTENER SIN CAMBIOS**

**Responsabilidad única:** crear el engine SQLAlchemy para `informes.db` (RAW) y exponer UPSERT portable entre SQLite y PostgreSQL.

**API expuesta:**
- `get_engine(db_kind: str, project_root: Path) -> Engine`
- `create_schema(engine: Engine) -> None`
- `drop_schema(engine: Engine) -> None`
- `reset_schema(engine: Engine) -> None`
- `upsert_informe(conn, record: dict) -> int | None`
- `insert_hallazgos(conn, informe_id: int, hallazgos: list[dict]) -> int`
- `insert_conclusion(conn, informe_id: int, texto_completo: str) -> int`
- `log_error(engine: Engine, archivo: str, ruta: str, exc: BaseException) -> None`

**No hace:** lógica de extracción de texto, parsing, regex, validación clínica.

#### `src/informes_vet/models.py` (124 LOC) — **MANTENER SIN CAMBIOS**

**Responsabilidad:** definir el schema de las 5 tablas RAW (`informes`, `hallazgos`, `conclusiones`, `errores_ingesta`, `embeddings`).

**Nota:** `embeddings` está vacía pero el esquema queda. Es el anclaje futuro para IA.

#### `src/informes_vet/extract.py` (441 LOC) — **MANTENER SIN CAMBIOS**

**Responsabilidad:** parsear un archivo `.docx` y extraer texto estructurado (tablas, headings, fecha, especie, hallazgos crudos, conclusión).

#### `src/informes_vet/docx_io.py` (79 LOC) — **MANTENER SIN CAMBIOS**

**Responsabilidad:** walk del filesystem, filtros basura (`~$*`, `._*`, `.DS_Store`, denylist).

#### `src/informes_vet/hashutil.py` (38 LOC) — **MANTENER SIN CAMBIOS**

**Responsabilidad:** SHA-256 sobre texto canónico.

#### `src/informes_vet/organs.py` (392 LOC) — **MANTENER SIN CAMBIOS**

**Responsabilidad:** clasificar órganos canónicos desde texto libre.

#### `scripts/run_ingest.py` (167 LOC) — **MANTENER SIN CAMBIOS**

**Responsabilidad:** CLI para ingesta única de RAW (escanea carpetas de año, llama `extract.py`, hace UPSERT a RAW).

### 4.2 Capa Silver

#### `src/informes_vet/silver_db.py` (383 LOC) — **MANTENER SIN CAMBIOS**

**Responsabilidad:** engine factory Silver + `migrate()` con 5 migraciones declaradas como lista de dicts Python.

**Patrón actual (`_MIGRATIONS` list):** cada migración tiene `version`, `name`, `check` (columna que indica si ya se aplicó), `table`, `ddl_sqlite`, `ddl_postgres`. Es la versión "Alembic-lite" sin framework. **Se mantiene exactamente como está.**

#### `src/informes_vet/models_silver.py` (563 LOC) — **MANTENER SIN CAMBIOS**

**Responsabilidad:** schema de las 24 tablas Silver.

#### `src/informes_vet/silver_dims.py` (207 LOC) — **MANTENER SIN CAMBIOS**

**Responsabilidad:** poblar las dimensiones base (F1: dim_organo, dim_especie, dim_sexo, dim_estado_reproductivo, dim_estudio, dim_edad_categoria).

#### `src/informes_vet/silver_etl.py` (2.057 LOC) — **MANTENER SIN CAMBIOS**

**Responsabilidad:** orquestador ETL Silver F1-F2.1. Es monolítico pero funciona. NO se refactoriza.

#### `src/informes_vet/silver_f3_dims.py` (522 LOC) — **MANTENER SIN CAMBIOS**

**Responsabilidad:** bootstrap dims F3 (dim_atributo, dim_organo_atributo, dim_segmento_anatomico, dim_valor_atributo) + extractores de atributos.

#### `src/informes_vet/silver_f4_values.py` (429 LOC) — **MANTENER SIN CAMBIOS**

**Responsabilidad:** poblar `dim_valor_atributo` consolidado + `map_atributo_valor`.

#### `src/informes_vet/silver_f5_conclusions.py` (838 LOC) — **MANTENER SIN CAMBIOS**

**Responsabilidad:** extraer items de conclusión y poblar `silver_conclusion_items` + `dim_termino_conclusion` + `stg_conclusion_no_match`.

#### `scripts/build_silver.py` (734 LOC) — **MANTENER SIN CAMBIOS**

**Responsabilidad:** CLI orquestador del ETL Silver. Acepta `--phase f1|f2|f2_1|f3|f4|f5|all`, `--db sqlite|postgres`, `--reset`, `--init`.

### 4.3 Capa Gold (NUEVA)

#### `src/informes_vet/models_gold.py` (~120 LOC) — **NUEVO**

**Responsabilidad:** schema de las 3 tablas Gold + 2 vistas. Esquema portable SQLite ↔ PostgreSQL (SQLAlchemy Core).

**Contenido esperado:**

```python
# Esquema de:
# - gold_diagnosticos (1 fila por conclusion_item)
# - gold_demografia (1 fila por informe)
# - gold_hallazgos (1 fila por atributo-hallazgo)
# - gold_coocurrencias (VIEW)
# - gold_tendencias (VIEW)
```

#### `src/informes_vet/gold.py` (~400 LOC) — **NUEVO**

**Responsabilidad:** funciones de build para Gold. Cada función es idempotente (DELETE + INSERT en una transacción).

**API expuesta:**
- `build_gold_diagnosticos(conn) -> int`
- `build_gold_demografia(conn) -> int`
- `build_gold_hallazgos(conn) -> int`
- `create_gold_views(conn) -> None` (idempotente: DROP VIEW IF EXISTS + CREATE VIEW)
- `drop_gold_views(conn) -> None`
- `get_engine(db_kind: str, project_root: Path) -> Engine` (engine factory para gold.db)
- `create_schema(engine)`, `reset_schema(engine)`, `drop_schema(engine)`

#### `scripts/build_gold.py` (~100 LOC) — **NUEVO**

**Responsabilidad:** CLI orquestador del ETL Gold.

**API CLI:**
```bash
python scripts/build_gold.py --phase diag|demo|hall|views|all [--db sqlite|postgres] [--reset]
```

#### `scripts/verify_gold.py` (~250 LOC) — **NUEVO**

**Responsabilidad:** verificación end-to-end de Gold. Chequea:

- `gold_etl_runs` registra ejecuciones OK.
- Las 3 tablas tienen el conteo esperado (gold_diagnosticos = silver_conclusion_items, etc.).
- 0 FKs huérfanas.
- 0 valores NULL en columnas críticas (termino_canonico, especie_nombre, organo_nombre).
- Índices existen.
- Exit code 0 si todo pasa, 1 si falla.

### 4.4 Capa verificación

#### `scripts/verify_raw.py` (~150 LOC) — **NUEVO**

**Responsabilidad:** validar el schema RAW y la idempotencia de la ingesta.

**Chequeos:**
- Las 5 tablas existen.
- `informes` no tiene duplicados en `sha256`.
- `hallazgos` y `conclusiones` tienen FKs válidas hacia `informes`.
- Conteos esperados vs observaciones (ej: si hay 2.893 informes en RAW, los `hallazgos` no deberían ser > 30.000).
- `errores_ingesta` existe (puede estar vacía).

#### `scripts/verify_silver.py` (~600 LOC) — **FUSIONAR 6 SCRIPTS EN 1**

**Responsabilidad:** validar el estado de Silver ejecutando todas las verificaciones de las 6 fases en una sola corrida.

**Estructura interna:**
```
=== Sección A: F1 ===
[checks de verify_silver_f1.py]

=== Sección B: F2 + F2.1 ===
[checks de verify_silver_f2.py + verify_silver_f2_1.py]

=== Sección C: F3 ===
[checks de verify_silver_f3.py]

=== Sección D: F4 ===
[checks de verify_silver_f4.py]

=== Sección E: F5 ===
[checks de verify_silver_f5.py]

=== Resumen ===
✓ 47/47 PASS — GO
✗ 45/47 PASS — 2 FAIL
```

**Exit code:** 0 si todas las secciones pasan, 1 si alguna falla.

**API CLI:**
```bash
python scripts/verify_silver.py            # verifica todo
python scripts/verify_silver.py --section f1   # solo F1
python scripts/verify_silver.py --section f5   # solo F5
```

#### `scripts/verify_gold.py` (~250 LOC) — **NUEVO** (descrito arriba)

### 4.5 Lo que se ELIMINA

#### `src/informes_vet/analytics.py` (9 LOC)

Stub que nunca se implementó. ELIMINAR.

#### `scripts/audit_*.py` y `scripts/_audit_*.py` y `scripts/_profile_*.py` (19 archivos, ~6.000 LOC)

Su rol fue one-shot (auditar/profiliar durante construcción de Silver). Ya cumplieron. Los hallazgos están en los docs `F3_*_AUDIT.md`, `F4_*_AUDIT.md`, `F5_*_AUDIT.md`. Si en el futuro se necesita re-auditar, se extrae la lógica de esos docs.

#### Archivos root

- `bronze.db`, `data.db`, `raw.db`, `reports.db` — artefactos `.db` vacíos.
- `_purgatorio/` — directorio de archivos borrados manualmente.
- `f5_build_log.txt`, `f5_verify_log.txt` — logs one-shot.

---

## 5. Esquemas de base de datos

### 5.1 RAW (`informes.db`) — **CONGELADO**

**5 tablas:** `informes`, `hallazgos`, `conclusiones`, `errores_ingesta`, `embeddings`.

**Cardinalidad observada (2026-06-26):**

| Tabla | Filas | Notas |
|---|---:|---|
| `informes` | 2.893 | 1 por .docx ingestado |
| `hallazgos` | 27.866 | ~9.63/informe |
| `conclusiones` | 2.893 | 1 por informe |
| `errores_ingesta` | variable | Best-effort log |
| `embeddings` | 0 | Vacía, esquema listo para futuro |

**Regla de inmutabilidad:** RAW es append-only (nunca UPDATE, nunca DELETE en producción). Las correcciones se hacen en Silver.

### 5.2 Silver (`silver.db`) — **CONGELADO**

**24 tablas:** 4 facts + 13 dimensiones + 4 staging/operativa + 3 maps.

**Cardinalidad observada (2026-06-26):**

| Tabla | Filas | Notas |
|---|---:|---|
| `silver_informes` | 2.893 | 1:1 con raw.informes |
| `silver_hallazgos` | 27.866 | 1:1 con raw.hallazgos |
| `silver_atributos_hallazgo` | 114.753 | ~4.12/informe |
| `silver_conclusion_items` | 16.939 | ~5.87/informe |
| `dim_especie` | 9 | enum-friendly |
| `dim_sexo` | 3 | enum |
| `dim_edad_categoria` | 5 | enum |
| `dim_estado_reproductivo` | 4 | enum |
| `dim_estudio` | 8 | 6 usados |
| `dim_organo` | 16 | 15 usados |
| `dim_atributo` | 30 | 30 usados |
| `dim_segmento_anatomico` | 6 | 6 usados |
| `dim_termino_conclusion` | 98 | 91 activos |
| `dim_organo_atributo` | 71 | bridge clínica |
| `dim_valor_atributo` | 177 | 112 usados |
| `dim_raza` | 63 | 63 canónicas (poblada en F2 Completion Release) |
| `dim_edad_categoria` | 5 | (idem anterior) |
| `map_raza` | 163 | 63 aprobadas + 100 pendientes |
| `map_especie` | 17 | variantes RAW |
| `map_sexo` | 22 | variantes RAW |
| `map_estudio` | 28 | variantes RAW |
| `map_atributo_valor` | 230 | consolidado F4 |
| `stg_atributos_valores` | 0 | placeholder |
| `stg_conclusion_no_match` | 8 | cids fuera de catálogo |
| `stg_razas_detectadas` | 100 | variantes freq<3 |
| `stg_valores_no_mapeados` | 24 | valores sin mapeo |
| `silver_revision_log` | 0 | placeholder |
| `silver_etl_runs` | 24+ | append-only, registra toda ejecución |

**Reglas:**
- Reconstruible 100% desde RAW vía `build_silver.py --phase all`.
- Signoff actual: `SILVER_FINAL_SIGNOFF.md` (19/19 verify checks OK).
- **NO se reabre** salvo bug crítico o migración de motor.

### 5.3 Gold (`gold.db`) — **A CONSTRUIR**

**3 tablas + 2 vistas:**

| Tabla/Vista | Tipo | Cardinalidad esperada | Grano |
|---|---|---:|---|
| `gold_diagnosticos` | TABLA | 16.939 | 1 por conclusion_item |
| `gold_demografia` | TABLA | 2.893 | 1 por informe |
| `gold_hallazgos` | TABLA | 114.753 | 1 por atributo-hallazgo |
| `gold_coocurrencias` | VIEW | 22.708 | 1 por par diagnóstico |
| `gold_tendencias` | VIEW | 6.500 | 1 por (año, mes, especie, diagnóstico) |

**Tablas operativas (auto-generadas en build):**

| Tabla | Filas esperadas | Propósito |
|---|---:|---|
| `gold_etl_runs` | igual que `silver_etl_runs` | Tracking de ejecuciones Gold |
| `sqlite_sequence` | auto | Secuencias PK |

**Esquema de columnas (resumen):**

#### `gold_diagnosticos`

```
conclusion_item_id INTEGER PK
informe_id         INTEGER NOT NULL
termino_canonico   TEXT NOT NULL          (denormalizado desde dim_termino_conclusion)
tipo_item          TEXT NOT NULL          (DIAGNOSTICO/ETIOLOGIA/NEGATIVO)
categoria_clinica  TEXT
organo_asociado    TEXT
lateralidad        TEXT
modificador_cualidad TEXT
modificador_distribucion TEXT
negado             INTEGER NOT NULL       (0/1)
confianza          REAL
anio               INTEGER NOT NULL       (denormalizado desde silver_informes.fecha_parseada)
mes                INTEGER NOT NULL
es_primario_en_informe INTEGER NOT NULL    (0/1)
```

#### `gold_demografia`

```
informe_id         INTEGER PK
fecha              DATE
anio               INTEGER NOT NULL
mes                INTEGER NOT NULL
trimestre          INTEGER
especie_nombre     TEXT NOT NULL
sexo_nombre        TEXT
edad_categoria_nombre TEXT
estudio_nombre     TEXT
estado_reproductivo_nombre TEXT
raza_raw           TEXT                   (cross-layer desde raw.informes)
nombre_paciente    TEXT
tutor              TEXT
n_hallazgos        INTEGER
n_atributos_extraidos INTEGER
n_items_diagnostico INTEGER
n_items_etiologia  INTEGER
n_items_negativo   INTEGER
```

#### `gold_hallazgos`

```
atributo_hallazgo_id INTEGER PK
informe_id         INTEGER NOT NULL
hallazgo_id        INTEGER NOT NULL
organo_nombre      TEXT NOT NULL
sistema            TEXT
atributo_nombre    TEXT NOT NULL
valor_nombre       TEXT
valor_canonico     TEXT
valor_numerico     REAL
segmento_nombre    TEXT
lateralidad        TEXT
estado_hallazgo    TEXT NOT NULL          (normal/anormal/no_evaluado)
unidad             TEXT
```

#### `gold_coocurrencias` (VIEW)

```sql
CREATE VIEW gold_coocurrencias AS
SELECT
  ta.id AS termino_a_id,
  ta.nombre_canonico AS termino_a_nombre,
  tb.id AS termino_b_id,
  tb.nombre_canonico AS termino_b_nombre,
  COUNT(*) AS n_coocurrencias,
  COUNT(*) * 1.0 / (SELECT COUNT(DISTINCT informe_id) FROM silver_conclusion_items) AS soporte
FROM silver_conclusion_items sa
JOIN silver_conclusion_items sb ON sa.informe_id = sb.informe_id AND sa.id < sb.id
JOIN dim_termino_conclusion ta ON ta.id = sa.termino_conclusion_id
JOIN dim_termino_conclusion tb ON tb.id = sb.termino_conclusion_id
WHERE ta.tipo_item = 'DIAGNOSTICO' AND tb.tipo_item = 'DIAGNOSTICO'
GROUP BY ta.id, tb.id;
```

#### `gold_tendencias` (VIEW)

```sql
CREATE VIEW gold_tendencias AS
SELECT
  CAST(strftime('%Y', si.fecha_parseada) AS INTEGER) AS anio,
  CAST(strftime('%m', si.fecha_parseada) AS INTEGER) AS mes,
  de.nombre_canonico AS especie_nombre,
  dt.nombre_canonico AS termino_canonico,
  COUNT(DISTINCT si.informe_id) AS n_informes_con_termino
FROM silver_conclusion_items sci
JOIN silver_informes si ON si.informe_id = sci.informe_id
JOIN dim_termino_conclusion dt ON dt.id = sci.termino_conclusion_id
JOIN dim_especie de ON de.id = si.dim_especie_id
WHERE dt.tipo_item = 'DIAGNOSTICO'
  AND si.fecha_parseada IS NOT NULL
GROUP BY 1, 2, 3, 4;
```

**Reglas Gold:**
- Reconstruible 100% desde Silver.
- Idempotente: cada `build_gold_*` hace DELETE + INSERT.
- 100% denormalizado (los nombres canónicos como strings, no FKs).
- Las 2 vistas son `CREATE VIEW` puras — sin tabla materializada.

---

## 6. Operaciones

### 6.1 Setup inicial (una vez)

```bash
# 1. Crear venv
python -m venv venvvector
venvvector\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar .env (opcional, solo si se quiere PG futuro)
cp .env.example .env
# Editar PG_DSN si se quiere dejar listo (NO se usa hoy)

# 4. Verificar entorno
python scripts/verify_raw.py
```

### 6.2 Pipeline estándar (Silver existente, Gold nuevo)

```bash
# 1. Verificar RAW (idempotente)
python scripts/verify_raw.py

# 2. Construir Silver desde RAW (idempotente, ~30s para 2.893 informes)
python scripts/build_silver.py --phase all

# 3. Verificar Silver (idempotente, ~5s)
python scripts/verify_silver.py

# 4. Construir Gold desde Silver (NUEVO, ~10s para 2.893 informes)
python scripts/build_gold.py --phase all

# 5. Verificar Gold (NUEVO, ~1s)
python scripts/verify_gold.py

# 6. Conectar Power BI Desktop a gold.db
#    (ODBC SQLite driver, abrir gold.db, importar las 3 tablas + 2 vistas)
```

### 6.3 Pipeline de ingesta de un nuevo .docx

```bash
# 1. Drop el archivo .docx en la carpeta "Ecografía YYYY/..."
# 2. Ejecutar ingesta (escanea todo, UPSERT por sha256, idempotente)
python scripts/run_ingest.py --db sqlite

# 3. Re-ejecutar Silver para incorporar el nuevo informe
python scripts/build_silver.py --phase all

# 4. Re-ejecutar Gold
python scripts/build_gold.py --phase all

# 5. Verificar
python scripts/verify_silver.py && python scripts/verify_gold.py

# 6. Refrescar Power BI (botón "Refresh" en el .pbix)
```

**Frecuencia esperada:** el usuario ejecuta estos pasos cuando tiene 5-10 archivos nuevos (típicamente 1-2 veces por semana).

### 6.4 Reset total (emergency)

```bash
# Reset RAW
python scripts/run_ingest.py --db sqlite --reset

# Reset Silver
python scripts/build_silver.py --reset --phase all

# Reset Gold
python scripts/build_gold.py --reset --phase all

# Verificar todo
python scripts/verify_raw.py && python scripts/verify_silver.py && python scripts/verify_gold.py
```

---

## 7. Convenciones de nombres y estilo

### 7.1 Naming

| Capa | Tablas | Archivos | Funciones |
|---|---|---|---|
| RAW | `informes`, `hallazgos`, `conclusiones`, `errores_ingesta`, `embeddings` | `db.py`, `models.py` | `get_engine`, `upsert_informe` |
| Silver | `silver_*`, `dim_*`, `map_*`, `stg_*` | `silver_*.py` | `build_f1`, `build_f2`, ... |
| Gold | `gold_*` | `gold.py`, `models_gold.py` | `build_gold_diagnosticos`, ... |

**Prefijos obligatorios:**
- `silver_*` para todas las tablas Silver (incluyendo dims, maps, staging).
- `gold_*` para todas las tablas y vistas Gold.
- `raw.` para calificar tablas cuando se hace cross-DB (ej: `raw.informes` desde Gold).
- `stg_*` para staging (datos pendientes de revisión manual).
- `map_*` para tablas puente de normalización RAW→dim.

**NO se usan prefijos** `vw_*`, `mat_*`, `tmp_*`, `arch_*`. Las vistas se llaman `gold_*` sin prefijo extra.

### 7.2 Estilo de código

- **Python 3.11+**, type hints en funciones públicas.
- **`from __future__ import annotations`** en cada archivo.
- **Docstrings** solo en funciones no obvias (las que tienen lógica no trivial).
- **NO usar** `ABC`, `Protocol`, `@dataclass` salvo necesidad justificada.
- **NO usar** frameworks de DI, factories, builders.
- **Logging:** `import logging; log = logging.getLogger(__name__)`. Formato simple: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`.
- **Errores:** raise con mensajes claros. Loggear con traceback. NO capturar y silenciar.
- **Tests:** no hay framework de tests instalado. Los `verify_*.py` SON los tests (integration tests sobre la DB real).

### 7.3 Estilo SQL

- **Nombres en snake_case.**
- **PK auto-increment: `id INTEGER PRIMARY KEY AUTOINCREMENT`** (SQLite) / `SERIAL` (PG).
- **FKs siempre con `REFERENCES table(col)`** cuando aplique (SQLite las declara pero no las enforce por default; PG sí).
- **Índices:** `ix_<tabla>_<columna>` para simples, `ix_<tabla>_<col1>_<col2>` para compuestos.
- **CHECK constraints:** solo cuando el dominio es cerrado y verificable (ej: `lateralidad IN ('izq','der','bilat')`).
- **Strings:** siempre `'` (comilla simple), nunca `"`.
- **Aliases:** `AS palabra` (con AS explícito).
- **CTEs:** permitidos cuando simplifican (no por moda).

---

## 8. Pipeline lógico completo (5 capas)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ CAPA 0: Datos fuente                                                      │
│   Ecografía 2022/ ... Ecografía 2026/   (.docx files, NO se tocan)       │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ (manual: drop de archivos por el usuario)
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ CAPA 1: RAW                                                               │
│   scripts/run_ingest.py                                                   │
│   → extract.py → db.upsert_informe → INSERT OR IGNORE por sha256         │
│   → INSERT a raw.hallazgos + raw.conclusiones                            │
│   → log_error si falla                                                    │
│   📁 informes.db (22 MB, 2.893 informes)                                  │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ (idempotente, ejecutable N veces)
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ CAPA 2: Silver                                                            │
│   scripts/build_silver.py --phase all                                    │
│   → F1: silver_informes (UPSERT por informe_id)                          │
│   → F2: dim_raza + map_* + stg_razas_detectadas                          │
│   → F3: dim_atributo + dim_organo_atributo + silver_atributos_hallazgo    │
│   → F4: dim_valor_atributo consolidado + map_atributo_valor               │
│   → F5: dim_termino_conclusion + silver_conclusion_items                  │
│   📁 silver.db (41 MB, 24 tablas, 162.451 filas totales)                 │
│                                                                          │
│   Verificación: scripts/verify_silver.py                                  │
│   → 19 checks agrupados en secciones F1-F5                                │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ (idempotente, ejecutable N veces)
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ CAPA 3: Gold (NUEVA)                                                      │
│   scripts/build_gold.py --phase all                                       │
│   → build_gold_diagnosticos: DELETE + INSERT (~2s, 16.939 filas)         │
│   → build_gold_demografia:   DELETE + INSERT (~1s, 2.893 filas, cross-RW)│
│   → build_gold_hallazgos:    DELETE + INSERT (~5s, 114.753 filas)        │
│   → create_gold_views:       DROP + CREATE VIEW (instantáneo)             │
│   📁 gold.db (~30 MB, 3 tablas + 2 vistas)                                │
│                                                                          │
│   Verificación: scripts/verify_gold.py                                    │
│   → 8 checks (counts, FKs, NULLs, índices)                                │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ (read-only)
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ CAPA 4: Consumidores                                                      │
│   Power BI Desktop → ODBC SQLite → SELECT * FROM gold_diagnosticos       │
│   Scripts Python ad-hoc → sqlite3.connect('gold.db')                     │
│   (Futuro) LLMs → embeddings table (vía RAW.embeddings cuando se llene)  │
└──────────────────────────────────────────────────────────────────────────┘
```

**Cada capa es idempotente.** Si el pipeline se interrumpe a mitad, se re-ejecuta desde la última capa completa y queda igual.

---

## 9. Estrategia de verificación (los tests del proyecto)

El proyecto NO tiene framework de tests (`unittest`, `pytest`). En su lugar, los `verify_*.py` SON los tests:

| Script | Capa | Tipo | Chequeos |
|---|---|---|---|
| `verify_raw.py` | RAW | Integration | Schema + idempotencia + FKs |
| `verify_silver.py` | Silver | Integration | 19 checks F1-F5 (paridad de counts, cobertura, FKs, no-match) |
| `verify_gold.py` | Gold | Integration | 8 checks (counts, FKs, NULLs, índices, vistas existen) |

**Patrón de ejecución:**

```bash
# Verificación rápida pre-commit (~10s total)
python scripts/verify_raw.py && \
python scripts/verify_silver.py && \
python scripts/verify_gold.py
```

**Si alguno falla → NO se commitea → se arregla primero.**

---

## 10. Configuración y variables de entorno

### 10.1 Variables soportadas

| Variable | Default | Propósito | Usado hoy |
|---|---|---|:---:|
| `PG_DSN` | — | Connection string PostgreSQL para migración futura | NO |
| `SILVER_PG_DSN` | — | Alternativa a `PG_DSN` solo para Silver | NO |

**Hoy solo se usa SQLite.** Las variables PG existen en `.env.example` para que el proyecto esté "1 línea de cambio" listo, pero **no se invocan**.

### 10.2 Archivo `.env` actual

```
PG_DSN=postgresql+psycopg://usuario:password@host:puerto/dbname
```

(El valor real de `PG_DSN` está en `.env` pero **NO se lee en el flujo SQLite**. Existe para futura migración.)

### 10.3 Archivo `.env.example`

Plantilla con la variable comentada o vacía. El usuario la rellena solo cuando decide migrar.

---

## 11. Plan de mantenimiento a 5 años

### 11.1 Escenario actual (2026, 2.893 informes)

- Pipeline completo (RAW → Silver → Gold): ~40 segundos.
- `gold.db`: ~30 MB.
- Power BI Desktop abre `gold.db` instantáneamente.

### 11.2 Escenario año 2 (2027, ~4.500 informes)

- Volumen +55%. Pipeline ~60 segundos.
- `gold.db`: ~45 MB.
- **Cambios necesarios:** ninguno. Solo ejecutar el pipeline más veces.

### 11.3 Escenario año 3 (2028, ~6.000 informes)

- Volumen +100% vs 2026. Pipeline ~90 segundos.
- `gold.db`: ~60 MB.
- **Cambios necesarios:** ninguno. SQLite sigue siendo suficiente.

### 11.4 Escenario año 5 (2030, ~10.000 informes)

- Volumen +250% vs 2026. Pipeline ~2-3 minutos.
- `gold.db`: ~100 MB.
- **Cambios necesarios:** ninguno en términos de arquitectura. **PERO** considerar:
  - Convertir `gold_coocurrencias` de VIEW a TABLE si el self-join pasa de 25ms a >500ms.
  - Convertir `gold_tendencias` de VIEW a TABLE si el LAG window function pasa de 25ms a >1s.
- **Trigger explícito:** medir la latencia con `EXPLAIN QUERY PLAN` o `EXPLAIN ANALYZE` (PG). Si >500ms en self-join o window → materializar.

### 11.5 Escenario año 7+ (2032, ~13.000+ informes)

- Volumen +350% vs 2026.
- `gold.db`: ~130 MB.
- SQLite empieza a sufrir en queries analíticas pesadas (>5s).
- **Único momento donde se justifica migrar a PostgreSQL.** Y el costo es:
  - Provisionar PG (1 VPS).
  - Cambiar `.env` `DATABASE_URL=postgres...`.
  - `db.py:42-50` y `silver_db.py:42-48` ya soportan ambos motores.
  - `gold.py` también.
  - Verificar que los 3 `verify_*.py` pasan contra PG.
  - **Tiempo estimado: 1 día.**

### 11.6 Resumen del plan de mantenimiento

| Año | Informes | Acción |
|---|---:|---|
| 2026 | 2.893 | Estado actual. Construir Gold. |
| 2027 | ~4.500 | Solo ejecutar pipeline más seguido. |
| 2028 | ~6.000 | Sin cambios. |
| 2029 | ~7.500 | Sin cambios. |
| 2030 | ~9.000 | Medir latencias. Si >500ms, materializar vistas. |
| 2031 | ~10.500 | Medir latencias. Considerar particionar Silver (NO Gold). |
| Cuando se cumplan los triggers de §12 | ~13.000+ | Migrar a PG. **1 día de trabajo.** |

**No se necesita ninguna decisión arquitectónica en los próximos 5 años.** Todo lo que pueda hacer falta ya está preparado para 1-cambio-de-línea.

---

## 12. Cuando migrar a PostgreSQL (regla explícita)

**NO se migra a PG por:**
- "Es mejor práctica".
- "El proyecto es serio".
- "El VPS ya está provisionado".
- "Tengo ganas de aprender PG".
- "Cualquier consulta en internet dice que PG es mejor que SQLite".

**SÍ se migra a PG cuando se cumple CUALQUIERA de estas condiciones (medibles):**

1. **Latencia >2s en queries analíticas típicas** (`top 10 diagnósticos`, `media de grosor de pared vesical`, etc.) medida con Power BI o script Python.
2. **Concurrencia:** se necesita que 2+ personas consulten la DB simultáneamente con latencia aceptable.
3. **Multi-device:** el usuario quiere acceder a Gold desde 2+ dispositivos.
4. **Volumen de datos que supere la capacidad de SQLite** (estimado en >100k informes o >1M filas en tablas fact).
5. **Backup remoto automático:** SQLite local se reemplaza por PG con `pg_dump` automático.

**Si ninguna condición se cumple → SQLite sigue siendo la opción correcta.** El costo de mantener un PG (VPS, backups, actualizaciones de seguridad, monitoreo) es ~10x mayor que mantener un SQLite local.

---

## 13. Lo que se hace al cerrar este documento

### 13.1 Acciones inmediatas (post-aprobación del usuario)

1. ✅ Eliminar 19 scripts audit/profile/_* legacy.
2. ✅ Eliminar `analytics.py`.
3. ✅ Eliminar `bronze.db`, `data.db`, `raw.db`, `reports.db`.
4. ✅ Eliminar `_purgatorio/`.
5. ✅ Mover `backup-20260618/` a `docs/archive/`.
6. ✅ Eliminar `f5_build_log.txt`, `f5_verify_log.txt`.
7. ✅ Fusionar los 6 `verify_silver_f*.py` en 1 `verify_silver.py`.
8. ✅ Crear `verify_raw.py` (no existía).
9. ✅ Actualizar `README.md` para reflejar la estructura final.

### 13.2 Acciones Gold MVP (Fase 1, post-limpieza)

10. ✅ Crear `src/informes_vet/models_gold.py` con schema 3 tablas + 2 vistas.
11. ✅ Crear `src/informes_vet/gold.py` con build functions.
12. ✅ Crear `scripts/build_gold.py` CLI.
13. ✅ Crear `scripts/verify_gold.py`.
14. ✅ Crear `gold.db`, poblar, verificar.

### 13.3 Acciones posteriores (solo si aparecen triggers reales)

- **Fase 2:** crear el primer dashboard Power BI.
- **Fase 3:** si la pregunta "¿cuál es la raza más frecuente en nefropatía?" se vuelve recurrente, ejecutar F6 mini-ETL para poblar `dim_raza` desde RAW (sin reabrir Silver).
- **Fase 4:** si las vistas Gold pasan >500ms, materializarlas.
- **Fase 5:** si SQLite sufre, migrar a PG (1 día).

---

## 14. Regla de incorporación de complejidad

Todo componente nuevo (framework, patrón, dependencia, carpeta, archivo de configuración) que se proponga agregar al proyecto debe responder afirmativamente las siguientes cuatro preguntas:

1. **¿Qué problema concreto resuelve?** — Debe ser un problema observable en el proyecto actual, no una eventualidad futura hipotética.
2. **¿Ese problema existe hoy?** — Debe existir evidencia medible (latencia >X ms, frecuencia de error >Y, tiempo perdido >Z horas/mes) que justifique la intervención.
3. **¿Puede resolverse modificando código existente en lugar de agregar una nueva capa?** — Antes de crear una nueva abstracción, verificar si el código existente se puede extender directamente.
4. **¿El beneficio supera claramente el costo de mantenimiento durante los próximos cinco años?** — Considerar tiempo de aprendizaje, deuda técnica acumulada, superficie de bugs y costo de actualizar la dependencia.

Si **alguna** respuesta es negativa, **el componente no debe incorporarse**. La carga de la prueba recae en quien propone el cambio.

Esta regla aplica a:

- Nuevas dependencias de Python (pip packages).
- Nuevas carpetas o reorganizaciones de archivos.
- Nuevos patrones arquitectónicos (Repository, Service, Builder, etc.).
- Nuevos frameworks de cualquier tipo.
- Cualquier refactor que aumente el LOC sin resolver un problema concreto y actual.

---

## 15. Componentes actualmente innecesarios

Esta sección lista componentes que **no son necesarios en el estado actual del proyecto**, pero **pueden incorporarse en el futuro** cuando exista un requerimiento concreto y medible que los justifique, previa aprobación de los cuatro criterios definidos en §14.

**Ningún elemento de esta lista está prohibido.** Su ausencia refleja la decisión deliberada de **no introducir complejidad hasta que sea útil**.

| Componente | Por qué no es necesario hoy | Trigger para incorporarlo |
|---|---|---|
| FastAPI / framework web | El consumidor es Power BI Desktop, que lee SQLite directo vía ODBC. | Necesidad de exponer Gold vía HTTP (Power BI Service en la nube, dashboard web, API para LLM externo). |
| Docker / Kubernetes | El deploy es "copiar la carpeta al laptop del usuario". | Deployment en múltiples servidores con orquestación centralizada. |
| systemd / daemon | El usuario ejecuta los scripts manualmente cuando tiene archivos nuevos. | Pipeline 100% automatizado sin intervención humana. |
| Watchdog (detector de archivos) | El usuario arrastra archivos al script (5 archivos/día). | Detección automática sin intervención humana. |
| Alembic / framework de migrations | Las migraciones declaradas como dict Python en `silver_db.py` son suficientes. | Cambios de schema frecuentes con necesidad de rollback automático. |
| PostgreSQL (operativo) | SQLite aguanta el volumen y la latencia esperada. | Ver §12 para los triggers medibles. |
| Schemas separados en PG | No aplica en SQLite. | Migración efectiva a PostgreSQL. |
| Partitioning | No hay problema de escala. SQLite aguanta 1M+ filas. | Latencia >2s en queries analíticas por fecha. |
| DLQ automatizada | El log + revisión manual funciona para el volumen actual. | Volumen alto con errores frecuentes que justifiquen retry automático. |
| ORM (SQLAlchemy ORM, SQLModel, etc.) | SQLAlchemy Core es suficiente para el volumen y la complejidad de queries del proyecto. | Lógica de dominio compleja que se beneficie de mapping objeto-relacional. |
| Framework de testing (pytest, etc.) | Los `verify_*.py` SON los integration tests. Cubren el 100% de los asserts del proyecto. | Crecimiento del código que justifique unit tests aislados. |
| Repository / Service Layer / Builder / Factory / Adapter | No hay lógica de negocio que justifique capas intermedias. | Lógica de dominio con múltiples implementaciones intercambiables. |
| CQRS / Event Bus / Saga / Outbox | Silver escribe, Gold lee. Ya están separados físicamente. | Múltiples consumidores que reaccionan a eventos del pipeline. |
| Dependency Injection framework | Python sin framework es DI por convención. | Múltiples implementaciones intercambiables con configuración declarativa. |
| pydantic-settings | `os.environ.get()` con default basta para las variables actuales. | >10 variables de configuración con validación compleja. |
| structlog / loguru | `logging` stdlib con formato simple es suficiente. | Necesidad de logging estructurado para agregadores externos. |
| OpenTelemetry / Prometheus / Sentry | No hay infraestructura distribuida que monitorear. | Deployment multi-servidor con SLOs medibles. |
| Cliente LLM (openai, anthropic, sentence-transformers, chromadb) | El placeholder `raw.embeddings` existe pero no se llena. | Necesidad concreta de embeddings o clasificación LLM. |

**Regla general:** antes de incorporar cualquier componente de esta lista, ejecutar los cuatro criterios de §14. Si todos pasan, se reabre este documento y se documenta la decisión con justificación cuantitativa.

---

## 16. Veredicto final

### 16.1 Arquitectura confirmada

- **Lenguaje:** Python 3.11+.
- **DB:** SQLite (operativa), PostgreSQL (preparada para migración 1-línea).
- **ORM:** SQLAlchemy Core. Suficiente para el volumen y la complejidad actuales del proyecto; un ORM completo no aporta valor cuando las queries son explícitas y los schemas son pequeños.
- **Pipeline:** RAW → Silver → Gold → Power BI.
- **Verificación:** scripts `verify_*.py` (integration tests sin framework).
- **CLI:** argparse stdlib (nunca Click/Typer).
- **Logging:** `logging` stdlib.
- **Config:** `os.environ` + `.env`.
- **Testing:** sin framework (verify_*.py SON los tests).
- **Packaging:** sin `pyproject.toml`, sin `setup.py`. El proyecto se ejecuta como script Python puro.

### 16.2 Métricas objetivo

| Métrica | Valor target | Cómo se mide |
|---|---:|---|
| Cobertura RAW | 100% | `verify_raw.py` |
| Idempotencia Silver | 3 runs consecutivos con `rows_written=0` en el 2do y 3ro | `verify_silver.py` |
| Idempotencia Gold | 3 runs consecutivos con `rows_written=0` en el 2do y 3ro | `verify_gold.py` |
| Tiempo pipeline completo | <60s para 2.893 informes | `time python scripts/build_*.py` |
| LOC productivos | <10.000 | `wc -l src/informes_vet/*.py scripts/*.py` |
| Scripts legacy | 0 | `ls scripts/ \| grep -E '_audit_\|_profile_\|audit_' \| wc -l` |
| Tests pasando | 100% | `verify_*.py` todos exit 0 |

### 16.3 Firma

**Este documento es la fuente única de verdad arquitectónica del proyecto VetTalk a partir del 2026-06-26.**

Cualquier cambio arquitectónico futuro requiere:
1. Reabrir este documento.
2. Documentar el cambio con justificación cuantitativa.
3. Aprobar el cambio antes de implementarlo.

**Después de aprobar este documento, no se discute más arquitectura. Se construye funcionalidad.**

---

## Anexo A — Resumen ejecutivo (1 página)

**VetTalk** es un pipeline ETL para extraer información estructurada de informes ecográficos veterinarios en formato `.docx` y exponerla para análisis clínico.

**Arquitectura congelada:**
- **Stack:** Python 3.11 + SQLite + SQLAlchemy Core.
- **Pipeline:** iCloud (manual) → RAW (informe.db, 5 tablas) → Silver (silver.db, 24 tablas) → Gold (gold.db, 3 tablas + 2 vistas) → Power BI Desktop.
- **Verificación:** 3 scripts (`verify_raw.py`, `verify_silver.py`, `verify_gold.py`) que ejecutan asserts sobre la DB.
- **Patrones prohibidos:** Hexagonal, Repository, Service Layer, Builder, Factory, Adapter, CQRS, UoW, DI framework, ABCs, FastAPI, Docker, K8s, systemd, Watchdog, Daemons, Alembic, PostgreSQL operativo, Partitioning, DLQ, Observability enterprise, Lineage por fila.

**Métricas actuales (2026-06-26):**
- 2.893 informes RAW.
- 162.451 filas Silver (4 facts + 158k en atributos).
- Pipeline completo: ~30 segundos.
- `gold.db` aún vacío (a construir en Fase 1).

**Próximo paso (post-aprobación):**
- Construir `gold_diagnosticos`, `gold_demografia`, `gold_hallazgos` + 2 vistas en `gold.db`.
- Tiempo estimado: 2-3 días.
- Resultado: Power BI Desktop puede abrir `gold.db` y analizar 62% del catálogo de preguntas clínicas.

**Migración a PostgreSQL:** NO ahora. Solo cuando se cumplan condiciones medibles (latencia >2s, multi-device, >100k informes). El código actual soporta PG con 1 cambio de `.env`.

---

*Fin del documento. Aprobado por el usuario el ____ / ____ / 2026.*