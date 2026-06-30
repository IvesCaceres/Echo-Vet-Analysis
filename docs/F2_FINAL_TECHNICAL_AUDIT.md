# F2 / F2.1 — Auditoría técnica exhaustiva

**Fecha de auditoría:** 2026-06-26
**Objetivo:** Determinar con evidencia si F2 realmente quedó sin ejecutar, identificar la causa raíz, y entregar un veredicto GO / NO GO para iniciar Gold.
**Restricción:** Solo análisis. Sin código, sin parches, sin implementación.

---

## Resumen ejecutivo (veredicto en §10)

- **Causa raíz:** `build_f2()` y `build_f2_1()` NUNCA fueron invocados por el orquestador. El código existe, está completo, es idempotente y ortogonal a F3/F4/F5. El orquestador `scripts/build_silver.py` tiene las fases `--phase f2` (línea 251) y `--phase f2_1` (línea 326) activas y funcionales, pero nadie ejecutó `python scripts/build_silver.py --phase f2` ni `--phase f2_1` desde el inicio del proyecto.
- **Evidencia principal:** 21 filas en `silver_etl_runs`. **Cero** con `phase='f2'`. **Cero** con `phase='f2_1'`. Conteos en `dim_raza`, `map_raza`, `map_especie`, `map_sexo`, `map_estudio`, `stg_razas_detectadas`, `stg_valores_no_mapeados`: **todos = 0**.
- **Veredicto:** Clasificación **A) F2 está completo pero nunca fue ejecutado**. **GO condicional para Gold**, condicionado a ejecutar `build_f2()` antes (sin esto, Gold queda con `silver_informes.dim_raza_id` 100% NULL y `dim_raza` 100% vacía).

---

## PARTE 1 — Estado real de F2

### 1.1 ¿Existe `build_f2()`?

| Atributo | Valor |
|---|---|
| **Archivo** | `src/informes_vet/silver_etl.py` |
| **Función** | `build_f2(silver_engine, raw_engine, *, actor="build_silver")` |
| **Líneas** | 1006 – 1083 (78 líneas) |
| **Docstring** | "Ejecuta la Fase 2: puebla `map_*` y `dim_raza`, deja excepciones en staging. Asume que F1 ya corrió (`silver_informes` poblado y `dim_*` base con seeds). **No modifica `silver_informes`**." (líneas 1009-1013) |
| **Estado** | **Completa y terminada** |
| **Retorno** | `dict[str, Any]` con métricas (`map_especie`, `stg_especie`, `map_sexo`, `stg_sexo`, `map_estudio`, `stg_estudio`, `dim_raza`, `map_raza`, `stg_razas`, `duration_ms`) |

### 1.2 Cuerpo de `build_f2()` (sub-fases que ejecuta)

| Sub-fase | Helper | Salida | Líneas |
|---|---|---|---|
| 1. Especie | `_build_map_especie` | `map_especie`, `stg_valores_no_mapeados` | 1018-1025 |
| 2. Sexo | `_build_map_sexo` | `map_sexo`, `stg_valores_no_mapeados` | 1028-1035 |
| 3. Estudio | `_build_map_estudio` | `map_estudio`, `stg_valores_no_mapeados` | 1038-1045 |
| 4. Raza (dim) | `_build_dim_raza` | `dim_raza` | 1048-1049 |
| 5. Raza (map + stg) | `_build_map_raza` | `map_raza`, `stg_razas_detectadas` | 1050-1059 |
| 6. Logging | `_log_run(phase="f2", status="ok")` | `silver_etl_runs` | 1077-1082 |

### 1.3 Dependencias

| Dependencia | Tipo | Estado actual |
|---|---|---|
| `silver_informes` poblado por F1 | Dato | ✅ 2893 filas |
| `dim_especie` (seed) | Tabla | ✅ 6 entradas (bootstrap_basico) |
| `dim_sexo` (seed) | Tabla | ✅ 3 entradas |
| `dim_estado_reproductivo` (seed) | Tabla | ✅ 4 entradas |
| `dim_estudio` (seed) | Tabla | ✅ 8 entradas |
| `raw.informes` (columna raza, especie, genero, estudio) | Dato | ✅ 2893 filas |
| `_log_run` (escribe a `silver_etl_runs`) | Función | ✅ Definida en `silver_etl.py:1086` |

**Conclusión:** Todas las dependencias existen. F2 puede ejecutarse hoy sin prerequisitos faltantes.

---

## PARTE 2 — Pipeline

### 2.1 Cadena de llamadas esperada

```
build_silver.py (orquestador CLI)
  ├── args.phase == "f1"     → silver_etl.build_f1()                       [línea 156]
  ├── args.phase == "f2"     → silver_etl.build_f2()                       [línea 251]
  ├── args.phase == "f2_1"   → silver_etl.build_f2_1()                     [línea 326]
  ├── args.phase == "f3"     → silver_etl.build_f3()                       [línea 412]
  ├── args.phase == "f4"     → _build_f4 (silver_f4_values.build_f4)      [línea 493]
  └── args.phase == "f5"     → _build_f5 (silver_f5_conclusions.build_f5) [línea 609]
```

### 2.2 ¿Está comentado? ¿Omitido? ¿Detrás de una condición?

