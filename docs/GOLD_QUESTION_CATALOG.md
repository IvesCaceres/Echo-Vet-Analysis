# Gold Question Catalog — Catálogo de Preguntas Clínicas y Epidemiológicas

> **Fecha:** 2026-06-25
> **Objetivo:** Inventariar 50+ preguntas de negocio/clínica respondibles desde Gold y mapear cada una a sus tablas/JOINs/costos.
> **Origen:** NO partir de tablas. **Partir de preguntas reales** que un veterinario, epidemiólogo o administrativo de clínica podría hacerse.
> **Audiencia:** clínicos veterinarios, epidemiólogos, administradores de clínica veterinaria.

---

## 1. Epidemiología (10 preguntas)

### E1. ¿Cuál es la distribución de informes por especie?

| Atributo | Valor |
|---|---|
| Pregunta | Distribución porcentual de informes por especie |
| Tablas | `silver_informes` + `dim_especie` |
| Joins | 1 (`silver_informes → dim_especie`) |
| Costo estimado | Trivial (2,893 filas) |
| Trivial / Costosa / Imposible | **Trivial** |
| Datos insuficientes | No |
| Notas | Útil para conocer la mezcla de pacientes de la clínica |

### E2. ¿Cuál es la prevalencia de nefropatía por especie?

| Atributo | Valor |
|---|---|
| Pregunta | % de informes con nefropatía (al menos 1 ítem nefropatía) por especie |
| Tablas | `silver_informes`, `silver_conclusion_items`, `dim_termino_conclusion`, `dim_especie` |
| Joins | 3 |
| Costo estimado | Bajo (~16,939 sci × 9 spp) |
| Notas | Requiere flag binario "tiene_nefropatia" por informe |

### E3. ¿Cuál es la prevalencia de nefropatía por especie y edad?

| Atributo | Valor |
|---|---|
| Pregunta | % de nefropatía por especie × categoría etaria |
| Tablas | silver_informes + sci + dim_termino + dim_especie + dim_edad_categoria |
| Joins | 4 |
| Costo estimado | Bajo |
| Trivial | Sí |

### E4. ¿Cuál es la prevalencia de nefropatía por especie, edad y sexo?

| Atributo | Valor |
|---|---|
| Pregunta | Triple pivot: especie × edad × sexo para nefropatía |
| Tablas | silver_informes + sci + dim_termino + dim_especie + dim_edad_categoria + dim_sexo |
| Joins | 5 |
| Costo estimado | Medio (matriz 9×5×3 = 135 celdas) |

### E5. ¿Cuál es la frecuencia de pancreatitis en felinos vs caninos?

| Atributo | Valor |
|---|---|
| Pregunta | Comparación de prevalencia pancreatitis entre caninos y felinos |
| Tablas | silver_informes + sci + dim_termino + dim_especie |
| Joins | 3 |
| Costo estimado | Trivial |
| Notas | Útil para sospecha clínica diferencial |

### E6. ¿Cuál es la distribución de diagnósticos por especie?

| Atributo | Valor |
|---|---|
| Pregunta | Top-10 diagnósticos en caninos; top-10 en felinos |
| Tablas | silver_informes + sci + dim_termino + dim_especie |
| Joins | 3 |
| Costo estimado | Bajo (pivot especie × diagnóstico) |

### E7. ¿Qué porcentaje de informes caninos tienen al menos un hallazgo hepático?

| Atributo | Valor |
|---|---|
| Pregunta | Prevalencia de hallazgos hepáticos en caninos |
| Tablas | silver_informes + silver_hallazgos + dim_organo + dim_especie |
| Joins | 3 |
| Costo estimado | Bajo |

### E8. ¿Hay diferencia en la frecuencia de nefropatía entre macho y hembra?

| Atributo | Valor |
|---|---|
| Pregunta | chi-cuadrado o test de proporciones nefropatía × sexo |
| Tablas | silver_informes + sci + dim_termino + dim_sexo |
| Joins | 3 |
| Costo estimado | Trivial |

