# Auditoría Funcional de Gold

**Fecha:** 2026-06-26
**Estado de Gold:** construido, poblado, verificado (27/27 PASS).
**Objetivo:** demostrar que Gold responde los casos de uso reales del proyecto.

---

## Parte 1. Auditoría del modelo

### 1.1 `gold_diagnosticos`

| Atributo | Valor |
|---|---|
| **Propósito** | Tabla principal de análisis de hallazgos de conclusión. Denormaliza cada `silver_conclusion_items` con su término canónico, modificadores y dimensiones temporales. |
| **Granularidad** | 1 fila por `conclusion_item` (un item de conclusión extraído del texto). |
| **PK** | `conclusion_item_id INTEGER` (1:1 con silver_conclusion_items.id). |
| **Cardinalidad** | 16.120 filas (= items con `fecha_parseada IS NOT NULL`). |
| **Origen Silver** | `silver_conclusion_items` JOIN `silver.dim_termino_conclusion` JOIN `silver.silver_informes`. |
| **Limitaciones** | (a) Solo entran items cuyo informe tiene fecha parseada: **819 items (4.83%) se pierden**. (b) `organo_asociado` siempre NULL porque Silver tampoco lo popula. |

| Columna | Tipo | Notas |
|---|---|---|
| `conclusion_item_id` | INTEGER PK | ID estable del item en silver. |
| `informe_id` | INTEGER NN | FK lógica a `gold_demografia.informe_id`. |
| `termino_canonico` | VARCHAR(64) NN | "nefropatia", "hepatomegalia", etc. |
| `tipo_item` | VARCHAR(16) NN | DIAGNOSTICO / ETIOLOGIA / NEGATIVO. |
| `categoria_clinica` | VARCHAR(32) | HEPATICA, RENAL, GASTROINTESTINAL, etc. |
| `organo_asociado` | VARCHAR(32) | **0% poblado** (limitación heredada de Silver). |
| `lateralidad` | VARCHAR(16) | bilateral / izquierdo / derecho / etc. |
| `modificador_cualidad` | VARCHAR(32) | severo, leve, focal, difuso, etc. |
| `modificador_distribucion` | VARCHAR(32) | multifocal, regional, etc. |
| `negado` | BOOLEAN NN | TRUE si el término está precedido de negación. |
| `confianza` | REAL | **Constante 1.0** en silver — columna inútil en la práctica. |
| `anio`, `mes` | INTEGER NN | Derivados de `silver_informes.fecha_parseada`. |
| `es_primario_en_informe` | BOOLEAN NN | 1 si es el primer item por pos_inicio en la conclusión. |
| `gold_built_at` | DATETIME | Auditoría. |

---

### 1.2 `gold_demografia`

| Atributo | Valor |
|---|---|
| **Propósito** | Tabla de hechos del informe: paciente, contexto temporal, conteos agregados. Es la "dimensión maestra" para análisis. |
| **Granularidad** | 1 fila por informe. |
| **PK** | `informe_id INTEGER` (1:1 con silver_informes.informe_id). |
| **Cardinalidad** | 2.759 filas (= silver_informes con fecha). |
| **Origen Silver** | `silver_informes` JOIN dims + LEFT JOIN `raw.informes` (para `raza_raw`) + 5 subqueries de agregación (n_hallazgos, n_atributos, n_items_por_tipo). |
| **Limitaciones** | (a) Falta `doctor_solicitante` (existe en Silver pero no se promovió a Gold). (b) `tutor` no es buen identificador. |

| Columna | Tipo | Notas |
|---|---|---|
| `informe_id` | INTEGER PK | |
| `fecha`, `anio`, `mes`, `trimestre` | DATE / INT | Derivados de `fecha_parseada`. |
| `especie_nombre` | VARCHAR(64) NN | Canino, Felino, Conejo, etc. |
| `sexo_nombre` | VARCHAR(32) | Hembra / Macho / Indeterminado. |
| `edad_categoria_nombre` | VARCHAR(32) | Cachorro / Juvenil / Adulto / Maduro / Geriátrico. |
| `estudio_nombre` | VARCHAR(64) | Abdominal, Gestacional, etc. |
| `estado_reproductivo_nombre` | VARCHAR(32) | Entero, Castrado, OVH — **94% "No especificado"**. |
| `raza_raw` | VARCHAR(255) | **Texto crudo** desde raw.informes.raza (159 variantes distintas, 79 con freq=1). |
| `nombre_paciente` | VARCHAR(255) | 1.439 pacientes distintos sobre 2.759 informes. |
| `tutor` | VARCHAR(255) | 2.241 tutores distintos. |
| `n_hallazgos`, `n_atributos_extraidos`, `n_items_*` | INTEGER | Conteos pre-agregados por informe. |
| `gold_built_at` | DATETIME | Auditoría. |

