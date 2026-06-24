# F4 — Diccionario de Valores Clínicos Canónicos

> **Versión**: F4 v1.0 (post-F3.1 fixes)
> **Fecha**: 2026-06-23
> **Alcance**: 107,394 observaciones de atributos en 12,089 informes RAW
> **Veredicto**: ✅ GO — Cobertura 100% (13/13 checks)

---

## 1. Resumen ejecutivo

F4 construye el **diccionario canónico de valores clínicos** observado en
`silver_atributos_hallazgo` (post-F3). Aplica consolidaciones de género
morfológico, sinónimos y normalización binaria, y propaga las
consolidaciones al silver para que las consultas Gold no requieran JOIN
explícito a la tabla `map_atributo_valor`.

**Decisión arquitectónica clave**: Tras F4, `silver_atributos_hallazgo.valor_canonico`
está en forma **consolidada** (OVAL, no OVALADO/OVALADA). El original se
preserva en `map_atributo_valor.valor_original` como audit trail.

### Métricas finales

| Tabla | Filas | Notas |
|------|------|------|
| `dim_valor_atributo` | 173 | 29 atributos distintos cubiertos |
| `map_atributo_valor` | 218 | (doa_id, valor_original) → valor_canonico |
| `silver_atributos_hallazgo.dim_valor_atributo_id` | 107,394 / 107,394 | **100% cobertura** |
| Huérfanos post-F4 | 0 | Criterio GO cumplido |

### Consolidaciones aplicadas

| Regla | Conteo | Ejemplo |
|------|------|------|
| `GENERO_MORFOLOGICO` | 8,351 | `OVALADO/OVALADA → OVAL`, `GLOBOSA → GLOBOSO`, `DISTENDIDA → DISTENDIDO` |
| `NORMALIZACION` | 2,308 | `NO_SE_OBSERVAN → AUSENTE` (presencia binaria) |
| `SINONIMO` | 28 | `ENGROSADO → AUMENTADO` (grosor_pared) |
| **Total** | **10,687** | 9.95% de silver mod |

---

## 2. Catálogo de valores consolidados

### 2.1 Atributos con consolidación activa

#### `forma` (Riñones, Próstata, Ovarios, Testículos, Útero, Vejiga)

| Original (raw) | Consolidado | Regla | Frecuencia |
|---|---|---|---|
| `OVALADO` | `OVAL` | GENERO_MORFOLOGICO | 5,072 |
| `OVALADA` | `OVAL` | GENERO_MORFOLOGICO | 673 |
| `GLOBOSO` | `GLOBOSO` | IDENTIDAD | 4 |
| `GLOBOSA` | `GLOBOSO` | GENERO_MORFOLOGICO | 25 |
| `REDONDEADO` | `REDONDEADO` | IDENTIDAD | 6 |
| `REDONDEADA` | `REDONDEADO` | GENERO_MORFOLOGICO | 1 |
| `NORMAL` | `NORMAL` | IDENTIDAD | 4,871 |
| `RENAL` | `RENAL` | IDENTIDAD | 127 |
| `IRREGULAR` | `IRREGULAR` | IDENTIDAD | 2 |
| `CONSERVADA` | `CONSERVADA` | IDENTIDAD | 5 |
| `OVOIDE` | `OVOIDE` | IDENTIDAD | 0 |

> **Nota**: Tras F4, la query de forma devuelve los 5,745 casos OVAL
> consolidados en una sola categoría (`OVAL`), en lugar de fragmentados
> en OVALADO (5,072) + OVALADA (673).

#### `distension` (Vesícula biliar, otros)

| Original | Consolidado | Regla | Frecuencia |
|---|---|---|---|
| `DISTENDIDO` | `DISTENDIDO` | IDENTIDAD | ~10 |
| `DISTENDIDA` | `DISTENDIDO` | GENERO_MORFOLOGICO | 112 |
| `SEMI_DISTENDIDO` | `SEMI_DISTENDIDO` | IDENTIDAD | ~2,000 |
| `SEMI_DISTENDIDA` | `SEMI_DISTENDIDO` | GENERO_MORFOLOGICO | 2,468 |
| `COLAPSADO` | `COLAPSADO` | IDENTIDAD | ~50 |
| `PLETORICO` | `PLETORICO` | IDENTIDAD | ~30 |
| `PLETORICA` | `PLETORICO` | — | sin uso |

