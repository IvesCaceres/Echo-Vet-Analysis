# Gold — Revisión Arquitectónica YAGNI/KISS

**Fecha:** 2026-06-26
**Tipo:** Auditoría honesta y decisoria. Cierra el debate arquitectónico antes de escribir código.
**Estado actual:** Silver congelado (F1–F5, F2 Completion Release ejecutado, 19/19 verify checks OK).
**Documentos previos que este revisa y, en su mayoría, descarta:**
- `GOLD_DESIGN_V1.md` (9 tablas, 5 dominios + 3 dim + 1 calidad)
- `GOLD_PRE_AUDIT_FINAL.md` (refinado a 6 tablas + 3 vistas)
- `GOLD_FINAL_PRE_IMPLEMENTATION_REVIEW.md` (refinado a MVP 4 tablas)
- `PRODUCTION_ARCHITECTURE_V1.md` (VPS + watchdog + systemd + FastAPI + DLQ + partitioning + 5 schemas PG)

---

## 0. Restricciones reales del proyecto (no negociables)

Antes de auditar cualquier componente, fijo el universo de decisiones. Estas restricciones son **datos del proyecto**, no opiniones:

| # | Restricción | Fuente |
|---|---|---|
| 1 | Una sola veterinaria | Mensaje del usuario |
| 2 | ~1.500 informes/año (~125/mes, ~5/día hábil) | Rampa observada 2022→2025 |
| 3 | Crecimiento muy bajo, estructura estable 5+ años | Mensaje del usuario |
| 4 | Sin multi-clínica | Mensaje del usuario |
| 5 | Sin usuarios concurrentes (1 veterinario) | Mensaje del usuario |
| 6 | Sin alta disponibilidad | Mensaje del usuario |
| 7 | Sin escalabilidad horizontal | Mensaje del usuario |
| 8 | Sin microservicios | Mensaje del usuario |
| 9 | Sin múltiples motores de DB | Mensaje del usuario |
| 10 | Un solo mantenedor (el usuario) | Mensaje del usuario |
| 11 | Optimizar para: mínima complejidad, mínimo código, mínimo mantenimiento, máxima legibilidad, máxima velocidad de desarrollo | Mensaje del usuario |

**Implicaciones inmediatas:**

- **PG_DSN ya existe pero no se usa.** El usuario corre todo en SQLite local. Migrar a PG hoy es **trabajo sin valor analítico nuevo**.
- **PG_DSN es 1 línea de código cambiar.** Si el día de mañana se necesita PG, el switch es `get_engine("sqlite")` → `get_engine("postgres")`. Ya funciona (verificado en `db.py:42-50`).
- **El "usuario final" del Gold es Power BI.** No es una API. No es un dashboard web. Es un archivo `.pbix` que se conecta a SQLite.
- **No hay trigger automático.** El usuario corre scripts manualmente cuando quiere (o una vez por semana). El "watcher" es una persona, no un daemon.

---

## 1. Metodología de auditoría

Para cada componente propuesto en las cuatro arquitecturas previas, respondo 4 preguntas y emito un veredicto:

1. **¿Qué problema resuelve?** (definición técnica)
2. **¿Ese problema existe en este proyecto?** (constraint check vs §0)
3. **¿Cuál es el costo de mantener esa abstracción?** (LOC + carga cognitiva)
4. **¿Qué tan difícil sería agregarla después si hace falta?** (deferral cost)

**Veredictos posibles:**
- 🟢 **IMPRESCINDIBLE** — sin esto el proyecto no entrega valor, o el costo de NO hacerlo es > costo de hacerlo.
- 🟡 **ÚTIL PERO PUEDE ESPERAR** — tiene valor, pero solo cuando aparezca una necesidad concreta (lo listo como "trigger" para agregarlo).
- 🔴 **SOBREINGENIERÍA** — resuelve un problema que no existe en este proyecto y agrega superficie de mantenimiento.

---

## 2. Auditoría componente por componente

### 2.1 Patrones arquitectónicos (de las propuestas previas)

#### 🔴 Hexagonal Architecture (puertos y adaptadores)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Aislar lógica de negocio de infraestructura para poder testear/mockear sin DB real |
| ¿Existe en este proyecto? | **No.** Las "queries de Gold" son SELECT con JOINs. No hay lógica de negocio compleja que justifique separación. |
| Costo de mantener | +5 capas de indirección (domain/ports/adapters/application/infrastructure). Estimar 2x–3x más LOC que un script monolítico bien escrito. |
| Dificultad de agregar después | **Trivial.** Es un refactor cosmético. Si algún día la lógica se vuelve compleja, se refactoriza. |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** La complejidad del proyecto (un ETL con ~10 queries) no justifica 5 capas. El código de Silver ya es monolítico (`silver_etl.py` 78KB) y funciona. Hexagonal es la solución a un problema que aparece con 10+ devs y múltiples deployments.

---

#### 🔴 Repository Pattern (un repository por tabla)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Encapsular acceso a datos en una clase testeable sin tocar SQL directo |
| ¿Existe en este proyecto? | **No.** Las queries de Gold son 1-2 SQLs por tabla. Repository agregaría ~80 LOC por tabla para envolver 5 líneas de SQL. |
| Costo de mantener | Por tabla Gold: 80 LOC de clase + interface + tests + documentación. Para 4 tablas: 320 LOC. |
| Dificultad de agregar después | **Trivial.** Es agregar una clase que envuelve SQL. 30 min por tabla si alguna vez hace falta. |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** El "repository" aquí se llamaría `def get_diagnosticos(): return session.execute(text("SELECT ..."))`. La indirección no aporta nada.

---

#### 🔴 Service Layer (lógica de negocio separada)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Centralizar reglas de negocio (ej: "qué es un paciente recurrente", "cómo se calcula lift") en un lugar testeable |
| ¿Existe en este proyecto? | **No.** Las reglas son: SELECT + INSERT. No hay "lógica de negocio" que requiera testeo unitario aislado de DB. |
| Costo de mantener | Una capa extra entre SQL y consumers. Indirección sin valor. |
| Dificultad de agregar después | **Trivial.** Se mueven las funciones de un `.py` a otro. |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** Si algún día hay lógica compleja (ej: "calcular score de riesgo clínico"), se mete en una función pura testeable. No requiere una "capa service".

---

#### 🔴 Builder Pattern (constructores de objetos complejos)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Construcción incremental de objetos con muchos campos opcionales |
| ¿Existe en este proyecto? | **No.** Los registros Gold se construyen con un INSERT directo desde un SELECT. No hay objetos complejos. |
| Costo de mantener | 50-100 LOC de boilerplate por cada builder. |
| Dificultad de agregar después | **Trivial.** |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** Las filas Gold son tuplas (id, columna1, ..., columnaN). Se construyen en una línea SQL.

---

#### 🔴 Domain Models (pydantic / dataclass separados de SQLAlchemy)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Tener modelos ricos (con métodos, validación) independientes del schema DB |
| ¿Existe en este proyecto? | **No.** El "modelo" es la tabla misma. Si SQLAlchemy Core ya tiene el schema, agregar dataclass encima es duplicar. |
| Costo de mantener | Cada cambio de schema requiere tocar 2 archivos (SQLAlchemy + dataclass). |
| Dificultad de agregar después | **Trivial.** Se agrega una clase al lado cuando se necesite. |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** Power BI lee SQL directamente. No consume objetos Python. Los dataclass no se serializan a ningún lado.

---

#### 🔴 EnginePort + Multi-engine factory

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Cambiar de motor (SQLite → PG) sin tocar código de aplicación |
| ¿Existe en este proyecto? | **Parcialmente.** El proyecto corre 100% en SQLite hoy. La migración a PG está en `.env` pero no se usa. |
| Costo de mantener | El código actual (`db.py:42-50`) ya tiene esto implementado: `get_engine("sqlite", root)` vs `get_engine("postgres", root)`. **No requiere más trabajo.** |
| Dificultad de agregar después | **Ya está hecho.** Costo marginal: 0. |

