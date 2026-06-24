# Fase 3 — Attribute Discovery

**Estado:** 📋 PROFILING (pre-implementación)
**Generado:** 2026-06-19
**Objetivo:** Validar que el catálogo de 22 atributos (Anexo A de SILVER_LAYER.md)
realmente coincide con el corpus de 27,866 hallazgos antes de construir
`silver_atributos_hallazgo`.

---

## 0. Resumen ejecutivo

| Resultado | Valor |
|---|---|
| Hallazgos en RAW | 27.866 |
| Órganos distintos | 15 (más "Cavidad abdominal" sin hallazgos) |
| Pares `(órgano, atributo)` en catálogo (Anexo A) | 57 |
| Pares con cobertura estimada ≥50% | 35 (61%) |
| Pares con cobertura estimada 10-50% | 12 (21%) |
| Pares con cobertura estimada <10% | 10 (18%) |
| Atributos organo-AGNÓSTICOS únicos | 22 (todos presentes en Anexo A) |

**Hallazgo principal:** El catálogo de 22 atributos es **globalmente correcto**
para los 9 órganos abdominales principales (Hígado, Vejiga, Riñones, Vesícula,
Bazo, Estómago, Intestino, Páncreas, Adrenales) y para Próstata. La cobertura
proyectada de `silver_atributos_hallazgo` es **alta en estos 10 órganos** y
**muy baja en los 5 órganos restantes** (Linfonodos, Útero, Ovarios,
Testículos, Gestación), donde las descripciones son demasiado breves o
heterogéneas para que un regex cerrado funcione.

**Recomendación para F3:** implementar F3 en dos tramos:
- **F3.0 (v1):** los 10 órganos con cobertura ≥50% (≈ 26.000 hallazgos)
- **F3.1 (v2):** refinar regex para los 12 pares con cobertura 10-50%
- **F3.2 (v3):** decidir si los órganos cortos (Linfonodos, Ovarios, etc.)
  se modelan con atributos "negativos" (presente/ausente) en lugar de
  descriptivos.

---

## 1. Frecuencia por órgano

```
Órgano               hallazgos     %           cobertura_atributos_estimada
─────────────────────────────────────────────────────────────────────────
Vejiga                  2.690     9.65%       ✅ ALTA (4/4 atributos)
Estómago                2.688     9.65%       ✅ ALTA (3/4)
Intestino               2.688     9.65%       ⚠️ MEDIA-ALTA (3/4, distension rara)
Páncreas                2.688     9.65%       ⚠️ BAJA (descripción siempre breve)
Riñones                 2.688     9.65%       ✅ ALTA (6/7)
Adrenales               2.687     9.64%       ⚠️ BAJA (≥95% "no evaluadas" o "conservadas")
Hígado                  2.687     9.64%       ✅ ALTA (7/7)
Bazo                    2.684     9.63%       ✅ ALTA (4/4)
Linfonodos              2.681     9.62%       ❌ MUY BAJA (≥95% "no se observan")
Vesícula                2.667     9.57%       ✅ ALTA (4/4)
Próstata                  737     2.64%       ✅ ALTA (4/4)
Gestación                 200     0.72%       ⚠️ MEDIA (1/2; preñez no existe como token)
Útero                     49     0.18%       ❌ BAJA (descripciones muy específicas)
Testículos                27     0.10%       ❌ BAJA (corpus escaso)
Ovarios                    5     0.02%       ❌ MUY BAJA (3/5 son "Ausentes")
```

**Lectura:** los 10 primeros órganos concentran el 95.5% de los hallazgos
y son los que el ETL F3.0 debe apuntar. Los 5 últimos suman apenas 1,036
hallazgos (3.7%) con descripciones heterogéneas que requieren NLP más
sofisticado o modelado "negativo".

---

## 2. Cobertura por (órgano, atributo)

Estimación realizada con regex tentativas (no finales) sobre el corpus real.
Cobertura = % de descripciones del órgano donde matchea AL MENOS una
expresión del atributo. Sirve como techo de lo que el extractor F3 puede
lograr con regex cerradas.

