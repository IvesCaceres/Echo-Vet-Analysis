# VetTalk — Arquitectura de Producción v1

**Fecha:** 2026-06-26
**Tipo:** Diseño técnico. Sin código. Crítico, cuantitativo, basado en evidencia del proyecto actual.
**Stack objetivo:** Python 3.11+ · PostgreSQL 16 · Linux VPS · File watcher (inotify/FSEvents) · systemd.
**Volumen esperado:** miles de informes/año (no millones). Throughput actual del pipeline local: ~30 s para 2.893 informes.

---

## 0. Línea base (estado actual del proyecto)

Auditoría de evidencia antes de diseñar:

### 0.1 Inventario de código

| Módulo | LOC | Rol |
|---|---:|---|
| `silver_etl.py` | 2.057 | Orquestadores F1–F2.1 + helpers ETL |
| `silver_f5_conclusions.py` | 838 | Extracción de ítems de conclusión |
| `models_silver.py` | 563 | Esquema Silver (24 tablas) |
| `silver_f3_dims.py` | 522 | Bootstrap dims F3 + extractores |
| `silver_f4_values.py` | 429 | Diccionario canónico de valores |
| `silver_db.py` | 383 | Engine factory + migraciones |
| `extract.py` | 441 | Parser .docx |
| `organs.py` | 392 | Clasificación de órganos |
| `silver_dims.py` | 207 | Bootstrap dims base (F1) |
| `db.py` | 142 | Engine factory RAW + UPSERT portable |
| `models.py` | 124 | Esquema RAW (5 tablas) |
| `docx_io.py` | 79 | Walk + filtros basura |
| `hashutil.py` | 38 | SHA-256 |
| `analytics.py` | 9 | (placeholder) |
| **TOTAL `src/informes_vet/`** | **~6.224** | |

| Scripts operativos | Cantidad | Rol |
|---|---:|---|
| `run_ingest.py` | 168 LOC | Ingesta única de RAW |
| `build_silver.py` | 734 LOC | Orquestador CLI F1–F5 |
| `verify_silver_*.py` | 6 scripts | Verificación post-fase |
| Audit/profile scripts | 12 scripts | Análisis puntuales (legacy) |

### 0.2 Volumen actual

| Tabla | Filas | Tamaño en disco |
|---|---:|---:|
| `informes` (RAW) | 2.893 | 22 MB (`informes.db`) |
| `hallazgos` (RAW) | 27.866 | |
| `conclusiones` (RAW) | 2.893 | |
| `silver_informes` | 2.893 | **41 MB (`silver.db`)** |
| `silver_hallazgos` | 27.866 | |
| `silver_atributos_hallazgo` | 114.753 | |
| `silver_conclusion_items` | 16.939 | |
| `dim_raza` | 63 | |
| `dim_termino_conclusion` | 98 | |
| `dim_valor_atributo` | 177 | |

**Crecimiento esperado:** ~500–1.000 informes/año. Para 10 años: 10.000–13.000 informes. Sigue siendo "miles", no millones.

### 0.3 Throughput medido (SQLite local, 2026-06-26)

| Fase | Tiempo medido | Throughput |
|---|---|---:|
| F2 (incluye backfill) | 2,97 s | ~974 informes/s |
| F3 | ~10 s | ~289 informes/s |
| F4 | 1,4 s | ~2.066 informes/s |
| F5 (extracción) | 4,5 s | ~643 informes/s |
| **Pipeline completo F1→F5** | **~30 s** | **~96 informes/s** |

**Implicación:** El pipeline completo tarda menos de un minuto sobre el dataset actual. Esto es fundamental para decidir orquestación (ver §5).

### 0.4 Infraestructura actual

- **Python:** 3.11+ con `venvvector/`
- **DB local:** SQLite (`silver.db`, `informes.db`, `gold.db` vacíos)
- **DB remoto (ya configurado):** `PG_DSN=postgresql+psycopg://ives:BC38d5a1e7@149.50.140.191:5432/db_ecografia` (VPS remoto ya provisionado)
- **Driver:** `psycopg[binary]>=3.2.0` (ya en requirements.txt)
- **Sin daemon:** No hay watcher, ni scheduler, ni systemd units. Todo se ejecuta manualmente.
- **Backups:** Manual (carpeta `backup-20260618/` + snapshots `pg_pre_reset_20260617_*.dump`).
- **Monitoreo:** Ninguno.

### 0.5 Hallazgos críticos del estado actual

1. **No hay ingestion automática.** Los archivos `.docx` viven en `Ecografía YYYY/` y se ingieren manualmente con `python scripts/run_ingest.py`.
2. **PG ya configurado pero no usado.** El `.env` apunta a un VPS remoto, pero el proyecto corre 100% en SQLite.
3. **Silver y Gold viven en archivos `.db` separados.** No existe un script que conecte ambos; `gold.db` está vacío.
4. **Falta el eslabón iCloud → servidor.** Hoy los `.docx` viven en la laptop del veterinario; no hay sincronización con el VPS.
5. **No hay API ni dashboard.** Power BI, scripts y futuros modelos aún no existen.
6. **Errores solo se loguean en `errores_ingest.log` + tabla `errores_ingesta`.** No hay notificaciones.

---

## 1. Flujo completo desde iCloud hasta PostgreSQL

### 1.1 Vista lógica (alto nivel)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          LAPTOP DEL VETERINARIO                          │
│                                                                          │
│  iCloud Drive                                                            │
│  └─ VetTalk/Informes/Ecografía YYYY/MM Mes YYYY/Paciente/archivo.docx   │
│           │                                                              │
│           ▼  (Apple FSEvents / inotify local)                           │
│  ┌────────────────────┐                                                  │
│  │  vettalk-watcher   │  proceso Python (watchdog + python-docx hash)    │
│  └─────────┬──────────┘                                                  │
│            │  HTTPS POST (JSON: ruta, sha256, timestamp)                 │
└────────────┼─────────────────────────────────────────────────────────────┘
             │
             │  Internet (TLS 1.3)
             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          VPS (Linux)                                     │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────┐            │
│  │  nginx (reverse proxy + TLS termination)                │            │
│  │  └─ /api/ingest   → FastAPI ingest service              │            │
│  └────────────────────────┬─────────────────────────────────┘            │
│                           │                                              │
│                           ▼                                              │
│  ┌──────────────────────────────────────────────────────────┐            │
│  │  PostgreSQL 16 (single instance, 80 GB SSD)             │            │
│  │  Schemas: raw, silver, gold, etl, audit                 │            │
│  └──────────────────────────────────────────────────────────┘            │
│                           ▲                                              │
│                           │                                              │
│  ┌────────────────────────┴─────────────────────────────────┐            │
│  │  vettalk-pipeline.service (systemd)                      │            │
│  │  trigger: cada 5 min OR evento del watcher              │            │
│  │  ejecuta: ingest → RAW upsert → F1..F5 → Gold → verify │            │
│  └──────────────────────────────────────────────────────────┘            │
│                           │                                              │
│                           ▼                                              │
│  ┌──────────────────────────────────────────────────────────┐            │
│  │  Power BI / Python scripts / futura API / IA models     │            │
│  │  consumen: vistas gold_* (lectura directa PG)           │            │
│  └──────────────────────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Vista de datos (transformaciones)