**Veredicto:** 🟢 **IMPRESCINDIBLE** (ya implementado, no requiere esfuerzo). Mantener como está. NO agregar más abstracción (ej: `EnginePort` interface, `SqliteAdapter`/`PostgresAdapter` separados).

---

#### 🔴 ClockPort (abstracción de tiempo para tests)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Poder testear "qué pasa si hoy es 2027-01-01" sin cambiar el reloj del sistema |
| ¿Existe en este proyecto? | **No.** No hay tests temporales. Los ETL runs usan `datetime.now()` y eso está bien. |
| Costo de mantener | Una interface + 2 implementaciones + DI para inyectar. ~50 LOC. |
| Dificultad de agregar después | **Trivial.** `from datetime import datetime; dt = datetime.now()` se cambia a `dt = clock.now()` en 5 min. |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** Si algún día hay tests que dependen de tiempo, se inyecta `monkeypatch.setattr(datetime, 'now', ...)`. No requiere una "abstracción de reloj".

---

#### 🔴 Unit of Work (transacciones explícitas)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Manejar transacciones multi-tabla con rollback explícito |
| ¿Existe en este proyecto? | **No.** Los ETL actuales usan `with engine.begin() as conn:` que es el patrón canónico de SQLAlchemy para esto. Ya hay Unit of Work (es el `Connection` de SQLAlchemy). |
| Costo de mantener | Reescribir lo que SQLAlchemy ya da gratis. |
| Dificultad de agregar después | **N/A.** Ya existe en SQLAlchemy. |

**Veredicto:** 🔴 **SOBREINGENIERÍA (encima de lo que ya hay).** `engine.begin()` ES Unit of Work. Agregar una capa encima es duplicar funcionalidad built-in.

---

#### 🔴 Dependency Injection (framework como `dependency-injector` o `inject`)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Inyectar dependencias sin acoplar |
| ¿Existe en este proyecto? | **No.** Las dependencias se pasan como argumentos de función o se importan. Eso ya es DI manual. |
| Costo de mantener | Agregar contenedor + configuración + lifecycle. ~200 LOC + curva de aprendizaje. |
| Dificultad de agregar después | **Trivial.** Las funciones Python ya reciben lo que necesitan. No hay que "convertir" nada. |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** Python sin framework es DI por convención. Los módulos se importan y las funciones reciben argumentos. Agregar un framework es agregar peso para resolver un problema que el lenguaje ya resolvió.

---

#### 🔴 Domain Events (event bus interno)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Desacoplar componentes que reaccionan a eventos ("informe creado" → "Gold rebuild") |
| ¿Existe en este proyecto? | **No.** El usuario corre scripts manualmente. No hay "eventos" — hay un `python build_gold.py` que se ejecuta cuando quiere. |
| Costo de mantener | Bus + handlers + tests + documentación. ~300 LOC. |
| Dificultad de agregar después | **Fácil.** Se puede usar `blinker` o `pyee` si algún día hace falta, pero es improbable. |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** "El usuario ejecuta `build_gold.py` cuando quiere actualizar" ya es el event bus. Es 1 línea de bash.

---

#### 🔴 Factories abstractas

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Centralizar creación de objetos complejos |
| ¿Existe en este proyecto? | **No.** |
| Costo de mantener | 30-100 LOC de boilerplate por factory. |
| Dificultad de agregar después | **Trivial.** |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** Las "factories" serían `def build_gold_diagnosticos():` que ejecuta un INSERT. Una función Python normal.

---

#### 🔴 Adapters (capa de adaptación entre dominio e infraestructura)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Ocultar detalles de DB detrás de una interface |
| ¿Existe en este proyecto? | **No.** El detalle (SQLite vs PG) está en `db.py` y solo ahí. |
| Costo de mantener | Wrapper por cada operación. 1 adapter = ~30 LOC. Para 4 tablas × 5 operaciones = 600 LOC. |
| Dificultad de agregar después | **Trivial.** |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** SQLAlchemy Core ya ES el adapter. Agregar otra capa encima es poner un adapter sobre el adapter.

---

#### 🔴 CQRS (separar lectura de escritura)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Optimizar lecturas y escrituras por separado |
| ¿Existe en este proyecto? | **No.** Gold es solo lectura (Power BI). Silver es solo escritura (ETL). No hay comandos ni queries mezclados. |
| Costo de mantener | 2 modelos (write-model, read-model) para cada tabla. |
| Dificultad de agregar después | **Trivial** (de hecho, ya está: Silver escribe, Gold lee). |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** Ya existe por accidente arquitectónico: Silver escribe, Gold lee. No requiere framework.

---

#### 🔴 Abstract base classes (jerarquías de herencia)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Compartir código entre clases hijas |
| ¿Existe en este proyecto? | **No.** Las tablas Gold son independientes entre sí. |
| Costo de mantener | Acoplamiento vía jerarquía. Cambios en base class rompen hijas. |
| Dificultad de agregar después | **Trivial.** |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** Sin código compartido entre tablas Gold, no hay base class que justifique existir.

---

#### 🔴 Múltiples packages (`domain/`, `application/`, `infrastructure/`)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Separar capas en el filesystem |
| ¿Existe en este proyecto? | **No.** El código actual (`src/informes_vet/`) tiene 13 archivos `.py` planos. Funciona. |
| Costo de mantener | Cada carpeta agrega imports relativos, `__init__.py`, navegación. Para 4 archivos Gold: ruido > señal. |
| Dificultad de agregar después | **Trivial.** Mover archivos entre carpetas es 5 minutos. |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** Carpeta `gold/` con 4 archivos `.py` dentro es suficiente. Subcarpetas `gold/builders/`, `gold/validators/`, `gold/lineage/` es ruido.

---

### 2.2 Componentes de infraestructura

#### 🔴 Alembic migrations (versionado de schema)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Tracking de cambios de schema en el tiempo, con rollback |
| ¿Existe en este proyecto? | **No, y no necesita.** El schema Gold se crea con 1 `CREATE TABLE` y queda fijo. Cambios futuros son raros y se hacen con `DROP TABLE + CREATE TABLE`. |
| Costo de mantener | Alembic setup: ~150 LOC. Cada migración: ~30 LOC. Tests de migración: ~30 LOC. |
| Dificultad de agregar después | **Media.** Alembic requiere reorganizar la creación de schema. 1-2 horas si se necesita. |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** Las migraciones Silver ya están como scripts Python ad-hoc (`silver_db.py:42-48`, `models_silver.py`). Gold puede usar el mismo patrón: 1 función `create_schema(engine)` que se llama al inicio.

---

#### 🔴 pydantic-settings (configuración tipada)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Cargar `.env` con tipos validados |
| ¿Existe en este proyecto? | **No.** El `.env` se lee con `os.environ.get("PG_DSN")`. Funciona para 2-3 variables. |
| Costo de mantener | Clase `Settings` con 5-10 campos tipados + tests. ~80 LOC. |
| Dificultad de agregar después | **Trivial.** Se agrega `pydantic-settings` y se importa en `db.py`. |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** `os.environ.get()` con fallback a default es suficiente para 2-3 variables de config.

---

#### 🟡 Multi-engine interface (`pg_insert` vs `sqlite_insert`)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | UPSERT portable entre SQLite y PG |
| ¿Existe en este proyecto? | **Sí, parcialmente.** `db.py:81-94` ya tiene el patrón condicional. |
| Costo de mantener | **Ya implementado.** ~15 LOC que detecta motor y elige la función correcta. |
| Dificultad de agregar después | **Ya hecho.** |

**Veredicto:** 🟢 **IMPRESCINDIBLE** (ya implementado). Mantener el patrón condicional inline. NO abstraer a un `UpsertAdapter`.

---