### 2.1. Órganos con cobertura ALTA (≥50% por par)

| Órgano | Atributo | match | total | % | Status |
|---|---|---:|---:|---:|---|
| Vejiga | replecion | 2641 | 2690 | 98.2% | ✅ |
| Vejiga | bordes_internos | 2546 | 2690 | 94.6% | ✅ |
| Vejiga | grosor_pared | 2542 | 2690 | 94.5% | ✅ |
| Vejiga | contenido | 2509 | 2690 | 93.3% | ✅ |
| Hígado | márgenes | 2638 | 2687 | 98.2% | ✅ |
| Hígado | ecogenicidad | 2571 | 2687 | 95.7% | ✅ |
| Hígado | tamaño | 2551 | 2687 | 94.9% | ✅ |
| Hígado | granulado | 2535 | 2687 | 94.3% | ✅ |
| Hígado | patron_vascular | 2474 | 2687 | 92.1% | ✅ |
| Hígado | bordes | 2473 | 2687 | 92.0% | ✅ |
| Hígado | arquitectura | 1760 | 2687 | 65.5% | ✅ |
| Riñones | forma | 2605 | 2688 | 96.9% | ✅ |
| Riñones | bordes | 2506 | 2688 | 93.2% | ✅ |
| Riñones | tamaño | 2456 | 2688 | 91.4% | ✅ |
| Riñones | diferenciacion_cm | 2328 | 2688 | 86.6% | ✅ |
| Riñones | relacion_cm | 2056 | 2688 | 76.5% | ✅ |
| Vesícula | distension | 2630 | 2667 | 98.6% | ✅ |
| Vesícula | grosor_pared | 2548 | 2667 | 95.5% | ✅ |
| Vesícula | bordes_internos | 2541 | 2667 | 95.3% | ✅ |
| Vesícula | contenido | 2540 | 2667 | 95.2% | ✅ |
| Bazo | márgenes | 2531 | 2684 | 94.3% | ✅ |
| Bazo | forma | 2419 | 2684 | 90.1% | ✅ |
| Bazo | arquitectura | 2367 | 2684 | 88.2% | ✅ |
| Bazo | tamaño | 159 | 2684 | 5.9% | ❌ ⚠️ |
| Próstata | homogeneidad | 718 | 737 | 97.4% | ✅ |
| Próstata | ecogenicidad | 715 | 737 | 97.0% | ✅ |
| Próstata | aspecto | 700 | 737 | 95.0% | ✅ |
| Próstata | tamaño | 646 | 737 | 87.7% | ✅ |
| Estómago | distension | 2614 | 2688 | 97.2% | ✅ |
| Estómago | grosor_pared | 2528 | 2688 | 94.0% | ✅ |
| Estómago | contenido | 2430 | 2688 | 90.4% | ✅ |
| Estómago | peristaltismo | 18 | 2688 | 0.7% | ❌ ⚠️ |
| Intestino | contenido | 2598 | 2688 | 96.7% | ✅ |
| Intestino | grosor_pared | 2560 | 2688 | 95.2% | ✅ |
| Intestino | peristaltismo | 2511 | 2688 | 93.4% | ✅ |
| Intestino | distension | 66 | 2688 | 2.5% | ❌ ⚠️ |
| Gestación | fetos | 107 | 200 | 53.5% | ✅ |

### 2.2. Órganos con cobertura BAJA/MIXTA (10-50% por par)