---

### 1.3 `gold_hallazgos`

| Atributo | Valor |
|---|---|
| **Propósito** | Tabla de hechos granular para análisis de atributos extraídos (forma, tamaño, ecogenicidad, etc.). |
| **Granularidad** | 1 fila por atributo-hallazgo (= silver_atributos_hallazgo.id). |
| **PK** | `atributo_hallazgo_id INTEGER`. |
| **Cardinalidad** | 114.753 filas (1:1 con silver_atributos_hallazgo). |
| **Origen Silver** | `silver_atributos_hallazgo` JOIN dim_organo + dim_atributo + dim_organo_atributo + dim_valor_atributo + dim_segmento_anatomico + silver_hallazgos. |
| **Limitaciones** | (a) `valor_numerico` 0.09% poblado (105 filas). (b) `unidad` 0% poblado. Ambos heredados de Silver. |

| Columna | Tipo | Notas |
|---|---|---|
| `atributo_hallazgo_id` | INTEGER PK | |
| `informe_id`, `hallazgo_id` | INTEGER NN | Lógica → gold_demografia / silver_hallazgos. |
| `organo_nombre`, `sistema` | VARCHAR NN | Riñones, Hígado, Bazo, etc. + urinario/digestivo/etc. |
| `atributo_nombre` | VARCHAR(64) NN | forma, tamaño, ecogenicidad, grosor_pared, etc. |
| `valor_nombre` | VARCHAR(64) | Valor canónico desde dim_valor_atributo (puede ser NULL). |
| `valor_canonico` | VARCHAR(64) | Valor canónico desde silver (puede ser NULL). |
| `valor_numerico` | REAL | **Solo 0.09% poblado** — preguntas cuantitativas no respondibles. |
| `segmento_nombre` | VARCHAR(64) | Riñón izquierdo, Duodeno yeyuno, etc. |
| `lateralidad` | VARCHAR(16) | NULL para la mayoría. |
| `estado_hallazgo` | VARCHAR(16) NN | normal / anormal / no_evaluado (proxy de severidad). |
| `unidad` | VARCHAR(16) | **0% poblado** — heredado de Silver. |
| `gold_built_at` | DATETIME | Auditoría. |

---

### 1.4 `gold_coocurrencias` (VIEW)

| Atributo | Valor |
|---|---|
| **Propósito** | Pares de diagnósticos que coocurren en el mismo informe. Solo DIAGNOSTICO+DIAGNOSTICO (no ETIOLOGIA con DIAGNOSTICO). |
| **Granularidad** | 1 fila por par `(termino_a, termino_b)` que aparece ≥1 vez en algún informe. |
| **Cardinalidad** | 1.520 filas (de 2.556 pares posibles entre 72 términos). |
| **Limitaciones** | Solo cuenta pares efectivamente coocurrentes. 1.036 pares teóricos nunca coocurren y no aparecen. |

Columnas: `termino_a_nombre`, `termino_b_nombre`, `n_coocurrencias`, `soporte` (proporción).

---

### 1.5 `gold_tendencias` (VIEW)

| Atributo | Valor |
|---|---|
| **Propósito** | Serie temporal mensual por especie y diagnóstico. Útil para "evolución de X por año/mes". |
| **Granularidad** | 1 fila por `(anio, mes, especie, termino_canonico)`. |
| **Cardinalidad** | 2.286 filas. |
| **Limitaciones** | Solo cuenta términos `tipo_item = 'DIAGNOSTICO'`. Excluye ETIOLOGIA y NEGATIVO. |

Columnas: `anio`, `mes`, `especie_nombre`, `termino_canonico`, `n_informes_con_termino`.

---

## Parte 2. Cobertura funcional

### Leyenda
- ✅ = respondible directamente con Gold (consulta verificada)
- ⚠️ = respondible con workaround (heurística o filtrado manual)
- ❌ = NO respondible (campo no existe en Gold)

### Demografía