#### 🟡 Quality Observability Layer (drift detection, freshness check, etc.)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Detectar automáticamente "Gold está stale" o "calidad del extractor bajó" |
| ¿Existe en este proyecto? | **No, pero hay un proxy barato:** `verify_silver_*.py` ya cuenta filas, valida FKs, etc. |
| Costo de mantener | Drift detector: ~100 LOC. Freshness checker: ~50 LOC. Total: ~150 LOC + tests. |
| Dificultad de agregar después | **Trivial.** Es 1 query SQL que se ejecuta después del build: `SELECT MAX(gold_built_at) FROM gold_diagnosticos;`. |

**Veredicto:** 🟡 **ÚTIL PERO PUEDE ESPERAR.** Por ahora el usuario corre `verify_silver_f*.py` después de cada ETL (ya existe). Cuando haya Gold, `verify_gold_f*.py` cumplirá el mismo rol. NO construir un "drift detector" automatizado: el usuario detecta drift porque abre Power BI y ve que el número de diagnósticos no cuadra.

---

#### 🔴 Lineage tracking (gold_built_at, gold_run_id, silver_built_at por fila)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Saber "esta fila fue construida en tal run, basada en tal versión de Silver" |
| ¿Existe en este proyecto? | **No, y no se necesita.** El usuario no hace auditoría de linaje. Si una fila está mal, vuelve a correr el build. |
| Costo de mantener | 3 columnas extra por tabla Gold × 4 tablas = 12 columnas. +50 LOC de INSERT con esos campos. |
| Dificultad de agregar después | **Trivial.** Se agregan las columnas con `ALTER TABLE` y se actualiza el INSERT. |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** El linaje existe a nivel de RUN (tabla `silver_etl_runs` ya tiene esto). Por fila es overkill. Si el día de mañana se necesita, se agrega en 30 min.

---

#### 🔴 RazaProviderPort (cross-layer Gold→RAW)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Encapsular la excepción arquitectónica "Gold lee de RAW para raza" |
| ¿Existe en este proyecto? | **El problema sí (cross-layer existe), pero la "port" no.** |
| Costo de mantener | Interface + adapter + tests = ~80 LOC para envolver 1 SELECT. |
| Dificultad de agregar después | **N/A.** |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** El cross-layer es 1 query SQL (`SELECT raza FROM raw.informes WHERE id = ?`). No requiere una "port" formal. Si algún día molesta, se ejecuta F6 y se cierra el cross-layer.

---

#### 🔴 DriftChecker automático

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Alertar cuando Gold está desactualizado respecto a Silver |
| ¿Existe en este proyecto? | **No.** El usuario ejecuta el pipeline manualmente. Si se olvida, los números están stale. |
| Costo de mantener | Query periódica + lógica de comparación + alerta. ~100 LOC. |
| Dificultad de agregar después | **Trivial.** `SELECT COUNT(*) FROM gold_diagnosticos = SELECT COUNT(*) FROM silver_conclusion_items` después de cada build. |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** El "drift" se evita construyendo Gold en el mismo script que Silver (ver §4). Una transacción cubre ambos. Si el usuario corre Silver pero no Gold, ya sabe que Gold está stale.

---

### 2.3 Componentes de datos y queries

#### 🟢 gold_diagnosticos (TABLA)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Responder 38/62 preguntas del catálogo (DX1-DX10, E2-E8, SP1-SP4, base de T y C) |
| ¿Existe en este proyecto? | **Sí.** Tabla base del MVP. Sin ella, Gold no existe. |
| Costo de mantener | ~200 LOC Python + ~150 LOC SQL. 16,939 filas. Build <2s. |
| Dificultad de agregar después | N/A — primero a construir. |

**Veredicto:** 🟢 **IMPRESCINDIBLE.**

---

#### 🟢 gold_demografia (TABLA)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Responder preguntas demográficas (D1-D8, E1, E9, E10), base de joins con gold_diagnosticos |
| ¿Existe en este proyecto? | **Sí.** Cimentación de todas las queries con filtro demográfico. |
| Costo de mantener | ~250 LOC + ~180 LOC SQL. 2,893 filas. Build <1s. |
| Dificultad de agregar después | N/A. |

**Veredicto:** 🟢 **IMPRESCINDIBLE.**

---

#### 🟢 gold_hallazgos (TABLA)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Responder preguntas de hallazgos (H1-H10), series numéricas |
| ¿Existe en este proyecto? | **Sí.** Única fuente para "media de grosor de pared vesical por especie", "distribución de tamaños renales", etc. |
| Costo de mantener | ~280 LOC + ~200 LOC SQL. 114,753 filas. Build <5s. |
| Dificultad de agregar después | N/A. |

**Veredicto:** 🟢 **IMPRESCINDIBLE.**

---

#### 🟡 gold_dim_paciente (TABLA)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Deduplicar pacientes (1,485 vs 1,695 según regla) para análisis longitudinal |
| ¿Existe en este proyecto? | **El problema sí (la ambigüedad de dedup existe).** ¿Pero se necesita una TABLA? |
| Costo de mantener | ~300 LOC + lógica de dedup canónica. 2,500 filas. |
| Dificultad de agregar después | **Trivial.** Es un SELECT DISTINCT con la regla aplicada. Si urge, se crea la tabla. |

**Veredicto:** 🟡 **ÚTIL PERO PUEDE ESPERAR.** El usuario puede hacer `SELECT DISTINCT especie, nombre_paciente, tutor FROM silver_informes` directamente y obtener la respuesta. La TABLA solo se justifica si el análisis de recurrencia se vuelve una query frecuente. **Trigger para materializar:** cuando se ejecuten >5 queries distintas con `GROUP BY paciente` en Power BI.

---

#### 🟡 gold_coocurrencias (VIEW primero, TABLE después)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Responder preguntas de comorbilidad (C1-C8) sin self-join costoso |
| ¿Existe en este proyecto? | **El problema sí.** 22,708 pares posibles. |
| Costo de mantener | VIEW: ~80 LOC (un SELECT con self-join). TABLE: ~220 LOC. |
| Dificultad de agregar después | **Trivial.** VIEW → TABLE es cambiar la definición. |

**Veredicto:** 🟡 **ÚTIL PERO PUEDE ESPERAR.** A 2,893 informes, el self-join sobre `silver_conclusion_items` toma 28ms (medido en `GOLD_PRE_AUDIT_FINAL.md` §3.1). Eso es imperceptible en Power BI. VIEW es trivial: `CREATE VIEW gold_coocurrencias AS SELECT ... FROM silver_conclusion_items a JOIN silver_conclusion_items b ...`. **Trigger para materializar:** cuando el corpus supere ~50k informes (proyección 2028-2029).

---

#### 🟡 gold_tendencias (VIEW primero, TABLE después)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Series temporales mensuales/anuales con delta vs mes anterior |
| ¿Existe en este proyecto? | **El problema sí, pero la urgencia no.** |
| Costo de mantener | VIEW: ~80 LOC. TABLE con LAG: ~280 LOC. |
| Dificultad de agregar después | **Trivial.** |

**Veredicto:** 🟡 **ÚTIL PERO PUEDE ESPERAR.** A 2,893 informes, la serie mensual toma 25ms. VIEW cubre el 90% de las necesidades. **Trigger para materializar:** idem gold_coocurrencias (>50k informes) o cuando se requiera análisis de delta mensual.

---

#### 🔴 gold_dim_tiempo (VIEW)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Atributos precalculados de fecha (trimestre, semestre, día del año) |
| ¿Existe en este proyecto? | **No.** Power BI calcula estas cosas con `MONTH()`, `YEAR()`, `QUARTER()` nativos. |
| Costo de mantener | ~40 LOC para una VIEW de 50 filas. |
| Dificultad de agregar después | **Trivial.** |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** Power BI tiene funciones de fecha built-in. No se necesita una dimensión de tiempo.

---

#### 🔴 gold_dim_termino (VIEW)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Precomputar n_informes, n_items por término |
| ¿Existe en este proyecto? | **No.** `SELECT dim_termino_conclusion_id, COUNT(*) FROM gold_diagnosticos GROUP BY 1` es trivial. |
| Costo de mantener | ~50 LOC para una VIEW de 91 filas. |
| Dificultad de agregar después | **Trivial.** |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** `dim_termino_conclusion` ya existe en Silver. Power BI hace JOIN directo.

