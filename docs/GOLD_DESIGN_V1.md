# Gold Design v1 — Diseño Conceptual de Capas Gold

> **Fecha:** 2026-06-25
> **Estado de Silver:** CERRADO (F1–F5.1, 19/19 checks OK)
> **Documentos relacionados:**
> - `docs/GOLD_READINESS_AUDIT.md` — Parte A (auditoría Silver) + Parte C (veredicto GO CON OBSERVACIONES)
> - `docs/GOLD_QUESTION_CATALOG.md` — Parte B.1 (62 preguntas) + Parte B.2 (matriz pregunta→datos)
> - `docs/GOLD_DESIGN_V1.md` — **ESTE DOCUMENTO** — Parte B.3 (capas) + B.4 (tamaño) + B.5 (priorización)
>
> **Restricción de diseño:**
> - Conceptual (sin SQL, sin DDL, sin código de implementación en este doc).
> - Datos reales del Silver ya cerrado (`silver.db`, 2,893 informes al 2026-06-24).
> - Raza queda **fuera del MVP** (ver A.6 / C.1 del audit).
> - Cross-layer read permitido solo desde Gold → RAW (no al revés).

---

## PARTE B.3 — PROPUESTA DE CAPAS GOLD

Gold se organiza como **5 dominios verticales** (cada uno materializa una o más tablas con un propósito analítico claro) + **1 capa de dimensiones compartidas** + **1 capa de linaje/calidad**. Ningún dominio depende de otro; todos leen exclusivamente de Silver (con la excepción documentada de `gold_informes`, que también lee de RAW para raza).

Diagrama lógico de capas:

```
+---------------------------------------------------------------+
| CAPA DE DOMINIOS GOLD (5)                                     |
|  gold_demografia   gold_diagnosticos   gold_hallazgos         |
|  gold_coocurrencias                  gold_tendencias          |
+---------------------------------------------------------------+
| CAPA DE DIMENSIONES COMPARTIDAS (3)                           |
|  gold_dim_tiempo  gold_dim_paciente  gold_dim_termino         |
+---------------------------------------------------------------+
| CAPA DE LINAJE Y CALIDAD (1)                                  |
|  gold_etl_runs / gold_calidad_extraccion                      |
+---------------------------------------------------------------+
                              |
                              v
        +------------------+ +----------------------+
        |   Silver (cerrado) | | RAW (solo raza)      |
        +------------------+ +----------------------+
```

---

### B.3.1 — `gold_demografia`

**Objetivo:** responder las preguntas de mezcla de población (especie, sexo, edad, estado reproductivo, tipo de estudio, raza via cross-layer) y servir como dimensión canónica de paciente/tiempo para el resto de Gold.

**Grano:** una fila por **`informe_id`** (denormalización plana — no por paciente). Decisión tomada porque la unidad mínima de análisis clínico es el estudio, no el animal; un paciente con 5 informes aporta 5 filas y eso preserva la trayectoria temporal.

**Medidas (métricas):**
- `n_hallazgos` (count de silver_hallazgos por informe)
- `n_hallazgos_normales`, `n_hallazgos_anormales`, `n_hallazgos_no_evaluados`
- `n_atributos_extraidos` (count de silver_atributos_hallazgo)
- `n_items_diagnostico`, `n_items_etiologia`, `n_items_negativo`
- `n_diagnosticos_unicos` (count distinct de término_conclusion_id categoría DIAGNOSTICO)
- `edad_meses`, `peso_kg` (copiados directos)