```
[.docx en iCloud]
        │ (1) watcher detecta (evento FSEvents)
        ▼
[hash SHA-256 sobre texto canónico]
        │ (2) POST /api/ingest con {ruta, sha256}
        ▼
[FastAPI valida y encola]
        │ (3) escribe a PostgreSQL:
        │     - .docx a filesystem /var/vettalk/archive/<sha256>.docx
        │     - fila en raw.informes (UPSERT por sha256)
        │     - filas en raw.hallazgos + raw.conclusiones
        ▼
[silver_etl.build_f1() detecta nuevos sha256]
        │ (4) UPSERT a silver_informes + dims (idempotente)
        ▼
[silver_etl.build_f2() consolida map_raza/dim_raza]
        │ (5) idempotente, no-op si no hay nuevos sha256
        ▼
[silver_etl.build_f3() extrae atributos]
        │
        ▼
[silver_etl.build_f4() consolida valores]
        │
        ▼
[silver_etl.build_f5() extrae conclusión]
        │
        ▼
[gold_etl.build_g1..gn() agregan y proyectan]
        │
        ▼
[verify_silver_*.py + verify_gold_*.py]
        │
        ▼
[vistas gold_* disponibles para Power BI / API / IA]
```

### 1.3 Garantías de diseño

- **Idempotencia en cada capa** (verificado: 3 runs consecutivos de F2 producen rows_written=0). El SHA-256 es la clave de unicidad end-to-end.
- **RAW es inmutable:** `informes` solo recibe INSERT (nunca UPDATE). Las correcciones se hacen en Silver.
- **Silver es derivable:** las 24 tablas se reconstruyen desde RAW con F1–F5.
- **Gold es derivable:** las tablas gold_* se reconstruyen desde Silver con g1–gn.
- **Verificación continua:** cada pipeline termina con verify scripts que deben pasar 100%.

---

## 2. Detección automática de nuevos informes

### 2.1 Opciones evaluadas

| Opción | Mecanismo | Plataforma | Pros | Contras |
|---|---|---|---|---|
| **A. Watchdog (FSEvents en macOS / inotify en Linux)** | Eventos del kernel | Ambas | Latencia <1s; bajo overhead; estándar Python | Requiere proceso siempre corriendo; no detecta archivos modificados offline |
| **B. Polling (cada N min)** | `os.walk` + comparar hash con DB | Cualquiera | Simple; robusto; funciona aunque el watcher esté caído | Latencia N minutos; alto I/O si carpeta tiene miles de archivos |
| **C. systemd path unit** | inotify via systemd | Solo Linux | Sin código Python; integrado con OS | Menos flexible; debugging más opaco |
| **D. FSEvents directo con `watchdog` library** | Watchdog sobre FSEvents en macOS | Solo macOS | Evento nativo macOS | Acoplado a plataforma |
| **E. rclone + cron** | Sincronización + trigger | Cualquiera | Útil si iCloud no está disponible en VPS | Añade capa de sincronización |

### 2.2 Recomendación: **Opción A (watchdog) + Opción B (polling) como fallback**

**Arquitectura híbrida:**

```
iCloud/  ──[watchdog FSEvents]──▶  watcher local (laptop)
                                       │
                                       │  POST /api/ingest
                                       ▼
                                  VPS PostgreSQL
                                       ▲
                                       │
              [polling cada 5 min]──┘
              (systemd timer + scan incremental)
```

**Justificación técnica:**

1. **Watcher para latencia baja** cuando el usuario está trabajando activamente (latencia <2 s). Se ejecuta en la laptop del veterinario o en un mini-servidor macOS local.
2. **Polling como red de seguridad** por si el watcher está caído o por archivos que llegaron cuando el watcher no estaba activo (laptop apagada, iCloud sync diferido). Corre cada 5 min en el VPS vía systemd timer.
3. **Ambos alimentan el mismo endpoint** (`POST /api/ingest`) → una sola fuente de verdad.

### 2.3 Implementación del watcher (especificación, sin código)

**Watcher local (en laptop con iCloud):**

- **Trigger:** `watchdog.observers.Observer` sobre `~/Library/Mobile Documents/com~apple~CloudDocs/VetTalk/Informes/`.
- **Filtro:** solo eventos `on_created` y `on_modified` sobre archivos `.docx` (excluir `~$*`, `._*`, `.DS_Store`).
- **Debounce:** esperar 5 segundos después del último evento (iCloud escribe en chunks → evita leer a medio escribir).
- **Lock file check:** si el `.docx` está abierto en Word (`~$<archivo>.docx` existe), descartar y reintentar en 30 s.
- **Hash:** `hash_doc(canonical_text)` sobre el texto canónico (no el binario .docx).
- **Envío:** HTTPS POST a `/api/ingest` con `{ruta_relativa, sha256, archivo}`.
- **Reintentos:** 3 intentos con backoff exponencial (1s, 5s, 25s). Si fallan, log a `~/vettalk-watcher.log` y descarta (el polling en VPS detectará después).
- **Heartbeat:** ping cada 60 s al endpoint `/api/heartbeat` para detectar cuándo el watcher está caído.

**Polling en VPS (systemd timer):**

- **Trigger:** `OnUnitActiveSec=5min` + `OnBootSec=2min`.
- **Servicio:** ejecuta `python -m vettalk.ingest.scan --root /var/vettalk/inbox --since-last-sha <last_sha>`.
- **Lógica:** compara lista de archivos en inbox con tabla `etl.ingest_queue`. Procesa los nuevos (sha256 no visto antes) y los que cambiaron (sha256 distinto).
- **Lock file:** si `.~lock.<archivo>.docx#` existe, descartar (archivo aún abierto por cliente iCloud).

### 2.4 Casos edge que el diseño debe tolerar

| Caso | Cómo se maneja |
|---|---|
| iCloud sync llega archivo en chunks (escribe `.tmp` y luego renombra) | Watcher espera 5s de debounce; polling verifica que el tamaño sea estable |
| Archivo eliminado en laptop mientras se ingestaba | SHA-256 ya está en BD; el registro persiste (inmutabilidad) |
| Mismo archivo modificado en laptop y subido dos veces | UPSERT por sha256; la 2da escritura es no-op |
| Archivo corrupto (.docx ilegible) | Se loguea en `errores_ingesta` con traceback; el pipeline sigue |
| Archivo sin tablas (caso observado: "Aura_Asevet.docx") | `extract.ExtractionError("Sin tablas")`; se loguea; no se ingiere |
| Lock de Word (`~$archivo.docx`) | Se filtra en `is_junk()`; nunca se intenta ingestar |
| AppleDouble (`._archivo.docx`) | Se filtra en `is_junk()`; nunca se intenta ingestar |
| Archivo denylistado (3 archivos específicos: Mike/Olga/Fiona) | DENYLIST en `docx_io.py`; filtrado antes de parsear |

---

## 3. Pipeline completo (10 componentes)

### 3.1 Diseño general