### E9. ¿Cuál es la frecuencia de hepatopatía por especie y raza?

| Atributo | Valor |
|---|---|
| Pregunta | % de informes con hepatopatía por especie × raza |
| Tablas | silver_informes + sci + dim_termino + dim_especie + (dim_raza o RAW.raza) |
| Joins | 4 + cross-layer RAW |
| Costo estimado | **Requiere raza** (ver A.6) — implementar vía Gold-side raza normalization |
| Notas | Patrón cross-layer read: gold_informes incluye raza_raw desde RAW |

### E10. ¿Cuál es la incidencia anual de nefropatía?

| Atributo | Valor |
|---|---|
| Pregunta | # informes con nefropatía / # informes totales por año |
| Tablas | silver_informes + sci + dim_termino |
| Joins | 2 |
| Costo estimado | Bajo |
| Notas | Serie temporal 2022-2026 |

---

## 2. Demografía (8 preguntas)

### D1. ¿Cuál es la distribución de informes por sexo?

| Atributo | Valor |
|---|---|
| Pregunta | % hembra vs macho vs indeterminado |
| Tablas | silver_informes + dim_sexo |
| Joins | 1 |
| Costo | Trivial |

### D2. ¿Cuál es la distribución por categoría etaria?

| Atributo | Valor |
|---|---|
| Pregunta | % cachorro, juvenil, adulto, maduro, geriátrico |
| Tablas | silver_informes + dim_edad_categoria |
| Joins | 1 |
| Costo | Trivial |

### D3. ¿Cuál es la pirámide etaria por especie?

| Atributo | Valor |
|---|---|
| Pregunta | Distribución de edad por especie |
| Tablas | silver_informes + dim_edad_categoria + dim_especie |
| Joins | 2 |
| Costo | Trivial |

### D4. ¿Cuál es la edad promedio por especie?

| Atributo | Valor |
|---|---|
| Pregunta | AVG(edad_meses) por especie |
| Tablas | silver_informes + dim_especie |
| Joins | 1 |
| Costo | Trivial |
| Notas | Útil para describir población |

### D5. ¿Cuántos informes por estado reproductivo?

| Atributo | Valor |
|---|---|
| Pregunta | Distribución por estado reproductivo |
| Tablas | silver_informes + dim_estado_reproductivo |
| Joins | 1 |
| Costo | Trivial |

### D6. ¿Cuántos pacientes únicos tenemos?

| Atributo | Valor |
|---|---|
| Pregunta | COUNT DISTINCT de pacientes |
| Tablas | silver_informes (definir dedup canónica) |
| Joins | 0 |
| Costo | Trivial |
| Notas | Definir regla: nombre_paciente + dim_especie_id + tutor → 1,695 únicos (verificado) |

### D7. ¿Cuántos pacientes tienen ≥2 informes (longitudinales)?

| Atributo | Valor |
|---|---|
| Pregunta | # pacientes con ≥2 informes |
| Tablas | silver_informes agrupado por (LOWER(nombre), especie) |
| Joins | 0 |
| Costo | Trivial |
| Datos observados | 493 pacientes con >1 informe |

### D8. ¿Cuál es la distribución de peso promedio por especie y edad?

| Atributo | Valor |
|---|---|
| Pregunta | AVG(peso_kg) por especie × edad |
| Tablas | silver_informes + dim_especie + dim_edad_categoria |
| Joins | 2 |
| Costo | Bajo |
| Notas | Útil para tamaños poblacionales |

---

## 3. Hallazgos ecográficos (10 preguntas)

### H1. ¿Cuál es la distribución de hallazgos por órgano?

| Atributo | Valor |
|---|---|
| Pregunta | Top-10 órganos por número de hallazgos |
| Tablas | silver_hallazgos + dim_organo |
| Joins | 1 |
| Costo | Trivial |