**Dimensiones (columnas de contexto):**
- `informe_id` (PK lógica)
- `anio`, `mes`, `trimestre` (columnas calculadas, NO dimensión — para evitar JOIN extra)
- `dim_especie_id` + `especie_nombre`
- `dim_sexo_id` + `sexo_nombre`
- `dim_edad_categoria_id` + `edad_categoria_nombre`
- `dim_estudio_id` + `estudio_nombre`
- `dim_estado_reproductivo_id` + `estado_reproductivo_nombre`
- `raza_raw` (string, **solo desde RAW** vía cross-layer read en build-time — denormalización controlada, sin crear FK porque `dim_raza` está vacía)
- `raza_normalizada` (string normalizada: minúsculas, sin acentos inconsistentes, primera letra mayúscula — aplicar TRIM + LOWER + REPLACE de variantes)
- `nombre_paciente`, `tutor` (para clustering posterior)

**Justificación del grano:** un Gold por informe, no por paciente, preserva todas las trayectorias. El paciente se deriva con un SELECT DISTINCT posterior sobre `gold_demografia` agrupando por (especie_nombre, nombre_paciente, tutor). Esto es preferible a pre-agregar porque perderíamos la capacidad de ver evolución intra-paciente.

---

### B.3.2 — `gold_diagnosticos`

**Objetivo:** consolidar el universo de **ítems de conclusión** extraídos en F5 (16,939 filas en Silver) en una capa que soporte análisis de prevalencia, ranking, filtros por modificador clínico, y pivotes demográficos.

**Grano:** una fila por **`silver_conclusion_items.id`** (mantenemos grano Silver — son 16,939 filas, no es grande y preserva la granularidad completa).

**Medidas (métricas):**
- `count_informes_con_termino` (precomputado en build — un diagnóstico "presente" se cuenta una vez por informe, no por ocurrencia)
- `es_primario_en_informe` (flag: 1 si es el primer DIAGNOSTICO no-negado de su conclusion)
- `peso_clinico` (derivado de modificadores — ver B.3.7 `gold_calidad_extraccion` para la fórmula exacta; placeholder por ahora)

**Dimensiones (columnas de contexto):**
- `conclusion_item_id` (PK lógica — copia de `silver_conclusion_items.id`)
- `informe_id`
- `dim_termino_conclusion_id` + `termino_canonico` + `tipo_item` + `categoria_clinica` + `organo_asociado`
- `lateralidad` (izq/der/bilat/sin_lateralidad — cardinalidad 4-5)
- `modificador_cualidad` (leve/moderado/severo/agudo/cronico/sin_modificador)
- `modificador_distribucion` (focal/multifocal/difuso/generalizado/sin_modificador)
- `negado` (flag — preservado desde Silver; los negativos también son información clínica)
- `confianza`, `metodo_extraccion`

**Justificación:** se mantienen todas las dimensiones para soportar los 62 pivotajes del catálogo (especie × diag, especie × edad × diag, etc.) sin necesidad de recomputar joins a Silver.

---

### B.3.3 — `gold_hallazgos`

**Objetivo:** consolidar el universo de **atributos de hallazgos** extraídos (114,753 filas en Silver) en una capa que soporte queries de "¿qué atributo es más prevalente en cada órgano?", "¿cómo se comporta X atributo por especie/edad?", series de mediciones numéricas (ej. grosor pared vesical en mm).

**Grano:** una fila por **`silver_atributos_hallazgo.id`** (114,753 filas — la Gold más grande por grano Silver, pero sigue siendo < 200k filas — manejable).

**Medidas (métricas):**
- `valor_numerico` (cuando aplica — para series temporales de mediciones)
- `valor_canonico` (para atributos categóricos: "aumentado", "disminuido", "heterogeneo", etc.)
- `es_anormal` (flag derivado: 1 si el hallazgo padre está en estado `anormal` — precomputado en build)
- `confianza_extraccion`

**Dimensiones (columnas de contexto):**
- `atributo_hallazgo_id` (PK lógica)
- `informe_id`, `hallazgo_id`
- `dim_organo_id` + `organo_nombre` + `sistema` (digestivo, urinario, reproductor, etc.)
- `dim_organo_atributo_id` + `atributo_nombre` (ej. "pared", "contenido", "tamaño", "moteado")
- `dim_valor_atributo_id` + `valor_nombre` + `valor_canonico`
- `segmento_anatomico_id` + `segmento_nombre` (corteza, médula, parénquima, etc.)
- `lateralidad`
- `estado_hallazgo` (normal/anormal/no_evaluado)