---

#### 🔴 gold_calidad_extraccion (VIEW o TABLE)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Exponer cobertura/cobertura F5 al consumidor |
| ¿Existe en este proyecto? | **No.** `silver_etl_runs` ya tiene estos datos. Power BI hace SELECT directo. |
| Costo de mantener | ~40 LOC para una VIEW de 21 filas. |
| Dificultad de agregar después | **Trivial.** |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** No se consume desde Power BI. Si el día de mañana se quiere un dashboard de calidad, se lee `silver_etl_runs` directamente.

---

### 2.4 Componentes de operaciones (de PRODUCTION_ARCHITECTURE_V1.md)

#### 🔴 Watcher daemon (watchdog + FastAPI)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Detectar nuevos .docx en <2s y subirlos automáticamente |
| ¿Existe en este proyecto? | **No.** El usuario ingiere manualmente con `run_ingest.py` cuando quiere. |
| Costo de mantener | Watcher + debounce + lock check + retry + heartbeat: ~400 LOC. Sumar systemd unit, FastAPI service, nginx config: ~600 LOC total. |
| Dificultad de agregar después | **Media.** Requiere un daemon siempre corriendo, manejar crashes, logs. 1-2 días. |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** El usuario ingiere 5 archivos al día. El costo de hacerlo manualmente es 30 segundos por día. El costo del watcher es: proceso siempre corriendo, debugging cuando se cae, configuración de iCloud path que cambia entre máquinas. **Trigger para construirlo:** cuando el usuario se vaya de vacaciones 2 semanas y quiera que el sistema ingiera sin él.

---

#### 🔴 FastAPI service (POST /api/ingest, GET /api/informes)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Exponer datos vía HTTP para consumidores externos |
| ¿Existe en este proyecto? | **No.** El consumidor es Power BI Desktop, que lee SQLite directo. |
| Costo de mantener | FastAPI app + endpoints + auth + nginx + certificados: ~500 LOC + DevOps. |
| Dificultad de agregar después | **Media.** 1-2 días. |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** Power BI Desktop abre `.db` directamente con el driver ODBC de SQLite. **Trigger para construirlo:** si el consumidor pasa a ser Power BI Service (en la nube) y necesita conectarse vía API, o si se construye una UI web.

---

#### 🔴 systemd timer (cada 5 min ejecuta pipeline)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Ejecutar el pipeline periódicamente sin intervención manual |
| ¿Existe en este proyecto? | **No.** El usuario corre scripts manualmente. |
| Costo de mantener | 2 archivos systemd + logs + monitoreo. ~100 LOC. |
| Dificultad de agregar después | **Trivial.** Es copiar 2 archivos `.service` + `.timer` a `/etc/systemd/system/`. |

**Veredicto:** 🔴 **SOBREINGENIERÍA (hoy).** El usuario ejecuta el pipeline cuando quiere actualizar Power BI. Si lo hace 1 vez por semana, no necesita timer. **Trigger para construirlo:** cuando el pipeline se vuelva "siempre actualizado" porque hay un consumidor en tiempo real.

---

#### 🔴 PostgreSQL VPS migration AHORA

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Centralizar DB en servidor remoto, acceder multi-dispositivo, backups gestionados |
| ¿Existe en este proyecto? | **No urge.** El proyecto corre en 1 laptop, 1 usuario. PG_DSN existe pero no se usa. |
| Costo de mantener | Setup PG + schemas + permisos + backups automatizados + monitoreo: ~2-3 días la primera vez, ~30 min/mes después. |
| Dificultad de agregar después | **Trivial.** `get_engine("sqlite")` → `get_engine("postgres")`. Toda la portabilidad ya está implementada. |

**Veredicto:** 🔴 **SOBREINGENIERÍA (hoy).** El costo de operación actual en SQLite es: 0 (no hay servidor que mantener, no hay backups remotos que verificar). PG solo agrega valor cuando hay multi-usuario, multi-device, o consultas concurrentes. **Trigger para migrar:** si la laptop se rompe y el usuario pierde 1 año de trabajo. **Acción concreta:** resolver el riesgo de pérdida con un script de backup automático a Google Drive / Dropbox, no migrando a PG.

---

#### 🔴 Schemas separados (`raw`, `silver`, `gold`, `etl`, `audit`)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Permisos granulares por schema, organización lógica |
| ¿Existe en este proyecto? | **No.** SQLite tiene 1 schema (default). PG puede tener schemas pero no se usan. |
| Costo de mantener | Prefijo `silver.` en cada query. Permisos por schema. |
| Dificultad de agregar después | **Trivial.** Si se migra a PG, se crean los schemas en 1 SQL. |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** En SQLite todo vive en `main`. Power BI consume tablas por nombre, no por schema. Cuando se migre a PG (si ocurre), se crean los schemas. Por ahora, no.

---

#### 🔴 Dead Letter Queue (`etl.dlq`)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Manejar archivos que fallan al ingestar para reintento posterior |
| ¿Existe en este proyecto? | **Sí, parcialmente.** `errores_ingesta` + `errores_ingest.log` ya cubren esto. |
| Costo de mantener | Tabla DLQ + lógica de retry automático + UI de inspección. ~150 LOC. |
| Dificultad de agregar después | **Trivial.** |

**Veredicto:** 🔴 **SOBREINGENIERÍA.** El usuario ve los errores en el log y los corrige manualmente. No hay volumen que justifique automatización.

---

#### 🔴 Partitioning por `anio` en PostgreSQL

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Queries por año son 10x más rápidas, archivado de años viejos es trivial |
| ¿Existe en este proyecto? | **No.** 41 MB en SQLite. No hay problema de performance. |
| Costo de mantener | Partición por año = +30% complejidad en schema. Queries deben incluir `anio` en WHERE. |
| Dificultad de agregar después | **Media-Alta.** Particionar después requiere reorganizar la tabla. 1-2 días. |

**Veredicto:** 🔴 **SOBREINGENIERÍA (hoy).** SQLite aguanta 1M filas sin partitioning. Con 1,500 informes/año, en 5 años hay 7,500 informes (no llega ni a 1M ni cerca). **Trigger para particionar:** si SQLite empieza a sufrir con queries por fecha (no esperable antes de 2030+).

---

#### 🟢 Verificación post-build (`verify_gold_f*.py`)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | Detectar bugs en Gold (filas faltantes, FKs huérfanas, cobertura incompleta) |
| ¿Existe en este proyecto? | **El patrón sí** (`verify_silver_f1..f5.py` ya existen). |
| Costo de mantener | 4 scripts × ~150 LOC = ~600 LOC. Idéntico patrón a Silver. |
| Dificultad de agregar después | N/A — primer entregable después de las tablas. |

**Veredicto:** 🟢 **IMPRESCINDIBLE.** Sin verificación, no hay forma de saber si Gold está bien. Es la única garantía de calidad.

---

### 2.5 Componentes de portabilidad

#### 🟢 `pg_insert` vs `sqlite_insert` (inline condicional)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | UPSERT portable entre motores |
| ¿Existe en este proyecto? | **Sí.** `db.py:81-94`. |
| Costo de mantener | ~15 LOC inline. |
| Dificultad de agregar después | Ya hecho. |

**Veredicto:** 🟢 **IMPRESCINDIBLE** (ya implementado). No tocar.

---

#### 🔴 Schema DDL portable (CREATE TABLE que funcione en SQLite y PG)

| Pregunta | Respuesta |
|---|---|
| Problema que resuelve | No tener que mantener 2 versiones de schema |
| ¿Existe en este proyecto? | **Parcialmente.** `models_silver.py` usa SQLAlchemy Core que es portable. |
| Costo de mantener | SQLAlchemy Core ya es portable. No requiere trabajo adicional. |
| Dificultad de agregar después | Ya hecho. |

**Veredicto:** 🟢 **IMPRESCINDIBLE** (ya implementado vía SQLAlchemy Core). No agregar más abstracción.

---

### 2.6 Resumen de auditoría (tabla maestra)

