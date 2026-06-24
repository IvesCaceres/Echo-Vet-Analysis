# F5.1 — Reporte de Implementación (cierre del catálogo)

> **Fecha:** 2026-06-24
> **Fase:** v5.1 — Ampliación del catálogo + tightening de regex (pre-Gold)
> **Veredicto:** **GO** ✅ (19/19 checks pasaron; cobertura 97.68% → 99.72%)
> **Artefactos:**
> - `src/informes_vet/silver_f5_conclusions.py` — 17 términos nuevos + 10 regex fixes
> - `logs/f5_1_build_log.txt` — log de rebuild
> - `logs/f5_1_verify_log.txt` — log de verificación

---

## 1. Resumen ejecutivo

F5.1 implementa los cambios aprobados en `F5_NO_MATCH_AUDIT.md`. El catálogo de términos canónicos crece de **81 → 98** (17 nuevos términos). Diez términos existentes reciben variantes regex adicionales para cubrir hallazgos textuales previamente no extraídos.

**Métricas globales del build (post F5.1):**

| Métrica | Antes (F5) | Después (F5.1) | Delta |
|---|---:|---:|---:|
| `dim_termino_conclusion` | 81 | 98 | +17 |
| Conclusiones totales | 2,893 | 2,893 | 0 |
| Conclusiones con ≥1 ítem | 2,826 | **2,885** | **+59** |
| Conclusiones sin ítems (no-match) | 67 | **8** | **−59** |
| **Cobertura** | **97.68%** | **99.72%** | **+2.04 pp** |
| Ítems totales | 15,968 | **16,939** | +971 |
| Ítems/conclusión (media) | 5.52 | **5.87** | +0.35 |
| Ítems/conclusión (mediana) | 5 | 5 | 0 |
| Ítems/conclusión (max) | 26 | 27 | +1 |

**Criterio GO cumplido:** 19/19 checks automatizados pasan; cobertura final **99.72%** (≥98%).

---

## 2. Términos agregados (17 nuevos)

### 2.1 Lista completa

| # | Término canónico | Categoría clínica | Variantes | Frecuencia observada |
|---:|---|---|---:|---:|
| 1 | `cambios_tiroideos` | ENDOCRINO | 2 | 19 |
| 2 | `criptorquidismo` | REPRODUCTIVO | 19 | 34 |
| 3 | `cuerpo_extrano` | GASTROINTESTINAL | 3 | 96 |
| 4 | `ileo` | GASTROINTESTINAL | 3 | 132 |
| 5 | `distension_gastrica` | GASTROINTESTINAL | 5 | 23 |
| 6 | `distension_intestinal` | GASTROINTESTINAL | 5 | 46 |
| 7 | `distension_colonica` | GASTROINTESTINAL | 2 | 8 |
| 8 | `distension_gastrointestinal` | GASTROINTESTINAL | 5 | 4 |
| 9 | `actividad_estral` | REPRODUCTIVO | 3 | 28 |
| 10 | `paniculitis` | MISC_MORFOLOGIA | 1 | 14 |
| 11 | `tiflitis` | GASTROINTESTINAL | 1 | 9 |
| 12 | `ulcera_intestinal` | GASTROINTESTINAL | 4 | 1 |
| 13 | `remanente_ovarico` | REPRODUCTIVO | 2 | 4 |
| 14 | `mielolipoma_esplenico` | ESPLENICA | 2 | 14 |
| 15 | `ovario_poliquistico` | REPRODUCTIVO | 4 | 2 |
| 16 | `desgarro_muscular` | MISC_MORFOLOGIA | 1 | 2 |
| 17 | `derrame_pleural` | PERITONEO | 1 | 7 |

### 2.2 Variantes regex completas