| Pregunta | Estado | Cómo |
|---|:---:|---|
| Pacientes por especie | ✅ | `SELECT especie_nombre, COUNT(DISTINCT informe_id) FROM gold_demografia GROUP BY 1` |
| Pacientes por sexo | ✅ | `sexo_nombre` |
| Pacientes por edad | ✅ | `edad_categoria_nombre` (5 categorías) |
| Pacientes por raza | ⚠️ | `raza_raw` tiene 159 variantes (79 con freq=1). Análisis agregados funcionan; análisis finos requieren normalización manual |
| Pacientes por clínica | ❌ | **No existe `clinica` en Gold, Silver ni RAW**. El proyecto es single-clinic por diseño |
| Pacientes por veterinario | ❌ | **No existe `veterinario` en Gold**. Existe `silver_informes.doctor_solicitante` (439 doctores distintos, 88% poblado). No se promovió a Gold |
| Distribución mensual | ✅ | `anio, mes` en gold_demografia |
| Distribución anual | ✅ | `anio` |

### Diagnósticos

| Pregunta | Estado | Cómo |
|---|:---:|---|
| Diagnósticos más frecuentes | ✅ | `SELECT termino_canonico, COUNT(*) FROM gold_diagnosticos WHERE tipo_item='DIAGNOSTICO' GROUP BY 1 ORDER BY 2 DESC` |
| Diagnósticos por especie | ✅ | JOIN con gold_demografia |
| Diagnósticos por raza | ⚠️ | JOIN con gold_demografia.raza_raw (con caveat de calidad) |
| Diagnósticos por clínica | ❌ | No existe |
| Diagnósticos por veterinario | ❌ | No existe en Gold |
| Diagnósticos por año | ✅ | `anio` |
| Diagnósticos por mes | ✅ | `mes` |
| Evolución temporal | ✅ | VIEW `gold_tendencias` (2.286 filas, granularidad mensual) |

### Hallazgos

| Pregunta | Estado | Cómo |
|---|:---:|---|
| Hallazgos más frecuentes | ✅ | `SELECT atributo_nombre, COUNT(*) FROM gold_hallazgos GROUP BY 1` |
| Hallazgos por órgano | ✅ | `organo_nombre` (15 órganos) |
| Hallazgos por especie | ✅ | JOIN con gold_demografia |
| Hallazgos por diagnóstico | ✅ | JOIN gold_hallazgos ↔ gold_diagnosticos por `informe_id` (no FK física, pero joinable) |
| Atributos más frecuentes | ✅ | 30 atributos, ej. "forma" 10.786, "contenido" 10.614 |
| Valores más frecuentes | ✅ | `valor_canonico` (ej. NORMAL 20.919, CONSERVADO 11.835) |
| Distribución de severidad | ⚠️ | `estado_hallazgo` distingue normal/anormal/no_evaluado, no severidad clínica fina |

### Relaciones

| Pregunta | Estado | Cómo |
|---|:---:|---|
| Coocurrencia de diagnósticos | ✅ | VIEW `gold_coorrtencias` (1.520 pares DIAGNOSTICO+DIAGNOSTICO) |
| Diagnóstico ↔ hallazgo | ✅ | JOIN por `informe_id` (gold_diagnosticos ↔ gold_hallazgos) |
| Órgano ↔ diagnóstico | ✅ | JOIN por `informe_id` (gold_hallazgos.organo_nombre ↔ gold_diagnosticos.termino_canonico) |
| Órgano ↔ especie | ✅ | JOIN gold_hallazgos ↔ gold_demografia |
| Órgano ↔ raza | ⚠️ | JOIN gold_hallazgos ↔ gold_demografia.raza_raw (con caveat de calidad) |

**Resumen de cobertura:** 22 ✅ + 4 ⚠️ + 5 ❌ sobre 31 preguntas.

Los 5 ❌ se reducen en realidad a **2 dimensiones faltantes**: `clinica` (no aplica, single-clinic) y `veterinario` (existe en Silver, falta en Gold).

---

## Parte 3. Power BI — Modelo relacional

### 3.1 Relaciones

```
gold_diagnosticos  ──[informe_id]──→  gold_demografia  ←──[informe_id]──  gold_hallazgos
        (N)                              (1)                              (N)
```

| Origen | Destino | Cardinalidad | Dirección filtro |
|---|---|---|---|
| `gold_diagnosticos[informe_id]` | `gold_demografia[informe_id]` | N : 1 | Single (gold_demografia → gold_diagnosticos) |
| `gold_hallazgos[informe_id]` | `gold_demografia[informe_id]` | N : 1 | Single (gold_demografia → gold_hallazgos) |

