# F3.1 — Clinical Attribute Model Revision

**Estado:** 📋 REVISIÓN DE CATÁLOGO (pre-implementación)
**Generado:** 2026-06-22
**Fuentes:**
- **Primaria:** plantilla clínica oficial de la veterinaria (atributos mandatorios)
- **Secundaria:** corpus RAW 27.866 hallazgos (validación de cobertura, variantes, sinónimos)

**Principio:** la plantilla clínica tiene **prioridad absoluta** sobre el corpus.
El corpus se usa solo para validar que los atributos clínicos son extraíbles,
descubrir variantes textuales, sinónimos y formas abreviadas.

---

## 0. Resumen ejecutivo

| Resultado | Valor |
|---|---|
| Atributos en plantilla clínica | 40 (en 12 órganos) |
| Atributos en catálogo actual (Anexo A) | 22 nombres únicos / 57 pares |
| Cobertura promedio del catálogo clínico sobre corpus | **97.6%** (≥1 atributo matcheado) |
| Atributos clínicos con cobertura ≥50% | **40 / 41** (97.6%) |
| Atributos clínicos con cobertura <10% | **1** (`Páncreas.aspecto_peripancreatico` 0.1%) |
| Atributos a ELIMINAR del catálogo actual | 18 (no en plantilla) |
| Atributos a FUSIONAR | 3 (aspecto → forma+lobulacion, etc.) |
| Atributos a RENOMBRAR | 3 (cm → corticomedular) |
| Nuevos atributos a AGREGAR | 7 (homogeneidad_contenido, lobulacion, estratificacion_pared×2, aspecto_peripancreatico, líquido_libre, masas) |
| **Catálogo F3 final propuesto** | **30 atributos / 49 pares** (era 22 / 57) |

**Cambio estructural clave:** Riñones soporta dos modos (UNIFICADO / SEPARADO con
lateralidad) e Intestino se reorganiza por segmento anatómico
(duodeno/yeyuno / peristaltismo / colon).

---

## 1. Plantilla clínica oficial (fuente primaria)

Atributos mandatorios definidos por la veterinaria. Estos **deben** existir en F3.

### 1.1. Tabla maestra

| Órgano | # | Atributos clínicos |
|---|---:|---|
| **Vejiga** | 5 | replecion, contenido, homogeneidad_contenido, bordes_internos, grosor_pared |
| **Próstata** | 5 | forma, lobulacion, tamaño, ecogenicidad, homogeneidad |
| **Riñones** | 7 | forma, tamaño, bordes, ecogenicidad_cortical, diferenciacion_corticomedular, relacion_corticomedular, compromiso_pelvico |
| **Bazo** | 4 | tamaño, forma, margenes, arquitectura |
| **Estómago** | 4 | distension, contenido, estratificacion_pared, grosor_pared |
| **Hígado** | 7 | tamaño, margenes, bordes, ecogenicidad, granulado, arquitectura, patron_vascular |
| **Vesícula** | 4 | distension, contenido, bordes_internos, grosor_pared |
| **Intestino** | 6 | (duodeno/yeyuno: contenido, grosor_pared, estratificacion_pared) + peristaltismo + (colon: contenido, paredes) |
| **Páncreas** | 2 | preservacion, aspecto_peripancreatico |
| **Adrenales** | 3 | forma, tamaño, arquitectura |
| **Linfonodos** | 2 | presencia, compromiso |
| **Cavidad abdominal** | 2 | liquido_libre, masas |
| **Total** | **51** | (en 12 órganos) |

### 1.2. Reglas especiales

**Riñones — modos de descripción:**
1. **UNIFICADO**: ambos riñones descritos conjuntamente ("ambas imágenes renales…")
2. **SEPARADO**: riñón izquierdo y derecho descritos individualmente ("riñón izquierdo…riñón derecho…")

**Intestino — segmentación anatómica:**
- Duodeno/yeyuno comparten los mismos 3 atributos (contenido, grosor_pared, estratificacion_pared)
- Peristaltismo es global
- Colon tiene sus propios atributos (contenido, paredes)

**Páncreas — `preservacion` y `aspecto_peripancreatico`:**
Son esencialmente binarios: el primero indica si el páncreas fue evaluable/preservado;
el segundo describe el tejido graso peripancreático (normal / alterado).

---

## 2. Catálogo actual (Anexo A) — referencia

22 atributos únicos / 57 pares distribuidos en 15 órganos:

```
Hígado:    tamaño, márgenes, bordes, ecogenicidad, granulado, arquitectura, patron_vascular  (7)
Riñones:   forma, tamaño, bordes, ecogenicidad_cortical, diferenciacion_cm, relacion_cm, compromiso_pelvico  (7)
Vejiga:    replecion, contenido, bordes_internos, grosor_pared  (4)
Vesícula:  distension, contenido, bordes_internos, grosor_pared  (4)
Bazo:      tamaño, forma, márgenes, arquitectura  (4)
Próstata:  aspecto, tamaño, ecogenicidad, homogeneidad  (4)
Estómago:  distension, contenido, grosor_pared, peristaltismo  (4)
Intestino: distension, contenido, grosor_pared, peristaltismo  (4)
Páncreas:  ecogenicidad, tamaño  (2)
Adrenales: tamaño, forma  (2)
Linfonodos:tamaño, forma, ecogenicidad, homogeneidad  (4)
Útero:     tamaño, contenido, grosor_pared  (3)        [NO en plantilla]
Ovarios:   tamaño, forma  (2)                            [NO en plantilla]
Testículos:tamaño, forma, ecogenicidad, homogeneidad  (4) [NO en plantilla]
Gestación: fetos, preñez  (2)                            [NO en plantilla]
```

---

## 3. Comparación atributo por atributo

### 3.1. Vejiga (5 clínico / 4 actual)

| Atributo clínico | Catálogo actual | Decisión | Cobertura corpus |
|---|---|---|---:|
| replecion | replecion | ✅ MANTENER | 99.5% |
| contenido | contenido | ✅ MANTENER | 99.0% |
| **homogeneidad_contenido** | (no existe) | 🆕 **AGREGAR** | 79.0% |
| bordes_internos | bordes_internos | ✅ MANTENER | 95.3% |
| grosor_pared | grosor_pared | ✅ MANTENER | 95.3% |

**Cambios:** +1 atributo (`homogeneidad_contenido`).

### 3.2. Próstata (5 clínico / 4 actual)

| Atributo clínico | Catálogo actual | Decisión | Cobertura corpus |
|---|---|---|---:|
| forma | (era "aspecto") | 🔀 FUSIONAR | 91.5% |
| **lobulacion** | (no existe) | 🆕 **AGREGAR** | 97.6% |
| tamaño | tamaño | ✅ MANTENER | 97.7% |
| ecogenicidad | ecogenicidad | ✅ MANTENER | 97.2% |
| homogeneidad | homogeneidad | ✅ MANTENER | 97.6% |

**Cambios:** eliminar `aspecto` (token genérico sin valor canónico). Agregar `lobulacion`
y `forma` separados. `lobulacion` se manifiesta como "bilobulada/o" en el corpus.

### 3.3. Riñones (7 clínico / 7 actual)

| Atributo clínico | Catálogo actual | Decisión | Cobertura corpus |
|---|---|---|---:|
| forma | forma | ✅ MANTENER | 97.3% |
| tamaño | tamaño | ✅ MANTENER | 99.3% |
| bordes | bordes | ✅ MANTENER | 96.9% |
| ecogenicidad_cortical | ecogenicidad_cortical | ✅ MANTENER | 39.3% ⚠️ |
| **diferenciacion_corticomedular** | diferenciacion_cm | 🔁 RENOMBRAR | 95.1% |
| **relacion_corticomedular** | relacion_cm | 🔁 RENOMBRAR | 95.7% |
| compromiso_pelvico | compromiso_pelvico | ✅ MANTENER | 92.1% |

**Cambios:**
- Renombrar `_cm` → `_corticomedular` (consistencia con nomenclatura clínica).
- `ecogenicidad_cortical` se mantiene pero la regex debe aceptar "ecogenicidad"
  sin calificador (cobertura real sería ~97% si se afloja).
- **Modo UNIFICADO/SEPARADO**: el corpus muestra 95% bilateral + 37% izq + 37% der.
  La extracción debe preservar lateralidad en `silver_atributos_hallazgo`.

### 3.4. Bazo (4 clínico / 4 actual)

| Atributo clínico | Catálogo actual | Decisión | Cobertura corpus |
|---|---|---|---:|
| tamaño | tamaño | ✅ MANTENER | 98.4% |
| forma | forma | ✅ MANTENER | 92.0% |
| margenes | márgenes | ✅ MANTENER | 95.5% |
| arquitectura | arquitectura | ✅ MANTENER | 91.1% |

**Cambios:** ninguno. Normalizar acento (márgenes → margenes en BD).

### 3.5. Estómago (4 clínico / 4 actual)

| Atributo clínico | Catálogo actual | Decisión | Cobertura corpus |
|---|---|---|---:|
| distension | distension | ✅ MANTENER | 97.5% |
| contenido | contenido | ✅ MANTENER | 99.2% |
| **estratificacion_pared** | (no existe) | 🆕 **AGREGAR** | 94.9% |
| grosor_pared | grosor_pared | ✅ MANTENER | 97.6% |
| (sigue en clínico?) ~~peristaltismo~~ | peristaltismo | ❌ **MOVER a Intestino** | 0.7% (corpus no lo usa) |

**Cambios:** +1 atributo (`estratificacion_pared`), mover `peristaltismo` a Intestino.