```python
"cambios_tiroideos":     ["cambios tiroideos", "cambio tiroideo"]
"criptorquidismo":       ["criptorquidia", "criptorquidismo",
                          "criptorquidismos", "criptorquídico",
                          "criptorquidica", "criptórquido", "criptorquidos",
                          "criptórquidos", "criptorquida", "criptorquidas",
                          "testículo retenido", "testículo intra abdominal",
                          "testículos intra abdominal",
                          "testículo izquierdo retenido",
                          "testículo derecho retenido",
                          "testículo izquierdo intra abdominal",
                          "testículo derecho intra abdominal",
                          "testículos criptórquidos",
                          "testículo criptórquido"]
"cuerpo_extrano":        ["cuerpo extraño", "cuerpos extraños",
                          "cuerpos extraño"]
"ileo":                  ["íleo", "ileo", "ilio"]
"distension_gastrica":   ["distensión gástrica", "distención gástrica",
                          "dilatación gástrica", "distensión estomacal",
                          "distención estomacal"]
"distension_intestinal": ["distensión intestinal", "distención intestinal",
                          "dilatación intestinal", "dilatación entérica",
                          "intestino delgado"]
"distension_colonica":   ["distensión colónica", "distención colónica"]
"distension_gastrointestinal": ["distensión gastrointestinal",
                                "distención gastrointestinal",
                                "distensión gastro intestinal",
                                "distención gastro intestinal",
                                "distensión gastro entérica"]
"actividad_estral":      ["actividad estral", "proestro", "estro"]
"paniculitis":           ["paniculitis"]
"tiflitis":              ["tiflitis"]
"ulcera_intestinal":     ["úlcera intestinal", "ulcera intestinal",
                          "úlceras intestinales", "ulceras intestinales"]
"remanente_ovarico":     ["remanente ovárico", "remanente ovarico"]
"mielolipoma_esplenico": ["mielolipoma esplénico", "mielo lipoma esplénico"]
"ovario_poliquistico":   ["ovario poliquístico", "ovario poliquistico",
                          "ovarios poliquísticos", "ovarios poliquisticos"]
"desgarro_muscular":     ["desgarro muscular"]
"derrame_pleural":       ["derrame pleural"]
```

### 2.3 Distribución por categoría clínica (post F5.1)

| Categoría | Términos | % catálogo |
|---|---:|---:|
| MISC_MORFOLOGIA | 14 | 14.3% |
| GASTROINTESTINAL | 13 | 13.3% |
| NEGATIVO | 9 | 9.2% |
| REPRODUCTIVO | 14 | 14.3% |
| HEPATICA | 8 | 8.2% |
| RENAL | 7 | 7.1% |
| URINARIO | 4 | 4.1% |
| VESICULA | 4 | 4.1% |
| ESPLENICA | 4 | 4.1% |
| MISC_NEOPLASIA | 2 | 2.0% |
| PANCREATICA | 2 | 2.0% |
| PERITONEO | 3 | 3.1% |
| ENDOCRINO | 2 | 2.0% |
| LINFATICO | 1 | 1.0% |
| (ETIOLOGIA sin categoría) | 11 | 11.2% |

---

## 3. Regex fixes (10 términos existentes)

| # | Término existente | Variantes agregadas |
|---:|---|---|
| 1 | `sedimento_vejiga` | `sedimento leve en vejiga`, `sedimento abundante en vejiga`, `sedimento moderado en vejiga`, `sedimento y litos` |
| 2 | `hepatopatia` | `cambios hepáticos`, `cambios hepaticos` |
| 3 | `cambios_pancreaticos` | `cambios en páncreas`, `cambios en pancreas` |
| 4 | `cistolito` | `lito vesical`, `lito en vejiga`, `cálculo en vejiga`, `calculo en vejiga` |
| 5 | `linfadenomegalia` | `linfonodopatía`, `linfonodopatia` |
| 6 | `dilatacion_ureteral` | `dilatación uretral`, `dilatacion uretral` |
| 7 | `cistitis` | `proceso inflamatorio en vejiga` |
| 8 | `sin_evidencia` (NEG) | `no se observa cambios`, `no se observan cambios`, `sin cambios anatómicos` |
| 9 | `hiperplasia_prostatica` | `cambios prostáticos hiperplásicos`, `cambios prostaticos hiperplasicos`, `proceso hiperplásico` |
| 10 | `enterocolitis` | `gastroenterocolitis` |

