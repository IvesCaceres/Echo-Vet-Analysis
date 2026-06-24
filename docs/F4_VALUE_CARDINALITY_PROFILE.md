# F4 — Perfil de Cardinalidad de Valores Clínicos

**Fecha:** 2026-06-23  
**Fuente:** `silver_atributos_hallazgo` (post-F3, 107,409 filas)  
**Objetivo:** Inventariar valores observados para diseñar `dim_valor_atributo` y `map_atributo_valor`.

## 0. Resumen ejecutivo

- **Total pares (órgano, atributo) evaluados:** 54
- **Total atributos únicos (reutilizados entre órganos):** 25
- **Cardinalidad:** LOW=54, MEDIUM=0, HIGH=0
- **Gobernanza:** AUTO_APROBABLE=53  REQUIERE_STAGING=1
- **Estimación `dim_valor_atributo` (fase 1):** ~110 filas
- **Estimación `map_atributo_valor` (fase 1):** ~171 filas

**Veredicto:** ✅ **Sí, estamos listos para construir F4.**
Todos los atributos son LOW_CARDINALITY (≤10 valores). La cobertura top-5 ≥95% en la mayoría de los casos.
No se detectan riesgos de explosión combinatoria.

## 1. Top 20 atributos más fáciles de normalizar (AUTO_APROBABLE)

Criterio: cobertura top-5 ≥95% **o** ≥95% de filas en familias clínicas conocidas, ≤20% únicos.

| # | Órgano | Atributo | Total | Distintos | Top-5 % | En familia % | Card. |
|---|--------|----------|------:|----------:|--------:|-------------:|:-----:|
| 1 | Riñones | diferenciacion_corticomedular | 5,127 | 2 | 100.0% | 100.0% | LOW_CARDINALITY |
| 2 | Adrenales | forma | 4,764 | 1 | 100.0% | 100.0% | LOW_CARDINALITY |
| 3 | Adrenales | arquitectura | 4,721 | 2 | 100.0% | 100.0% | LOW_CARDINALITY |
| 4 | Riñones | relacion_corticomedular | 4,159 | 3 | 100.0% | 100.0% | LOW_CARDINALITY |
| 5 | Bazo | tamano | 2,601 | 5 | 100.0% | 100.0% | LOW_CARDINALITY |
| 6 | Intestino | grosor_pared | 2,560 | 5 | 100.0% | 100.0% | LOW_CARDINALITY |
| 7 | Estómago | estratificacion_pared | 2,552 | 1 | 100.0% | 100.0% | LOW_CARDINALITY |
| 8 | Estómago | grosor_pared | 2,543 | 3 | 100.0% | 100.0% | LOW_CARDINALITY |
| 9 | Vesícula | bordes_internos | 2,538 | 2 | 100.0% | 100.0% | LOW_CARDINALITY |
| 10 | Hígado | patron_vascular | 2,508 | 2 | 100.0% | 100.0% | LOW_CARDINALITY |
| 11 | Vejiga | bordes_internos | 2,507 | 3 | 100.0% | 100.0% | LOW_CARDINALITY |
| 12 | Bazo | arquitectura | 2,368 | 2 | 100.0% | 100.0% | LOW_CARDINALITY |
| 13 | Linfonodos | compromiso | 2,330 | 4 | 100.0% | 100.0% | LOW_CARDINALITY |
| 14 | Linfonodos | presencia | 2,315 | 2 | 100.0% | 100.0% | LOW_CARDINALITY |
| 15 | Vejiga | homogeneidad_contenido | 2,126 | 2 | 100.0% | 100.0% | LOW_CARDINALITY |
| 16 | Hígado | arquitectura | 1,757 | 2 | 100.0% | 100.0% | LOW_CARDINALITY |
| 17 | Próstata | homogeneidad | 718 | 2 | 100.0% | 100.0% | LOW_CARDINALITY |
| 18 | Próstata | tamano | 631 | 3 | 100.0% | 100.0% | LOW_CARDINALITY |
| 19 | Bazo | forma | 102 | 2 | 100.0% | 100.0% | LOW_CARDINALITY |
| 20 | Útero | tamano | 22 | 2 | 100.0% | 100.0% | LOW_CARDINALITY |

