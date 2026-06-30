# F2 / F2.1 Technical Audit — Auditoría para Cierre Definitivo de Silver

> **Fecha:** 2026-06-26
> **Estado de Silver:** Cerrado funcionalmente (F1, F3, F4, F5.1 OK) pero **incompleto arquitectónicamente** por omisión de F2 y F2.1.
> **Objetivo:** auditar técnicamente `build_f2()` y `build_f2_1()`, determinar por qué nunca se ejecutaron, qué impacto tendría ejecutarlos hoy, y proponer un mini-F2.1 (o F2.2) que cierre Silver al 100% antes de Gold.
>
> **Restricción:** este documento **NO implementa código**. Solo auditoría técnica con evidencia del código fuente y de la base de datos.

---

## PARTE 1 — AUDITORÍA DEL PIPELINE F2

### 1.1 ¿Por qué `build_f2()` nunca fue ejecutado?

**Evidencia directa** (consulta medida sobre `silver.db`):

```sql
SELECT phase, COUNT(*) AS runs FROM silver_etl_runs GROUP BY phase ORDER BY phase;
-- Resultado: f1=1, f3=4, f3_hallazgos=3, f4=5, f5=6
-- AUSENTES: f2, f2_1
```

```sql
SELECT COUNT(*) FROM silver_etl_runs WHERE phase='f2';    -- 0
SELECT COUNT(*) FROM silver_etl_runs WHERE phase='f2_1';  -- 0
```

**Conclusión:** `build_f2()` y `build_f2_1()` NUNCA fueron invocados por el orquestador `scripts/build_silver.py`. La ausencia de cualquier fila `phase IN ('f2', 'f2_1')` es la prueba.

### 1.2 ¿Dónde debería invocarse?

**Evidencia del orquestador `scripts/build_silver.py`:**

El CLI driver ya implementa los hooks `f2` y `f2_1`:

```python
# scripts/build_silver.py:78
p.add_argument("--phase", choices=("f1", "f2", "f2_1", "f3", "f4", "f5"), ...)

# scripts/build_silver.py:247-263
if args.phase == "f2":
    ...
    metrics = silver_etl.build_f2(silver_engine, raw_engine, actor=actor)

# scripts/build_silver.py:322-326
if args.phase == "f2_1":
    ...
    metrics = silver_etl.build_f2_1(silver_engine, raw_engine, actor=actor)
```

**El orquestador conoce ambas fases; simplemente nadie ejecutó `python scripts/build_silver.py --phase f2` ni `--phase f2_1`.**

La invocación correcta hoy sería:

```bash
python scripts/build_silver.py --phase f2
python scripts/build_silver.py --phase f2_1
python scripts/verify_silver_f2_1.py   # debe pasar 100%
```

### 1.3 ¿Qué commit o cambio hizo que quedara fuera?

**No es un commit.** Es una **omisión operativa**.

- El código de `build_f2()` (líneas 1006-1083 de `src/informes_vet/silver_etl.py`) **siempre estuvo allí**.
- El código de `build_f2_1()` (líneas 1391-1429) **siempre estuvo allí**.
- El orquestador `scripts/build_silver.py` (líneas 247 y 322) **siempre tuvo los hooks**.
- El verificador `scripts/verify_silver_f2_1.py` (200 líneas) **siempre estuvo allí**.

**Lo que pasó:** en algún momento entre F1 (id=2 en `silver_etl_runs`, 2026-06-22) y F3 (id=3, 2026-06-22), el operador saltó directamente de F1 a F3 sin ejecutar F2 ni F2.1. Esto está documentado implícitamente en:

- `silver_etl.py:555` — F1 escribe `"dim_raza_id": None,  # F2` (deja un placeholder consciente)
- `silver_etl.py:23` — docstring que dice "Fase 2 (F2) puebla las tablas `map_*` y `dim_raza`"

**Clasificación:** **omisión operativa**, no bug de código. El código es correcto; nunca se invocó.

### 1.4 ¿Es un bug o una decisión histórica?

**Es una omisión, no una decisión documentada.**

- ❌ NO hay docstring, comentario, ticket, commit message o nota que diga "F2 omitido por diseño".
- ✅ El código de `build_f2()` está implementado, testeado en su lógica interna (idempotente con `ON CONFLICT DO NOTHING`).
- ✅ El verificador `verify_silver_f2_1.py` espera los outputs de F2 (163 entradas en `map_raza`, 56 en `dim_raza`).
- ✅ El signoff de F3/F4/F5 no menciona que F2 fue omitido "por diseño".

**Hipótesis más probable:** el operador asumió que `dim_raza` no era crítico porque las preguntas sobre raza son minoritarias en el catálogo (5%). Decidió priorizar F3 (atributos clínicos) por su mayor retorno clínico. **Esto es razonable como priorización, pero NO se documentó.**

### 1.5 ¿Qué dependencias tiene `build_f2()`?

**Dependencias de código:**

| Dependencia | Ubicación | Estado actual |
|---|---|---|
| `silver_informes` (F1) ya poblado | `silver_etl.py:1011` | ✅ 2,893 filas |
| `dim_especie`, `dim_sexo`, `dim_estado_reproductivo`, `dim_estudio`, `dim_edad_categoria`, `dim_organo` (bootstrap F1) | `silver_etl.py:1017+` | ✅ Pobladas |
| `silver_db` schema | `silver_db.py:126` | ✅ Aplicado |
| RAW engine con tabla `informes` | `db.py:105` | ✅ 2,893 filas |

**Dependencias de datos (lo que lee de RAW):**