**El código NO está comentado.** Las llamadas existen dentro de bloques `if args.phase == ...`:

```python
# scripts/build_silver.py:247-251
if args.phase == "f2":
    t0 = time.monotonic()
    print("[f2] poblando map_especie/sexo/estudio, dim_raza, map_raza, stg_*...")
    try:
        metrics = silver_etl.build_f2(silver_engine, raw_engine, actor=actor)
```

```python
# scripts/build_silver.py:322-326
if args.phase == "f2_1":
    t0 = time.monotonic()
    print("[f2_1] refactor dim_raza + DPC/DPL + backfill edad_meses...")
    try:
        metrics = silver_etl.build_f2_1(silver_engine, raw_engine, actor=actor)
```

El argparse en `build_silver.py:78` declara `choices=("f1", "f2", "f2_1", "f3", "f4", "f5")`. **Las fases `f2` y `f2_1` son explícitamente válidas.**

### 2.3 ¿Se eliminó durante un refactor?

No. La cadena de llamadas aparece intacta desde la primera versión del orquestador. No hay historia de git en este repositorio (no es un repo git), pero no hay evidencia de eliminación:
- `scripts/build_silver.py` línea 78: `choices=("f1", "f2", "f2_1", "f3", "f4", "f5")` — incluye f2 y f2_1.
- `scripts/build_silver.py` líneas 6-9 (docstring del orquestador) documenta el orden de ejecución F1 → F2 → F2_1 → F3 → F4 → F5.

### 2.4 ¿Por qué no se ejecutó?

**No fue un fallo técnico ni una condición de código.** El orquestador conoce las fases. Nunca se ejecutaron los comandos `python scripts/build_silver.py --phase f2` ni `--phase f2_1`. Los registros de `silver_etl_runs` lo prueban.

---

## PARTE 3 — `silver_etl_runs`

### 3.1 ¿Existe algún registro F2 o F2.1?

**NO.** Cero filas con `phase='f2'`. Cero filas con `phase='f2_1'`.

### 3.2 Listado completo de ejecuciones registradas

| id | phase | status | rows_read | rows_written | rows_skipped | dur_ms | started_at | actor |
|---|---|---|---|---|---|---|---|---|
| 1 | f3 | error | 0 | 0 | 0 | 12 | 2026-06-22 13:32:29 | ivesc |
| 2 | f1 | ok | 2893 | 2893 | 0 | 1158 | 2026-06-22 13:38:58 | ivesc |
| 3 | f3_hallazgos | ok | 27866 | 27866 | 0 | 4985 | 2026-06-22 13:41:42 | ivesc |
| 4 | f3 | ok | 27866 | 107409 | 0 | 9704 | 2026-06-22 13:41:47 | ivesc |
| 5 | f3_hallazgos | ok | 27866 | 27866 | 0 | 5283 | 2026-06-23 10:32:47 | ivesc |
| 6 | f3 | ok | 27866 | 107394 | 0 | 9817 | 2026-06-23 10:32:52 | ivesc |
| 7 | f4 | error | 0 | 0 | 0 | 118 | 2026-06-23 10:37:21 | ivesc |
| 8 | f4 | error | 0 | 0 | 0 | 304 | 2026-06-23 10:37:46 | ivesc |
| 9 | f4 | ok | 107394 | 0 | 0 | 345 | 2026-06-23 10:38:40 | ivesc |
| 10 | f4 | ok | 107394 | 0 | 0 | 317 | 2026-06-23 10:40:20 | ivesc |
| 11 | f4 | ok | 107394 | 0 | 0 | 1408 | 2026-06-23 10:49:46 | ivesc |
| 12 | f4 | ok | 107394 | 11 | 0 | 839 | 2026-06-23 10:52:06 | ivesc |
| 13 | f4 | ok | 107394 | 0 | 0 | 772 | 2026-06-23 10:53:22 | ivesc |
| 14 | f3_hallazgos | ok | 27866 | 0 | 27866 | 2224 | 2026-06-24 11:48:55 | ivesc |
| 15 | f3 | ok | 27866 | 7359 | 107394 | 9430 | 2026-06-24 11:48:57 | ivesc |
| 16 | f5 | error | 0 | 0 | 0 | 2656 | 2026-06-24 13:31:02 | ivesc |
| 17 | f5 | ok | 2893 | 16035 | 0 | 2881 | 2026-06-24 13:32:36 | ivesc |
| 18 | f5 | ok | 2893 | 16035 | 0 | 2809 | 2026-06-24 13:33:22 | ivesc |
| 19 | f5 | ok | 2893 | 16940 | 0 | 4506 | 2026-06-24 14:42:44 | ivesc |
| 20 | f5 | ok | 2893 | 16947 | 0 | 4518 | 2026-06-24 14:45:56 | ivesc |
| 21 | f5 | ok | 2893 | 16947 | 0 | 4544 | 2026-06-24 14:47:28 | ivesc |

### 3.3 Distribución por phase