## 2. Top 20 atributos más complejos (REQUIERE_STAGING)

Criterio: >20% valores únicos, >50 valores distintos, o cobertura top-5 <95%.

| # | Órgano | Atributo | Total | Distintos | Únicos % | Top-5 % | En familia % |
|---|--------|----------|------:|----------:|---------:|--------:|-------------:|
| 1 | Gestación | fetos | 107 | 9 | 0.0% | 72.9% | 0.0% |

## 3. Estimación de filas iniciales

- **`dim_valor_atributo`** (1 fila por `atributo + valor` único, reutilizable entre órganos): **~110 filas**
- **`map_atributo_valor`** (1 fila por `par (órgano, atributo) + valor` con sinónimos): **~171 filas**
- **Pares (órgano, atributo) únicos:** 54
- **Atributos únicos:** 25

Notas:
- `dim_valor_atributo` se reusa entre órganos. Ej: `atributo='tamano'`, `valor='AUMENTADO'` existe en Hígado, Bazo, Riñones, Bazo, etc. → 1 fila, no N.
- `map_atributo_valor` une un par (órgano, atributo, valor) con sus variantes léxicas. Aquí 1 fila inicial ≈ 1 (órgano, atributo, valor) observado.

## 4. Recomendación de estrategia F4

### Fase 1: Bulk insert desde `silver_atributos_hallazgo`
- Construir `dim_valor_atributo` y `map_atributo_valor` a partir de los valores canónicos ya extraídos por F3.
- Esto crea la base **observada** del corpus sin depender de LLM/diccionario manual.
- Permite poblar Gold y pivotar inmediatamente.

### Fase 2: Clustering semántico de variantes
- Revisar manualmente los 20 pares más complejos (si los hay).
- Para cada valor, capturar variantes léxicas en `map_atributo_valor.sinonimos_csv` (p.ej. `'aumentada','aumentado','aumentados','incrementado'`).

### Fase 3: Validación cruzada
- Auditoría con muestra para verificar que las variantes cubren el corpus.

## 5. Riesgos detectados

- **Riesgo bajo: cardinalidad.** Todos LOW (≤10). No hay explosión combinatoria.
- **Riesgo bajo: ambigüedad semántica.** Familias clínicas canónicas cubren 68.4% del corpus (ponderado por filas).
- **Riesgo medio: valores numéricos sueltos.** `valor_numerico` se usa en Gestación/fetos. Verificar que la codificación en palabras (UNO, DOS, ...) está bien normalizada.
- **Riesgo bajo: cobertura por órgano.** Atributos como `tamano` en Testículos (22 filas) y Ovarios (1 fila) tienen muy pocas muestras; pueden tener valores ruidosos que distorsionen stats.

## 6. Plan de implementación F4

1. **F4.1 — DDL de `dim_valor_atributo`** (id, atributo_id, valor, sinonimos, patron_extraccion, es_binario_true, orden, activo).
2. **F4.2 — DDL de `map_atributo_valor`** (dim_organo_atributo_id, dim_valor_atributo_id, sinonimos_csv, estado_revision).
3. **F4.3 — Seed automático**: para cada `valor_canonico` no NULL en `silver_atributos_hallazgo`, insertar en `dim_valor_atributo` (con `patron_extraccion` derivado de regex del F3).
4. **F4.4 — Cross-link FK**: poblar `silver_atributos_hallazgo.dim_valor_atributo_id` a partir de `valor_canonico` + `dim_organo_atributo_id`.
5. **F4.5 — Verificación**: `verify_silver_f4.py` con assertions sobre cobertura, integridad FK, 0 NULL huérfanos.

## 7. Detalle por par (órgano, atributo)

Ordenado por total de filas descendente.

