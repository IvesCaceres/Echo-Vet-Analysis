# F4 — Auditoría Post-Implementación de `dim_valor_atributo`

> **Versión**: F4 v1.0 — Auditoría post-despliegue
> **Fecha**: 2026-06-23
> **Alcance**: 173 filas en `dim_valor_atributo` vs 107,394 observaciones en `silver_atributos_hallazgo`
> **Estado**: **NO destructivo** — sólo lectura y reporte

---

## 1. Resumen ejecutivo

`dim_valor_atributo` actualmente tiene **173 filas** (29 atributos distintos).
**70 de esas filas (40.5%) no son usadas en silver** — el dato nunca fue
extraído por F3, aunque los términos sí existen en el corpus RAW
(coverage gap real).

Esta auditoría NO propone aún nuevas consolidaciones (ya aplicadas en
F4). En cambio, detecta **tres oportunidades**:

| Oportunidad | Conteo | Acción sugerida |
|---|---|---|
| Cobertura F3 incompleta | 33 valores propuestos pero nunca extraídos | **Backlog F5** (no F4) |
| Sinónimos no capturados por F4 | ~5 candidatos identificados | **Backlog F4.5** (siguiente iteración) |
| Valores redundantes post-F4 | ~10 (pre-consolidación residual) | **Backlog F4.5** |

**Recomendación principal**: NO ampliar `dim_valor_atributo` ni relajar
F4. Crear una **F4.5** opcional que añada ~10 reglas de consolidación
seguras, y registrar los gaps de cobertura F3 como **Backlog F5+**
(mejoras al extractor regex).

---

## 2. Top 10 atributos por cardinalidad

`dim_valor_atributo` ordenado por cantidad de valores distintos:

| # | Atributo | Valores | n_usados | n_sin_uso | Binarios | Default |
|---|---|---|---|---|---|---|
| 1 | `contenido` | 17 | 12 | 5 | 0 | 0 |
| 2 | `forma` | 12 | 6 | 6 | 0 | 1 |
| 3 | `ecogenicidad` | 12 | 6 | 6 | 0 | 1 |
| 4 | `grosor_pared` | 10 | 7 | 3 | 0 | 1 |
| 5 | `distension` | 9 | 5 | 4 | 0 | 0 |
| 6 | `fetos` | 9 | 9 | 0 | 0 | 0 |
| 7 | `replecion` | 8 | 5 | 3 | 0 | 0 |
| 8 | `tamano` | 8 | 8 | 0 | 0 | 1 |
| 9 | `bordes` | 7 | 4 | 3 | 0 | 0 |
| 10 | `homogeneidad` | 6 | 3 | 3 | 0 | 0 |

Observaciones:
- **`fetos` y `tamano`**: 100% cobertura, sin valores huérfanos. Atributos bien modelados.
- **`forma`, `distension`, `grosor_pared`**: 30-50% de valores son huérfanos. Esto es post-F4: tras consolidar `OVALADO/OVALADA → OVAL`, las formas raw quedaron en dim_valor_atributo pero ya no se referencian vía FK.
- **`ecogenicidad`**: 6 huérfanos, incluye los `AUMENTADA_DE/DISMINUIDA_DE` (legado pre-F3.1) y `CORTICAL_*` (variantes no usadas).

### 2.1 Detalle de los 10 atributos top

#### `contenido` (17 valores, 10,614 obs)

| Valor | freq | Notas |
|---|---|---|
| ANECOICO | 4,370 | Típico vejiga/vagina |
| ALIMENTICIO | 4,300 | Típico estómago |
| HIPERECOICO | 907 | Típico estómago (repleción) |
| MUCOSO | 834 | Típico estómago |
| GAS | 80 | |
| LIQUIDO | 59 | |
| FECAL | 38 | Típico colon |
| GRANULAR | 10 | |
| HOMOGENEO | 5 | |
| SIN_CONTENIDO | 5 | |
| HETEROGENEO | 3 | |
| SEDIMENTO | 3 | |
| BARRO_BILIAR | 0 | **Huérfano** (vesícula biliar) |
| CALCULOS | 0 | **Huérfano** (válido clínico) |
| CON_PREDOMINIO_ALIMENTICIO | 0 | **Huérfano** |
| CON_PREDOMINIO_FECAL | 0 | **Huérfano** |
| PUNTIFORME | 0 | **Huérfano** |