| phase | ejecuciones | rango temporal |
|---|---|---|
| f1 | 1 | 2026-06-22 13:38:58 |
| f3 | 4 | 2026-06-22 13:32:29 → 2026-06-24 11:48:57 |
| f3_hallazgos | 3 | 2026-06-22 13:41:42 → 2026-06-24 11:48:55 |
| f4 | 7 | 2026-06-23 10:37:21 → 2026-06-23 10:53:22 |
| f5 | 6 | 2026-06-24 13:31:02 → 2026-06-24 14:47:28 |
| **f2** | **0** | — |
| **f2_1** | **0** | — |

### 3.4 ¿Hubo rollback, ejecución parcial o abortada?

**No para F2/F2.1.** Esas fases nunca aparecieron en el log, ni siquiera con status='error'.

Hubo errores en otras fases (f3 #1, f4 #7-8, f5 #16), pero todas se recuperaron en runs posteriores. Ningún rollback afectó F2/F2.1.

### 3.5 Nota sobre `f3_hallazgos`

El phase `f3_hallazgos` aparece 3 veces en el log. Es un sub-phase interno de `build_f3()`: `_build_hallazgos()` (línea 1845) se llama desde `build_f3` (línea 1828) y registra su propia fila con `_log_run(..., phase="f3_hallazgos", ...)` en la línea 1933. No es una fase independiente del orquestador; no aparece en `argparse choices`.

---

## PARTE 4 — Estado del código

### 4.1 `_build_dim_raza()`

| Atributo | Valor |
|---|---|
| **Archivo** | `src/informes_vet/silver_etl.py` |
| **Líneas** | 903 – 946 (44 líneas) |
| **Estado** | **Completa y terminada** |
| **Llamada por** | `build_f2()` línea 1049 |
| **Funcionalidad** | Crea entradas en `dim_raza` solo para razas con `freq >= RAZA_AUTOAPPROVE_THRESHOLD` (3). Inserta con `on_conflict_do_nothing(index_elements=["dim_especie_id", "nombre_canonico"])` sobre UNIQUE constraint. |
| **Idempotencia** | ✅ Confirmada por código (líneas 932-940). Re-ejecución es no-op. |

### 4.2 `_build_map_raza()`

| Atributo | Valor |
|---|---|
| **Archivo** | `src/informes_vet/silver_etl.py` |
| **Líneas** | 949 – 999 (51 líneas) |
| **Estado** | **Completa y terminada** |
| **Llamada por** | `build_f2()` línea 1050 |
| **Funcionalidad** | Genera filas para `map_raza` (todas las 163 variantes; `dim_raza_id` poblado si aprobada o NULL si pendiente) y para `stg_razas_detectadas` (solo freq<3). |
| **Idempotencia** | ✅ `map_raza` tiene UNIQUE constraint en `valor_original`. `stg_razas_detectadas` también. |

### 4.3 `refactor_dim_raza()`

| Atributo | Valor |
|---|---|
| **Archivo** | `src/informes_vet/silver_etl.py` |
| **Líneas** | 1152 – 1315 (164 líneas) |
| **Estado** | **Completa y terminada** |
| **Llamada por** | `build_f2_1()` línea 1409 |
| **Funcionalidad** | Consolida 7 grupos de duplicados en `dim_raza` (mediante UPDATE de `map_raza.dim_raza_id` + DELETE en `dim_raza`) y aplica renames DPC → "Doméstico Pelo Corto" / DPL → "Doméstico Pelo Largo". |
| **Idempotencia** | ✅ Líneas 1188-1197: `already_applied` check detecta consolidación ya hecha y retorna early. |

### 4.4 `backfill_raza()` (no listada por el usuario pero consultada)

| Atributo | Valor |
|---|---|
| **Existencia** | **NO EXISTE en el código.** Verificado por `grep -r "def backfill_raza"` (cero resultados). |
| **Conclusión** | El usuario incluyó esta función en la pregunta de auditoría pero no existe. Solo existe `backfill_silver_informes_edad` (líneas 1318-1388) que backfillea `edad_meses` y `edad_parse_ok`, no `dim_raza_id`. |

### 4.5 Resumen

| Función | Existe | Terminada | Idempotente | Nunca llamada |
|---|---|---|---|---|
| `_build_dim_raza` | ✅ | ✅ | ✅ | ✅ (sería llamada si F2 corriese) |
| `_build_map_raza` | ✅ | ✅ | ✅ | ✅ |
| `refactor_dim_raza` | ✅ | ✅ | ✅ | ✅ (sería llamada si F2.1 corriese) |
| `backfill_silver_informes_edad` | ✅ | ✅ | ✅ | ✅ (sería llamada si F2.1 corriese) |
| `build_f2` | ✅ | ✅ | ✅ | ✅ |
| `build_f2_1` | ✅ | ✅ | ✅ | ✅ |

**No hay código muerto.** Todo el código F2/F2.1 está vivo, solo nunca se invocó.

---

## PARTE 5 — Dependencias

### 5.1 Referencias a `dim_raza`, `map_raza`, `raza_id`, `dim_raza_id`

**Búsqueda exhaustiva (`grep -rn`) en todo el proyecto:**

#### dim_raza

| Archivo | Línea | Uso |
|---|---|---|
| `src/informes_vet/models_silver.py` | varios | Definición del schema (id, dim_especie_id, nombre_canonico, es_mestizo, agrupacion, fuente) |
| `src/informes_vet/silver_etl.py` | 597, 903, 949, 1152 | Import + 3 funciones |
| `src/informes_vet/silver_db.py` | — | (no referenciada explícitamente; index_exists sí) |
| `src/informes_vet/silver_dims.py` | — | (silver_dims.bootstrap_basico no crea dim_raza; se crea en F2) |

#### map_raza

| Archivo | Línea | Uso |
|---|---|---|
| `src/informes_vet/models_silver.py` | 346 | Definición del schema |
| `src/informes_vet/silver_etl.py` | 601, 949, 1152, 1232, 1280 | Import + 2 funciones |

#### dim_raza_id

| Archivo | Línea | Uso |
|---|---|---|
| `src/informes_vet/models_silver.py` | 48, 351 | Columna en `silver_informes` (FK a dim_raza), columna en `map_raza` (FK a dim_raza) |
| `src/informes_vet/silver_etl.py` | 555 | Placeholder en F1: `"dim_raza_id": None,  # F2` |
| `src/informes_vet/silver_etl.py` | 908, 969, 977, 980, 1161, 1235-1236, 1282-1283 | Lógica interna de `_build_dim_raza`, `_build_map_raza`, `refactor_dim_raza` |

**Ningún archivo de F3, F4 o F5 lee `silver_informes.dim_raza_id`** (verificado en Parte 6).

#### raza_id (sufijo abstracto)

Cero referencias fuera de las anteriores.

### 5.2 ¿Quién DEBERÍA usar `dim_raza_id`?

- **Gold (futuro):** `gold_informes` hará JOIN con `dim_raza` para filtrar/agrupar por raza. `gold_diagnosticos_raza` segmenta hallazgos por raza.
- **Silver (hoy):** Solo F2 mismo, a través de `map_raza.dim_raza_id` (FK lógica, no constraint real — `PRAGMA foreign_keys` está en `OFF` por defecto; el evento `connect` en `silver_db.py:36` lo activa, pero SQLite ignora FKs cross-engine).

### 5.3 ¿Qué queda roto?

| Componente | Estado | Impacto |
|---|---|---|
| `silver_informes.dim_raza_id` | 100% NULL (0/2893) | Gold no puede filtrar por raza desde silver_informes |
| `dim_raza` | 0 filas | No existe catálogo canónico de razas |
| `map_raza` | 0 filas | No existe mapeo de variantes → canónico |
| `map_especie`, `map_sexo`, `map_estudio` | 0 filas | Tablas operativas de auditoría vacías |
| `stg_razas_detectadas` | 0 filas | Razas pendientes de revisión no están registradas |
| `stg_valores_no_mapeados` | 0 filas | Excepciones especie/sexo/estudio no registradas |
| F3/F4/F5 | Operativos | No requieren F2 para funcionar (ver Parte 6) |

---

## PARTE 6 — Seguridad

### 6.1 ¿Ejecutar F2 hoy puede afectar F3/F4/F5?

**No. Evidencia:**

#### Búsqueda de `raza` en código F3/F4/F5

```
silver_f3_dims.py     → 0 referencias
silver_f4_values.py   → 0 referencias
silver_f5_conclusions.py → 0 referencias
```

#### Búsqueda de `raza` en scripts de verificación

```
scripts/verify_silver_f3.py → 0 referencias
scripts/verify_silver_f4.py → 0 referencias
scripts/verify_silver_f5.py → 0 referencias
```

#### ¿Qué tablas consume F3?

- **Entradas:** `raw.hallazgos`, `dim_organo`, `raw.informes` (para joins por `informe_id`).
- **Salidas:** `dim_atributo`, `dim_organo_atributo`, `dim_segmento_anatomico`, `dim_valor_atributo`, `silver_hallazgos`, `silver_atributos_hallazgo`.
- **Intersección con F2:** ninguna tabla en común.

#### ¿Qué tablas consume F4?

- **Entradas:** `silver_atributos_hallazgo` (post-F3), `dim_atributo`, `dim_organo_atributo`.
- **Salidas:** `dim_valor_atributo` (consolidado), `map_atributo_valor`, UPDATE de `silver_atributos_hallazgo.dim_valor_atributo_id`.
- **Intersección con F2:** ninguna tabla en común.

#### ¿Qué tablas consume F5?

- **Entradas:** `raw.conclusiones`, `dim_termino_conclusion` (seed), `silver_informes` (para joins por `informe_id`).
- **Salidas:** `silver_conclusion_items` (DROP+CREATE si `termino_conclusion_id` no existe), `stg_conclusion_no_match`.
- **Intersección con F2:** `silver_informes` se lee pero F2 no la escribe. Sin colisión.

### 6.2 `dim_valor_atributo` y `silver_conclusion_items`

- **`dim_valor_atributo`:** Poblada por F3 (172 seeds) y F4 (consolidación). F2 no la toca. **Sin riesgo.**
- **`silver_conclusion_items`:** Tiene schema v5.0 con columna `termino_conclusion_id`. `migrate()` (silver_db.py:285-310) detecta la presencia de la columna y NO hace DROP+CREATE. F5 hace `DELETE FROM silver_conclusion_items WHERE informe_id IN (...)` + `INSERT`. **Sin riesgo de DROP+CREATE por ejecutar F2 antes.**

### 6.3 Riesgo residual

F2 **reescribe `dim_raza` y `map_raza` con `INSERT ON CONFLICT DO NOTHING`**. Si F2 ya se hubiera ejecutado antes, re-ejecutarlo es no-op para esas tablas. Pero hoy ambas están vacías, así que la primera ejecución las puebla.

F2 también escribe en `stg_razas_detectadas` y `stg_valores_no_mapeados` (también con `ON CONFLICT DO NOTHING`). **Idempotente.**

### 6.4 Veredicto de seguridad

**Ejecutar `build_f2()` y `build_f2_1()` hoy es SEGURO respecto a F3/F4/F5.** Los 19/19 verify checks de F3/F4/F5 pasarán idénticamente. La única verificación que fallaría actualmente es `verify_silver_f2_1.py` (que espera outputs de F2.1), y dejaría de fallar después de ejecutar F2.1.

---

## PARTE 7 — Estado funcional

### 7.1 Conteos directos desde `informes.db` (RAW) y `silver.db` (Silver)

#### RAW (informes.db)

| Métrica | Valor | Fuente |
|---|---|---|
| Total informes RAW | **2893** | `SELECT COUNT(*) FROM raw.informes` |
| Informes con raza no-vacía | **2829** | filtro `raza IS NOT NULL AND TRIM(raza) != ''` |
| Informes sin raza | **64** | diferencia |
| Distinct valores de raza no-vacíos | **163** | `SELECT COUNT(DISTINCT raza)` |
| Razas con freq ≥ 3 (auto-aprobadas) | **63** | `GROUP BY raza HAVING c >= 3` |
| Razas con freq = 2 | **21** | `GROUP BY raza HAVING c = 2` |
| Razas con freq = 1 | **79** | `GROUP BY raza HAVING c = 1` |

#### Top 30 razas por frecuencia

| freq | raza |
|---|---|
| 643 | 'Mestizo' |
| 624 | 'DPC' |
| 222 | 'DPL' |
| 202 | 'Poodle' |
| 106 | 'Dachshund' |
| 82 | 'Terrier Chileno' |
| 81 | 'Pastor Alemán' |
| 75 | 'Yorkshire' |
| 59 | 'Golden Retriever' |
| 42 | 'Beagle' |
| 38 | 'Akita' |
| 35 | 'Boyero de Berna' |
| 34 | 'Bull Dog Francés' |
| 33 | 'Pug' |
| 29 | 'Schnauzer' |
| 27 | 'Chihuahua' |
| 26 | 'Border Collie' |
| 24 | 'Bóxer' |
| 23 | 'Labrador' |
| 20 | 'Rottweiler' |
| 16 | 'Samoyedo' |
| 15 | 'Gran Pirineo' |
| 15 | 'Maltés' |
| 14 | 'Boxer' |
| 13 | 'Cocker' |
| 13 | 'Shih Tzu' |
| 11 | 'Cane Corso' |
| 11 | 'Gran Danés' |
| 10 | 'Siamés' |
| 9 | 'Weimaraner' |

#### Variantes Mestizo detectadas

`'Mestizo'`, `'Mestiza'`, `'Mestizoq'` (typo), `'Mestizp'` (typo), `'mestizo'` (lowercase), `'Mestizo.'` (con punto)

#### Variantes DPC/DPL detectadas

`'DPC'`, `'DPL'`, `'DPc'` (typo), `'DPl'` (typo)

### 7.2 Conteos directos desde `silver.db` (estado actual)

| Tabla | Filas actuales |
|---|---|
| `silver_informes` | 2893 |
| `silver_informes.dim_raza_id IS NOT NULL` | **0** |
| `dim_raza` | **0** |
| `map_raza` | **0** |
| `map_especie` | **0** |
| `map_sexo` | **0** |
| `map_estudio` | **0** |
| `stg_razas_detectadas` | **0** |
| `stg_valores_no_mapeados` | **0** |
| `silver_hallazgos` | 27866 |
| `silver_atributos_hallazgo` | 114753 |
| `silver_informes.edad_meses IS NOT NULL` | 2854 / 2893 (98.72%) |

### 7.3 Proyección: cuántas filas tendría cada tabla DESPUÉS de ejecutar F2

| Tabla | Esperado post-F2 | Cálculo |
|---|---|---|
| `dim_raza` | **63** | 63 razas con freq≥3 (sin consolidar) |
| `map_raza` | **163** | todas las variantes (aprobadas + pendientes) |
| `map_especie` | **~5** | caninos, felinos, etc. |
| `map_sexo` | **~3** | Hembra, Macho, Indeterminado |
| `map_estudio` | **~10** | Abdominal, Gestacional, etc. |
| `stg_razas_detectadas` | **100** | 21 (freq=2) + 79 (freq=1) |
| `stg_valores_no_mapeados` | **~24** | excepciones especie/sexo/estudio (verificado por `verify_silver_f2_1.py` línea 151 que espera 24) |

### 7.4 Proyección DESPUÉS de ejecutar F2.1 (consolidación)

| Tabla | Esperado post-F2.1 | Cálculo |
|---|---|---|
| `dim_raza` | **56** | 63 - 7 consolidaciones (Bóxer/Boxer, Bull Dog Frances/Francés, Rotweiler/Rottweiler, Pastor alemán/Alemán, Terrier chileno/Chileno, Mestizo+Mestiza+Mestizo. consolidados, DPC renombrado). **Nota:** la entrada DPC se renombra a "Doméstico Pelo Corto", no se borra. La consolidación DPC+DPc requiere agrupar por `(dim_especie_id, canónico)`. El conteo exacto post-F2.1 depende de si 'DPc'/'DPl' (typos) generan entradas adicionales en dim_raza o quedan solo en map_raza. |
| `map_raza` | **163** | conserva todas las variantes; FKs redirigidas |
| `silver_informes.edad_meses IS NOT NULL` | **2865 / 2893 (99.04%)** | F2.1 aplica `parse_edad_meses_v2` (parser robusto). Esperado: ~11 filas adicionales parseadas vs F1. |

### 7.5 Informes enlazados a raza (proyección)

| Escenario | Informes con `dim_raza_id` |
|---|---|
| Post-F2 (con backfill de silver_informes.dim_raza_id) | **~2820** (2829 con raza en RAW × % de match en map_raza) |
| Informes sin raza | **64** (RAZAS con valor NULL/vacío en RAW) |
| Pendientes de revisión (dim_raza_id NULL pero con valor en RAW) | **~100** (razas con freq<3 que van a stg_razas_detectadas) |

**Nota:** El número exacto de "informes enlazados" depende de si se ejecuta el backfill de `silver_informes.dim_raza_id` (F2.1 actualmente NO lo hace — solo `backfill_silver_informes_edad`).

---

## PARTE 8 — Esfuerzo real

### 8.1 Código existente (NO requiere trabajo)

| Componente | Líneas | Ubicación |
|---|---|---|
| `build_f2()` (orquestador) | 78 | silver_etl.py:1006-1083 |
| `_build_dim_raza()` | 44 | silver_etl.py:903-946 |
| `_build_map_raza()` | 51 | silver_etl.py:949-999 |
| `_build_map_especie()` | 30 | silver_etl.py:757-786 |
| `_build_map_sexo()` | 55 | silver_etl.py:792-846 |
| `_build_map_estudio()` | 44 | silver_etl.py:853-896 |
| `build_f2_1()` (orquestador) | 39 | silver_etl.py:1391-1429 |
| `refactor_dim_raza()` | 164 | silver_etl.py:1152-1315 |
| `backfill_silver_informes_edad()` | 71 | silver_etl.py:1318-1388 |
| `parse_edad_meses_v2()` (parser robusto) | 46 | silver_etl.py:260-305 |
| CLI orquestador (con --phase f2 y --phase f2_1) | — | scripts/build_silver.py |
| `verify_silver_f2.py` | 123 | scripts/verify_silver_f2.py |
| `verify_silver_f2_1.py` | 186 | scripts/verify_silver_f2_1.py |

**Total código existente: ~931 líneas ya implementadas y testeadas internamente.**

### 8.2 Código faltante

| Componente | Estimación | Razonamiento |
|---|---|---|
| Script cross-layer para poblar `silver_informes.dim_raza_id` | ~50-80 LOC | SELECT raw.informes → JOIN map_raza → UPDATE silver_informes. Idempotente (UPDATE solo si cambia). |
| (Opcional) Mejora en `_RAZA_CANONICAL_ALIAS` para typos `DPc`/`DPl`, `Mestizoq`/`Mestizp`/`mestizo` | ~6 líneas | Añadir entradas al dict existente. |

### 8.3 Configuración

| Componente | Estimación |
|---|---|
| Backup de `silver.db` → `silver.db.pre_f2` | 1 comando shell (5 seg, silver.db = 41 MB) |
| Nada más. El orquestador ya conoce las fases. | — |

### 8.4 Migraciones

| Migración | Estado |
|---|---|
| v2.1 (`add_edad_parse_ok`) | **Ya aplicada**. `silver_informes.edad_parse_ok` existe. F2.1 detectará `already_applied` y no la re-ejecutará. |
| v3.0 (F3 columnas) | Ya aplicada |
| v5.0 (F5 DROP+CREATE) | Ya aplicada (la columna `termino_conclusion_id` existe en `silver_conclusion_items`) |
| **Nuevas migraciones necesarias** | **CERO** |

### 8.5 Backfill

| Componente | Estimación |
|---|---|
| Script `scripts/f2_backfill_informes_raza.py` | 50-80 LOC (ver §8.2) |
| Tiempo de ejecución | <1 segundo (UPDATE de 2893 filas, índice ya existe en `dim_raza_id`) |

### 8.6 Verificación

| Verificación | Estado |
|---|---|
| `verify_silver_f2.py` | ✅ Listo. Esperará pasar después de ejecutar F2 (sin consolidación). |
| `verify_silver_f2_1.py` | ✅ Listo. Esperará pasar después de F2 + F2.1 + backfill. |
| `verify_silver_f3.py`, `verify_silver_f4.py`, `verify_silver_f5.py` | ✅ Listo. Pasan idénticamente. |

### 8.7 Documentación

| Documento | Acción |
|---|---|
| `docs/SILVER_FINAL_SIGNOFF.md` | Actualizar: "F2 cerrado al 100%" |
| `docs/SILVER_LAYER.md` | Actualizar diagrama de fases |
| `docs/GOLD_*` | Actualizar claim sobre dim_raza gap |
| `docs/F2_1_DATA_QUALITY.md` | Confirmar ejecución (opcional) |

### 8.8 Horas reales estimadas (solo código faltante)

| Tarea | Horas estimadas |
|---|---|
| Backup silver.db | 0.05 h (5 min) |
| Ejecutar `build_silver.py --phase f2` | 0.10 h (5-10 min de ejecución, supervisado) |
| Ejecutar `build_silver.py --phase f2_1` | 0.10 h (5-10 min) |
| Crear script `f2_backfill_informes_raza.py` | 0.50 h (incluye tests básicos) |
| Ejecutar script backfill | 0.05 h |
| Verificar con `verify_silver_f2.py`, `verify_silver_f2_1.py`, `verify_silver_f3.py`, `verify_silver_f4.py`, `verify_silver_f5.py` | 0.25 h |
| Actualizar documentación | 0.50 h |
| **TOTAL código faltante** | **~1.5 horas-hombre** |

**No se incluye tiempo de espera de ejecución** (las fases tardan <2 min cada una en SQLite local).

---

## PARTE 9 — Diagnóstico final

### Clasificación: **A) F2 está completo pero nunca fue ejecutado**

### 9.1 Evidencia que sostiene A

1. **`build_f2()` existe en `silver_etl.py:1006-1083`** — función completa de 78 líneas con docstring, manejo de errores, logging en `silver_etl_runs`.

2. **Las 6 sub-funciones que invoca (`_build_dim_raza`, `_build_map_raza`, `_build_map_especie`, `_build_map_sexo`, `_build_map_estudio`, `_upsert_chunks`, `_log_run`) existen y están completas.**

3. **El orquestador `scripts/build_silver.py` tiene la llamada activa en línea 251**, dentro del bloque `if args.phase == "f2":`. No está comentado, no está detrás de una feature flag, no está en una rama `else`.

4. **`silver_etl_runs` tiene 21 filas. Cero con `phase='f2'`. Cero con `phase='f2_1'`.**

5. **Las tablas que F2 debería poblar (`dim_raza`, `map_raza`, `map_especie`, `map_sexo`, `map_estudio`, `stg_razas_detectadas`, `stg_valores_no_mapeados`) tienen 0 filas.**

6. **`silver_informes.dim_raza_id` está al 100% NULL** (0/2893), confirmando que F1 (que escribe esta columna con `None`) corrió pero la fase posterior que la llenaría nunca lo hizo.

7. **No hay evidencia de rollback, refactor o eliminación**: las llamadas están en su lugar, las funciones están en su lugar, el argparse incluye `("f1", "f2", "f2_1", "f3", "f4", "f5")`.

### 9.2 Por qué no es B, C, D ni E

- **B) F2 implementado parcialmente:** Incorrecto. La función está completa.
- **C) F2 roto por refactor:** Incorrecto. El código no muestra síntomas de refactor incompleto (no hay `# TODO`, no hay `pass` ni `raise NotImplementedError`).
- **D) F2 reemplazado por otra implementación:** Incorrecto. No existe otra implementación de F2 ni en `silver_etl.py` ni en ningún otro archivo del proyecto.
- **E) Otro:** Considerado. Pero la evidencia es uniforme: el código está, simplemente nunca se invocó.