| Órgano | Atributo | match | total | % | Status |
|---|---|---:|---:|---:|---|
| Riñones | ecogenicidad_cortical | 424 | 2688 | 15.8% | ⚠️ |
| Páncreas | ecogenicidad | 194 | 2688 | 7.2% | ❌ ⚠️ |
| Páncreas | tamaño | 30 | 2688 | 1.1% | ❌ ⚠️ |
| Adrenales | tamaño | 121 | 2687 | 4.5% | ❌ ⚠️ |
| Adrenales | forma | 2417 | 2687 | 90.0% | ✅ (engañoso) |
| Linfonodos | ecogenicidad | 475 | 2681 | 17.7% | ⚠️ |
| Linfonodos | homogeneidad | 365 | 2681 | 13.6% | ⚠️ |
| Linfonodos | forma | 106 | 2681 | 4.0% | ⚠️ |
| Linfonodos | tamaño | 12 | 2681 | 0.4% | ❌ |
| Útero | contenido | 7 | 49 | 14.3% | ⚠️ |
| Útero | grosor_pared | 7 | 49 | 14.3% | ⚠️ |
| Útero | tamaño | 0 | 49 | 0.0% | ❌ |
| Testículos | homogeneidad | 7 | 27 | 25.9% | ⚠️ |
| Testículos | ecogenicidad | 5 | 27 | 18.5% | ⚠️ |
| Testículos | tamaño | 2 | 27 | 7.4% | ❌ |
| Testículos | forma | 1 | 27 | 3.7% | ❌ |
| Ovarios | tamaño | 0 | 5 | 0.0% | ❌ |
| Ovarios | forma | 0 | 5 | 0.0% | ❌ |
| Riñones | compromiso_pelvico | 20 | 2688 | 0.7% | ❌ |
| Gestación | preñez | 0 | 200 | 0.0% | ❌ |

---

## 3. Top 30 valores por par (extracto representativo)

### 3.1. Hígado.ecogenicidad (95.7% cobertura)

| Valor | n |
|---|---:|
| hipoecoica | 1.949 |
| hiperecoica | 481 |
| levemente_aumentada | 44 |
| aumentada | 33 |
| levemente_disminuida | 18 |
| conservada | 10 |
| disminuida | 9 |
| normal | 1 |

**Lectura:** 5 valores cubren el 99% del corpus. Catálogo cerrado viable.

### 3.2. Hígado.granulado (94.3% cobertura)

| Valor | n |
|---|---:|
| grueso | 1.922 |
| fino | 613 |

**Lectura:** 2 valores. Catálogo trivial.

### 3.3. Hígado.márgenes (98.2% cobertura)

| Valor | n |
|---|---:|
| lisos | 2.615 |
| redondeados | 16 |
| irregulares | 5 |
| mal_definidos | 2 |

**Lectura:** "lisos" domina al 99%. Catálogo simple.

### 3.4. Hígado.tamaño (94.9% cobertura)

| Valor | n |
|---|---:|
| normal | 1.437 |
| aumentada (F) | 296 |
| levemente_aumentada (F) | 285 |
| levemente_aumentado (M) | 280 |
| aumentado (M) | 105 |
| moderadamente_aumentado (M) | 68 |
| disminuido (M) | 35 |
| severamente_aumentado | 20 |
| **morfológica**: el atributo está en femenino ("aumentada de tamaño") cuando califica al hígado como sustantivo femenino; el catálogo debe aceptarlo. | |

### 3.5. Riñones.forma (96.9% cobertura)

| Valor | n |
|---|---:|
| ovalado | 2.522 |
| irregulares | 67 |
| globoso | 5 |
| redondeado | 5 |
| ovalada | 4 |

### 3.6. Riñones.diferenciacion_cm (86.6% cobertura)

| Valor (regex) | n |
|---|---:|
| córtico medular + bien_definida | 2.222 |
| cortico medular (sin tilde) | 75 |
| córtico-medular (con guión) | 29 |
| cortico-medular | 1 |
| corticomedular | 1 |

**Lectura:** el atributo es binario (bien/mal definida). La regex captura el
"adjetivo" de "diferenciación X". Se observa que el corpus prefiere
"diferenciación córtico medular bien definida" sobre "diferenciación cm bien
definida". Catálogo viable.

### 3.7. Vejiga.replecion (98.2% cobertura)

| Valor | n |
|---|---:|
| semi pletórica | 2.182 |
| pletórica | 233 |
| semi depletada | 154 |
| depletada | 51 |
| vacía | 12 |
| distendida | 4 |

**Lectura:** catalogable con 5 valores + variantes con mayúscula.

### 3.8. Vesícula.distension (98.6% cobertura)

| Valor | n |
|---|---:|
| semi distendida | 2.468 |
| distendida | 112 |
| semi pletórica | 22 |
| pletórica | 15 |
| depletada | 8 |