| Componente | Veredicto | Razón en una línea |
|---|---|---|
| **Patrones arquitectónicos** | | |
| Hexagonal Architecture | 🔴 | 5 capas para 4 tablas es ruido |
| Repository Pattern | 🔴 | 80 LOC de clase para envolver 5 LOC de SQL |
| Service Layer | 🔴 | No hay lógica de negocio compleja |
| Builder Pattern | 🔴 | Filas Gold son tuplas simples |
| Domain Models | 🔴 | Power BI lee SQL, no objetos Python |
| EnginePort + Multi-engine factory | 🟢 | Ya implementado en `db.py`. NO agregar más abstracción. |
| ClockPort | 🔴 | Sin tests temporales |
| Unit of Work | 🔴 | `engine.begin()` ya ES Unit of Work |
| Dependency Injection framework | 🔴 | Python sin framework es DI |
| Domain Events | 🔴 | El usuario ejecutando scripts ES el event bus |
| Factories abstractas | 🔴 | 1 función Python normal basta |
| Adapters | 🔴 | SQLAlchemy ya ES el adapter |
| CQRS | 🔴 | Silver escribe, Gold lee (ya está separado físicamente) |
| Abstract base classes | 🔴 | Sin código compartido entre tablas |
| Multi-package (`domain/`, `application/`, ...) | 🔴 | 1 carpeta `gold/` con 4 archivos |
| **Infraestructura** | | |
| Alembic migrations | 🔴 | 1 `CREATE TABLE` + script ad-hoc es suficiente |
| pydantic-settings | 🔴 | `os.environ.get()` con default basta |
| Multi-engine UPSERT inline | 🟢 | Ya implementado en `db.py:81-94` |
| Quality Observability Layer | 🟡 | `verify_*.py` ya cumple este rol |
| Lineage tracking por fila | 🔴 | Lineage por RUN ya existe (`silver_etl_runs`) |
| RazaProviderPort | 🔴 | Cross-layer es 1 SELECT, no requiere port |
| DriftChecker automático | 🔴 | Construir Silver + Gold en misma tx elimina drift |
| **Datos y queries** | | |
| gold_diagnosticos | 🟢 | 38/62 preguntas |
| gold_demografia | 🟢 | Cimentación de joins demográficos |
| gold_hallazgos | 🟢 | Única fuente para hallazgos numéricos |
| gold_dim_paciente | 🟡 | DISTINCT en Silver funciona; materializar cuando se use |
| gold_coocurrencias | 🟡 | VIEW en SQLite (28ms es OK); TABLE si >50k informes |
| gold_tendencias | 🟡 | VIEW en SQLite (25ms es OK); TABLE si >50k informes |
| gold_dim_tiempo | 🔴 | Power BI tiene funciones de fecha |
| gold_dim_termino | 🔴 | `dim_termino_conclusion` ya está en Silver |
| gold_calidad_extraccion | 🔴 | `silver_etl_runs` ya tiene los datos |
| **Operaciones** | | |
| Watcher daemon | 🔴 | El usuario ingiere manualmente 5 archivos/día |
| FastAPI service | 🔴 | Power BI Desktop lee SQLite directo |
| systemd timer | 🔴 | El usuario corre el pipeline cuando quiere |
| PG migration AHORA | 🔴 | SQLite + backups a Dropbox resuelve el riesgo |
| Schemas separados en PG | 🔴 | En SQLite no aplica; cuando se migre, se crean |
| DLQ automatizada | 🔴 | El log + inspección manual ya funciona |
| Partitioning por año | 🔴 | SQLite aguanta 1M filas; no hay problema de escala |
| **Verificación** | | |
| `verify_gold_f*.py` | 🟢 | Única garantía de calidad |
| **Portabilidad** | | |
| SQLAlchemy Core | 🟢 | Ya es portable; no agregar más |

**Conteo final:**

- 🟢 **IMPRESCINDIBLE: 5** (3 tablas + 1 engine factory + UPSERT inline + verify scripts)
- 🟡 **ÚTIL PERO PUEDE ESPERAR: 4** (gold_dim_paciente + gold_coocurrencias VIEW + gold_tendencias VIEW + Quality Observability)
- 🔴 **SOBREINGENIERÍA: 22** (todos los patrones enterprise + componentes de producción no necesarios hoy)

---

## 3. Minimum Lovable Architecture

### 3.1 Principios de diseño (los que aplican a este proyecto)

1. **Power BI es el único consumidor.** Todo lo que construyo debe ser consultable desde un `.pbix` con un driver ODBC de SQLite. Esto elimina APIs, daemons, auth.

2. **SQLite aguanta hasta ~1M filas sinPartitioning.** El proyecto no llega ni cerca en 5 años. No hay problema de escala que justifique particionar, migrar a PG, o cachear.

3. **Idempotencia por construcción.** El ETL Gold es FULL REBUILD: `DELETE FROM gold_*` + `INSERT INTO gold_* SELECT ...`. Si falla a mitad, se re-ejecuta. Sin UPSERT, sin delta, sin incremental.

4. **El usuario corre el pipeline cuando quiere.** Sin daemon, sin timer, sin watcher. `python build_gold.py` se ejecuta manualmente.

5. **El "watcher" es el usuario.** El veterinario ve un .docx nuevo en iCloud y ejecuta el script. Costo: 30 segundos. Beneficio: cero infraestructura que mantener.

6. **Denormalización total en Gold.** Cada fila Gold tiene los nombres canónicos como strings. Power BI no quiere JOINs; quiere columnas.

7. **Cross-layer Gold → RAW SOLO para raza_raw.** Es 1 SELECT en `gold_demografia`. No requiere F6, no requiere reabrir Silver. Si se ejecuta F6 en el futuro, se elimina.

8. **No hay linaje por fila.** El linaje está a nivel de RUN (`gold_etl_runs`, igual que `silver_etl_runs`). Por fila es overkill.

9. **Verificación con asserts.** `verify_gold_f*.py` ejecuta queries de control y reporta pass/fail. Idéntico patrón a Silver.

10. **Backups por convención, no por automatización.** El usuario hace `cp silver.db backup-2026-07-01.db` cuando quiere. Si se vuelve crítico, se automatiza.

### 3.2 Estructura de archivos propuesta

```
src/informes_vet/
├── (todo lo existente se mantiene)
├── models_gold.py          # NUEVO. Schema Gold (~80 LOC, 4 tablas)
├── gold_etl.py             # NUEVO. Build Gold (~350 LOC, 4 funciones)
└── gold_views.py           # NUEVO. Definición de VIEWs SQL (~50 LOC)

scripts/
├── build_gold.py           # NUEVO. Orquestador CLI (~80 LOC)
├── verify_gold_f1.py       # NUEVO. Verify gold_diagnosticos (~150 LOC)
├── verify_gold_f2.py       # NUEVO. Verify gold_demografia (~150 LOC)
├── verify_gold_f3.py       # NUEVO. Verify gold_hallazgos (~150 LOC)
└── verify_gold_f4.py       # NUEVO. Verify gold_dim_paciente (~150 LOC, si se materializa)

docs/
├── GOLD_DESIGN_MINIMAL.md  # NUEVO. ~150 LOC, descripción breve
└── GOLD_YAGNI_KISS_REVIEW.md  # este documento
```

**LOC total estimado: ~1.300.** Comparado con la propuesta enterprise de `PRODUCTION_ARCHITECTURE_V1.md` (estimada en ~6.000-8.000 LOC entre Hexagonal, FastAPI, watcher, systemd, nginx, DLQ), es **5x menos código**.

### 3.3 Las 4 tablas del MVP (esquema)