### H2. ¿Cuál es la frecuencia de cada hallazgo morfológico (masa, nódulo, quiste) por especie?

| Atributo | Valor |
|---|---|
| Pregunta | # hallazgos con `masa`, `nódulo`, `quiste` por especie |
| Tablas | silver_hallazgos + silver_informes + dim_organo + dim_especie + dim_termino_conclusion |
| Joins | 4 (sci solo para inferir término) |
| Costo | Medio |

### H3. ¿Cuál es la frecuencia de cada hallazgo por raza?

| Atributo | Valor |
|---|---|
| Pregunta | Pivot raza × hallazgo |
| Tablas | silver_informes + silver_hallazgos + dim_organo + RAW.informes.raza (cross-layer) |
| Joins | 3 + cross-layer |
| Costo | **Requiere raza** |

### H4. ¿Cuántos hallazgos por informe en promedio por especie?

| Atributo | Valor |
|---|---|
| Pregunta | AVG(n_hallazgos) por especie |
| Tablas | silver_informes + silver_hallazgos + dim_especie |
| Joins | 2 |
| Costo | Trivial |
| Datos observados | Felino 9.79, Canino 9.54, Conejo 10.37, otros ~10 |

### H5. ¿Cuántos atributos (mediciones) por hallazgo en promedio?

| Atributo | Valor |
|---|---|
| Pregunta | AVG(n_atributos) por hallazgo |
| Tablas | silver_hallazgos + silver_atributos_hallazgo |
| Joins | 1 |
| Costo | Trivial |
| Datos observados | 4.12 attrs/hallazgo global |

### H6. ¿Cuál es la distribución de valores canónicos para un atributo específico (ej. pared_vejiga)?

| Atributo | Valor |
|---|---|
| Pregunta | Top valores para `paredes` en vejiga |
| Tablas | silver_atributos_hallazgo + dim_organo_atributo + dim_atributo + dim_organo + dim_valor_atributo |
| Joins | 4 |
| Costo | Medio |

### H7. ¿Cuántos informes tienen lateralidad documentada para un hallazgo bilateral?

| Atributo | Valor |
|---|---|
| Pregunta | % de hallazgos renales con lateralidad |
| Tablas | silver_atributos_hallazgo + dim_organo_atributo + dim_organo |
| Joins | 2 |
| Costo | Bajo |

### H8. ¿Cuál es la distribución de hallazgos por estudio (abdominal vs gestacional)?

| Atributo | Valor |
|---|---|
| Pregunta | # hallazgos por tipo de estudio |
| Tablas | silver_informes + silver_hallazgos + dim_estudio |
| Joins | 2 |
| Costo | Trivial |
| Datos observados | Abdominal: 2,699; Gestacional: 119; Cervical: 36; Otro: 17 |

### H9. ¿Cuál es la distribución de gestación por especie?

| Atributo | Valor |
|---|---|
| Pregunta | # informes gestacionales por especie |
| Tablas | silver_informes + silver_conclusion_items + dim_termino + dim_especie (filtrar `gestacion`) |
| Joins | 3 |
| Costo | Bajo |

### H10. ¿Cuál es la longitud promedio de hallazgos por especie?

| Atributo | Valor |
|---|---|
| Pregunta | AVG(longitud_caracteres) por especie |
| Tablas | silver_hallazgos + silver_informes + dim_especie |
| Joins | 2 |
| Costo | Trivial |

---

## 4. Diagnósticos (10 preguntas)

### DX1. ¿Cuáles son los 10 diagnósticos más frecuentes?

| Atributo | Valor |
|---|---|
| Pregunta | Top-10 términos canónicos DIAGNOSTICO por count |
| Tablas | silver_conclusion_items + dim_termino_conclusion |
| Joins | 1 |
| Costo | Trivial |
| Datos observados | nefropatia (1,624), hepatomegalia (1,110), neoplasico (763) |