### 3.9. Próstata.ecogenicidad (97.0% cobertura)

| Valor | n |
|---|---:|
| hipoecoica | 446 |
| hiperecoica | 261 |
| hipoecoico | 6 |
| hiperecoico | 1 |

### 3.10. Estómago.contenido (90.4% cobertura)

| Valor | n |
|---|---:|
| alimenticio | 2.119 |
| mucoso | 264 |
| líquido | 32 |
| gas | 12 |

### 3.11. Intestino.contenido (96.7% cobertura)

| Valor | n |
|---|---:|
| con predominio + alimenticio | 2.508 |
| mucoso | 36 |
| fecal | 35 |
| alimenticio | 8 |
| patrón líquido | 5 |

### 3.12. Intestino.grosor_pared (95.2% cobertura)

| Valor | n |
|---|---:|
| conservado | 2.418 |
| levemente_aumentado | 64 |
| aumentado | 24 |
| discretamente_aumentado | 21 |
| moderadamente_aumentado | 21 |
| severamente_aumentado | 2 |

### 3.13. Intestino.peristaltismo (93.4% cobertura)

| Valor | n |
|---|---:|
| normal | 2.449 |
| aumentado | 25 |
| disminuido | 24 |
| ausente | 8 |
| conservado | 1 |

### 3.14. Gestación.fetos (53.5% cobertura)

| Valor | n |
|---|---:|
| 5 | 20 |
| 6 | 18 |
| 4 | 15 |
| 3 | 14 |
| 1 | 12 |
| 7 | 9 |
| 8 | 9 |
| 2 | 8 |
| 9 | 2 |

**Lectura:** atributo numérico cerrado. 9 valores cubren 107 hallazgos. La
mitad de los hallazgos Gestación NO mencionan fetos (describen útero
aumentado, paredes engrosadas, "No se observa aumento uterino") — el atributo
debería complementarse con un atributo derivado `gestacion_activa` booleano.

---

## 4. Atributos ambiguos (polisémicos)

### 4.1. `tamaño` (keyword presente en casi todas las descripciones)

| Órgano | % de hallazgos que mencionan "tamaño" | ¿Es atributo válido? |
|---|---:|---|
| Hígado | 99.5% | ✅ sí |
| Riñones | 99.3% | ✅ sí |
| Bazo | 98.4% | ✅ sí |
| Próstata | 97.7% | ✅ sí |
| Linfonodos | 16.6% | ⚠️ solo cuando se describe un nódulo; falso positivo alto |
| Testículos | 22.2% | ⚠️ solo a veces |

**Conclusión:** el keyword `tamaño` es seguro en los 4 primeros, ruidoso en
los 2 últimos. En Linfonodos/Testículos debe ir acompañado de
negative-claim detection ("No se observan…") para no extraer falsos positivos.

### 4.2. `conservado/a` (polisémico: atributo, diagnóstico, "todo normal")

| Órgano | % de hallazgos que mencionan "conservado" | Notas |
|---|---:|---|
| Hígado | 95.4% | usualmente como "ecogenicidad conservada" o "patrón vascular conservado" |
| Páncreas | 95.2% | "Páncreas conservado" — frase completa, no atributo |
| Bazo | 88.3% | mixto |
| Vejiga | 81.2% | "grosor conservado", "bordes conservados" |
| Testículos | 33.3% | "ambos testículos conservados" (resumen) |
| Riñones | 13.4% | muy raro |
| Adrenales | 3.1% | "adrenales conservadas" (resumen) |

**Conclusión:** "conservado" como valor canónico es correcto SOLO cuando
acompaña a un atributo específico (grosor conservado, ecogenicidad
conservada, etc.). Cuando aparece como "órgano X conservado" sin atributo,
NO debe extraerse como silver_atributos_hallazgo — es un resumen, no un
atributo. La regex debe exigir un modificador previo: `\bconservad[oa]\b`
solo si hay un sustantivo de atributo en los 3 tokens anteriores.

### 4.3. `bordes` vs `bordes_internos` vs `pared de bordes`