### 3.6. Hígado (7 clínico / 7 actual)

| Atributo clínico | Catálogo actual | Decisión | Cobertura corpus |
|---|---|---|---:|
| tamaño | tamaño | ✅ MANTENER | 99.5% |
| margenes | márgenes | ✅ MANTENER | 99.1% |
| bordes | bordes | ✅ MANTENER | 93.4% |
| ecogenicidad | ecogenicidad | ✅ MANTENER | 97.7% |
| granulado | granulado | ✅ MANTENER | 95.8% |
| arquitectura | arquitectura | ✅ MANTENER | 68.6% |
| patron_vascular | patron_vascular | ✅ MANTENER | 93.9% |

**Cambios:** ninguno.

### 3.7. Vesícula (4 clínico / 4 actual)

| Atributo clínico | Catálogo actual | Decisión | Cobertura corpus |
|---|---|---|---:|
| distension | distension | ✅ MANTENER | 99.0% |
| contenido | contenido | ✅ MANTENER | 99.0% |
| bordes_internos | bordes_internos | ✅ MANTENER | 95.4% |
| grosor_pared | grosor_pared | ✅ MANTENER | 96.0% |

**Cambios:** ninguno.

### 3.8. Intestino (6 clínico / 4 actual) — REORGANIZACIÓN

| Atributo clínico | Catálogo actual | Decisión | Cobertura corpus |
|---|---|---|---:|
| **duodeno_yeyuno.contenido** | contenido | 🔀 FUSIONAR en sub-segmento | 96.7% |
| **duodeno_yeyuno.grosor_pared** | grosor_pared | 🔀 FUSIONAR en sub-segmento | 95.2% |
| **duodeno_yeyuno.estratificacion_pared** | (no existe) | 🆕 **AGREGAR** | n/d |
| **peristaltismo** (global) | peristaltismo | ✅ MANTENER + MOVER desde Estómago | 93.4% |
| **colon.contenido** | (no existe) | 🆕 **AGREGAR** | n/d |
| **colon.paredes** | (no existe) | 🆕 **AGREGAR** | n/d |
| ~~distension~~ | distension | ❌ **ELIMINAR** | 2.5% (corpus no usa) |

**Cambios:** reorganización completa por segmento. Distribución de menciones:
- **colon** 97.0% — "colon con contenido…"
- **duodeno** 96.2% — "duodeno con…"
- **yeyuno** 96.1% — "yeyuno con…"
- ileon 1.8%, ciego 0.3%, recto 0.0%

> Nota: la plantilla clínica usa "duodeno/yeyuno" como segmento único. El corpus
> usa ambos términos. Se recomienda tratarlos como un solo segmento (95%+ cobertura
> en al menos uno).

### 3.9. Páncreas (2 clínico / 2 actual) — REEMPLAZO TOTAL

| Atributo clínico | Catálogo actual | Decisión | Cobertura corpus |
|---|---|---|---:|
| **preservacion** | (no existe) | 🆕 **AGREGAR** | 97.1% |
| **aspecto_peripancreatico** | (no existe) | 🆕 **AGREGAR** | 0.1% ❌ |
| ~~ecogenicidad~~ | ecogenicidad | ❌ ELIMINAR | 7.2% |
| ~~tamaño~~ | tamaño | ❌ ELIMINAR | 1.1% |

**Cambios:** reemplazo total. Los atributos del catálogo actual (`ecogenicidad`, `tamaño`)
no son los que la plantilla pide. `preservacion` se matchea con "Páncreas conservado"
(la mayoría del corpus). `aspecto_peripancreatico` casi no aparece — **decisión clínica
requerida**: ¿se relaja la regex para inferir (grasa peripancreática normal/alterada)
o se descarta este atributo?

### 3.10. Adrenales (3 clínico / 2 actual)

| Atributo clínico | Catálogo actual | Decisión | Cobertura corpus |
|---|---|---|---:|
| forma | forma | ✅ MANTENER | 90.0% |
| tamaño | tamaño | ✅ MANTENER | 92.2% |
| **arquitectura** | (no existe) | 🆕 **AGREGAR** | 90.4% |

**Cambios:** +1 atributo (`arquitectura`). Corpus usa "arquitectura y tamaño conservado".

### 3.11. Linfonodos (2 clínico / 4 actual) — REEMPLAZO TOTAL

| Atributo clínico | Catálogo actual | Decisión | Cobertura corpus |
|---|---|---|---:|
| **presencia** | (no existe) | 🆕 **AGREGAR** (binario) | 99.4% |
| **compromiso** | (no existe) | 🆕 **AGREGAR** (binario) | 89.7% |
| ~~tamaño~~ | tamaño | ❌ ELIMINAR | 0.4% |
| ~~forma~~ | forma | ❌ ELIMINAR | 4.0% |
| ~~ecogenicidad~~ | ecogenicidad | ❌ ELIMINAR | 17.7% |
| ~~homogeneidad~~ | homogeneidad | ❌ ELIMINAR | 13.6% |

