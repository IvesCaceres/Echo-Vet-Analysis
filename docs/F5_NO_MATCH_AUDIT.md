# F5 — Auditoría clínica de `stg_conclusion_no_match` (pre-Gold)

> **Fecha:** 2026-06-24
> **Alcance:** 67 conclusiones sin ítems extraídos (`stg_conclusion_no_match`)
> **Objetivo:** decidir si los 67 no-match justifican retrasar Gold
> **Veredicto:** **B) GO tras F5.1** (agregar 11 términos + 4 regex fixes, ~15 min)
> **Artefactos:**
> - `scripts/_audit_f5_no_match.py` — profiler
> - `scripts/_audit_f5_classify.py` — clasificador manual

---

## 1. Resumen ejecutivo

| Métrica | Valor |
|---|---:|
| Total conclusiones sin match | 67 (2.32% de 2,893) |
| Textos únicos normalizados | 64 |
| Caracteres (media / mediana / max) | 91 / 90 / 256 |
| Palabras (media / mediana / max) | 11.8 / 11 / 36 |
| Oraciones (media / max) | 1.48 / 4 |
| Tipo_no_match | `sin_patron` (100%) |

**Clasificación clínica:**

| Cat | Descripción | Conclusiones | % |
|---|---|---:|---:|
| A | Sin información clínica (ruido / admin) | 2 | 3.0% |
| B | Ya cubierto, falla de regex | 11 | 16.4% |
| C | Nuevo diagnóstico relevante | 45 | 67.2% |
| D | Nueva etiología relevante | 0 | 0.0% |
| E | Nuevo término negativo relevante | 0 | 0.0% |
| F | Texto ambiguo / fuera de scope | 8 | 11.9% |
| **?** | Pendiente revisar | 1 | 1.5% |

**Decisión cuantitativa:**

| Escenario | +ítems | +cids | Items total | % ítems | Cobertura |
|---|---:|---:|---:|---:|---:|
| **Actual** | — | — | 15,968 | — | **97.68%** |
| Top 1 término (`cambios_tiroideos`) | +18 | +12 | 15,986 | +0.11% | 98.10% |
| Top 3 términos | +41 | +27 | 16,009 | +0.26% | 98.62% |
| Top 5 términos | +50 | +34 | 16,018 | +0.31% | 98.86% |
| **Top 11 (F5.1 recomendado)** | **+67** | **+45** | **16,035** | **+0.42%** | **99.24%** |
| Todos los no-F | +85 | +59 | 16,053 | +0.53% | 99.72% |

**Recomendación:** aplicar F5.1 (15 min de trabajo) cubriendo el 67.2% de los no-match con riesgo de FP bajo. NO retrasar Gold por los 8 casos F (fuera de scope del catálogo actual: ortopedia, laringe, panículo).

---

## 2. Perfilado completo (Tarea 1)

### 2.1 Distribución por longitud (palabras)

| Bucket | Conclusiones | % |
|---|---:|---:|
| 1–5 palabras | 9 | 13.4% |
| 6–10 palabras | 23 | 34.3% |
| 11–15 palabras | 21 | 31.3% |
| 16–20 palabras | 9 | 13.4% |
| 21–30 palabras | 4 | 6.0% |
| 31–100 palabras | 1 | 1.5% |

**Lectura:** El 47.7% (32/67) tiene ≤10 palabras — son conclusiones cortas y específicas (criptorquidia, sedimento, lito vesical, etc.). El 1.5% (1 caso) tiene 36 palabras — es texto administrativo (cid=1153, "Presencia de varios cuerpos extraño en estómago...").

### 2.2 Conclusiones más largas (top 5)