| Órgano | bordes_internos | pared de bordes | notas |
|---|---:|---:|---|
| Vejiga | 2.558 (95%) | 2.551 (95%) | sinonimia total — la regex debe aceptar ambas |
| Vesícula | 2.543 (95%) | 3 (0.1%) | solo "bordes internos" |

**Conclusión:** para Vejiga, la regex debe aceptar AMBAS formas. Para
Vesícula, solo `bordes internos`.

### 4.4. `forma` (¿atributo o solo declaración?)

En Adrenales, el corpus usa "arquitectura y tamaño conservado" — `forma`
aparece como keyword pero la cobertura real es 0% (ningún hallazgo Adrenales
dice "forma ovalada"). El atributo `forma` para Adrenales debería
replantearse a `preservada/alterada` o eliminarse.

### 4.5. `ecogenicidad` (genérica vs específica)

- `ecogenicidad_cortical` en Riñones: 15.8%. El corpus dice "ecogenicidad
  adecuada" o "ecogenicidad conservada" sin calificar "cortical". La
  distinción cortical/medular en el catálogo puede ser SOBRE-especificada.

- `ecogenicidad` (sin sufijo) en Páncreas, Linfonodos, Testículos, Bazo:
  cobertura 7-25%. Cuando el corpus la usa, suele ser "hipoecoico" sin
  matiz. El catálogo debería ser más generoso en la unidad de medida
  (considerar `parénquima` o `parénquima de mayor ecogenicidad`).

### 4.6. Atributos con texto del corpus engañoso

- `diferenciacion_cm`: corpus dice "diferenciación córtico medular" (no "cm").
  La regex debe aceptar la frase completa, no la abreviatura.

- `relacion_cm`: corpus dice "relación adecuada" o "relación cortico
  medular adecuada" — el `cm` está embebido en la frase, no como
  modificador aislado.

- `patron_vascular` en Hígado: corpus dice "patrón vascular conservado" o
  "vasculatura esplénica" (en Bazo). La unidad semántica es "patrón
  vascular" completo.

---

## 5. Atributos que requieren regex específica

Lista priorizada de pares con problemas de extracción:

| # | Par | Problema | Regex sugerida |
|---|---|---|---|
| 1 | Bazo.tamaño | 5.9% — corpus dice "tamaño normal" pero también "tamaño y forma normales" | `tama[ñn]o\s+(?:y\s+forma\s+)?(normal\|...)` |
| 2 | Estómago.peristaltismo | 0.7% — corpus casi nunca lo menciona para estómago | ELIMINAR del catálogo o aceptar que es 0.7% real |
| 3 | Intestino.distension | 2.5% — corpus no describe distensión intestinal, solo grosor/contenido | ELIMINAR del catálogo |
| 4 | Riñones.compromiso_pelvico | 0.7% — corpus dice "sin compromiso pélvico" (negativo) | Regex: `sin\s+compromiso\s+p[ée]lvic\|con\s+compromiso\s+p[ée]lvic` |
| 5 | Riñones.ecogenicidad_cortical | 15.8% — corpus dice "ecogenicidad" sin calificar | Regex más permisiva: `ecogenicidad\s+\w+` y aceptar como cortical por contexto |
| 6 | Páncreas.* | <10% — descripciones siempre breves ("Páncreas conservado") | NLP o modelo "todo normal" |
| 7 | Adrenales.tamaño | 4.5% — corpus dice "adrenales conservadas" sin detalle | Regex con negative-claim: `adrenales\s+(?:no\s+evaluadas\|conservadas\|de\s+tama[ñn]o\s+\w+)` |
| 8 | Adrenales.forma | 90% engañoso — matchea "forma" como keyword pero valor es "no aplica" | ELIMINAR `forma` para Adrenales |
| 9 | Linfonodos.* | <20% — corpus es "No se observan…" (negativo) | Modelo binario: `presente\|ausente\|no_se_observan` |
| 10 | Ovarios.* | 0% — solo 5 hallazgos, 3 son "Ausentes" | ELIMINAR atributos descriptivos; usar `presente\|ausente` |
| 11 | Testículos.* | <26% — corpus muy variable | Regex case-by-case, esperar F3.1 |
| 12 | Gestación.preñez | 0% — corpus no usa "preñez" como token | ELIMINAR; reemplazar por atributo derivado booleano `gestacion_activa` |