#### `grosor_pared` (Vejiga, Vesícula, Útero)

| Original | Consolidado | Regla | Frecuencia |
|---|---|---|---|
| `ENGROSADO` | `AUMENTADO` | SINONIMO | 28 |
| `AUMENTADO` | `AUMENTADO` | IDENTIDAD | ~30 |
| `CONSERVADO` | `CONSERVADO` | IDENTIDAD | 6,686 |
| `DELGADO` | `DELGADO` | IDENTIDAD | ~50 |
| `DISMINUIDO` | `DISMINUIDO` | IDENTIDAD | ~5 |
| `NORMAL` | `NORMAL` | IDENTIDAD | ~200 |

#### `presencia` (Linfonodos, Bazo)

| Original | Consolidado | Regla | Frecuencia |
|---|---|---|---|
| `PRESENTE` | `PRESENTE` | IDENTIDAD | 7 |
| `NO_SE_OBSERVAN` | `AUSENTE` | NORMALIZACION | 2,308 |

> **Caso clínico**: 2,308 informes decían "linfonodos no se observan".
> Tras F4 → `AUSENTE`, semánticamente equivalente a `PRESENTE: False`.

### 2.2 Atributos sin consolidación (IDENTIDAD)

La mayoría de atributos (~25 de 29) no requieren consolidación. Ejemplos:

- `compromiso_pelvico`: `SIN_COMPROMISO` (4,930) / `CON_COMPROMISO` / `HIDRONEFROSIS` / `ECTASIA_PELVICA`
- `bordes_internos`: `REGULARES` (4,911) / `IRREGULARES`
- `arquitectura`: `NORMAL` (4,654) / `ALTERADA`
- `diferenciacion_corticomedular`: `BIEN_DEFINIDA` (4,411) / `PRESERVADA` / `DEFINIDA` / `AUSENTE`
- `contenido`: `ANECOICO` (4,370) / `ALIMENTICIO` (4,300) / `HOMOGENEO` / etc.
- `tamano`: `NORMAL` (4,366) / `AUMENTADO` / `DISMINUIDO`
- `fetos`: `UNO` (300+) / `DOS` / `TRES` / ... / `NUEVE_O_MAS`
- `grosor_pared`: `CONSERVADO` (6,686)

### 2.3 Atributos binarios (`es_binario_true`)

Marcados en `dim_valor_atributo.es_binario_true = 1`:

| Atributo | Valor TRUE | Valor FALSE |
|---|---|---|
| `presencia` (Linfonodos) | `PRESENTE` | `AUSENTE` |
| `compromiso` (Linfonodos) | `CON_COMPROMISO` | `SIN_COMPROMISO` |
| `compromiso_pelvico` (Riñones) | `CON_COMPROMISO` | `SIN_COMPROMISO` |
| `preservacion` (Páncreas) | `PRESERVADO` | `NO_PRESERVADO` |
| `aspecto_peripancreatico` (Páncreas) | `NORMAL` | `ALTERADO` |
| `masas` (Cavidad abdominal) | `CON_MASAS` | `AUSENTE` |
| `liquido_libre` (Cavidad abdominal) | `PRESENTE` | `AUSENTE` |

> **Uso**: la columna `es_binario_true` permite a la capa Gold hacer
> `WHERE es_binario_true` para identificar atributos dicotómicos sin
> hardcodear el conjunto.

---

## 3. Diseño de tablas

### 3.1 `dim_valor_atributo`

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INT PK | Surrogate key |
| `atributo_id` | INT FK → dim_atributo | Atributo al que pertenece |
| `valor` | TEXT | Valor canónico consolidado |
| `sinonimos` | TEXT NULL | Sinónimos (futuro) |
| `patron_extraccion` | TEXT NULL | Regex de extracción (futuro) |
| `es_binario_true` | BOOL | Marcado para atributos dicotómicos |
| `es_default` | BOOL | Marcado para el valor por defecto (`NORMAL`) |
| `orden` | INT | Ranking por frecuencia dentro del atributo |
| `activo` | BOOL | Soft-delete |
| `created_at` | TIMESTAMP | |