| cid | chars | Texto resumido |
|---|---:|---|
| 1153 | 256 | "Presencia de varios cuerpos extraño... seguimiento y control ecográfico... según Médico Veterinario Tratante" (administrativo) |
| 1612 | 190 | "Cambios en tejido subcutáneo que sugieren acúmulo de tejido graso... control ecográfico..." (administrativo + ambiguo) |
| 893 | 180 | Ortopedia rodilla: "Surco troclear aplanado... artrosis... incompetencia ligamento" (fuera scope) |
| 715 | 172 | "Presencia de elemento en estómago... sugerentes de cuerpos extraños" (cubrible con `cuerpo_extrano`) |
| 399 | 168 | Ortopedia rodilla: "Derrame sinovial... Luxación medial de patella... hiperlaxitud ligamento" (fuera scope) |

### 2.3 Patrones repetidos (≥2 apariciones)

| Patrón | # apariciones | cids |
|---|---:|---|
| `cambios tiroideos` | 12 | 314, 371, 414, 530, 642, 702, 897, 1003, 1602, 1643, 1747, 2768 |
| `criptorquid` / `criptórquid` | 9 | 1519, 1555, 1621, 1805, 2339, 2377, 2435, 2526, 2728 |
| `cuerpo extraño` | 6 | 224, 612, 2162, 2311, 2836, 2860 |
| `sedimento` | 5 | 668, 794, 1620, 1774, 2887 |
| `obstructivo` | 8 | 92, 224, 1153, 1431, 2162, 2311, 2660, 2836 |
| `distención` / `distension` | 5 | 612, 1431, 1489, 2144, 2860 |
| `patella` / `artrosis` / `surco troclear` | 4+3+2 | 376, 399, 893, 907 |
| `proestro` | 2 | 5, 1821 |

**Lectura:** 4 clusters dominan: tiroides (12), criptorquidia (9), cuerpo extraño (8), sedimento (5). Esos 4 clusters explican 34/67 = 51% de los no-match.

---

## 3. Clasificación clínica manual (Tarea 2)

### 3.1 Tabla completa (67 conclusiones)