**Justificación:** denormalización profunda (6 dimensiones + 5 métricas + 4 flags) para evitar que queries clínicos pesados como "¿media de grosor de pared vesical en felinos geriátricos con cistitis?" requieran 5 JOINs sobre Silver cada vez.

---

### B.3.4 — `gold_coocurrencias`

**Objetivo:** precomputar las **combinaciones diagnósticas que aparecen juntas en el mismo informe** para alimentar análisis de comorbilidad, sospechas clínicas diferenciales, y patrones sindrómicos.

**Grano:** una fila por **par diagnóstico-canónico (a, b)** donde `a.id < b.id` (para evitar duplicados) y ambos `tipo_item = 'DIAGNOSTICO'`. **NO se incluyen pares con negativos** porque los negativos ya tienen su propia categoría clínica.

**Medidas (métricas):**
- `n_coocurrencias` (cuántos informes contienen el par exacto)
- `lift` (opcional: `n_co / (n_a * n_b / n_total)` — se computa en build, no on-the-fly)
- `soporte` (`n_co / n_total_informes` — soporte como % del corpus)
- `confianza_a_dado_b` (`n_co / n_b` — probabilidad condicional P(a|b))
- `confianza_b_dado_a` (`n_co / n_a`)

**Dimensiones (columnas de contexto):**
- `termino_a_id`, `termino_a_nombre`
- `termino_b_id`, `termino_b_nombre`
- `organo_a` (cuando aplica, vía `organo_asociado` del término)
- `organo_b`

**Justificación:** actualmente hay **22,708 pares únicos** en Silver (ver B.4); precomputarlos en Gold ahorra el self-join en cada query analítica. Lift/soporte/confianza son derivadas que NO se deben computar en runtime — el cardinal 22,708 × N consultas las hace inviables sin materialización.

---

### B.3.5 — `gold_tendencias`

**Objetivo:** series temporales precomputadas de diagnósticos y hallazgos, agregadas por mes/año × especie × diagnóstico, para análisis de **incidencia, estacionalidad, evolución del corpus**.

**Grano:** una fila por **(anio, mes, dim_especie_id, dim_termino_conclusion_id)**. Solo se emiten filas donde `n_informes >= 1` (sin ceros espurios).

**Medidas (métricas):**
- `n_informes_con_termino` (prevalencia mensual)
- `n_informes_total` (denominador)
- `prevalencia_pct` (`n_informes_con_termino / n_informes_total * 100` — precomputada)
- `delta_absoluto_vs_mes_anterior` (window function LAG en build — para detectar alertas de cambio)
- `delta_pct_vs_mes_anterior`

**Dimensiones (columnas de contexto):**
- `anio`, `mes` (PK compuesta 1-2)
- `dim_especie_id` + `especie_nombre` (PK compuesta 3-4)
- `dim_termino_conclusion_id` + `termino_canonico` + `tipo_item` (PK compuesta 5-6-7)

**Justificación:** soporta directamente las preguntas T1–T8 del catálogo (incidencias anuales, comparaciones YoY, tendencias mensuales). Las window functions LAG son pesadas sobre Silver puro (necesitan partición por término); precomputarlas en Gold las hace accesibles a dashboards.

---

### B.3.6 — Dimensiones compartidas (`gold_dim_*`)

Tres dimensiones reutilizables que evitan joins repetitivos desde `gold_demografia`/`gold_diagnosticos`/`gold_hallazgos`:

| Dimensión compartida | Grano | Cardinalidad esperada | Propósito |
|---|---|---:|---|
| `gold_dim_tiempo` | una fila por (anio, mes) | ~50 (5 años × 12 meses) | Atributos de fecha precomputados: trimestre, semestre, dia_del_anio, es_inicio_mes, es_fin_mes |
| `gold_dim_paciente` | una fila por (especie, nombre_paciente_normalizado, tutor_normalizado) | ~2,500 estimado | Deduplicación canónica de pacientes, conteo de informes por paciente, primera/última visita, flag "paciente_recurrente" |
| `gold_dim_termino` | una fila por `dim_termino_conclusion.id` | 98 | Precomputa n_informes, n_items, primera_aparicion, ultima_aparicion por término — alimenta rankings |

**Justificación `gold_dim_paciente`:** hoy hay 1,485 vs 1,695 pacientes según dedup, una ambigüedad que debe resolverse al construir Gold (decisión arquitectónica del audit C.3 — riesgo medio). La dimensión se construye UNA vez con la regla canónica y queda referenciada por las demás tablas Gold.

---

### B.3.7 — Capa de linaje y calidad (`gold_calidad_extraccion`)

**Objetivo:** exponer la calidad interna del extractor F5 al consumidor Gold, para que un dashboard pueda alertar degradación.

**Grano:** una fila por **`silver_etl_runs.id`** (un snapshot de calidad por ejecución ETL Silver).

**Medidas:**
- `cobertura_conclusion_pct`
- `n_items_extraidos`
- `n_no_match`
- `n_match_ratio`

**Dimensiones:**
- `etl_run_id`, `started_at`, `finished_at`
- `fase` (F1–F5.1)

**Justificación:** si baja la cobertura F5 de 99.72% a 95%, los analistas deben saberlo antes de tomar decisiones. Esta capa es el "canario en la mina" de la calidad upstream.

---

### B.3.8 — Resumen de capas Gold

| Capa | Tabla(s) | Grano | Filas estimadas | Cardinalidad dimensiones |
|---|---|---|---:|---|
| **Dominios** | `gold_demografia` | 1/informe | 2,893 | 7 + 3 calculadas |
| | `gold_diagnosticos` | 1/conclusión-item | 16,939 | 9 |
| | `gold_hallazgos` | 1/atributo-hallazgo | 114,753 | 9 |
| | `gold_coocurrencias` | 1/par (a<b) DIAGNOSTICO | ~22,708 | 4 + 3 métricas |
| | `gold_tendencias` | 1/(año,mes,especie,termino) | ~6,500 estimado | 7 |
| **Compartidas** | `gold_dim_tiempo` | 1/(año,mes) | ~50 | 5 |
| | `gold_dim_paciente` | 1/paciente único | ~2,500 | 7 |
| | `gold_dim_termino` | 1/término | 98 | 5 |
| **Linaje** | `gold_calidad_extraccion` | 1/ETL run | 21 (acumulativo) | 3 |

**Total materializado:** ~166,461 filas en MVP; < 200k incluso con F6 raza ejecutada. Bien dentro del rango de SQLite y DuckDB sin necesidad de particionado.

---

## PARTE B.4 — TAMAÑO ESPERADO

Datos base medidos sobre `silver.db` al 2026-06-24 (post-F5.1, 19/19 checks OK):

| Métrica base | Valor |
|---|---:|
| `silver_informes` | 2,893 |
| `silver_hallazgos` | 27,866 |
| `silver_atributos_hallazgo` | 114,753 |
| `silver_conclusion_items` | 16,939 |
| `dim_termino_conclusion` activos | 91 / 98 |
| `dim_organo` activos | 15 / 16 |
| `dim_especie` activos | 9 / 9 |
| `dim_sexo` activos | 3 / 3 |
| `dim_edad_categoria` activos | 5 / 5 |
| `dim_estudio` activos | 6 / 8 |
| `dim_estado_reproductivo` activos | 4 / 4 |
| Promedio hallazgos/informe | 9.63 |
| Promedio atributos/hallazgo (con attrs) | 4.26 |
| Promedio conclusion-items/conclusión | 5.87 |
| Pares diag-diag únicos | 22,708 |
| Tuplas (informe, órgano, diag) únicas | 105,553 |