**Cambios:** reemplazo total por modelo binario. Corpus es ~99% "No se observan
linfonodos" / "linfonodos conservados" — el modelo descriptivo es ruido.

### 3.12. Cavidad abdominal (2 clínico / 0 actual) — ÓRGANO NUEVO

| Atributo clínico | Catálogo actual | Decisión | Cobertura corpus |
|---|---|---|---:|
| **liquido_libre** | (no existe) | 🆕 **AGREGAR** | 0% como órgano, 10 órganos lo mencionan en descripción |
| **masas** | (no existe) | 🆕 **AGREGAR** | 0% como órgano |

**Cambios:** órgano completamente nuevo. En RAW no existe como `organo='Cavidad
abdominal'` (0 hallazgos). Las menciones a "líquido libre" aparecen dentro de
descripciones de otros órganos (10 órganos distintos). **Decisión clínica
requerida**: ¿el atributo `liquido_libre` se modela como sub-atributo de cada
hallazgo de órgano (independiente del `organo` principal), o se crea un órgano
virtual "Cavidad abdominal" con `silver_atributos_hallazgo` cruzando FK?

---

## 4. Atributos faltantes en el catálogo actual

| # | Atributo | Órgano clínico | Cobertura corpus |
|---:|---|---|---:|
| 1 | `homogeneidad_contenido` | Vejiga | 79.0% |
| 2 | `lobulacion` | Próstata | 97.6% |
| 3 | `estratificacion_pared` | Estómago | 94.9% |
| 4 | `preservacion` | Páncreas | 97.1% |
| 5 | `aspecto_peripancreatico` | Páncreas | 0.1% ⚠️ |
| 6 | `arquitectura` | Adrenales | 90.4% |
| 7 | `presencia` | Linfonodos (binario) | 99.4% |
| 8 | `compromiso` | Linfonodos (binario) | 89.7% |
| 9 | `liquido_libre` | Cavidad abdominal | 0% como órgano |
| 10 | `masas` | Cavidad abdominal | 0% como órgano |
| 11 | `estratificacion_pared` | Intestino (duodeno/yeyuno) | n/d |
| 12 | `paredes` | Intestino (colon) | n/d |

---

## 5. Atributos sobrantes en el catálogo actual

Atributos del Anexo A que **NO están en la plantilla clínica** y deben eliminarse:

| Atributo actual | Órgano | Razón |
|---|---|---|
| `distension` | Intestino | cobertura 2.5%, corpus no usa |
| `ecogenicidad` | Páncreas | reemplazado por `preservacion` |
| `tamaño` | Páncreas | reemplazado por `preservacion` |
| `tamaño` | Linfonodos | reemplazado por binario |
| `forma` | Linfonodos | reemplazado por binario |
| `ecogenicidad` | Linfonodos | reemplazado por binario |
| `homogeneidad` | Linfonodos | reemplazado por binario |
| `aspecto` | Próstata | fusionar en `forma` + `lobulacion` |
| `tamaño` | Útero | órgano no en plantilla |
| `contenido` | Útero | órgano no en plantilla |
| `grosor_pared` | Útero | órgano no en plantilla |
| `tamaño` | Ovarios | órgano no en plantilla |
| `forma` | Ovarios | órgano no en plantilla |
| `tamaño` | Testículos | órgano no en plantilla |
| `forma` | Testículos | órgano no en plantilla |
| `ecogenicidad` | Testículos | órgano no en plantilla |
| `homogeneidad` | Testículos | órgano no en plantilla |
| `fetos` | Gestación | órgano no en plantilla |
| `prenez` | Gestación | órgano no en plantilla |

**Total a eliminar:** 19 atributos.

**Órganos completos a eliminar del catálogo:** Útero (3), Ovarios (2),
Testículos (4), Gestación (2) — **4 órganos / 11 atributos**.

---

## 6. Fusiones necesarias

| Atributo a eliminar | Atributos destino | Razón |
|---|---|---|
| `Próstata.aspecto` | `Próstata.forma` + `Próstata.lobulacion` | el corpus usa "aspecto ovalado", "aspecto conservado" + "bilobulada" — separar el descriptor de forma del descriptor de lobulación |
| `Intestino.contenido` (genérico) | `Intestino.duodeno_yeyuno.contenido` + `Intestino.colon.contenido` | la plantilla obliga a separar por segmento |
| `Intestino.grosor_pared` (genérico) | `Intestino.duodeno_yeyuno.grosor_pared` + `Intestino.colon.paredes` | idem |

**Total fusiones:** 3.

---

## 7. Renombramientos

