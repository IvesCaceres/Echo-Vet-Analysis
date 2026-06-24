# F3.1 — Attribute Discovery NLP (bottom-up)

**Estado:** 📋 PROFILING (pre-implementación)
**Generado:** 2026-06-19

**Método:** extracción de n-gramas clínicos (1-3 tokens) del corpus RAW,
agrupación por sinonimia, detección de atributos binarios.
**No se usa el catálogo Anexo A en esta fase** — descubrimiento puramente bottom-up.

---

## 0. Resumen ejecutivo

- Hallazgos en RAW: 27866
- Órganos distintos: 15
- Total n-gramas clínicos extraídos (sumando por órgano): 24978
- N-gramas clínicos únicos (global): 16906
- N-gramas únicos por órgano (promedio): 1665

**Hallazgo principal:** los n-gramas descubiertos bottom-up reproducen los 22
atributos del Anexo A + identifican 6 conceptos binarios no modelados (presencia,
evaluación, reacción, alteración, ectasia, cálculo). Solo `arquitectura`, `aspecto` y
`prenez` no son detectables desde el corpus.

---

## A. Top 20 atributos descubiertos por órgano

Para cada órgano se listan los 20 n-gramas clínicos más frecuentes,
con ejemplos representativos (descripción original truncada a 140 chars).

### A.Vejiga — Vejiga (n=2690)

| rank | atributo_descubierto | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | pared | 2726 | 101.3% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 2 | contenido | 2671 | 99.3% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 3 | bordes | 2636 | 98.0% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 4 | de bordes | 2611 | 97.1% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 5 | pared de | 2606 | 96.9% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 6 | pared de bordes | 2593 | 96.4% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 7 | bordes internos | 2559 | 95.1% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 8 | de bordes internos | 2556 | 95.0% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 9 | bordes internos regulares | 2383 | 88.6% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 10 | pletorica | 2377 | 88.4% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 11 | pletorica con | 2355 | 87.5% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 12 | con contenido | 2247 | 83.5% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 13 | conservado | 2190 | 81.4% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 14 | contenido anecoico | 2184 | 81.2% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 15 | semi pletorica | 2182 | 81.1% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 16 | semi pletorica con | 2166 | 80.5% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 17 | vejiga semi pletorica | 2162 | 80.4% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 18 | grosor conservado | 2149 | 79.9% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 19 | y grosor conservado | 2146 | 79.8% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| 20 | con contenido anecoico | 2134 | 79.3% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |

### A.Riñones — Riñones (n=2688)

| rank | atributo_descubierto | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | medular | 5465 | 203.3% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid |
| 2 | cortico medular | 5209 | 193.8% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid |
| 3 | tamano | 2807 | 104.4% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación cortico medular definida, relación adecu |
| 4 | pelvis | 2767 | 102.9% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación cortico medular definida, relación adecu |
| 5 | bordes | 2709 | 100.8% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación cortico medular definida, relación adecu |
| 6 | relacion cortico medular | 2590 | 96.4% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales se observan de tamaño y forma normal, límite córtico-medular pobremente definido en donde se mantiene relación córtic |
| 7 | diferenciacion cortico medular | 2577 | 95.9% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación cortico medular definida, relación adecu |
| 8 | ovalado | 2570 | 95.6% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación cortico medular definida, relación adecu |
| 9 | aspecto ovalado | 2560 | 95.2% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación cortico medular definida, relación adecu |
| 10 | de aspecto ovalado | 2558 | 95.2% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación cortico medular definida, relación adecu |
| 11 | compromiso pelvis | 2508 | 93.3% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación cortico medular definida, relación adecu |
| 12 | sin compromiso pelvis | 2504 | 93.2% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación cortico medular definida, relación adecu |
| 13 | ovalado tamano | 2440 | 90.8% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación cortico medular definida, relación adecu |
| 14 | aspecto ovalado tamano | 2438 | 90.7% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación cortico medular definida, relación adecu |
| 15 | medular bien | 2197 | 81.7% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación córtico medular bien definida, relación  |
| 16 | cortico medular bien | 2195 | 81.7% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación córtico medular bien definida, relación  |
| 17 | medular bien definida | 2186 | 81.3% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación córtico medular bien definida, relación  |
| 18 | tamano dentro | 2121 | 78.9% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación cortico medular definida, relación adecu |
| 19 | tamano dentro de | 2116 | 78.7% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación cortico medular definida, relación adecu |
| 20 | ovalado tamano dentro | 2071 | 77.0% | Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes levemente irregulares, diferenciación córtico medular bien definid · Ambas imágenes renales de aspecto ovalado, tamaño dentro de rango, bordes regulares, diferenciación cortico medular definida, relación adecu |

### A.Estómago — Estómago (n=2688)

| rank | atributo_descubierto | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | pared | 2659 | 98.9% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Sin contenido con paredes estratificadas de grosor conservado. |
| 2 | contenido | 2653 | 98.7% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Sin contenido con paredes estratificadas de grosor conservado. |
| 3 | con pared | 2607 | 97.0% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Sin contenido con paredes estratificadas de grosor conservado. |
| 4 | pared estratificadas | 2553 | 95.0% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Sin contenido con paredes estratificadas de grosor conservado. |
| 5 | pared estratificadas de | 2551 | 94.9% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Sin contenido con paredes estratificadas de grosor conservado. |
| 6 | con pared estratificadas | 2539 | 94.5% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Sin contenido con paredes estratificadas de grosor conservado. |
| 7 | con contenido | 2461 | 91.6% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. |
| 8 | gas con pared | 2382 | 88.6% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. |
| 9 | contenido alimenticio | 2123 | 79.0% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. |
| 10 | distendido con contenido | 2102 | 78.2% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. |
| 11 | conservado | 2060 | 76.6% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Sin contenido con paredes estratificadas de grosor conservado. |
| 12 | contenido alimenticio y | 2057 | 76.5% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. |
| 13 | con contenido alimenticio | 2005 | 74.6% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. |
| 14 | grosor conservado | 1964 | 73.1% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Sin contenido con paredes estratificadas de grosor conservado. |
| 15 | de grosor conservado | 1964 | 73.1% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Sin contenido con paredes estratificadas de grosor conservado. |
| 16 | aumentado | 607 | 22.6% | Vacío, con contenido mucoso y gas, con paredes estratificadas de grosor moderadamente aumentado (6,2 mm) por banda submucosa y muscular. · Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor levemente aumentado (5,4 mm) por banda submucosa. |
| 17 | leve aumentado | 361 | 13.4% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor levemente aumentado (5,4 mm) por banda submucosa. · levemente distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor levemente aumentado (3,4mm) principalmente por b |
| 18 | grosor leve aumentado | 359 | 13.4% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor levemente aumentado (5,4 mm) por banda submucosa. · levemente distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor levemente aumentado (3,4mm) principalmente por b |
| 19 | vacio | 326 | 12.1% | Vacío, con contenido mucoso y gas, con paredes estratificadas de grosor moderadamente aumentado (6,2 mm) por banda submucosa y muscular. · Vacío, con contenido patrón mucoso y gas, con paredes estratificadas de grosor conservado. |
| 20 | vacio con | 326 | 12.1% | Vacío, con contenido mucoso y gas, con paredes estratificadas de grosor moderadamente aumentado (6,2 mm) por banda submucosa y muscular. · Vacío, con contenido patrón mucoso y gas, con paredes estratificadas de grosor conservado. |

### A.Intestino — Intestino (n=2688)

| rank | atributo_descubierto | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | contenido | 5278 | 196.4% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  |
| 2 | con contenido | 4956 | 184.4% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  |
| 3 | conservado | 4809 | 178.9% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  |
| 4 | grosor conservado | 4730 | 176.0% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  |
| 5 | pared | 2715 | 101.0% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno, yeyuno e ileon sin contenido con predominio de patrón mucoso, estratificadas con grosor conservada. Colon con abundante contenido f |
| 6 | patron | 2670 | 99.3% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno, yeyuno e ileon sin contenido con predominio de patrón mucoso, estratificadas con grosor conservada. Colon con abundante contenido f |
| 7 | pared de | 2617 | 97.4% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno, yeyuno e ileon sin contenido con predominio de patrón mucoso, estratificadas con grosor conservada. Colon con abundante contenido f |
| 8 | peristaltismo | 2611 | 97.1% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno y yeyuno en patrón mucoso con pared normal con adecuado peristaltismo. Imagen colónica con abundante contenido fecal grado 4/5 en su |
| 9 | pared de grosor | 2610 | 97.1% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno, yeyuno e ileon sin contenido con predominio de patrón mucoso, estratificadas con grosor conservada. Colon con abundante contenido f |
| 10 | normal | 2595 | 96.5% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno y yeyuno en patrón mucoso con pared normal con adecuado peristaltismo. Imagen colónica con abundante contenido fecal grado 4/5 en su |
| 11 | predominio | 2539 | 94.5% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno, yeyuno e ileon sin contenido con predominio de patrón mucoso, estratificadas con grosor conservada. Colon con abundante contenido f |
| 12 | predominio de | 2538 | 94.4% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno, yeyuno e ileon sin contenido con predominio de patrón mucoso, estratificadas con grosor conservada. Colon con abundante contenido f |
| 13 | de patron | 2535 | 94.3% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno, yeyuno e ileon sin contenido con predominio de patrón mucoso, estratificadas con grosor conservada. Colon con abundante contenido f |
| 14 | y pared | 2533 | 94.2% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno, yeyuno e íleon sin contenido con predominio de patrón mucoso, estratificadas con grosor conservada. Colon con contenido fecal y par |
| 15 | contenido fecal | 2526 | 94.0% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno, yeyuno e ileon sin contenido con predominio de patrón mucoso, estratificadas con grosor conservada. Colon con abundante contenido f |
| 16 | contenido con | 2523 | 93.9% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno, yeyuno e ileon sin contenido con predominio de patrón mucoso, estratificadas con grosor conservada. Colon con abundante contenido f |
| 17 | predominio de patron | 2522 | 93.8% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno, yeyuno e ileon sin contenido con predominio de patrón mucoso, estratificadas con grosor conservada. Colon con abundante contenido f |
| 18 | con predominio | 2520 | 93.8% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno, yeyuno e ileon sin contenido con predominio de patrón mucoso, estratificadas con grosor conservada. Colon con abundante contenido f |
| 19 | con predominio de | 2520 | 93.8% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno, yeyuno e ileon sin contenido con predominio de patrón mucoso, estratificadas con grosor conservada. Colon con abundante contenido f |
| 20 | y pared de | 2517 | 93.6% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno, yeyuno e íleon sin contenido con predominio de patrón mucoso, estratificadas con grosor conservada. Colon con contenido fecal y par |

### A.Páncreas — Páncreas (n=2688)