| Órgano | Atributo | Tipo | Total | Distintos | Únicos % | Top-5 % | En familia % | Card. | Gobernanza | Familias |
|--------|----------|------|------:|----------:|---------:|--------:|-------------:|:-----:|:----------:|----------|
| Riñones | forma | texto | 5,215 | 6 | 0.0% | 100.0% | 0.2% | LOW_CARDINALITY | AUTO_APROBABLE | IRREGULAR, NORMAL |
| Riñones | diferenciacion_corticomedular | texto | 5,127 | 2 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | IRREGULAR, REGULAR |
| Riñones | compromiso_pelvico | texto | 5,010 | 2 | 0.0% | 100.0% | 98.4% | LOW_CARDINALITY | AUTO_APROBABLE | AUSENTE |
| Riñones | bordes | texto | 5,004 | 4 | 0.0% | 100.0% | 84.7% | LOW_CARDINALITY | AUTO_APROBABLE | IRREGULAR, REGULAR |
| Riñones | tamano | texto | 4,959 | 8 | 0.0% | 98.2% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | AUMENTADO, DISMINUIDO, NORMAL |
| Adrenales | forma | texto | 4,764 | 1 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | NORMAL |
| Adrenales | arquitectura | texto | 4,721 | 2 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | NORMAL |
| Riñones | relacion_corticomedular | texto | 4,159 | 3 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | AUMENTADO, DISMINUIDO, NORMAL |
| Riñones | ecogenicidad | texto | 3,017 | 8 | 0.0% | 99.3% | 31.3% | LOW_CARDINALITY | AUTO_APROBABLE | AUMENTADO, DISMINUIDO, NORMAL |
| Intestino | contenido | texto | 2,663 | 4 | 0.0% | 100.0% | 0.0% | LOW_CARDINALITY | AUTO_APROBABLE | — |
| Estómago | contenido | texto | 2,653 | 5 | 0.0% | 100.0% | 0.0% | LOW_CARDINALITY | AUTO_APROBABLE | — |
| Vejiga | contenido | texto | 2,644 | 6 | 0.0% | 99.9% | 0.3% | LOW_CARDINALITY | AUTO_APROBABLE | HETEROGENEO, HOMOGENEO |
| Vejiga | replecion | texto | 2,641 | 6 | 0.0% | 99.8% | 0.0% | LOW_CARDINALITY | AUTO_APROBABLE | — |
| Hígado | margenes | texto | 2,638 | 4 | 0.0% | 100.0% | 99.3% | LOW_CARDINALITY | AUTO_APROBABLE | IRREGULAR, REGULAR |
| Vesícula | distension | texto | 2,630 | 4 | 0.0% | 100.0% | 0.0% | LOW_CARDINALITY | AUTO_APROBABLE | — |
| Vesícula | contenido | texto | 2,620 | 2 | 0.0% | 100.0% | 0.0% | LOW_CARDINALITY | AUTO_APROBABLE | — |
| Estómago | distension | texto | 2,612 | 3 | 0.0% | 100.0% | 0.0% | LOW_CARDINALITY | AUTO_APROBABLE | — |
| Páncreas | preservacion | binario | 2,611 | 2 | 0.0% | 100.0% | 98.0% | LOW_CARDINALITY | AUTO_APROBABLE | NORMAL |
| Bazo | tamano | texto | 2,601 | 5 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | AUMENTADO, DISMINUIDO, NORMAL |
| Intestino | grosor_pared | texto | 2,560 | 5 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | AUMENTADO, NORMAL |
| Estómago | estratificacion_pared | texto | 2,552 | 1 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | PRESENTE |
| Vejiga | grosor_pared | texto | 2,549 | 4 | 0.0% | 100.0% | 99.1% | LOW_CARDINALITY | AUTO_APROBABLE | AUMENTADO, NORMAL |
| Estómago | grosor_pared | texto | 2,543 | 3 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | AUMENTADO, NORMAL |
| Vesícula | bordes_internos | texto | 2,538 | 2 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | IRREGULAR, REGULAR |
| Hígado | granulado | texto | 2,534 | 2 | 0.0% | 100.0% | 0.0% | LOW_CARDINALITY | AUTO_APROBABLE | — |
| Hígado | ecogenicidad | texto | 2,524 | 5 | 0.0% | 100.0% | 2.0% | LOW_CARDINALITY | AUTO_APROBABLE | AUMENTADO, DISMINUIDO, NORMAL |
| Hígado | patron_vascular | texto | 2,508 | 2 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | NORMAL |
| Vejiga | bordes_internos | texto | 2,507 | 3 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | IRREGULAR, REGULAR |
| Bazo | arquitectura | texto | 2,368 | 2 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | NORMAL |
| Linfonodos | compromiso | binario | 2,330 | 4 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | AUSENTE, NORMAL, PRESENTE |
| Linfonodos | presencia | binario | 2,315 | 2 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | AUSENTE, PRESENTE |
| Vejiga | homogeneidad_contenido | texto | 2,126 | 2 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | HETEROGENEO, HOMOGENEO |
| Hígado | arquitectura | texto | 1,757 | 2 | 0.1% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | NORMAL |
| Hígado | tamano | texto | 1,454 | 7 | 0.1% | 99.8% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | AUMENTADO, DISMINUIDO, NORMAL |
| Próstata | lobulacion | texto | 719 | 1 | 0.0% | 100.0% | 0.0% | LOW_CARDINALITY | AUTO_APROBABLE | — |
| Próstata | homogeneidad | texto | 718 | 2 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | HETEROGENEO, HOMOGENEO |
| Próstata | ecogenicidad | texto | 715 | 2 | 0.0% | 100.0% | 0.0% | LOW_CARDINALITY | AUTO_APROBABLE | — |
| Próstata | forma | texto | 699 | 3 | 0.1% | 100.0% | 0.0% | LOW_CARDINALITY | AUTO_APROBABLE | — |
| Próstata | tamano | texto | 631 | 3 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | AUMENTADO, DISMINUIDO, NORMAL |
| Vesícula | grosor_pared | texto | 118 | 3 | 0.0% | 100.0% | 96.6% | LOW_CARDINALITY | AUTO_APROBABLE | AUMENTADO, NORMAL |
| Gestación | fetos | numerico | 107 | 9 | 0.0% | 72.9% | 0.0% | LOW_CARDINALITY | REQUIERE_STAGING | — |
| Bazo | forma | texto | 102 | 2 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | NORMAL |
| Útero | contenido | texto | 34 | 3 | 2.9% | 100.0% | 2.9% | LOW_CARDINALITY | AUTO_APROBABLE | HOMOGENEO |
| Bazo | margenes | texto | 31 | 3 | 0.0% | 100.0% | 93.5% | LOW_CARDINALITY | AUTO_APROBABLE | IRREGULAR, REGULAR |
| Útero | tamano | texto | 22 | 2 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | AUMENTADO, NORMAL |
| Intestino | estratificacion_pared | texto | 14 | 1 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | PRESENTE |
| Hígado | bordes | texto | 9 | 2 | 11.1% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | IRREGULAR, REGULAR |
| Útero | grosor_pared | texto | 8 | 3 | 25.0% | 100.0% | 12.5% | LOW_CARDINALITY | AUTO_APROBABLE | NORMAL |
| Testículos | homogeneidad | texto | 7 | 1 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | HETEROGENEO |
| Testículos | ecogenicidad | texto | 6 | 2 | 16.7% | 100.0% | 16.7% | LOW_CARDINALITY | AUTO_APROBABLE | NORMAL |
| Páncreas | aspecto_peripancreatico | binario | 5 | 1 | 0.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | NORMAL |
| Testículos | forma | texto | 5 | 1 | 0.0% | 100.0% | 0.0% | LOW_CARDINALITY | AUTO_APROBABLE | — |
| Testículos | tamano | texto | 4 | 3 | 50.0% | 100.0% | 100.0% | LOW_CARDINALITY | AUTO_APROBABLE | AUMENTADO, DISMINUIDO, NORMAL |
| Ovarios | forma | texto | 1 | 1 | 100.0% | 100.0% | 0.0% | LOW_CARDINALITY | AUTO_APROBABLE | — |