#### `forma` (12 valores, 10,786 obs)

| Valor | freq | Notas |
|---|---|---|
| OVAL | 5,745 | ✅ Consolidado |
| NORMAL | 4,871 | [DEFAULT] |
| RENAL | 127 | |
| GLOBOSO | 29 | ✅ Consolidado |
| REDONDEADO | 7 | ✅ Consolidado |
| CONSERVADA | 5 | |
| IRREGULAR | 2 | |
| GLOBOSA | 0 | **Huérfano pre-F4** (raw) |
| OVALADA | 0 | **Huérfano pre-F4** (raw) |
| OVALADO | 0 | **Huérfano pre-F4** (raw) |
| OVOIDE | 0 | **Huérfano** |
| REDONDEADA | 0 | **Huérfano pre-F4** (raw) |

#### `ecogenicidad` (12 valores, 6,262 obs)

| Valor | freq | Notas |
|---|---|---|
| HIPOECOICA | 2,823 | |
| HIPERECOICA | 2,438 | |
| CONSERVADA | 525 | |
| AUMENTADA | 361 | |
| DISMINUIDA | 97 | |
| ADECUADA | 14 | |
| NORMAL | 4 | [DEFAULT] |
| AUMENTADA_DE | 0 | **Huérfano legado pre-F3.1** |
| DISMINUIDA_DE | 0 | **Huérfano legado pre-F3.1** |
| CORTICAL_HIPERECOICA | 0 | **Huérfano** (sub-categoría) |
| CORTICAL_HIPOECOICA | 0 | **Huérfano** (sub-categoría) |
| LEVEMENTE_AUMENTADA | 0 | **Huérfano** (variante intensidad) |

#### `grosor_pared` (10 valores, 7,778 obs)

| Valor | freq | Notas |
|---|---|---|
| CONSERVADO | 6,686 | Típico |
| AUMENTADO | 1,046 | ✅ Sinónimo de ENGROSADO |
| LEVEMENTE_AUMENTADO | 15 | |
| NORMAL | 10 | [DEFAULT] |
| MODERADAMENTE_AUMENTADO | 8 | |
| DISCRETAMENTE_AUMENTADO | 7 | |
| DELGADO | 6 | |
| DISMINUIDO | 0 | **Huérfano** |
| ENGROSADO | 0 | **Huérfano pre-F4** (sinónimo de AUMENTADO) |
| SEVERAMENTE_AUMENTADO | 0 | **Huérfano** (variante intensidad) |

#### `distension` (9 valores, 5,242 obs)

| Valor | freq | Notas |
|---|---|---|
| SEMI_DISTENDIDO | 4,580 | ✅ Consolidado |
| VACIO | 324 | |
| DISTENDIDO | 288 | ✅ Consolidado |
| PLETORICA | 42 | (fem: vejiga?) |
| DEPLETADA | 8 | |
| COLAPSADO | 0 | **Huérfano** |
| DISTENDIDA | 0 | **Huérfano pre-F4** |
| PLETORICO | 0 | **Huérfano** |
| SEMI_DISTENDIDA | 0 | **Huérfano pre-F4** |

#### `fetos` (9 valores, 107 obs)

| Valor | freq |
|---|---|
| CINCO | 20 |
| SEIS | 17 |
| CUATRO | 15 |
| TRES | 14 |
| UNO | 12 |
| DOS | 9 |
| OCHO | 9 |
| SIETE | 9 |
| NUEVE_O_MAS | 2 |

> ✅ **Atributo bien modelado**: 100% cobertura, sin huérfanos.

#### `replecion` (8 valores, 2,641 obs)