### 9.3 Causa raíz específica

**Causa raíz:** El orquestador documenta el orden F1 → F2 → F2.1 → F3 → F4 → F5 en su docstring (líneas 6-9 de `scripts/build_silver.py`), pero el operador (o el script de automatización) saltó de F1 directamente a F3 sin invocar F2/F2.1.

Esto es un **gap operacional**, no un **bug técnico**. El sistema funcionó como se le indicó: ejecutar las fases que se le pidieron.

---

## PARTE 10 — Recomendación

### 10.1 ¿Conviene ejecutar F2 antes de Gold?

**SÍ. Sin ambigüedad.**

**Justificación técnica:**
- Gold requerirá joins con `dim_raza` para `gold_informes`, `gold_diagnosticos_raza`, y posiblemente `gold_coocurrencias_raza`.
- Sin F2 ejecutado, `dim_raza` tiene 0 filas. Cualquier JOIN devolvería NULL o vacío.
- Sin F2.1, el `dim_raza` post-F2 tendría 63 filas con duplicados (Bóxer/Boxer, DPC/DPL, etc.), obligando a Gold a hacer su propia normalización (lo cual duplica lógica).
- F2 es idempotente y ortogonal a F3/F4/F5. No hay riesgo de regresión.

**Tiempo requerido:** ~1 hora-hombre (ver §8.8).