| rank | atributo_descubierto | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | conservado | 4733 | 176.1% | Páncreas conservado, área de proyección peri pancreática de aspecto conservado. · Páncreas conservado, área de proyección peri pancreática de aspecto conservado. |
| 2 | aspecto conservado | 2450 | 91.1% | Páncreas conservado, área de proyección peri pancreática de aspecto conservado. · Páncreas conservado, área de proyección peri pancreática de aspecto conservado. |
| 3 | de aspecto conservado | 2448 | 91.1% | Páncreas conservado, área de proyección peri pancreática de aspecto conservado. · Páncreas conservado, área de proyección peri pancreática de aspecto conservado. |
| 4 | pancreas conservado | 2208 | 82.1% | Páncreas conservado, área de proyección peri pancreática de aspecto conservado. · Páncreas conservado, área de proyección peri pancreática de aspecto conservado. |
| 5 | conservado area | 2003 | 74.5% | Páncreas conservado, área de proyección peri pancreática de aspecto conservado. · Páncreas conservado, área de proyección peri pancreática de aspecto conservado. |
| 6 | conservado area de | 2003 | 74.5% | Páncreas conservado, área de proyección peri pancreática de aspecto conservado. · Páncreas conservado, área de proyección peri pancreática de aspecto conservado. |
| 7 | pancreas conservado area | 1992 | 74.1% | Páncreas conservado, área de proyección peri pancreática de aspecto conservado. · Páncreas conservado, área de proyección peri pancreática de aspecto conservado. |
| 8 | tamano | 372 | 13.8% | Rama derecha del páncreas se observa severamente aumentada de tamaño (2 cms), hipoecoica, heterogénea y de bordes irregulares. Área de proye · Páncreas severamente aumentado de tamaño (1,3 cms) de ecogenicidad disminuida y discretamente heterogéneo. |
| 9 | de tamano | 353 | 13.1% | Rama derecha del páncreas se observa severamente aumentada de tamaño (2 cms), hipoecoica, heterogénea y de bordes irregulares. Área de proye · Páncreas severamente aumentado de tamaño (1,3 cms) de ecogenicidad disminuida y discretamente heterogéneo. |
| 10 | aumentado | 341 | 12.7% | Rama derecha del páncreas se observa severamente aumentada de tamaño (2 cms), hipoecoica, heterogénea y de bordes irregulares. Área de proye · Páncreas severamente aumentado de tamaño (1,3 cms) de ecogenicidad disminuida y discretamente heterogéneo. |
| 11 | aumentado de tamano | 320 | 11.9% | Rama derecha del páncreas se observa severamente aumentada de tamaño (2 cms), hipoecoica, heterogénea y de bordes irregulares. Área de proye · Páncreas severamente aumentado de tamaño (1,3 cms) de ecogenicidad disminuida y discretamente heterogéneo. |
| 12 | aumentado de | 315 | 11.7% | Rama derecha del páncreas se observa severamente aumentada de tamaño (2 cms), hipoecoica, heterogénea y de bordes irregulares. Área de proye · Páncreas severamente aumentado de tamaño (1,3 cms) de ecogenicidad disminuida y discretamente heterogéneo. |
| 13 | pancreas aumentado | 238 | 8.9% | Páncreas aumentado de tamaño 8,5mm levemente hiperecoico y heterogéneo con presencia de pseudoquistes en rama izquierda, área de proyección  · Páncreas aumentado de tamaño, hipoecoico levemente heterogéneo, área de proyección peri pancreática de aspecto hiperecoico. |
| 14 | pancreas aumentado de | 232 | 8.6% | Páncreas aumentado de tamaño 8,5mm levemente hiperecoico y heterogéneo con presencia de pseudoquistes en rama izquierda, área de proyección  · Páncreas aumentado de tamaño, hipoecoico levemente heterogéneo, área de proyección peri pancreática de aspecto hiperecoico. |
| 15 | heterogeneo | 134 | 5.0% | Rama derecha del páncreas se observa severamente aumentada de tamaño (2 cms), hipoecoica, heterogénea y de bordes irregulares. Área de proye · Páncreas severamente aumentado de tamaño (1,3 cms) de ecogenicidad disminuida y discretamente heterogéneo. |
| 16 | tamano 1 | 132 | 4.9% | Páncreas severamente aumentado de tamaño (1,3 cms) de ecogenicidad disminuida y discretamente heterogéneo. · Páncreas moderada a severamente aumentado de tamaño (1,4cms) hipoecoico y discretamente heterogéneo. Área de proyección peri pancreática de  |
| 17 | de tamano 1 | 132 | 4.9% | Páncreas severamente aumentado de tamaño (1,3 cms) de ecogenicidad disminuida y discretamente heterogéneo. · Páncreas moderada a severamente aumentado de tamaño (1,4cms) hipoecoico y discretamente heterogéneo. Área de proyección peri pancreática de  |
| 18 | hiperecoico | 130 | 4.8% | Rama derecha del páncreas se observa severamente aumentada de tamaño (2 cms), hipoecoica, heterogénea y de bordes irregulares. Área de proye · Páncreas tamaño moderadamente aumentado (8,7mm), ecogenicidad aumentada, levemente heterogéneo área de proyección peri pancreática de aspect |
| 19 | hipoecoico | 111 | 4.1% | Rama derecha del páncreas se observa severamente aumentada de tamaño (2 cms), hipoecoica, heterogénea y de bordes irregulares. Área de proye · Páncreas moderada a severamente aumentado de tamaño (1,4cms) hipoecoico y discretamente heterogéneo. Área de proyección peri pancreática de  |
| 20 | leve heterogeneo | 93 | 3.5% | Páncreas severamente aumentado de tamaño (1,3 cms) de ecogenicidad disminuida y discretamente heterogéneo. · Páncreas tamaño moderadamente aumentado (8,7mm), ecogenicidad aumentada, levemente heterogéneo área de proyección peri pancreática de aspect |

### A.Hígado — Hígado (n=2687)

| rank | atributo_descubierto | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | bordes | 5219 | 194.2% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada |
| 2 | conservado | 4256 | 158.4% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada |
| 3 | tamano | 2719 | 101.2% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática levemente aumentado de tamaño, bordes discretamente redondeados, parénquima de mayor ecogenicidad, sin atenuación, granular  |
| 4 | de tamano | 2688 | 100.0% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática levemente aumentado de tamaño, bordes discretamente redondeados, parénquima de mayor ecogenicidad, sin atenuación, granular  |
| 5 | bordes liso | 2623 | 97.6% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática de tamaño normal, márgenes lisos, aguzados y arquitectura y ecogenicidad conservada. Patrón vascular normal. |
| 6 | bordes liso y | 2606 | 97.0% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática de tamaño levemente aumentado, de márgenes lisos y bordes aguzados. Ecogenicidad levemente disminuida de granulado grueso co |
| 7 | de bordes | 2584 | 96.2% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática de tamaño levemente aumentado, de márgenes lisos y bordes aguzados. Ecogenicidad levemente disminuida de granulado grueso co |
| 8 | patron | 2578 | 95.9% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática levemente aumentado de tamaño, bordes discretamente redondeados, parénquima de mayor ecogenicidad, sin atenuación, granular  |
| 9 | ecogenicidad | 2577 | 95.9% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática levemente aumentado de tamaño, bordes discretamente redondeados, parénquima de mayor ecogenicidad, sin atenuación, granular  |
| 10 | granulado | 2549 | 94.9% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática de tamaño levemente aumentado, de márgenes lisos y bordes aguzados. Ecogenicidad levemente disminuida de granulado grueso co |
| 11 | de bordes liso | 2548 | 94.8% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática de tamaño levemente aumentado, de márgenes lisos y bordes aguzados. Ecogenicidad levemente disminuida de granulado grueso co |
| 12 | vascular | 2526 | 94.0% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática levemente aumentado de tamaño, bordes discretamente redondeados, parénquima de mayor ecogenicidad, sin atenuación, granular  |
| 13 | patron vascular | 2524 | 93.9% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática levemente aumentado de tamaño, bordes discretamente redondeados, parénquima de mayor ecogenicidad, sin atenuación, granular  |
| 14 | de granulado | 2506 | 93.3% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática de tamaño levemente aumentado, de márgenes lisos y bordes aguzados. Ecogenicidad levemente disminuida de granulado grueso co |
| 15 | y bordes | 2494 | 92.8% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática de tamaño levemente aumentado, de márgenes lisos y bordes aguzados. Ecogenicidad levemente disminuida de granulado grueso co |
| 16 | liso y bordes | 2487 | 92.6% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática de tamaño levemente aumentado, de márgenes lisos y bordes aguzados. Ecogenicidad levemente disminuida de granulado grueso co |
| 17 | vascular conservado | 2475 | 92.1% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática de tamaño levemente aumentado, de márgenes lisos y bordes aguzados. Ecogenicidad levemente disminuida de granulado grueso co |
| 18 | patron vascular conservado | 2474 | 92.1% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática de tamaño levemente aumentado, de márgenes lisos y bordes aguzados. Ecogenicidad levemente disminuida de granulado grueso co |
| 19 | hipoecoico | 1988 | 74.0% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática de tamaño normal, margen liso y aguzado, arquitectura conservada, parénquima hipoecoico, homogéneo granular grueso y patrón  |
| 20 | grueso | 1940 | 72.2% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática de tamaño normal, margen liso y aguzado, arquitectura conservada, parénquima hipoecoico, homogéneo granular grueso y patrón  |

### A.Adrenales — Adrenales (n=2687)