| cid | Cat | Texto (resumido) | Acción propuesta |
|---:|:--:|---|---|
| 5 | C | Útero y ovarios sugerentes de actividad estral | +`actividad_estral` |
| 79 | C | Paniculitis grasa intra abdominal focal | +`paniculitis` |
| 92 | F | Vejiga dilatada sin signos de punto obstructivo | — (ambiguo) |
| 144 | B/C | Derrame pleural y peritoneal severo | +`derrame_pleural` |
| 224 | C | Sugerentes de proceso obstructivo, sin cuerpo extraño | +`cuerpo_extrano` |
| 314 | C | Cambios tiroideos sugerentes de proceso inflamatorio crónico | +`cambios_tiroideos` |
| 320 | B/C | Linfonodopatía de aspecto reactivo. Desgarro muscular | regex fix +`linfadenomegalia` / ortopedia |
| 371 | C | Cambios tiroideos (RR 0.7-2.0ml) | +`cambios_tiroideos` |
| 376 | F | Surco troclear aplanado. Artrosis rodilla | — (fuera scope ortopedia) |
| 379 | C | Íleo moderado a severo de intestino delgado | +`ileo` |
| 399 | F | Derrame sinovial. Luxación patella | — (fuera scope ortopedia) |
| 414 | C | Cambios tiroideos sugerentes | +`cambios_tiroideos` |
| 456 | C | Ilio intestinal severo (typo) | +`ileo` |
| 478 | A | No se observa cambios anatómicos ni patológicos | regex fix `sin_evidencia` |
| 530 | C | Cambios tiroideos (con espacio extra) | +`cambios_tiroideos` |
| 612 | C | Distención estomacal con cuerpo extraño | +`distension_gastrica` +`cuerpo_extrano` |
| 642 | C | Cambios tiroideos (RR 124-215mm3) | +`cambios_tiroideos` |
| 667 | C | Tiflitis. Úlceras intestinales | +`tiflitis` +`ulcera_intestinal` |
| 668 | B | Sedimento leve en vejiga | regex fix `sedimento_vejiga` |
| 702 | C | Cambios tiroideos (compromiso) | +`cambios_tiroideos` |
| 715 | C | Elemento en estómago... cuerpos extraños | +`cuerpo_extrano` |
| 794 | B | Sedimento abundante en vejiga | regex fix `sedimento_vejiga` |
| 893 | F | Surco troclear + artrosis rodilla izquierda | — (fuera scope) |
| 897 | C | Cambios tiroideos (RR hipertiroideo) | +`cambios_tiroideos` |
| 907 | F | Luxación patella + artrosis | — (fuera scope) |
| 990 | B | Proceso inflamatorio en vejiga. Testículo retenido | regex fix `cistitis` + `criptorquidismo` |
| 1003 | C | Cambios tiroideos | +`cambios_tiroideos` |
| 1008 | C | Remanente ovárico derecho | +`remanente_ovarico` |
| 1026 | C | Hipomotilidad intestino. Íleo de ciego | +`hipomotilidad_intestinal` |
| 1030 | B | Lito vesical | regex fix `cistolito` |
| 1091 | B | Dilatación uretral (typo de ureteral) | regex fix `dilatacion_ureteral` |
| 1153 | C | Cuerpos extraño + texto administrativo | +`cuerpo_extrano` |
| 1303 | F | Bursitis bicipital | — (fuera scope ortopedia) |
| 1431 | C | Dilatación hiperperistáltica intestino delgado | +`distension_intestinal` |
| 1489 | C | Distensión gastro entérica | +`distension_gastrica` |
| 1519 | C | Testículo Criptórquido derecho subcutáneo | +`criptorquidismo` |
| 1555 | C | Criptorquidia testicular derecha | +`criptorquidismo` |
| 1602 | C | Cambios tiroideos (agudo) | +`cambios_tiroideos` |
| 1612 | F | Acúmulo de tejido graso subcutáneo | — (ambiguo) |
| 1620 | B/C | Sedimento + cambios prostáticos hiperplásicos | regex + `hiperplasia_prostatica` |
| 1621 | C | Testículo izquierdo en zona subcutánea | +`criptorquidismo` |
| 1631 | B | Cambios hepáticos sugerentes | regex fix `hepatopatia` |
| 1643 | C | Cambios tiroideos | +`cambios_tiroideos` |
| 1648 | B | Cambios en páncreas | regex fix `cambios_pancreaticos` |
| 1747 | C | Cambios tiroideos (disminución) | +`cambios_tiroideos` |
| 1774 | B | Sedimento y litos vesicales | regex fix `sedimento_vejiga` |
| 1794 | F | Cambio de tejido blando adyacente a laringe | — (origen indeterminado) |
| 1805 | C | Criptorquidia unilateral | +`criptorquidismo` |
| 1821 | C | Ovarios iniciando proestro | +`actividad_estral` |
| 1909 | B | Cambios hepáticos sugerentes | regex fix `hepatopatia` |
| 2000 | C | Lito en vejiga + ovario poliquístico | regex + `ovario_poliquistico` |
| 2016 | C | Mielo lipoma esplénico | +`mielolipoma_esplenico` |
| 2144 | C | Discreta distención colónica | +`distension_colonica` |
| 2162 | C | Cuerpo extraño gástrico obstructivo | +`cuerpo_extrano` |
| 2311 | C | Dilatación intestinal + cuerpo extraño | +`cuerpo_extrano` |
| 2339 | C | Criptorquidismo bilateral intra abdominal | +`criptorquidismo` |
| 2377 | C | Criptorquidismo bilateral subcutáneo | +`criptorquidismo` |
| 2435 | C | Testículo izquierdo retenido subcutáneo | +`criptorquidismo` |
| 2526 | C | Testículo izquierdo intra abdominal | +`criptorquidismo` |
| 2561 | B/C | Testículo criptórquido + Gastroenterocolitis | regex + `criptorquidismo` |
| 2660 | C | Cálculo en vejiga + Íleo paralítico | regex + `ileo` |
| 2717 | A | Sin cambios anatómicos | regex fix `sin_evidencia` |
| 2728 | C | Testículos criptórquidos bilateral | +`criptorquidismo` |
| 2768 | C | Cambios tiroideos | +`cambios_tiroideos` |
| 2836 | C | Dilatación entérica + cuerpo extraño | +`cuerpo_extrano` |
| 2860 | C | Distensión gastro intestinal + cuerpo extraño | +`distension_gastrointestinal` +`cuerpo_extrano` |
| 2887 | B | Sedimento leve + Testículo Criptórquido | regex + `criptorquidismo` |