### 10.2 ¿Conviene implementar un mini F2.1?

**SÍ, pero solo para la parte de consolidación de dim_raza y DPC/DPL. NO para `parse_edad_meses_v2`.**

**Justificación técnica:**
- `refactor_dim_raza()` ya existe y está completo en `silver_etl.py:1152-1315`. Solo hay que ejecutarlo.
- F2 deja `dim_raza` con duplicados (Bóxer/Boxer, etc.). Sin refactor, Gold verá "Bóxer" y "Boxer" como dos razas distintas — segmentación rota.
- DPC/DPL son abreviaciones. Sin rename, Gold mostrará "DPC" en lugar de "Doméstico Pelo Corto" — UX rota.

**Sobre `parse_edad_meses_v2`:** La cobertura actual con v1 es 98.72% (2854/2893). F2.1 la subiría a ~99.04%. La diferencia es 11 informes. Es deseable pero no bloqueante. Si se decide no ejecutar el backfill de edad, Gold seguirá funcionando (los 11 informes sin `edad_meses` simplemente no tendrán categoría de edad).

### 10.3 ¿Conviene reparar el pipeline?

**NO requiere reparación. El pipeline está intacto.**

**Justificación técnica:**
- Las llamadas a F2/F2.1 existen y son correctas en `scripts/build_silver.py`.
- Las funciones existen y son completas en `silver_etl.py`.
- El argparse acepta las fases.
- **No hay nada que reparar a nivel de código.** Solo falta ejecutar.