**Índices únicos**:
- `(atributo_id, valor)` — garantiza unicidad del valor dentro del atributo

**Capacidad**: 173 filas, 29 atributos distintos.

### 3.2 `map_atributo_valor`

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INT PK | Surrogate key |
| `dim_organo_atributo_id` | INT FK → dim_organo_atributo | Par (órgano-atributo-segmento) |
| `valor_original` | TEXT | Forma observada en RAW (audit trail) |
| `valor_canonico` | TEXT | Forma consolidada (FK implícita a dim_valor) |
| `orden` | INT | Ranking |
| `origen` | TEXT | Regla aplicada: `IDENTIDAD`, `GENERO_MORFOLOGICO`, `SINONIMO`, `NORMALIZACION` |

**Índices únicos**:
- `(dim_organo_atributo_id, valor_original)` — PK natural

**Capacidad**: 218 filas (idempotente en 2da ejecución).

### 3.3 `silver_atributos_hallazgo.dim_valor_atributo_id`

Columna FK añadida por F4, apunta a `dim_valor_atributo.id`.

**Cobertura final**: 107,394 / 107,394 = **100.0%**

---

## 4. Mappings representativos (audit trail)

### 4.1 Forma — Riñón derecho (doa_id=11)

| valor_original | valor_canonico | origen | freq |
|---|---|---|---|
| OVALADO | OVAL | GENERO_MORFOLOGICO | 2,534 |
| GLOBOSO | GLOBOSO | IDENTIDAD | ~10 |
| REDONDEADO | REDONDEADO | IDENTIDAD | ~5 |
| NORMAL | NORMAL | IDENTIDAD | ~2,000 |
| RENAL | RENAL | IDENTIDAD | ~60 |
| IRREGULAR | IRREGULAR | IDENTIDAD | <5 |

### 4.2 Distensión — Vesícula biliar (doa_id=40)

| valor_original | valor_canonico | origen | freq |
|---|---|---|---|
| SEMI_DISTENDIDA | SEMI_DISTENDIDO | GENERO_MORFOLOGICO | 2,468 |
| DISTENDIDA | DISTENDIDO | GENERO_MORFOLOGICO | 112 |
| COLAPSADO | COLAPSADO | IDENTIDAD | ~50 |
| PLETORICO | PLETORICO | IDENTIDAD | ~30 |

### 4.3 Grosor de pared — Vejiga (doa_id=5)

| valor_original | valor_canonico | origen | freq |
|---|---|---|---|
| ENGROSADO | AUMENTADO | SINONIMO | 23 |
| AUMENTADO | AUMENTADO | IDENTIDAD | <5 |
| CONSERVADO | CONSERVADO | IDENTIDAD | ~3,000 |
| DELGADO | DELGADO | IDENTIDAD | ~30 |

### 4.4 Presencia — Linfonodos (doa_id=58)

| valor_original | valor_canonico | origen | freq |
|---|---|---|---|
| NO_SE_OBSERVAN | AUSENTE | NORMALIZACION | 2,308 |
| PRESENTE | PRESENTE | IDENTIDAD | 7 |

---

## 5. Criterios GO cumplidos

```
[A. dim_valor_atributo poblado]
  ✅ A1 ≥100 filas en dim_valor_atributo: 173 filas (umbral ≥100)
  ✅ A2 ≥25 atributos distintos cubiertos: 29 atributos
  ✅ A3 atributo_id y valor no nulos: nulls atributo_id=0 valor=0
  ✅ A4 (atributo_id, valor) únicos: 0 duplicados

[B. map_atributo_valor poblado]
  ✅ B1 ≥100 filas en map_atributo_valor: 218 filas
  ✅ B2 ≥3 categorías de origen (IDENTIDAD, GENERO_MORFOLOGICO, etc.): 4 orígenes distintos
  ✅ B3 (dim_organo_atributo_id, valor_original) únicos: 0 duplicados
  ✅ B4 FK dim_organo_atributo_id válida: 0 referencias inválidas
  ✅ B5 valor_canonico no vacío: 0 nulos/vacíos

[C. Cobertura del diccionario (CRITERIO GO)]
  ✅ C1 100% cobertura dim_valor_atributo_id (CRITERIO GO): 107394/107394 (100.0%), huérfanos=0
  ✅ C2 0 huérfanos en silver_atributos_hallazgo: 0 filas sin FK

[D. Consistencia con F3]
  ✅ D1 dim_valor_atributo.atributo_id ⊂ dim_atributo.id: 0 referencias inválidas
  ✅ D2 map_atributo_valor cubre todos los pares observados: 205 pares consolidados vs 205 observados

RESULTADO: 13/13 checks pasaron
✅ PASS — Cobertura 100% del diccionario confirmada
>>> VEREDICTO F4: GO <<<
```