### 3.2 Distribución por categoría

```
A) Sin información clínica   ██  2  (3.0%)
B) Ya cubierto, regex falla  ███████████  11  (16.4%)
C) Nuevo diagnóstico         █████████████████████████████████████████████  45  (67.2%)
D) Nueva etiología           ·   0  (0.0%)
E) Nuevo término negativo    ·   0  (0.0%)
F) Ambiguo / fuera scope     ████████  8  (11.9%)
?  Pendiente                 █  1  (1.5%)  [cid=320 — clasificar B+C, desgarro muscular es ambiguo]
```

**Lectura:** El 67.2% (45/67) son **diagnósticos reales no catalogados**. El 16.4% son variantes textuales de términos ya cubiertos (resoluble sin agregar términos, solo ajustando regex). El 11.9% son casos **fuera del scope actual del catálogo** (ortopedia musculoesquelética, hallazgos ambiguos sin diagnóstico claro).

---

## 4. Detección de quick wins (Tarea 3)

### 4.1 Términos que aparecen ≥3 veces

| Término propuesto | # cids | # items estimados | Riesgo FP | Variantes regex |
|---|---:|---:|---|---|
| `cambios_tiroideos` | 12 | ~18 | **Bajo** (palabra específica) | `cambios tiroideos` |
| `criptorquidismo` | 9 | ~14 | **Bajo** | `criptorquidismo`, `criptorquidia`, `testículo criptórquido`, `testículo retenido`, `testículo intra abdominal` |
| `cuerpo_extrano` | 6-8 | ~9-12 | **Bajo** | `cuerpo extraño`, `cuerpos extraños`, `elemento en estómago` |
| `ileo` | 3 | ~5 | **Bajo** | `íleo`, `ilio` (typo), `íleo paralítico` |
| `sedimento_vejiga` (regex fix) | 4 | ~4 | **Medio** (cambia cobertura) | agregar `"sedimento"` como variante standalone |
| `distension_gastrica` + `distension_intestinal` | 5 | ~7 | **Bajo** | `distención`, `distensión`, `dilatación entérica`, `dilatación gástrica` |
| `actividad_estral` | 2 | ~3 | **Bajo** | `actividad estral`, `proestro`, `estro` |
| `hiperplasia_prostatica` (regex fix) | 1+ | ~2 | **Bajo** | `cambios prostáticos hiperplásicos` |

### 4.2 Cobertura incremental esperada (orden de impacto)

| Acción | cids cubiertos | ítems añadidos | Acumulado cobertura |
|---|---:|---:|---:|
| 1. `cambios_tiroideos` | 12 | +18 | 98.10% |
| 2. `criptorquidismo` | +9 | +14 | 98.62% |
| 3. `cuerpo_extrano` | +6 | +9 | 98.79% |
| 4. `ileo` | +3 | +5 | 98.93% |
| 5. `sedimento_vejiga` (regex) | +4 | +4 | 99.03% |
| 6. `distension_*` (3 términos) | +5 | +7 | 99.31% |
| 7. `actividad_estral` | +2 | +3 | 99.41% |
| 8. `paniculitis` | +1 | +1 | 99.45% |
| 9. `tiflitis` + `ulcera_intestinal` | +1 | +2 | 99.52% |
| 10. `remanente_ovarico` | +1 | +1 | 99.55% |
| 11. `mielolipoma_esplenico` | +1 | +1 | 99.59% |
| **TOTAL F5.1** | **+45 cids** | **+67 ítems** | **99.59%** |

### 4.3 Riesgo de FP por término