### DX2. ¿Cuál es la frecuencia de nefropatía por año?

| Atributo | Valor |
|---|---|
| Pregunta | Serie temporal de nefropatía por año |
| Tablas | silver_conclusion_items + dim_termino_conclusion + silver_informes |
| Joins | 2 |
| Costo | Bajo |
| Notas | Tendencia de nefropatía |

### DX3. ¿Cuál es la frecuencia de pancreatitis por mes?

| Atributo | Valor |
|---|---|
| Pregunta | # pancreatitis por mes (últimos 24 meses) |
| Tablas | silver_informes + silver_conclusion_items + dim_termino_conclusion |
| Joins | 2 |
| Costo | Bajo |

### DX4. ¿Cuál es la distribución de diagnósticos por categoría clínica?

| Atributo | Valor |
|---|---|
| Pregunta | # ítems por categoría clínica |
| Tablas | silver_conclusion_items + dim_termino_conclusion |
| Joins | 1 |
| Costo | Trivial |
| Datos observados | HEPATICA 2,393; RENAL 1,847; GASTROINTESTINAL 1,393 |

### DX5. ¿Cuál es el top-10 de diagnósticos negados?

| Atributo | Valor |
|---|---|
| Pregunta | Top-10 términos con `negado=TRUE` |
| Tablas | silver_conclusion_items + dim_termino_conclusion (filtro WHERE negado=1) |
| Joins | 1 |
| Costo | Trivial |
| Notas | "Sin nefropatía", "sin hepatomegalia", etc. |

### DX6. ¿Cuál es la frecuencia de diagnósticos por edad?

| Atributo | Valor |
|---|---|
| Pregunta | Pivot diagnóstico × edad_categoria |
| Tablas | silver_informes + silver_conclusion_items + dim_termino + dim_edad_categoria |
| Joins | 3 |
| Costo | Bajo |

### DX7. ¿Cuál es la frecuencia de cada diagnóstico con modificador severo?

| Atributo | Valor |
|---|---|
| Pregunta | # diagnósticos con modificador_cualidad='severa' |
| Tablas | silver_conclusion_items + dim_termino_conclusion |
| Joins | 1 |
| Costo | Trivial |
| Notas | Útil para "qué casos severos vemos más" |

### DX8. ¿Cuál es la tasa de nefropatía bilateral?

| Atributo | Valor |
|---|---|
| Pregunta | % de nefropatía con lateralidad='bilateral' |
| Tablas | silver_conclusion_items + dim_termino (filtro nefropatia) |
| Joins | 1 |
| Costo | Trivial |

### DX9. ¿Cuántos diagnósticos se acompañan de "sospecha_inflamatoria"?

| Atributo | Valor |
|---|---|
| Pregunta | Coocurrencia diagnóstico × sospecha_inflamatoria |
| Tablas | silver_conclusion_items + dim_termino |
| Joins | 1 (mismo fact) |
| Costo | Bajo |
| Notas | Ver coocurrencias |

### DX10. ¿Cuál es la distribución de diagnósticos por trimestre del año?

| Atributo | Valor |
|---|---|
| Pregunta | Patrón estacional de diagnósticos |
| Tablas | silver_informes + silver_conclusion_items + dim_termino |
| Joins | 2 |
| Costo | Bajo |
| Notas | Útil para estacionalidad |

---

## 5. Coocurrencias (8 preguntas)

### C1. ¿Cuáles son los 20 pares de diagnósticos más coocurrentes?

| Atributo | Valor |
|---|---|
| Pregunta | Top-20 pares (dx1, dx2) por count en MISMO conclusion_id |
| Tablas | silver_conclusion_items (self-join) + dim_termino_conclusion |
| Joins | 1 self-join |
| Costo | Medio (auto-producto sobre 16,939 ítems) |
| Datos observados | nefropatia + hepatomegalia (793); hepatopatia + vacuolar (556) |