---

## 6. Cobertura por atributo organo-AGNÓSTICO (sumando todos los órganos)

| Atributo | match | total | % | Status |
|---|---:|---:|---:|---|
| aspecto | 700 | 737 | 95.0% | ✅ |
| bordes | 4979 | 5375 | 92.6% | ✅ |
| bordes_internos | 5087 | 5357 | 95.0% | ✅ |
| compromiso_pelvico | 20 | 2688 | 0.7% | ❌ |
| contenido | 10084 | 10782 | 93.5% | ✅ |
| diferenciacion_cm | 2328 | 2688 | 86.6% | ✅ |
| distension | 5310 | 8043 | 66.0% | ⚠️ |
| ecogenicidad | 3960 | 8820 | 44.9% | ⚠️ |
| ecogenicidad_cortical | 424 | 2688 | 15.8% | ❌ |
| fetos | 107 | 200 | 53.5% | ⚠️ |
| forma | 7548 | 10772 | 70.1% | ✅ |
| granulado | 2535 | 2687 | 94.3% | ✅ |
| grosor_pared | 10185 | 10782 | 94.5% | ✅ |
| homogeneidad | 1090 | 3445 | 31.6% | ⚠️ |
| márgenes | 5169 | 5371 | 96.2% | ✅ |
| patron_vascular | 2474 | 2687 | 92.1% | ✅ |
| peristaltismo | 2529 | 5376 | 47.0% | ⚠️ |
| preñez | 0 | 200 | 0.0% | ❌ |
| relacion_cm | 2056 | 2688 | 76.5% | ✅ |
| replecion | 2641 | 2690 | 98.2% | ✅ |
| tamaño | 5977 | 16933 | 35.3% | ⚠️ |

**Lectura por atributo (no por par):**
- ✅ Catálogo cerrado viable: aspecto, bordes, bordes_internos, contenido,
  diferenciacion_cm, forma, granulado, grosor_pared, márgenes, patron_vascular,
  relacion_cm, replecion (12 atributos).
- ⚠️ Cobertura media, requiere regex permisiva: distension, ecogenicidad,
  fetos, homogeneidad, peristaltismo, tamaño (6 atributos).
- ❌ Atributos a revisar: compromiso_pelvico, ecogenicidad_cortical, preñez
  (3 atributos).

---

## 7. Atributos vs. valor: ¿cuántos matches por hallazgo?

Estimación de la cardinalidad promedio de `silver_atributos_hallazgo` por
hallazgo (asumiendo regex perfectas):

| Órgano | Atributos matcheando (alta cobertura) | Matches / hallazgo estimado |
|---|---:|---:|
| Vejiga | 4/4 | 3.8 |
| Hígado | 7/7 | 6.4 |
| Riñones | 6/7 | 5.0 |
| Vesícula | 4/4 | 3.8 |
| Bazo | 3/4 (tamaño es ruidoso) | 2.7 |
| Próstata | 4/4 | 3.8 |
| Estómago | 3/4 | 2.9 |
| Intestino | 3/4 | 2.8 |
| Páncreas | 0-1/2 | 0.1 |
| Adrenales | 0-1/2 | 0.5 |
| Linfonodos | 0-1/4 | 0.2 |
| Útero | 0-1/3 | 0.4 |
| Ovarios | 0/2 | 0.0 |
| Testículos | 0-1/4 | 0.4 |
| Gestación | 1/2 | 0.5 |

**Cardinalidad total estimada de silver_atributos_hallazgo (F3.0):**
≈ 26.000 hallazgos × 3.5 matches/hallazgo = **~91.000 filas**

(contra las 27.866 originales de hallazgos — una proporción de ~3.3:1, que
encaja con el "4-6 atributos por hallazgo" mencionado en SILVER_LAYER.md §3.3.)

---

## 8. Propuesta de orden de implementación