## 8. Top 50 valores por par (sólo pares con cardinalidad ≥5)


### Gestación / fetos — 9 valores, 107 filas

| Rank | Valor canónico | Familia | Frecuencia | % |
|----:|----------------|---------|-----------:|--:|
| 1 | `CINCO` | — | 20 | 18.69% |
| 2 | `SEIS` | — | 17 | 15.89% |
| 3 | `CUATRO` | — | 15 | 14.02% |
| 4 | `TRES` | — | 14 | 13.08% |
| 5 | `UNO` | — | 12 | 11.21% |
| 6 | `DOS` | — | 9 | 8.41% |
| 7 | `OCHO` | — | 9 | 8.41% |
| 8 | `SIETE` | — | 9 | 8.41% |
| 9 | `NUEVE_O_MAS` | — | 2 | 1.87% |

### Riñones / ecogenicidad — 8 valores, 3,017 filas

| Rank | Valor canónico | Familia | Frecuencia | % |
|----:|----------------|---------|-----------:|--:|
| 1 | `HIPERECOICA` | — | 1,683 | 55.78% |
| 2 | `CONSERVADA` | NORMAL | 514 | 17.04% |
| 3 | `HIPOECOICA` | — | 385 | 12.76% |
| 4 | `AUMENTADA` | AUMENTADO | 325 | 10.77% |
| 5 | `DISMINUIDA` | DISMINUIDO | 88 | 2.92% |
| 6 | `ADECUADA` | NORMAL | 14 | 0.46% |
| 7 | `AUMENTADA_DE` | — | 4 | 0.13% |
| 8 | `NORMAL` | NORMAL | 4 | 0.13% |