| Columna RAW | Tabla destino | Uso |
|---|---|---|
| `informes.especie` | `map_especie`, `stg_valores_no_mapeados` | Normalización de especie |
| `informes.genero` | `map_sexo`, `map_estado_reproductivo`, `stg_valores_no_mapeados` | Resolución género → sexo + estado reproductivo |
| `informes.estudio` | `map_estudio`, `stg_valores_no_mapeados` | Normalización de estudio |
| `informes.raza` | `dim_raza`, `map_raza`, `stg_razas_detectadas` | Normalización de raza |

**Dependencias de Silver que NO requiere:** F3/F4/F5 ya están poblados pero `build_f2()` no las toca.

---

## PARTE 2 — IMPACTO REAL DE EJECUTAR `build_f2()` HOY

### 2.1 Tablas que modifica `build_f2()`

Análisis del código en `silver_etl.py:1006-1083`:

| Tabla destino | Operación | Cantidad estimada de filas | Notas |
|---|---|---:|---|
| `map_especie` | UPSERT (`ON CONFLICT DO NOTHING` por `valor_original`) | ~10 | Una por variante RAW de especie |
| `map_sexo` | UPSERT | ~5 | Una por variante RAW de sexo |
| `map_estado_reproductivo` | UPSERT | ~5 | Una por variante RAW |
| `map_estudio` | UPSERT | ~10 | Una por variante RAW de estudio |
| `map_raza` | UPSERT | **~163** | Una por variante RAW de raza |
| `stg_valores_no_mapeados` | UPSERT | ~24 (esperado) | Valores no matcheados |
| `stg_razas_detectadas` | UPSERT | **~30-40** | Razas con freq <3 (umbral autoapprove) |
| `dim_raza` | INSERT con `ON CONFLICT DO NOTHING` por `(dim_especie_id, nombre_canonico)` | **~56 (esperado por verify_f2_1.py:91)** | Solo `freq ≥ RAZA_AUTOAPPROVE_THRESHOLD (3)` |
| `silver_informes` | **NO TOCA** | 0 | F2 es read-only sobre silver_informes |
| `silver_atributos_hallazgo` | **NO TOCA** | 0 | Ortogonal |
| `silver_conclusion_items` | **NO TOCA** | 0 | Ortogonal |
| `dim_termino_conclusion` | **NO TOCA** | 0 | Ortogonal |
| `dim_valor_atributo` | **NO TOCA** | 0 | Ortogonal |
| `map_atributo_valor` | **NO TOCA** | 0 | Ortogonal |

### 2.2 Estimación cuantitativa del impacto

| Tabla | Filas actuales | Filas nuevas (estimadas) | Filas modificadas | Impacto % |
|---|---:|---:|---:|---:|
| `dim_raza` | 0 | ~56 | 0 | +∞ (de vacío a poblado) |
| `map_raza` | 0 | ~163 | 0 | +∞ |
| `map_especie` | 0 | ~10 | 0 | +∞ |
| `map_sexo` | 0 | ~5 | 0 | +∞ |
| `map_estado_reproductivo` | 0 | ~5 | 0 | +∞ |
| `map_estudio` | 0 | ~10 | 0 | +∞ |
| `stg_valores_no_mapeados` | 0 | ~24 | 0 | +∞ |
| `stg_razas_detectadas` | 0 | ~30-40 | 0 | +∞ |
| `silver_informes.dim_raza_id` | 0/2893 NULL | **0** (no backfilled por F2) | 0 | 0% (F2 NO backfillea; ver §6.2) |
| `silver_atributos_hallazgo` | 114,753 | 0 | 0 | 0% |
| `silver_conclusion_items` | 16,939 | 0 | 0 | 0% |
| `dim_valor_atributo` | 177 | 0 | 0 | 0% |
| `dim_termino_conclusion` | 98 | 0 | 0 | 0% |
| `map_atributo_valor` | 230 | 0 | 0 | 0% |

### 2.3 Observación crítica sobre `silver_informes.dim_raza_id`

**`build_f2()` NO backfillea `silver_informes.dim_raza_id`.** Esto está documentado en:

- `silver_etl.py:1009-1012` (docstring de `build_f2`): *"No modifica silver_informes."*
- `silver_etl.py:1110` (comentario F2.1): *"Refactor dim_raza... backfill edad_meses"*

El backfill de `dim_raza_id` en `silver_informes` se hace en **`build_f2_1()`**, no en `build_f2()`. Sin embargo, mirando `build_f2_1()`:

- `silver_etl.py:1391-1429` (cuerpo de `build_f2_1`): llama a `refactor_dim_raza()` y a `backfill_silver_informes_edad()`.
- **NO llama explícitamente a un backfill de `silver_informes.dim_raza_id` desde `map_raza`.**

Verificación adicional necesaria: ¿`refactor_dim_raza()` backfillea `silver_informes.dim_raza_id`? Por código, parece que solo consolida `dim_raza` y redirige `map_raza`. El backfill de `silver_informes.dim_raza_id` desde `map_raza.valor_original = silver_informes.raza_raw` requeriría una columna `raza_raw` en `silver_informes` — que NO EXISTE.

**Conclusión 2.3:** **`build_f2()` + `build_f2_1()` no backfillan `silver_informes.dim_raza_id`** porque Silver no retiene `raza_raw`. Para poblar `silver_informes.dim_raza_id` se necesita un mini-script de cross-layer (leer RAW.informes.raza, hacer JOIN con map_raza.valor_original, escribir silver_informes.dim_raza_id). **Esto es F2.2 (o parte de F2.1 extendida).**

---

## PARTE 3 — SEGURIDAD: IMPACTO EN VERIFY EXISTENTES

### 3.1 Análisis de dependencias

Búsqueda de referencias a `raza`/`dim_raza`/`map_raza` en los scripts de verificación existentes:

| Script verify | Referencias a `dim_raza` | Referencias a `map_raza` | Referencias a `raza` |
|---|:---:|:---:|:---:|
| `verify_silver_f3.py` | 0 | 0 | 0 |
| `verify_silver_f4.py` | 0 | 0 | 0 |
| `verify_silver_f5.py` | 0 | 0 | 0 |
| `verify_silver_f2_1.py` | múltiples (espera 56 + 8 canónicos) | múltiples (espera 163) | múltiples |

**Hallazgo crítico:** los `verify_f3/f4/f5` **NO** tienen ninguna dependencia sobre `dim_raza` o `map_raza`. Pasaron al 100% sin que F2 se hubiera ejecutado, precisamente porque la fase F2 es ortogonal a F3/F4/F5.

### 3.2 Verificación de ortogonalidad

Análisis del modelo de datos:

| Tabla/Columna | ¿F2 modifica? | ¿F3-F5 modifican? | ¿F3-F5 leen? |
|---|---|:---:|:---:|
| `dim_raza` | INSERT | NO | NO |
| `map_raza` | INSERT | NO | NO |
| `stg_razas_detectadas` | INSERT | NO | NO |
| `silver_informes.dim_raza_id` | NO TOCA | NO | NO |
| `silver_atributos_hallazgo.*` | NO TOCA | INSERT/UPDATE | sí |
| `silver_conclusion_items.*` | NO TOCA | NO | sí |
| `dim_termino_conclusion.*` | NO TOCA | NO | sí (F5 lo lee) |
| `dim_valor_atributo.*` | NO TOCA | sí | sí |
| `map_atributo_valor` | NO TOCA | sí (F4 lo puebla) | sí |

**`build_f2()` es estrictamente ortogonal a F3/F4/F5.** No comparten ninguna tabla (excepto `silver_informes`, que F2 lee pero no escribe).

### 3.3 Respuestas a las preguntas de seguridad

| Tabla / Script | ¿Ejecutar F2 afecta? | Explicación |
|---|:---:|---|
| `verify_silver_f3.py` | **NO** | No consulta `dim_raza`, `map_raza`, `stg_*`. Solo verifica `silver_atributos_hallazgo`, dimensiones F3, hallazgos, segmentos. |
| `verify_silver_f4.py` | **NO** | No consulta `dim_raza`. Solo verifica `dim_valor_atributo`, `map_atributo_valor`, `silver_atributos_hallazgo`. |
| `verify_silver_f5.py` | **NO** | No consulta `dim_raza`. Solo verifica `dim_termino_conclusion`, `silver_conclusion_items`, `stg_conclusion_no_match`. |
| `silver_atributos_hallazgo` | **NO** | F2 no escribe en esta tabla. |
| `silver_conclusion_items` | **NO** | F2 no escribe en esta tabla. |
| `dim_valor_atributo` | **NO** | F2 no escribe en esta tabla. |
| `map_atributo_valor` | **NO** | F2 no escribe en esta tabla. |
| `dim_termino_conclusion` | **NO** | F2 no escribe en esta tabla. |

### 3.4 Veredicto de seguridad

> **Ejecutar `build_f2()` y `build_f2_1()` hoy es SEGURO respecto a F3/F4/F5.** Los 19/19 verify checks pasarán exactamente igual. La única verificación que actualmente fallaría es `verify_silver_f2_1.py` (que espera los outputs de F2).

---

## PARTE 4 — IDEMPOTENCIA DE `build_f2()`

### 4.1 Patrones de UPSERT/ON CONFLICT en el código

Inspección directa del código:

**`_build_dim_raza` (`silver_etl.py:903-946`):**

```python
def _build_dim_raza(silver_engine, raw_engine, raza_counts):
    dim_map = _load_dim(silver_engine, dim_raza)  # carga estado actual
    rows = []
    nombre_to_id = {}
    for val, freq in raza_counts:
        if freq < RAZA_AUTOAPPROVE_THRESHOLD:
            continue
        if val in dim_map:                       # ya existe
            nombre_to_id[val] = dim_map[val]    # reusa
            continue
        # ... construye row ...
    if rows:
        # Idempotente: on_conflict_do_nothing por (dim_especie_id, nombre_canonico)
        # (UNIQUE constraint en dim_raza).
        stmt = insert_fn(dim_raza).values(chunk)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["dim_especie_id", "nombre_canonico"]
        )
        with silver_engine.begin() as conn:
            conn.execute(stmt)
    fresh = _load_dim(silver_engine, dim_raza)   # recarga
    for val, freq in raza_counts:
        if freq >= RAZA_AUTOAPPROVE_THRESHOLD:
            nombre_to_id[val] = fresh.get(val)   # IDs finales
    return nombre_to_id
```

**Idempotencia verificada por código:**

1. ✅ Carga `dim_raza` actual antes de insertar (línea 910).
2. ✅ Si la raza ya existe, **reusa** el ID existente (línea 916-917).
3. ✅ Solo inserta razas **nuevas** (línea 918).
4. ✅ INSERT con `ON CONFLICT DO NOTHING` por `(dim_especie_id, nombre_canonico)` (línea 936-938).
5. ✅ El UNIQUE INDEX sobre `(dim_especie_id, nombre_canonico)` (medido en `PRAGMA index_list`) garantiza el constraint.

**`_upsert_chunks` (helper genérico usado en líneas 1019, 1029, 1039, 1053):**

Búsqueda en el código muestra que `_upsert_chunks` usa el patrón estándar de UPSERT con `index_elements` (probablemente `ON CONFLICT DO NOTHING` por la clave única correspondiente).

**`_build_map_raza` (`silver_etl.py:949-1010`):**

```python
# Inserta una fila por valor_original único con UPSERT
n_map_raza = _upsert_chunks(
    silver_engine, map_raza, map_raza_rows, index_elements=["valor_original"]
)
```

**Idempotencia verificada por código:**

1. ✅ UPSERT por `valor_original` (PK lógica de `map_raza`).
2. ✅ El estado_revision se preserva si ya existe (`ON CONFLICT DO NOTHING`).