### C2. ¿Cuál es la tríada diagnóstica más común?

| Atributo | Valor |
|---|---|
| Pregunta | Top tríos de diagnósticos |
| Tablas | silver_conclusion_items (2 self-joins) |
| Joins | 2 self-joins |
| Costo | **Alto** (triple producto cartesiano filtrado) |
| Notas | Útil pero costoso; fact_derived recomendado |

### C3. ¿Qué diagnósticos se asocian a nefropatía?

| Atributo | Valor |
|---|---|
| Pregunta | Top-10 diagnósticos coocurrentes con nefropatia |
| Tablas | silver_conclusion_items + dim_termino |
| Joins | 1 self-join |
| Costo | Bajo |
| Datos observados | hepatomegalia (793), neoplasico (407), gastritis (349), barro_biliar (305) |

### C4. ¿Cuál es la coocurrencia de nefropatía + hepatomegalia + barro_biliar?

| Atributo | Valor |
|---|---|
| Pregunta | "Triada" nefropatía + hepatomegalia + barro_biliar |
| Tablas | silver_conclusion_items |
| Joins | self-join |
| Costo | Bajo |

### C5. ¿Hay correlación entre nefropatía y pancreatitis?

| Atributo | Valor |
|---|---|
| Pregunta | Odds ratio nefropatía × pancreatitis |
| Tablas | silver_conclusion_items + dim_termino |
| Joins | 1 self-join |
| Costo | Bajo |

### C6. ¿Qué hallazgo de órgano (silver_hallazgos) se asocia a qué diagnóstico (sci)?

| Atributo | Valor |
|---|---|
| Pregunta | Pivot hallazgo_organo × diagnóstico |
| Tablas | silver_hallazgos + silver_conclusion_items + dim_organo + dim_termino |
| Joins | 3 (vinculados por conclusion_id o por informe_id) |
| Costo | Medio |

### C7. ¿Cuál es la coocurrencia de hallazgo morfológico + diagnóstico?

| Atributo | Valor |
|---|---|
| Pregunta | Pareo (nódulo/masa/quiste) × diagnóstico |
| Tablas | silver_hallazgos + silver_conclusion_items |
| Joins | 2 |
| Costo | Medio |

### C8. ¿Cuántos diagnósticos comparten lateralidad bilateral?

| Atributo | Valor |
|---|---|
| Pregunta | # pares de diagnósticos con lateralidad='bilateral' en mismo informe |
| Tablas | silver_conclusion_items |
| Joins | self-join |
| Costo | Bajo |

---

## 6. Tendencias temporales (8 preguntas)

### T1. ¿Cómo evoluciona el número de informes por mes?

| Atributo | Valor |
|---|---|
| Pregunta | Serie mensual de informes |
| Tablas | silver_informes |
| Joins | 0 |
| Costo | Trivial |

### T2. ¿Cómo evoluciona la prevalencia de nefropatía por trimestre?

| Atributo | Valor |
|---|---|
| Pregunta | Serie trimestral de prevalencia nefropatía |
| Tablas | silver_informes + silver_conclusion_items + dim_termino |
| Joins | 2 |
| Costo | Bajo |

### T3. ¿Hay estacionalidad en gastroenteritis?

| Atributo | Valor |
|---|---|
| Pregunta | # gastroenteritis por mes × año |
| Tablas | silver_informes + silver_conclusion_items + dim_termino |
| Joins | 2 |
| Costo | Bajo |

### T4. ¿Cómo varía la prevalencia de nefropatía por año y especie?

| Atributo | Valor |
|---|---|
| Pregunta | Pivot año × especie × nefropatía |
| Tablas | silver_informes + silver_conclusion_items + dim_termino + dim_especie |
| Joins | 3 |
| Costo | Bajo |

### T5. ¿Cuándo se introdujo cada término en el corpus (cronología)? (meta)