**No hay relación gold_diagnosticos ↔ gold_hallazgos** vía informe_id directa (Power BI la infiere pero ambiguamente). Power BI a veces detecta transitividad: si Demografia está en el medio, filtra Diagnosticos via Hallazgos funciona. Si NO se quiere transitividad, se modela manualmente con `informe_id` como dimensión compartida.

### 3.2 Ambigüedades

- **informe_id** aparece como columna en las 3 tablas. Power BI puede interpretar la transitividad y crear relaciones indirectas. Recomendación: en Power BI, definir manualmente las 2 relaciones (diag→demo y hall→demo) con `cross-filter direction = single` y desactivar la detección automática.
- **gold_coocurrencias y gold_tendencias**: NO tienen FK a gold_diagnosticos (son agregaciones por nombre y por año/mes/especie). Se vinculan "lógicamente" por `termino_canonico` y `especie_nombre` (string match, no enforced). En Power BI son tablas independientes que se usan para visualizaciones dedicadas.
- **anio, mes**: aparecen en gold_diagnosticos Y gold_demografia. Power BI puede intentar crear una relación. Recomendación: NO crear esa relación (sería 1:1 dentro del mismo informe, no aporta).

### 3.3 Cardinalidades observadas

| Relación | n_left | n_right | Cardinalidad real |
|---|---:|---:|---|
| diag → demo | 16.120 | 2.759 | 5.8 : 1 (cada informe tiene ~5.8 items de conclusión) |
| hall → demo | 114.753 | 2.759 | 41.6 : 1 (cada informe tiene ~42 atributos-hallazgo) |

---

## Parte 4. Casos reales (queries verificadas)

### Caso 1. Diagnóstico hepático más frecuente en perros

```sql
SELECT termino_canonico, COUNT(*) AS n
FROM gold_diagnosticos gd
JOIN gold_demografia gdm ON gdm.informe_id = gd.informe_id
WHERE gdm.especie_nombre = 'Canino'
  AND gd.categoria_clinica = 'HEPATICA'
  AND gd.tipo_item = 'DIAGNOSTICO'
  AND gd.negado = 0
GROUP BY termino_canonico ORDER BY n DESC LIMIT 10;
```

| Término | n |
|---|---:|
| hepatomegalia | 695 |
| hepatopatia | 393 |
| hepatopatia_vacuolar | 352 |
| microhepatia | 84 |
| fibrosis | 14 |

### Caso 2. Razas con más esplenomegalia

```sql
SELECT gdm.raza_raw, COUNT(*) AS n
FROM gold_diagnosticos gd
JOIN gold_demografia gdm ON gdm.informe_id = gd.informe_id
WHERE gd.termino_canonico = 'esplenomegalia'
  AND gd.tipo_item = 'DIAGNOSTICO' AND gd.negado = 0
GROUP BY gdm.raza_raw ORDER BY n DESC LIMIT 10;
```

| Raza | n |
|---|---:|
| Mestizo | 61 |
| DPC | 51 |
| DPL | 23 |
| Pastor Alemán | 9 |
| Golden Retriever | 7 |

### Caso 3. Evolución de hepatopatía por año

```sql
SELECT anio, COUNT(DISTINCT informe_id) AS n_informes
FROM gold_diagnosticos
WHERE categoria_clinica = 'HEPATICA' AND tipo_item='DIAGNOSTICO' AND negado=0
GROUP BY anio ORDER BY anio;
```

| Año | n_informes |
|---:|---:|
| 2022 | 2 |
| 2023 | 204 |
| 2024 | 449 |
| 2025 | 415 |
| 2026 | 104 |

### Caso 4. Diagnósticos que coocurren con pancreatitis

```sql
SELECT
  CASE WHEN termino_a_nombre='pancreatitis' THEN termino_b_nombre
       ELSE termino_a_nombre END AS otro_termino,
  n_coocurrencias,
  ROUND(soporte*100, 2) AS soporte_pct
FROM gold_coocurrencias
WHERE 'pancreatitis' IN (termino_a_nombre, termino_b_nombre)
ORDER BY n_coocurrencias DESC LIMIT 10;
```

| Otro término | n | soporte |
|---|---:|---:|
| nefropatia | 162 | 5.89% |
| hepatomegalia | 145 | 5.27% |
| hepatopatia | 86 | 3.13% |
| gastritis | 65 | 2.36% |
| peritonitis | 55 | 2.00% |

### Caso 5. Órgano con más hallazgos + % anormales