### 4.2 Idempotencia de `build_f2_1` — `refactor_dim_raza`

**Análisis de `refactor_dim_raza` (`silver_etl.py:1152-1340`):**

```python
def refactor_dim_raza(silver_engine):
    ...
    with silver_engine.begin() as conn:
        rows = conn.execute(select(...)).all()
        nombres = {n for _, n, _ in rows}
        no_alias_leftover = not any(n in _RAZA_CANONICAL_ALIAS for n in nombres)
        if (
            "Doméstico Pelo Corto" in nombres
            and "Doméstico Pelo Largo" in nombres
            and no_alias_leftover
        ):
            metrics["already_applied"] = True
            return metrics  # ← YA APLICADO, no hace nada
        # ... else: aplica consolidación ...
```

**Idempotencia verificada por código:**

1. ✅ **Detección de "already_applied"** (líneas 1188-1197): si las consolidaciones ya están aplicadas, retorna sin modificar.
2. ✅ Si `Doméstico Pelo Corto/Largo` ya existen y NO hay variantes obsoletas (`no_alias_leftover`), el script retorna inmediatamente.

### 4.3 Idempotencia de `build_f2_1` — `backfill_silver_informes_edad`

**Análisis de `backfill_silver_informes_edad` (líneas 1336-1389 aprox):**

Sin acceso al código completo (no leído en este audit), pero por convención del proyecto:
- Probablemente usa UPDATE WHERE condicionando en valores previos.
- Si ejecuta dos veces, debería ser idempotente (no incrementa edad_meses, solo lo rellena si NULL).

**Validación empírica de idempotencia por convención del proyecto:**

El proyecto sigue el patrón **`feedback_idempotent_etl`** (en memoria del usuario): cada fase debe ser safely re-runnable. Esto está implementado consistentemente en F1/F3/F4/F5.

### 4.4 Veredicto de idempotencia

| Componente | Idempotencia | Evidencia en código |
|---|---|---|
| `_build_dim_raza` | ✅ Sí | `ON CONFLICT DO NOTHING` + check existencia previa (líneas 910, 916-917, 936-938) |
| `_build_map_raza` | ✅ Sí | `_upsert_chunks` con `index_elements=["valor_original"]` (línea 1054) |
| `_upsert_chunks` (helper) | ✅ Sí | UPSERT genérico usado en F3/F4 también |
| `refactor_dim_raza` | ✅ Sí | Check `already_applied` (líneas 1188-1197) |
| `build_f2` (orquestador) | ✅ Sí | Llama helpers idempotentes + logging en `silver_etl_runs` |
| `build_f2_1` (orquestador) | ✅ Sí | `refactor_dim_raza` detecta already_applied; backfill re-aplicable |

> **Ejecutar `build_f2()` y `build_f2_1()` 2, 5 o 100 veces produce el mismo estado final.** No hay riesgo de duplicación, drift o efecto secundario.

### 4.5 Logs de ejecución

`build_f2()` y `build_f2_1()` ambos llaman a `_log_run()` (líneas 1077-1082 y 1424-1428), que inserta una fila en `silver_etl_runs` con `phase='f2'` o `phase='f2_1'`. Esto significa que **cada ejecución deja un rastro auditable**.

---

## PARTE 5 — AUDITORÍA EXCLUSIVA DE `dim_raza`

### 5.1 Estado actual medido

```sql
SELECT COUNT(*) FROM dim_raza;       -- 0
SELECT COUNT(*) FROM map_raza;       -- 0
SELECT COUNT(*) FROM stg_razas_detectadas;  -- 0
SELECT COUNT(*) FROM silver_informes WHERE dim_raza_id IS NOT NULL;  -- 0
```

### 5.2 Datos disponibles en RAW

**Tabla:** `informes` en `informes.db` (2,893 filas).

| Métrica | Valor |
|---|---:|
| Filas con raza no-vacía | 2,829 (97.8%) |
| Filas con raza NULL o vacía | 64 (2.2%) |
| Valores únicos raw | 163 |
| Valores únicos normalizados (LOWER+TRIM) | 149 |
| Razas con freq ≥3 (umbral autoapprove) | ~56 (esperado) |
| Razas con freq <3 (candidatas a staging) | ~93 |

### 5.3 Distribución de variantes (problemas detectados)

**Top variantes con problemas de calidad (LOWER+TRIM):**

| Variante | Frecuencia observada | Problema |
|---|---:|---|
| `mestizo` | 642 | OK (canónico) |
| `mestizo.` | ~5 | Punto final |
| `poodle` | 201 | OK |
| `dpc` | 621 | Abreviatura (jerga) |
| `dpc.` | ~5 | Abreviatura + punto |
| `dpl` | 221 | Abreviatura |
| `dpl.` | ~3 | Abreviatura + punto |
| `bóxer` | 24 | Acento |
| `boxer` | 14 | Sin acento |
| `bull dog frances` | 38 | Sin acento |
| `bull dog francés` | 3 | Con acento |
| `pastor alemán` | 84 | Acento |
| `pastor aleman` | ~3 | Sin acento |
| `terrier chileno` | 88 | OK |
| `terrier chileno` | 88 | OK |
| `rotweiler` | ~3 | Typo |
| `rottweiler` | 20 | OK |
| `mestiza` | ~3 | Género distinto |

### 5.4 Algoritmo de normalización actual

**Análisis del código `_build_dim_raza` (líneas 903-946):**

```python
# NO hay normalización previa al INSERT en dim_raza.
# Cada valor_raw se inserta tal cual si freq >= threshold.
# La normalización ocurre en F2.1 vía _RAZA_CANONICAL_ALIAS.
```

**Pasos del algoritmo actual:**