### Riñones / tamano — 8 valores, 4,959 filas

| Rank | Valor canónico | Familia | Frecuencia | % |
|----:|----------------|---------|-----------:|--:|
| 1 | `DENTRO_DE_RANGO` | NORMAL | 4,186 | 84.41% |
| 2 | `AUMENTADO` | AUMENTADO | 333 | 6.72% |
| 3 | `LEVEMENTE_AUMENTADO` | AUMENTADO | 178 | 3.59% |
| 4 | `DISMINUIDO` | DISMINUIDO | 118 | 2.38% |
| 5 | `NORMAL` | NORMAL | 54 | 1.09% |
| 6 | `SEVERAMENTE_AUMENTADO` | AUMENTADO | 42 | 0.85% |
| 7 | `MODERADAMENTE_AUMENTADO` | AUMENTADO | 32 | 0.65% |
| 8 | `CONSERVADO` | NORMAL | 16 | 0.32% |

### Hígado / tamano — 7 valores, 1,454 filas

| Rank | Valor canónico | Familia | Frecuencia | % |
|----:|----------------|---------|-----------:|--:|
| 1 | `NORMAL` | NORMAL | 1,436 | 98.76% |
| 2 | `AUMENTADO` | AUMENTADO | 5 | 0.34% |
| 3 | `LEVEMENTE_AUMENTADO` | AUMENTADO | 4 | 0.28% |
| 4 | `MODERADAMENTE_AUMENTADO` | AUMENTADO | 4 | 0.28% |
| 5 | `CONSERVADO` | NORMAL | 2 | 0.14% |
| 6 | `DISMINUIDO` | DISMINUIDO | 2 | 0.14% |
| 7 | `SEVERAMENTE_AUMENTADO` | AUMENTADO | 1 | 0.07% |

### Riñones / forma — 6 valores, 5,215 filas