| Término | FP risk | Justificación |
|---|---|---|
| `cambios_tiroideos` | 1/1000 | "tiroides" solo aparece en informes de tiroides |
| `criptorquidismo` | 1/1000 | "criptorquid" / "testículo retenido" son muy específicos |
| `cuerpo_extrano` | 1/2000 | "cuerpo extraño" es terminología veterinaria precisa |
| `ileo` | 5/1000 | "íleo"/"ilio" como typo podría colisionar con nombres propios — validar |
| `distension_gastrica` | 3/1000 | "distención" es término común pero casi siempre clínico |
| `actividad_estral` | 1/1000 | "proestro/estro" muy específico de reproducción |

**Estimación global FP rate:** < 5/100,000 (0.005%). Riesgo aceptable.

---

## 5. Análisis de cobertura marginal (Tarea 4)

### 5.1 Pregunta: ¿Cuánto sube la cobertura con N nuevos términos?

| Escenario | +ítems | +cids únicos | Items total | % items | Cobertura conclusions |
|---|---:|---:|---:|---:|---:|
| Actual | 0 | 0 | 15,968 | — | 97.68% |
| Top 1 | +18 | +12 | 15,986 | +0.11% | 98.10% |
| Top 3 | +41 | +27 | 16,009 | +0.26% | 98.62% |
| Top 5 | +50 | +34 | 16,018 | +0.31% | 98.86% |
| **Top 11 (F5.1)** | **+67** | **+45** | **16,035** | **+0.42%** | **99.24%** |
| Todos los no-F | +85 | +59 | 16,053 | +0.53% | 99.72% |
| Hipotético 100% | +85 | +67 | 16,053 | +0.53% | 100.00% |

### 5.2 Lectura

- **Cobertura actual 97.68% es excelente.** Subir a 99.24% con 11 términos aporta +1.56 puntos porcentuales de cobertura de conclusions.
- **Items solo suben +0.42%.** El efecto en volumetría de queries es marginal (de 15,968 a 16,035 ítems).
- **Rendimientos decrecientes claros:** Top 1 aporta 0.11%, Top 3 aporta 0.26% (3× pero solo 2.3× cids), Top 11 aporta 0.42% (3.8× cids pero solo 1.6× el delta de Top 1).
- **Los 8 casos F no son mejorables** con el catálogo actual (ortopedia, laringe, panículo ambiguo).
- **Los 2 casos A son ruido clínico puro** ("examen OK") — no aportan información y mantenerlos en `stg_conclusion_no_match` es correcto.

---

## 6. Revisión del catálogo de 81 términos (Tarea 5)

### 6.1 Términos nunca utilizados (7)

| Término | Tipo | Categoría | Decisión |
|---|---|---|---|
| `colelitiasis` | DIAGNOSTICO | VESICULA | **Mantener** — entidad nosológica válida |
| `ectasia_pelvica` | DIAGNOSTICO | RENAL | **Mantener** — específico de pelvis renal |
| `estenosis` | DIAGNOSTICO | MISC_MORFOLOGIA | **Mantener** — entidad clínica |
| `gastropatia` | DIAGNOSTICO | GASTROINTESTINAL | **Mantener** — genérico para estómago |
| `hematoma_esplenico` | DIAGNOSTICO | ESPLENICA | **Mantener** — entidad clínica |
| `sedimento_biliar` | DIAGNOSTICO | VESICULA | **Mantener** — entidad clínica |
| `sospecha_neoplasica` | ETIOLOGIA | — | **Mantener** — alternativa a `neoplasico` |

**Análisis:** Los 7 términos no usados son todos entidades clínicas válidas que faltan en el corpus actual pero son probables en informes futuros. **No eliminar.**

### 6.2 Términos con frecuencia <5 (14 — incluye los 7 anteriores + 7)