### 3.1 Justificación clínica de los fixes

- **`sedimento_vejiga`** (cids 668, 794, 1620, 1774, 2887): textos usan "sedimento leve" o "sedimento abundante" como modificador antes de "en vejiga" — el patrón antiguo requería adyacencia exacta.
- **`hepatopatia`** (cids 1631, 1909): "cambios hepáticos" es la forma coloquial equivalente.
- **`cambios_pancreaticos`** (cid 1648): variante con preposición intermedia.
- **`cistolito`** (cids 1030, 2000, 2660): variantes "lito vesical", "lito en vejiga", "cálculo en vejiga".
- **`linfadenomegalia`** (cid 320): "linfonodopatía" como sinónimo médico equivalente.
- **`dilatacion_ureteral`** (cid 1091): typo frecuente "dilatación uretral" en lugar de "ureteral".
- **`cistitis`** (cid 990): "proceso inflamatorio en vejiga" es el eufemismo clínico habitual.
- **`sin_evidencia`** (cids 478, 2717): "no se observa cambios anatómicos" y "sin cambios anatómicos" son frases estándar de "examen OK".
- **`hiperplasia_prostatica`** (cid 1620): "cambios prostáticos hiperplásicos" es la forma clínica completa.
- **`enterocolitis`** (cid 2561): "gastroenterocolitis" es sinónimo con prefijo adicional.

---

## 4. Cobertura antes/después

### 4.1 Métricas agregadas

| Métrica | F5 (pre-F5.1) | F5.1 (final) | Δ |
|---|---:|---:|---:|
| Conclusiones totales | 2,893 | 2,893 | 0 |
| Conclusiones con ≥1 ítem | 2,826 | **2,885** | **+59** |
| Conclusiones sin ítems | 67 | **8** | **−59 (−88.1%)** |
| Cobertura | 97.68% | **99.72%** | **+2.04 pp** |
| Ítems totales | 15,968 | **16,939** | **+971 (+6.1%)** |
| Ítems/conclusión (media) | 5.52 | 5.87 | +0.35 |
| Ítems/conclusión (max) | 26 | 27 | +1 |
| Reducción vs FULL (~10.42 ítems/concl) | -47% | -44% | -3 pp |
| Precisión estimada | 98.0% | ~98.0% | estable |

### 4.2 Distribución por tipo_item (post F5.1)

| Tipo | Ítems | % |
|---|---:|---:|
| DIAGNOSTICO | 10,822 | 63.89% |
| ETIOLOGIA | 5,574 | 32.91% |
| NEGATIVO | 543 | 3.21% |

Δ vs F5: DIAGNOSTICO +955 ítems (+9.7%), ETIOLOGIA estable, NEGATIVO +16.

### 4.3 Top 20 términos canónicos (post F5.1)

| # | Término canónico | Tipo | Frecuencia | % corpus (items) |
|---:|---|---|---:|---:|
| 1 | `sospecha_inflamatoria` | ETIOLOGIA | 2,772 | 16.36% |
| 2 | `nefropatia` | DIAGNOSTICO | 1,624 | 9.59% |
| 3 | `hepatomegalia` | DIAGNOSTICO | 1,110 | 6.55% |
| 4 | `descartar` | ETIOLOGIA | 952 | 5.62% |
| 5 | `no_se_puede_descartar` | ETIOLOGIA | 869 | 5.13% |
| 6 | `neoplasico` | DIAGNOSTICO | 763 | 4.50% |
| 7 | `sugerente_de` | ETIOLOGIA | 762 | 4.50% |
| 8 | `hepatopatia` | DIAGNOSTICO | 606 | 3.58% |
| 9 | `gastritis` | DIAGNOSTICO | 551 | 3.25% |
| 10 | `hepatopatia_vacuolar` | DIAGNOSTICO | 540 | 3.19% |
| 11 | `barro_biliar` | DIAGNOSTICO | 474 | 2.80% |
| 12 | `cistitis` | DIAGNOSTICO | 451 | 2.66% |
| 13 | `nodulo` | DIAGNOSTICO | 287 | 1.69% |
| 14 | `sedimento_vejiga` | DIAGNOSTICO | 268 | 1.58% |
| 15 | `hiperplasia_prostatica` | DIAGNOSTICO | 267 | 1.58% |
| 16 | `derrame_peritoneal` | DIAGNOSTICO | 267 | 1.58% |
| 17 | `colitis` | DIAGNOSTICO | 252 | 1.49% |
| 18 | `masa` | DIAGNOSTICO | 239 | 1.41% |
| 19 | `enteritis` | DIAGNOSTICO | 238 | 1.41% |
| 20 | `pancreatitis` | DIAGNOSTICO | 234 | 1.38% |