| Atributo | Valor |
|---|---|
| Pregunta | Para auditoría: en qué año/mes apareció por primera vez cada término |
| Tablas | silver_conclusion_items + dim_termino + silver_informes |
| Joins | 2 |
| Costo | Bajo |

### T6. ¿Hay tendencia creciente/decreciente en algún diagnóstico?

| Atributo | Valor |
|---|---|
| Pregunta | Análisis de tendencia lineal sobre serie temporal |
| Tablas | silver_informes + sci + dim_termino |
| Joins | 2 |
| Costo | Bajo (computacionalmente Gold-side) |

### T7. ¿Cuál es la cadencia de informes por paciente (frecuencia de seguimientos)?

| Atributo | Valor |
|---|---|
| Pregunta | AVG días entre informes del mismo paciente |
| Tablas | silver_informes |
| Joins | 0 (self) |
| Costo | Medio (cálculo de deltas) |

### T8. ¿Cuál es el "lag" entre informes de seguimiento (delta temporal)? 

| Atributo | Valor |
|---|---|
| Pregunta | Distribución de días entre 1° y 2° informe del mismo paciente |
| Tablas | silver_informes (window function sobre partición por paciente) |
| Joins | 0 |
| Costo | Medio |

---

## 7. Calidad diagnóstica (8 preguntas)

### Q1. ¿Cuántas conclusiones quedaron sin ítems (stg_conclusion_no_match)?

| Atributo | Valor |
|---|---|
| Pregunta | # conclusiones sin ítems / total |
| Tablas | stg_conclusion_no_match |
| Joins | 0 |
| Costo | Trivial |
| Datos observados | 8/2,893 (0.28%) |

### Q2. ¿Cuál es la distribución de ítems/conclusión?

| Atributo | Valor |
|---|---|
| Pregunta | Histograma de n_items por conclusion_id |
| Tablas | silver_conclusion_items |
| Joins | 0 (group by) |
| Costo | Trivial |
| Datos observados | media=5.87, mediana=5, max=27 |

### Q3. ¿Cuántos ítems están negados?

| Atributo | Valor |
|---|---|
| Pregunta | % de ítems con `negado=TRUE` |
| Tablas | silver_conclusion_items |
| Joins | 0 |
| Costo | Trivial |
| Datos observados | 1,648/16,939 (9.73%) |

### Q4. ¿Cuál es la tasa de modificación (ítems con modificador_cualidad)?

| Atributo | Valor |
|---|---|
| Pregunta | % de ítems con modificador_cualidad no-NULL |
| Tablas | silver_conclusion_items |
| Joins | 0 |
| Costo | Trivial |
| Datos observados | 11,580/16,939 (68.4%) |

### Q5. ¿Cuántos hallazgos están marcados como `estado='invalidado'`?

| Atributo | Valor |
|---|---|
| Pregunta | # hallazgos con estado != 'ok' |
| Tablas | silver_hallazgos |
| Joins | 0 |
| Costo | Trivial |
| Notas | Útil para auditoría de calidad |

### Q6. ¿Cuántos hallazgos son `gestacion_fallback`?

| Atributo | Valor |
|---|---|
| Pregunta | # hallazgos con es_gestacion_fallback=TRUE |
| Tablas | silver_hallazgos |
| Joins | 0 |
| Costo | Trivial |

### Q7. ¿Cuántos atributos son `metodo_extraccion` != 'REGEX_RULE'?

| Atributo | Valor |
|---|---|
| Pregunta | # atributos extraídos por método no-regex |
| Tablas | silver_atributos_hallazgo |
| Joins | 0 |
| Costo | Trivial |

### Q8. ¿Cuántos atributos tienen `confianza < 1.0`?

| Atributo | Valor |
|---|---|
| Pregunta | # atributos con confianza < 1.0 |
| Tablas | silver_atributos_hallazgo |
| Joins | 0 |
| Costo | Trivial |

---