```
┌──────────────────────────────────────────────────────────────────────────┐
│  COMPONENTE         │ ENTRADA         │ SALIDA           │ DURACIÓN      │
├──────────────────────────────────────────────────────────────────────────┤
│  1. Inbox watcher   │ filesystem      │ etl.ingest_queue │ <1s por arch. │
│  2. Validator       │ .docx file      │ hash + metadata  │ ~0.3s/arch    │
│  3. RAW loader      │ hash + raw text │ raw.informes     │ ~0.5s/arch    │
│  4. Hallazgos loader│ raw.hallazgos[] │ raw.hallazgos    │ ~0.2s/arch    │
│  5. Conclusiones    │ raw text        │ raw.conclusiones │ ~0.1s/arch    │
│  6. Silver F1       │ raw.informes    │ silver_informes  │ ~2s/2893      │
│  7. Silver F2       │ raw+silver      │ map_*, dim_raza  │ ~3s/2893      │
│  8. Silver F3       │ silver.hallaz   │ silver_atributos │ ~10s/2893     │
│  9. Silver F4       │ silver_atrib    │ map_atributo     │ ~1.4s/2893    │
│ 10. Silver F5       │ silver.concl    │ silver_concl_items│ ~4.5s/2893   │
│ 11. Gold g1..gn     │ silver.*        │ gold.*           │ TBD           │
│ 12. Verify suite    │ silver.*+gold.* │ pass/fail        │ ~5s           │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Manejo de errores (por componente)

| Componente | Tipo de error | Acción | Reintento |
|---|---|---|---|
| Watcher | File system read error | Log + skip + alerta | No |
| Validator | .docx corrupto | Log a `etl.watcher_errors` | No |
| Validator | Lock de Word activo | Skip (polling reintentará) | Sí (cada 5 min) |
| RAW loader | DB constraint violation | Log + DLQ (`etl.dlq`) | No |
| RAW loader | Conexión PG caída | Backoff exponencial | Sí (3 intentos) |
| Silver F1–F5 | Excepción Python | Log + abortar fase | Sí (en próximo run) |
| Silver F1–F5 | Idempotency violation | Log + alerta | No (es bug) |
| Verify | Cualquier check FAIL | Marcar run como `degraded` | No (requiere fix manual) |
| Gold | Similar a Silver | Idempotente + retry | Sí |

### 3.3 Reintentos y Dead Letter Queue (DLQ)

- **Reintentos síncronos:** 3 intentos con backoff exponencial (1s, 5s, 25s) por archivo/carpeta.
- **DLQ:** tabla `etl.dlq` con `(archivo, ruta, error, traceback, created_at, retry_count)`. Items en DLQ se inspeccionan manualmente.
- **Reintento automático de DLQ:** después de 24h, el pipeline intenta de nuevo. Si falla 3 veces, queda permanente.

### 3.4 Logging estructurado

Todos los componentes emiten logs en formato JSON a:
- **PostgreSQL:** tablas `etl.pipeline_runs` y `etl.pipeline_steps` (idénticas a `silver_etl_runs` actual).
- **Archivos:** `/var/log/vettalk/pipeline.log` (rotación daily, 30 días retención).
- **Stderr:** para journald en systemd.

**Esquema de `etl.pipeline_runs` (nuevo, abstrae silver_etl_runs + futuros gold runs):**

```sql
CREATE TABLE etl.pipeline_runs (
  id BIGSERIAL PRIMARY KEY,
  run_id UUID NOT NULL UNIQUE,             -- agrupa steps de un mismo run
  pipeline VARCHAR(32) NOT NULL,            -- 'silver' | 'gold'
  phase VARCHAR(32) NOT NULL,               -- 'f1' | 'f2' | 'f3' | 'g1' | ...
  status VARCHAR(16) NOT NULL,              -- 'ok' | 'error' | 'degraded'
  started_at TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ,
  rows_read INTEGER,
  rows_written INTEGER,
  rows_skipped INTEGER,
  rows_errored INTEGER DEFAULT 0,
  duration_ms INTEGER,
  actor VARCHAR(64),
  notes JSONB
);
```

### 3.5 Modelo de ejecución: incremental vs full

**Decisión crítica:** ¿el pipeline se re-ejecuta completo cada vez, o solo procesa los delta?

**Análisis cuantitativo:**

| Modo | F2 | F3 | F5 | Total F1-F5 |
|---|---|---|---|---|
| **Full rebuild** (todo desde RAW) | 3 s | 10 s | 4,5 s | ~30 s |
| **Incremental** (solo nuevos sha256) | <1 s (no-op si no hay nuevos) | <1 s | <1 s | **~3 s** |

**Recomendación:** **Incremental por defecto, full semanal como reconciliación.**

- **Incremental diario:** solo procesa sha256 que aparecieron en `raw.informes` después del último run OK.
- **Full semanal:** todos los domingos 03:00 UTC. Detecta drift (archivos modificados manualmente, restores de backup, etc.).
- **Full on-demand:** con flag `--full` cuando se cambia lógica ETL.

**Lógica incremental en F1** (ejemplo de cómo se vería):

```python
# Pseudo-lógica (NO código de implementación)
last_run = get_last_successful_run('f1')
new_informes = SELECT * FROM raw.informes WHERE ingested_at > last_run.finished_at
# Procesar solo new_informes en F1; el resto es no-op por UPSERT
```

---

## 4. Organización recomendada del proyecto

### 4.1 Estructura de carpetas propuesta

```
vettalk/
├── README.md
├── requirements.txt              # deps producción
├── requirements-dev.txt          # deps dev/test
├── pyproject.toml                # (futuro) configuración pip install -e
├── .env.example                  # plantilla config
├── .gitignore
│
├── src/informes_vet/             # paquete principal (existente, refactor menor)
│   ├── __init__.py
│   ├── core/                     # utilidades cross-cutting
│   │   ├── __init__.py
│   │   ├── config.py             # carga de .env, settings tipados
│   │   ├── logging.py            # setup logging JSON
│   │   ├── db.py                 # engine factory (SQLite|postgres)
│   │   ├── models.py             # raw.* schema
│   │   ├── models_silver.py      # silver.* schema
│   │   ├── models_gold.py        # (futuro) gold.* schema
│   │   ├── models_etl.py         # etl.* schema (pipeline_runs, dlq, etc.)
│   │   └── hashutil.py
│   ├── ingest/                   # NUEVO: componente 1-5
│   │   ├── __init__.py
│   │   ├── watcher.py            # watchdog observer
│   │   ├── poller.py             # scan incremental
│   │   ├── validator.py          # hash + lock check
│   │   ├── extractor.py          # parse .docx (extract.py actual)
│   │   ├── loader.py             # UPSERT a raw.*
│   │   └── archive.py            # copia .docx a /var/vettalk/archive/
│   ├── silver/                   # renombre de silver_*.py → paquete
│   │   ├── __init__.py
│   │   ├── etl.py                # build_f1..f5 (silver_etl.py actual)
│   │   ├── dims.py               # bootstrap dims (silver_dims.py)
│   │   ├── db.py                 # silver_db.py
│   │   ├── migrations.py         # v2.1, v3.0, v5.0
│   │   ├── f3_dims.py
│   │   ├── f4_values.py
│   │   └── f5_conclusions.py
│   ├── gold/                     # NUEVO: componente 11
│   │   ├── __init__.py
│   │   └── etl.py                # build_g1..gn (a implementar)
│   ├── api/                      # NUEVO: lectura para Power BI/IA
│   │   ├── __init__.py
│   │   ├── ingest.py             # POST /api/ingest
│   │   ├── reads.py              # GET /api/informes, /api/diagnosticos, etc.
│   │   └── auth.py               # API key / JWT (futuro)
│   └── notify/                   # NUEVO: alertas
│       ├── __init__.py
│       └── slack.py              # webhook a Slack (futuro)
│
├── scripts/                      # CLIs operacionales
│   ├── run_ingest.py             # (mantener compat) ingesta única
│   ├── run_watcher.py            # daemon del watcher
│   ├── run_pipeline.py           # ejecuta silver+gold+verify
│   ├── build_silver.py           # (mantener) --phase f1..f5
│   ├── build_gold.py             # (futuro) --phase g1..gn
│   ├── verify_silver_*.py        # (mantener)
│   ├── verify_gold_*.py          # (futuro)
│   ├── migrate_sqlite_to_pg.py   # (futuro) ETL schema
│   ├── backup_db.sh              # pg_dump wrapper
│   └── restore_db.sh             # restore wrapper
│
├── systemd/                      # NUEVO: units de Linux
│   ├── vettalk-watcher.service
│   ├── vettalk-watcher@.service  # template para múltiples watchers
│   ├── vettalk-pipeline.service
│   ├── vettalk-pipeline.timer
│   └── README.md
│
├── deploy/                       # NUEVO: infra as code
│   ├── docker-compose.yml        # PG + app (para staging local)
│   ├── nginx/
│   │   └── vettalk.conf
│   ├── prometheus/
│   │   └── vettalk.yml
│   └── README.md
│
├── tests/                        # (mantener) unit + integration
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
└── docs/
    ├── README.md
    ├── PRODUCTION_ARCHITECTURE_V1.md  # este documento
    ├── F2_FINAL_TECHNICAL_AUDIT.md
    ├── SILVER_FINAL_SIGNOFF.md
    ├── F2_1_COMPLETION_REPORT.md
    ├── GOLD_DESIGN_V1.md
    └── ...