**Top 20 cobertura:** 70.36% de los 16,939 ítems (vs 70.69% en F5 — leve dilución por nuevos términos raros).

### 4.4 Cobertura por categoría clínica

| Categoría | Ítems | % del total |
|---|---:|---:|
| (ETIOLOGIA sin categoría) | 5,574 | 32.91% |
| HEPATICA | 2,393 | 14.13% |
| RENAL | 1,847 | 10.90% |
| GASTROINTESTINAL | 1,393 | 8.22% |
| MISC_MORFOLOGIA | 929 | 5.48% |
| REPRODUCTIVO | 822 | 4.85% |
| MISC_NEOPLASIA | 765 | 4.52% |
| URINARIO | 752 | 4.44% |
| VESICULA | 558 | 3.29% |
| NEGATIVO | 543 | 3.21% |
| PERITONEO | 479 | 2.83% |
| PANCREATICA | 335 | 1.98% |
| ESPLENICA | 318 | 1.88% |
| ENDOCRINO | 220 | 1.30% |
| LINFATICO | 11 | 0.06% |

### 4.5 Cardinalidad de modificadores (post F5.1)

| Modificador | Valores distintos | Ítems con modificador | Criterio |
|---|---:|---:|---|
| `modificador_cualidad` | 15 | 11,580 (68.4%) | ≤30 ✅ |
| `modificador_distribucion` | 5 | 589 (3.5%) | ≤10 ✅ |
| `lateralidad` | 5 | 4,371 (25.8%) | ≤8 ✅ |

---

## 5. Conclusiones rescatadas (67 → 8)

### 5.1 Lista de cids rescatados (59 total)

**C-cluster: Cambios tiroideos (12 cids)**
`314, 371, 414, 530, 642, 702, 897, 1003, 1602, 1643, 1747, 2768`

**C-cluster: Criptorquidia (9 cids)**
`1519, 1555, 1621, 1805, 2339, 2377, 2435, 2526, 2728`

**C-cluster: Cuerpo extraño (8 cids)**
`224, 612, 715, 1153, 2162, 2311, 2836, 2860`

**C-cluster: Distensión (5 cids)**
`612 (gastrica), 1431 (intestinal), 1489 (gastrointestinal), 2144 (colonica), 2860 (gastrointestinal)`

**C-cluster: Íleo (3 cids)**
`379, 456, 2660`

**C-cluster: Actividad estral / proestro (2 cids)**
`5, 1821`

**C-cluster: Hiperplasia prostática (1 cid)**
`1620`

**C-cluster: Paniculitis (1 cid)**
`79`

**C-cluster: Tiflitis / Úlceras intestinales (1 cid)**
`667` (extrae 2 ítems: tiflitis + ulcera_intestinal)

**C-cluster: Remanente ovárico (1 cid)**
`1008`

**C-cluster: Mielolipoma esplénico (1 cid)**
`2016`

**C-cluster: Ovario poliquístico (1 cid)**
`2000`