```sql
-- gold_diagnosticos (TABLA)
CREATE TABLE gold_diagnosticos (
  conclusion_item_id INTEGER PRIMARY KEY,
  informe_id INTEGER NOT NULL,
  termino_canonico TEXT NOT NULL,
  tipo_item TEXT NOT NULL,            -- DIAGNOSTICO / ETIOLOGIA / NEGATIVO / MODIFICADOR
  categoria_clinica TEXT,
  organo_asociado TEXT,
  lateralidad TEXT,
  modificador_cualidad TEXT,
  modificador_distribucion TEXT,
  negado INTEGER NOT NULL DEFAULT 0,  -- 0/1
  confianza REAL,
  anio INTEGER NOT NULL,
  mes INTEGER NOT NULL,
  es_primario_en_informe INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX ix_gd_informe ON gold_diagnosticos(informe_id);
CREATE INDEX ix_gd_termino ON gold_diagnosticos(termino_canonico);
CREATE INDEX ix_gd_tipo ON gold_diagnosticos(tipo_item, informe_id);
CREATE INDEX ix_gd_anio_mes ON gold_diagnosticos(anio, mes);

-- gold_demografia (TABLA)
CREATE TABLE gold_demografia (
  informe_id INTEGER PRIMARY KEY,
  fecha DATE,
  anio INTEGER NOT NULL,
  mes INTEGER NOT NULL,
  trimestre INTEGER,
  especie_nombre TEXT NOT NULL,
  sexo_nombre TEXT,
  edad_categoria_nombre TEXT,
  estudio_nombre TEXT,
  estado_reproductivo_nombre TEXT,
  raza_raw TEXT,                       -- desde RAW cross-layer
  nombre_paciente TEXT,
  tutor TEXT,
  n_hallazgos INTEGER,
  n_atributos_extraidos INTEGER,
  n_items_diagnostico INTEGER,
  n_items_etiologia INTEGER,
  n_items_negativo INTEGER
);
CREATE INDEX ix_gdm_especie_anio ON gold_demografia(especie_nombre, anio);
CREATE INDEX ix_gdm_anio_mes ON gold_demografia(anio, mes);

-- gold_hallazgos (TABLA)
CREATE TABLE gold_hallazgos (
  atributo_hallazgo_id INTEGER PRIMARY KEY,
  informe_id INTEGER NOT NULL,
  hallazgo_id INTEGER NOT NULL,
  organo_nombre TEXT NOT NULL,
  sistema TEXT,
  atributo_nombre TEXT NOT NULL,
  valor_nombre TEXT,
  valor_canonico TEXT,
  valor_numerico REAL,
  segmento_nombre TEXT,
  lateralidad TEXT,
  estado_hallazgo TEXT NOT NULL,        -- normal / anormal / no_evaluado
  unidad TEXT                            -- ej: "mm", "cm/s"
);
CREATE INDEX ix_gh_informe ON gold_hallazgos(informe_id);
CREATE INDEX ix_gh_organo_atributo ON gold_hallazgos(organo_nombre, atributo_nombre);
CREATE INDEX ix_gh_atributo_valor ON gold_hallazgos(atributo_nombre, valor_canonico);

-- gold_dim_paciente (TABLA — opcional, construir cuando se use)
CREATE TABLE gold_dim_paciente (
  paciente_key TEXT PRIMARY KEY,        -- hash de (especie + nombre + tutor normalizado)
  especie_nombre TEXT NOT NULL,
  nombre_paciente_normalizado TEXT,
  tutor_normalizado TEXT,
  n_informes INTEGER NOT NULL,
  primer_informe_id INTEGER,
  ultimo_informe_id INTEGER,
  es_recurrente INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX ix_gdp_especie ON gold_dim_paciente(especie_nombre);
```

### 3.4 Las 2 vistas (no son tablas)

```sql
-- gold_coocurrencias (VIEW, no TABLA)
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

-- gold_tendencias (VIEW, no TABLA)
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

**Total: 4 tablas + 2 vistas. ~600 LOC de DDL/SQL. ~700 LOC de Python ETL. ~600 LOC de verify scripts.**

### 3.5 El script `build_gold.py` (~80 LOC)

```python
"""Build Gold Layer. Idempotente: re-ejecutable sin efectos colaterales."""
import argparse
from pathlib import Path
from sqlalchemy import create_engine, text
from informes_vet.gold_etl import (
    build_gold_diagnosticos,
    build_gold_demografia,
    build_gold_hallazgos,
    build_gold_dim_paciente,
)

PHASES = {
    "diag": build_gold_diagnosticos,
    "demo": build_gold_demografia,
    "hall": build_gold_hallazgos,
    "pac": build_gold_dim_paciente,
    "all": None,  # todas
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=list(PHASES.keys()), default="all")
    parser.add_argument("--db", default="sqlite", choices=["sqlite", "postgres"])
    args = parser.parse_args()
    
    engine = get_engine(args.db, Path.cwd())  # función existente en db.py
    ensure_gold_schema(engine)                # CREATE TABLE IF NOT EXISTS
    
    if args.phase == "all":
        for name, fn in [("demo", build_gold_demografia),
                         ("diag", build_gold_diagnosticos),
                         ("hall", build_gold_hallazgos),
                         ("pac", build_gold_dim_paciente)]:
            log_run(engine, name, fn, engine)
    else:
        fn = PHASES[args.phase]
        log_run(engine, args.phase, fn, engine)

def log_run(engine, phase, fn, target_engine):
    """Patrón idéntico a silver_etl_runs: id, phase, status, rows_written, duration."""
    with target_engine.begin() as conn:
        # INSERT INTO gold_etl_runs (status='running', started_at=now())
        # ... ejecutar fn(conn) ...
        # UPDATE gold_etl_runs SET status='ok', finished_at=now(), rows_written=...
    print(f"[{phase}] OK — N filas")
```

**Idempotencia:** cada `build_gold_*` hace `DELETE FROM gold_X` antes de `INSERT INTO gold_X SELECT ...`. Si falla a mitad, se re-ejecuta y queda igual.

### 3.6 El script `gold_etl.py` (~350 LOC)

Una función por tabla. Cada una ~50-80 LOC. Ejemplo de `build_gold_diagnosticos`:

```python
def build_gold_diagnosticos(conn) -> int:
    """Reconstruye gold_diagnosticos desde silver_conclusion_items + dim_termino + silver_informes.
    
    Idempotente: DELETE + INSERT en transacción única.
    Retorna: número de filas insertadas.
    """
    conn.execute(text("DELETE FROM gold_diagnosticos"))
    
    result = conn.execute(text("""
        INSERT INTO gold_diagnosticos (
            conclusion_item_id, informe_id, termino_canonico, tipo_item,
            categoria_clinica, organo_asociado, lateralidad,
            modificador_cualidad, modificador_distribucion, negado,
            confianza, anio, mes, es_primario_en_informe
        )
        SELECT
            sci.id,
            sci.informe_id,
            dt.nombre_canonico,
            dt.tipo_item,
            dt.categoria_clinica,
            dt.organo_asociado,
            sci.lateralidad,
            sci.modificador_cualidad,
            sci.modificador_distribucion,
            sci.es_negado,
            sci.confianza,
            CAST(strftime('%Y', si.fecha_parseada) AS INTEGER),
            CAST(strftime('%m', si.fecha_parseada) AS INTEGER),
            CASE 
              WHEN dt.tipo_item = 'DIAGNOSTICO' AND sci.es_negado = 0
                   AND sci.pos_inicio = (
                     SELECT MIN(sci2.pos_inicio) FROM silver_conclusion_items sci2
                     WHERE sci2.informe_id = sci.informe_id
                       AND sci2.termino_conclusion_id IN (
                         SELECT id FROM dim_termino_conclusion WHERE tipo_item = 'DIAGNOSTICO'
                       )
                       AND sci2.es_negado = 0
                   )
              THEN 1 ELSE 0
            END
        FROM silver_conclusion_items sci
        JOIN dim_termino_conclusion dt ON dt.id = sci.termino_conclusion_id
        JOIN silver_informes si ON si.informe_id = sci.informe_id
    """))
    
    return result.rowcount