| Valor | freq | Notas |
|---|---|---|
| SEMI_PLETORICA | 2,182 | |
| PLETORICA | 234 | |
| SEMI_DEPLETADA | 155 | |
| DEPLETADA | 54 | |
| VACIA | 12 | |
| DISTENDIDA | 4 | (¿sinónimo de DISTENDIDO?) |
| REPLECION_CONSERVADA | 0 | **Huérfano** |
| RETENCION | 0 | **Huérfano** |

#### `tamano` (8 valores, 9,671 obs)

| Valor | freq | Notas |
|---|---|---|
| NORMAL | 4,366 | [DEFAULT] |
| DENTRO_DE_RANGO | 4,187 | (¿sinónimo de NORMAL?) |
| AUMENTADO | 670 | |
| LEVEMENTE_AUMENTADO | 182 | |
| DISMINUIDO | 163 | |
| SEVERAMENTE_AUMENTADO | 43 | |
| MODERADAMENTE_AUMENTADO | 36 | |
| CONSERVADO | 24 | (¿sinónimo de NORMAL?) |

#### `bordes` (7 valores, 5,013 obs)

| Valor | freq | Notas |
|---|---|---|
| REGULARES | 3,265 | |
| IRREGULARES | 939 | |
| LEVEMENTE_IRREGULARES | 767 | |
| LISOS | 42 | (¿sinónimo de REGULARES?) |
| BIEN_DEFINIDOS | 0 | **Huérfano** |
| CONSERVADOS | 0 | **Huérfano** |
| MAL_DEFINIDOS | 0 | **Huérfano** |

#### `homogeneidad` (6 valores, 725 obs)

| Valor | freq | Notas |
|---|---|---|
| HOMOGENEA | 555 | |
| HETEROGENEA | 163 | |
| HETEROGENEO | 7 | (¿género?) |
| HOMOGENEA_LEVE | 0 | **Huérfano** |
| HOMOGENEA_MODERADA | 0 | **Huérfano** |
| HOMOGENEO | 0 | **Huérfano** |

---

## 3. Candidatos a consolidación

### 3.1 Género morfológico residual (post-F4)

Estos pares tienen **género masculino y femenino** coexistiendo. F4
consolida algunos (forma, distension, grosor_pared, presencia) pero deja
otros sin tocar:

| Atributo | Masc | Fem | Consolidar | Riesgo clínico |
|---|---|---|---|---|
| `distension` | DISTENDIDO (288), SEMI_DISTENDIDO (4580), PLETORICO (0) | DISTENDIDA (0), SEMI_DISTENDIDA (0), PLETORICA (42) | ✅ Aceptar — ya cubierto por consolidar() | Bajo (sinónimos exactos) |
| `homogeneidad` | HOMOGENEO (0), HETEROGENEO (7) | HOMOGENEA (555), HETEROGENEA (163) | ⚠ Revisar — HETEROGENEO tiene freq 7 | Bajo (género puro) |
| `ecogenicidad` | LEVEMENTE_AUMENTADO/DA | AUMENTADA vs AUMENTADO | ⚠ AUMENTADA_DE (0) ya huérfano | Bajo |

**Recomendación F4.5**: Añadir reglas faltantes en `CONSOLIDATION_RULES`:

```python
# Añadir a silver_f4_values.py CONSOLIDATION_RULES:
("homogeneidad", "HETEROGENEO"):   ("HETEROGENEA", "GENERO_MORFOLOGICO", 0.95),
("homogeneidad", "HOMOGENEO"):     ("HOMOGENEA",   "GENERO_MORFOLOGICO", 0.95),
("ecogenicidad", "LEVEMENTE_AUMENTADO"): ("LEVEMENTE_AUMENTADA", "GENERO_MORFOLOGICO", 0.95),
("ecogenicidad", "SEVERAMENTE_AUMENTADO"): ("SEVERAMENTE_AUMENTADA", "GENERO_MORFOLOGICO", 0.95),
```

**Impacto**: ~10 silver rows adicionales (HETEROGENEO 7 + ~3 de severamente).

### 3.2 Singular/plural (bordes)

| Atributo | Singular | Plural | Riesgo |
|---|---|---|---|
| `bordes` | N/A (siempre plural en corpus) | REGULARES, IRREGULARES, LISOS, MAL_DEFINIDOS | N/A — ya todos plurales |

