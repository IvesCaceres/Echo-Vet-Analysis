# F4 — Revisión clínica del diccionario de valores canónicos

**Fecha:** 2026-06-23  
**Fuente:** `silver_atributos_hallazgo.valor_canonico` (post-F3, 107,409 filas)  
**Agrupación:** por `dim_atributo.nombre_canonico` (NO por par órgano+atributo).  
**Objetivo:** validación manual antes de poblar `dim_valor_atributo` y `map_atributo_valor`.

**Instrucciones de revisión:**
- ¿Todos los valores canónicos tienen sentido clínico para el atributo?
- ¿Hay sinónimos que deberían mapearse al mismo canónico? (ej. AUMENTADO ↔ AUMENTADA)
- ¿Algún valor es ruido o artefacto de regex que debe limpiarse?
- ¿La cobertura top-5 ≥95% indica que el resto es marginal o hay un valor importante en cola larga?

---

## Resumen

- **Atributos únicos:** 25
- **Total valores distintos (suma):** 110

| # | Atributo | Observaciones | Hallazgos únicos | Valores | Órganos |
|--:|----------|--------------:|-----------------:|--------:|---------|
| 1 | `arquitectura` | 8,846 | 6,490 | 2 | 3 (Bazo,Hígado,Adrenales) |
| 2 | `aspecto_peripancreatico` | 5 | 5 | 1 | 1 (Páncreas) |
| 3 | `bordes` | 5,013 | 2,515 | 4 | 2 (Riñones,Hígado) |
| 4 | `bordes_internos` | 5,045 | 5,045 | 3 | 2 (Vejiga,Vesícula) |
| 5 | `compromiso` | 2,330 | 2,330 | 4 | 1 (Linfonodos) |
| 6 | `compromiso_pelvico` | 5,010 | 2,509 | 2 | 1 (Riñones) |
| 7 | `contenido` | 10,614 | 10,614 | 12 | 5 (Vejiga,Estómago,Vesícula,Intestino,Útero) |
| 8 | `diferenciacion_corticomedular` | 5,127 | 2,567 | 2 | 1 (Riñones) |
| 9 | `distension` | 5,242 | 5,242 | 7 | 2 (Estómago,Vesícula) |
| 10 | `ecogenicidad` | 6,262 | 4,757 | 8 | 4 (Hígado,Riñones,Próstata,Testículos) |
| 11 | `estratificacion_pared` | 2,566 | 2,566 | 1 | 2 (Estómago,Intestino) |
| 12 | `fetos` | 107 | 107 | 9 | 1 (Gestación) |
| 13 | `forma` | 10,786 | 5,806 | 10 | 6 (Riñones,Bazo,Adrenales,Próstata,Ovarios,Testículos) |
| 14 | `granulado` | 2,534 | 2,534 | 2 | 1 (Hígado) |
| 15 | `grosor_pared` | 7,778 | 7,778 | 8 | 5 (Vejiga,Estómago,Intestino,Vesícula,Útero) |
| 16 | `homogeneidad` | 725 | 725 | 3 | 2 (Próstata,Testículos) |
| 17 | `homogeneidad_contenido` | 2,126 | 2,126 | 2 | 1 (Vejiga) |
| 18 | `lobulacion` | 719 | 719 | 1 | 1 (Próstata) |
| 19 | `margenes` | 2,669 | 2,669 | 6 | 2 (Hígado,Bazo) |
| 20 | `patron_vascular` | 2,508 | 2,508 | 2 | 1 (Hígado) |
| 21 | `presencia` | 2,315 | 2,315 | 2 | 1 (Linfonodos) |
| 22 | `preservacion` | 2,611 | 2,611 | 2 | 1 (Páncreas) |
| 23 | `relacion_corticomedular` | 4,159 | 2,082 | 3 | 1 (Riñones) |
| 24 | `replecion` | 2,641 | 2,641 | 6 | 1 (Vejiga) |
| 25 | `tamano` | 9,671 | 7,196 | 8 | 6 (Riñones,Bazo,Hígado,Próstata,Testículos,Útero) |

---

## Detalle por atributo

### `arquitectura`