```

**Las otras 3 funciones son análogas.** Cada una con su SELECT específico.

### 3.7 Las verificaciones (~600 LOC total)

Patrón idéntico a `verify_silver_f*.py`:

```python
# verify_gold_f1.py (gold_diagnosticos)
def main():
    gold = sqlite3.connect("gold.db")
    fails = []
    
    # 1. Tabla existe y tiene filas
    n = gold.execute("SELECT COUNT(*) FROM gold_diagnosticos").fetchone()[0]
    if n != 16939:
        fails.append(f"✗ gold_diagnosticos tiene {n} filas (esperado 16939)")
    
    # 2. Coincide con silver_conclusion_items
    n_sci = gold.execute("SELECT COUNT(*) FROM silver_conclusion_items").fetchone()[0]
    if n != n_sci:
        fails.append(f"✗ Mismatch: gold={n}, silver={n_sci}")
    
    # 3. Sin termino_canonico NULL
    n_null = gold.execute("SELECT COUNT(*) FROM gold_diagnosticos WHERE termino_canonico IS NULL").fetchone()[0]
    if n_null > 0:
        fails.append(f"✗ {n_null} filas con termino_canonico NULL")
    
    # 4. anio/mes válidos
    invalid = gold.execute("SELECT COUNT(*) FROM gold_diagnosticos WHERE anio < 2020 OR anio > 2030 OR mes < 1 OR mes > 12").fetchone()[0]
    if invalid > 0:
        fails.append(f"✗ {invalid} filas con anio/mes inválido")
    
    # 5. Cobertura por tipo
    for tipo in ['DIAGNOSTICO', 'ETIOLOGIA', 'NEGATIVO', 'MODIFICADOR']:
        n = gold.execute("SELECT COUNT(*) FROM gold_diagnosticos WHERE tipo_item = ?", (tipo,)).fetchone()[0]
        print(f"  └─ {tipo}: {n} filas")
    
    # Reporte
    print(f"\n✓ {5 - len(fails)}/5 checks pasaron")
    if fails:
        for f in fails:
            print(f"  {f}")
        return 1
    return 0