---

### B.4.1 — Estimación por tabla Gold

| Tabla | Filas estimadas | Cálculo | Crecimiento esperado | Frecuencia de rebuild |
|---|---:|---|---|---|
| `gold_demografia` | **2,893** | 1:1 con silver_informes | +600-1,000/año (según rampa 2022→2025: 6 → 477 → 968 → 1,102 → 340 parcial 2026) | Tras cada Silver ETL (incremental UPSERT por `informe_id`) |
| `gold_diagnosticos` | **16,939** | 1:1 con silver_conclusion_items | +3,500-6,000/año (ratio estable: 5.87 items/informe × ~1,000 informes/año) | Tras cada Silver ETL |
| `gold_hallazgos` | **114,753** | 1:1 con silver_atributos_hallazgo | +25,000-40,000/año (~40 attrs/informe × ~1,000 informes) | Tras cada Silver ETL |
| `gold_coocurrencias` | **~22,708** | Self-join sobre silver_conclusion_items donde tipo='DIAGNOSTICO', agrupado por (a<b) | +5,000/año (suma combinatoria: n_diags_unicos² / 2) | Tras cada Silver ETL (FULL rebuild — la materialización es barata sobre 17k filas) |
| `gold_tendencias` | **~6,500** | (anio, mes) × especie × termino. Cálculo: 50 meses observados × 9 especies × 91 términos activos = 40,950 teórico, pero ~16% de celdas tienen >=1 informe → ~6,500 real | +1,300/año (12 meses × 9 spp × 91 terminos × ~16% cobertura) | Mensual (suficiente — la granularidad es mes) o tras Silver ETL |
| `gold_dim_tiempo` | **~50** | 5 años × 12 meses observados → con margen 7 años × 12 = 84 | +12/año | Anual (regeneración trivial) |
| `gold_dim_paciente` | **~2,500** | Estimación: si 2,893 informes únicos × 1.2 ratio medio (algunos pacientes recurrentes) | +500/año (paralelo al crecimiento de informes) | Tras cada Silver ETL (FULL rebuild — el dedup es lo caro) |
| `gold_dim_termino` | **91** | Activos en dim_termino_conclusion | Estable (solo crece con F5.X si se agregan términos) | Tras cada Silver ETL (FULL rebuild — trivial) |
| `gold_calidad_extraccion` | **21** (hoy) | 1 fila por silver_etl_runs | +20-50/año (depende de la cadencia ETL) | Append-only tras cada Silver ETL |

---

### B.4.2 — Volumen total y trayectoria de almacenamiento

| Año | Informes esperados | Total filas Gold estimado | Crecimiento almacenamiento |
|---|---:|---:|---:|
| 2026 (parcial) | ~1,000 | ~166k | base (~15 MB en SQLite) |
| 2027 (proyección) | ~1,300 | ~225k | +5 MB |
| 2028 (proyección) | ~1,700 | ~295k | +6 MB |
| 2029 (proyección) | ~2,200 | ~385k | +8 MB |
| 2030 (proyección) | ~2,900 | ~510k | +10 MB |

> El tamaño es **absolutamente trivial** para cualquier RDBMS moderno. SQLite soporta sin problemas hasta 1M filas; ni siquiera vale la pena considerar DuckDB/PostgreSQL por volumen. Migración justificada solo si queries analíticas pesadas son lentas (no esperable con esta cardinalidad).

---

### B.4.3 — Consideraciones de idempotencia y rebuild