| Nombre actual | Nombre clínico propuesto |
|---|---|
| `diferenciacion_cm` | `diferenciacion_corticomedular` |
| `relacion_cm` | `relacion_corticomedular` |

**Razón:** consistencia con nomenclatura clínica. La abreviatura `cm` es interna;
la veterinaria usa siempre el nombre completo.

---

## 8. Atributos binarios (modelado clínico explícito)

Atributos cuyo modelo de valores es esencialmente **presente / ausente** (o
**normal / alterado**). Estos deben modelarse en `silver_atributos` con
`es_binario = TRUE` y `dim_valores_atributo` con cardinalidad 2-3.

| Órgano | Atributo | Valores canónicos propuestos | Cobertura |
|---|---|---|---:|
| Linfonodos | presencia | presente / ausente / no_evaluado | 99.4% |
| Linfonodos | compromiso | comprometido / no_comprometido / conservado | 89.7% |
| Páncreas | preservacion | preservado / alterado / no_evaluado | 97.1% |
| Páncreas | aspecto_peripancreatico | normal / alterado | 0.1% ⚠️ |
| Riñones | compromiso_pelvico | con_compromiso / sin_compromiso / ectasia | 92.1% |
| Cavidad abdominal | liquido_libre | presente / ausente | (decidir modelo) |
| Cavidad abdominal | masas | presente / ausente | (decidir modelo) |