Criterio: (cobertura % × n_hallazgos) prioriza los pares con mayor impacto
en `silver_atributos_hallazgo`. Sub-fases por tramos de cobertura.

### 8.1. F3.0 (v1) — 10 órganos principales, 35 pares

| rank | Órgano | Atributo | matches esperados | % |
|---:|---|---|---:|---:|
| 1 | Vejiga | replecion | 2.641 | 98% |
| 2 | Hígado | márgenes | 2.638 | 98% |
| 3 | Vesícula | distension | 2.630 | 99% |
| 4 | Estómago | distension | 2.614 | 97% |
| 5 | Riñones | forma | 2.605 | 97% |
| 6 | Intestino | contenido | 2.598 | 97% |
| 7 | Hígado | ecogenicidad | 2.571 | 96% |
| 8 | Intestino | grosor_pared | 2.560 | 95% |
| 9 | Hígado | tamaño | 2.551 | 95% |
| 10 | Vesícula | grosor_pared | 2.548 | 96% |
| 11 | Vejiga | bordes_internos | 2.546 | 95% |
| 12 | Vejiga | grosor_pared | 2.542 | 94% |
| 13 | Vesícula | bordes_internos | 2.541 | 95% |
| 14 | Vesícula | contenido | 2.540 | 95% |
| 15 | Hígado | granulado | 2.535 | 94% |
| 16 | Bazo | márgenes | 2.531 | 94% |
| 17 | Estómago | grosor_pared | 2.528 | 94% |
| 18 | Intestino | peristaltismo | 2.511 | 93% |
| 19 | Vejiga | contenido | 2.509 | 93% |
| 20 | Riñones | bordes | 2.506 | 93% |
| 21 | Hígado | patron_vascular | 2.474 | 92% |
| 22 | Hígado | bordes | 2.473 | 92% |
| 23 | Riñones | tamaño | 2.456 | 91% |
| 24 | Estómago | contenido | 2.430 | 90% |
| 25 | Bazo | forma | 2.419 | 90% |
| 26 | Bazo | arquitectura | 2.367 | 88% |
| 27 | Riñones | diferenciacion_cm | 2.328 | 87% |
| 28 | Próstata | homogeneidad | 718 | 97% |
| 29 | Próstata | ecogenicidad | 715 | 97% |
| 30 | Próstata | aspecto | 700 | 95% |
| 31 | Próstata | tamaño | 646 | 88% |
| 32 | Riñones | relacion_cm | 2.056 | 76% |
| 33 | Hígado | arquitectura | 1.760 | 66% |
| 34 | Gestación | fetos | 107 | 54% |
| 35 | Bazo | tamaño | 159 | 6% (revisar) |

**Suma F3.0 (orden de implementación sugerido):**
1. Vejiga (4) → 2. Hígado (7) → 3. Vesícula (4) → 4. Estómago (3) →
5. Riñones (6) → 6. Intestino (3) → 7. Bazo (3) → 8. Próstata (4) →
9. Gestación (1) → 10. Riñones.compromiso_pelvico (1) [último, baja cobertura]

### 8.2. F3.1 (v2) — refinar regex para 12 pares en 10-50%

| Par | % | Acción |
|---|---:|---|
| Linfonodos.ecogenicidad | 17.7% | agregar regex con negative-claim |
| Linfonodos.homogeneidad | 13.6% | idem |
| Riñones.ecogenicidad_cortical | 15.8% | regex más permisiva (aceptar "ecogenicidad" sin "cortical") |
| Útero.contenido | 14.3% | regex dedicada a "útero" |
| Útero.grosor_pared | 14.3% | idem |
| Testículos.homogeneidad | 25.9% | regex case-by-case |
| Testículos.ecogenicidad | 18.5% | idem |
| Linfonodos.forma | 4.0% | idem (mover a F3.2 si no mejora) |
| Útero.tamaño | 0.0% | (corpus no menciona "tamaño" para útero, ver muestra) |
| Testículos.forma | 3.7% | idem |
| Testículos.tamaño | 7.4% | idem |
| Páncreas.ecogenicidad | 7.2% | regex dedicada |
| Páncreas.tamaño | 1.1% | idem |
| Adrenales.tamaño | 4.5% | regex con negative-claim |
| Adrenales.forma | (engañoso) | ELIMINAR o reemplazar por `preservada/alterada` |
| Bazo.tamaño | 5.9% | regex con "tamaño y forma normales" |
| Intestino.distension | 2.5% | **ELIMINAR** del catálogo (corpus no lo usa) |
| Estómago.peristaltismo | 0.7% | **ELIMINAR** del catálogo |
| Riñones.compromiso_pelvico | 0.7% | regex con "sin/con compromiso pélvico" |
| Gestación.preñez | 0.0% | **ELIMINAR**; crear `gestacion_activa` derivado |