```sql
SELECT organo_nombre, COUNT(*) AS n,
       SUM(CASE WHEN estado_hallazgo='anormal' THEN 1 ELSE 0 END) AS n_anormales
FROM gold_hallazgos GROUP BY organo_nombre ORDER BY n DESC;
```

| Órgano | total | anormales | % anormal |
|---|---:|---:|---:|
| Riñones | 32.491 | 17.272 | 53.2% |
| Adrenales | 14.333 | 860 | 6.0% |
| Hígado | 13.424 | 5.069 | 37.8% |
| Vejiga | 12.467 | 2.133 | 17.1% |
| Estómago | 10.360 | 2.520 | 24.3% |
| Páncreas | 2.616 | 275 | 10.5% |

### Caso 6. Distribución de edad en nefropatía

```sql
SELECT gdm.edad_categoria_nombre, COUNT(DISTINCT gd.informe_id) AS n_informes
FROM gold_diagnosticos gd
JOIN gold_demografia gdm ON gdm.informe_id = gd.informe_id
WHERE gd.termino_canonico='nefropatia' AND gd.tipo_item='DIAGNOSTICO' AND gd.negado=0
GROUP BY gdm.edad_categoria_nombre ORDER BY n_informes DESC;
```

| Edad | n |
|---|---:|
| Adulto | 636 |
| Geriátrico | 407 |
| Maduro | 355 |
| Juvenil | 77 |
| Cachorro | 33 |

**Conclusión:** las 6 preguntas de la Parte 4 se responden únicamente con Gold (más `gold_coocurrencias` para Caso 4). No se requiere acceso a Silver ni RAW.

---

## Parte 5. Auditoría crítica (problemas reales)

### Problema 1 — Falta `veterinario` (o `doctor_solicitante`) en Gold

- **Impacto:** ALTO. 3 preguntas explícitas del usuario ("diagnósticos por veterinario", "pacientes por veterinario") no son respondibles. Las demás preguntas pueden contestarse en Silver pero no desde Gold.
- **Probabilidad:** 100% (confirmado: columna no existe en Gold, sí existe en Silver con 88% poblado, 439 doctores distintos).
- **Solución:** agregar `veterinario_nombre` (denormalizado desde `silver_informes.doctor_solicitante`) a `gold_demografia`. Cambio de ~10 LOC en `models_gold.py` + `gold.py:build_gold_demografia()`. No requiere cambios en Silver.

### Problema 2 — `valor_numerico` y `unidad` 0% útiles en gold_hallazgos

- **Impacto:** ALTO para preguntas cuantitativas ("media de grosor de pared vesical", "distribución del tamaño renal"). NO afecta análisis categóricos (forma, ecogenicidad, etc.).
- **Probabilidad:** 100% (confirmado: `valor_numerico` 105/114.753 = 0.09%, `unidad` 0/114.753).
- **Origen:** Silver tampoco popula esos campos (inherited). Verificar si el extractor regex numérico en `silver_atributos_hallazgo` está extrayendo mal — **no es un problema de Gold**, es un problema de extracción en Silver.
- **Solución:** NO se puede arreglar en Gold sin reabrir Silver. Si la pregunta cuantitativa es bloqueante, abrir ticket sobre Silver. Para el MVP de Power BI (análisis categórico), no bloquea.

### Problema 3 — `organo_asociado` en gold_diagnosticos: 0% poblado

- **Impacto:** MEDIO. La columna existe pero está vacía. Las preguntas por órgano se responden vía `gold_hallazgos.organo_nombre` o `gold_diagnosticos.categoria_clinica`.
- **Probabilidad:** 100%.
- **Origen:** `silver.dim_termino_conclusion.organo_asociado` también está 0/98 poblado. La info de órgano está implícita en `categoria_clinica` (HEPATICA, RENAL, VESICULA, etc.).
- **Solución:** ninguna razonable sin reabrir Silver. La columna se mantiene en Gold como place-holder para una eventual promoción.

### Problema 4 — Calidad de `raza_raw`: 159 variantes, 79 con freq=1

- **Impacto:** MEDIO. Análisis por raza_top funciona; análisis por raza_específica tiene ruido (variantes ortográficas: "Bóxer"/"Boxer", "Yorkshire"/"Yorkshire Terrier").
- **Probabilidad:** 100%.
- **Origen:** texto crudo de raw. Silver tiene `map_raza` (163 entradas) y `dim_raza` (63 canónicas), pero Gold no las promovió.
- **Solución:** opcional, agregar `raza_canonica` (denormalizada desde `silver.dim_raza.nombre_canonico` via `silver_informes.dim_raza_id`). Cambio de ~5 LOC. **Recomendado solo si se valida que las preguntas por raza específica son recurrentes.**