| Tabla | Estrategia de rebuild | Razón |
|---|---|---|
| `gold_demografia` | UPSERT incremental por `informe_id` | Solo cambian informes nuevos o modificados |
| `gold_diagnosticos` | DELETE + INSERT para informes cambiados; UPSERT para nuevos | Grano = ítem de conclusión; items pueden aparecer/desaparecer si cambia el catálogo F5 |
| `gold_hallazgos` | DELETE + INSERT por `informe_id` afectado | Mismo razonamiento |
| `gold_coocurrencias` | FULL REBUILD (truncate + recompute) | Más barato que diff; 22k filas se computan en <2s |
| `gold_tendencias` | FULL REBUILD mensual | Las series temporales son baratas de regenerar; simplifica lógica |
| `gold_dim_tiempo` | FULL REBUILD anual | 50-84 filas, trivial |
| `gold_dim_paciente` | FULL REBUILD (necesario por la lógica de dedup canónica) | El dedup es global; UPSERT por paciente no es seguro |
| `gold_dim_termino` | FULL REBUILD tras cada cambio de catálogo | Trivial |
| `gold_calidad_extraccion` | APPEND-ONLY tras cada ETL run | Histórico |

**Garantía:** cada script Gold es **idempotente** (puede ejecutarse N veces y producir el mismo estado). Cumple con `feedback_idempotent_etl`.

---

### B.4.4 — Distribución de cardinalidad (validación de sizing)

Para validar que las estimaciones son sanas, distribución real observada:

**Especie × informe** (top 5, total 100%):

| Especie | Informes | % |
|---|---:|---:|
| Canino | 1,950 | 67.4% |
| Felino | 879 | 30.4% |
| Conejo | 19 | 0.7% |
| Cobaya | 11 | 0.4% |
| Erizo / Hurón / Hámster / Cuy / Ratón | 27 | 0.9% |

→ 9 especies × ~5,871 conclusion-items esperados cada una es consistente con el ranking clínico esperado.

**Diagnósticos top 5 (10,822 ítems DIAGNOSTICO totales):**

| Término | n | % de diagnósticos |
|---|---:|---:|
| nefropatía | 1,624 | 15.0% |
| hepatomegalia | 1,110 | 10.3% |
| neoplasico | 763 | 7.0% |
| hepatopatía | 606 | 5.6% |
| gastritis | 551 | 5.1% |

→ Los 91 diagnósticos activos tienen distribución sesgada (long tail); `gold_dim_termino` precomputa la frecuencia y `gold_tendencias` cubre los top-N.

**Etiologías (5,574 ítems):**

| Término | n |
|---|---:|
| sospecha_inflamatoria | 2,772 (49.7%) |
| descartar | 952 |
| no_se_puede_descartar | 869 |
| sugerente_de | 762 |

→ 4 etiologías explican 96% de las menciones — `gold_diagnosticos` las tendrá denormalizadas para conteo rápido.

**Órganos (27,866 hallazgos):**

| Órgano | n | Notas |
|---|---:|---|
| Vejiga, Estómago, Intestino, Páncreas, Riñones, Adrenales, Hígado, Bazo, Linfonodos, Vesícula | ~2,687 cada uno | Estudio abdominal sistemático (10 órganos × 2,687 = 26,870) |
| Próstata | 737 | Solo en estudios reproductivos masculinos |
| Gestación | 200 | Marcador de estudio gestacional |
| Útero | 49 | Hallazgos incidentales |
| Testículos | 27 | Bajo reporte |
| Ovarios | 5 | Marginal |

→ Confirma que `gold_hallazgos` debe estar bien indexada por `dim_organo_id` (A.4 del audit lo recomienda).

---

### B.4.5 — Resumen de sizing para el consumidor

> **Para 2,893 informes y 16,939 conclusion-items, Gold materializado ocupa ~166k filas en SQLite (~15 MB) y se regenera en segundos.** No requiere infraestructura especial, ni particionado, ni migraciones de motor. La única razón válida para migrar a DuckDB/PostgreSQL sería queries exploratorias pesadas por parte del consumidor, no el volumen.

---

## PARTE B.5 — PRIORIZACIÓN

### B.5.1 — Clasificación P0/P1/P2