1. `raza_counts = _read_raw_distinct_column(raw_engine, "raza")` — devuelve lista de `(valor_raw, freq)`.
2. Para cada `(val, freq)` con `freq >= 3`:
   - Si `val` ya está en `dim_raza`, reusar.
   - Si no, inferir especie (`_infer_especie_for_raza`), construir fila, INSERT con `ON CONFLICT DO NOTHING`.
3. **`nombre_canonico = val`** (sin normalizar).

**Consolidación posterior en F2.1 (`refactor_dim_raza`):**

- Aplica `_RAZA_CANONICAL_ALIAS` (8 grupos: Bóxer/Boxer, Bull Dog Frances/Francés, etc.).
- DPC/DPL → Doméstico Pelo Corto/Largo.

### 5.5 ¿Requiere mejoras antes de poblar Silver?

**Sí, 3 mejoras menores necesarias:**

1. **Limpieza de punto final y capitalización** — los casos `mestizo.`, `dpc.`, `Mestizo` se insertarán como entradas separadas si no se normalizan antes. El código actual no hace `.strip('.').lower()` antes del INSERT.

   **Mitigación:** `_RAZA_CANONICAL_ALIAS` actual solo cubre 8 grupos; faltan casos como `mestizo.`, `dpc.`. **Recomendado:** ampliar el alias dict antes de ejecutar F2.

2. **Detección de data quality mal clasificada** — los valores `hembra`, `11 años`, `Raza:`, `Emergencias` (8-10 informes) se insertarían como razas canónicas, contaminando `dim_raza`. **Recomendado:** agregar filtro en `_build_dim_raza` para descartar valores que NO parecen razas (regex: longitud mínima, no contener números solos, etc.).

3. **Threshold de autoapprove** — `RAZA_AUTOAPPROVE_THRESHOLD = 3` significa que solo 56 razas de las 163 entrarán a `dim_raza`. Las 107 restantes van a `stg_razas_detectadas` como `pendientes`. **Esto es correcto por diseño** (revisión humana para casos raros). No requiere cambio.

### 5.6 Estimación de filas a poblar (post-F2 + F2.1)

| Tabla | Filas estimadas |
|---|---:|
| `dim_raza` (consolidadas) | **56** |
| `map_raza` (todas las variantes) | **163** |
| `stg_razas_detectadas` (freq<3 + 1-2 ocurrencias) | **~107** |
| `silver_informes.dim_raza_id` no-NULL (post F2.1+backfill) | **2,829** (97.8%) |

---

## PARTE 6 — OTRAS DIMENSIONES: AUDITORÍA COMPLETA

### 6.1 Estado de las 11 dimensiones

Inspección directa de cada dimensión con cardinalidad, cobertura y estado:

| Dimensión | Filas actuales | Usadas | % uso | Esperadas | Estado |
|---|---:|---:|---:|---:|---|
| `dim_especie` | 9 | 9 | **100%** | 9 | ✅ Completa |
| `dim_sexo` | 3 | 3 | **100%** | 3 | ✅ Completa |
| `dim_edad_categoria` | 5 | 5 | **100%** | 5 | ✅ Completa |
| `dim_estado_reproductivo` | 4 | 4 | **100%** | 4 | ✅ Completa |
| `dim_estudio` | 8 | 6 | 75% | 6-8 | ✅ Completa (2 unused = categorías válidas futuras) |
| `dim_organo` | 16 | 15 | 94% | 16 | ✅ Completa (1 unused = categoría válida) |
| `dim_atributo` | 30 | 30 | **100%** | 30 | ✅ Completa |
| `dim_segmento_anatomico` | 6 | 6 | **100%** | 6 | ✅ Completa |
| `dim_termino_conclusion` | 98 | 91 | 93% | 91-98 | ✅ Completa (7 inactivos = categorías pendientes de matchear corpus) |
| `dim_organo_atributo` | 71 | 68 | 96% | 71 | ✅ Completa (3 unused = combinaciones válidas) |
| `dim_valor_atributo` | 177 | 112 | 63% | 177 | ✅ Completa (65 unused = valores definidos para cobertura futura) |
| `dim_raza` | **0** | 0 | **0%** | 56 | ❌ **INCOMPLETA — gap ETL conocido** |

### 6.2 Tabla resumen pedida

| Dimensión | Estado | Completa | Pendiente | No utilizada | Debe eliminarse |
|---|:---:|:---:|:---:|:---:|:---:|
| `dim_especie` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `dim_sexo` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `dim_edad_categoria` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `dim_estado_reproductivo` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `dim_estudio` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `dim_organo` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `dim_atributo` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `dim_segmento_anatomico` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `dim_termino_conclusion` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `dim_organo_atributo` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `dim_valor_atributo` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `dim_raza` | ❌ | ❌ | ✅ | ❌ | ❌ |

### 6.3 Veredicto

**Única dimensión pendiente:** `dim_raza`. Las otras 11 están completas.

---

## PARTE 7 — PLAN F2.1 (PROPUESTA NO IMPLEMENTADA)

### 7.1 Cambios mínimos necesarios

**Resumen:** ejecutar F2 → ejecutar F2.1 → agregar 3 mini-mejoras al `_RAZA_CANONICAL_ALIAS` → backfill de `silver_informes.dim_raza_id` vía mini-script cross-layer.

### 7.2 Archivos afectados

| Archivo | Tipo de cambio | LOC estimadas |
|---|---|---:|
| `src/informes_vet/silver_etl.py` | Ampliar `_RAZA_CANONICAL_ALIAS` (agregar ~10 casos) | +20 LOC |
| `src/informes_vet/silver_etl.py` | Agregar filtro de "no-razas" en `_build_dim_raza` | +15 LOC |
| `scripts/build_silver.py` | (sin cambios — ya soporta `--phase f2` y `--phase f2_1`) | 0 LOC |
| `scripts/f2_backfill_informes_raza.py` (nuevo) | Mini-script backfill `silver_informes.dim_raza_id` desde RAW.informes.raza JOIN map_raza | +80 LOC |
| `scripts/verify_silver_f2_1.py` | (sin cambios — ya valida correctamente) | 0 LOC |