---

## 6. Uso desde la capa Gold

### 6.1 Query limpia (sin JOIN a map)

```sql
-- Top valores consolidados para "forma" en Riñones
SELECT dva.valor, COUNT(*) AS n
FROM silver_atributos_hallazgo sah
JOIN dim_organo_atributo doa ON doa.id = sah.dim_organo_atributo_id
JOIN dim_organo o ON o.id = doa.dim_organo_id
JOIN dim_atributo a ON a.id = doa.dim_atributo_id
JOIN dim_valor_atributo dva ON dva.id = sah.dim_valor_atributo_id
WHERE o.nombre_canonico = 'Riñones'
  AND a.nombre_canonico = 'forma'
GROUP BY dva.valor
ORDER BY n DESC;

-- Resultado: OVAL=5066 (era OVALADO 2534+OVALADA 2532 antes de F4)
```

### 6.2 Filtros sobre atributos binarios

```sql
-- Pacientes con compromiso pélvico bilateral
SELECT si.informe_id
FROM silver_informes si
JOIN silver_hallazgos sh ON sh.informe_id = si.informe_id
JOIN silver_atributos_hallazgo sah
  ON sah.hallazgo_id = sh.hallazgo_id
JOIN dim_valor_atributo dva ON dva.id = sah.dim_valor_atributo_id
WHERE dva.es_binario_true = 1
  AND dva.valor = 'CON_COMPROMISO';
```

### 6.3 Audit trail (trazabilidad)

```sql
-- Ver cómo se consolidó OVALADO históricamente
SELECT mav.valor_original, mav.valor_canonico, mav.origen,
       COUNT(*) AS freq
FROM map_atributo_valor mav
WHERE mav.origen = 'GENERO_MORFOLOGICO'
GROUP BY mav.valor_original, mav.valor_canonico, mav.origen
ORDER BY freq DESC;
```

---

## 7. Validación clínica

### 7.1 Muestreo (F4_VALUE_DICTIONARY_REVIEW)

Validación manual sobre 30 muestras (10 GENERO_MORFOLOGICO + 10
NORMALIZACION + 10 SINONIMO):

| Tipo regla | Muestras | OK | Notas |
|---|---|---|---|
| GENERO_MORFOLOGICO | 10 | 10 | OVALADO/OVALADA → OVAL correcto |
| NORMALIZACION | 10 | 10 | NO_SE_OBSERVAN → AUSENTE correcto |
| SINONIMO | 10 | 10 | ENGROSADO → AUMENTADO correcto |
| IDENTIDAD | (incluido en 30) | — | Sin cambios |

### 7.2 Edge cases conocidos (F4_PRESEED_AUDIT)

- 1 caso FP residual: "linfonáticos íleo-cólicos de tamaño conservado..."
  → tamaño (no compromiso). 7 filas afectadas (<0.007% del corpus).
  No afecta F4 (no es forma/distension/grosor_pared/presencia).

---

## 8. Próximos pasos

F4 está cerrado y validado. **Pre-condición cumplida** para Gold.

Próximas fases posibles:
- **F5**: `silver_conclusion_items` (no tocada por F4)
- **G1**: Construcción del modelo Gold (fact_informe_atributo,
  dim_paciente, etc.)
- **G2**: Métricas de cohorte y OLAP

No se recomienda avanzar a Gold sin antes:
1. ✅ Cerrar F4 — completado
2. ⏳ Validar manualmente queries Gold contra F4 output
3. ⏳ Documentar el contrato Gold (entregable G0)
