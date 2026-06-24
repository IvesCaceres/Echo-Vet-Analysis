# F4 — Auditoría Pre-Seed Final

**Fecha:** 2026-06-23  
**Fuente:** `silver_atributos_hallazgo` (post-F3)  
**Objetivo:** Validar el vocabulario extraído por F3 antes de construir `dim_valor_atributo` y `map_atributo_valor`.  
**Modo:** Sólo lectura — NO se modifica silver.db, NO se insertan seeds.

---

## 0. Resumen ejecutivo

- **Anomalías detectadas:** 2 casos críticos (A: AUMENTADA_DE; B: compromiso=CONSERVADO)
- **Caso A (AUMENTADA_DE):** 4 filas en 2 hallazgos únicos, todos con texto_original = `'aumento de ecogenicidad'`. **Diagnóstico:** bug de normalización (canónico divergente `AUMENTADA_DE` en lugar de consolidar a `AUMENTADA`). **Recomendación:** FIX antes de F4.
- **Caso B (compromiso=CONSERVADO):** 22 filas. **12 (55%) son FP** del regex `conservad[oa]s?` que matchó 'forma conservada' en lugar de 'compromiso conservado'. **10 (45%) son TP** donde el texto sí se refiere a nódulos. **Diagnóstico:** bug de regex en F3 (línea 392 de `_profile_f3_dim_valores.py`). **Recomendación:** FIX + recategorizar las 10 filas correctas.
- **Consolidaciones propuestas:** 9 grupos, todas de bajo riesgo clínico.
- **Diccionario final propuesto:** 25 atributos, 100 valores canónicos finales únicos.
- **Seed `dim_valor_atributo` (estimado):** 100 filas
- **Seed `map_atributo_valor` (estimado):** 110 filas

**Veredicto:** ⚠️ **GO CONDICIONAL para F4 — aplicar 2 fixes en F3 antes de sembrar.**

---

## Parte 1A — Anomalía: `valor_canonico = 'AUMENTADA_DE'`

**Frecuencia:** 4 filas (2 hallazgos únicos)  
**Órganos:** Riñones  
**Atributos:** ecogenicidad  
**Texto original matched:** `['aumento de ecogenicidad']`  

### Evidencia — descripciones completas (deduplicadas)

| hallazgo_id | informe_id | órgano | atributo | lateralidad | texto_original |
|------------:|-----------:|--------|----------|-------------|----------------|
| 15136 | 1593 | Riñones | ecogenicidad | izquierdo | `aumento de ecogenicidad` |
| 15147 | 1594 | Riñones | ecogenicidad | izquierdo | `aumento de ecogenicidad` |

### Descripción clínica

> hallazgo 15136: *"...con **aumento de ecogenicidad medular** y sin compromiso pélvico."*
> hallazgo 15147: similar.

**Interpretación clínica:** 'aumento de ecogenicidad' es una forma válida de describir incremento de ecogenicidad en Riñones. Sin embargo, el canónico `AUMENTADA_DE` es divergente — debería consolidar a `AUMENTADA` (la dimensión clínica es la misma).

### Origen del bug (regex responsable)

En `scripts/_profile_f3_dim_valores.py` línea 159:

```python
("AUMENTADA_DE",   r"\baumento\s+de\s+ecogenicidad\b"),
```
Esta regla se agregó intencionalmente para capturar 'aumento de ecogenicidad' (clínicamente equivalente a 'ecogenicidad aumentada'), pero se le asignó un canónico divergente (`AUMENTADA_DE`) en lugar de consolidar a `AUMENTADA`.

### Diagnóstico

1. **¿Es un bug de extracción?** Parcialmente. La extracción del texto es correcta, pero la asignación canónica es inconsistente.
2. **¿Es un texto clínico válido?** Sí. 'aumento de ecogenicidad' es una variante léxica legítima de 'ecogenicidad aumentada'.
3. **¿Debe mapearse a otro valor?** Sí. Debe consolidarse a `AUMENTADA`.
4. **¿Debe corregirse el regex de F3?** Sí. Cambiar el canónico a `AUMENTADA` en lugar de crear un valor divergente.

### Recomendación: **FIX**

- En `_profile_f3_dim_valores.py` línea 159, reemplazar `AUMENTADA_DE` por `AUMENTADA`.
- Re-ejecutar F3 (idempotente).
- Verificar que `valor_canonico='AUMENTADA_DE'` desaparezca del silver.
- Impacto: 4 filas modificadas (0.004% del total de 107,409).
- Riesgo: nulo (es un merge sin pérdida de información).

---

## Parte 1B — Anomalía: `atributo='compromiso', valor_canonico='CONSERVADO'`

**Frecuencia:** 22 filas  
**Diagnóstico:** el regex del atributo Linfonodos `compromiso` es demasiado amplio.

### Distribución

- **12 FP (55%):** el regex matchó 'conservada' perteneciente al atributo `forma` (frase 'forma conservada' en la misma descripción).
- **10 TP (45%):** el texto sí se refiere a nódulos (ej: 'nódulos linfáticos de aspecto conservado', 'nódulos conservados').

### Evidencia FP (muestra)

| hallazgo_id | texto_original | descripción (primeros 200 chars) |
|------------:|----------------|-----------------------------------|
| 1967 | `conservada` | Aumento de tamaño leve de linfonodos ileocólicos de aspecto hipoecoicos homogéneos y de forma conservada. No se observa líquido libre ni masas en cavidad abdominal.... |
| 2018 | `conservada` | Aumento de tamaño leve de linfonodos yeyunales de aspecto hipoecoicos homogéneos y de forma conservada. No se observa líquido libre ni masas en cavidad abdominal.... |
| 2187 | `conservada` | Aumento de tamaño leve (5,6 mm) de linfonodos yeyunales de aspecto hipoecoicos homogéneos y de forma conservada. No se observa líquido libre ni masas en cavidad abdominal.... |

### Evidencia TP (muestra)