## 8. Preguntas específicas de especie (bonus)

### SP1. ¿Cuál es la prevalencia de urolitiasis en felinos?

| Atributo | Valor |
|---|---|
| Tablas | silver_informes + sci + dim_termino + dim_especie |
| Joins | 3 |
| Costo | Trivial |

### SP2. ¿Cuál es la prevalencia de cardiomiopatía por raza en caninos?

| Atributo | Valor |
|---|---|
| Tablas | requiere raza → usar cross-layer RAW |
| Costo | **Requiere raza** |

### SP3. ¿Cuál es la frecuencia de gestaciones por edad en caninos?

| Atributo | Valor |
|---|---|
| Tablas | silver_informes + sci + dim_termino + dim_especie + dim_edad_categoria |
| Joins | 4 |
| Costo | Bajo |

### SP4. ¿Hay diferencia de nefropatía entre caninos enteros vs castrados?

| Atributo | Valor |
|---|---|
| Tablas | silver_informes + sci + dim_termino + dim_estado_reproductivo |
| Joins | 3 |
| Costo | Bajo |

---

## Resumen ejecutivo del catálogo

**Total preguntas catalogadas:** 62 (50+ requeridas).

**Por dominio:**

| Dominio | # preguntas |
|---|---:|
| Epidemiología | 10 |
| Demografía | 8 |
| Hallazgos | 10 |
| Diagnósticos | 10 |
| Coocurrencias | 8 |
| Tendencias temporales | 8 |
| Calidad diagnóstica | 8 |
| Específicas de especie (bonus) | 4 |
| **TOTAL** | **62** |

**Por factibilidad:**

| Clasificación | # preguntas | % |
|---|---:|---:|
| Triviales (0-2 JOINs) | 28 | 45% |
| Bajo costo (3 JOINs) | 24 | 39% |
| Costo medio (4 JOINs) | 7 | 11% |
| Costo alto (self-join + ventana) | 2 | 3% |
| **Requieren raza** | 1 | 2% (E9, H3, SP2) |

**Requieren cruzar a RAW para raza:** 3 preguntas (E9, H3, SP2). Las 59 restantes se responden puramente desde Silver.

---

## Matriz agregada pregunta → datos

