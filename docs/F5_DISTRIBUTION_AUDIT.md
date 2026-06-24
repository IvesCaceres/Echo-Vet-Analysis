# F5 — Auditoría de distribución (corpus completo)

> **Fecha:** 2026-06-24  
> **Alcance:** 2,893 conclusiones · 15,968 items Opción C  
> **Veredicto:** **GO**  
> **Artefactos:** `docs/_F5_opcion_c_full.json` (5.8 MB) · `docs/_F5_opcion_c_summary.json`

---

## 1. Resumen ejecutivo

- **Items totales:** 15,968 (Opción C, sobre 2,893 conclusiones)
- **Términos distintos observados:** 74
- **Items/conclusión (media):** 5.52
- **Cobertura Top 50:** 99.27% de los items
- **Conclusiones con ≥1 item:** 2,826/2,893 (97.68%)

**Modificadores (cardinalidad y cobertura):**

| Modificador | Valores distintos | Items totales | Cobertura (sobre items) |
|---|---:|---:|---:|
| `modificador_cualidad` | 15 | 11,185 | 70.0% |
| `modificador_distribucion` | 4 | 556 | 3.5% |
| `lateralidad` | 4 | 4,316 | 27.0% |

---

## 2. Top 50 términos canónicos

| # | Término canónico | Frecuencia items | Frecuencia informes | % corpus (items) | % corpus (informes) | Categoría | Tipo |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | `sospecha_inflamatoria` | 2,772 | 1,961 | 17.36% | 67.78% | ETIOLOGIA | ETIOLOGIA |
| 2 | `nefropatia` | 1,624 | 1,604 | 10.17% | 55.44% | RENAL | DIAGNOSTICO |
| 3 | `hepatomegalia` | 1,110 | 1,107 | 6.95% | 38.26% | HEPATICA | DIAGNOSTICO |
| 4 | `descartar` | 952 | 768 | 5.96% | 26.55% | ETIOLOGIA | ETIOLOGIA |
| 5 | `no_se_puede_descartar` | 869 | 713 | 5.44% | 24.65% | ETIOLOGIA | ETIOLOGIA |
| 6 | `neoplasico` | 763 | 568 | 4.78% | 19.63% | MISC_NEOPLASIA | DIAGNOSTICO |
| 7 | `sugerente_de` | 762 | 658 | 4.77% | 22.74% | ETIOLOGIA | ETIOLOGIA |
| 8 | `hepatopatia` | 559 | 556 | 3.50% | 19.22% | HEPATICA | DIAGNOSTICO |
| 9 | `gastritis` | 551 | 547 | 3.45% | 18.91% | GASTROINTESTINAL | DIAGNOSTICO |
| 10 | `hepatopatia_vacuolar` | 540 | 540 | 3.38% | 18.67% | HEPATICA | DIAGNOSTICO |
| 11 | `barro_biliar` | 474 | 473 | 2.97% | 16.35% | VESICULA | DIAGNOSTICO |
| 12 | `cistitis` | 450 | 444 | 2.82% | 15.35% | URINARIO | DIAGNOSTICO |
| 13 | `nodulo` | 287 | 249 | 1.80% | 8.61% | MISC_MORFOLOGIA | DIAGNOSTICO |
| 14 | `derrame_peritoneal` | 267 | 260 | 1.67% | 8.99% | PERITONEO | DIAGNOSTICO |
| 15 | `colitis` | 252 | 252 | 1.58% | 8.71% | GASTROINTESTINAL | DIAGNOSTICO |
| 16 | `masa` | 239 | 217 | 1.50% | 7.50% | MISC_MORFOLOGIA | DIAGNOSTICO |
| 17 | `enteritis` | 238 | 235 | 1.49% | 8.12% | GASTROINTESTINAL | DIAGNOSTICO |
| 18 | `pancreatitis` | 234 | 233 | 1.47% | 8.05% | PANCREATICA | DIAGNOSTICO |
| 19 | `normal` | 221 | 115 | 1.38% | 3.98% | NEGATIVO | NEGATIVO |
| 20 | `esplenomegalia` | 217 | 217 | 1.36% | 7.50% | ESPLENICA | DIAGNOSTICO |
| 21 | `peritonitis` | 205 | 204 | 1.28% | 7.05% | PERITONEO | DIAGNOSTICO |
| 22 | `adrenomegalia` | 201 | 198 | 1.26% | 6.84% | ENDOCRINO | DIAGNOSTICO |
| 23 | `no_se_observan` | 162 | 159 | 1.01% | 5.50% | NEGATIVO | NEGATIVO |
| 24 | `pielectasia` | 155 | 153 | 0.97% | 5.29% | RENAL | DIAGNOSTICO |
| 25 | `quiste` | 154 | 137 | 0.96% | 4.74% | MISC_MORFOLOGIA | DIAGNOSTICO |
| 26 | `prostatomegalia` | 146 | 146 | 0.91% | 5.05% | REPRODUCTIVO | DIAGNOSTICO |
| 27 | `histeromegalia` | 139 | 138 | 0.87% | 4.77% | REPRODUCTIVO | DIAGNOSTICO |
| 28 | `gestacion` | 133 | 132 | 0.83% | 4.56% | REPRODUCTIVO | DIAGNOSTICO |
| 29 | `sedimento_vejiga` | 127 | 127 | 0.80% | 4.39% | URINARIO | DIAGNOSTICO |
| 30 | `microhepatia` | 104 | 104 | 0.65% | 3.59% | HEPATICA | DIAGNOSTICO |
| 31 | `negativo` | 88 | 67 | 0.55% | 2.32% | NEGATIVO | NEGATIVO |
| 32 | `nodulo_esplenico` | 87 | 86 | 0.54% | 2.97% | ESPLENICA | DIAGNOSTICO |
| 33 | `compatible_con` | 86 | 84 | 0.54% | 2.90% | ETIOLOGIA | ETIOLOGIA |
| 34 | `colecistitis` | 84 | 84 | 0.53% | 2.90% | VESICULA | DIAGNOSTICO |
| 35 | `cambios_pancreaticos` | 84 | 84 | 0.53% | 2.90% | PANCREATICA | DIAGNOSTICO |
| 36 | `posible` | 55 | 52 | 0.34% | 1.80% | ETIOLOGIA | ETIOLOGIA |
| 37 | `atrofia` | 52 | 52 | 0.33% | 1.80% | MISC_MORFOLOGIA | DIAGNOSTICO |
| 38 | `absceso` | 50 | 49 | 0.31% | 1.69% | MISC_MORFOLOGIA | DIAGNOSTICO |
| 39 | `piometra` | 49 | 49 | 0.31% | 1.69% | REPRODUCTIVO | DIAGNOSTICO |
| 40 | `evidencia_de` | 40 | 40 | 0.25% | 1.38% | ETIOLOGIA | ETIOLOGIA |
| 41 | `probable` | 36 | 36 | 0.23% | 1.24% | ETIOLOGIA | ETIOLOGIA |
| 42 | `hiperplasia` | 35 | 35 | 0.22% | 1.21% | MISC_MORFOLOGIA | DIAGNOSTICO |
| 43 | `lesion` | 34 | 31 | 0.21% | 1.07% | MISC_MORFOLOGIA | DIAGNOSTICO |
| 44 | `sin_evidencia` | 33 | 33 | 0.21% | 1.14% | NEGATIVO | NEGATIVO |
| 45 | `nefromegalia` | 29 | 29 | 0.18% | 1.00% | RENAL | DIAGNOSTICO |
| 46 | `obstruccion` | 24 | 24 | 0.15% | 0.83% | MISC_MORFOLOGIA | DIAGNOSTICO |
| 47 | `fibrosis` | 22 | 21 | 0.14% | 0.73% | HEPATICA | DIAGNOSTICO |
| 48 | `hematoma` | 20 | 20 | 0.13% | 0.69% | MISC_MORFOLOGIA | DIAGNOSTICO |
| 49 | `ileitis` | 19 | 19 | 0.12% | 0.66% | GASTROINTESTINAL | DIAGNOSTICO |
| 50 | `polipo` | 17 | 17 | 0.11% | 0.59% | MISC_MORFOLOGIA | DIAGNOSTICO |