### Problema 5 — `confianza` siempre = 1.0 (columna inútil)

- **Impacto:** BAJO. La columna existe pero es constante.
- **Probabilidad:** 100%.
- **Origen:** `silver_conclusion_items.confianza` se popula con valor fijo 1.0 (default del server). En Silver F5 no se calcula confianza real.
- **Solución:** eliminar la columna `confianza` de `gold_diagnosticos` y del INSERT. Limpieza menor, ~3 LOC. **NO urge.**

### Problema 6 — 819 conclusion_items sin fecha no llegan a Gold

- **Impacto:** BAJO (4.83% del total). Distorsiona análisis temporal en el margen.
- **Probabilidad:** 100%.
- **Origen:** `silver_informes.fecha_parseada IS NULL` (fechas no parseables).
- **Solución:** ninguna razonable sin reabrir Silver. Trade-off documentado en `build_gold_diagnosticos` (filtro `WHERE si.fecha_parseada IS NOT NULL`).

### Problema 7 — Cardinalidad de gold_coocurrencias real (1.520) vs estimada en doc (22.708)

- **Impacto:** BAJO (la cifra de la doc era estimación). Las 1.520 filas son los pares que efectivamente coocurren — la VIEW está bien implementada.
- **Probabilidad:** N/A (es un issue de documentación).
- **Solución:** actualizar el Anexo A de ARCHITECTURE_FINAL.md con la cifra real.

### Problema 8 — Posible "transitividad" en Power BI entre diag/hall/demo

- **Impacto:** BAJO. Power BI puede inferir relaciones transitivas que filtren doble.
- **Probabilidad:** MEDIA.
- **Solución:** documentar en README del Gold la regla de modelado: definir las 2 relaciones manualmente con cross-filter = single.

---

## Parte 6. Veredicto

### **A. Gold está listo para Power BI.**

**Resolución del Problema 1 (2026-06-26):** el usuario decidió **NO** implementar la dimensión de veterinario en Gold, reclasificándola como **mejora futura condicionada por un caso de uso real**.

**Justificación de la decisión:**

- El proyecto tiene una única ecografista (la misma persona firma todos los informes).
- El veterinario solicitante no forma parte de los análisis de negocio definidos para Power BI.
- No existe ningún dashboard, KPI o consulta que requiera segmentar información por veterinario solicitante.
- Agregar una columna únicamente para aumentar la cobertura teórica del modelo viola YAGNI.

**Triggers documentados para incorporación futura** (si aparece un requerimiento concreto):

- Analizar derivaciones por veterinario.
- Comparar diagnósticos por veterinario remitente.
- Generar indicadores comerciales o de fidelización.

Cuando se materialice cualquiera de estos triggers, la columna `veterinario_nombre` se promoverá a `gold_demografia` desde `silver_informes.doctor_solicitante` (~15 LOC). Hasta entonces, Gold permanece sin cambios.

**Problemas heredados de Silver que NO se tocan:**

- **Problema 2** (`valor_numerico`/`unidad` 0.09%/0% poblado): requiere reabrir Silver, fuera de scope.
- **Problema 3** (`organo_asociado` NULL): la info se cubre con `categoria_clinica` y `gold_hallazgos.organo_nombre`.
- **Problema 6** (819 items sin fecha): trade-off documentado, aceptable.

**Problemas de Gold que NO se tocan (no urge):**

- **Problema 4** (calidad `raza_raw`): se valida si las preguntas por raza específica se vuelven recurrentes.
- **Problema 5** (`confianza` constante): limpieza estética, no bloqueante.
- **Problema 7** (cardinalidad coocurrencias): issue de doc, no de código.
- **Problema 8** (transitividad Power BI): se documenta al modelar el .pbix.

**Restricciones respetadas:**

- Cero cambios en código Gold.
- Cero tablas nuevas.
- Cero columnas nuevas.
- Cero componentes nuevos.
- Cero rediseño arquitectónico.

**Próximo paso:** consumir Gold desde Power BI Desktop (ODBC SQLite → gold.db). La capa de modelado queda cerrada.

---

*Fin de la auditoría. Gold aprobado para Power BI el 2026-06-26.*