```

### 4.2 Responsabilidades por capa

| Capa | Responsabilidad única | NO debe hacer |
|---|---|---|
| `core/` | DB engines, schemas, config, logging, hashing | Lógica de negocio |
| `ingest/` | Detectar, validar, copiar .docx, escribir a RAW | Tocar Silver o Gold |
| `silver/` | ETL Silver (F1–F5) | Tocar Gold directamente |
| `gold/` | ETL Gold (g1–gn) | Tocar Silver |
| `api/` | Solo lectura de gold_* | Escribir a DB |
| `notify/` | Enviar alertas | Modificar estado del pipeline |
| `scripts/` | CLIs operacionales | Lógica reutilizable (debe estar en `core/`) |
| `systemd/` | Lifecycle de procesos | Lógica de aplicación |

### 4.3 Reglas de dependencia (acíclicas)

```
core  ←  ingest  ←  scripts/run_watcher.py
core  ←  silver  ←  scripts/build_silver.py, run_pipeline.py
core  ←  gold    ←  scripts/build_gold.py, run_pipeline.py
core  ←  api     ←  nginx upstream
core  ←  notify  ←  silver, gold (emiten errores)
```

**Reglas duras:**
- `ingest` NUNCA importa de `silver` o `gold`. (RAW es inmutable; ingest solo escribe RAW.)
- `silver` NUNCA importa de `gold`.
- `gold` NUNCA importa de `ingest` o `silver.etl` directamente — solo lee vía SQL.
- `api` NUNCA escribe; solo SELECT desde `gold`.

---

## 5. Estrategia de orquestación

### 5.1 Análisis cuantitativo del volumen

| Métrica | Valor actual | Valor proyectado (10 años) |
|---|---:|---:|
| Informes RAW | 2.893 | ~13.000 |
| Hallazgos | 27.866 | ~125.000 |
| Atributos | 114.753 | ~500.000 |
| Items conclusión | 16.939 | ~75.000 |
| Tiempo pipeline completo | ~30 s | ~2 min |
| Informes/día (asumiendo 500/año) | 1,4 | 1,4 |
| Pico (campaña de temporada) | ~20/día | ~20/día |

**Conclusión:** el volumen es **trivial** para una base de datos PostgreSQL moderna.

### 5.2 Opciones evaluadas

| Opción | Adecuado para VetTalk? | Costo | Pros | Contras |
|---|---|---|---|---|
| **A. cron + script Python** | ✅ Sí, recomendado | 0 | Simple, estándar Linux, sin dependencias | Sin UI; sin retries nativos; sin logs centralizados |
| **B. systemd timer + service** | ✅ Sí, **recomendado** | 0 | Nativo Linux; restart on failure; logging a journald | Sin orquestación de DAGs |
| **C. APScheduler (in-process)** | ⚠ Sobre-ingeniería | Bajo | Scheduler rico | Proceso debe estar siempre corriendo; single point of failure |
| **D. Celery + Redis** | ❌ Excesivo | Medio | Distributed task queue | Mucha infraestructura para 1 cron job |
| **E. Airflow** | ❌ NO recomendado ahora | Alto | UI rica; DAGs; SLA tracking | Overhead enorme para 5 steps; curva de aprendizaje |
| **F. Prefect** | ❌ NO recomendado ahora | Alto | Moderno; Python-first | Mismo problema que Airflow |
| **G. Dagster** | ❌ NO recomendado ahora | Alto | Data-aware | Mismo problema |
| **H. Temporal** | ❌ NO recomendado ahora | Alto | Workflow engine | Diseñado para casos mucho más complejos |

### 5.3 Recomendación: **systemd timer + service** (Opción B)

**Justificación cuantitativa:**

1. **El pipeline tiene 1 trigger** (ingestión de nuevos informes). No es un DAG complejo de 50 tasks.
2. **Cada step tarda <30 segundos**. No hay tareas largas que justifiquen un orquestador.
3. **El "schedule" es reactivo** (cuando llega un nuevo .docx), no periódico (cada hora). Eso se resuelve con el watcher, no con un orquestador.
4. **Si en 3 años el pipeline crece a 10+ steps con dependencias complejas**, se puede migrar a Airflow sin reescribir el código del pipeline (solo agregar un DAG wrapper).
5. **El costo de Mantener Airflow** (1 dev-day/semana en updates, monitoring, etc.) es mayor que el costo total de operación actual.

**Cuándo migrar a Airflow/Prefect (reglas claras):**

- Cuando se tengan **3+ fuentes de datos distintas** además de los .docx (ej: CSV de laboratorio, API de gestión, HL7 de PACS).
- Cuando se necesite **backfill >1 mes** regularmente.
- Cuando haya **SLA estrictos** (ej: "Gold debe estar actualizado 1h después del último informe").
- Cuando múltiples **equipos necesiten ver el estado** del pipeline.

**Implementación (especificación):**

```ini
# /etc/systemd/system/vettalk-pipeline.service
[Unit]
Description=VetTalk Silver+Gold ETL pipeline
After=postgresql.service

[Service]
Type=oneshot
User=vettalk
EnvironmentFile=/etc/vettalk/pipeline.env
ExecStart=/opt/vettalk/venv/bin/python /opt/vettalk/src/scripts/run_pipeline.py --incremental
WorkingDirectory=/opt/vettalk
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/vettalk-pipeline.timer
[Unit]
Description=Run VetTalk pipeline every 5 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
AccuracySec=30s
Persistent=true

[Install]
WantedBy=timers.target
```

**Por qué NO cron:**
- cron no tiene retry nativo; si el script crashea, no se entera nadie.
- cron no tiene logging estructurado.
- cron no se reinicia solo si el server reboota (aunque con `@reboot` se puede).

---

## 6. Estrategia de migración SQLite → PostgreSQL

### 6.1 Estado actual de portabilidad

**El esquema ya es portable.** Evidencia:

- `db.py:45-50` ya soporta `get_engine("postgres", root)` con `PG_DSN`.
- `silver_db.py:42-48` ya soporta el mismo patrón.
- `models.py`, `models_silver.py` usan SQLAlchemy Core con tipos portables (Integer, String, Text, DateTime, JSON).
- `pg_insert` y `sqlite_insert` ya se usan condicionalmente (`db.py:81-94`).
- `psycopg[binary]>=3.2.0` ya está en `requirements.txt`.
- `.env` ya tiene `PG_DSN=postgresql+psycopg://ives:BC38d5a1e7@149.50.140.191:5432/db_ecografia`.