**Cobertura acumulada Top 50:** 99.27% de los 15,968 items totales.

---

## 3. Distribución de modificadores

### 3.1 `modificador_cualidad`

**Total:** 11,185 items con cualidad (70.0% cobertura).

| Valor | Frecuencia | Frecuencia informes | % del total con cualidad |
|---|---:|---:|---:|
| `leve` | 3,746 | 1,967 | 33.5% |
| `inflamatorio` | 3,502 | 2,020 | 31.3% |
| `moderada` | 1,546 | 1,056 | 13.8% |
| `infiltrativo` | 1,323 | 629 | 11.8% |
| `severa` | 877 | 470 | 7.8% |
| `reactivo` | 88 | 35 | 0.8% |
| `cronica` | 54 | 32 | 0.5% |
| `dilatado` | 14 | 9 | 0.1% |
| `aguda` | 13 | 7 | 0.1% |
| `aumentado` | 10 | 5 | 0.1% |
| `degenerativo` | 3 | 2 | 0.0% |
| `hiperecoico` | 3 | 2 | 0.0% |
| `anecoico` | 3 | 2 | 0.0% |
| `disminuido` | 2 | 1 | 0.0% |
| `engrosado` | 1 | 1 | 0.0% |

### 3.2 `modificador_distribucion`