- **Observaciones:** 8,846  
- **Hallazgos únicos:** 6,490  
- **Valores distintos:** 2  
- **Órganos donde aplica (3):** Bazo,Hígado,Adrenales  
- **Top-5 cobertura:** 100.0% (8,846/8,846, 2/2 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `NORMAL` | 4,654 | 52.61% | 52.61% |
| 2 | `CONSERVADA` | 4,192 | 47.39% | 100.00% |

### `aspecto_peripancreatico`

- **Observaciones:** 5  
- **Hallazgos únicos:** 5  
- **Valores distintos:** 1  
- **Órganos donde aplica (1):** Páncreas  
- **Top-5 cobertura:** 100.0% (5/5, 1/1 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `NORMAL` | 5 | 100.00% | 100.00% |

### `bordes`

- **Observaciones:** 5,013  
- **Hallazgos únicos:** 2,515  
- **Valores distintos:** 4  
- **Órganos donde aplica (2):** Riñones,Hígado  
- **Top-5 cobertura:** 100.0% (5,013/5,013, 4/4 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `REGULARES` | 3,265 | 65.13% | 65.13% |
| 2 | `IRREGULARES` | 939 | 18.73% | 83.86% |
| 3 | `LEVEMENTE_IRREGULARES` | 767 | 15.30% | 99.16% |
| 4 | `LISOS` | 42 | 0.84% | 100.00% |

### `bordes_internos`

- **Observaciones:** 5,045  
- **Hallazgos únicos:** 5,045  
- **Valores distintos:** 3  
- **Órganos donde aplica (2):** Vejiga,Vesícula  
- **Top-5 cobertura:** 100.0% (5,045/5,045, 3/3 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `REGULARES` | 4,911 | 97.34% | 97.34% |
| 2 | `IRREGULARES` | 133 | 2.64% | 99.98% |
| 3 | `LISOS` | 1 | 0.02% | 100.00% |

### `compromiso`

- **Observaciones:** 2,330  
- **Hallazgos únicos:** 2,330  
- **Valores distintos:** 4  
- **Órganos donde aplica (1):** Linfonodos  
- **Top-5 cobertura:** 100.0% (2,330/2,330, 4/4 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `NO_COMPROMETIDO` | 2,264 | 97.17% | 97.17% |
| 2 | `COMPROMETIDO` | 42 | 1.80% | 98.97% |
| 3 | `CONSERVADO` | 22 | 0.94% | 99.91% |
| 4 | `REACTIVO` | 2 | 0.09% | 100.00% |

### `compromiso_pelvico`

- **Observaciones:** 5,010  
- **Hallazgos únicos:** 2,509  
- **Valores distintos:** 2  
- **Órganos donde aplica (1):** Riñones  
- **Top-5 cobertura:** 100.0% (5,010/5,010, 2/2 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `SIN_COMPROMISO` | 4,930 | 98.40% | 98.40% |
| 2 | `DILATACION_PELVICA` | 80 | 1.60% | 100.00% |

### `contenido`

- **Observaciones:** 10,614  
- **Hallazgos únicos:** 10,614  
- **Valores distintos:** 12  
- **Órganos donde aplica (5):** Vejiga,Estómago,Vesícula,Intestino,Útero  
- **Top-5 cobertura:** 98.8% (10,491/10,614, 5/12 valores = 42% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `ANECOICO` | 4,370 | 41.17% | 41.17% |
| 2 | `ALIMENTICIO` | 4,300 | 40.51% | 81.68% |
| 3 | `HIPERECOICO` | 907 | 8.55% | 90.23% |
| 4 | `MUCOSO` | 834 | 7.86% | 98.09% |
| 5 | `GAS` | 80 | 0.75% | 98.84% |
| 6 | `LIQUIDO` | 59 | 0.56% | 99.40% |
| 7 | `FECAL` | 38 | 0.36% | 99.76% |
| 8 | `GRANULAR` | 10 | 0.09% | 99.85% |
| 9 | `SIN_CONTENIDO` | 5 | 0.05% | 99.90% |
| 10 | `HOMOGENEO` | 5 | 0.05% | 99.94% |
| 11 | `SEDIMENTO` | 3 | 0.03% | 99.97% |
| 12 | `HETEROGENEO` | 3 | 0.03% | 100.00% |

### `diferenciacion_corticomedular`

- **Observaciones:** 5,127  
- **Hallazgos únicos:** 2,567  
- **Valores distintos:** 2  
- **Órganos donde aplica (1):** Riñones  
- **Top-5 cobertura:** 100.0% (5,127/5,127, 2/2 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `BIEN_DEFINIDA` | 4,411 | 86.03% | 86.03% |
| 2 | `MAL_DEFINIDA` | 716 | 13.97% | 100.00% |

### `distension`

- **Observaciones:** 5,242  
- **Hallazgos únicos:** 5,242  
- **Valores distintos:** 7  
- **Órganos donde aplica (2):** Estómago,Vesícula  
- **Top-5 cobertura:** 99.0% (5,192/5,242, 5/7 valores = 71% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `SEMI_DISTENDIDA` | 2,468 | 47.08% | 47.08% |
| 2 | `SEMI_DISTENDIDO` | 2,112 | 40.29% | 87.37% |
| 3 | `VACIO` | 324 | 6.18% | 93.55% |
| 4 | `DISTENDIDO` | 176 | 3.36% | 96.91% |
| 5 | `DISTENDIDA` | 112 | 2.14% | 99.05% |
| 6 | `PLETORICA` | 42 | 0.80% | 99.85% |
| 7 | `DEPLETADA` | 8 | 0.15% | 100.00% |

### `ecogenicidad`

- **Observaciones:** 6,262  
- **Hallazgos únicos:** 4,757  
- **Valores distintos:** 8  
- **Órganos donde aplica (4):** Hígado,Riñones,Próstata,Testículos  
- **Top-5 cobertura:** 99.6% (6,240/6,262, 5/8 valores = 62% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `HIPOECOICA` | 2,823 | 45.08% | 45.08% |
| 2 | `HIPERECOICA` | 2,438 | 38.93% | 84.01% |
| 3 | `CONSERVADA` | 525 | 8.38% | 92.40% |
| 4 | `AUMENTADA` | 357 | 5.70% | 98.10% |
| 5 | `DISMINUIDA` | 97 | 1.55% | 99.65% |
| 6 | `ADECUADA` | 14 | 0.22% | 99.87% |
| 7 | `NORMAL` | 4 | 0.06% | 99.94% |
| 8 | `AUMENTADA_DE` | 4 | 0.06% | 100.00% |

### `estratificacion_pared`

- **Observaciones:** 2,566  
- **Hallazgos únicos:** 2,566  
- **Valores distintos:** 1  
- **Órganos donde aplica (2):** Estómago,Intestino  
- **Top-5 cobertura:** 100.0% (2,566/2,566, 1/1 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `PRESENTE` | 2,566 | 100.00% | 100.00% |

### `fetos`

- **Observaciones:** 107  
- **Hallazgos únicos:** 107  
- **Valores distintos:** 9  
- **Órganos donde aplica (1):** Gestación  
- **Top-5 cobertura:** 72.9% (78/107, 5/9 valores = 56% de los distintos)  
- ❌ **Cola larga relevante:** top-5 cubre solo 72.9%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `CINCO` | 20 | 18.69% | 18.69% |
| 2 | `SEIS` | 17 | 15.89% | 34.58% |
| 3 | `CUATRO` | 15 | 14.02% | 48.60% |
| 4 | `TRES` | 14 | 13.08% | 61.68% |
| 5 | `UNO` | 12 | 11.21% | 72.90% |
| 6 | `SIETE` | 9 | 8.41% | 81.31% |
| 7 | `OCHO` | 9 | 8.41% | 89.72% |
| 8 | `DOS` | 9 | 8.41% | 98.13% |
| 9 | `NUEVE_O_MAS` | 2 | 1.87% | 100.00% |

### `forma`

- **Observaciones:** 10,786  
- **Hallazgos únicos:** 5,806  
- **Valores distintos:** 10  
- **Órganos donde aplica (6):** Riñones,Bazo,Adrenales,Próstata,Ovarios,Testículos  
- **Top-5 cobertura:** 99.8% (10,768/10,786, 5/10 valores = 50% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `OVALADO` | 5,072 | 47.02% | 47.02% |
| 2 | `NORMAL` | 4,871 | 45.16% | 92.18% |
| 3 | `OVALADA` | 673 | 6.24% | 98.42% |
| 4 | `RENAL` | 127 | 1.18% | 99.60% |
| 5 | `GLOBOSA` | 25 | 0.23% | 99.83% |
| 6 | `REDONDEADO` | 6 | 0.06% | 99.89% |
| 7 | `CONSERVADA` | 5 | 0.05% | 99.94% |
| 8 | `GLOBOSO` | 4 | 0.04% | 99.97% |
| 9 | `IRREGULAR` | 2 | 0.02% | 99.99% |
| 10 | `REDONDEADA` | 1 | 0.01% | 100.00% |

### `granulado`

- **Observaciones:** 2,534  
- **Hallazgos únicos:** 2,534  
- **Valores distintos:** 2  
- **Órganos donde aplica (1):** Hígado  
- **Top-5 cobertura:** 100.0% (2,534/2,534, 2/2 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `GRUESO` | 1,922 | 75.85% | 75.85% |
| 2 | `FINO` | 612 | 24.15% | 100.00% |

### `grosor_pared`

- **Observaciones:** 7,778  
- **Hallazgos únicos:** 7,778  
- **Valores distintos:** 8  
- **Órganos donde aplica (5):** Vejiga,Estómago,Intestino,Vesícula,Útero  
- **Top-5 cobertura:** 99.7% (7,757/7,778, 5/8 valores = 62% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `CONSERVADO` | 6,686 | 85.96% | 85.96% |
| 2 | `AUMENTADO` | 1,018 | 13.09% | 99.05% |
| 3 | `ENGROSADO` | 28 | 0.36% | 99.41% |
| 4 | `LEVEMENTE_AUMENTADO` | 15 | 0.19% | 99.60% |
| 5 | `NORMAL` | 10 | 0.13% | 99.73% |
| 6 | `MODERADAMENTE_AUMENTADO` | 8 | 0.10% | 99.83% |
| 7 | `DISCRETAMENTE_AUMENTADO` | 7 | 0.09% | 99.92% |
| 8 | `DELGADO` | 6 | 0.08% | 100.00% |

### `homogeneidad`

- **Observaciones:** 725  
- **Hallazgos únicos:** 725  
- **Valores distintos:** 3  
- **Órganos donde aplica (2):** Próstata,Testículos  
- **Top-5 cobertura:** 100.0% (725/725, 3/3 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `HOMOGENEA` | 555 | 76.55% | 76.55% |
| 2 | `HETEROGENEA` | 163 | 22.48% | 99.03% |
| 3 | `HETEROGENEO` | 7 | 0.97% | 100.00% |

### `homogeneidad_contenido`

- **Observaciones:** 2,126  
- **Hallazgos únicos:** 2,126  
- **Valores distintos:** 2  
- **Órganos donde aplica (1):** Vejiga  
- **Top-5 cobertura:** 100.0% (2,126/2,126, 2/2 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `HOMOGENEO` | 2,106 | 99.06% | 99.06% |
| 2 | `HETEROGENEO` | 20 | 0.94% | 100.00% |

### `lobulacion`

- **Observaciones:** 719  
- **Hallazgos únicos:** 719  
- **Valores distintos:** 1  
- **Órganos donde aplica (1):** Próstata  
- **Top-5 cobertura:** 100.0% (719/719, 1/1 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `BILOBULADA` | 719 | 100.00% | 100.00% |

### `margenes`

- **Observaciones:** 2,669  
- **Hallazgos únicos:** 2,669  
- **Valores distintos:** 6  
- **Órganos donde aplica (2):** Hígado,Bazo  
- **Top-5 cobertura:** 99.9% (2,667/2,669, 5/6 valores = 83% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `LISOS` | 2,615 | 97.98% | 97.98% |
| 2 | `IRREGULARES` | 25 | 0.94% | 98.91% |
| 3 | `REDONDEADOS` | 16 | 0.60% | 99.51% |
| 4 | `REGULARES` | 9 | 0.34% | 99.85% |
| 5 | `MAL_DEFINIDOS` | 2 | 0.07% | 99.93% |
| 6 | `CONSERVADOS` | 2 | 0.07% | 100.00% |

### `patron_vascular`

- **Observaciones:** 2,508  
- **Hallazgos únicos:** 2,508  
- **Valores distintos:** 2  
- **Órganos donde aplica (1):** Hígado  
- **Top-5 cobertura:** 100.0% (2,508/2,508, 2/2 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `CONSERVADO` | 2,474 | 98.64% | 98.64% |
| 2 | `NORMAL` | 34 | 1.36% | 100.00% |

### `presencia`

- **Observaciones:** 2,315  
- **Hallazgos únicos:** 2,315  
- **Valores distintos:** 2  
- **Órganos donde aplica (1):** Linfonodos  
- **Top-5 cobertura:** 100.0% (2,315/2,315, 2/2 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `NO_SE_OBSERVAN` | 2,308 | 99.70% | 99.70% |
| 2 | `PRESENTE` | 7 | 0.30% | 100.00% |

### `preservacion`

- **Observaciones:** 2,611  
- **Hallazgos únicos:** 2,611  
- **Valores distintos:** 2  
- **Órganos donde aplica (1):** Páncreas  
- **Top-5 cobertura:** 100.0% (2,611/2,611, 2/2 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `CONSERVADO` | 2,559 | 98.01% | 98.01% |
| 2 | `NO_EVALUADO` | 52 | 1.99% | 100.00% |

### `relacion_corticomedular`

- **Observaciones:** 4,159  
- **Hallazgos únicos:** 2,082  
- **Valores distintos:** 3  
- **Órganos donde aplica (1):** Riñones  
- **Top-5 cobertura:** 100.0% (4,159/4,159, 3/3 valores = 100% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `ADECUADA` | 3,220 | 77.42% | 77.42% |
| 2 | `AUMENTADA` | 579 | 13.92% | 91.34% |
| 3 | `DISMINUIDA` | 360 | 8.66% | 100.00% |

### `replecion`

- **Observaciones:** 2,641  
- **Hallazgos únicos:** 2,641  
- **Valores distintos:** 6  
- **Órganos donde aplica (1):** Vejiga  
- **Top-5 cobertura:** 99.8% (2,637/2,641, 5/6 valores = 83% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `SEMI_PLETORICA` | 2,182 | 82.62% | 82.62% |
| 2 | `PLETORICA` | 234 | 8.86% | 91.48% |
| 3 | `SEMI_DEPLETADA` | 155 | 5.87% | 97.35% |
| 4 | `DEPLETADA` | 54 | 2.04% | 99.39% |
| 5 | `VACIA` | 12 | 0.45% | 99.85% |
| 6 | `DISTENDIDA` | 4 | 0.15% | 100.00% |

### `tamano`

- **Observaciones:** 9,671  
- **Hallazgos únicos:** 7,196  
- **Valores distintos:** 8  
- **Órganos donde aplica (6):** Riñones,Bazo,Hígado,Próstata,Testículos,Útero  
- **Top-5 cobertura:** 98.9% (9,568/9,671, 5/8 valores = 62% de los distintos)  
- ✅ **Distribución saludable:** top-5 cubre ≥95%

| # | Valor canónico | Frecuencia | % | Acumulado % |
|--:|----------------|-----------:|--:|------------:|
| 1 | `NORMAL` | 4,366 | 45.15% | 45.15% |
| 2 | `DENTRO_DE_RANGO` | 4,187 | 43.29% | 88.44% |
| 3 | `AUMENTADO` | 670 | 6.93% | 95.37% |
| 4 | `LEVEMENTE_AUMENTADO` | 182 | 1.88% | 97.25% |
| 5 | `DISMINUIDO` | 163 | 1.69% | 98.93% |
| 6 | `SEVERAMENTE_AUMENTADO` | 43 | 0.44% | 99.38% |
| 7 | `MODERADAMENTE_AUMENTADO` | 36 | 0.37% | 99.75% |
| 8 | `CONSERVADO` | 24 | 0.25% | 100.00% |