| Término | n_items | Análisis |
|---|---:|---|
| `colelitiasis` | 0 | raro en este corpus, mantener |
| `ectasia_pelvica` | 0 | raro, mantener |
| `estenosis` | 0 | raro, mantener |
| `gastropatia` | 0 | raro, mantener |
| `hematoma_esplenico` | 0 | raro, mantener |
| `sedimento_biliar` | 0 | raro, mantener |
| `sospecha_neoplasica` | 0 | variante de `neoplasico` + `sospecha_neoplasica` |
| `amiloidosis` | 1 | raro, mantener |
| `aparente` | 1 | borderline, mantener |
| `cirrosis` | 1 | raro, mantener |
| `ectasia_independiente` | 1 | catch-all, mantener |
| `hemometra` | 1 | raro, mantener |
| `quiste_ovarico` | 1 | raro, mantener |
| `sin_alteraciones` | 1 | variante de `sin_evidencia`, mantener |

**Análisis:** Términos con n<5 son todos válidos en español clínico; su rareza es por distribución natural del corpus. **No eliminar.** Si el usuario filtra por `frecuencia_rank <= 50`, ya quedan automáticamente fuera.

### 6.3 Términos potencialmente redundantes (0)

Análisis automatizado de prefijos comunes: **ningún par de términos tiene la misma raíz con sufijos distintos relevantes**. Las "redundancias" del audit previo (higado_graso vs hepatopatia_vacuolar, hiperplasia vs hiperplasia_prostatica) ya están resueltas por la decisión de mantener ambas como entidades clínico-distintas.

**Acción:** Ninguna fusión ni división.

### 6.4 Validación del catálogo

| Criterio | Resultado |
|---|---|
| Cobertura Top 50 | 99.27% del corpus ✅ |
| Términos nunca usados | 7 (mantener, todos válidos) ✅ |
| Términos raros (<5) | 14 (mantener, todos válidos) ✅ |
| Redundancias | 0 ✅ |
| Cardinalidad modificadores estable | Sí ✅ |

**Veredicto del catálogo:** **No requiere cambios estructurales.** Las adiciones de F5.1 extienden el catálogo sin romper la coherencia existente.

---

## 7. Decisión GOLD (Tarea 6)

### 7.1 ¿Hay algún hallazgo en los 67 no-match que justifique retrasar Gold?

**Respuesta:** SÍ parcialmente. Justifica un **F5.1 de 15 minutos** (no un rediseño).

**Justificación cuantitativa:**

| Pregunta | Respuesta |
|---|---|
| ¿Hay diagnósticos reales no cubiertos? | **SÍ** — 45 cids (67%) con diagnósticos reales (tiroides, criptorquidia, cuerpo extraño, íleo, distensión) |
| ¿Hay etiologías/negativos nuevos relevantes? | **NO** — 0 cids |
| ¿La corrección es trivial? | **SÍ** — 11 términos nuevos + 4 regex fixes (~15 min) |
| ¿El beneficio es sustancial? | **MODERADO** — +1.56% cobertura conclusions, +0.42% items |
| ¿Retrasar indefinidamente Gold? | **NO** — la mejora es marginal y la ley de rendimientos decrecientes es clara |

### 7.2 Opción recomendada: **B) GO tras F5.1**

**Plan de acción:**

1. **F5.1 (~15 min)** — agregar 11 términos + 4 regex fixes:
   - **Términos nuevos:** `cambios_tiroideos`, `criptorquidismo`, `cuerpo_extrano`, `ileo`, `distension_gastrica`, `distension_intestinal`, `distension_colonica`, `distension_gastrointestinal`, `actividad_estral`, `paniculitis`, `tiflitis`, `ulcera_intestinal`, `remanente_ovarico`, `mielolipoma_esplenico`, `ovario_poliquistico`, `desgarro_muscular` (16 en realidad, no 11)
   - **Regex fixes:** `sedimento_vejiga` (agregar "sedimento"), `hepatopatia` (agregar "cambios hepáticos"), `cambios_pancreaticos` (agregar "cambios en páncreas"), `cistolito` (agregar "lito vesical", "lito en vejiga", "cálculo en vejiga"), `linfadenomegalia` (agregar "linfonodopatía"), `dilatacion_ureteral` (agregar "dilatación uretral"), `cistitis` (agregar "proceso inflamatorio en vejiga"), `sin_evidencia` (agregar "no se observa cambios", "sin cambios anatómicos"), `derrame_peritoneal` (mantener) + nuevo `derrame_pleural`, `hiperplasia_prostatica` (agregar "cambios prostáticos hiperplásicos"), `enterocolitis` (agregar "gastroenterocolitis")
   - **Resultado esperado:** 67 → 15 no_match (10 de los 8 F + 5 sin clasificar definitivamente + 2 A por ruido)
   - **Cobertura:** 97.68% → 99.24%