| # | Capa / Tabla | Prioridad | Justificación |
|---|---|:---:|---|
| 1 | `gold_demografia` | **P0** | Cimentación de cualquier otra capa; preguntas D1–D8 + E1–E10 dependen de ella |
| 2 | `gold_diagnosticos` | **P0** | Cimentación para prevalencias, rankings, tendencias; preguntas DX1–DX10 + T1–T8 dependen de ella |
| 3 | `gold_hallazgos` | **P0** | Capa más grande pero única fuente para preguntas de hallazgos (H1–H10); sin ella, el 25% del catálogo no se responde |
| 4 | `gold_dim_paciente` | **P0** | Resuelve la ambigüedad de dedup (riesgo C.3); dimensión compartida crítica |
| 5 | `gold_calidad_extraccion` | **P1** | Valiosa para auditoría pero no bloqueante para preguntas clínicas |
| 6 | `gold_tendencias` | **P1** | Responder T1–T8, pero se puede aproximar con queries directos sobre Silver hasta que esté construida |
| 7 | `gold_coocurrencias` | **P1** | Responder C1–C8 (comorbilidades), pero el self-join sobre Silver es factible bajo demanda |
| 8 | `gold_dim_termino` | **P2** | Tabla auxiliar pequeña; puede reemplazarse con una vista SQL |
| 9 | `gold_dim_tiempo` | **P2** | Tabla trivial; puede reemplazarse con funciones de fecha |

**Resumen:** 4 tablas P0 + 3 P1 + 2 P2 = 9 tablas totales. Las 4 P0 cubren **~75% del catálogo de preguntas** (47 de 62).

---

### B.5.2 — Pregunta crítica: ¿qué construir si solo hay tiempo para UNA iteración?

Si solo hay tiempo para construir **una tabla Gold**, construir:

# **`gold_diagnosticos`**

**Justificación cuantitativa (de las 62 preguntas del catálogo):**

| Preguntas respondibles por `gold_diagnosticos` directamente | Count |
|---|---:|
| Epidemiología (E2, E3, E4, E5, E6, E8, E10) | 7 |
| Demografía (D8 parcial) | 1 |
| Hallazgos (H2, H9) | 2 |
| Diagnósticos (DX1–DX10) | 10 |
| Coocurrencias (C1, C3–C5, C8) | 5 (como base para self-join) |
| Tendencias (T1–T6) | 6 |
| Calidad (Q1–Q4) | 4 |
| Específicas especie (SP1, SP3, SP4) | 3 |
| **Total directo** | **38 / 62 (61%)** |

Además, **`gold_diagnosticos` es pre-requisito lógico** para construir `gold_coocurrencias` (P1) y `gold_tendencias` (P1) en iteraciones siguientes. Sin ella, esas dos son inviables.

**Desventajas de las alternativas:**
- `gold_demografia` solo: responde 19/62 (31%) pero ninguna de las preguntas DX (que son las más clínicas).
- `gold_hallazgos` solo: responde 12/62 (19%) y es la más costosa de construir (114k filas denormalizadas).
- `gold_coocurrencias` solo: requiere `gold_diagnosticos` ya construida (pre-requisito); no es construible en aislamiento.

**Costo de implementación estimado de `gold_diagnosticos`:**
- 1 script Python ~150-200 líneas (lee Silver, escribe Gold con UPSERT).
- Build: <2 segundos para 16,939 filas.
- Tests: 5-8 asserts (PK uniqueness, count = silver, campos denormalizados no nulos, etc.).
- Tiempo total estimado: **1 día de trabajo** (incluyendo tests y signoff parcial).

---

### B.5.3 — Roadmap priorizado alineado con `GOLD_READINESS_AUDIT.md` C.4

#### **Semana 1 — MVP P0 (4 tablas)**

1. **`gold_demografia`** (~2,893 filas, build <1s) — incluye `raza_raw` y `raza_normalizada` vía cross-layer read desde RAW.
2. **`gold_diagnosticos`** (~16,939 filas, build <2s).
3. **`gold_hallazgos`** (~114,753 filas, build <5s).
4. **`gold_dim_paciente`** (~2,500 filas, build <1s) — define la regla canónica de dedup `(LOWER(TRIM(especie)) || LOWER(TRIM(nombre_paciente)) || LOWER(TRIM(tutor)))`.