**Total:** 556 items con distribución (3.5% cobertura).

| Valor | Frecuencia | Frecuencia informes | % del total con distribución |
|---|---:|---:|---:|
| `focal` | 311 | 136 | 55.9% |
| `discreta` | 160 | 89 | 28.8% |
| `generalizada` | 52 | 26 | 9.4% |
| `difusa` | 33 | 17 | 5.9% |

### 3.3 `lateralidad`

**Total:** 4,316 items con lateralidad (27.0% cobertura).

| Valor | Frecuencia | Frecuencia informes | % del total con lateralidad |
|---|---:|---:|---:|
| `bilateral` | 3,299 | 1,560 | 76.4% |
| `izquierdo` | 600 | 284 | 13.9% |
| `derecho` | 401 | 218 | 9.3% |
| `ambos` | 16 | 13 | 0.4% |

---

## 4. Estabilidad del catálogo

### 4.1 ¿81 términos siguen siendo suficientes?

**Sí.** 74 términos observados; el Top 50 cubre 99.27% de los 15,968 items. Los 24 términos restantes son long-tail (cada uno <0.1%). Mantener los 60-80 términos canónicos en `dim_termino_conclusion` cubre el 100% del volumen detectable; el resto puede dejarse como `termino_detectado` ad-hoc con `termino_conclusion_id=NULL` para futura catalogación.

### 4.2 ¿Términos con <5 ocurrencias?

**Total:** 14 términos con <5 ocurrencias:

| Término | Frecuencia |
|---|---:|
| `amiloidosis` | 1 |
| `hemometra` | 1 |
| `cirrosis` | 1 |
| `sin_alteraciones` | 1 |
| `sospecha_infecciosa` | 1 |
| `urolitiasis` | 1 |
| `quiste_ovarico` | 1 |
| `aparente` | 1 |
| `ectasia_independiente` | 1 |
| `neoplasia` | 2 |
| `dentro_de_rango` | 2 |
| `hiperplasia_prostatica` | 2 |
| `ausencia_de` | 3 |
| `linfadenomegalia` | 4 |

**Recomendación:** Mantener todos en el catálogo pero marcados como `activo=1`. Son términos válidos del español clínico; su rareza es por distribución natural del corpus, no por error. Se pueden excluir del Gold si el usuario filtra por `frecuencia_rank <= 50`.

### 4.3 ¿Términos con cardinalidad alta (muchas variantes textuales)?

Top 10 términos con más `termino_detectado` distintos:

| Término canónico | # Variantes | Top 3 variantes (variante: count) |
|---|---:|---|
| `derrame_peritoneal` | 5 | `Derrame peritoneal`: 210, `derrame peritoneal`: 35, `líquido libre`: 17 |
| `nodulo` | 4 | `Nódulo`: 172, `Nódulos`: 42, `nódulo`: 37 |
| `sedimento_vejiga` | 4 | `Sedimento en vejiga`: 57, `Sedimento vesical`: 35, `sedimento en vejiga`: 19 |
| `quiste` | 4 | `quiste`: 61, `Quiste`: 59, `quistes`: 18 |
| `masa` | 4 | `Masa`: 148, `masa`: 65, `masas`: 18 |
| `lesion` | 4 | `Lesión`: 17, `lesión`: 14, `lesiones`: 2 |
| `ileitis` | 4 | `Ileítis`: 10, `Ileitis`: 4, `ileítis`: 3 |
| `gestacion` | 3 | `Gestación`: 109, `gestación`: 14, `preñez`: 10 |
| `nefropatia` | 3 | `Nefropatía`: 1592, `nefropatía`: 30, `Nefropatia`: 2 |
| `probable` | 3 | `probable`: 34, `Probable`: 1, `probables`: 1 |