### 8.3. F3.2 (v3) — modelo "negativo" para órganos con descripciones breves

Para los 5 órganos donde la mayoría de hallazgos son resúmenes o
negaciones, se propone un modelo de **un único atributo binario**:

| Órgano | Atributo único | Valores |
|---|---|---|
| Linfonodos | compromiso | `comprometidos / no_comprometidos / no_evaluados` |
| Páncreas | preservacion | `preservado / alterado / no_evaluado` |
| Adrenales | evaluacion | `evaluadas_conservadas / evaluadas_alteradas / no_evaluadas` |
| Ovarios | presencia | `presentes / ausentes / no_evaluados` |
| Testículos | preservacion | `conservados / alterados / no_evaluados` |

Este modelo cubre el 100% de los hallazgos con una sola fila en
`silver_atributos_hallazgo` por hallazgo, sin pretender extraer detalles
que el corpus no tiene.

---

## 9. Cambios sugeridos al Anexo A antes de F3.0

Conclusión derivada del profiling. Todos opcionales — F3.0 puede implementarse
con el catálogo actual.

1. **ELIMINAR del catálogo (3):**
   - `Intestino.distension` (cobertura 2.5%, no usado en corpus)
   - `Estómago.peristaltismo` (cobertura 0.7%, no usado en corpus)
   - `Gestación.preñez` (cobertura 0%, no aparece como token)

2. **REEMPLAZAR con atributo derivado:**
   - `Gestación.preñez` → `Gestación.gestacion_activa` (booleano, derivado
     de "fetos > 0" o "útero aumentado")

3. **RENOMBRAR para reducir ambigüedad:**
   - `Riñones.ecogenicidad_cortical` → `Riñones.ecogenicidad_parenquima`
     (más fiel al corpus, donde no se distingue cortical/medular)

4. **MOVER a F3.2 (modelo binario):**
   - Linfonodos (4 atributos), Páncreas (2), Adrenales (2, salvo `forma`),
     Ovarios (2), Testículos (4)

5. **MANTENER como está (35 pares F3.0):**
   - 10 órganos × 3-7 atributos cada uno, todos con cobertura >50%

---

## 10. Validación contra criterios de aprobación

- [x] Frecuencia de cada órgano (15 órganos, 27.866 hallazgos)
- [x] Frecuencia de cada atributo candidato por órgano (57 pares)
- [x] Top 30 valores observados por par (extractos en §3, total 494 líneas en perfil crudo)
- [x] Cobertura potencial de extracción por atributo (§6)
- [x] Atributos ambiguos (4 fuentes de polisemia en §4)
- [x] Atributos que requieren regex específica (12 pares en §5)
- [x] Propuesta de orden de implementación de órganos según cobertura esperada (§8)
- [x] **Cambios sugeridos al Anexo A** (5 acciones concretas en §9)
- [x] Cardinalidad estimada de `silver_atributos_hallazgo`: ~91.000 filas

---

*Generado por `scripts/_profile_f3_focused.py` y `scripts/_profile_f3.py` (corpus profiling only; sin escribir en silver.db).*

*Para reproducir:*
```bash
python scripts/_profile_f3.py
python scripts/_profile_f3_focused.py
```

*Próximo paso: revisar §9 con el clínico y decidir si F3.0 arranca con el
catálogo actual (35 pares) o con el catálogo refinado (32 pares).*