**Cierre Semana 1:** 47/62 preguntas respondibles; verificación de cobertura (asserts: count(*) match entre Silver y Gold); signoff parcial `docs/GOLD_SIGNOFF_WEEK1.md`.

#### **Semana 2 — P1 (3 tablas)**

5. **`gold_tendencias`** (~6,500 filas, build mensual ~3s con window functions).
6. **`gold_coocurrencias`** (~22,708 filas, build full <3s con self-join).
7. **`gold_calidad_extraccion`** (~21+ filas, append-only).

**Cierre Semana 2:** 62/62 preguntas respondibles (las 3 con dependencia de raza, vía cross-layer); signoff parcial `docs/GOLD_SIGNOFF_WEEK2.md`.

#### **Semana 3 — P2 + cierre (2 tablas + decisión F6)**

8. **`gold_dim_tiempo`** (~50 filas, trivial).
9. **`gold_dim_termino`** (~91 filas, trivial).
10. Decisión sobre **F6 mini-ETL de raza**: si se ejecuta, repoblar `dim_raza` en Silver y regenerar `gold_demografia` con FK propia (eliminar la columna `raza_raw` redundante). Si no, mantener el patrón cross-layer indefinidamente.
11. Tests de regresión Gold end-to-end + dashboard de salud.

**Cierre Semana 3:** `docs/GOLD_FINAL_SIGNOFF.md` con veredicto GOLD CERRADO.

---

### B.5.4 — Riesgos de la priorización

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| `gold_diagnosticos` P0 expone gaps de calidad F5 (8 cids no-match) | Alta | `gold_calidad_extraccion` debe existir desde Semana 2 para alertar |
| Cross-layer read a RAW para raza viola el principio medallion puro | Media | Documentar como **excepción justificada y trazable**; plan B es F6 mini-ETL en Semana 3 |
| `gold_dim_paciente` con regla de dedup diferente a la usada por clínicos | Media | Validar regla con 2-3 clínicos antes de congelar; documentar la decisión |
| SQLite sufre con queries pesadas sobre `gold_coocurrencias` (lift, confianza condicional) | Baja | Las métricas precomputadas eliminan el problema; verificación con EXPLAIN en Week 1 |
| Crecimiento del corpus (rampa 2024→2025: +14%) supere estimación | Baja | Re-estimar sizing cada 6 meses; migrar a DuckDB si >500k filas en Gold |

---

## Resumen ejecutivo del diseño

> **Gold se construye como 5 dominios + 3 dimensiones compartidas + 1 capa de calidad = 9 tablas, ~166k filas iniciales, ~15 MB, build <10s en SQLite.**
>
> **P0: `gold_demografia`, `gold_diagnosticos`, `gold_hallazgos`, `gold_dim_paciente`** (4 tablas; responden 47/62 preguntas).
>
> **Si solo una iteración: `gold_diagnosticos`** (responde 38/62 preguntas directamente + habilita P1 en iteraciones siguientes; construible en 1 día).
>
> **Roadmap:** Semana 1 = P0, Semana 2 = P1, Semana 3 = P2 + decisión F6.
>
> **Restricción arquitectónica:** raza se maneja vía cross-layer read Gold → RAW durante MVP; resolver definitivamente en Semana 3 con F6 mini-ETL.

---

## Próximo paso

Implementación. Los 3 documentos de auditoría (`GOLD_READINESS_AUDIT.md`, `GOLD_QUESTION_CATALOG.md`, `GOLD_DESIGN_V1.md`) están cerrados. Esperar decisión del usuario sobre:
1. Iniciar implementación de `gold_diagnosticos` (P0) como primer paso del roadmap.
2. O bien, ajustar prioridades si algún supuesto del diseño no aplica.