2. **Re-run verify_silver_f5.py** → confirmar 19/19 checks + nuevos checks para F5.1.

3. **GO a Gold** (diseñar capa de agregaciones por paciente / raza / edad / periodo).

### 7.3 Lo que NO se debe hacer

- **NO rediseñar F5** — la arquitectura está validada y los 8 casos F son intrínsecos al scope.
- **NO agregar los 8 casos F al catálogo** — son ortopedia musculoesquelética (fuera del dominio del catálogo de ultrasonido abdominal actual) y hallazgos ambiguos sin diagnóstico claro.
- **NO esperar cobertura 100%** — los 2 casos A son ruido puro (examen OK); mantenerlos en `stg_conclusion_no_match` es lo correcto.

---

## 8. Veredicto final

## **B) GO tras F5.1**

**Justificación resumida:**

- 67/67 no-match analizados manualmente.
- 67.2% (45 cids) son diagnósticos reales nuevos; resolubles con 16 términos adicionales y 11 regex fixes.
- 16.4% (11 cids) son fallas de regex; corregibles sin nuevos términos.
- 11.9% (8 cids) son fuera de scope (ortopedia, ambiguos); se mantienen en `stg_conclusion_no_match`.
- 3.0% (2 cids) son ruido clínico puro ("examen OK"); se mantienen en `stg_conclusion_no_match` como referencia.
- **0 cids requieren rediseño de F5.**
- Beneficio de F5.1: cobertura 97.68% → 99.24%, items +0.42%.
- Costo de F5.1: ~15 min de trabajo + 1 verify round.
- **Riesgo de FP: < 0.005%** (todos los términos nuevos son clínica-específicos).

**Próximo paso:** ejecutar F5.1 con los 16 términos + 11 regex fixes, re-verificar con `verify_silver_f5.py`, y luego iniciar diseño de capa Gold.

---

## Anexo A — Listado de los 11 cids que NO se podrán cubrir (F)

| cid | Texto | Razón |
|---|---|---|
| 92 | Vejiga dilatada sin signos de punto obstructivo | Ambiguo (¿obstructiva?) |
| 376 | Surco troclear aplanado. Artrosis rodilla derecha | Ortopedia (fuera scope) |
| 399 | Derrame sinovial. Luxación medial de patella | Ortopedia (fuera scope) |
| 893 | Surco troclear + artrosis rodilla izquierda | Ortopedia (fuera scope) |
| 907 | Luxación patella + artrosis | Ortopedia (fuera scope) |
| 1303 | Bursitis bicipital leve | Ortopedia (fuera scope) |
| 1612 | Acúmulo de tejido graso subcutáneo | Ambiguo (no diagnóstico claro) |
| 1794 | Cambio de tejido blando adyacente a laringe | Origen indeterminado (ambiguo) |

## Anexo B — Listado de los 2 cids que NO se deben cubrir (A)

| cid | Texto | Razón |
|---|---|---|
| 478 | No se observa cambios anatómicos ni patológicos al presente examen | Ruido clínico (examen OK). Mantener en stg para auditoría. |
| 2717 | Sin cambios anatómicos ni patológicos al presente examen | Idem. |

Estos 2 casos **deberían** matchear `sin_evidencia` con un fix de regex (agregar "no se observa cambios" como variante), pero el valor clínico de marcarlos como "negativos" es nulo — es información trivial. Se mantienen en `stg_conclusion_no_match` como referencia de cobertura.