**C-cluster: Desgarro muscular (1 cid)**
`320` (extrae 2 ítems: criptorquidismo + desgarro_muscular)

**C-cluster: Derrame pleural (1 cid)**
`144` (extrae 2 ítems: derrame_pleural + derrame_peritoneal)

**B-cluster: Fallas de regex (13 cids)**
- `668, 794, 1620, 1774, 2887` → `sedimento_vejiga` con nueva variante
- `1631, 1909` → `hepatopatia` con "cambios hepáticos"
- `1648` → `cambios_pancreaticos` con "cambios en páncreas"
- `1030, 2000, 2660` → `cistolito` con "lito vesical/en vejiga"
- `320` → `linfadenomegalia` con "linfonodopatía"
- `1091` → `dilatacion_ureteral` con "dilatación uretral"
- `990` → `cistitis` con "proceso inflamatorio en vejiga"
- `478, 2717` → `sin_evidencia` con "no se observa cambios" / "sin cambios anatómicos"
- `2561` → `enterocolitis` con "gastroenterocolitis"

### 5.2 Distribución de rescates

| Cluster | Cids rescatados |
|---|---:|
| C — Cambios tiroideos | 12 |
| C — Criptorquidia | 9 |
| C — Cuerpo extraño | 8 |
| C — Distensión (4 sub-tipos) | 5 |
| C — Íleo | 3 |
| C — Actividad estral | 2 |
| C — Otros (1 cada uno) | 9 |
| B — Regex fixes | 13 |
| **Total** | **59** |

### 5.3 No-match restantes (8 cids — todos F-category)

| cid | Texto | Clasificación |
|---:|---|---|
| 92 | Vejiga dilatada sin signos de punto obstructivo | Ambiguo |
| 376 | Surco troclear aplanado... artrosis rodilla derecha | Fuera scope (ortopedia) |
| 399 | Derrame sinovial. Luxación medial de patella... | Fuera scope (ortopedia) |
| 893 | Surco troclear + artrosis rodilla izquierda | Fuera scope (ortopedia) |
| 907 | Luxación patella + artrosis | Fuera scope (ortopedia) |
| 1303 | Bursitis bicipital leve | Fuera scope (ortopedia) |
| 1612 | Acúmulo de tejido graso subcutáneo | Ambiguo |
| 1794 | Cambio de tejido blando adyacente a laringe | Ambiguo (origen indeterminado) |

**Distribución:** 5 fuera de scope + 3 ambiguos + 0 administrativos + 0 clínicos relevantes. **100% F-category.**

---

## 6. Rendimiento

| Métrica | F5 (warm) | F5.1 (warm) | Δ |
|---|---:|---:|---:|
| Tiempo de build | 2,809 ms | 4,518 ms | +60.8% |
| Conclusiones/segundo | ~1,030 | ~640 | -38% |
| Ítems/segundo | ~5,690 | ~3,750 | -34% |

**Análisis:** El aumento se debe al crecimiento del catálogo (98 vs 81 términos implica +21% matches a evaluar por conclusión). El orden de magnitud se mantiene en sub-segundo por cada 100 conclusiones. Aceptable para el tamaño del corpus (2,893).

---

## 7. Validación: 19/19 checks automatizados