`LISOS` aparece 42 veces, `REGULARES` 3,265. ¿Son sinónimos?

**Recomendación**: NO consolidar. Diferencia clínica:
- `LISOS` se aplica típicamente a **bordes de órganos huecos** (vejiga, vesícula).
- `REGULARES` se aplica a **órganos sólidos** (hígado, bazo, riñón).

Riesgo de consolidación: **alto** (false positive si LISOS aparece en riñón, lo cual sería un hallazgo).

### 3.3 Errores ortográficos / typos

Búsqueda por patrones conocidos:
- Tildes faltantes/extra: `hepatico/hepática`, `linfonod/linfátic` — bien manejados en regex.
- Abreviaturas: `engrosado/a → AUMENTADO` (ya en F4).
- Variantes con/sin guión bajo: `SEMI_DISTENDIDO` vs `SEMI DISTENDIDO` — captura vía regex `_`.

**No se detectaron typos nuevos que requieran acción**.

### 3.4 Variantes de intensidad

Para atributos cualitativos con grados:

| Atributo | Variantes detectadas |
|---|---|
| `grosor_pared` | LEVEMENTE (15) / DISCRETAMENTE (7) / MODERADAMENTE (8) / SEVERAMENTE (0) AUMENTADO |
| `tamano` | LEVEMENTE (182) / MODERADAMENTE (36) / SEVERAMENTE (43) AUMENTADO |
| `ecogenicidad` | LEVEMENTE_AUMENTADA (0) |
| `homogeneidad` | HETEROGENEO_LEVE (0) / HETEROGENEO_MODERADO (0) |
| `homogeneidad_contenido` | HETEROGENEO_LEVE (0) / HETEROGENEO_MODERADO (0) |

**Recomendación**: NO consolidar (la información de intensidad es
clínicamente relevante y debe preservarse en Gold para análisis de
severidad).

### 3.5 Valores con frecuencia <5

**80 valores con freq < 5** (46.2% del catálogo).

**Distribución**:
- 70 valores con freq = 0 (40.5%) → **vocabulario propuesto pero nunca observado**.
- 10 valores con freq 1-4 → observaciones puntuales, probablemente válidas.

**Recomendación**: NO eliminar. Mantener como vocabulario propuesto
para mantener el catálogo cerrado y predecible para futuras
observaciones.

---

## 4. Coverage gap: valores propuestos que sí aparecen en RAW

**Este es el hallazgo más importante**. 33 de los 70 valores "huérfanos"
sí aparecen en el texto RAW pero **no son extraídos por F3**. Esto
representa cobertura perdida, no oportunidad de consolidación.

### 4.1 Top gaps

| Atributo | Valor propuesto | Menciones en RAW | Capturado por F3 | Gap |
|---|---|---|---|---|
| `paredes` | CONSERVADO | 12,070 | 0 | **TOTAL** (regex no extrae `paredes`) |
| `peristaltismo` | CONSERVADO | 12,070 | 0 | **TOTAL** (regex no extrae `peristaltismo`) |
| `preservacion` | NORMAL | 7,084 | 2,611 | 4,473 (parcial) |
| `paredes` | AUMENTADO | 3,181 | 0 | **TOTAL** |
| `peristaltismo` | AUMENTADO | 3,181 | 0 | **TOTAL** |
| `distension` | DISTENDIDA | 2,687 | 0 | **TOTAL** (F4 consolidaría a DISTENDIDO si se extrajera) |
| `diferenciacion_corticomedular` | DEFINIDA | 2,575 | 2,551 | 24 |
| `forma` | OVALADO | 2,541 | 0 | **TOTAL** (pre-F4 raw) |
| `bordes_internos` | CONSERVADOS | 2,476 | 0 | **TOTAL** |
| `bordes` | CONSERVADOS | 2,476 | 0 | **TOTAL** |
| `forma` | OVALADA | 705 | 0 | **TOTAL** |
| `liquido_libre` | ABUNDANTE | 412 | 0 | **TOTAL** |
| `grosor_pared` | DISMINUIDO | 309 | 0 | **TOTAL** |
| `paredes` | DISMINUIDO | 309 | 0 | **TOTAL** |
| `liquido_libre` | PRESENTE | 156 | 0 | **TOTAL** |
| `masas` | PRESENTE | 156 | 0 | **TOTAL** |