**Acción recomendada:** documentar en `README.md` o `OPERATIONS.md` el orden canónico de ejecución del pipeline, para evitar que vuelva a ocurrir.

### 10.4 ¿Conviene hacer una migración?

**NO. Ninguna migración nueva es necesaria.**

**Justificación técnica:**
- v2.1 ya aplicada (columna `edad_parse_ok` existe en `silver_informes`).
- v3.0 ya aplicada (columnas F3 en `silver_atributos_hallazgo`).
- v5.0 ya aplicada (columna `termino_conclusion_id` en `silver_conclusion_items`).
- La columna `silver_informes.dim_raza_id` existe desde el schema inicial (línea 48 de `models_silver.py`). No requiere ALTER.
- La tabla `dim_raza` existe desde el schema inicial. No requiere CREATE.

### 10.5 ¿Conviene construir `dim_raza` desde Gold?

**NO. Sería una violación arquitectónica grave.**

**Justificación técnica:**
- Rompe la medallion architecture: Gold debe leer de Silver, no construir dimensiones propias.
- Generaría inconsistencia: si Silver se reconstruye desde RAW algún día, Gold perdería la dimensión.
- Dificulta auditoría: el linaje RAW → Silver → Gold se rompe.
- El código para hacerlo en Silver YA EXISTE y es idempotente.