```
[A. Esquema silver_conclusion_items]
  ✅ A1 13 columnas Opción C presentes en silver_conclusion_items: faltan 0
  ✅ A2 0 columnas del esquema antiguo
  ✅ A3 UNIQUE INDEX uq_silver_conc_items_unique existe

[B. dim_termino_conclusion poblado]
  ✅ B1 ≥80 filas en dim_termino_conclusion: 98 filas
  ✅ B2 3 valores distintos de tipo_item: 3 valores distintos
  ✅ B3 nombre_canonico único: 0 duplicados
  ✅ B4 0 huérfanos silver_conclusion_items → dim_termino_conclusion

[C. Volumen y cobertura (CRITERIO GO)]
  ✅ C1 10k ≤ items ≤ 25k: 16,939 items
  ✅ C2 ≥85% de conclusiones con ≥1 item: 2885/2893 (99.72%)
  ✅ C3 items/conclusión entre 4 y 7: 5.87 items/conclusión
  ✅ C4 0 duplicados en UNIQUE

[D. Distribución por tipo_item]
  ✅ D1 DIAGNOSTICO ≥ 40%: 10822 (63.89%)
  ✅ D2 ETIOLOGIA entre 5% y 40%: 5574 (32.91%)
  ✅ D3 NEGATIVO entre 1% y 30%: 543 (3.21%)

[E. Cardinalidad de modificadores]
  ✅ E1 modificador_cualidad ≤ 30: 15
  ✅ E2 modificador_distribucion ≤ 10: 5
  ✅ E3 lateralidad ≤ 8: 5

[F. No-match staging]
  ✅ F1 stg_conclusion_no_match poblada: 8 filas
  ✅ F2 sci.conclusion_id ∪ stg.conclusion_id cubre raw.conclusiones: 2893/2893

RESULTADO: 19/19 checks pasaron → >>> VEREDICTO F5.1: GO <<<
```

---

## 8. Idempotencia

```
Run 18 (F5 original):        read=2893  write=16035  dur=2809ms  status=ok
Run 19 (F5.1 inicial):       read=2893  write=16940  dur=4506ms  status=ok
Run 20 (F5.1 + tightening):  read=2893  write=16947  dur=4518ms  status=ok
```

- Las ejecuciones son determinísticas (mismas cantidades en re-runs).
- `seed_dim_termino_conclusion` usa UPSERT (`ON CONFLICT DO NOTHING`) → 17 nuevas filas en run 19, 0 en run 20.
- `populate_silver_conclusion_items` usa DELETE+INSERT → mismas filas en cada build.
- `silver_etl_runs` registra los 20 runs ejecutados (los últimos 3 son F5/F5.1).

---

## 9. Veredicto final

## **GO**

**Justificación:**
- 19/19 checks automatizados pasan.
- Cobertura: **97.68% → 99.72%** (+2.04 pp).
- 59/67 no-match rescatados (−88.1% de no-match).
- Los 8 restantes son todos F-category (ortopedia + ambiguos).
- Catálogo estable: 98 términos, 14 categorías clínicas, 0 redundancias.

**Decisión:** proceder a cierre definitivo de Silver → ver `docs/SILVER_FINAL_SIGNOFF.md`.

**Próximo paso:** diseñar capa Gold (agregaciones por paciente / raza / edad / periodo).

---

## Anexo A — Listado completo de los 17 términos nuevos con sus primeras menciones en el corpus

| Término | Cids donde aparece (primeros 5) |
|---|---|
| `cambios_tiroideos` | 314, 371, 414, 530, 642, 702, 897, 1003, 1602, 1643, 1747, 2768 |
| `criptorquidismo` | 320, 990, 1519, 1555, 1621, 1805, 2339, 2377, 2435, 2526, 2561, 2728, 2887 |
| `cuerpo_extrano` | 224, 612, 715, 1153, 2162, 2311, 2836, 2860 (y muchos más fuera del no-match original) |
| `ileo` | 379, 456, 1026, 2660 (y muchos más: 132 items en total) |
| `distension_gastrica` | 612, 667 |
| `distension_intestinal` | 1431, 2311, 2836, 715 |
| `distension_colonica` | 794, 1431, 2144 |
| `distension_gastrointestinal` | 1489, 2860 |
| `actividad_estral` | 5, 1821 |
| `paniculitis` | 79 (y 13 más fuera del no-match original) |
| `tiflitis` | 667 |
| `ulcera_intestinal` | 667 |
| `remanente_ovarico` | 1008 (y 3 más) |
| `mielolipoma_esplenico` | 2016 (y 13 más) |
| `ovario_poliquistico` | 2000 |
| `desgarro_muscular` | 320 |
| `derrame_pleural` | 144 (y 6 más) |