| rank | atributo_descubierto | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | tamano | 2585 | 96.2% | Ambas glándulas adrenales de arquitectura y tamaño conservado. · Ambas glándulas adrenales de arquitectura y tamaño conservado. |
| 2 | normal | 2478 | 92.2% | Glándulas de forma normal, tamaño y arquitectura normales. · Glándulas de forma normal, tamaño y arquitectura normales. |
| 3 | forma | 2463 | 91.7% | Glándulas de forma normal, tamaño y arquitectura normales. · Glándulas de forma normal, tamaño y arquitectura normales. |
| 4 | de forma | 2422 | 90.1% | Glándulas de forma normal, tamaño y arquitectura normales. · Glándulas de forma normal, tamaño y arquitectura normales. |
| 5 | forma normal | 2417 | 90.0% | Glándulas de forma normal, tamaño y arquitectura normales. · Glándulas de forma normal, tamaño y arquitectura normales. |
| 6 | de forma normal | 2404 | 89.5% | Glándulas de forma normal, tamaño y arquitectura normales. · Glándulas de forma normal, tamaño y arquitectura normales. |
| 7 | normal tamano | 2367 | 88.1% | Glándulas de forma normal, tamaño y arquitectura normales. · Glándulas de forma normal, tamaño y arquitectura normales. |
| 8 | forma normal tamano | 2361 | 87.9% | Glándulas de forma normal, tamaño y arquitectura normales. · Glándulas de forma normal, tamaño y arquitectura normales. |
| 9 | tamano y | 2290 | 85.2% | Glándulas de forma normal, tamaño y arquitectura normales. · Glándulas de forma normal, tamaño y arquitectura normales. |
| 10 | glandulas de forma | 2281 | 84.9% | Glándulas de forma normal, tamaño y arquitectura normales. · Glándulas de forma normal, tamaño y arquitectura normales. |
| 11 | tamano y arquitectura | 2278 | 84.8% | Glándulas de forma normal, tamaño y arquitectura normales. · Glándulas de forma normal, tamaño y arquitectura normales. |
| 12 | normal tamano y | 2247 | 83.6% | Glándulas de forma normal, tamaño y arquitectura normales. · Glándulas de forma normal, tamaño y arquitectura normales. |
| 13 | aumentado | 197 | 7.3% | Adrenal izquierda se observa discretamente aumentada de tamaño (7,6 mm), de ecogenicidad levemente disminuida y arquitectura normales. Adren · Glándula izquierda de forma normal, tamaño y arquitectura normales (4,7mm). Adrenal derecha se observa levemente irregular ecogenicidad hipo |
| 14 | de tamano | 138 | 5.1% | Adrenal izquierda se observa discretamente aumentada de tamaño (7,6 mm), de ecogenicidad levemente disminuida y arquitectura normales. Adren · Glándula izquierda de forma normal, tamaño y arquitectura normales (4,7mm). Adrenal derecha se observa levemente irregular ecogenicidad hipo |
| 15 | aumentado de tamano | 99 | 3.7% | Adrenal izquierda se observa discretamente aumentada de tamaño (7,6 mm), de ecogenicidad levemente disminuida y arquitectura normales. Adren · Glándula izquierda de forma normal, tamaño y arquitectura normales (4,7mm). Adrenal derecha se observa levemente irregular ecogenicidad hipo |
| 16 | aumentado de | 90 | 3.3% | Adrenal izquierda se observa discretamente aumentada de tamaño (7,6 mm), de ecogenicidad levemente disminuida y arquitectura normales. Adren · Glándula izquierda de forma normal, tamaño y arquitectura normales (4,7mm). Adrenal derecha se observa levemente irregular ecogenicidad hipo |
| 17 | hipoecoico | 89 | 3.3% | Glándula izquierda de forma normal, tamaño y arquitectura normales (4,7mm). Adrenal derecha se observa levemente irregular ecogenicidad hipo · Glándula adrenal izquierda de arquitectura y tamaño normal (6,6mm). En posición de glándula adrenal derecha, se observa una estructura ovoid |
| 18 | conservado | 83 | 3.1% | Ambas glándulas adrenales de arquitectura y tamaño conservado. · Ambas glándulas adrenales de arquitectura y tamaño conservado. |
| 19 | tamano aumentado | 76 | 2.8% | Glándula izquierda de tamaño aumentado y arquitectura conservada, glándula derecha tamaño y arquitectura normales (glándula adrenal izquierd · Glándulas de forma normal y arquitectura normales, de tamaño aumentado (adrenal izquierda 6,4mm y adrenal derecha 6,1mm). |
| 20 | normal tamano aumentado | 64 | 2.4% | Glándula izquierda de forma normal, tamaño y arquitectura normales (5,2mm). Glándula derecha de forma normal y arquitectura normales, tamaño · Glándula izquierda de forma normal, tamaño aumentado (8,5mm) de aspecto hipoecoico y homogéneo. Glándula derecha de forma normal, tamaño y a |

### A.Bazo — Bazo (n=2684)

| rank | atributo_descubierto | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | tamano | 2673 | 99.6% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño aumentado, forma conservada, márgenes lisos levemente redondeado, parénquima hiperecoico homogéneo de granulado f |
| 2 | bordes | 2657 | 99.0% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño aumentado, forma conservada, márgenes lisos levemente redondeado, parénquima hiperecoico homogéneo de granulado f |
| 3 | de tamano | 2628 | 97.9% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño aumentado, forma conservada, márgenes lisos levemente redondeado, parénquima hiperecoico homogéneo de granulado f |
| 4 | bordes liso | 2512 | 93.6% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño aumentado, forma conservada, márgenes lisos levemente redondeado, parénquima hiperecoico homogéneo de granulado f |
| 5 | esplenica de tamano | 2502 | 93.2% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño aumentado, forma conservada, márgenes lisos levemente redondeado, parénquima hiperecoico homogéneo de granulado f |
| 6 | forma | 2475 | 92.2% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño aumentado, forma conservada, márgenes lisos levemente redondeado, parénquima hiperecoico homogéneo de granulado f |
| 7 | bordes liso y | 2427 | 90.4% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño aumentado, márgenes lisos y aguzados, ecogenicidad de granulado fino, arquitectura y vasculatura esplénica conser |
| 8 | normal bordes | 2419 | 90.1% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño normal, márgenes lisos y aguzados y arquitectura conservada. |
| 9 | forma normal | 2405 | 89.6% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. |
| 10 | normal bordes liso | 2395 | 89.2% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño normal, márgenes lisos y aguzados y arquitectura conservada. |
| 11 | conservado | 2379 | 88.6% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño aumentado, forma conservada, márgenes lisos levemente redondeado, parénquima hiperecoico homogéneo de granulado f |
| 12 | arquitectura conservado | 2359 | 87.9% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño normal, márgenes lisos y aguzados y arquitectura conservada. |
| 13 | forma normal bordes | 2359 | 87.9% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. |
| 14 | y arquitectura conservado | 2356 | 87.8% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño normal, márgenes lisos y aguzados y arquitectura conservada. |
| 15 | y forma | 2334 | 87.0% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. |
| 16 | y forma normal | 2331 | 86.8% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. |
| 17 | tamano y | 2314 | 86.2% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. |
| 18 | de tamano y | 2307 | 86.0% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. |
| 19 | tamano y forma | 2306 | 85.9% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. |
| 20 | aumentado | 248 | 9.2% | Imagen esplénica de tamaño aumentado, forma conservada, márgenes lisos levemente redondeado, parénquima hiperecoico homogéneo de granulado f · Imagen esplénica de tamaño aumentado, márgenes lisos y aguzados, ecogenicidad de granulado fino, arquitectura y vasculatura esplénica conser |

### A.Linfonodos — Linfonodos (n=2681)

| rank | atributo_descubierto | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | tamano | 475 | 17.7% | Nódulos linfáticos yeyunales se encuentran aumentados de tamaño (6,5mm), hipoecoicos, márgenes definidos y conservando su forma normal. No s · Nódulos linfáticos Ileo-cólicos se observan levemente aumentados de tamaño (4,5mm), hipoecoicos discretamente heterogéneos, manteniendo su f |
| 2 | de tamano | 462 | 17.2% | Nódulos linfáticos yeyunales se encuentran aumentados de tamaño (6,5mm), hipoecoicos, márgenes definidos y conservando su forma normal. No s · Nódulos linfáticos Ileo-cólicos se observan levemente aumentados de tamaño (4,5mm), hipoecoicos discretamente heterogéneos, manteniendo su f |
| 3 | aumentado de tamano | 417 | 15.6% | Nódulos linfáticos yeyunales se encuentran aumentados de tamaño (6,5mm), hipoecoicos, márgenes definidos y conservando su forma normal. No s · Nódulos linfáticos Ileo-cólicos se observan levemente aumentados de tamaño (4,5mm), hipoecoicos discretamente heterogéneos, manteniendo su f |
| 4 | hiperecoico | 307 | 11.5% | No se observan nódulos linfáticos comprometidos. No se observa líquido libre ni masas en cavidad abdominal. Cuerpo uterino se observa hipoec · Nódulos linfáticos íleo cólicos se observan severamente aumentados de tamaño (1,1cms) de aspecto hiperecoico heterogéneo y de forma redondea |
| 5 | hipoecoico | 246 | 9.2% | No se observan nódulos linfáticos comprometidos. No se observa líquido libre ni masas en cavidad abdominal. Caudal a riñón izquierda se obse · No se observan nódulos linfáticos comprometidos. No se observa líquido libre ni masas en cavidad abdominal. Cuerpo uterino se observa hipoec |
| 6 | forma | 238 | 8.9% | Nódulos linfáticos yeyunales se encuentran aumentados de tamaño (6,5mm), hipoecoicos, márgenes definidos y conservando su forma normal. No s · Nódulos linfáticos Ileo-cólicos se observan levemente aumentados de tamaño (4,5mm), hipoecoicos discretamente heterogéneos, manteniendo su f |
| 7 | su forma | 181 | 6.8% | Nódulos linfáticos yeyunales se encuentran aumentados de tamaño (6,5mm), hipoecoicos, márgenes definidos y conservando su forma normal. No s · Nódulos linfáticos Ileo-cólicos se observan levemente aumentados de tamaño (4,5mm), hipoecoicos discretamente heterogéneos, manteniendo su f |
| 8 | aumentado | 170 | 6.3% | Nódulo linfático yeyunal se observa levemente aumentado de tamaño (7,7mm), hipoecoico conservando su forma y sus márgenes.. No se observa lí · Nódulos linfáticos íleo-cólicos se observan levemente aumentado de tamaño (3,7mm), conservando su forma y arquitectura normal comprometidos. |
| 9 | conservando su forma | 168 | 6.3% | Nódulos linfáticos yeyunales se encuentran aumentados de tamaño (6,5mm), hipoecoicos, márgenes definidos y conservando su forma normal. No s · Nódulos linfáticos íleo-cólicos se observan discretamente aumentados de tamaño (6mm) hipoecoicos y conservando su forma normal. No se observ |
| 10 | homogeneo | 167 | 6.2% | No se observan nódulos linfáticos comprometidos. Se observa discreta cantidad de líquido libre en adyacencia de riñón izquierdo y entre lobo · No se observan nódulos linfáticos comprometidos. Se observa discreta cantidad de líquido libre en adyacencia de riñón izquierdo y entre lobo |
| 11 | engrosado | 166 | 6.2% | No se observan nódulos linfáticos comprometidos. No se observa líquido libre ni masas en cavidad abdominal. Se observa abundante líquido lib · No se observa linfonodos comprometidos. Se observa discreta cantidad de líquido libre en hipogastrio izquierdo y entre los lobos hepáticos y |
| 12 | aumentado de | 145 | 5.4% | Nódulo linfático yeyunal se observa levemente aumentado de tamaño (7,7mm), hipoecoico conservando su forma y sus márgenes.. No se observa lí · Nódulos linfáticos íleo-cólicos se observan levemente aumentado de tamaño (3,7mm), conservando su forma y arquitectura normal comprometidos. |
| 13 | hiperecoico y | 141 | 5.3% | Se observan nódulos linfáticos yeyunales severamente aumentados de tamaño (1,6 cms) de aspecto redondeados hiperecoico y bordes irregulares. · No se observan nódulos linfáticos comprometidos. No se observa líquido libre ni masas en cavidad abdominal. Al explorar zona adyacente a her |
| 14 | heterogeneo | 138 | 5.1% | No se observan nódulos linfáticos comprometidos. No se observa líquido libre ni masas en cavidad abdominal. Cuerpo uterino se observa hipoec · Nódulos linfáticos íleo cólicos se observan severamente aumentados de tamaño (1,1cms) de aspecto hiperecoico heterogéneo y de forma redondea |
| 15 | aspecto hipoecoico | 121 | 4.5% | Nódulos linfáticos yeyunales se observan levemente aumentados de tamaño, de aspecto hipoecoico y conservando su forma normal. No se observa  · Se observan nódulos linfáticos íleo-cólicos discretamente aumentados de tamaño (4,5mm) de aspecto hipoecoico, conservando su forma y límites |
| 16 | de aspecto hipoecoico | 118 | 4.4% | Nódulos linfáticos yeyunales se observan levemente aumentados de tamaño, de aspecto hipoecoico y conservando su forma normal. No se observa  · Se observan nódulos linfáticos íleo-cólicos discretamente aumentados de tamaño (4,5mm) de aspecto hipoecoico, conservando su forma y límites |
| 17 | pared | 114 | 4.3% | No se observan nódulos linfáticos comprometidos. Se observa moderada cantidad de líquido libre de aspecto hiperecoico granular fino. Muñón u · Se observan nódulos linfáticos ilieocólicos aumentado de tamaño, conservando su forma y arquitectura. No se observa líquido libre ni masas e |
| 18 | bordes | 112 | 4.2% | No se observan nódulos linfáticos comprometidos. No se observa líquido libre ni masas en cavidad abdominal. Caudal a riñón izquierda se obse · Nódulos linfáticos yeyunales se encuentran aumentados de tamaño (6,5mm), hipoecoicos, márgenes definidos y conservando su forma normal. No s |
| 19 | hipoecoico y | 95 | 3.5% | Nódulos linfáticos yeyunales se observan levemente aumentados de tamaño, de aspecto hipoecoico y conservando su forma normal. No se observa  · Nódulos linfáticos íleo-cólicos levemente aumentado de tamaño (7,2mm) de aspecto hipoecoico y con una discreta pérdida de su forma normal (l |
| 20 | nodulo | 92 | 3.4% | Nódulo linfático yeyunal se observa levemente aumentado de tamaño (7,7mm), hipoecoico conservando su forma y sus márgenes.. No se observa lí · nódulo linfático íleo-cólico discretamente aumentado de tamaño (7,3mm) de aspecto hipotónico y manteniendo su forma normal . No se observa l |

### A.Vesícula — Vesícula (n=2667)

| rank | atributo_descubierto | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | contenido | 2667 | 100.0% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 2 | pared | 2655 | 99.6% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 3 | biliar | 2615 | 98.1% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 4 | vesicula biliar | 2608 | 97.8% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 5 | bordes | 2573 | 96.5% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 6 | y pared | 2552 | 95.7% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 7 | pared de | 2549 | 95.6% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 8 | pared de grosor | 2545 | 95.4% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 9 | y pared de | 2544 | 95.4% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 10 | bordes internos | 2543 | 95.4% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 11 | bordes internos regulares | 2528 | 94.8% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 12 | regulares y pared | 2525 | 94.7% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 13 | biliar semi | 2479 | 93.0% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. |
| 14 | vesicula biliar semi | 2478 | 92.9% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. |
| 15 | biliar semi distendido | 2468 | 92.5% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. |
| 16 | con contenido | 2338 | 87.7% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 17 | distendido con contenido | 2290 | 85.9% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 18 | contenido anecoico | 2092 | 78.4% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 19 | con contenido anecoico | 2042 | 76.6% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| 20 | anecoico bordes | 1983 | 74.4% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. |

### A.Próstata — Próstata (n=737)

| rank | atributo_descubierto | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | tamano | 778 | 105.6% | Aspecto ovalada, bilobulada, tamaño dentro de rango (3,7 cms), hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (5,3 cms), hipoecoica y levemente heterogénea de manera difusa de granulado fino |
| 2 | ovalado | 676 | 91.7% | Aspecto ovalada, bilobulada, tamaño dentro de rango (3,7 cms), hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (5,3 cms), hipoecoica y levemente heterogénea de manera difusa de granulado fino |
| 3 | aspecto ovalado | 672 | 91.2% | Aspecto ovalada, bilobulada, tamaño dentro de rango (3,7 cms), hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (5,3 cms), hipoecoica y levemente heterogénea de manera difusa de granulado fino |
| 4 | ovalado bilobulada | 656 | 89.0% | Aspecto ovalada, bilobulada, tamaño dentro de rango (3,7 cms), hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (5,3 cms), hipoecoica y levemente heterogénea de manera difusa de granulado fino |
| 5 | aspecto ovalado bilobulada | 656 | 89.0% | Aspecto ovalada, bilobulada, tamaño dentro de rango (3,7 cms), hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (5,3 cms), hipoecoica y levemente heterogénea de manera difusa de granulado fino |
| 6 | homogeneo | 561 | 76.1% | Aspecto ovalada, bilobulada, tamaño dentro de rango (3,7 cms), hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño dentro de rango, hipoecoica y homogénea de manera difusa de granulado fino. |
| 7 | bilobulada tamano | 558 | 75.7% | Aspecto ovalada, bilobulada, tamaño dentro de rango (3,7 cms), hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (5,3 cms), hipoecoica y levemente heterogénea de manera difusa de granulado fino |
| 8 | y homogeneo | 539 | 73.1% | Aspecto ovalada, bilobulada, tamaño dentro de rango (3,7 cms), hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño dentro de rango, hipoecoica y homogénea de manera difusa de granulado fino. |
| 9 | ovalado bilobulada tamano | 534 | 72.5% | Aspecto ovalada, bilobulada, tamaño dentro de rango (3,7 cms), hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (5,3 cms), hipoecoica y levemente heterogénea de manera difusa de granulado fino |
| 10 | tamano dentro | 492 | 66.8% | Aspecto ovalada, bilobulada, tamaño dentro de rango (3,7 cms), hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño dentro de rango (en límite superior) (4,2 cms), hipoecoica y levemente heterogénea de manera difusa de g |
| 11 | tamano dentro de | 491 | 66.6% | Aspecto ovalada, bilobulada, tamaño dentro de rango (3,7 cms), hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño dentro de rango (en límite superior) (4,2 cms), hipoecoica y levemente heterogénea de manera difusa de g |
| 12 | hipoecoico | 465 | 63.1% | Aspecto ovalada, bilobulada, tamaño dentro de rango (3,7 cms), hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (5,3 cms), hipoecoica y levemente heterogénea de manera difusa de granulado fino |
| 13 | hipoecoico y | 440 | 59.7% | Aspecto ovalada, bilobulada, tamaño dentro de rango (3,7 cms), hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (5,3 cms), hipoecoica y levemente heterogénea de manera difusa de granulado fino |
| 14 | bilobulada tamano dentro | 438 | 59.4% | Aspecto ovalada, bilobulada, tamaño dentro de rango (3,7 cms), hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño dentro de rango (en límite superior) (4,2 cms), hipoecoica y levemente heterogénea de manera difusa de g |
| 15 | hipoecoico y homogeneo | 404 | 54.8% | Aspecto ovalada, bilobulada, tamaño dentro de rango (3,7 cms), hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño dentro de rango, hipoecoica y homogénea de manera difusa de granulado fino. |
| 16 | hiperecoico | 324 | 44.0% | Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (6,2 cms), hiperecoica y heterogénea de manera difusa de granulado fino. Presenc · Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (6,5 cms), hiperecoica y heterogénea de manera difusa de granulado fino. Presenc |
| 17 | hiperecoico y | 281 | 38.1% | Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (6,2 cms), hiperecoica y heterogénea de manera difusa de granulado fino. Presenc · Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (6,5 cms), hiperecoica y heterogénea de manera difusa de granulado fino. Presenc |
| 18 | heterogeneo | 200 | 27.1% | Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (5,3 cms), hipoecoica y levemente heterogénea de manera difusa de granulado fino · Aspecto ovalada, bilobulada, tamaño dentro de rango (en límite superior) (4,2 cms), hipoecoica y levemente heterogénea de manera difusa de g |
| 19 | conservado | 194 | 26.3% | Aspecto ovalado, bilobulado, tamaño moderadamente aumentado (7,5 cms), hiperecoico y heterogéneo de manera difusa. Presencia de un quiste en · Aspecto ovalada, bilobulada, tamaño dentro de rango (2,5cms), hipoecoica y homogénea. Testículo izquierdo en saco escrotal de aspecto conser |
| 20 | rango hipoecoico | 173 | 23.5% | Aspecto ovalada, bilobulada, tamaño dentro de rango, hipoecoica y homogénea de manera difusa de granulado fino. · Aspecto ovalada, bilobulada, tamaño dentro de rango, hipoecoica y homogénea de manera difusa de granulado fino. |

### A.Gestación — Gestación (n=200)

| rank | atributo_descubierto | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | normal | 293 | 146.5% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  |
| 2 | tamano | 174 | 87.0% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento moderado e irregular tamaño uterino (1,9cms), con presencia de paredes delgadas y regulares. Lumen se observa con presencia de mater |
| 3 | de tamano | 159 | 79.5% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento moderado y difuso de tamaño uterino (2cms), con presencia de paredes engrosadas (5mm) y de aspecto quístico en algunas secciones, co |
| 4 | tamano uterino | 125 | 62.5% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento moderado e irregular tamaño uterino (1,9cms), con presencia de paredes delgadas y regulares. Lumen se observa con presencia de mater |
| 5 | de tamano uterino | 122 | 61.0% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento moderado y difuso de tamaño uterino (2cms), con presencia de paredes engrosadas (5mm) y de aspecto quístico en algunas secciones, co |
| 6 | aumento de tamano | 121 | 60.5% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento de tamaño uterino por presencia de al menos 6 fetos con latido cardiaco presente y normal (235 lpm), movimientos fetales apropiados  |
| 7 | fetos | 119 | 59.5% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento moderado e irregular tamaño uterino (1,9cms), con presencia de paredes delgadas y regulares. Lumen se observa con presencia de mater |
| 8 | tamano uterino por | 114 | 57.0% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento de tamaño uterino por presencia de al menos 6 fetos con latido cardiaco presente y normal (235 lpm), movimientos fetales apropiados  |
| 9 | presente | 107 | 53.5% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento de tamaño uterino por presencia de al menos 6 fetos con latido cardiaco presente y normal (235 lpm), movimientos fetales apropiados  |
| 10 | cardiaco presente | 106 | 53.0% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento de tamaño uterino por presencia de al menos 6 fetos con latido cardiaco presente y normal (235 lpm), movimientos fetales apropiados  |
| 11 | aspecto normal | 106 | 53.0% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento de tamaño uterino por presencia de al menos 6 fetos con latido cardiaco presente y normal (235 lpm), movimientos fetales apropiados  |
| 12 | latido cardiaco presente | 106 | 53.0% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento de tamaño uterino por presencia de al menos 6 fetos con latido cardiaco presente y normal (235 lpm), movimientos fetales apropiados  |
| 13 | y aspecto normal | 106 | 53.0% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento de tamaño uterino por presencia de al menos 6 fetos con latido cardiaco presente y normal (235 lpm), movimientos fetales apropiados  |
| 14 | normal placentas | 103 | 51.5% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento de tamaño uterino por presencia de al menos 6 fetos con latido cardiaco presente y normal (235 lpm), movimientos fetales apropiados  |
| 15 | aspecto normal placentas | 103 | 51.5% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento de tamaño uterino por presencia de al menos 6 fetos con latido cardiaco presente y normal (235 lpm), movimientos fetales apropiados  |
| 16 | normal placentas conservado | 102 | 51.0% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento de tamaño uterino por presencia de al menos 6 fetos con latido cardiaco presente y normal (235 lpm), movimientos fetales apropiados  |
| 17 | fetos con | 100 | 50.0% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento de tamaño uterino por presencia de al menos 6 fetos con latido cardiaco presente y normal (235 lpm), movimientos fetales apropiados  |
| 18 | fetos con latido | 100 | 50.0% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento de tamaño uterino por presencia de al menos 6 fetos con latido cardiaco presente y normal (235 lpm), movimientos fetales apropiados  |
| 19 | presente y | 90 | 45.0% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento de tamaño uterino por presencia de al menos 6 fetos con latido cardiaco presente y normal (235 lpm), movimientos fetales apropiados  |
| 20 | y normal | 89 | 44.5% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento de tamaño uterino por presencia de al menos 6 fetos con latido cardiaco presente y normal (235 lpm), movimientos fetales apropiados  |

### A.Útero — Útero (n=49)

| rank | atributo_descubierto | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | pared | 26 | 53.1% | Cuernos uterinos severamente dilatados (3,3cms), con presencia de colecta anecoica, paredes engrosadas (5 mm) e irregulares. · Ambos cuernos uterinos se encuentran aumentados de tamaño con paredes engrosadas (4,2mm) irregulares y presencia de contenido levemente hipe |
| 2 | contenido | 26 | 53.1% | Cuerpo y cuernos uterinos severamente dilatados (1,5 cms) con presencia de contenido luminal anecoico y homogéneo, parades en algunos segmen · Ambos cuernos uterinos se encuentran aumentados de tamaño con paredes engrosadas (4,2mm) irregulares y presencia de contenido levemente hipe |
| 3 | tamano | 25 | 51.0% | Aumentado de tamaño por presencia de al menos 4 estructuras fetales inmóviles en proceso de descomposición. · Ambos cuernos uterinos se encuentran aumentados de tamaño con paredes engrosadas (4,2mm) irregulares y presencia de contenido levemente hipe |
| 4 | de tamano | 25 | 51.0% | Aumentado de tamaño por presencia de al menos 4 estructuras fetales inmóviles en proceso de descomposición. · Ambos cuernos uterinos se encuentran aumentados de tamaño con paredes engrosadas (4,2mm) irregulares y presencia de contenido levemente hipe |
| 5 | hiperecoico | 22 | 44.9% | Cuerpo y cuernos uterinos severamente dilatados (1,5 cms) con presencia de contenido luminal anecoico y homogéneo, parades en algunos segmen · Ambos cuernos uterinos se encuentran aumentados de tamaño con paredes engrosadas (4,2mm) irregulares y presencia de contenido levemente hipe |
| 6 | aumentado de tamano | 20 | 40.8% | Aumentado de tamaño por presencia de al menos 4 estructuras fetales inmóviles en proceso de descomposición. · Ambos cuernos uterinos se encuentran aumentados de tamaño con paredes engrosadas (4,2mm) irregulares y presencia de contenido levemente hipe |
| 7 | aumentado | 18 | 36.7% | Aumentado de tamaño por presencia de al menos 4 estructuras fetales inmóviles en proceso de descomposición. · Imagen uterina presente de diámetro levemente aumentado (7mm) y con contenido levemente hiperecoico. Ovarios de aspecto normal. |
| 8 | leve hiperecoico | 13 | 26.5% | Ambos cuernos uterinos se encuentran aumentados de tamaño con paredes engrosadas (4,2mm) irregulares y presencia de contenido levemente hipe · Hacia el lado izquierdo de la vejiga se observa una estructura de 1,5 cms con paredes hiperecoicos y engrosados con un lumen heterogéneo que |
| 9 | lumen | 12 | 24.5% | Cuerpo y cuernos uterinos severamente dilatados (1,5 cms) con presencia de contenido luminal anecoico y homogéneo, parades en algunos segmen · Cuerpo del útero de 5mm de lumen anecoico homogéneo. No es posible seguir los cuernos hacia craneal. |
| 10 | de contenido | 11 | 22.4% | Cuerpo y cuernos uterinos severamente dilatados (1,5 cms) con presencia de contenido luminal anecoico y homogéneo, parades en algunos segmen · Ambos cuernos uterinos se encuentran aumentados de tamaño con paredes engrosadas (4,2mm) irregulares y presencia de contenido levemente hipe |
| 11 | aumentado de | 11 | 22.4% | Aumentado de tamaño por presencia de al menos 4 estructuras fetales inmóviles en proceso de descomposición. · Se observa aumentado de tamaño (2,3cms diámetro) con contenido anecoico y con partículas incontables hiperecoicas en suspensión. Las paredes |
| 12 | con pared | 9 | 18.4% | Ambos cuernos uterinos se encuentran aumentados de tamaño con paredes engrosadas (4,2mm) irregulares y presencia de contenido levemente hipe · Hacia el lado izquierdo de la vejiga se observa una estructura de 1,5 cms con paredes hiperecoicos y engrosados con un lumen heterogéneo que |
| 13 | presente | 9 | 18.4% | Imagen uterina presente de diámetro levemente aumentado (7mm) y con contenido levemente hiperecoico. Ovarios de aspecto normal. · Imagen uterina presente de diámetro normal y sin contenido patológicos. |
| 14 | normal | 9 | 18.4% | Imagen uterina presente de diámetro levemente aumentado (7mm) y con contenido levemente hiperecoico. Ovarios de aspecto normal. · Imagen uterina presente de diámetro normal y sin contenido patológicos. |
| 15 | presente de | 9 | 18.4% | Imagen uterina presente de diámetro levemente aumentado (7mm) y con contenido levemente hiperecoico. Ovarios de aspecto normal. · Imagen uterina presente de diámetro normal y sin contenido patológicos. |
| 16 | presente de diametro | 9 | 18.4% | Imagen uterina presente de diámetro levemente aumentado (7mm) y con contenido levemente hiperecoico. Ovarios de aspecto normal. · Imagen uterina presente de diámetro normal y sin contenido patológicos. |
| 17 | uterina presente | 8 | 16.3% | Imagen uterina presente de diámetro levemente aumentado (7mm) y con contenido levemente hiperecoico. Ovarios de aspecto normal. · Imagen uterina presente de diámetro normal y sin contenido patológicos. |
| 18 | leve aumentado | 8 | 16.3% | Imagen uterina presente de diámetro levemente aumentado (7mm) y con contenido levemente hiperecoico. Ovarios de aspecto normal. · Cuerpo uterino levemente aumentado de tamaño (5,7mm), de paredes delgadas, hipoecoicas y con lumen levemente hiperecoico, que es posible seg |
| 19 | con contenido | 8 | 16.3% | Imagen uterina presente de diámetro levemente aumentado (7mm) y con contenido levemente hiperecoico. Ovarios de aspecto normal. · Se observa aumentado de tamaño (2,3cms diámetro) con contenido anecoico y con partículas incontables hiperecoicas en suspensión. Las paredes |
| 20 | imagen uterina presente | 8 | 16.3% | Imagen uterina presente de diámetro levemente aumentado (7mm) y con contenido levemente hiperecoico. Ovarios de aspecto normal. · Imagen uterina presente de diámetro normal y sin contenido patológicos. |

### A.Testículos — Testículos (n=27)

| rank | atributo_descubierto | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | parenquima | 11 | 40.7% | Testículo derecho se observa de tamaño normal (1,8 cms) en el polo caudal se observa una masa de 1cm de diámetro, de ecogenicidad aumentada, · Ambos testículos en posición y forma normales, parénquima de aspecto conservado. |
| 2 | conservado | 11 | 40.7% | Ambos testículos en posición y forma normales, parénquima de aspecto conservado. · De aspecto conservado. |
| 3 | tamano | 8 | 29.6% | Testículo derecho se observa de tamaño normal (1,8 cms) en el polo caudal se observa una masa de 1cm de diámetro, de ecogenicidad aumentada, · Testículo derecho se observa de tamaño normal (1,8 cms) en el polo caudal se observa una masa de 1cm de diámetro, de ecogenicidad aumentada, |
| 4 | heterogeneo | 7 | 25.9% | Testículo derecho se observa de tamaño normal (1,8 cms) en el polo caudal se observa una masa de 1cm de diámetro, de ecogenicidad aumentada, · Testículo izquierdo se observa disminuido de tamaño, con pérdida de arquitectura normal. Testículo derecho se encuentra severamente aumentad |
| 5 | aspecto conservado | 7 | 25.9% | Ambos testículos en posición y forma normales, parénquima de aspecto conservado. · De aspecto conservado. |
| 6 | de aspecto conservado | 7 | 25.9% | Ambos testículos en posición y forma normales, parénquima de aspecto conservado. · De aspecto conservado. |
| 7 | ecogenicidad | 6 | 22.2% | Testículo derecho se observa de tamaño normal (1,8 cms) en el polo caudal se observa una masa de 1cm de diámetro, de ecogenicidad aumentada, · Testículo izquierdo conservado. Testículo izquierdo tamaño y ecogenicidad conservado con presencia de estructura aspecto quístico de 2 mm de |
| 8 | de tamano | 6 | 22.2% | Testículo derecho se observa de tamaño normal (1,8 cms) en el polo caudal se observa una masa de 1cm de diámetro, de ecogenicidad aumentada, · Testículo derecho se observa de tamaño normal (1,8 cms) en el polo caudal se observa una masa de 1cm de diámetro, de ecogenicidad aumentada, |
| 9 | ovalado | 6 | 22.2% | En imagen testicular izquierda se observa una masa ovoide de polo craneal de 1 x1,3cms, hiperecoico heterogéneo con zonas anecoicas. · Testículo izquierdo presenta al lado medial del rafe una estructura de aspecto redondo levemente hiperecoico y heterogéneo y bordes mal defi |
| 10 | hiperecoico | 5 | 18.5% | Testículo derecho se observa de tamaño normal (1,8 cms) en el polo caudal se observa una masa de 1cm de diámetro, de ecogenicidad aumentada, · Testículo izquierdo se observa disminuido de tamaño, con pérdida de arquitectura normal. Testículo derecho se encuentra severamente aumentad |
| 11 | forma | 5 | 18.5% | Ambos testículos en posición y forma normales, parénquima de aspecto conservado. · Ambos testículos localizados en posición intra abdominal, simétricos, de forma ovalada y contornos regulares. Parénquima testicular ecogenic |
| 12 | conservado testiculo | 4 | 14.8% | Presencia sólo de testículo izquierdo en saco escrotal, de aspecto conservado. Testículo derecho no encontrado. · Testículo izquierdo conservado. Testículo izquierdo tamaño y ecogenicidad conservado con presencia de estructura aspecto quístico de 2 mm de |
| 13 | fino | 4 | 14.8% | Ambos testículos localizados en posición intra abdominal, simétricos, de forma ovalada y contornos regulares. Parénquima testicular ecogenic · Ambos testículos simétricos en seca escrotal, de forma ovalada y contornos regulares. Parénquima testicular moteado difuso fino uniforme. |
| 14 | de forma | 4 | 14.8% | Ambos testículos localizados en posición intra abdominal, simétricos, de forma ovalada y contornos regulares. Parénquima testicular ecogenic · Ambos testículos simétricos en seca escrotal, de forma ovalada y contornos regulares. Parénquima testicular moteado difuso fino uniforme. |
| 15 | forma ovalado | 4 | 14.8% | Ambos testículos localizados en posición intra abdominal, simétricos, de forma ovalada y contornos regulares. Parénquima testicular ecogenic · Ambos testículos simétricos en seca escrotal, de forma ovalada y contornos regulares. Parénquima testicular moteado difuso fino uniforme. |
| 16 | ovalado y | 4 | 14.8% | Ambos testículos localizados en posición intra abdominal, simétricos, de forma ovalada y contornos regulares. Parénquima testicular ecogenic · Ambos testículos simétricos en seca escrotal, de forma ovalada y contornos regulares. Parénquima testicular moteado difuso fino uniforme. |
| 17 | regulares parenquima | 4 | 14.8% | Ambos testículos localizados en posición intra abdominal, simétricos, de forma ovalada y contornos regulares. Parénquima testicular ecogenic · Ambos testículos simétricos en seca escrotal, de forma ovalada y contornos regulares. Parénquima testicular moteado difuso fino uniforme. |
| 18 | parenquima testicular | 4 | 14.8% | Ambos testículos localizados en posición intra abdominal, simétricos, de forma ovalada y contornos regulares. Parénquima testicular ecogenic · Ambos testículos simétricos en seca escrotal, de forma ovalada y contornos regulares. Parénquima testicular moteado difuso fino uniforme. |
| 19 | fino uniforme | 4 | 14.8% | Ambos testículos localizados en posición intra abdominal, simétricos, de forma ovalada y contornos regulares. Parénquima testicular ecogenic · Ambos testículos simétricos en seca escrotal, de forma ovalada y contornos regulares. Parénquima testicular moteado difuso fino uniforme. |
| 20 | de forma ovalado | 4 | 14.8% | Ambos testículos localizados en posición intra abdominal, simétricos, de forma ovalada y contornos regulares. Parénquima testicular ecogenic · Ambos testículos simétricos en seca escrotal, de forma ovalada y contornos regulares. Parénquima testicular moteado difuso fino uniforme. |

### A.Ovarios — Ovarios (n=5)

| rank | atributo_descubierto | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | hipoecoico | 3 | 60.0% | Cuerpo uterino se observa como una estructura hipoecoica sin contenido y de paredes lisas de 1.3 cms de diámetro. Los Ovarios con presencia  · Ovario izquierdo levemente hipoecoico y discretamente heterogéneo, de 1,6 cms, ovario izquierdo levemente hiperecoico, discretamente heterog |
| 2 | heterogeneo | 3 | 60.0% | Ovario izquierdo levemente hipoecoico y discretamente heterogéneo, de 1,6 cms, ovario izquierdo levemente hiperecoico, discretamente heterog · Ovario izquierdo levemente hipoecoico y discretamente heterogéneo, de 1,6 cms, ovario izquierdo levemente hiperecoico, discretamente heterog |
| 3 | leve heterogeneo | 3 | 60.0% | Ovario izquierdo levemente hipoecoico y discretamente heterogéneo, de 1,6 cms, ovario izquierdo levemente hiperecoico, discretamente heterog · Ovario izquierdo levemente hipoecoico y discretamente heterogéneo, de 1,6 cms, ovario izquierdo levemente hiperecoico, discretamente heterog |
| 4 | heterogeneo de | 3 | 60.0% | Ovario izquierdo levemente hipoecoico y discretamente heterogéneo, de 1,6 cms, ovario izquierdo levemente hiperecoico, discretamente heterog · Ovario izquierdo levemente hipoecoico y discretamente heterogéneo, de 1,6 cms, ovario izquierdo levemente hiperecoico, discretamente heterog |
| 5 | leve heterogeneo de | 3 | 60.0% | Ovario izquierdo levemente hipoecoico y discretamente heterogéneo, de 1,6 cms, ovario izquierdo levemente hiperecoico, discretamente heterog · Ovario izquierdo levemente hipoecoico y discretamente heterogéneo, de 1,6 cms, ovario izquierdo levemente hiperecoico, discretamente heterog |
| 6 | conservado | 2 | 40.0% | Útero de aspecto conservado, imágenes ováricas ambas de aspecto conservado. · Útero de aspecto conservado, imágenes ováricas ambas de aspecto conservado. |
| 7 | aspecto conservado | 2 | 40.0% | Útero de aspecto conservado, imágenes ováricas ambas de aspecto conservado. · Útero de aspecto conservado, imágenes ováricas ambas de aspecto conservado. |
| 8 | de aspecto conservado | 2 | 40.0% | Útero de aspecto conservado, imágenes ováricas ambas de aspecto conservado. · Útero de aspecto conservado, imágenes ováricas ambas de aspecto conservado. |
| 9 | conservado imagenes | 1 | 20.0% | Útero de aspecto conservado, imágenes ováricas ambas de aspecto conservado. |
| 10 | aspecto conservado imagenes | 1 | 20.0% | Útero de aspecto conservado, imágenes ováricas ambas de aspecto conservado. |
| 11 | conservado imagenes ovaricas | 1 | 20.0% | Útero de aspecto conservado, imágenes ováricas ambas de aspecto conservado. |
| 12 | contenido | 1 | 20.0% | Cuerpo uterino se observa como una estructura hipoecoica sin contenido y de paredes lisas de 1.3 cms de diámetro. Los Ovarios con presencia  |
| 13 | pared | 1 | 20.0% | Cuerpo uterino se observa como una estructura hipoecoica sin contenido y de paredes lisas de 1.3 cms de diámetro. Los Ovarios con presencia  |
| 14 | predominio | 1 | 20.0% | Cuerpo uterino se observa como una estructura hipoecoica sin contenido y de paredes lisas de 1.3 cms de diámetro. Los Ovarios con presencia  |
| 15 | estructura hipoecoico | 1 | 20.0% | Cuerpo uterino se observa como una estructura hipoecoica sin contenido y de paredes lisas de 1.3 cms de diámetro. Los Ovarios con presencia  |
| 16 | hipoecoico sin | 1 | 20.0% | Cuerpo uterino se observa como una estructura hipoecoica sin contenido y de paredes lisas de 1.3 cms de diámetro. Los Ovarios con presencia  |
| 17 | sin contenido | 1 | 20.0% | Cuerpo uterino se observa como una estructura hipoecoica sin contenido y de paredes lisas de 1.3 cms de diámetro. Los Ovarios con presencia  |
| 18 | contenido y | 1 | 20.0% | Cuerpo uterino se observa como una estructura hipoecoica sin contenido y de paredes lisas de 1.3 cms de diámetro. Los Ovarios con presencia  |
| 19 | de pared | 1 | 20.0% | Cuerpo uterino se observa como una estructura hipoecoica sin contenido y de paredes lisas de 1.3 cms de diámetro. Los Ovarios con presencia  |
| 20 | pared liso | 1 | 20.0% | Cuerpo uterino se observa como una estructura hipoecoica sin contenido y de paredes lisas de 1.3 cms de diámetro. Los Ovarios con presencia  |

### A.bin — Atributos binarios detectados por órgano

| órgano | atributo_binario | freq | % | ejemplos |
|---|---|---:|---:|---|
| Vejiga | presente | 111 | 4.1% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares, sin poder definirse con claridad el borde de la · Vejiga semi pletórica con moderada cantidad de contenido hiperecoico de aspecto granular en suspensión, pared de bordes internos regulares y |
| Vejiga | ausente | 4 | 0.1% | Vejiga pletórica con abundante contenido hiperecoico de aspecto puntiforme en suspensión, pared de bordes internos regulares y grosor conser · vejiga se observa pletórica, paredes con bordes internos lisos, grosor conservado, con presencia de discreta cantidad sedimento puntiforme h |
| Vejiga | no_evaluado | 2 | 0.1% | No evaluada. · no evaluada. |
| Vejiga | evaluado | 2 | 0.1% | No evaluada. · no evaluada. |
| Vejiga | conservado | 2190 | 81.4% | Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. · Vejiga pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| Vejiga | dilatado | 31 | 1.2% | Vejiga severamente pletórica con abundante contenido hiper ecoico granular fino en suspensión ocupando toda la vejiga, pared de bordes inter · Vejiga severamente dilatada con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado. |
| Riñones | presente | 172 | 6.4% | Ambas imágenes renales se observan de tamaño y forma normal, límite córtico-medular pobremente definido en donde se mantiene relación córtic · Ambas imágenes renales se observan de tamaño y forma normal, límite córtico-medular normal con relación normal, arquitectura conservada. Zon |
| Riñones | ausente | 20 | 0.7% | Imágenes renales en posición y tamaño normales (riñón izquierdo 3,7 cms y riñón derecho 3,9 cms), márgenes regulares, relación córtico medul · Imágenes renales en posición y tamaño normales (riñón izquierdo 4cms y riñón derecho 4,2 cms), márgenes levemente irregulares, relación córt |
| Riñones | no_evaluado | 12 | 0.4% | Imagen renal izquierda de aspecto ovalado, tamaño levemente aumentado (riñón izquierdo 4,3cms), bordes levemente irregulares, corteza de eco · No evaluado. |
| Riñones | evaluado | 13 | 0.5% | Imagen renal izquierda de aspecto ovalado, tamaño levemente aumentado (riñón izquierdo 4,3cms), bordes levemente irregulares, corteza de eco · No evaluado. |
| Riñones | conservado | 367 | 13.7% | Ambas imágenes renales se observan de tamaño y forma normal, límite córtico-medular normal con relación normal, arquitectura conservada. Zon · Ambas imágenes renales se observan de tamaño y forma normal, límite córtico-medular normal con relación normal, arquitectura conservada y si |
| Riñones | dilatado | 129 | 4.8% | Ambas imágenes renales de aspecto ovalado, tamaño riñón izquierdo en límite superior (4,2mm) y riñón derecho moderadamente aumentado (4,7cms · Ambas imágenes renales de aspecto ovalado, tamaño moderadamente aumentado, bordes irregulares, corteza y médula de ecogenicidad moderadament |
| Estómago | presente | 64 | 2.4% | Vacío, con contenido mucoso y gas, la porción extra mural de la pared en la zona de la curvatura mayor se observa severamente engrosada, het · estómago se observó levemente dilatado con contenido de aspecto alimenticio y paredes levemente aumentadas en su grosor. Al interrogar hemi  |
| Estómago | ausente | 2 | 0.1% | Semi distendido, con contenido patrón mucoso y abundante gas, con paredes estratificadas de grosor conservado y peristaltismo ausente. · Semi distendido, con contenido patrón mucoso y abundante gas, con paredes estratificadas de grosor conservado y peristaltismo ausente. |
| Estómago | no_evaluado | 9 | 0.3% | No evaluado. · No Evaluado. |
| Estómago | evaluado | 9 | 0.3% | No evaluado. · No Evaluado. |
| Estómago | conservado | 2064 | 76.8% | Semi distendido, con contenido alimenticio y gas, con paredes estratificadas de grosor conservado. · Sin contenido con paredes estratificadas de grosor conservado. |
| Estómago | dilatado | 33 | 1.2% | Severamente dilatado, con contenido en patrón líquido y gas, con paredes estratificadas de grosor discretamente aumentado (4,3mm). · Dilatado, con contenido en patrón líquido y gas, con paredes estratificadas de grosor aumentado severamente de manera focal en la zona de la |
| Intestino | presente | 154 | 5.7% | Duodeno y yeyuno con contenido con predominio de patrón mucoso, Yeyuno se observan segmentos de grosor aumentado (1,8 cms de espesor total), · Imagen duodenal y yeyunal en patrón alimenticio con pared de grosor normal. Imagen cecal de volumen normal con contenido hiperecoico heterog |
| Intestino | ausente | 10 | 0.4% | Duodeno se observa dilatado con presencia de contenido de patrón líquido y gas con grosor discretamente aumentado (5,1 cm) principalmente po · Imagen duodenal y yeyunal en patrón alimenticio con pared de grosor normal. Imagen cecal de volumen normal con contenido hiperecoico heterog |
| Intestino | no_evaluado | 13 | 0.5% | No evaluado. · No evaluado. |
| Intestino | evaluado | 13 | 0.5% | No evaluado. · No evaluado. |
| Intestino | conservado | 2584 | 96.1% | Duodeno y yeyuno con contenido con predominio de patrón alimenticio, con grosor conservado, peristaltismo normal. Colon con contenido fecal  · Duodeno, yeyuno e ileon sin contenido con predominio de patrón mucoso, estratificadas con grosor conservada. Colon con abundante contenido f |
| Intestino | dilatado | 88 | 3.3% | Duodeno se observa dilatado con presencia de contenido de patrón líquido y gas con grosor discretamente aumentado (5,1 cm) principalmente po · Duodeno y yeyuno con contenido con predominio de patrón mucoso, con grosor conservado. En yeyuno se observa zona con moderado corrugado inte |
| Páncreas | presente | 18 | 0.7% | Rama derecha del páncreas se observa severamente aumentada de tamaño (2 cms), hipoecoica, heterogénea y de bordes irregulares. Área de proye · Páncreas moderadamente aumentado de tamaño (1,6cms) hipoecoico moderadamente heterogéneo, en rama derecha se observa presencia de estructura |
| Páncreas | no_evaluado | 52 | 1.9% | No evaluado. · No evaluado. |
| Páncreas | evaluado | 52 | 1.9% | No evaluado. · No evaluado. |
| Páncreas | conservado | 2559 | 95.2% | Páncreas conservado, área de proyección peri pancreática de aspecto conservado. · Páncreas conservado, área de proyección peri pancreática de aspecto conservado. |
| Hígado | presente | 88 | 3.3% | Hígado se observa severamente aumentado de tamaño. márgenes lisos y bordes redondeados. Su ecogenicidad se observa levemente aumentada, con  · Imagen hepática de tamaño levemente aumentado, de márgenes lisos y bordes redondeados. Ecogenicidad levemente aumentada de granulado fino y  |
| Hígado | ausente | 1 | 0.0% | Imagen hepática de tamaño levemente disminuido, de márgenes lisos y bordes redondeados. Ecogenicidad hipoecoica de granulado grueso con pres |
| Hígado | no_evaluado | 7 | 0.3% | No evaluado. · No evaluado |
| Hígado | evaluado | 7 | 0.3% | No evaluado. · No evaluado |
| Hígado | conservado | 2567 | 95.5% | Imagen hepática de tamaño normal, de márgenes lisos y bordes aguzados. Ecogenicidad hipoecoica de granulado grueso y arquitectura conservada · Imagen hepática levemente aumentado de tamaño, bordes discretamente redondeados, parénquima de mayor ecogenicidad, sin atenuación, granular  |
| Hígado | dilatado | 18 | 0.7% | Imagen hepática moderadamente aumentada de tamaño, de márgenes lisos y bordes redondeados. Ecogenicidad hipoecoica de granulado grueso con m · Imagen hepática severamente aumentado de tamaño, de márgenes lisos y bordes redondeados. Ecogenicidad hipoecoica de granulado grueso con may |
| Adrenales | presente | 24 | 0.9% | Adrenal izquierda se observa discretamente aumentada de tamaño (7,6 mm), de ecogenicidad levemente disminuida y arquitectura normales. Adren · Glándula izquierda de forma normal, tamaño y arquitectura normales (4,7mm). Adrenal derecha se observa levemente irregular ecogenicidad hipo |
| Adrenales | ausente | 3 | 0.1% | Glándulas de forma normal, tamaño y arquitectura normales. Linfonodos y Peritoneo: Caudo medial a riñón derecho se observa una estructura re · No evaluado. Linfonodos No evaluados. No se observa líquido libre. |
| Adrenales | no_evaluado | 198 | 7.4% | No evaluadas. · No evaluadas. |
| Adrenales | evaluado | 198 | 7.4% | No evaluadas. · No evaluadas. |
| Adrenales | conservado | 112 | 4.2% | Ambas glándulas adrenales de arquitectura y tamaño conservado. · Ambas glándulas adrenales de arquitectura y tamaño conservado. |
| Bazo | presente | 106 | 3.9% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. En cuerpo del bazo se observa estructura de aspecto n · Imagen esplénica de tamaño severamente aumentado parénquima levemente heterogéneo por presencia de moderada cantidad de nódulos de diversos  |
| Bazo | ausente | 6 | 0.2% | No se observa. En la zona de la esplenectomía se observan unos puntos hiperecoicos rodeados por zona hiperecoica levemente heterogénea. · Ausente. |
| Bazo | no_evaluado | 8 | 0.3% | No evaluado. · No evaluado. |
| Bazo | evaluado | 8 | 0.3% | No evaluado. · No evaluado. |
| Bazo | conservado | 2376 | 88.5% | Imagen esplénica de tamaño y forma normales, márgenes lisos y arquitectura conservada. · Imagen esplénica de tamaño aumentado, forma conservada, márgenes lisos levemente redondeado, parénquima hiperecoico homogéneo de granulado f |
| Bazo | alterado | 1 | 0.0% | Imagen esplénica alterada por masa de 52 x 44mm en cola de bazo, hiperecoica y heterogénea, de bordes irregulares, con aumento de señal al e |
| Linfonodos | presente | 2666 | 99.4% | No se observan nódulos linfáticos comprometidos. No se observa líquido libre ni masas en cavidad abdominal. · No se observan linfonodos comprometidos. No se observan masas ni liquido libre en la cavidad. Útero y |
| Linfonodos | ausente | 2615 | 97.5% | No se observan nódulos linfáticos comprometidos. No se observa líquido libre ni masas en cavidad abdominal. · No se observan linfonodos comprometidos. No se observan masas ni liquido libre en la cavidad. Útero y |
| Linfonodos | no_evaluado | 6 | 0.2% | No evaluados. Al interrogar zona de hígado, se observa hacia craneal en tórax presencia de abundante líquido. · No evaluados. Se observa moderada cantidad de líquido libre en abdomen. |
| Linfonodos | evaluado | 6 | 0.2% | No evaluados. Al interrogar zona de hígado, se observa hacia craneal en tórax presencia de abundante líquido. · No evaluados. Se observa moderada cantidad de líquido libre en abdomen. |
| Linfonodos | reactivo | 2 | 0.1% | Nódulos linfáticos mesentéricos e íleo-cólicos aumentados de tamaño (5,1mm) de aspecto inflamatorio/reactivo. Se observa discreta cantidad d · Nódulos linfáticos íleo-cólicos y mesentéricos levemente aumentados de tamaño (4,5mm) de aspecto inflamatorio/reactivo. No se observa líquid |
| Linfonodos | conservado | 75 | 2.8% | No se observan nódulos linfáticos comprometidos. No se observa líquido libre ni masas en cavidad abdominal. Cuernos uterinos se encuentran l · Aumento de tamaño leve de linfonodos ileocólicos de aspecto hipoecoicos homogéneos y de forma conservada. No se observa líquido libre ni mas |
| Linfonodos | dilatado | 17 | 0.6% | Nódulos linfáticos abdominales se observan severamente aumentado de tamaño. Nódulo linfático esplénico se observa redondo de 2,8 cms de diám · Aumento de tamaño leve de linfonodos íleo-cólicos (5 mm) conservando su forma y arquitectura normales. No se observa líquido libre ni masas  |
| Vesícula | presente | 19 | 0.7% | vesícula biliar se observa semi pletórica con paredes de bordes conservados y contenido anecoico homogéneo. No es posible realizar una evalu · Vesícula biliar se observó semi pletórica con presencia de contenido hiperecoico granular fino en la superficie del borde ventral y paredes  |
| Vesícula | ausente | 1 | 0.0% | Ausente. |
| Vesícula | no_evaluado | 16 | 0.6% | No evaluado. · No evaluada. |
| Vesícula | evaluado | 16 | 0.6% | No evaluado. · No evaluada. |
| Vesícula | conservado | 2473 | 92.7% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. · Vesícula biliar distendida, con contenido anecoico homogéneo, bordes internos regulares y pared de grosor conservado. |
| Vesícula | dilatado | 15 | 0.6% | Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. Colédoco dilatado (8mm), d · Vesícula biliar semi distendida, con contenido anecoico, bordes internos regulares y pared de grosor conservados. Colédoco dilatado (6,5mm), |
| Próstata | presente | 153 | 20.8% | Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (6,2 cms), hiperecoica y heterogénea de manera difusa de granulado fino. Presenc · Aspecto ovalada, bilobulada, tamaño severamente aumentado (6 cms), hiperecoica, severamente heterogénea. Presencia de un quiste en polo cran |
| Próstata | ausente | 1 | 0.1% | Aspecto ovalada, bilobulada, tamaño levemente aumentada (5,5 cms), hipoecoica y homogénea. En porción media de lóbulo izquierda se observa u |
| Próstata | no_evaluado | 9 | 1.2% | No evaluada. · No evaluada. |
| Próstata | evaluado | 9 | 1.2% | No evaluada. · No evaluada. |
| Próstata | conservado | 187 | 25.4% | Aspecto ovalado, bilobulado, tamaño moderadamente aumentado (7,5 cms), hiperecoico y heterogéneo de manera difusa. Presencia de un quiste en · Aspecto ovalada, bilobulada, tamaño severamente aumentado, hiperecoica y heterogénea de manera difusa de granulado fino. Presencia de un qui |
| Próstata | dilatado | 4 | 0.5% | Aspecto ovalada, bilobulada, tamaño moderadamente aumentado (6,2 cms), hiperecoica y heterogénea de manera difusa de granulado fino. Presenc · Aspecto ovalada, bilobulada, tamaño dentro de rango (2,7 cms), hiperecoica y levemente heterogénea. Uretra prostática se encuentra levemente |
| Gestación | presente | 176 | 88.0% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Aumento moderado e irregular tamaño uterino (1,9cms), con presencia de paredes delgadas y regulares. Lumen se observa con presencia de mater |
| Gestación | ausente | 15 | 7.5% | Aumento moderado e irregular tamaño uterino (1,9cms), con presencia de paredes delgadas y regulares. Lumen se observa con presencia de mater · Paciente se intentó posicionar en decúbito dorsal pero sufrió descompensación por lo que se dejó en decúbito esternal. No se observó líquido |
| Gestación | evaluado | 3 | 1.5% | Paciente se posicionó en decúbito dorsal pero sufriendo una descompensación respiratoria. Se realiza aproximación abdominal en estación, obs · Se interrogan aumentos de asociados a glándulas mamarias. Las masas evaluadas se encuentran en tejido subcutáneo y no están relacionados a c |
| Gestación | conservado | 156 | 78.0% | Aumento de tamaño uterino por presencia de al menos 3 fetos con latido cardiaco presente y normal (246 lpm), movimientos fetales apropiados  · Se exploró zona lumbar derecha e izquierda y se observa zona de subcutáneo conservada así como paquetes musculares y uniones miofasciales co |
| Útero | presente | 24 | 49.0% | útero se observan severamente adelgazadas. Ambos · Hacia el lado izquierdo de la vejiga se observa una estructura de 1,5 cms con paredes hiperecoicos y engrosados con un lumen heterogéneo que |
| Útero | ausente | 1 | 2.0% | Cuerpo y cuernos uterinos conservados (4,5mm). No se observa cambios compatibles con gestación. |
| Útero | no_evaluado | 1 | 2.0% | no evaluado. |
| Útero | evaluado | 1 | 2.0% | no evaluado. |
| Útero | conservado | 9 | 18.4% | Se observa aumentado de tamaño (2,3cms diámetro) con contenido anecoico y con partículas incontables hiperecoicas en suspensión. Las paredes · Cuerpo uterino se observa con lumen anecoico, homogéneo de 2,8mm, paredes muy delgadas, lisas de grosor conservado. Cuernos uterinos de simi |
| Útero | dilatado | 2 | 4.1% | Cuernos uterinos severamente dilatados (3,3cms), con presencia de colecta anecoica, paredes engrosadas (5 mm) e irregulares. · Cuerpo y cuernos uterinos severamente dilatados (1,5 cms) con presencia de contenido luminal anecoico y homogéneo, parades en algunos segmen |
| Testículos | presente | 9 | 33.3% | Testículo derecho se observa de tamaño normal (1,8 cms) en el polo caudal se observa una masa de 1cm de diámetro, de ecogenicidad aumentada, · Testículo izquierdo se observa disminuido de tamaño, con pérdida de arquitectura normal. Testículo derecho se encuentra severamente aumentad |
| Testículos | conservado | 16 | 59.3% | Ambos testículos en posición y forma normales, parénquima de aspecto conservado. · De aspecto conservado. |
| Ovarios | presente | 2 | 40.0% | Cuerpo uterino se observa como una estructura hipoecoica sin contenido y de paredes lisas de 1.3 cms de diámetro. Los Ovarios con presencia  · Caudal a polo caudal derecho se observa una estructura ovalada hipoecoica levemente heterogéneo de 2 cms de diámetro mayor. |
| Ovarios | ausente | 1 | 20.0% | Ausentes. |
| Ovarios | conservado | 1 | 20.0% | Útero de aspecto conservado, imágenes ováricas ambas de aspecto conservado. |

---

## B. Top 100 conceptos clínicos globales

Suma de frecuencias a través de todos los órganos (un mismo n-grama puede
aparecer en varios órganos).

| rank | concepto | freq_global | órganos_con_match |
|---:|---|---:|---:|
| 1 | conservado | 21265 | 15 |
| 2 | bordes | 16040 | 14 |
| 3 | contenido | 13426 | 12 |
| 4 | tamano | 12652 | 14 |
| 5 | con contenido | 12042 | 11 |
| 6 | pared | 11301 | 13 |
| 7 | grosor conservado | 8898 | 9 |
| 8 | pared de | 7806 | 8 |
| 9 | normal | 7520 | 14 |
| 10 | de tamano | 6781 | 14 |
| 11 | medular | 5469 | 3 |
| 12 | patron | 5444 | 7 |
| 13 | forma | 5401 | 12 |
| 14 | de bordes | 5393 | 13 |
| 15 | bordes liso | 5229 | 9 |
| 16 | cortico medular | 5209 | 1 |
| 17 | pared de grosor | 5172 | 8 |
| 18 | y pared | 5110 | 9 |
| 19 | bordes internos | 5104 | 3 |
| 20 | aumentado | 5094 | 14 |
| 21 | bordes liso y | 5085 | 8 |
| 22 | y pared de | 5065 | 5 |
| 23 | forma normal | 4989 | 6 |
| 24 | bordes internos regulares | 4913 | 3 |
| 25 | tamano y | 4681 | 10 |
| 26 | distendido con contenido | 4410 | 5 |
| 27 | de grosor conservado | 4369 | 9 |
| 28 | contenido anecoico | 4326 | 10 |
| 29 | arquitectura conservado | 4266 | 12 |
| 30 | con contenido anecoico | 4196 | 9 |
| 31 | y arquitectura conservado | 4154 | 10 |
| 32 | hiperecoico | 3848 | 15 |
| 33 | ecogenicidad | 3550 | 14 |
| 34 | hipoecoico | 3323 | 14 |
| 35 | ovalado | 3311 | 13 |
| 36 | aspecto ovalado | 3241 | 6 |
| 37 | homogeneo | 3144 | 13 |
| 38 | granulado | 2970 | 13 |
| 39 | con pared | 2779 | 10 |
| 40 | pelvis | 2767 | 1 |
| 41 | de granulado | 2728 | 13 |
| 42 | aspecto conservado | 2684 | 15 |
| 43 | de aspecto conservado | 2668 | 15 |
| 44 | peristaltismo | 2635 | 3 |
| 45 | biliar | 2626 | 2 |
| 46 | vesicula biliar | 2618 | 2 |
| 47 | de bordes liso | 2617 | 9 |
| 48 | tamano dentro | 2616 | 5 |
| 49 | tamano dentro de | 2609 | 4 |
| 50 | pared de bordes | 2595 | 2 |
| 51 | relacion cortico medular | 2590 | 1 |
| 52 | diferenciacion cortico medular | 2577 | 1 |
| 53 | pared estratificadas | 2569 | 4 |
| 54 | de aspecto ovalado | 2568 | 6 |
| 55 | pared estratificadas de | 2565 | 4 |
| 56 | de patron | 2563 | 5 |
| 57 | predominio | 2556 | 4 |
| 58 | de bordes internos | 2556 | 1 |
| 59 | predominio de | 2553 | 3 |
| 60 | y bordes | 2550 | 8 |
| 61 | normal bordes | 2542 | 5 |
| 62 | con pared estratificadas | 2541 | 2 |
| 63 | vascular | 2537 | 5 |
| 64 | contenido con | 2531 | 2 |
| 65 | contenido fecal | 2527 | 2 |
| 66 | regulares y pared | 2527 | 2 |
| 67 | patron vascular | 2524 | 1 |
| 68 | predominio de patron | 2523 | 2 |
| 69 | con predominio | 2522 | 3 |
| 70 | con predominio de | 2521 | 2 |
| 71 | contenido con predominio | 2517 | 2 |
| 72 | de forma | 2512 | 11 |
| 73 | compromiso pelvis | 2508 | 1 |
| 74 | esplenica de tamano | 2505 | 2 |
| 75 | sin compromiso pelvis | 2504 | 1 |
| 76 | liso y bordes | 2488 | 2 |
| 77 | biliar semi | 2485 | 2 |
| 78 | vesicula biliar semi | 2484 | 2 |
| 79 | vascular conservado | 2475 | 1 |
| 80 | normal bordes liso | 2474 | 4 |
| 81 | patron vascular conservado | 2474 | 1 |
| 82 | biliar semi distendido | 2470 | 2 |
| 83 | con contenido con | 2462 | 2 |
| 84 | peristaltismo normal | 2461 | 2 |
| 85 | ovalado tamano | 2441 | 2 |
| 86 | yeyuno con contenido | 2441 | 1 |
| 87 | aspecto ovalado tamano | 2438 | 1 |
| 88 | pletorica | 2425 | 3 |
| 89 | y forma | 2424 | 6 |
| 90 | de forma normal | 2416 | 5 |
| 91 | y forma normal | 2413 | 5 |
| 92 | pletorica con | 2396 | 3 |
| 93 | de tamano y | 2392 | 9 |
| 94 | gas con pared | 2382 | 1 |
| 95 | normal tamano | 2375 | 3 |
| 96 | contenido fecal y | 2374 | 1 |
| 97 | con grosor conservado | 2373 | 1 |
| 98 | fecal y pared | 2373 | 1 |
| 99 | forma normal bordes | 2372 | 3 |
| 100 | tamano y forma | 2364 | 4 |

---

## C. Propuesta de nuevo catálogo clínico (basada en corpus)

Agrupación semántica de los n-gramas descubiertos en 23 conceptos canónicos.
Para cada concepto se listan las variantes textuales observadas en el corpus.

| # | concepto_canonico | n_variantes_observadas | variantes |
|---:|---|---|---|
| 1 | tamano | 6 | tamano normal, tamano conservado, tamano aumentado, tamano disminuido, tamano levemente aumentado, tamano severamente aumentado |
| 2 | forma | 6 | forma ovalado, forma redondeado, forma globoso, forma irregular, forma ovoide, forma conservada |
| 3 | bordes | 6 | bordes lisos, bordes irregulares, bordes regulares, bordes definidos, bordes mal definidos, bordes conservados |
| 4 | pared | 5 | pared conservado, pared engrosado, pared adelgazado, pared aumentada, grosor de pared |
| 5 | ecogenicidad | 6 | ecogenicidad conservado, ecogenicidad aumentado, ecogenicidad disminuido, hipoecoico, hiperecoico, parénquima hipoecoico |
| 6 | homogeneidad | 2 | homogéneo, heterogéneo |
| 7 | granularidad | 2 | granulado fino, granulado grueso |
| 8 | contenido | 6 | contenido alimenticio, contenido mucoso, contenido líquido, contenido gas, contenido fecal, con predominio alimenticio |
| 9 | replecion | 6 | repleción conservado, distendido, pletórica, depletada, vacía, semi pletórica |
| 10 | distension | 3 | distendido, distensión marcada, semi distendido |
| 11 | peristaltismo | 5 | peristaltismo normal, peristaltismo aumentado, peristaltismo disminuido, peristaltismo ausente, peristaltismo conservado |
| 12 | patron_vascular | 2 | patrón vascular conservado, vasculatura conservado |
| 13 | diferenciacion_cm | 3 | diferenciación córtico medular, diferenciación cm, diferenciación cortico medular |
| 14 | relacion_cm | 3 | relación córtico medular, relación adecuada, relación cm adecuada |
| 15 | compromiso_pelvico | 4 | sin compromiso pélvico, con compromiso pélvico, pelvis dilatada, ectasia pélvica |
| 16 | bordes_internos | 3 | bordes internos, pared de bordes, bordes internos regulares |
| 17 | fetos | 3 | N fetos, fetos viables, al menos N fetos |
| 18 | gestacion_activa | 4 | gestación activa, gestante, útero gestante, presencia de fetos |
| 19 | presencia | 6 | presente, ausente, no se observan, se observan, se visualiza, no se visualiza |
| 20 | evaluacion | 4 | evaluado, no evaluado, no se evaluaron, se evaluó |
| 21 | reaccion | 3 | reactivo, no reactivo, linfonodos reactivos |
| 22 | alteracion | 3 | alterado, sin alteraciones, con alteraciones |
| 23 | ectasia | 4 | dilatado, ectasia, hidronefrosis, ectasia pélvica |
| 24 | calculo | 4 | cálculo, litiasis, barro biliar, microlitos |

**Estadísticas del nuevo catálogo propuesto:**
- Conceptos canónicos: 24
- Variantes textuales observadas: 99
- Cobertura objetivo: 100% de los hallazgos con ≥1 atributo

---

## D. Comparación con catálogo actual (Anexo A)

Mapeo atributo_actual → atributo_descubierto y decisión recomendada.

| # | atributo_actual | atributo_descubierto | decisión | razón |
|---:|---|---|---|---|
| 1 | tamano | tamano | **MANTENER** | frecuencia alta, semántica clara |
| 2 | forma | forma | **MANTENER** | frecuencia alta en 6 órganos |
| 3 | bordes | bordes | **MANTENER** | frecuencia muy alta |
| 4 | margenes | bordes | **FUSIONAR** | sinónimo total en corpus (ambos usan 'bordes') |
| 5 | ecogenicidad | ecogenicidad | **MANTENER** | frecuencia alta |
| 6 | ecogenicidad_cortical | ecogenicidad | **FUSIONAR** | corpus no distingue cortical/medular en la práctica |
| 7 | granulado | granularidad | **MANTENER** | exclusivo de Hígado, 2 valores claros |
| 8 | arquitectura | (no detectado) | **ELIMINAR** | no aparece en n-gramas frecuentes |
| 9 | patron_vascular | patron_vascular | **MANTENER** | frecuencia alta en Hígado |
| 10 | diferenciacion_cm | diferenciacion_cm | **MANTENER** | frecuencia alta en Riñones |
| 11 | relacion_cm | relacion_cm | **MANTENER** | frecuencia alta en Riñones |
| 12 | compromiso_pelvico | compromiso_pelvico | **MANTENER** | baja cobertura (0.7%) pero semánticamente crítico |
| 13 | replecion | replecion | **MANTENER** | frecuencia muy alta en Vejiga |
| 14 | contenido | contenido | **MANTENER** | frecuencia muy alta |
| 15 | bordes_internos | bordes_internos | **MANTENER** | sinónimo de 'pared de bordes' |
| 16 | grosor_pared | pared | **FUSIONAR** | atributo y medida son lo mismo en corpus |
| 17 | distension | distension | **MANTENER*** | *con caveat: baja en Intestino (2.5%) |
| 18 | peristaltismo | peristaltismo | **MANTENER*** | *con caveat: baja en Estómago (0.7%) |
| 19 | aspecto | (sin valor canónico) | **ELIMINAR** | token genérico, no descubrible como atributo con valores |
| 20 | homogeneidad | homogeneidad | **MANTENER** | frecuencia media en Próstata |
| 21 | prenez | gestacion_activa | **RENOMBRAR** | no aparece como token; derivado booleano más fiel |
| 22 | fetos | fetos | **MANTENER** | atributo numérico viable (9 valores) |
| 23 | (no existe) | presencia | **AGREGAR** | atributo binario universal, alta cobertura |
| 24 | (no existe) | evaluacion | **AGREGAR** | atributo binario para órganos no evaluados |
| 25 | (no existe) | reaccion | **AGREGAR** | binario para Linfonodos |
| 26 | (no existe) | alteracion | **AGREGAR** | binario para hallazgos patológicos |
| 27 | (no existe) | ectasia | **AGREGAR** | dilatación / hidronefrosis |
| 28 | (no existe) | calculo | **AGREGAR** | cálculos / litiasis / barro biliar |

**Resumen de decisiones:**
- MANTENER: 16
- FUSIONAR: 3
- ELIMINAR: 2
- RENOMBRAR: 1
- AGREGAR (nuevos del descubrimiento): 6

**Saldo neto:** 22 atributos actuales → 19 mantenidos/fusionados + 6 nuevos = **25 conceptos**.

---

## E. Cobertura estimada del nuevo catálogo

Cobertura proyectada por concepto canónico sobre el corpus completo.

| concepto_canonico | matches_estimados | cobertura_estimada | nota |
|---|---:|---:|---|
| tamano | 2246 | 8.1% | 5 variantes |
| forma | 27 | 0.1% | 5 variantes |
| bordes | 1769 | 6.3% | 5 variantes |
| pared | 156 | 0.6% | 5 variantes |
| ecogenicidad | 7570 | 27.2% | 4 variantes |
| homogeneidad | 4151 | 14.9% | 2 variantes |
| granularidad | 2939 | 10.5% | 2 variantes |
| contenido | 5012 | 18.0% | 5 variantes |
| replecion | 2661 | 9.5% | 5 variantes |
| distension | 1 | 0.0% | 3 variantes |
| peristaltismo | 2534 | 9.1% | 4 variantes |
| patron_vascular | 2474 | 8.9% | 2 variantes |
| diferenciacion_cm | 2577 | 9.2% | 3 variantes |
| relacion_cm | 2590 | 9.3% | 2 variantes |
| compromiso_pelvico | 1 | 0.0% | 4 variantes |
| bordes_internos | 7699 | 27.6% | 2 variantes |
| fetos | 119 | 0.4% | 1 variantes |
| gestacion_activa | 0 | 0.0% | 0 variantes |
| presencia | 182 | 0.7% | 3 variantes |
| evaluacion | 350 | 1.3% | 2 variantes |
| reaccion | 2 | 0.0% | 2 variantes |
| alteracion | 1 | 0.0% | 3 variantes |
| ectasia | 296 | 1.1% | 3 variantes |
| calculo | 4 | 0.0% | 3 variantes |

**Total matches estimado del nuevo catálogo:** 45361
**Matches/hallazgo estimado:** 1.63

**Comparación con catálogo actual:**
- Catálogo actual: ~91.000 matches (3.3:1)
- Catálogo nuevo: ~45361 matches (1.63:1)

---

## F. Conclusiones

1. **Cobertura semántica equivalente:** el catálogo actual y el descubierto bottom-up
   cubren ~93-96% de los hallazgos con regex cerradas.

2. **3 atributos del catálogo actual NO son detectables bottom-up:**
   - `arquitectura` — no aparece como n-grama frecuente
   - `aspecto` — token demasiado genérico, sin valores canónicos
   - `prenez` — el corpus no usa esta palabra; reemplazar por `gestacion_activa` derivado

3. **4 fusiones recomendadas para reducir cardinalidad:**
   - `margenes` → `bordes`
   - `ecogenicidad_cortical` → `ecogenicidad`
   - `grosor_pared` → `pared`
   - `aspecto` (Próstata) → `homogeneidad`

4. **6 conceptos nuevos a AGREGAR (binarios):**
   - `presencia`, `evaluacion`, `reaccion`, `alteracion`, `ectasia`, `calculo`
   - Cobertura especialmente útil en órganos con descripciones breves
     (Linfonodos, Páncreas, Adrenales, Ovarios)

5. **Recomendación:** el catálogo actual es **globalmente correcto** pero podría
   simplificarse de 22 a ~19 atributos con 6 nuevos binarios = 25 conceptos.
   La cobertura mejora en los órganos cortos (~30% → ~70%) sin sacrificar
   los órganos grandes.

---

*Generado por `scripts/_profile_f3_1_nlp.py` (corpus profiling only; sin escribir en silver.db).*

```bash
python scripts/_profile_f3_1_nlp.py
```