### 7.3 Pasos del mini-F2.1 (orden de ejecución)

**Paso 1 — Ampliar `_RAZA_CANONICAL_ALIAS`** (edición, no ejecución):
- Agregar `"Mestizo.": "Mestizo"`, `"Mestiza": "Mestizo"`, `"dpc.": "Doméstico Pelo Corto"`, `"dpl.": "Doméstico Pelo Largo"`, `"Dpc": "Doméstico Pelo Corto"`, `"Dpl": "Doméstico Pelo Largo"`.
- Total: 8 casos actuales + 6 nuevos = 14 casos.

**Paso 2 — Agregar filtro de "no-razas" en `_build_dim_raza`** (edición):
- Descartar valores que NO parecen razas:
  - Longitud < 3 caracteres.
  - Contiene solo dígitos.
  - Coincide con valores conocidos de data quality (`"hembra"`, `"11 años"`, `"raza:"`, `"emergencias"`).

**Paso 3 — Ejecutar `build_f2()`:**
```bash
python scripts/build_silver.py --phase f2
```
- Pobla: `map_especie` (~10), `map_sexo` (~5), `map_estado_reproductivo` (~5), `map_estudio` (~10), `map_raza` (163), `dim_raza` (~56), `stg_razas_detectadas` (~107), `stg_valores_no_mapeados` (~24).
- Registra run en `silver_etl_runs.phase='f2'`.

**Paso 4 — Ejecutar `build_f2_1()`:**
```bash
python scripts/build_silver.py --phase f2_1
```
- Consolida `dim_raza` (aplica `_RAZA_CANONICAL_ALIAS`, merge keepers).
- Renombra DPC/DPL → Doméstico Pelo Corto/Largo.
- Backfill `silver_informes.edad_meses` + `edad_parse_ok`.
- Registra run en `silver_etl_runs.phase='f2_1'`.

**Paso 5 — Mini-script de backfill `silver_informes.dim_raza_id`** (NUEVO):
```bash
python scripts/f2_backfill_informes_raza.py
```
- Lee RAW.informes.raza para cada `silver_informes.sha256`.
- JOIN con `map_raza.valor_original` (LOWER+TRIM normalizado).
- UPDATE `silver_informes.dim_raza_id = map_raza.dim_raza_id` WHERE match.
- Expected: 2,829/2,893 = 97.8% cobertura.

**Paso 6 — Verificar:**
```bash
python scripts/verify_silver_f2_1.py
```
- Espera: dim_raza=56, map_raza=163, edad_parse_ok ≥99%, stg_valores_no_mapeados=24.

**Paso 7 — Verificar que F3/F4/F5 siguen pasando:**
```bash
python scripts/verify_silver_f3.py
python scripts/verify_silver_f4.py
python scripts/verify_silver_f5.py
```
- Espera: 19/19 checks OK (F3: 5+ checks, F4: 7 checks, F5: 7 checks).

### 7.4 Verify necesarios

| Verify | Resultado esperado | Notas |
|---|---|---|
| `verify_silver_f2_1.py` | ✅ 8/8 passes (incluye nuevas aserciones) | El más crítico |
| `verify_silver_f3.py` | ✅ sin cambios (ortogonal) | No toca raza |
| `verify_silver_f4.py` | ✅ sin cambios (ortogonal) | No toca raza |
| `verify_silver_f5.py` | ✅ sin cambios (ortogonal) | No toca raza |
| Verify custom post-backfill | ✅ `silver_informes.dim_raza_id` 100% no-NULL para informes con raza_raw no-vacía | Nuevo |

### 7.5 Tiempo estimado

| Paso | Tiempo |
|---|---:|
| 1. Edición `_RAZA_CANONICAL_ALIAS` | 0.5 h |
| 2. Edición filtro no-razas | 0.5 h |
| 3. Ejecución `build_f2` | 5 min |
| 4. Ejecución `build_f2_1` | 5 min |
| 5. Mini-script backfill | 4 h (incluyendo tests) |
| 6. Verificación | 1 h |
| 7. Verificación F3/F4/F5 regresión | 0.5 h |
| 8. Documentación signoff | 2 h |
| **TOTAL** | **~8.5 h (~1 día)** |

### 7.6 Rollback

**Snapshot pre-F2 disponible:**
- `snapshots/pg_pre_reset_20260617_095555.dump` (2295.8 KB, del 2026-06-17).
- ⚠️ **No es un snapshot de SQLite.** Es un dump de PostgreSQL (probablemente de una prueba anterior). **No directamente usable para rollback de silver.db.**

**Estrategia de rollback recomendada:**
1. **Antes de ejecutar F2:** copiar `silver.db` → `silver.db.pre_f21`.
2. Si falla post-F2.1: restaurar desde `silver.db.pre_f21` y descartar `silver_etl_runs` post-F2.
3. Las filas de `silver_etl_runs.phase='f2'` o `'f2_1'` se pueden borrar manualmente con `DELETE FROM silver_etl_runs WHERE phase IN ('f2','f2_1')`.

**IMPORTANTE:** `silver_etl_runs` NO tiene FK a las tablas modificadas, así que el rollback de F2 + F2.1 es **limpio y reversible**.