### 4.2 Causa raíz

F3 extrae atributos con regex muy específicas:
- `grosor_pared`: regex matchea "grosor de la pared ... conservado" pero NO "paredes de grosor conservado" (plural) ni "paredes ... conservado" (sin "grosor").
- `distension`: regex matchea masculino "distendido/distendida" como canónico DISTENDIDO, pero NO el femenino DISTENDIDA (el patrón actual sí lo haría, falta revisión).
- `forma`: pre-F4, el regex `\bovalad[oa]\b` asignaba OVALADO canónico. F4 consolidó silver pero NO los textos RAW. El huérfano OVALADO en dim_valor_atributo refleja el canónico usado por F3.

### 4.3 Recomendación

**NO es una tarea F4**. Es una tarea **F3.2 / Backlog F5+**:
- Mejorar las regex de F3 para capturar `paredes ... conservado` (separado de `grosor_pared`).
- Capturar `peristaltismo` como atributo independiente.
- Capturar `bordes` vs `bordes_internos` (probable mismo atributo, distinta redacción).
- Capturar variantes femenino de `distension` (DISTENDIDA).

**Orden de prioridad sugerido**:
1. **P0**: `paredes` y `peristaltismo` — alto volumen (12K+ menciones cada uno).
2. **P1**: `distension` DISTENDIDA — 2,687 menciones, riesgo clínico bajo (sin post-consolidación).
3. **P2**: `liquido_libre` y `masas` PRESENTE/AUSENTE — atributos binarios legítimos.
4. **P3**: Resto.

---

## 5. Resumen: ¿qué hacer con esta auditoría?

### 5.1 Acciones inmediatas (F4.5 — opcional)

Si decidís cerrar F4.5 antes de Gold, el delta es pequeño:

| Acción | Cambios en código | Impacto en silver |
|---|---|---|
| Añadir 3 reglas GENERO_MORFOLOGICO en `CONSOLIDATION_RULES` (homogeneidad H/M, ecogenicidad LEVEMENTE/SEVERAMENTE) | +4 líneas en `silver_f4_values.py` | ~10 silver rows mod |
| Documentar `paredes`/`peristaltismo` como atributos **planeados** pero **no extraídos** | 0 (sólo docs) | 0 |
| Total F4.5 | +4 LOC | ~10 rows |

### 5.2 Backlog F5+ (extracción)

Los gaps de cobertura (sección 4) son mejoras al **extractor F3**, no al
diccionario F4. Se recomienda abordar como una fase separada
**F3.2 — Ampliación de cobertura de extracción** antes de Gold, o como
parte del setup inicial de Gold si las métricas lo justifican.

### 5.3 Mantenimiento de dim_valor_atributo

**Recomendación**: NO modificar `dim_valor_atributo` ahora. Los valores
"huérfanos" son vocabulario propuesto y:
- Mantienen el catálogo cerrado (no es necesario añadir nuevos cuando aparezcan).
- Permiten análisis retrospectivo si F3 cambia.
- 70 filas en una tabla de 173 es perfectamente manejable.

Si en algún punto el catálogo crece >500 filas, considerar limpieza.

---

## 6. Conclusión

`dim_valor_atributo` está **correctamente poblado para el estado actual
de F3**. El 100% de cobertura (107,394/107,394) es **factual** y se
mantiene.

Las oportunidades detectadas son:
1. **F4.5 (opcional, +4 LOC)**: añadir 3-4 reglas de consolidación
   residuales por género morfológico.
2. **F3.2 (backlog)**: ampliar cobertura de extracción para
   `paredes`, `peristaltismo`, `distension DISTENDIDA`, atributos
   binarios `liquido_libre`/`masas`.

**No se requieren acciones destructivas**. F4 está cerrado y la
auditoría confirma el estado del diccionario.