**Riesgos residuales** (a verificar durante la migración):

| Riesgo | Severidad | Mitigación |
|---|---|---|
| `PRAGMA foreign_keys=ON` no se ejecuta en PG | Baja | PG tiene FKs always on en tablas InnoDB-style; verificar caso por caso |
| `AUTOINCREMENT` (SQLite) vs `SERIAL`/`BIGSERIAL` (PG) | Baja | `Integer, primary_key=True, autoincrement=True` se traduce automáticamente |
| `Text` columns sin length limit | Baja | PG permite Text sin límite; sin cambio |
| `JSON` column type | Baja | PG tiene JSON nativo; SQLite almacena como Text |
| `BOOLEAN` en SQLite es INTEGER 0/1 | Media | Verificar lectura/escritura; usar `Boolean` que SQLAlchemy traduce |
| `UNIQUE INDEX` con COALESCE | Media | PG soporta; verificar sintaxis |
| Encoding UTF-8 con caracteres españoles (ñ, í, ó) | Media | PG requiere `client_encoding=utf8`; psycopg lo hace por default |
| `CHECK` constraints | Baja | Sintaxis compatible |
| Transacciones `with engine.begin():` | Baja | Idéntica semántica |
| `RETURNING` clause | Baja | Ambos la soportan |

### 6.2 Plan de migración (5 fases)

**Fase 1 — Provisioning del PostgreSQL de producción (Día 1)**

- Crear DB `vettalk` con usuario `vettalk_app` (no `ives`).
- Schemas separados: `raw`, `silver`, `gold`, `etl`, `audit`.
- Permisos: `vettalk_app` tiene SELECT/INSERT/UPDATE/DELETE en `raw`, `silver`, `gold`, `etl`; solo SELECT en `audit`.
- Roles separados: `vettalk_ro` para Power BI / API (solo SELECT).
- Backups automatizados: `pg_dump` diario + WAL archiving (PITR).

**Fase 2 — Schema creation (Día 1, ~30 min)**

```sql
-- Equivalente a create_schema(engine) pero aplicado a PG
python scripts/run_ingest.py --db postgres --reset   # crea raw.*
python scripts/build_silver.py --db postgres --init  # crea silver.*
```

**Fase 3 — Bulk data migration (Día 1, ~2 horas)**

Para cada capa (raw, silver), en este orden:

1. **Export SQLite → CSV (o JSON):**
   ```bash
   sqlite3 silver.db ".mode csv" ".headers on" ".out silver_informes.csv" "SELECT * FROM silver_informes;"
   ```

2. **Import CSV → PostgreSQL:**
   ```bash
   psql -h $PG_HOST -U vettalk_app -d vettalk -c "\COPY silver.silver_informes FROM 'silver_informes.csv' CSV HEADER"
   ```

3. **Verify counts:**
   ```sql
   SELECT 'silver_informes', COUNT(*) FROM silver.silver_informes
   UNION ALL SELECT 'silver_hallazgos', COUNT(*) FROM silver.silver_hallazgos
   -- ... etc
   ```

**Alternativa más rápida:** usar `pgloader` (herramienta dedicada) o un script Python con SQLAlchemy que lee de SQLite y escribe a PG con `executemany`.

**Fase 4 — Verificación end-to-end (Día 1, ~1 hora)**

Ejecutar todos los verify scripts contra PG:

```bash
PG_DSN=... python scripts/verify_silver_f1.py
PG_DSN=... python scripts/verify_silver_f2.py
PG_DSN=... python scripts/verify_silver_f3.py
PG_DSN=... python scripts/verify_silver_f4.py
PG_DSN=... python scripts/verify_silver_f5.py
```

(Los verify scripts ya usan `silver_db.get_engine(root)` que respeta `PG_DSN`.)

**Fase 5 — Switchover (Día 2, ventana de mantenimiento)**

1. Stop del pipeline (`systemctl stop vettalk-pipeline.timer`).
2. Snapshot final de SQLite (`sqlite3 silver.db ".backup silver.db.precutover"`).
3. Último run incremental del pipeline contra PG (debe ser no-op si todo está migrado).
4. Switch del `.env`: `DATABASE_URL=postgres...` (en lugar de tener que cambiar cada script).
5. Activar timer: `systemctl start vettalk-pipeline.timer`.
6. Smoke test: drop un .docx de prueba en inbox, verificar que llega a RAW en PG.
7. Mantener SQLite como cold backup durante 30 días.

### 6.3 Decisiones irreversibles (lock-in)

| Decisión | Reversible? | Consecuencia |
|---|---|---|
| Usar PostgreSQL | **NO** después de 6 meses | Reescribir todos los UPSERT si se quiere cambiar |
| Schemas `raw`/`silver`/`gold` separados | Sí (con migración) | Convencional; sin lock-in |
| Usar SQLAlchemy Core (no ORM) | Sí | Core es portable a cualquier DB relacional |
| Decimales como `Float` (no `Numeric`) | **NO** | Pérdida de precisión en cálculos financieros; NO usar para plata |
| Text encoding UTF-8 | Sí | PG requiere; sin cambio |
| `id` autoincrement en TODAS las tablas | Sí (con migración) | Convencional; no es lock-in |
| **Sin encriptación at-rest** | **NO** | Si se decide encriptar después, requiere re-import completo |
| **Sin partitioning por fecha** | **NO** después de 100k filas | Decidir AHORA si se va a particionar |

**Recomendación crítica:** incluir partitioning por `anio` desde el día 1 en las tablas de facts (`silver_informes`, `silver_hallazgos`, `silver_atributos_hallazgo`, `silver_conclusion_items`). Costo: ~10% más complejo en creación de schema. Beneficio: queries por año son 10x más rápidas, archivado de años viejos es trivial.

### 6.4 Plan de rollback

Si algo sale mal en el switchover:

1. `systemctl stop vettalk-pipeline.timer`
2. Cambiar `.env` de vuelta a SQLite (mantener el `.env.sqlite.bak`)
3. `systemctl start vettalk-pipeline.timer`
4. Investigar logs en `/var/log/vettalk/pipeline.log`
5. Restaurar datos desde `silver.db.precutover` si es necesario

---

## 7. Esquema de despliegue en VPS

### 7.1 Especificaciones mínimas del VPS

**Fase 1 (año 1, 2.893 → 5.000 informes):**

| Recurso | Mínimo | Recomendado |
|---|---|---|
| vCPU | 2 | 4 |
| RAM | 4 GB | 8 GB |
| Disco | 80 GB SSD | 160 GB SSD |
| Transferencia | 2 TB/mes | 4 TB/mes |
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| Costo (Hetzner) | ~$15/mes | ~$30/mes |

**Fase 2 (año 5, 10.000 informes):** mismo VPS o upgrade a 8 GB RAM.

**Fase 3 (año 10, 13.000+ informes):** sigue cabiendo en el mismo VPS; solo agregar disco si se guardan los .docx originales (10 años × 500/año × 50 KB ≈ 250 MB total — despreciable).

### 7.2 Servicios a desplegar