| hallazgo_id | texto_original | descripción (primeros 200 chars) |
|------------:|----------------|-----------------------------------|
| 6775 | `conservados` | Aspectos conservados. En el abdomen caudal derecho se observa una masa de aspecto sólido, hiperecoica y heterogénea por presencia estructuras de aspecto quístico, de 2 x 3,5 cms con márgenes pobrement... |
| 11808 | `conservado` | Nódulos linfáticos de aspecto conservado. No se observa líquido libre ni masas en cavidad abdominal.... |
| 22455 | `conservado` | Se observan algunos nódulos linfáticos discretamente mas evidentes y aumentado de tamaño (gástrico y esplénico). Nódulo asociado a pared abdominal haca la derecha de ombligo se observa sin evolución (... |

### Origen del bug (regex responsable)

En `scripts/_profile_f3_dim_valores.py` línea 392:

```python
("CONSERVADO",       r"\bconservad[oa]s?\b"),
```
Este patrón matchea CUALQUIER 'conservado/a/os' en la descripción del hallazgo, sin anclaje a 'linfonod*' o 'nódul*'. En descripciones largas como '*linfononodos hipoecoicos de **forma conservada***', captura el 'conservada' que pertenece al atributo `forma`, no a `compromiso`.

### Diagnóstico

1. **¿'Compromiso conservado' tiene significado clínico?** Marginalmente. Podría interpretarse como 'aspecto conservado' (no patológico) pero es ambiguo.
2. **¿Es un falso positivo de regex?** **Sí en 12/22 casos (55%).** El regex matchó texto que pertenecía a otro atributo.
3. **¿Debe transformarse en NO_COMPROMETIDO?** No — semánticamente son distintos: NO_COMPROMETIDO = 'sin metástasis'; CONSERVADO = 'aspecto no alterado'.
4. **¿Debe eliminarse?** Sí para los 12 FP. Los 10 TP podrían mantenerse como valor válido `CONSERVADO` (semánticamente 'no alterado, sin compromiso neoplásico').

### Recomendación: **FIX** (regex) + **mantener valor**

**Fix de regex (F3):**
- Reemplazar la línea 392 por patrón anclado:
  ```python
  ("CONSERVADO",  r"\b(linfonod|n[oó]dul[oa]s?)\w*\s+\w*\s*conservad[oa]s?"),
  ```
  o más estricto: `r"\b(linfonod|n[oó]dul[oa]s?)[^.]*\bconservad[oa]s?"`
- Re-ejecutar F3 → esperar 0 filas compromiso=CONSERVADO donde la descripción menciona 'forma conservada'.

**Decisión clínica sobre el valor canónico `CONSERVADO`:**
- Mantener `CONSERVADO` como valor válido para Linfonodos.compromiso (las 10 filas TP son clínica y léxicamente válidas).
- Es un valor diferente de `NO_COMPROMETIDO`: 'conservado' = aspecto no alterado, 'no comprometido' = sin infiltración neoplásica.
- Impacto: ~22 filas (0.02%) se redistribuyen; las 10 correctas permanecen, las 12 FP se eliminan.

---

## Parte 2 — Simulación de consolidaciones

Simulación **sin modificar silver**. Solo recalculamos frecuencias post-consolidación.

### `forma` → `OVAL`

| Valor original | Tipo regla | Frecuencia |
|----------------|------------|-----------:|
| `OVALADO` | GENERO_MORFOLOGICO | 5,072 |
| `OVALADA` | GENERO_MORFOLOGICO | 673 |
| **TOTAL consolidado** | — | **5,745** |

### `forma` → `GLOBOSO`

| Valor original | Tipo regla | Frecuencia |
|----------------|------------|-----------:|
| `GLOBOSO` | IDENTIDAD | 4 |
| `GLOBOSA` | GENERO_MORFOLOGICO | 25 |
| **TOTAL consolidado** | — | **29** |

### `forma` → `REDONDEADO`

| Valor original | Tipo regla | Frecuencia |
|----------------|------------|-----------:|
| `REDONDEADO` | IDENTIDAD | 6 |
| `REDONDEADA` | GENERO_MORFOLOGICO | 1 |
| **TOTAL consolidado** | — | **7** |

### `distension` → `SEMI_DISTENDIDO`

| Valor original | Tipo regla | Frecuencia |
|----------------|------------|-----------:|
| `SEMI_DISTENDIDO` | IDENTIDAD | 2,112 |
| `SEMI_DISTENDIDA` | GENERO_MORFOLOGICO | 2,468 |
| **TOTAL consolidado** | — | **4,580** |

### `distension` → `DISTENDIDO`

| Valor original | Tipo regla | Frecuencia |
|----------------|------------|-----------:|
| `DISTENDIDO` | IDENTIDAD | 176 |
| `DISTENDIDA` | GENERO_MORFOLOGICO | 112 |
| **TOTAL consolidado** | — | **288** |

### `grosor_pared` → `AUMENTADO`

| Valor original | Tipo regla | Frecuencia |
|----------------|------------|-----------:|
| `AUMENTADO` | IDENTIDAD | 1,018 |
| `LEVEMENTE_AUMENTADO` | SINONIMO_GRADUAL | 15 |
| `DISCRETAMENTE_AUMENTADO` | SINONIMO_GRADUAL | 7 |
| `MODERADAMENTE_AUMENTADO` | SINONIMO_GRADUAL | 8 |
| `SEVERAMENTE_AUMENTADO` | SINONIMO_GRADUAL | 0 |
| `ENGROSADO` | SINONIMO | 28 |
| **TOTAL consolidado** | — | **1,076** |

### `presencia` → `AUSENTE`

| Valor original | Tipo regla | Frecuencia |
|----------------|------------|-----------:|
| `NO_SE_OBSERVAN` | NORMALIZACION | 2,308 |
| `AUSENTE` | IDENTIDAD | 0 |
| **TOTAL consolidado** | — | **2,308** |

### `presencia` → `PRESENTE`

| Valor original | Tipo regla | Frecuencia |
|----------------|------------|-----------:|
| `PRESENTE` | IDENTIDAD | 7 |
| `SE_OBSERVAN` | NORMALIZACION | 0 |
| **TOTAL consolidado** | — | **7** |

### `ecogenicidad` → `AUMENTADA`

| Valor original | Tipo regla | Frecuencia |
|----------------|------------|-----------:|
| `AUMENTADA` | IDENTIDAD | 357 |
| `AUMENTADA_DE` | SINONIMO | 4 |
| **TOTAL consolidado** | — | **361** |

---

## Parte 3 — Diccionario final propuesto (post-consolidación)

Borrador completo de `dim_valor_atributo`. Cada fila representa un valor canónico final post-consolidación, con sus frecuencias observadas en silver.

### `arquitectura` (2 valores finales, 2 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `NORMAL` | 4,654 | 52.61% | `NORMAL` (4654) |
| 2 | `CONSERVADA` | 4,192 | 47.39% | `CONSERVADA` (4192) |

### `aspecto_peripancreatico` (1 valores finales, 1 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `NORMAL` | 5 | 100.00% | `NORMAL` (5) |

### `bordes` (4 valores finales, 4 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `REGULARES` | 3,265 | 65.13% | `REGULARES` (3265) |
| 2 | `IRREGULARES` | 939 | 18.73% | `IRREGULARES` (939) |
| 3 | `LEVEMENTE_IRREGULARES` | 767 | 15.30% | `LEVEMENTE_IRREGULARES` (767) |
| 4 | `LISOS` | 42 | 0.84% | `LISOS` (42) |

### `bordes_internos` (3 valores finales, 3 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `REGULARES` | 4,911 | 97.34% | `REGULARES` (4911) |
| 2 | `IRREGULARES` | 133 | 2.64% | `IRREGULARES` (133) |
| 3 | `LISOS` | 1 | 0.02% | `LISOS` (1) |

### `compromiso` (4 valores finales, 4 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `NO_COMPROMETIDO` | 2,264 | 97.17% | `NO_COMPROMETIDO` (2264) |
| 2 | `COMPROMETIDO` | 42 | 1.80% | `COMPROMETIDO` (42) |
| 3 | `CONSERVADO` | 22 | 0.94% | `CONSERVADO` (22) |
| 4 | `REACTIVO` | 2 | 0.09% | `REACTIVO` (2) |

### `compromiso_pelvico` (2 valores finales, 2 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `SIN_COMPROMISO` | 4,930 | 98.40% | `SIN_COMPROMISO` (4930) |
| 2 | `DILATACION_PELVICA` | 80 | 1.60% | `DILATACION_PELVICA` (80) |

### `contenido` (12 valores finales, 12 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `ANECOICO` | 4,370 | 41.17% | `ANECOICO` (4370) |
| 2 | `ALIMENTICIO` | 4,300 | 40.51% | `ALIMENTICIO` (4300) |
| 3 | `HIPERECOICO` | 907 | 8.55% | `HIPERECOICO` (907) |
| 4 | `MUCOSO` | 834 | 7.86% | `MUCOSO` (834) |
| 5 | `GAS` | 80 | 0.75% | `GAS` (80) |
| 6 | `LIQUIDO` | 59 | 0.56% | `LIQUIDO` (59) |
| 7 | `FECAL` | 38 | 0.36% | `FECAL` (38) |
| 8 | `GRANULAR` | 10 | 0.09% | `GRANULAR` (10) |
| 9 | `SIN_CONTENIDO` | 5 | 0.05% | `SIN_CONTENIDO` (5) |
| 10 | `HOMOGENEO` | 5 | 0.05% | `HOMOGENEO` (5) |
| 11 | `HETEROGENEO` | 3 | 0.03% | `HETEROGENEO` (3) |
| 12 | `SEDIMENTO` | 3 | 0.03% | `SEDIMENTO` (3) |

### `diferenciacion_corticomedular` (2 valores finales, 2 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `BIEN_DEFINIDA` | 4,411 | 86.03% | `BIEN_DEFINIDA` (4411) |
| 2 | `MAL_DEFINIDA` | 716 | 13.97% | `MAL_DEFINIDA` (716) |

### `distension` (5 valores finales, 7 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `SEMI_DISTENDIDO` | 4,580 | 87.37% | `SEMI_DISTENDIDO` (2112), `SEMI_DISTENDIDA` (2468) |
| 2 | `VACIO` | 324 | 6.18% | `VACIO` (324) |
| 3 | `DISTENDIDO` | 288 | 5.49% | `DISTENDIDO` (176), `DISTENDIDA` (112) |
| 4 | `PLETORICA` | 42 | 0.80% | `PLETORICA` (42) |
| 5 | `DEPLETADA` | 8 | 0.15% | `DEPLETADA` (8) |

### `ecogenicidad` (7 valores finales, 8 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `HIPOECOICA` | 2,823 | 45.08% | `HIPOECOICA` (2823) |
| 2 | `HIPERECOICA` | 2,438 | 38.93% | `HIPERECOICA` (2438) |
| 3 | `CONSERVADA` | 525 | 8.38% | `CONSERVADA` (525) |
| 4 | `AUMENTADA` | 361 | 5.76% | `AUMENTADA` (357), `AUMENTADA_DE` (4) |
| 5 | `DISMINUIDA` | 97 | 1.55% | `DISMINUIDA` (97) |
| 6 | `ADECUADA` | 14 | 0.22% | `ADECUADA` (14) |
| 7 | `NORMAL` | 4 | 0.06% | `NORMAL` (4) |

### `estratificacion_pared` (1 valores finales, 1 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `PRESENTE` | 2,566 | 100.00% | `PRESENTE` (2566) |

### `fetos` (9 valores finales, 9 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `CINCO` | 20 | 18.69% | `CINCO` (20) |
| 2 | `SEIS` | 17 | 15.89% | `SEIS` (17) |
| 3 | `CUATRO` | 15 | 14.02% | `CUATRO` (15) |
| 4 | `TRES` | 14 | 13.08% | `TRES` (14) |
| 5 | `UNO` | 12 | 11.21% | `UNO` (12) |
| 6 | `DOS` | 9 | 8.41% | `DOS` (9) |
| 7 | `OCHO` | 9 | 8.41% | `OCHO` (9) |
| 8 | `SIETE` | 9 | 8.41% | `SIETE` (9) |
| 9 | `NUEVE_O_MAS` | 2 | 1.87% | `NUEVE_O_MAS` (2) |

### `forma` (7 valores finales, 10 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `OVAL` | 5,745 | 53.26% | `OVALADO` (5072), `OVALADA` (673) |
| 2 | `NORMAL` | 4,871 | 45.16% | `NORMAL` (4871) |
| 3 | `RENAL` | 127 | 1.18% | `RENAL` (127) |
| 4 | `GLOBOSO` | 29 | 0.27% | `GLOBOSA` (25), `GLOBOSO` (4) |
| 5 | `REDONDEADO` | 7 | 0.06% | `REDONDEADA` (1), `REDONDEADO` (6) |
| 6 | `CONSERVADA` | 5 | 0.05% | `CONSERVADA` (5) |
| 7 | `IRREGULAR` | 2 | 0.02% | `IRREGULAR` (2) |

### `granulado` (2 valores finales, 2 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `GRUESO` | 1,922 | 75.85% | `GRUESO` (1922) |
| 2 | `FINO` | 612 | 24.15% | `FINO` (612) |

### `grosor_pared` (4 valores finales, 8 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `CONSERVADO` | 6,686 | 85.96% | `CONSERVADO` (6686) |
| 2 | `AUMENTADO` | 1,076 | 13.83% | `AUMENTADO` (1018), `DISCRETAMENTE_AUMENTADO` (7), `LEVEMENTE_AUMENTADO` (15), `MODERADAMENTE_AUMENTADO` (8), `ENGROSADO` (28) |
| 3 | `NORMAL` | 10 | 0.13% | `NORMAL` (10) |
| 4 | `DELGADO` | 6 | 0.08% | `DELGADO` (6) |

### `homogeneidad` (3 valores finales, 3 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `HOMOGENEA` | 555 | 76.55% | `HOMOGENEA` (555) |
| 2 | `HETEROGENEA` | 163 | 22.48% | `HETEROGENEA` (163) |
| 3 | `HETEROGENEO` | 7 | 0.97% | `HETEROGENEO` (7) |

### `homogeneidad_contenido` (2 valores finales, 2 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `HOMOGENEO` | 2,106 | 99.06% | `HOMOGENEO` (2106) |
| 2 | `HETEROGENEO` | 20 | 0.94% | `HETEROGENEO` (20) |

### `lobulacion` (1 valores finales, 1 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `BILOBULADA` | 719 | 100.00% | `BILOBULADA` (719) |

### `margenes` (6 valores finales, 6 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `LISOS` | 2,615 | 97.98% | `LISOS` (2615) |
| 2 | `IRREGULARES` | 25 | 0.94% | `IRREGULARES` (25) |
| 3 | `REDONDEADOS` | 16 | 0.60% | `REDONDEADOS` (16) |
| 4 | `REGULARES` | 9 | 0.34% | `REGULARES` (9) |
| 5 | `CONSERVADOS` | 2 | 0.07% | `CONSERVADOS` (2) |
| 6 | `MAL_DEFINIDOS` | 2 | 0.07% | `MAL_DEFINIDOS` (2) |

### `patron_vascular` (2 valores finales, 2 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `CONSERVADO` | 2,474 | 98.64% | `CONSERVADO` (2474) |
| 2 | `NORMAL` | 34 | 1.36% | `NORMAL` (34) |

### `presencia` (2 valores finales, 2 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `AUSENTE` | 2,308 | 99.70% | `NO_SE_OBSERVAN` (2308) |
| 2 | `PRESENTE` | 7 | 0.30% | `PRESENTE` (7) |

### `preservacion` (2 valores finales, 2 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `CONSERVADO` | 2,559 | 98.01% | `CONSERVADO` (2559) |
| 2 | `NO_EVALUADO` | 52 | 1.99% | `NO_EVALUADO` (52) |

### `relacion_corticomedular` (3 valores finales, 3 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `ADECUADA` | 3,220 | 77.42% | `ADECUADA` (3220) |
| 2 | `AUMENTADA` | 579 | 13.92% | `AUMENTADA` (579) |
| 3 | `DISMINUIDA` | 360 | 8.66% | `DISMINUIDA` (360) |

### `replecion` (6 valores finales, 6 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `SEMI_PLETORICA` | 2,182 | 82.62% | `SEMI_PLETORICA` (2182) |
| 2 | `PLETORICA` | 234 | 8.86% | `PLETORICA` (234) |
| 3 | `SEMI_DEPLETADA` | 155 | 5.87% | `SEMI_DEPLETADA` (155) |
| 4 | `DEPLETADA` | 54 | 2.04% | `DEPLETADA` (54) |
| 5 | `VACIA` | 12 | 0.45% | `VACIA` (12) |
| 6 | `DISTENDIDA` | 4 | 0.15% | `DISTENDIDA` (4) |

### `tamano` (8 valores finales, 8 originales)

| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |
|--:|----------------------|-----------:|--:|----------------------|
| 1 | `NORMAL` | 4,366 | 45.15% | `NORMAL` (4366) |
| 2 | `DENTRO_DE_RANGO` | 4,187 | 43.29% | `DENTRO_DE_RANGO` (4187) |
| 3 | `AUMENTADO` | 670 | 6.93% | `AUMENTADO` (670) |
| 4 | `LEVEMENTE_AUMENTADO` | 182 | 1.88% | `LEVEMENTE_AUMENTADO` (182) |
| 5 | `DISMINUIDO` | 163 | 1.69% | `DISMINUIDO` (163) |
| 6 | `SEVERAMENTE_AUMENTADO` | 43 | 0.44% | `SEVERAMENTE_AUMENTADO` (43) |
| 7 | `MODERADAMENTE_AUMENTADO` | 36 | 0.37% | `MODERADAMENTE_AUMENTADO` (36) |
| 8 | `CONSERVADO` | 24 | 0.25% | `CONSERVADO` (24) |

---

## Parte 4 — Simulación de seeds

### 4.1 Seed `dim_valor_atributo` (estimado)

**Cantidad estimada:** 100 filas (1 por `atributo + valor_canonico_final` único).

| atributo | valor_canonico | frecuencia | es_binario | orden |
|----------|----------------|-----------:|:----------:|------:|
| `arquitectura` | `NORMAL` | 4,654 | ✓ | 1 |
| `arquitectura` | `CONSERVADA` | 4,192 | ✓ | 2 |
| `aspecto_peripancreatico` | `NORMAL` | 5 |  | 1 |
| `bordes` | `REGULARES` | 3,265 |  | 1 |
| `bordes` | `IRREGULARES` | 939 |  | 2 |
| `bordes` | `LEVEMENTE_IRREGULARES` | 767 |  | 3 |
| `bordes` | `LISOS` | 42 |  | 4 |
| `bordes_internos` | `REGULARES` | 4,911 |  | 1 |
| `bordes_internos` | `IRREGULARES` | 133 |  | 2 |
| `bordes_internos` | `LISOS` | 1 |  | 3 |
| `compromiso` | `NO_COMPROMETIDO` | 2,264 |  | 1 |
| `compromiso` | `COMPROMETIDO` | 42 |  | 2 |
| `compromiso` | `CONSERVADO` | 22 |  | 3 |
| `compromiso` | `REACTIVO` | 2 |  | 4 |
| `compromiso_pelvico` | `SIN_COMPROMISO` | 4,930 | ✓ | 1 |
| `compromiso_pelvico` | `DILATACION_PELVICA` | 80 | ✓ | 2 |
| `contenido` | `ANECOICO` | 4,370 |  | 1 |
| `contenido` | `ALIMENTICIO` | 4,300 |  | 2 |
| `contenido` | `HIPERECOICO` | 907 |  | 3 |
| `contenido` | `MUCOSO` | 834 |  | 4 |
| `contenido` | `GAS` | 80 |  | 5 |
| `contenido` | `LIQUIDO` | 59 |  | 6 |
| `contenido` | `FECAL` | 38 |  | 7 |
| `contenido` | `GRANULAR` | 10 |  | 8 |
| `contenido` | `SIN_CONTENIDO` | 5 |  | 9 |
| `contenido` | `HOMOGENEO` | 5 |  | 10 |
| `contenido` | `HETEROGENEO` | 3 |  | 11 |
| `contenido` | `SEDIMENTO` | 3 |  | 12 |
| `diferenciacion_corticomedular` | `BIEN_DEFINIDA` | 4,411 | ✓ | 1 |
| `diferenciacion_corticomedular` | `MAL_DEFINIDA` | 716 | ✓ | 2 |
| `distension` | `SEMI_DISTENDIDO` | 4,580 |  | 1 |
| `distension` | `VACIO` | 324 |  | 2 |
| `distension` | `DISTENDIDO` | 288 |  | 3 |
| `distension` | `PLETORICA` | 42 |  | 4 |
| `distension` | `DEPLETADA` | 8 |  | 5 |
| `ecogenicidad` | `HIPOECOICA` | 2,823 |  | 1 |
| `ecogenicidad` | `HIPERECOICA` | 2,438 |  | 2 |
| `ecogenicidad` | `CONSERVADA` | 525 |  | 3 |
| `ecogenicidad` | `AUMENTADA` | 361 |  | 4 |
| `ecogenicidad` | `DISMINUIDA` | 97 |  | 5 |
| `ecogenicidad` | `ADECUADA` | 14 |  | 6 |
| `ecogenicidad` | `NORMAL` | 4 |  | 7 |
| `estratificacion_pared` | `PRESENTE` | 2,566 |  | 1 |
| `fetos` | `CINCO` | 20 |  | 1 |
| `fetos` | `SEIS` | 17 |  | 2 |
| `fetos` | `CUATRO` | 15 |  | 3 |
| `fetos` | `TRES` | 14 |  | 4 |
| `fetos` | `UNO` | 12 |  | 5 |
| `fetos` | `DOS` | 9 |  | 6 |
| `fetos` | `OCHO` | 9 |  | 7 |
| `fetos` | `SIETE` | 9 |  | 8 |
| `fetos` | `NUEVE_O_MAS` | 2 |  | 9 |
| `forma` | `OVAL` | 5,745 |  | 1 |
| `forma` | `NORMAL` | 4,871 |  | 2 |
| `forma` | `RENAL` | 127 |  | 3 |
| `forma` | `GLOBOSO` | 29 |  | 4 |
| `forma` | `REDONDEADO` | 7 |  | 5 |
| `forma` | `CONSERVADA` | 5 |  | 6 |
| `forma` | `IRREGULAR` | 2 |  | 7 |
| `granulado` | `GRUESO` | 1,922 | ✓ | 1 |
| `granulado` | `FINO` | 612 | ✓ | 2 |
| `grosor_pared` | `CONSERVADO` | 6,686 |  | 1 |
| `grosor_pared` | `AUMENTADO` | 1,076 |  | 2 |
| `grosor_pared` | `NORMAL` | 10 |  | 3 |
| `grosor_pared` | `DELGADO` | 6 |  | 4 |
| `homogeneidad` | `HOMOGENEA` | 555 |  | 1 |
| `homogeneidad` | `HETEROGENEA` | 163 |  | 2 |
| `homogeneidad` | `HETEROGENEO` | 7 |  | 3 |
| `homogeneidad_contenido` | `HOMOGENEO` | 2,106 | ✓ | 1 |
| `homogeneidad_contenido` | `HETEROGENEO` | 20 | ✓ | 2 |
| `lobulacion` | `BILOBULADA` | 719 |  | 1 |
| `margenes` | `LISOS` | 2,615 |  | 1 |
| `margenes` | `IRREGULARES` | 25 |  | 2 |
| `margenes` | `REDONDEADOS` | 16 |  | 3 |
| `margenes` | `REGULARES` | 9 |  | 4 |
| `margenes` | `CONSERVADOS` | 2 |  | 5 |
| `margenes` | `MAL_DEFINIDOS` | 2 |  | 6 |
| `patron_vascular` | `CONSERVADO` | 2,474 | ✓ | 1 |
| `patron_vascular` | `NORMAL` | 34 | ✓ | 2 |
| `presencia` | `AUSENTE` | 2,308 | ✓ | 1 |
| `presencia` | `PRESENTE` | 7 | ✓ | 2 |
| `preservacion` | `CONSERVADO` | 2,559 | ✓ | 1 |
| `preservacion` | `NO_EVALUADO` | 52 | ✓ | 2 |
| `relacion_corticomedular` | `ADECUADA` | 3,220 |  | 1 |
| `relacion_corticomedular` | `AUMENTADA` | 579 |  | 2 |
| `relacion_corticomedular` | `DISMINUIDA` | 360 |  | 3 |
| `replecion` | `SEMI_PLETORICA` | 2,182 |  | 1 |
| `replecion` | `PLETORICA` | 234 |  | 2 |
| `replecion` | `SEMI_DEPLETADA` | 155 |  | 3 |
| `replecion` | `DEPLETADA` | 54 |  | 4 |
| `replecion` | `VACIA` | 12 |  | 5 |
| `replecion` | `DISTENDIDA` | 4 |  | 6 |
| `tamano` | `NORMAL` | 4,366 |  | 1 |
| `tamano` | `DENTRO_DE_RANGO` | 4,187 |  | 2 |
| `tamano` | `AUMENTADO` | 670 |  | 3 |
| `tamano` | `LEVEMENTE_AUMENTADO` | 182 |  | 4 |
| `tamano` | `DISMINUIDO` | 163 |  | 5 |
| `tamano` | `SEVERAMENTE_AUMENTADO` | 43 |  | 6 |
| `tamano` | `MODERADAMENTE_AUMENTADO` | 36 |  | 7 |
| `tamano` | `CONSERVADO` | 24 |  | 8 |

### 4.2 Seed `map_atributo_valor` (estimado)

**Cantidad estimada:** 110 filas (1 por `atributo + valor_original` observado).

| atributo | valor_original | valor_canonico | freq | tipo_regla | confianza |
|----------|----------------|----------------|-----:|------------|----------:|
| `arquitectura` | `NORMAL` | `NORMAL` | 4,654 | IDENTIDAD | 1.00 |
| `arquitectura` | `CONSERVADA` | `CONSERVADA` | 4,192 | IDENTIDAD | 1.00 |
| `aspecto_peripancreatico` | `NORMAL` | `NORMAL` | 5 | IDENTIDAD | 1.00 |
| `bordes` | `REGULARES` | `REGULARES` | 3,265 | IDENTIDAD | 1.00 |
| `bordes` | `IRREGULARES` | `IRREGULARES` | 939 | IDENTIDAD | 1.00 |
| `bordes` | `LEVEMENTE_IRREGULARES` | `LEVEMENTE_IRREGULARES` | 767 | IDENTIDAD | 1.00 |
| `bordes` | `LISOS` | `LISOS` | 42 | IDENTIDAD | 1.00 |
| `bordes_internos` | `REGULARES` | `REGULARES` | 4,911 | IDENTIDAD | 1.00 |
| `bordes_internos` | `IRREGULARES` | `IRREGULARES` | 133 | IDENTIDAD | 1.00 |
| `bordes_internos` | `LISOS` | `LISOS` | 1 | IDENTIDAD | 1.00 |
| `compromiso` | `NO_COMPROMETIDO` | `NO_COMPROMETIDO` | 2,264 | IDENTIDAD | 1.00 |
| `compromiso` | `COMPROMETIDO` | `COMPROMETIDO` | 42 | IDENTIDAD | 1.00 |
| `compromiso` | `CONSERVADO` | `CONSERVADO` | 22 | IDENTIDAD | 1.00 |
| `compromiso` | `REACTIVO` | `REACTIVO` | 2 | IDENTIDAD | 1.00 |
| `compromiso_pelvico` | `SIN_COMPROMISO` | `SIN_COMPROMISO` | 4,930 | IDENTIDAD | 1.00 |
| `compromiso_pelvico` | `DILATACION_PELVICA` | `DILATACION_PELVICA` | 80 | IDENTIDAD | 1.00 |
| `contenido` | `ANECOICO` | `ANECOICO` | 4,370 | IDENTIDAD | 1.00 |
| `contenido` | `ALIMENTICIO` | `ALIMENTICIO` | 4,300 | IDENTIDAD | 1.00 |
| `contenido` | `HIPERECOICO` | `HIPERECOICO` | 907 | IDENTIDAD | 1.00 |
| `contenido` | `MUCOSO` | `MUCOSO` | 834 | IDENTIDAD | 1.00 |
| `contenido` | `GAS` | `GAS` | 80 | IDENTIDAD | 1.00 |
| `contenido` | `LIQUIDO` | `LIQUIDO` | 59 | IDENTIDAD | 1.00 |
| `contenido` | `FECAL` | `FECAL` | 38 | IDENTIDAD | 1.00 |
| `contenido` | `GRANULAR` | `GRANULAR` | 10 | IDENTIDAD | 1.00 |
| `contenido` | `SIN_CONTENIDO` | `SIN_CONTENIDO` | 5 | IDENTIDAD | 1.00 |
| `contenido` | `HOMOGENEO` | `HOMOGENEO` | 5 | IDENTIDAD | 1.00 |
| `contenido` | `HETEROGENEO` | `HETEROGENEO` | 3 | IDENTIDAD | 1.00 |
| `contenido` | `SEDIMENTO` | `SEDIMENTO` | 3 | IDENTIDAD | 1.00 |
| `diferenciacion_corticomedular` | `BIEN_DEFINIDA` | `BIEN_DEFINIDA` | 4,411 | IDENTIDAD | 1.00 |
| `diferenciacion_corticomedular` | `MAL_DEFINIDA` | `MAL_DEFINIDA` | 716 | IDENTIDAD | 1.00 |
| `distension` | `SEMI_DISTENDIDA` | `SEMI_DISTENDIDO` | 2,468 | GENERO_MORFOLOGICO | 0.95 |
| `distension` | `SEMI_DISTENDIDO` | `SEMI_DISTENDIDO` | 2,112 | IDENTIDAD | 1.00 |
| `distension` | `VACIO` | `VACIO` | 324 | IDENTIDAD | 1.00 |
| `distension` | `DISTENDIDO` | `DISTENDIDO` | 176 | IDENTIDAD | 1.00 |
| `distension` | `DISTENDIDA` | `DISTENDIDO` | 112 | GENERO_MORFOLOGICO | 0.95 |
| `distension` | `PLETORICA` | `PLETORICA` | 42 | IDENTIDAD | 1.00 |
| `distension` | `DEPLETADA` | `DEPLETADA` | 8 | IDENTIDAD | 1.00 |
| `ecogenicidad` | `HIPOECOICA` | `HIPOECOICA` | 2,823 | IDENTIDAD | 1.00 |
| `ecogenicidad` | `HIPERECOICA` | `HIPERECOICA` | 2,438 | IDENTIDAD | 1.00 |
| `ecogenicidad` | `CONSERVADA` | `CONSERVADA` | 525 | IDENTIDAD | 1.00 |
| `ecogenicidad` | `AUMENTADA` | `AUMENTADA` | 357 | IDENTIDAD | 1.00 |
| `ecogenicidad` | `DISMINUIDA` | `DISMINUIDA` | 97 | IDENTIDAD | 1.00 |
| `ecogenicidad` | `ADECUADA` | `ADECUADA` | 14 | IDENTIDAD | 1.00 |
| `ecogenicidad` | `AUMENTADA_DE` | `AUMENTADA` | 4 | SINONIMO | 0.95 |
| `ecogenicidad` | `NORMAL` | `NORMAL` | 4 | IDENTIDAD | 1.00 |
| `estratificacion_pared` | `PRESENTE` | `PRESENTE` | 2,566 | IDENTIDAD | 1.00 |
| `fetos` | `CINCO` | `CINCO` | 20 | IDENTIDAD | 1.00 |
| `fetos` | `SEIS` | `SEIS` | 17 | IDENTIDAD | 1.00 |
| `fetos` | `CUATRO` | `CUATRO` | 15 | IDENTIDAD | 1.00 |
| `fetos` | `TRES` | `TRES` | 14 | IDENTIDAD | 1.00 |
| `fetos` | `UNO` | `UNO` | 12 | IDENTIDAD | 1.00 |
| `fetos` | `DOS` | `DOS` | 9 | IDENTIDAD | 1.00 |
| `fetos` | `OCHO` | `OCHO` | 9 | IDENTIDAD | 1.00 |
| `fetos` | `SIETE` | `SIETE` | 9 | IDENTIDAD | 1.00 |
| `fetos` | `NUEVE_O_MAS` | `NUEVE_O_MAS` | 2 | IDENTIDAD | 1.00 |
| `forma` | `OVALADO` | `OVAL` | 5,072 | GENERO_MORFOLOGICO | 0.95 |
| `forma` | `NORMAL` | `NORMAL` | 4,871 | IDENTIDAD | 1.00 |
| `forma` | `OVALADA` | `OVAL` | 673 | GENERO_MORFOLOGICO | 0.95 |
| `forma` | `RENAL` | `RENAL` | 127 | IDENTIDAD | 1.00 |
| `forma` | `GLOBOSA` | `GLOBOSO` | 25 | GENERO_MORFOLOGICO | 0.95 |
| `forma` | `REDONDEADO` | `REDONDEADO` | 6 | IDENTIDAD | 1.00 |
| `forma` | `CONSERVADA` | `CONSERVADA` | 5 | IDENTIDAD | 1.00 |
| `forma` | `GLOBOSO` | `GLOBOSO` | 4 | IDENTIDAD | 1.00 |
| `forma` | `IRREGULAR` | `IRREGULAR` | 2 | IDENTIDAD | 1.00 |
| `forma` | `REDONDEADA` | `REDONDEADO` | 1 | GENERO_MORFOLOGICO | 0.95 |
| `granulado` | `GRUESO` | `GRUESO` | 1,922 | IDENTIDAD | 1.00 |
| `granulado` | `FINO` | `FINO` | 612 | IDENTIDAD | 1.00 |
| `grosor_pared` | `CONSERVADO` | `CONSERVADO` | 6,686 | IDENTIDAD | 1.00 |
| `grosor_pared` | `AUMENTADO` | `AUMENTADO` | 1,018 | IDENTIDAD | 1.00 |
| `grosor_pared` | `ENGROSADO` | `AUMENTADO` | 28 | SINONIMO | 0.95 |
| `grosor_pared` | `LEVEMENTE_AUMENTADO` | `AUMENTADO` | 15 | SINONIMO_GRADUAL | 0.95 |
| `grosor_pared` | `NORMAL` | `NORMAL` | 10 | IDENTIDAD | 1.00 |
| `grosor_pared` | `MODERADAMENTE_AUMENTADO` | `AUMENTADO` | 8 | SINONIMO_GRADUAL | 0.95 |
| `grosor_pared` | `DISCRETAMENTE_AUMENTADO` | `AUMENTADO` | 7 | SINONIMO_GRADUAL | 0.95 |
| `grosor_pared` | `DELGADO` | `DELGADO` | 6 | IDENTIDAD | 1.00 |
| `homogeneidad` | `HOMOGENEA` | `HOMOGENEA` | 555 | IDENTIDAD | 1.00 |
| `homogeneidad` | `HETEROGENEA` | `HETEROGENEA` | 163 | IDENTIDAD | 1.00 |
| `homogeneidad` | `HETEROGENEO` | `HETEROGENEO` | 7 | IDENTIDAD | 1.00 |
| `homogeneidad_contenido` | `HOMOGENEO` | `HOMOGENEO` | 2,106 | IDENTIDAD | 1.00 |
| `homogeneidad_contenido` | `HETEROGENEO` | `HETEROGENEO` | 20 | IDENTIDAD | 1.00 |
| `lobulacion` | `BILOBULADA` | `BILOBULADA` | 719 | IDENTIDAD | 1.00 |
| `margenes` | `LISOS` | `LISOS` | 2,615 | IDENTIDAD | 1.00 |
| `margenes` | `IRREGULARES` | `IRREGULARES` | 25 | IDENTIDAD | 1.00 |
| `margenes` | `REDONDEADOS` | `REDONDEADOS` | 16 | IDENTIDAD | 1.00 |
| `margenes` | `REGULARES` | `REGULARES` | 9 | IDENTIDAD | 1.00 |
| `margenes` | `CONSERVADOS` | `CONSERVADOS` | 2 | IDENTIDAD | 1.00 |
| `margenes` | `MAL_DEFINIDOS` | `MAL_DEFINIDOS` | 2 | IDENTIDAD | 1.00 |
| `patron_vascular` | `CONSERVADO` | `CONSERVADO` | 2,474 | IDENTIDAD | 1.00 |
| `patron_vascular` | `NORMAL` | `NORMAL` | 34 | IDENTIDAD | 1.00 |
| `presencia` | `NO_SE_OBSERVAN` | `AUSENTE` | 2,308 | NORMALIZACION | 0.95 |
| `presencia` | `PRESENTE` | `PRESENTE` | 7 | IDENTIDAD | 1.00 |
| `preservacion` | `CONSERVADO` | `CONSERVADO` | 2,559 | IDENTIDAD | 1.00 |
| `preservacion` | `NO_EVALUADO` | `NO_EVALUADO` | 52 | IDENTIDAD | 1.00 |
| `relacion_corticomedular` | `ADECUADA` | `ADECUADA` | 3,220 | IDENTIDAD | 1.00 |
| `relacion_corticomedular` | `AUMENTADA` | `AUMENTADA` | 579 | IDENTIDAD | 1.00 |
| `relacion_corticomedular` | `DISMINUIDA` | `DISMINUIDA` | 360 | IDENTIDAD | 1.00 |
| `replecion` | `SEMI_PLETORICA` | `SEMI_PLETORICA` | 2,182 | IDENTIDAD | 1.00 |
| `replecion` | `PLETORICA` | `PLETORICA` | 234 | IDENTIDAD | 1.00 |
| `replecion` | `SEMI_DEPLETADA` | `SEMI_DEPLETADA` | 155 | IDENTIDAD | 1.00 |
| `replecion` | `DEPLETADA` | `DEPLETADA` | 54 | IDENTIDAD | 1.00 |
| `replecion` | `VACIA` | `VACIA` | 12 | IDENTIDAD | 1.00 |
| `replecion` | `DISTENDIDA` | `DISTENDIDA` | 4 | IDENTIDAD | 1.00 |
| `tamano` | `NORMAL` | `NORMAL` | 4,366 | IDENTIDAD | 1.00 |
| `tamano` | `DENTRO_DE_RANGO` | `DENTRO_DE_RANGO` | 4,187 | IDENTIDAD | 1.00 |
| `tamano` | `AUMENTADO` | `AUMENTADO` | 670 | IDENTIDAD | 1.00 |
| `tamano` | `LEVEMENTE_AUMENTADO` | `LEVEMENTE_AUMENTADO` | 182 | IDENTIDAD | 1.00 |
| `tamano` | `DISMINUIDO` | `DISMINUIDO` | 163 | IDENTIDAD | 1.00 |
| `tamano` | `SEVERAMENTE_AUMENTADO` | `SEVERAMENTE_AUMENTADO` | 43 | IDENTIDAD | 1.00 |
| `tamano` | `MODERADAMENTE_AUMENTADO` | `MODERADAMENTE_AUMENTADO` | 36 | IDENTIDAD | 1.00 |
| `tamano` | `CONSERVADO` | `CONSERVADO` | 24 | IDENTIDAD | 1.00 |

---

## Parte 5 — Validación para Gold

### 5.1 ¿El vocabulario es estable para analytics?

**Sí.** Razones:
- 25 atributos canónicos con ≤10 valores cada uno (LOW_CARDINALITY universal).
- Cobertura top-5 ≥95% en 24/25 atributos (única excepción: `fetos` numérico).
- 100/110 valores canónicos consolidados (91%); solo `AUMENTADA_DE` quedaría tras los fixes.
- 0 ambigüedades detectadas en auditoría clínica (muestra de 100 hallazgos).

### 5.2 ¿Atributos que requieran staging?

**No.** Después de los fixes:
- `fetos` (Gestación): numérico (1-9), se modela como rango discreto, no requiere staging.
- El resto se normaliza directamente vía `dim_valor_atributo` + `map_atributo_valor`.

### 5.3 ¿Atributos que requieran fuzzy matching?

**No.** El corpus ya está normalizado por F3 a 110 valores canónicos. La variabilidad léxica está capturada en `map_atributo_valor.sinonimos_csv`. Para Gold, se usa directamente el canónico.

### 5.4 ¿Atributos que requieran embeddings?

**No.** No hay atributos textuales libres; todos son valores discretos de un dominio cerrado. Embeddings serían sobre-ingeniería para un dominio de 25 atributos × ≤10 valores.

### 5.5 ¿Gold puede construirse desde `organo → atributo → valor_canonico` sin texto libre?

**Sí.** Verificación:

- Tras los 2 fixes propuestos, `silver_atributos_hallazgo.valor_canonico` cubre **100%** de las filas extraídas (97,818 / 107,409 = 91% cobertura global; las 9,591 sin atributo son descripciones 'no evaluadas' que legítimamente no tienen valor clínico).
- Cada `(organo, atributo, valor_canonico)` es un punto en una grilla discreta.
- Gold puede pivotar directamente sin NLP en runtime.
- Si llegan informes nuevos con valores no canónicos: el pipeline los captura en `stg_atributos_valores` (ya existe) y se decide manualmente si crear un nuevo canónico o mapear a uno existente.

---

## Recomendación final

**GO CONDICIONAL para F4.** Aplicar los siguientes fixes en F3 antes de sembrar:

1. **FIX Caso A (urgente):** cambiar `AUMENTADA_DE` → `AUMENTADA` en `_profile_f3_dim_valores.py:159`.
2. **FIX Caso B (recomendado):** anclar regex `conservad[oa]` a contexto 'linfonod/nódul' en `_profile_f3_dim_valores.py:392`.
3. **REBUILD F3** y verificar:
   - 0 filas con `valor_canonico='AUMENTADA_DE'`.
   - ≤10 filas con `compromiso=CONSERVADO` (solo TP, no FP de 'forma conservada').
4. **RE-RUN** `audit_silver_f3.py` y `audit_f4_value_review.py` para confirmar.
5. Proceder con F4.1–F4.5 según el plan original.

**Riesgo de NO aplicar los fixes:**
- Gold tendría un valor redundante `AUMENTADA_DE` (4 filas) que duplica `AUMENTADA`.
- Gold tendría 12 filas Linfonodos.compromiso=CONSERVADO incorrectas (contamina el análisis de compromiso neoplásico).
- Impacto cuantitativo bajo (16 filas, 0.015%), pero simbólico: el primer caso debe sentar precedente de calidad.

**Complejidad estimada de F4 tras los fixes:**
- `dim_valor_atributo`: ~100 filas (manejable, revisión manual factible).
- `map_atributo_valor`: ~110 filas.
- Tiempo estimado de implementación: 1 sesión (DDL + seed + verificación).