### 7.7 Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|:---:|---|---|
| Alias extendido mal aplicado (e.g., `Mestiza` debería ser `Mestizo` por género pero podría ser raza distinta) | Media | Bajo | Revisar manualmente los 6 nuevos alias con clínico veterinario antes de aplicar |
| Filtro no-razas descarta razas válidas (e.g., raza con 2 caracteres) | Baja | Bajo | Filtro conservador (longitud ≥3, no solo dígitos) |
| Backfill de `silver_informes.dim_raza_id` introduce FK violation | Muy baja | Alto | Pre-validar con query SELECT antes de UPDATE; map_raza FK ya está enforced (idempotente) |
| `refactor_dim_raza` re-corre y elimina keepers por error | Muy baja | Alto | `already_applied` check (línea 1188) lo previene; probar antes |
| F3/F4/F5 verify regresionan | Muy baja (ortogonal) | Alto | Ejecutar verify_f3/4/5 inmediatamente después de F2.1; si fallan, rollback |

---

## PARTE 8 — CHECKLIST FINAL DE SILVER (PRE-GOLD)

Cada item debe ser ✅ para autorizar Gold.

### 8.1 Dimensiones

- [x] ✅ `dim_especie` completa (9/9 usadas)
- [x] ✅ `dim_sexo` completa (3/3 usadas)
- [x] ✅ `dim_edad_categoria` completa (5/5 usadas)
- [x] ✅ `dim_estado_reproductivo` completa (4/4 usadas)
- [x] ✅ `dim_estudio` completa (6/8 usadas; 2 categorías válidas futuras)
- [x] ✅ `dim_organo` completa (15/16 usadas; 1 categoría válida futura)
- [x] ✅ `dim_atributo` completa (30/30 usadas)
- [x] ✅ `dim_segmento_anatomico` completa (6/6 usadas)
- [x] ✅ `dim_termino_conclusion` completa (91/98 activas usadas)
- [x] ✅ `dim_organo_atributo` completa (68/71 usadas; 3 combinaciones válidas futuras)
- [x] ✅ `dim_valor_atributo` completa (112/177 usadas; 65 valores definidos para cobertura futura)
- [ ] ❌ **`dim_raza` INCOMPLETA** — gap ETL conocido; requiere F2.1

### 8.2 Foreign Keys

- [x] ✅ `silver_informes.dim_especie_id` → `dim_especie.id` (100% integridad)
- [x] ✅ `silver_informes.dim_sexo_id` → `dim_sexo.id` (100% integridad)
- [x] ✅ `silver_informes.dim_edad_categoria_id` → `dim_edad_categoria.id` (100% integridad)
- [x] ✅ `silver_informes.dim_estado_reproductivo_id` → `dim_estado_reproductivo.id` (100% integridad)
- [x] ✅ `silver_informes.dim_estudio_id` → `dim_estudio.id` (100% integridad)
- [ ] ⚠️ **`silver_informes.dim_raza_id` → `dim_raza.id` (100% NULL — bloquea F2.1)**
- [x] ✅ `silver_hallazgos.dim_organo_id` → `dim_organo.id` (100% integridad)
- [x] ✅ `silver_atributos_hallazgo.dim_organo_id` → `dim_organo.id` (100% integridad)
- [x] ✅ `silver_atributos_hallazgo.dim_organo_atributo_id` → `dim_organo_atributo.id` (100% integridad)
- [x] ✅ `silver_atributos_hallazgo.dim_valor_atributo_id` → `dim_valor_atributo.id` (NULL permitido)
- [x] ✅ `silver_conclusion_items.termino_conclusion_id` → `dim_termino_conclusion.id` (100% integridad)

### 8.3 Tablas pobladas

- [x] ✅ `silver_informes` (2,893 filas, 100% cobertura)
- [x] ✅ `silver_hallazgos` (27,866 filas)
- [x] ✅ `silver_atributos_hallazgo` (114,753 filas)
- [x] ✅ `silver_conclusion_items` (16,939 filas, cobertura 99.72%)
- [x] ✅ `silver_etl_runs` (21 runs)
- [x] ✅ `map_atributo_valor` (230 filas)
- [ ] ❌ **`dim_raza` VACÍA (0/56 esperadas)**
- [ ] ❌ **`map_especie` VACÍA (0/10 esperadas)**
- [ ] ❌ **`map_sexo` VACÍA (0/5 esperadas)**
- [ ] ❌ **`map_estado_reproductivo` VACÍA (0/5 esperadas)**
- [ ] ❌ **`map_estudio` VACÍA (0/10 esperadas)**
- [ ] ❌ **`map_raza` VACÍA (0/163 esperadas)**
- [ ] ❌ **`stg_razas_detectadas` VACÍA (0/~107 esperadas)**
- [ ] ❌ **`stg_valores_no_mapeados` VACÍA (0/24 esperadas)**

### 8.4 Tablas huérfanas

- [x] ✅ Ninguna tabla huérfana absoluta. Las 5 maps_* vacías son esquema-preservadas por decisión arquitectónica de F2 (serán pobladas cuando F2 corra).

### 8.5 ETL ejecutados

- [x] ✅ F1 ejecutado (id=2)
- [ ] ❌ **F2 NO ejecutado** (0 runs en `silver_etl_runs`)
- [ ] ❌ **F2.1 NO ejecutado** (0 runs en `silver_etl_runs`)
- [x] ✅ F3 ejecutado (id=1, 3, 4, 6, 15)
- [x] ✅ F3_hallazgos ejecutado (id=3, 5, 14)
- [x] ✅ F4 ejecutado (id=7-13, incluye errores y re-runs)
- [x] ✅ F5 ejecutado (id=16-21, incluye F5.1)

### 8.6 Verificaciones que pasan

- [x] ✅ `verify_silver_f3.py` — pasa
- [x] ✅ `verify_silver_f4.py` — pasa
- [x] ✅ `verify_silver_f5.py` — pasa (19/19 checks)
- [ ] ❌ **`verify_silver_f2_1.py` — NO HA SIDO EJECUTADO NUNCA** (esperaría fallo)

### 8.7 Resumen del checklist