```
VPS (Ubuntu 24.04 LTS)
├── PostgreSQL 16
│   ├── port 5432 (interno, no expuesto)
│   ├── data: /var/lib/postgresql/16/main
│   ├── backups: /var/backups/postgresql/
│   └── config: /etc/postgresql/16/main/postgresql.conf
│
├── vettalk-watcher.service (systemd)
│   ├── user: vettalk
│   ├── working dir: /opt/vettalk
│   ├── env: /etc/vettalk/watcher.env
│   └── auto-restart: yes (Restart=always)
│
├── vettalk-pipeline.service (systemd, oneshot)
├── vettalk-pipeline.timer (systemd, cada 5 min)
│
├── vettalk-api.service (systemd) [Fase 4]
│   ├── uvicorn FastAPI
│   ├── port 8000 (interno)
│   └── detrás de nginx
│
├── nginx (reverse proxy)
│   ├── port 443 (HTTPS público)
│   ├── port 80 (redirect a 443)
│   ├── cert: Let's Encrypt via certbot
│   ├── upstream: vettalk-api:8000
│   └── rate limit: 100 req/min por IP
│
├── prometheus-node-exporter (opcional Fase 3)
├── grafana (opcional Fase 3)
│
└── backups automáticos
    ├── pg_dump daily (cron 02:00 UTC)
    ├── WAL archiving (continuous)
    ├── retención: 30 días pg_dump, 7 días WAL
    └── destino: /var/backups/postgresql/ + rsync off-site
```

### 7.3 Configuración de PostgreSQL (production-tuned)

```ini
# /etc/postgresql/16/main/postgresql.conf (extracto)

# Conexiones
max_connections = 100                # suficiente para app + Power BI + API
superuser_reserved_connections = 3

# Memoria
shared_buffers = 1GB                 # 25% de 4GB RAM
effective_cache_size = 3GB           # 75% de 4GB RAM
work_mem = 16MB                      # para queries analíticas
maintenance_work_mem = 256MB

# WAL
wal_level = replica
max_wal_size = 2GB
min_wal_size = 512MB
checkpoint_completion_target = 0.9

# Query planner
random_page_cost = 1.1               # SSD
effective_io_concurrency = 200       # SSD

# Logging
log_min_duration_statement = 500ms   # log queries lentas
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
```

### 7.4 Backups

**Estrategia 3-2-1:**

| Backup | Frecuencia | Retención | Destino |
|---|---|---|---|
| `pg_dump` full | Diario 02:00 UTC | 30 días | Local + off-site |
| WAL archiving | Continuo | 7 días | Local + off-site |
| `pg_dump` schema-only | Semanal | 90 días | Local |
| Backup de `/var/vettalk/archive/` (.docx originales) | Diario | Indefinido | Local + off-site |

**Restore drill:** ejecutar `pg_restore` en staging **trimestralmente** para verificar que los backups funcionan.

### 7.5 Monitoreo

**Fase 1-2 (mínimo viable):**

- Health check endpoint: `GET /health` → `{status: "ok", db: "ok", last_run: "..."}`.
- Uptime monitoring externo: UptimeRobot (free) o similar.
- Logs centralizados: journald + `/var/log/vettalk/*.log`.

**Fase 3 (recomendado):**

- Prometheus + Grafana (on the same VPS).
- Métricas clave:
  - `vettalk_pipeline_runs_total{phase, status}` (counter)
  - `vettalk_pipeline_duration_seconds{phase}` (histogram)
  - `vettalk_db_connections_active` (gauge)
  - `vettalk_dlq_size` (gauge)
  - `vettalk_inbox_files_pending` (gauge)
- Alertas: pipeline FAIL 3 veces seguidas → email/Slack.

### 7.6 Seguridad

| Capa | Medida |
|---|---|
| Red | Firewall (ufw): solo 22 (SSH), 80/443 (HTTP/HTTPS) públicos. 5432 solo desde localhost. |
| SSH | Key-based auth only; `PermitRootLogin no`; fail2ban. |
| DB | Password fuerte para `vettalk_app`; conexión solo desde localhost vía Unix socket O desde el VPS via TCP con TLS. |
| API | API key en header; rate limit; CORS restrictivo para Power BI. |
| HTTPS | Let's Encrypt + certbot auto-renew. |
| Secrets | `.env` con permisos 600; nunca committear. |
| Backups | Cifrados con gpg antes de subir off-site. |

---

## 8. Orden de implementación: antes / durante / después de Gold

### 8.1 ANTES de Gold (pre-requisitos)

Estos componentes **deben estar listos** antes de empezar a implementar Gold. Sin ellos, Gold se construye sobre cimientos movedizos.