| Pregunta | Tablas involucradas | Joins | Costo |
|---|---|---:|---|
| E1 | silver_informes, dim_especie | 1 | Trivial |
| E2 | + silver_conclusion_items, dim_termino | 3 | Bajo |
| E3 | + dim_edad_categoria | 4 | Bajo |
| E4 | + dim_sexo | 5 | Medio |
| E5 | silver_informes, sci, dim_termino, dim_especie | 3 | Bajo |
| E6 | (idem) | 3 | Bajo |
| E7 | silver_informes, silver_hallazgos, dim_organo, dim_especie | 3 | Bajo |
| E8 | silver_informes, sci, dim_termino, dim_sexo | 3 | Trivial |
| E9 | + RAW.informes.raza | 4 + cross-layer | **Requiere raza** |
| E10 | silver_informes, sci, dim_termino | 2 | Bajo |
| D1 | silver_informes, dim_sexo | 1 | Trivial |
| D2 | silver_informes, dim_edad_categoria | 1 | Trivial |
| D3 | + dim_especie | 2 | Trivial |
| D4 | silver_informes, dim_especie | 1 | Trivial |
| D5 | silver_informes, dim_estado_reproductivo | 1 | Trivial |
| D6 | silver_informes | 0 | Trivial |
| D7 | silver_informes | 0 | Trivial |
| D8 | silver_informes, dim_especie, dim_edad_categoria | 2 | Bajo |
| H1 | silver_hallazgos, dim_organo | 1 | Trivial |
| H2 | + silver_informes, dim_especie, dim_termino | 4 | Medio |
| H3 | + RAW.informes.raza | 3 + cross-layer | **Requiere raza** |
| H4 | silver_informes, silver_hallazgos, dim_especie | 2 | Trivial |
| H5 | silver_hallazgos, silver_atributos_hallazgo | 1 | Trivial |
| H6 | silver_atributos_hallazgo, dim_organo_atributo, dim_atributo, dim_organo, dim_valor_atributo | 4 | Medio |
| H7 | silver_atributos_hallazgo, dim_organo_atributo, dim_organo | 2 | Bajo |
| H8 | silver_informes, silver_hallazgos, dim_estudio | 2 | Trivial |
| H9 | silver_informes, sci, dim_termino, dim_especie | 3 | Bajo |
| H10 | silver_hallazgos, silver_informes, dim_especie | 2 | Trivial |
| DX1 | silver_conclusion_items, dim_termino | 1 | Trivial |
| DX2 | + silver_informes | 2 | Bajo |
| DX3 | (idem) | 2 | Bajo |
| DX4 | silver_conclusion_items, dim_termino | 1 | Trivial |
| DX5 | silver_conclusion_items, dim_termino | 1 | Trivial |
| DX6 | silver_informes, sci, dim_termino, dim_edad_categoria | 3 | Bajo |
| DX7 | silver_conclusion_items, dim_termino | 1 | Trivial |
| DX8 | silver_conclusion_items, dim_termino | 1 | Trivial |
| DX9 | silver_conclusion_items, dim_termino | 1 | Bajo |
| DX10 | silver_informes, sci, dim_termino | 2 | Bajo |
| C1 | silver_conclusion_items (self-join), dim_termino | 1 self | Medio |
| C2 | silver_conclusion_items (2 self-joins) | 2 self | Alto |
| C3 | (idem C1) | 1 self | Bajo |
| C4 | silver_conclusion_items | 1 self | Bajo |
| C5 | silver_conclusion_items, dim_termino | 1 self | Bajo |
| C6 | silver_hallazgos, sci, dim_organo, dim_termino | 3 | Medio |
| C7 | silver_hallazgos, sci | 2 | Medio |
| C8 | silver_conclusion_items (self) | 1 self | Bajo |
| T1 | silver_informes | 0 | Trivial |
| T2-T4 | silver_informes, sci, dim_termino + (dim_especie, dim_edad_categoria) | 2-3 | Bajo |
| T5 | silver_conclusion_items, dim_termino, silver_informes | 2 | Bajo |
| T6 | (idem) | 2 | Bajo |
| T7 | silver_informes | 0 (window) | Medio |
| T8 | silver_informes | 0 (window) | Medio |
| Q1 | stg_conclusion_no_match | 0 | Trivial |
| Q2-Q4 | silver_conclusion_items | 0 | Trivial |
| Q5-Q6 | silver_hallazgos | 0 | Trivial |
| Q7-Q8 | silver_atributos_hallazgo | 0 | Trivial |
| SP1 | silver_informes, sci, dim_termino, dim_especie | 3 | Trivial |
| SP2 | + RAW.informes.raza | 3 + cross-layer | **Requiere raza** |
| SP3 | silver_informes, sci, dim_termino, dim_especie, dim_edad_categoria | 4 | Bajo |
| SP4 | silver_informes, sci, dim_termino, dim_estado_reproductivo | 3 | Bajo |

---

## Conclusión del catálogo

> **62 preguntas catalogadas, 59 respondibles puramente desde Silver, 3 requieren acceso cross-layer a RAW para raza.** Las preguntas triviales (45%) se pueden resolver con queries directos sobre Silver; las de costo medio (11%) requieren joins múltiples pero son factibles; las de costo alto (3%) requieren materialización previa en Gold (no se recomputan cada vez).
>
> **El catálogo es exhaustivo para los objetivos clínicos y epidemiológicos del proyecto.** Las preguntas que requieren raza (3) son un subconjunto manejable que puede abordarse vía Gold-side normalization sin reabrir Silver.