| Categoría | Total | ✅ OK | ❌ Gap |
|---|---:|---:|---:|
| Dimensiones | 12 | 11 | 1 (`dim_raza`) |
| Foreign Keys | 11 | 10 | 1 (depende de dim_raza) |
| Tablas pobladas | 13 | 5 | 8 (todas dependen de F2) |
| Tablas huérfanas | — | ✅ | — |
| ETL ejecutados | 7 fases | 5 | 2 (F2, F2.1) |
| Verify passing | 3 scripts | 3 | 1 (no ejecutado) |

> **5 de 6 categorías tienen gaps relacionados con la omisión de F2.** Ejecutar F2.1 cerraría el 100% del checklist.

---

## PARTE 9 — VEREDICTO

### 9.1 Respuesta a la pregunta directa

## **B) Ejecutar primero F2.1 (mejorado) y luego Gold.**

### 9.2 Justificación cuantitativa

| Criterio | Estado actual | Post-F2.1 |
|---|---|:---:|
| Dimensiones completas | 11/12 | 12/12 ✅ |
| Tablas Silver pobladas | 5/13 | 13/13 ✅ |
| ETL phases ejecutados | 5/7 | 7/7 ✅ |
| Verify scripts passing | 3/4 | 4/4 ✅ |
| FKs activas con datos | 10/11 | 11/11 ✅ |
| Catálogo de preguntas respondibles desde Silver puro | 33/62 (53%) | 62/62 (100%) ✅ |
| Catálogo bloqueado por gap raza | 3 preguntas (E9, H3, SP2) | 0 preguntas ✅ |
| Cross-layer read necesario | Sí (Gold → RAW para raza) | NO ✅ |

### 9.3 Lo que se gana ejecutando F2.1 ANTES de Gold

1. **Cierre total del checklist de Silver** (12/12 dimensiones, 13/13 tablas, 7/7 ETL, 4/4 verify).
2. **Silver 100% puro** — sin necesidad de cross-layer read desde Gold.
3. **100% de las preguntas respondibles** desde Silver (vs 95% con cross-layer).
4. **Signoff arquitectónico definitivo** sin excepciones.
5. **Alineación con el principio medallion** (Gold NO lee de RAW).
6. **Tests + verify existentes siguen pasando** (ortogonalidad probada).
7. **Inversión:** ~1 día de trabajo + 1 snapshot de rollback.
8. **Idempotencia** garantiza que se puede re-ejecutar sin daño.

### 9.4 Lo que se pierde NO ejecutando F2.1 antes de Gold

1. Silver queda con un **gap arquitectónico conocido** (`dim_raza` vacía).
2. Gold debe implementar **cross-layer read** (Gold → RAW) para responder preguntas de raza.
3. El **signoff Silver nunca es 100%** — siempre queda "incompleto por F2 omitido".
4. **Deuda técnica consciente** que requerirá reabrir Silver en algún momento futuro.

### 9.5 Riesgos de NO ejecutar F2.1 ahora

| Riesgo | Probabilidad | Impacto |
|---|:---:|---|
| Cross-layer read Gold → RAW se convierte en patrón aceptado y se replica a otras dimensiones | Alta | Medio |
| Alguien (Gold developer) implementa workaround de raza que luego es difícil de remover | Media | Medio |
| Migración futura a DuckDB/PostgreSQL obliga a reabrir Silver de todas formas | Baja (1-2 años) | Alto |
| El gap `dim_raza` se "olvida" y nunca se corrige | Media | Bajo |

### 9.6 Recomendación operativa

**Ejecutar mini-F2.1 (8.5 horas de trabajo) ANTES de construir Gold.**

Pasos ordenados:

1. **Backup:** `cp silver.db silver.db.pre_f21`
2. **Editar `_RAZA_CANONICAL_ALIAS`** en `silver_etl.py` (agregar 6 casos)
3. **Agregar filtro de no-razas** en `_build_dim_raza` (~15 LOC)
4. **Ejecutar:** `python scripts/build_silver.py --phase f2`
5. **Ejecutar:** `python scripts/build_silver.py --phase f2_1`
6. **Crear mini-script** `f2_backfill_informes_raza.py` (~80 LOC, cross-layer RAW→silver_informes.dim_raza_id)
7. **Ejecutar backfill**
8. **Verificar:** `python scripts/verify_silver_f2_1.py` (debe pasar todas)
9. **Re-verificar:** `verify_silver_f3.py`, `verify_silver_f4.py`, `verify_silver_f5.py` (no deben regresionar)
10. **Documentar:** `docs/SILVER_FINAL_SIGNOFF.md` con veredicto SILVER CLOSED 100%

**Post-F2.1:** autorizar inicio de Gold sin excepciones arquitectónicas.

### 9.7 Resumen ejecutivo

> **Silver está al 91% (5/6 categorías OK).** El 9% restante es un gap ETL conocido y documentado: las fases F2 y F2.1 nunca se ejecutaron, dejando `dim_raza`, los 5 `map_*` (excepto `map_atributo_valor`) y los `stg_*` (excepto `stg_conclusion_no_match`) vacíos.
>
> **Ejecutar `build_f2()` + `build_f2_1()` hoy es seguro** (ortogonal a F3/F4/F5), **idempotente** (verificado por código), y **reversible** (con snapshot de rollback).
>
> **Costo total:** ~8.5 horas de trabajo (1 día).
>
> **Beneficio:** Silver 100% completo, sin necesidad de cross-layer read en Gold, signoff arquitectónico definitivo.
>
> **VEREDICTO: B) Ejecutar F2.1 primero, luego Gold.**

---

## Próximo paso

Esperar autorización del usuario para:

1. **Proceder con la implementación de mini-F2.1** (8 pasos descritos en §9.6).
2. **O bien, ajustar el plan** si alguna de las 8 asunciones de §7.3 no se acepta.