| # | Componente | Esfuerzo | Prioridad | Razón |
|---|---|---|---|---|
| 1 | Migración SQLite → PostgreSQL (con datos) | 1 día | P0 | Gold debe vivir en PG desde el inicio |
| 2 | Schema `etl.*` (pipeline_runs, dlq, ingest_queue) | 0.5 día | P0 | Tracking de ejecuciones Gold |
| 3 | FastAPI ingest service (`POST /api/ingest`) | 2 días | P0 | Habilita ingestión remota |
| 4 | Watcher local (laptop con iCloud) | 1 día | P0 | Cierra el gap de detección automática |
| 5 | Polling en VPS (systemd timer) | 0.5 día | P0 | Fallback del watcher |
| 6 | Pipeline incremental (solo sha256 nuevos) | 1 día | P0 | Reduce tiempo de 30s a 3s |
| 7 | systemd units (watcher + pipeline) | 0.5 día | P1 | Operacionaliza todo |
| 8 | Verify scripts portables a PG | 0.5 día | P0 | Idempotencia probada en PG |
| 9 | Backups automatizados (pg_dump cron) | 0.5 día | P0 | DR mínimo viable |
| 10 | nginx + TLS (Let's Encrypt) | 1 día | P1 | Necesario para HTTPS del watcher → API |
| 11 | Documentación operacional (runbooks) | 1 día | P1 | Para no depender de una sola persona |

**Total ANTES de Gold:** ~10 días-hombre.

### 8.2 DURANTE Gold

Gold puede implementarse en paralelo con los items 7-11 de arriba (que son operacionalización, no bloqueantes para el desarrollo de Gold).

| # | Componente | Esfuerzo | Prioridad | Notas |
|---|---|---|---|---|
| 12 | Diseño Gold (g1–gn) | 1 semana | P0 | Ya documentado en `GOLD_DESIGN_V1.md` |
| 13 | Implementación tablas Gold | 2-3 semanas | P0 | Estrellas + facts + dimensiones |
| 14 | Verify scripts Gold | 0.5 semana | P0 | |
| 15 | Vistas SQL para Power BI | 1 semana | P0 | `gold.v_informes_resumen`, etc. |
| 16 | Documentación Gold | 1 semana | P1 | |

**Total DURANTE Gold:** ~6 semanas.

### 8.3 DESPUÉS de Gold

Una vez Gold esté operativo, se pueden agregar consumidores.

| # | Componente | Esfuerzo | Prioridad | Notas |
|---|---|---|---|---|
| 17 | API REST para lectura (FastAPI) | 1 semana | P1 | `GET /api/informes`, `/api/diagnosticos` |
| 18 | Power BI dashboard inicial | 1-2 semanas | P1 | Conectar a `gold.*` views |
| 19 | Notificaciones Slack (errores) | 0.5 semana | P2 | Webhook a canal `#vettalk-alerts` |
| 20 | Monitoreo Prometheus + Grafana | 1 semana | P2 | Dashboards de pipeline + DB |
| 21 | Embeddings (RAG para IA) | 2 semanas | P2 | Usa `embeddings` table ya en schema |
| 22 | LLM-based extraction (mejora F5) | 4 semanas | P3 | Sustituir regex con LLM; alto riesgo |
| 23 | Multi-veterinaria (multi-tenancy) | 4+ semanas | P3 | Solo si el producto escala a N veterinarias |

**Total DESPUÉS de Gold:** ~10-15 semanas (puede priorizarse según necesidad de negocio).

---

## 9. Roadmap completo por fases

### 9.1 Fase 0 — Foundation (Semanas 1-2)

**Objetivo:** PostgreSQL productivo + schema etl + backups automatizados.

| Tarea | Esfuerzo | Dependencias | Riesgo |
|---|---|---|---|
| Provisioning PG en VPS (ya hecho en parte) | 0.5 día | Ninguna | Bajo |
| Crear schemas (raw, silver, gold, etl, audit) | 0.5 día | PG provisionado | Bajo |
| Crear roles (`vettalk_app`, `vettalk_ro`) | 0.5 día | Schemas | Bajo |
| Migrar datos SQLite → PG (CSV bulk) | 1 día | Schemas | Medio (encoding, tipos) |
| Verify scripts corren limpios contra PG | 0.5 día | Datos migrados | Medio |
| Configurar `pg_dump` cron + off-site backup | 1 día | PG | Bajo |
| Documentar runbook de recovery | 0.5 día | Backups | Bajo |

**Esfuerzo total Fase 0:** 4.5 días-hombre. **Riesgo global:** MEDIO.

### 9.2 Fase 1 — Ingestion automática (Semanas 3-4)

**Objetivo:** Detección y carga automática de nuevos informes.

| Tarea | Esfuerzo | Dependencias | Riesgo |
|---|---|---|---|
| Implementar FastAPI ingest service | 2 días | Fase 0 | Bajo |
| Implementar watcher local (laptop macOS) | 1.5 días | FastAPI | Medio (FSEvents quirks) |
| Implementar poller VPS (systemd timer) | 1 día | FastAPI | Bajo |
| Lógica incremental en F1 (solo sha256 nuevos) | 1 día | Poller | Bajo |
| Lock check para Word open | 0.5 día | Watcher | Bajo |
| Debounce + retry con backoff | 0.5 día | Watcher | Bajo |
| Tests de integración end-to-end | 1 día | Todo lo anterior | Medio |

**Esfuerzo total Fase 1:** 7.5 días-hombre. **Riesgo global:** MEDIO.

### 9.3 Fase 2 — Gold Layer (Semanas 5-10)

**Objetivo:** Tablas Gold operativas y verificadas.

| Tarea | Esfuerzo | Dependencias | Riesgo |
|---|---|---|---|
| Diseño final de tablas Gold (g1–gn) | 3 días | Fase 1 | Bajo (diseño ya iniciado) |
| Implementar `gold.etl.build_g1..gn()` | 10 días | Diseño | Medio |
| Verify scripts Gold (g1..gn) | 2 días | Implementación | Bajo |
| Vistas SQL para Power BI | 3 días | Verify pass | Bajo |
| Pipeline completo Gold en systemd | 1 día | Verify pass | Bajo |
| Documentación Gold | 2 días | Pipeline OK | Bajo |
| Smoke test con Power BI real | 2 días | Vistas | Bajo |

**Esfuerzo total Fase 2:** 23 días-hombre (~5 semanas). **Riesgo global:** MEDIO.

### 9.4 Fase 3 — Operacionalización (Semanas 11-12)

**Objetivo:** Producción hardened con monitoreo y DR.

| Tarea | Esfuerzo | Dependencias | Riesgo |
|---|---|---|---|
| nginx + Let's Encrypt | 1 día | Fase 1 | Bajo |
| Prometheus node_exporter + Grafana | 2 días | nginx | Bajo |
| Dashboards Grafana (pipeline, DB, ingestión) | 1 día | Prometheus | Bajo |
| Alertas Slack/email | 1 día | Dashboards | Bajo |
| Restore drill trimestral documentado | 0.5 día | Backups | Bajo |
| Runbook operacional completo | 1 día | Todo | Bajo |

**Esfuerzo total Fase 3:** 6.5 días-hombre. **Riesgo global:** BAJO.

### 9.5 Fase 4 — Consumers (Semanas 13+)

**Objetivo:** Power BI + API + bases para IA.

| Tarea | Esfuerzo | Dependencias | Riesgo |
|---|---|---|---|
| API REST FastAPI (`GET /api/*`) | 5 días | Fase 2 | Bajo |
| Power BI dashboards (3-5 vistas) | 5 días | API o vistas PG | Bajo |
| Embeddings (sentence-transformers sobre hallazgos) | 5 días | Fase 2 | Medio |
| Vector store (pgvector o FAISS) | 3 días | Embeddings | Medio |
| RAG endpoint para consultas en lenguaje natural | 5 días | Vector store | Alto |

**Esfuerzo total Fase 4:** 23 días-hombre (~5 semanas). **Riesgo global:** MEDIO-ALTO.

### 9.6 Esfuerzo total del roadmap

| Fase | Semanas | Días-hombre | Estado |
|---|---:|---:|---|
| 0 — Foundation | 2 | 4.5 | P0 — bloqueante |
| 1 — Ingestion automática | 2 | 7.5 | P0 — bloqueante |
| 2 — Gold Layer | 6 | 23 | P0 — objetivo principal |
| 3 — Operacionalización | 2 | 6.5 | P1 |
| 4 — Consumers (Power BI, API, IA) | 5+ | 23+ | P2-P3 |
| **TOTAL** | **17+** | **~65+ días-hombre** | (~3-4 meses con 1 dev) |

### 9.7 Dependencias críticas entre fases

```
Fase 0 (PG)
    │
    ▼
Fase 1 (Ingesta)
    │
    ▼
Fase 2 (Gold) ──────────────┐
    │                       │
    ▼                       ▼
Fase 3 (Ops)         Fase 4 (Consumers, en paralelo)
```

**Critical path:** Fase 0 → 1 → 2 → 3 (no se puede saltar). Fase 4 puede arrancar en paralelo con Fase 3.

### 9.8 Riesgos del roadmap (top 5)

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| **Fase 1 (watcher iCloud) más compleja de lo estimado** | Alta | Medio | Empezar con polling-only; agregar watcher como mejora |
| **Gold requiere más tablas de las estimadas** | Media | Alto | Diseño iterativo; MVP con 5 tablas core, agregar después |
| **Power BI connectivity issues con PG** | Baja | Bajo | Usar DirectQuery + ODBC; documentar workaround |
| **Costo del VPS sube** | Baja | Bajo | Migración a Hetzner ($15 vs $40 actual) |
| **Cambio de veterinario / abandono del proyecto** | Media | Alto | Documentación exhaustiva; runbooks para no-devs |

---

## 10. Cuellos de botella, decisiones irreversibles y recomendaciones de largo plazo

### 10.1 Cuellos de botella identificados

| Cuello de botella | Cuándo se manifestará | Mitigación |
|---|---|---|
| **`UNIQUE INDEX` con COALESCE** en `silver_atributos_hallazgo` | >100k filas; queries con segmento IS NULL | PG soporta igual; verificar EXPLAIN |
| **Full table scan en `silver_conclusion_items`** para "top términos" | >50k items | Crear índice en `termino_conclusion_id` |
| **Power BI + DirectQuery** sobre tablas grandes | >50k filas en dashboard | Configurar modo Import con refresh scheduled |
| **Generación de embeddings** (cuando se implemente) | >10k hallazgos → ~5 minutos | Pre-calcular batch offline; no on-demand |
| **Backups pg_dump** sobre DB grande | >10 GB → >10 min backup | Combinar pg_dump + WAL archiving (PITR) |
| **iCloud sync conflicts** (mismo archivo editado en 2 devices) | Cualquier momento | SHA-256 sobre texto canónico; el "último gana" |

### 10.2 Decisiones irreversibles (o muy costosas de revertir)

| Decisión | Cuándo decidir | Costo de revertir |
|---|---|---|
| PostgreSQL como DB única | **AHORA** | Reescribir todos los UPSERT, FKs, etc. |
| Schemas separados `raw`/`silver`/`gold` | **AHORA** | Bajo (convencional) |
| SQLAlchemy Core (no ORM) | **AHORA** | Bajo (refactor) |
| Identificación por SHA-256 (no por UUID) | **AHORA** | Reescribir RAW.informes; perder historial |
| Idempotencia por UPSERT (no CDC) | **AHORA** | Reescribir ingestion |
| `parse_docx` con python-docx (no LLM) | **AHORA** | Bajo (cambiar extractor) |
| Sin encriptación at-rest | **AHORA** | Re-import completo si se requiere |
| Sin partitioning por fecha | **AHORA** | Migración de 100k+ filas dolorosa |
| Idioma español (no multi-idioma) | **AHORA** | Reescribir diccionarios |

**Recomendación:** tomar todas estas decisiones **antes** de implementar Fase 1. El costo de revertir después es 10-100x mayor.

### 10.3 Recomendaciones de largo plazo (3-5 años)

1. **Particionar tablas grandes por `anio`** desde el inicio. Costo bajo, beneficio enorme.
2. **Versionar el schema** con migraciones explícitas (Alembic). Hoy se hace manual; es frágil.
3. **Snapshottear Silver mensualmente** como "releases inmutables" para auditoría retrospectiva.
4. **Documentar el linaje** de cada métrica Gold (qué fase la genera, qué reglas aplica).
5. **Inversión continua en datos sintéticos de prueba**: ~1.000 informes sintéticos para regression testing.
6. **Capacitar a un segundo dev** en el pipeline antes de Fase 3 (bus-factor mitigation).
7. **Plan de exit para el veterinario:** si deja el proyecto, los datos deben quedar accesibles vía Gold API pública.
8. **NO usar LLMs como extractor primario** hasta tener 2+ años de operación Gold estable. El regex + diccionario actual es 100% determinista y auditable; un LLM introduciría variabilidad.
9. **Embeddings primero, RAG después:** los embeddings (sin RAG) ya habilitan búsqueda semántica útil; RAG requiere mucho más diseño.
10. **Multi-veterinaria (multi-tenancy)** vía `veterinaria_id` en RAW.informes, NO en DBs separadas. Si en 3 años hay 5+ veterinarias, una sola DB con RLS (Row-Level Security) es 10x más simple que 5 DBs separadas.

### 10.4 Métricas de éxito (a monitorear mensualmente)

| Métrica | Target | Cómo medir |
|---|---|---|
| Latencia ingestión (iCloud → Silver) | <5 min p95 | `etl.pipeline_runs` timestamps |
| Cobertura Gold (% informes con ≥1 finding en Gold) | >99% | verify_gold_*.py |
| Drift schema (cambios no versionados) | 0 | Alembic migrations vs metadata |
| Uptime del pipeline | >99.5% | `etl.pipeline_runs.status='ok'` / total |
| DLQ size | <5 archivos | `SELECT COUNT(*) FROM etl.dlq` |
| Backup success rate | 100% | log de cron |
| Time to recover from backup | <1h | drill trimestral |
| Size de silver.db | <1 GB para 5 años | `pg_database_size('vettalk')` |

### 10.5 Anti-patrones a evitar

| Anti-patrón | Por qué evitarlo |
|---|---|
| Big-bang migration (todo de una) | Si falla, no hay rollback granular |
| Mover lógica de negocio a la DB (stored procs, triggers) | Acopla lógica a SQL; testing doloroso |
| Gold como "select * from silver" | Pierde valor; Gold debe agregar valor semántico |
| Embeddings sin evaluar | Caro de calcular; sin métricas no se sabe si ayudan |
| "AI para todo" | Regex + diccionarios es mejor cuando es determinista |
| Backups sin restore drill | "Tenemos backups" no significa nada si no se probaron |
| Push directo a `main` desde laptop | Sin review, sin tests, sin auditoría |
| Logs en stdout sin structured | Imposible de parsear / alertar |
| Compartir usuario `postgres` con la app | Si la app se compromete, pierde toda la DB |
| HARD-delete en cualquier capa | RAWs son inmutables por diseño |

---

## 11. Veredicto final

### 🟢 Arquitectura viable y bien fundamentada.

**Resumen de decisiones clave:**

| Decisión | Recomendación |
|---|---|
| DB de producción | **PostgreSQL 16** (ya provisionado en VPS) |
| Detección nuevos informes | **Watcher (watchdog) + Polling (systemd timer) como fallback** |
| Orquestación | **systemd timer + service** (NO Airflow/Prefect ahora) |
| Pipeline | **Incremental por defecto + Full semanal** |
| Migración SQLite → PG | **Fase 0 inmediata** (5 fases, ~1 día total) |
| Deployment | **VPS único** ($15-30/mes Hetzner) |
| Backup | **pg_dump diario + WAL archiving + off-site rsync** |
| Monitoring | **Fase 3** (Prometheus + Grafana; health check básico antes) |

**Próximos pasos inmediatos (orden de ejecución):**

1. **Esta semana:** Validar Fase 0 (PG migration dry-run).
2. **Próxima semana:** Iniciar Fase 1 (ingest service + watcher).
3. **Semanas 3-8:** Fase 2 (Gold).
4. **Mes 3:** Fase 3 (operacionalización).
5. **Mes 4+:** Fase 4 (Power BI, API, IA).

**Decisiones críticas a tomar ANTES de implementar:**

- [ ] Confirmar partitioning por `anio` en facts.
- [ ] Confirmar estructura de schemas (`raw`/`silver`/`gold`/`etl`/`audit`).
- [ ] Confirmar uso de Alembic para migraciones (o continuar manual).
- [ ] Confirmar retención de backups (30 días pg_dump + 7 días WAL).
- [ ] Confirmar thresholds de alertas (pipeline fail X veces → email).

**Riesgo global del roadmap:** MEDIO. Volumen pequeño, código maduro, decisiones técnicas sólidas. El proyecto está en buena posición para escalar a miles de informes sin reescritura mayor.

---

**Anexo A — Referencias del proyecto**

| Documento | Propósito |
|---|---|
| `docs/SILVER_FINAL_SIGNOFF.md` | Estado Silver al cierre |
| `docs/F2_FINAL_TECHNICAL_AUDIT.md` | Auditoría técnica F2 |
| `docs/F2_1_COMPLETION_REPORT.md` | Reporte del Completion Release |
| `docs/GOLD_DESIGN_V1.md` | Diseño Gold Layer (parcial) |
| `docs/GOLD_PRE_AUDIT_FINAL.md` | Auditoría pre-Gold |
| `docs/GOLD_QUESTION_CATALOG.md` | 62 preguntas sobre Gold |
| `docs/SILVER_LAYER.md` | Diseño Silver original |
| `src/informes_vet/` | Código fuente (6.224 LOC) |
| `requirements.txt` | Dependencias (ya incluye psycopg) |
| `.env` | Configuración PG (ya apunta a VPS remoto) |