| Rank | Valor canónico | Familia | Frecuencia | % |
|----:|----------------|---------|-----------:|--:|
| 1 | `OVALADO` | — | 5,066 | 97.14% |
| 2 | `RENAL` | — | 127 | 2.44% |
| 3 | `NORMAL` | NORMAL | 10 | 0.19% |
| 4 | `REDONDEADO` | — | 6 | 0.12% |
| 5 | `GLOBOSO` | — | 4 | 0.08% |
| 6 | `IRREGULAR` | IRREGULAR | 2 | 0.04% |

### Vejiga / contenido — 6 valores, 2,644 filas

| Rank | Valor canónico | Familia | Frecuencia | % |
|----:|----------------|---------|-----------:|--:|
| 1 | `ANECOICO` | — | 2,194 | 82.98% |
| 2 | `HIPERECOICO` | — | 430 | 16.26% |
| 3 | `GRANULAR` | — | 10 | 0.38% |
| 4 | `HOMOGENEO` | HOMOGENEO | 4 | 0.15% |
| 5 | `HETEROGENEO` | HETEROGENEO | 3 | 0.11% |
| 6 | `SEDIMENTO` | — | 3 | 0.11% |

### Vejiga / replecion — 6 valores, 2,641 filas

| Rank | Valor canónico | Familia | Frecuencia | % |
|----:|----------------|---------|-----------:|--:|
| 1 | `SEMI_PLETORICA` | — | 2,182 | 82.62% |
| 2 | `PLETORICA` | — | 234 | 8.86% |
| 3 | `SEMI_DEPLETADA` | — | 155 | 5.87% |
| 4 | `DEPLETADA` | — | 54 | 2.04% |
| 5 | `VACIA` | — | 12 | 0.45% |
| 6 | `DISTENDIDA` | — | 4 | 0.15% |

### Bazo / tamano — 5 valores, 2,601 filas

| Rank | Valor canónico | Familia | Frecuencia | % |
|----:|----------------|---------|-----------:|--:|
| 1 | `NORMAL` | NORMAL | 2,358 | 90.66% |
| 2 | `AUMENTADO` | AUMENTADO | 234 | 9.00% |
| 3 | `CONSERVADO` | NORMAL | 6 | 0.23% |
| 4 | `DISMINUIDO` | DISMINUIDO | 2 | 0.08% |
| 5 | `DENTRO_DE_RANGO` | NORMAL | 1 | 0.04% |

### Estómago / contenido — 5 valores, 2,653 filas

| Rank | Valor canónico | Familia | Frecuencia | % |
|----:|----------------|---------|-----------:|--:|
| 1 | `ALIMENTICIO` | — | 2,157 | 81.30% |
| 2 | `MUCOSO` | — | 356 | 13.42% |
| 3 | `GAS` | — | 80 | 3.02% |
| 4 | `LIQUIDO` | — | 55 | 2.07% |
| 5 | `SIN_CONTENIDO` | — | 5 | 0.19% |

### Hígado / ecogenicidad — 5 valores, 2,524 filas

| Rank | Valor canónico | Familia | Frecuencia | % |
|----:|----------------|---------|-----------:|--:|
| 1 | `HIPOECOICA` | — | 1,976 | 78.29% |
| 2 | `HIPERECOICA` | — | 497 | 19.69% |
| 3 | `AUMENTADA` | AUMENTADO | 32 | 1.27% |
| 4 | `CONSERVADA` | NORMAL | 10 | 0.40% |
| 5 | `DISMINUIDA` | DISMINUIDO | 9 | 0.36% |

### Intestino / grosor_pared — 5 valores, 2,560 filas

| Rank | Valor canónico | Familia | Frecuencia | % |
|----:|----------------|---------|-----------:|--:|
| 1 | `CONSERVADO` | NORMAL | 2,528 | 98.75% |
| 2 | `LEVEMENTE_AUMENTADO` | AUMENTADO | 15 | 0.59% |
| 3 | `MODERADAMENTE_AUMENTADO` | AUMENTADO | 8 | 0.31% |
| 4 | `DISCRETAMENTE_AUMENTADO` | AUMENTADO | 7 | 0.27% |
| 5 | `AUMENTADO` | AUMENTADO | 2 | 0.08% |