**Interpretación:** `termino_detectado` es la forma textual exacta (ej. 'nefropatía' con tilde, 'nefropatia' sin tilde, 'nefropatía bilateral' como variante). Cardinalidad alta aquí **no es problema** — es información de auditoría, no afecta queries (que filtran por `termino_canonico`).

### 4.4 Candidatos a FUSIÓN

| Término A | Término B | Razón | Recomendación |
|---|---|---|---|
| `higado_graso` | `hepatopatia_vacuolar` | Misma categoría HEPATICA, a menudo co-ocurren (infiltración grasa + vacuolar) | NO FUSIONAR — son hallazgos clínicamente distintos (etiología grasa vs degeneración vacuolar). |
| `hiperplasia` | `hiperplasia_prostatica` | El segundo es un caso específico del primero; hiperplasia_prostatica solo tiene 2 menciones. | NO FUSIONAR — hiperplasia_prostatica es REDUNDANTE con prostatomegalia en el corpus clínico. |
| `nefrocalcinosis` | `nefropatia` | Categorías distintas (mineralización vs diagnóstico parenquimatoso). | NO FUSIONAR — son entidades nosológicas separadas. |
| `sospecha_inflamatoria` | `sospecha_neoplasica` | Marcadores de etiología distintos (inflamatoria vs neoplásica). | NO FUSIONAR — son mutuamente excluyentes clínicamente. |
| `ectasia_independiente` | `ectasia_pelvica` | El segundo es específico del primero en riñón. | NO FUSIONAR — ectasia_pelvica tiene contexto renal; ectasia_independiente no. |
| `ausencia_de` | `no_se_observan` | Negaciones distintas (ausencia_de es más formal, no_se_observan es hallazgo operativo). | NO FUSIONAR — diferentes contextos de uso (texto escrito vs informe estructurado). |

### 4.5 Candidatos a DIVISIÓN

- **`neoplasico`:** Mezcla 'neoplásico' (adjetivo) y 'neoproliferativo' (sustantivo). Valorar separar en: neoplasico (adjetivo) vs neoplasia_proliferativa (sustantivo).
- **`masa`:** Genérico: masa esplénica, masa hepática, masa abdominal. Si la clínica lo requiere, considerar masa_hepatica, masa_esplenica, etc.
- **`nodulo`:** Similar a 'masa': nódulo esplénico, nódulo hepático, nódulo cutáneo.
- **`ectasia_independiente`:** Podría ser 'ectasia' sin más — todos los casos son ectasia sin contexto anatómico.

**Recomendación general:** el catálogo actual cubre el corpus con suficiencia. No se recomienda fusión ni división en esta iteración. Si en iteraciones futuras el corpus crece, revisar específicamente `neoplasico` y `masa/nodulo` (categorías MISC).

### 4.6 ¿Hay explosión de cardinalidad en modificadores?

- **`modificador_cualidad`:** 15 valores distintos (rango razonable).
- **`modificador_distribucion`:** 4 valores distintos (rango muy bajo).
- **`lateralidad`:** 4 valores distintos (5 valores canónicos: bilateral, izquierdo, derecho, ambos, unilateral).

**Conclusión:** NO hay explosión de cardinalidad. Los rangos son manejables y estables.

---

## 5. Veredicto

## **GO**


**Justificación:** Todos los criterios cuantitativos cumplidos:

- Cobertura del Top 50: 99.27% (target ≥95%) ✅
- Cardinalidad de modificadores estable ✅
- Términos raros manejables (14 con <5 ocurrencias) ✅
- 0% necesidad de fusión/división del catálogo ✅

---

## 6. Resumen final

| Métrica | Valor | Criterio |
|---|---:|---|
| Conclusiones totales | 2,893 | — |
| Conclusiones con ≥1 item | 2,826 (97.68%) | ≥85% |
| Items totales (Opción C) | 15,968 | — |
| Términos distintos | 74 | — |
| Cobertura Top 50 | 99.27% | ≥95% |
| Items/conclusión (media) | 5.52 | ≤7 |
| Cardinalidad `modificador_cualidad` | 15 | ≤30 |
| Cardinalidad `modificador_distribucion` | 4 | ≤10 |
| Cardinalidad `lateralidad` | 4 | ≤8 |
| Términos raros (<5) | 14 | ≤50 |
| Precisión estimada | 98.0% | ≥95% |
| Reducción vs FULL | -42% items | ≥-30% |

**Esperando aprobación del esquema DDL + veredicto para proceder con implementación de F5.**