```

---

## 4. Roadmap simplificado (Silver → Gold → Power BI → PG futuro)

### Fase 0 — HOY (Silver ya está, Gold aún no)

**Estado:** Silver congelado, 19/19 verify checks OK, 2,893 informes.

**Acción concreta:** Ninguna. El proyecto está en el lugar correcto para iniciar Gold.

**Trigger para iniciar Fase 1:** "Quiero ver diagnósticos en Power BI" (1 frase del usuario).

---

### Fase 1 — Gold MVP (2-3 días)

**Objetivo:** 4 tablas Gold materializadas + 2 vistas. Power BI puede conectarse a `gold.db` y responder el 62% del catálogo.

**Tareas:**

| # | Tarea | LOC | Tiempo |
|---|---|---:|---:|
| 1.1 | `models_gold.py` (4 tablas + 2 vistas) | ~80 | 2h |
| 1.2 | `gold_etl.py` (4 funciones build) | ~350 | 6h |
| 1.3 | `build_gold.py` (orquestador CLI) | ~80 | 1h |
| 1.4 | `verify_gold_f1.py` (gold_diagnosticos) | ~150 | 1h |
| 1.5 | `verify_gold_f2.py` (gold_demografia) | ~150 | 1h |
| 1.6 | `verify_gold_f3.py` (gold_hallazgos) | ~150 | 1h |
| 1.7 | `gold.db` creado, datos cargados, todos los verify pasan | — | 0.5h |
| 1.8 | `docs/GOLD_DESIGN_MINIMAL.md` (documentación breve) | ~150 | 1h |
| **Total Fase 1** | | **~1.100 LOC** | **~2.5 días** |

**Cierre Fase 1:**
- `python scripts/build_gold.py --phase all` ejecuta los 4 builds en <15 segundos.
- `python scripts/verify_gold_f1.py` ... `f4.py` todos pasan.
- Power BI Desktop abre `gold.db` y ve 4 tablas listas para análisis.

---

### Fase 2 — Power BI (1-2 días, depende del usuario)

**Objetivo:** Dashboard básico en Power BI Desktop conectado a `gold.db`.

**Tareas (las hace el usuario, no código):**

1. Abrir Power BI Desktop.
2. Get Data → ODBC → SQLite ODBC Driver → seleccionar `gold.db`.
3. Importar 4 tablas + 2 vistas (las vistas como `DirectQuery` o importadas).
4. Crear 3 visualizaciones mínimas:
   - **Diagnósticos top 10** (bar chart sobre `gold_diagnosticos.termino_canonico`).
   - **Especie × año** (matrix sobre `gold_demografia.especie_nombre × anio`).
   - **Distribución de edades por especie** (stacked bar sobre `gold_demografia`).
5. Guardar `.pbix` en la carpeta del proyecto.

**No requiere código Python.**

---

### Fase 3 — Mejoras incrementales (cuando aparezcan necesidades reales)

**Esta fase NO se ejecuta por anticipado.** Cada sub-fase tiene un trigger concreto:

| Sub-fase | Trigger | Acción | Tiempo |
|---|---|---|---|
| 3.1 `gold_dim_paciente` materializado | El usuario ejecuta >5 queries con `GROUP BY paciente` en Power BI | Convertir VIEW a TABLE + rebuild | 2h |
| 3.2 F6 mini-ETL raza | El usuario quiere preguntas de raza sin cross-layer read | Ejecutar F6 desde RAW → `dim_raza`, regenerar `gold_demografia` con FK propia | 1 día |
| 3.3 `gold_coocurrencias` TABLE | El corpus supera 50k informes Y el self-join toma >500ms | Convertir VIEW a TABLE + rebuild | 3h |
| 3.4 `gold_tendencias` TABLE | Idem 3.3 | Idem | 3h |
| 3.5 Backup automatizado | El usuario pierde datos por crash de disco | Script Python que copia `*.db` a Google Drive / Dropbox cada noche | 2h |
| 3.6 API REST | El consumidor pasa de Power BI Desktop a Power BI Service | FastAPI + 1 endpoint `/api/diagnosticos` | 1 día |
| 3.7 Migración a PG | El usuario quiere acceso multi-device O hay riesgo de pérdida de datos NO mitigado por backup | Setup PG + schemas + portabilidad ya en código | 1-2 días |

**Cierre Fase 3:** Cada sub-fase es independiente. Se ejecutan solo cuando el trigger aparece.

---

### Fase 4 — PostgreSQL (solo si la Fase 3.7 se activa)

**Objetivo:** Migrar de SQLite a PostgreSQL sin reescribir lógica de aplicación.

**Tareas (todas se ejecutan en orden):**

| # | Tarea | Tiempo |
|---|---|---:|
| 4.1 | Provisioning PG (VPS o local) | 1h |
| 4.2 | Crear schemas `raw`, `silver`, `gold`, `etl` | 0.5h |
| 4.3 | Bulk data migration (CSV o pgloader) | 2h |
| 4.4 | Verificar counts Gold = counts Silver (parity) | 0.5h |
| 4.5 | Cambiar `.env`: `DATABASE_URL=postgres...` | 0.1h |
| 4.6 | Smoke test: ejecutar `build_gold.py` contra PG | 0.5h |
| 4.7 | Mantener SQLite como cold backup 30 días | 0h (ya está) |
| **Total Fase 4** | | **~5h** |

**No requiere cambios de código Python** porque `db.py:42-50` ya soporta ambos motores. Solo se cambia config.

---

### Fase 5 — Watcher daemon (solo si la Fase 3.6 + automatizaciones se activan)

**Objetivo:** Detección automática de nuevos .docx sin intervención del usuario.

**Trigger:** el usuario se va de vacaciones 2 semanas y quiere que el sistema siga funcionando.

**Acción:** construir el watcher + FastAPI + systemd propuestos en `PRODUCTION_ARCHITECTURE_V1.md`. **Pero solo cuando se necesite.**

---

### Resumen del roadmap

| Fase | Cuándo | LOC | Tiempo | Valor |
|---|---|---:|---:|---|
| 0 (estado actual) | HOY | 0 | 0 | Silver cerrado |
| 1 Gold MVP | Cuando el usuario lo pida | ~1.100 | ~2.5 días | 62% del catálogo respondible |
| 2 Power BI | Inmediatamente después de Fase 1 | 0 (Power BI visual) | 1-2 días | Dashboards visuales |
| 3 Mejoras incrementales | Solo cuando aparezca trigger | Variable | Variable | Resolver problemas reales |
| 4 Migración a PG | Solo si Fase 3.7 se activa | ~50 (config) | ~5h | Multi-device |
| 5 Watcher daemon | Solo si Fase 3.6 lo requiere | ~600 | 1-2 días | Automatización total |

**Total comprometido HOY:** Fase 1 + Fase 2 = ~3-4 días.
**Total dejado explícitamente para después:** ~3.000+ LOC de enterprise architecture que NO se van a escribir hasta que hagan falta.

---

## 5. Comparación cuantitativa: Propuestas previas vs Minimum Lovable

| Aspecto | Propuesta enterprise (`PRODUCTION_ARCHITECTURE_V1.md` + hexagonal) | Minimum Lovable |
|---|---:|---:|
| **LOC totales** | ~8.000-10.000 | ~1.300 |
| **Archivos nuevos** | ~40 (paquetes, capas, adapters, ports, daemons, systemd units, nginx config) | ~7 (4 .py en src + 4 scripts + 1 doc) |
| **Tablas Gold materializadas** | 9 | 4 + 2 vistas |
| **Tablas Gold P2** | 3 (`dim_tiempo`, `dim_termino`, `calidad_extraccion`) | 0 (Power BI calcula) |
| **Daemon watcher** | Sí (watchdog + FastAPI + systemd) | No (usuario ingiere manualmente) |
| **API REST** | Sí (FastAPI con auth) | No (Power BI lee SQLite directo) |
| **PG migration AHORA** | Recomendada | Diferida (portabilidad ya existe) |
| **Schemas separados PG** | Sí (`raw`/`silver`/`gold`/`etl`/`audit`) | No (SQLite, 1 schema) |
| **DLQ automatizada** | Sí | No (log manual) |
| **Partitioning por año** | Sí | No (no hay problema de escala) |
| **Lineage por fila** | Sí (`gold_built_at`, `gold_run_id`) | No (lineage por RUN ya existe) |
| **Quality observability** | DriftChecker + freshness + alerts | `verify_*.py` post-build |
| **Cobertura del catálogo** | 100% (con F6) | 62% (sin F6; F6 es Fase 3.2) |
| **Tiempo hasta primer dashboard** | 3-4 semanas | 3-4 días |
| **Tiempo de mantenimiento mensual** | 2-4 horas (daemons, logs, backups PG) | 0 horas |
| **Riesgo de romper algo al cambiar** | Medio-Alto (capas acopladas) | Bajo (cada script es independiente) |
| **Legibilidad para el usuario en 6 meses** | Media (requiere entender Hexagonal) | Alta (4 funciones + 2 vistas, claramente nombradas) |

---

## 6. Decisiones explícitas (las que necesito del usuario)

| # | Decisión | Recomendación | Alternativa |
|---|---|---|---|
| 1 | ¿Construir Fase 1 (Gold MVP) ahora? | **SÍ** | Esperar a tener más volumen |
| 2 | ¿Empezar por `gold_diagnosticos` o construir las 4 tablas juntas? | Las 4 juntas (1 solo orquestador, idempotente) | Una por una (más seguro pero más lento) |
| 3 | ¿`gold_coocurrencias` y `gold_tendencias` como VIEW? | **SÍ** (a 2,893 informes, 25-28ms es OK) | TABLE desde el inicio (más rápido pero más LOC) |
| 4 | ¿`gold_dim_paciente` se construye en Fase 1? | **NO**, esperar al trigger de uso | Sí, desde el inicio (más completo pero especulativo) |
| 5 | ¿Migrar a PG ahora? | **NO**, esperar trigger real | Sí, hacerlo en Fase 1 |
| 6 | ¿Construir el watcher daemon? | **NO**, usuario ingiere manualmente | Sí, automatizar desde el inicio |
| 7 | ¿Crear el `docs/GOLD_DESIGN_MINIMAL.md` aunque haya este doc? | **SÍ** (~150 LOC de referencia rápida) | No, este doc basta |

---

## 7. Veredicto final

### Lo que SÍ se construye (Fase 1)

✅ **4 tablas Gold:**
- `gold_diagnosticos` (16,939 filas, ~200 LOC)
- `gold_demografia` (2,893 filas, ~250 LOC, incluye `raza_raw` cross-layer)
- `gold_hallazgos` (114,753 filas, ~280 LOC)
- `gold_dim_paciente` (2,500 filas, ~300 LOC) — **opcional, ver decisión #4**

✅ **2 vistas Gold:**
- `gold_coocurrencias` (VIEW, ~80 LOC)
- `gold_tendencias` (VIEW, ~80 LOC)

✅ **Verificación:**
- `verify_gold_f1.py` ... `verify_gold_f4.py` (4 scripts, ~150 LOC c/u)

✅ **Orquestador:**
- `build_gold.py` (~80 LOC)

✅ **Documentación:**
- `docs/GOLD_DESIGN_MINIMAL.md` (~150 LOC, referencia rápida)

**Total: ~1.300 LOC, ~2.5 días, 4 tablas + 2 vistas, 62% del catálogo.**

### Lo que NO se construye (ahora)

❌ Watcher daemon, FastAPI, systemd timer, nginx, auth, DLQ — todo lo de `PRODUCTION_ARCHITECTURE_V1.md`
❌ Migración a PostgreSQL
❌ Schemas separados, partitioning, indexes compuestos elaborados
❌ Lineage por fila, drift checker, freshness checker
❌ Repository pattern, service layer, hexagonal, builders, factories, adapters
❌ Domain models separados, abstract base classes
❌ Quality observability layer, RazaProviderPort, ClockPort, UnitOfWork

### Lo que se difiere con trigger claro

🟡 Migración a PG → trigger: multi-device o backup insuficiente
🟡 API REST → trigger: Power BI Service en lugar de Desktop
🟡 Watcher daemon → trigger: ausencias prolongadas del usuario
🟡 `gold_coocurrencias` TABLE → trigger: >50k informes O >500ms en self-join
🟡 `gold_tendencias` TABLE → trigger: idem
🟡 `gold_dim_paciente` → trigger: >5 queries con `GROUP BY paciente`
🟡 F6 mini-ETL raza → trigger: preguntas de raza se vuelven frecuentes

---

## 8. Una nota sobre el código previo

El Silver actual (78KB en `silver_etl.py`, 13 archivos en `src/informes_vet/`) es **monolítico y funciona**. No voy a proponer refactorizarlo a Hexagonal porque:

1. El usuario lo lee y lo entiende.
2. Funciona idempotentemente (verificado en 21+ ETL runs).
3. Los verify scripts pasan 19/19.
4. Romperlo para hacerlo "más limpio" introduce riesgo sin valor.

**Mismo principio para Gold:** script monolítico bien organizado > 5 capas de indirección. Si en 3 años la lógica Gold se vuelve compleja (ej: cuando agreguemos reglas clínicas de scoring, alertas, IA), ENTONCES se refactoriza. Mientras tanto, las 4 funciones `build_gold_*` en un solo archivo son **legibles, testeables, y mantebiles por una sola persona**.

---

## 9. Cierre

> **El "Minimum Lovable Architecture" para este proyecto es:**
>
> 4 tablas Gold + 2 vistas Gold + 4 verify scripts + 1 orquestador.
> ~1.300 LOC. ~2.5 días de trabajo.
> Power BI Desktop lee el resultado directamente desde `gold.db`.
> Sin daemons. Sin API. Sin PG. Sin partitioning. Sin hexagonal.
>
> **Lo demás se construye cuando haya un motivo concreto, no antes.**

**Próximo paso:** esperar decisión del usuario sobre las 7 preguntas de §6. Por defecto (si no hay objeción), se procede con Fase 1 tal como está descrita.