Adicionalmente, el atributo `conservado/a` aparece en el corpus como resumen
(81% Vejiga, 91% Hígado, etc.) y debería modelarse como una **constante global**
`dim_valor_constante = "conservado"` que se asigna cuando la regex matchea
`\bconservad[oa]\b` en contexto de atributo explícito (no como "órgano X
conservado" aislado).

---

## 9. Lateralidad en Riñones (modo UNIFICADO / SEPARADO)

### 9.1. Distribución en corpus

| Lateralidad | n | % |
|---|---:|---:|
| ambos / bilateral | 2.566 | 95.5% |
| izquierdo (con o sin ambos) | 999 | 37.2% |
| derecho (con o sin ambos) | 990 | 36.8% |
| sin lateralidad explícita | 20 | 0.7% |

### 9.2. Modelo de datos propuesto

Agregar columnas a `silver_atributos_hallazgo`:

```sql
ALTER TABLE silver_atributos_hallazgo ADD COLUMN lateralidad VARCHAR(16);
-- Valores: 'izquierdo', 'derecho', 'bilateral', NULL
```

### 9.3. Lógica de extracción

1. **Detectar tokens de lateralidad** en la descripción del hallazgo:
   - `\b(ambos|ambas|bilateral|bi)\b` → `bilateral`
   - `\b(ri[ñn][oó]n\s+izquierd[oa]|izquierd[oa]|izq\.?)\b` → `izquierdo`
   - `\b(ri[ñn][oó]n\s+derech[oa]|derech[oa]|der\.?)\b` → `derecho`
2. **Si solo aparece un lado**: registrar 1 fila en `silver_atributos_hallazgo`
   con `lateralidad = 'izquierdo'` o `'derecho'`.
3. **Si aparecen ambos o ninguno**: registrar 1 fila con `lateralidad = 'bilateral'`.
4. **Si no hay tokens**: registrar 1 fila con `lateralidad = NULL`.

El atributo `silver_hallazgos.id` sigue siendo la FK; `silver_atributos_hallazgo`
se vuelve una tabla con 2.688 (UNIFICADO) o hasta ~5.000 (SEPARADO) filas para Riñones.

---

## 10. Cobertura validada en corpus

### 10.1. Por atributo clínico

Resultado del script `_profile_f3_1_clinical_coverage.py` (regex tentativas sobre
las 27.866 descripciones de hallazgos).

| Órgano clínico | Atributo | match | total | % | Status |
|---|---|---:|---:|---:|---|
| Vejiga | replecion | 2.677 | 2.690 | 99.5% | ✅ |
| Vejiga | contenido | 2.664 | 2.690 | 99.0% | ✅ |
| Vejiga | homogeneidad_contenido | 2.126 | 2.690 | 79.0% | ✅ |
| Vejiga | bordes_internos | 2.564 | 2.690 | 95.3% | ✅ |
| Vejiga | grosor_pared | 2.563 | 2.690 | 95.3% | ✅ |
| Próstata | tamaño | 720 | 737 | 97.7% | ✅ |
| Próstata | lobulacion | 719 | 737 | 97.6% | ✅ |
| Próstata | homogeneidad | 719 | 737 | 97.6% | ✅ |
| Próstata | ecogenicidad | 716 | 737 | 97.2% | ✅ |
| Próstata | forma | 674 | 737 | 91.5% | ✅ |
| Riñones | tamaño | 2.669 | 2.688 | 99.3% | ✅ |
| Riñones | forma | 2.615 | 2.688 | 97.3% | ✅ |
| Riñones | bordes | 2.606 | 2.688 | 96.9% | ✅ |
| Riñones | relacion_corticomedular | 2.572 | 2.688 | 95.7% | ✅ |
| Riñones | diferenciacion_corticomedular | 2.556 | 2.688 | 95.1% | ✅ |
| Riñones | compromiso_pelvico | 2.475 | 2.688 | 92.1% | ✅ |
| Riñones | ecogenicidad_cortical | 1.056 | 2.688 | 39.3% | ⚠️ |
| Bazo | tamaño | 2.642 | 2.684 | 98.4% | ✅ |
| Bazo | margenes | 2.563 | 2.684 | 95.5% | ✅ |
| Bazo | forma | 2.469 | 2.684 | 92.0% | ✅ |
| Bazo | arquitectura | 2.444 | 2.684 | 91.1% | ✅ |
| Estómago | contenido | 2.667 | 2.688 | 99.2% | ✅ |
| Estómago | grosor_pared | 2.624 | 2.688 | 97.6% | ✅ |
| Estómago | distension | 2.621 | 2.688 | 97.5% | ✅ |
| Estómago | estratificacion_pared | 2.552 | 2.688 | 94.9% | ✅ |
| Hígado | tamaño | 2.673 | 2.687 | 99.5% | ✅ |
| Hígado | margenes | 2.662 | 2.687 | 99.1% | ✅ |
| Hígado | ecogenicidad | 2.624 | 2.687 | 97.7% | ✅ |
| Hígado | granulado | 2.575 | 2.687 | 95.8% | ✅ |
| Hígado | patron_vascular | 2.524 | 2.687 | 93.9% | ✅ |
| Hígado | bordes | 2.509 | 2.687 | 93.4% | ✅ |
| Hígado | arquitectura | 1.843 | 2.687 | 68.6% | ✅ |
| Vesícula | contenido | 2.641 | 2.667 | 99.0% | ✅ |
| Vesícula | distension | 2.639 | 2.667 | 99.0% | ✅ |
| Vesícula | grosor_pared | 2.559 | 2.667 | 96.0% | ✅ |
| Vesícula | bordes_internos | 2.543 | 2.667 | 95.4% | ✅ |
| Páncreas | preservacion | 2.611 | 2.688 | 97.1% | ✅ |
| Páncreas | aspecto_peripancreatico | 4 | 2.688 | 0.1% | ❌ |
| Adrenales | tamaño | 2.478 | 2.687 | 92.2% | ✅ |
| Adrenales | arquitectura | 2.430 | 2.687 | 90.4% | ✅ |
| Adrenales | forma | 2.419 | 2.687 | 90.0% | ✅ |
| Linfonodos | presencia | 2.666 | 2.681 | 99.4% | ✅ |
| Linfonodos | compromiso | 2.404 | 2.681 | 89.7% | ✅ |

### 10.2. Por órgano (≥1 atributo matcheado)

| Órgano | match ≥1 | total | % |
|---|---:|---:|---:|
| Vejiga | 2.685 | 2.690 | 99.8% |
| Próstata | 724 | 737 | 98.2% |
| Riñones | 2.679 | 2.688 | 99.7% |
| Bazo | 2.651 | 2.684 | 98.8% |
| Estómago | 2.676 | 2.688 | 99.6% |
| Hígado | 2.677 | 2.687 | 99.6% |
| Vesícula | 2.642 | 2.667 | 99.1% |
| Páncreas | 2.613 | 2.688 | 97.2% |
| Adrenales | 2.502 | 2.687 | 93.1% |
| Linfonodos | 2.667 | 2.681 | 99.5% |

**Cobertura global del catálogo clínico:** **97.6%** sobre 27.866 hallazgos.

### 10.3. Atributos con cobertura insuficiente (decisión clínica requerida)

| Atributo | Cobertura | Recomendación |
|---|---:|---|
| `Riñones.ecogenicidad_cortical` | 39.3% | **Aceptar** — la regex actual es estricta (busca "ecogenicidad cortical" explícito). Relajarla a `\becogenicidad\b` aceptaría ~97% pero perdería la distinción. **Decisión:** mantener estricto y capturar `ecogenicidad` en atributo separado sin sufijo si la clínica lo aprueba. |
| `Páncreas.aspecto_peripancreatico` | 0.1% | **Descartar o inferir** — el corpus nunca menciona "peripancreático". **Decisión:** eliminar atributo o derivarlo de palabras clave vecinas ("grasa", "inflamación pancreática") con NLP más sofisticado. |
| `Cavidad abdominal.liquido_libre` | 0% (sin hallazgos en RAW) | **Crear como atributo libre** sin FK a organo, o agregar como sub-atributo del hallazgo principal. |
| `Cavidad abdominal.masas` | 0% (sin hallazgos en RAW) | idem |

### 10.4. Segmentación de Intestino

Distribución de menciones a segmentos anatómicos en 2.688 hallazgos de Intestino:

| Segmento | n | % |
|---|---:|---:|
| colon | 2.608 | 97.0% |
| duodeno | 2.586 | 96.2% |
| yeyuno | 2.583 | 96.1% |
| yeyunal (forma adj.) | 64 | 2.4% |
| ileon | 49 | 1.8% |
| ciego | 8 | 0.3% |
| recto | 0 | 0.0% |
| (sin segmento explícito) | 50 | 1.9% |

> **Conclusión:** la plantilla clínica `duodeno/yeyuno` se cumple: ambos segmentos
> están presentes en >96% del corpus. `colon` también en 97%. Los demás segmentos
> son residuales.

### 10.5. Lateralidad de Riñones

Distribución de menciones a lateralidad en 2.688 hallazgos de Riñones:

| Lateralidad | n | % |
|---|---:|---:|
| ambos / bilateral | 2.566 | 95.5% |
| izquierdo (con o sin ambos) | 999 | 37.2% |
| derecho (con o sin ambos) | 990 | 36.8% |
| sin lateralidad explícita | 20 | 0.7% |

> **Conclusión:** modo UNIFICADO cubre 95.5% del corpus. Modo SEPARADO requiere
> desdoblar cada hallazgo con `riñón izquierdo` y `riñón derecho` en filas
> individuales de `silver_atributos_hallazgo`.

---

## 11. Propuesta final de catálogo F3

### 11.1. Tabla canónica

30 atributos únicos / 49 pares en 12 órganos:

```
VEJIGA (5)
  - replecion
  - contenido
  - homogeneidad_contenido     [NUEVO]
  - bordes_internos
  - grosor_pared

PRÓSTATA (5)
  - forma                       [RENOMBRADO desde 'aspecto']
  - lobulacion                  [NUEVO]
  - tamaño
  - ecogenicidad
  - homogeneidad

RIÑONES (7, con lateralidad)
  - forma
  - tamaño
  - bordes
  - ecogenicidad_cortical
  - diferenciacion_corticomedular   [RENOMBRADO desde _cm]
  - relacion_corticomedular         [RENOMBRADO desde _cm]
  - compromiso_pelvico

BAZO (4)
  - tamaño
  - forma
  - margenes
  - arquitectura

ESTÓMAGO (4)
  - distension
  - contenido
  - estratificacion_pared      [NUEVO]
  - grosor_pared

HÍGADO (7)
  - tamaño
  - margenes
  - bordes
  - ecogenicidad
  - granulado
  - arquitectura
  - patron_vascular

VESÍCULA (4)
  - distension
  - contenido
  - bordes_internos
  - grosor_pared

INTESTINO (6, organizados por segmento)
  - duodeno_yeyuno.contenido
  - duodeno_yeyuno.grosor_pared
  - duodeno_yeyuno.estratificacion_pared   [NUEVO]
  - peristaltismo (global)
  - colon.contenido                        [NUEVO]
  - colon.paredes                          [NUEVO]

PÁNCREAS (2)
  - preservacion                    [NUEVO, reemplaza ecogenicidad+tamaño]
  - aspecto_peripancreatico         [NUEVO, ⚠️ cobertura 0.1%]

ADRENALES (3)
  - forma
  - tamaño
  - arquitectura                    [NUEVO]

LINFONODOS (2, ambos binarios)    [REEMPLAZA 4 atributos descriptivos]
  - presencia
  - compromiso

CAVIDAD ABDOMINAL (2)             [ÓRGANO NUEVO]
  - liquido_libre
  - masas
```

### 11.2. Eliminados completamente del catálogo

- **Próstata.aspecto** (fusionado en forma + lobulacion)
- **Intestino.distension** (no usado)
- **Estómago.peristaltismo** (movido a Intestino)
- **Páncreas.ecogenicidad, Páncreas.tamaño** (reemplazados)
- **Linfonodos.{tamaño, forma, ecogenicidad, homogeneidad}** (reemplazados)
- **Órganos completos:** Útero, Ovarios, Testículos, Gestación

---

## 12. Cambios al esquema `silver_atributos`

### 12.1. Tabla `dim_atributo`

```sql
CREATE TABLE dim_atributo (
    id              INTEGER PRIMARY KEY,
    nombre          VARCHAR(64) UNIQUE NOT NULL,
    es_binario      BOOLEAN DEFAULT FALSE,
    aplica_a        VARCHAR(16) NOT NULL,   -- 'organo' | 'segmento' | 'cavidad'
    descripcion     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Poblar con los 30 atributos canónicos. Atributos binarios: `presencia`,
`compromiso`, `preservacion`, `aspecto_peripancreatico`, `compromiso_pelvico`,
`liquido_libre`, `masas`.

### 12.2. Tabla `dim_segmento_anatomico`

Nueva tabla para modelar los segmentos de Intestino:

```sql
CREATE TABLE dim_segmento_anatomico (
    id              INTEGER PRIMARY KEY,
    nombre          VARCHAR(64) UNIQUE NOT NULL,  -- 'duodeno_yeyuno', 'colon', etc.
    organo_id       INTEGER REFERENCES dim_organo(id),
    descripcion     TEXT
);
```

### 12.3. Tabla `silver_atributos_hallazgo`

```sql
CREATE TABLE silver_atributos_hallazgo (
    id                  INTEGER PRIMARY KEY,
    hallazgo_id         INTEGER NOT NULL,
    atributo_id         INTEGER NOT NULL REFERENCES dim_atributo(id),
    valor_id            INTEGER REFERENCES dim_valor_atributo(id),
    valor_texto         VARCHAR(255),         -- para valores no canónicos
    segmento_id         INTEGER REFERENCES dim_segmento_anatomico(id),  -- solo Intestino
    lateralidad         VARCHAR(16),          -- solo Riñones: 'izq'/'der'/'bilateral'/NULL
    confianza           DECIMAL(3,2),         -- 0.00-1.00, derivado de longitud de match
    fuente              VARCHAR(16) DEFAULT 'regex',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hallazgo_id, atributo_id, segmento_id, lateralidad)
);
```

### 12.4. Tabla `dim_valor_atributo`

```sql
CREATE TABLE dim_valor_atributo (
    id              INTEGER PRIMARY KEY,
    atributo_id     INTEGER NOT NULL REFERENCES dim_atributo(id),
    valor           VARCHAR(64) NOT NULL,
    sinonimos       TEXT,                       -- 'aumentado,aumentada,aumentados'
    es_binario_true BOOLEAN,                    -- solo si atributo es binario
    orden           INTEGER,
    UNIQUE(atributo_id, valor)
);
```

Cardinalidad estimada: ~150 valores totales (5 por atributo × 30 atributos).

---

## 13. Plan de implementación propuesto

> Este documento **no incluye código**. Solo la ruta de migración.

### Fase F3.0 (siguiente)
- Aplicar cambios al esquema: dim_atributo, dim_segmento_anatomico,
  dim_valor_atributo, silver_atributos_hallazgo con columna `lateralidad`.
- Implementar extractores regex para los 30 atributos canónicos.
- Resolver pregunta clínica pendiente: `Páncreas.aspecto_peripancreatico` (¿mantener
  con regex inferencial o eliminar?).
- Resolver pregunta clínica pendiente: `Cavidad abdominal.liquido_libre` /
  `masas` (¿sub-atributo por hallazgo u órgano virtual?).

### Fase F3.1 (refinamiento)
- Aflojar regex de `Riñones.ecogenicidad_cortical` si la clínica aprueba.
- Validar fusión `aspecto → forma+lobulacion` con muestra clínica.
- Implementar lógica de desdoblamiento UNIFICADO/SEPARADO para Riñones.

### Fase F3.2 (extensión)
- Cavidad abdominal como sub-atributo libre (cross-FK).
- Modelo binario para atributos derivados (`gestacion_activa`, etc.) si la clínica
  lo requiere en el futuro.

---

## 14. Resumen de decisiones pendientes (clínico)

| # | Pregunta | Bloquea |
|---|---|---|
| 1 | ¿`Riñones.ecogenicidad_cortical` se mantiene estricto (39%) o se generaliza (97%)? | F3.0 |
| 2 | ¿`Páncreas.aspecto_peripancreatico` se mantiene (0.1%) o se elimina? | F3.0 |
| 3 | ¿`Cavidad abdominal.liquido_libre` y `masas` se modelan como sub-atributo por hallazgo o como órgano virtual? | F3.0 |
| 4 | ¿`Próstata.aspecto` debe separarse en `forma` + `lobulacion` o mantenerse unificado? | F3.0 |
| 5 | Riñones: ¿desdoblar cada hallazgo SEPARADO en 2 filas (izq/der) o agregar columna `lateralidad`? | F3.0 (esquema) |
| 6 | Intestino: ¿`duodeno_yeyuno` se trata como un solo segmento o se separa en duodeno / yeyuno? | F3.0 |

---

*Generado por `scripts/_profile_f3_1_clinical_coverage.py` (corpus profiling only;
sin escribir en silver.db). Para reproducir:*

```bash
python scripts/_profile_f3_1_clinical_coverage.py
```

*Fuentes:*
- *Primaria:* `docs/F3_1_ATTRIBUTE_DISCOVERY_NLP.md` §C-D (descubrimiento NLP)
- *Secundaria:* `docs/F3_ATTRIBUTE_DISCOVERY.md` §2 (cobertura Anexo A)
- *Terciaria:* plantilla clínica oficial (proporcionada por el usuario en este turno)