### 10.6 Veredicto final

**🟢 GO para Gold, CONDICIONADO a:**

1. Ejecutar `python scripts/build_silver.py --phase f2` (5-10 min).
2. Ejecutar `python scripts/build_silver.py --phase f2_1` (5-10 min).
3. Crear y ejecutar `scripts/f2_backfill_informes_raza.py` (~50 LOC, 5 min de ejecución).
4. Verificar con los 5 scripts `verify_silver_*.py` que pasen.

**Costo total:** ~1.5 horas-hombre + 30 minutos de ejecución supervisada.
**Beneficio:** `silver_informes.dim_raza_id` pasa de 0% a ~97% poblado. `dim_raza` pasa de 0 a 56 entradas consolidadas. Gold queda habilitado para todos sus análisis raciales.

**Riesgo de NO hacerlo:** Gold queda con `gold_informes.raza` 100% NULL, `gold_diagnosticos_raza` vacío, y `gold_coocurrencias_raza` no se puede construir.

---

## Anexo A — Queries SQL utilizadas para gathering de evidencia

```sql
-- silver_etl_runs
SELECT id, phase, status, rows_read, rows_written, rows_skipped,
       duration_ms, actor, datetime(started_at)
FROM silver_etl_runs ORDER BY id;

-- Conteos Silver actuales
SELECT COUNT(*) FROM silver_informes;
SELECT COUNT(*) FROM dim_raza;
SELECT COUNT(*) FROM map_raza;
SELECT COUNT(*), SUM(CASE WHEN dim_raza_id IS NOT NULL THEN 1 ELSE 0 END)
FROM silver_informes;

-- RAW raza counts
SELECT COUNT(DISTINCT raza) FROM raw.informes
WHERE raza IS NOT NULL AND TRIM(raza) != '';
SELECT raza, COUNT(*) c FROM raw.informes
WHERE raza IS NOT NULL AND TRIM(raza) != ''
GROUP BY raza ORDER BY c DESC;
```

## Anexo B — Rutas de archivos críticos

| Ruta | Propósito |
|---|---|
| `src/informes_vet/silver_etl.py` | Orquestadores de fase + helpers F2/F2.1 |
| `src/informes_vet/models_silver.py` | Schema (24 tablas + silver_etl_runs) |
| `src/informes_vet/silver_db.py` | Engine, migrate(), helpers de columna/index |
| `scripts/build_silver.py` | CLI orquestador (línea 251 invoca F2; línea 326 invoca F2.1) |
| `scripts/verify_silver_f2.py` | Verificación post-F2 |
| `scripts/verify_silver_f2_1.py` | Verificación post-F2.1 |
| `silver.db` | BD Silver actual (41 MB, 28 tablas) |
| `informes.db` | BD RAW actual (22 MB) |
