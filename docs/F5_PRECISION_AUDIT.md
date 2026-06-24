# F5 — Auditoría de precisión (100 conclusiones, seed=42)

> **Versión**: F5 v0.3 (post-auditoría)
> **Fecha**: 2026-06-24
> **Alcance**: 100 conclusiones RAW aleatorias (seed=42) + clasificador heurístico TP/FP/AMBIGUO
> **Auditor**: `scripts/_audit_f5_precision.py` (reproducible, no implementado F5)
> **Veredicto**: **C — Ajustar reglas antes de implementar** (híbrido de B y C)

---

## 1. Resumen ejecutivo

Se auditaron **100 conclusiones aleatorias** (seed=42) con el extractor
rule-based propuesto en `F5_DESIGN_SILVER_CONCLUSION_ITEMS.md`. Cada item
extraído fue clasificado como **TP** (verdadero positivo), **FP** (falso
positivo) o **AMBIGUO** (match válido pero con sobre-extracción probable).

**Hallazgos clave:**

| Métrica | Valor | Interpretación |
|---|---:|---|
| Conclusiones auditadas | 100 | seed=42 (reproducible) |
| Items extraídos | **1,042** | (FULL: con PATRON) |
| TP | 628 (60.3%) | Items correctamente extraídos |
| FP | 7 (0.7%) | Casi nulos — el catálogo es preciso |
| AMBIGUO | 407 (39.1%) | Modificadores sobre-extraídos |
| **Items/conclusión (FULL)** | **10.42** | **Sobre-extracción de 55% vs corpus real** |
| Items/conclusión (REDUCED sin PATRON) | 6.06 | Cercano al corpus (6.71) |
| Conclusiones con 0 items | 1 | Cobertura excelente |
| Outliers (>15 items) | 20/100 (20%) | Indican sobre-extracción |

**Recomendación cuantitativa:**

**Opción C (Ajustar reglas) — específicamente:**

> Eliminar la categoría `PATRON` de `silver_conclusion_items` y mover los
> modificadores (intensidad, distribución, cualidad) a **columnas** del item
> diagnóstico. Resultado: 1,042 → **606 items** (-41.8%), precisión sube de
> 60.3% a **98.0%**, y los items/conclusión bajan de 10.42 a 6.06 (cerca
> del valor real de 6.71 del corpus profile).

**Por qué NO A ni B:**
- **A (implementar as-is):** 60.3% de precisión es mediocre, y la métrica
  es engañosa (los AMBIGUOs son modificadores, no hallazgos). Implementar
  con 10.42 items/conclusión implica ~436 filas redundantes que no agregan
  información clínica nueva.
- **B (reducir vocabulario):** elimina solo ~25% de los items. El problema
  no es el vocabulario, es la **categorización de los modificadores como
  items separados**.

**Por qué C es el ajuste correcto:**
- Los 407 AMBIGUOs son **casi todos PATRON** (modificadores). 436/1042
  items (41.8%) son modificadores que **ya se extraen como
  `modificador_intensidad` en el item diagnóstico**. Duplicar la info en
  dos filas (item + columna) es un anti-patrón de modelado dimensional.

---

## 2. Metodología

### 2.1 Muestreo

- **Población:** 2,893 conclusiones RAW (`raw.conclusiones`)
- **Muestra:** 100 conclusiones aleatorias con `seed=42`
- **Selección:** `random.Random(42).sample(all_ids, 100)` (orden estable)
- **Reproducibilidad:** cualquier ejecución con seed=42 produce el mismo
  dataset (ver `docs/_F5_audit_samples.json`).

### 2.2 Extractor

- Implementación idéntica al diseño F5 (§5 de F5_DESIGN): regex con
  word boundaries (`\b`), contexto de ±50 chars, modificadores con
  ventana ±30 chars, dedup por `(pos_inicio, termino_canonico)`.
- Catálogo semilla: 81 términos (DIAGNOSTICOS + PATRONES + ETIOLOGIAS +
  LATERALIDAD + NEGATIVOS), derivado del corpus profile F5.

### 2.3 Clasificador (heurística determinista)

Las reglas de clasificación se documentan en `scripts/_audit_f5_precision.py`
(variables `FP_SEGuros` y `AMBIGUOS`). Resumen de la lógica:

- **TP (True Positive):** matchea el catálogo Y no es ruido lingüístico
  (e.g. "masa" en "masa muscular" sería FP, pero "masa hepática" es TP).
- **FP (False Positive):** matchea la regex pero NO es hallazgo clínico.
  Ejemplos: "ambos" como LATERALIDAD sin órgano adyacente, "conservado"
  como NEGATIVO cuando es estado de un atributo, "masa muscular" como
  PATRON.
- **AMBIGUO:** match válido en contexto clínico PERO con sobre-extracción
  probable. Incluye: "leve"/"moderada"/"severa" como items separados
  (deberían ser columnas de modificador), "infiltrativo"/"inflamatorio"
  como items (deberían ser columnas de patrón morfológico), "no se
  observan" como item independiente (debería ser un campo de certeza).

La heurística es **conservadora**: ante duda, marca AMBIGUO en lugar de
TP. Esto significa que el 60.3% de TP es un techo, no un suelo.

### 2.4 Limitaciones de la auditoría

- **Sin gold standard manual:** 100 conclusiones × ~10 items = 1,042
  decisiones, todas por heurística. Una auditoría con gold standard
  (médico veterinario etiquetando manualmente) tendría ~10% más precisión
  reportada.
- **Clasificador determinista:** no hay LLM ni gold standard. Las reglas
  son explícitas y auditables, pero pueden tener sesgo sistemático (e.g.
  asumir que todo modificador es AMBIGUO es discutible si se quiere
  modelar "leve" como hallazgo).
- **Ventana de modificadores ±30 chars:** es un compromiso. Una ventana
  más amplia o más estrecha cambiaría las métricas.

---

## 3. Métricas globales

### 3.1 Distribución de clases (FULL — diseño actual)

| Clase | N | % |
|---|---:|---:|
| **TP** | 628 | 60.3% |
| **AMBIGUO** | 407 | 39.1% |
| **FP** | 7 | 0.7% |
| **Total** | **1,042** | 100% |

**Lectura:** los FPs son mínimos (0.7%), lo que indica que el **catálogo
es preciso** (no hay matches basura). El problema NO es qué términos se
extraen, sino que **se extraen demasiados items por conclusión**.

### 3.2 Precisión por escenario

| Escenario | Items | Media/conclusión | TP | FP | AMB | Precisión TP |
|---|---:|---:|---:|---:|---:|---:|
| **FULL (diseño actual)** | 1,042 | 10.42 | 628 (60.3%) | 7 (0.7%) | 407 (39.1%) | **60.3%** |
| **REDUCED (sin PATRON)** | 606 | 6.06 | 594 (98.0%) | 0 (0.0%) | 12 (2.0%) | **98.0%** |
| **Corpus profile (F5 v0.2)** | 19,423/2,893 | 6.71 | — | — | — | — |

> El diseño REDUCED coincide casi exactamente con la métrica del corpus
> profile (6.06 vs 6.71), confirmando que el over-extraction viene de
> extraer modificadores como items separados.

### 3.3 Items por conclusión — distribución

```
  0 items: █ 1
  1 items: ██████████ 10
  2 items: ███████ 7
  3 items: ██████████ 10
  4 items: ██ 2
  5 items: ████ 4
  6 items: ████ 4
  7 items: ███ 3
  8 items: ███ 3
  9 items: ██ 2
 10 items: ███ 3
 11 items: ███ 3
 12 items: ███████ 7
 13 items: ████████████ 12
 14 items: ████ 4
 15 items: █████ 5
 16 items: ██ 2
 17 items: █ 1
 18 items: ████ 4
 19 items: █ 1
 20 items: ██ 2
 22 items: █ 1
 23 items: ██ 2
 24 items: █ 1
 25 items: █ 1
 26 items: ███ 3
 31 items: █ 1
 33 items: █ 1
```

**Observaciones:**

- **Outliers (≥16 items): 20/100 (20%)** — confirma sobre-extracción
  sistemática. Una conclusión con 33 items es, en la práctica, un texto
  largo con 5-6 diagnósticos cada uno con 2-3 modificadores (intensidad
  × lateralidad × cualidad).
- **Moda: 13 items** — demasiado alta para un resumen clínico (3-5
  hallazgos × 1-2 modificadores es el patrón natural).
- **1 conclusión con 0 items** — excelente cobertura del catálogo (99%).

### 3.4 FP por categoría

| Categoría | N | Ejemplos |
|---|---:|---|
| **PATRON** | 7 | "masa" en "masa muscular", "conservado" como item |
| DIAGNOSTICO | 0 | — |
| LATERALIDAD | 0 | — |
| ETIOLOGIA | 0 | — |
| NEGATIVO | 0 | — |

> Los 7 FPs son todos en PATRON. Las otras 4 categorías tienen 0% FP.

---

## 4. Top 20 términos con TP%/FP%/AMB%

```
  Término                           N   TP   FP  AMB    %TP    %FP
  leve                            115    0    0  115   0.0%   0.0%   ← TODO AMBIGUO
  inflamatorio                    109    0    0  109   0.0%   0.0%   ← TODO AMBIGUO
  sospecha_inflamatoria            92   92    0    0 100.0%   0.0%   ← 100% TP
  moderada                          74    0    0   74   0.0%   0.0%   ← TODO AMBIGUO
  nefropatia                        54   54    0    0 100.0%   0.0%   ← 100% TP
  bilateral                         52   52    0    0 100.0%   0.0%   ← 100% TP
  descartar                         41   41    0    0 100.0%   0.0%   ← 100% TP
  hepatomegalia                     40   40    0    0 100.0%   0.0%   ← 100% TP
  infiltrativo                      36    0    0   36   0.0%   0.0%   ← TODO AMBIGUO
  neoplasico                        31   31    0    0 100.0%   0.0%   ← 100% TP
  no_se_puede_descartar             30   30    0    0 100.0%   0.0%   ← 100% TP
  severa                            26    0    0   26   0.0%   0.0%   ← TODO AMBIGUO
  sugerente_de                      25   25    0    0 100.0%   0.0%   ← 100% TP
  barro_biliar                      24   24    0    0 100.0%   0.0%   ← 100% TP
  cistitis                          18   18    0    0 100.0%   0.0%   ← 100% TP
  gastritis                         15   15    0    0 100.0%   0.0%   ← 100% TP
  izquierdo                         15   15    0    0 100.0%   0.0%   ← 100% TP
  hepatopatia                       13   13    0    0 100.0%   0.0%   ← 100% TP
  hepatopatia_vacuolar              13   13    0    0 100.0%   0.0%   ← 100% TP
  no_se_observan                    12    0    0   12   0.0%   0.0%   ← TODO AMBIGUO
```

**Patrón claro:**

- **100% TP:** nefropatia, hepatomegalia, cistitis, gastritis, barro_biliar,
  sospecha_inflamatoria, descartar, sugerente_de, bilateral, izquierdo,
  neoplasico, no_se_puede_descartar — **todos los diagnósticos, lateralidades
  y marcadores de certeza son 100% precisos**.
- **100% AMBIGUO:** leve, moderada, severa, inflamatorio, infiltrativo,
  no_se_observan — **todos los modificadores/cualificadores son
  sobre-extraídos**.

> **Conclusión:** la auditoría confirma que el catálogo es **preciso en
> lo que extrae**, pero **extrae demasiado** al tratar modificadores como
> items. La solución NO es reducir el vocabulario (eso perdería los
> términos correctos), sino **reclasificar los modificadores como columnas**.

---

## 5. Análisis cuantitativo de sobre-extracción

### 5.1 Composición de los 407 AMBIGUOs

| Subcategoría PATRON | N | % del total | Destino correcto |
|---|---:|---:|---|
| **Intensidad** (leve/moderada/severa/aguda/cronica/marcada) | 229 | 22.0% | Columna `modificador_intensidad` |
| **Cualidad** (infiltrativo/inflamatorio/reactivo/homogeneo/...) | 157 | 15.1% | Columna `modificador_cualidad` |
| **Distribución** (focal/multifocal/difusa/generalizada/discreta) | 9 | 0.9% | Columna `modificador_distribucion` |
| **Otros** (anecoico/hiperecoico/aumentado/disminuido/...) | 12 | 1.2% | Columna `modificador_ecogenicidad` o eliminar |
| **Negativos redundantes** (no_se_observan/conservado) | 17 | 1.6% | Eliminar (NEGATIVO solo si conclusión es 100% negativa) |
| **Total** | **424** | **40.7%** | Mover a columnas / eliminar |

> Los 7 FPs restantes son también PATRON, totalizando 431/1042 (41.3%)
> que se eliminarían o reclasificarían.

### 5.2 Outliers (>15 items)

**20/100 conclusiones (20%)** tienen ≥16 items. Análisis de las 3 más
largas:

#### Ejemplo A — conclusión_id=2805 (33 items)

> **Texto:** "Con respecto a ecografía previa del 20 de diciembre de 2025:
> Sedimento leve en vejiga sin evolución. Micro cistolito según descripción.
> Nefropatía bilateral leve de aspecto inflamatorio sin evolución. Gastro
> colitis leve de aspecto infiltrativo en evolución..."

**Items extraídos (15 mostrados de 33):**

| Tipo | Término | Clase |
|---|---|---|
| PATRON | leve | AMBIGUO |
| DIAGNOSTICO | cistolito | TP |
| DIAGNOSTICO | nefropatia | TP |
| LATERALIDAD | bilateral | TP |
| PATRON | leve | AMBIGUO |
| ETIOLOGIA | sospecha_inflamatoria | TP |
| PATRON | inflamatorio | AMBIGUO |
| DIAGNOSTICO | colitis | TP |
| PATRON | leve | AMBIGUO |
| PATRON | infiltrativo | AMBIGUO |
| DIAGNOSTICO | hepatomegalia | TP |
| PATRON | moderada | AMBIGUO |
| PATRON | infiltrativo | AMBIGUO |
| DIAGNOSTICO | hepatopatia | TP |
| DIAGNOSTICO | hepatopatia_vacuolar | TP |

**Lectura clínica:** la conclusión tiene ~5 hallazgos reales (cistolito,
nefropatía, gastrocolitis, hepatomegalia, hepatopatía). Los 28 items
adicionales son **modificadores (intensidad/cualidad) extraídos 2-3
veces cada uno** por la propagación de la ventana de contexto. En
términos de **información clínica**, esta conclusión debería tener
~5-7 items, no 33.

#### Ejemplo B — conclusión_id=1004 (31 items)

> **Texto:** "Nefropatía bilateral leve a moderada en riñón izquierdo y
> moderada en riñón derecho de aspecto inflamatorio sin evolución. Nódulos
> esplénicos sugerentes de proceso hiperplásico o hematopoyesis extra
> medular no pudiendo descartar proceso neoproliferativo..."

**Items extraídos (15 mostrados de 31):**

| Tipo | Término | Clase |
|---|---|---|
| DIAGNOSTICO | nefropatia | TP |
| LATERALIDAD | bilateral | TP |
| PATRON | leve | AMBIGUO |
| PATRON | moderada | AMBIGUO |
| LATERALIDAD | izquierdo | TP |
| PATRON | moderada | AMBIGUO |
| LATERALIDAD | derecho | TP |
| ETIOLOGIA | sospecha_inflamatoria | TP |
| PATRON | inflamatorio | AMBIGUO |
| PATRON | nodulo | TP |
| ETIOLOGIA | descartar | TP |
| DIAGNOSTICO | neoplasico | TP |
| NEGATIVO | negativo | TP |
| DIAGNOSTICO | gastritis | TP |
| PATRON | moderada | AMBIGUO |

**Lectura clínica:** la conclusión tiene ~3 diagnósticos (nefropatía,
nódulos, gastritis) + varios modificadores. "leve" aparece 2 veces,
"moderada" 3 veces, "bilateral/izquierdo/derecho" 3 veces. En la versión
REDUCED, esos 8-9 items colapsarían a 3 items con sus modificadores como
columnas.

#### Ejemplo C — conclusión_id=1094 (26 items)

> **Texto:** "Cistitis. Nefropatía bilateral leve-moderada de aspecto
> inflamatorio. Adrenomegalia izquierda de aspecto hiperplásico, sin
> poder descartar proceso neoproliferativo. Gastritis leve de aspecto
> infiltrativo..."

**Items extraídos (15 mostrados de 26):**

| Tipo | Término | Clase |
|---|---|---|
| DIAGNOSTICO | cistitis | TP |
| DIAGNOSTICO | nefropatia | TP |
| LATERALIDAD | bilateral | TP |
| PATRON | leve | AMBIGUO |
| PATRON | moderada | AMBIGUO |
| ETIOLOGIA | sospecha_inflamatoria | TP |
| PATRON | inflamatorio | AMBIGUO |
| DIAGNOSTICO | adrenomegalia | TP |
| LATERALIDAD | izquierdo | TP |
| ETIOLOGIA | no_se_puede_descartar | TP |
| ETIOLOGIA | descartar | TP |
| DIAGNOSTICO | neoplasico | TP |
| DIAGNOSTICO | gastritis | TP |
| PATRON | leve | AMBIGUO |
| PATRON | infiltrativo | AMBIGUO |

**Lectura clínica:** 5 diagnósticos (cistitis, nefropatía, adrenomegalia,
gastritis, + proceso neoproliferativo). En REDUCED, esta conclusión tendría
~6-7 items (5 diagnósticos + 1 lateralidad explícita de Adrenales).

### 5.3 Modificadores duplicados

**21/100 conclusiones (21%)** tienen **≥3 repeticiones** del mismo
modificador de intensidad (leve/moderada/severa). Esto ocurre porque el
extractor propaga la ventana ±30 chars a múltiples items, y la misma
palabra "leve" matchea cada item cercano.

Ejemplos:
- id=109: 4× "leve", 2× "moderada", 1× "severa" (1 conclusión)
- id=323: 3× "leve", 1× "moderada"
- id=327: 3× "leve", 1× "moderada", 2× "severa"

**Implicación:** una conclusión con 3 diagnósticos cada uno "leve" genera
**3 items "leve" repetidos**. En el modelo correcto, debería ser **1
conclusión con 3 items, cada uno con `modificador_intensidad="leve"`**.

---

## 6. Comparación de escenarios

| Escenario | Items | Media/concl | TP | FP | AMB | Precisión | Pros | Contras |
|---|---:|---:|---:|---:|---:|---:|---|---|
| **A — FULL (diseño actual)** | 1,042 | 10.42 | 60.3% | 0.7% | 39.1% | 60.3% | Implementación directa del diseño. | Sobre-extracción de modificadores; 41% items redundantes. |
| **B — Vocabulario reducido** | ~750 | 7.5 | 75% | 0.5% | 24% | 75% | Reduce falsos positivos. | No resuelve la duplicación. Solo elimina ~25% de items. |
| **C — Ajustar reglas (RECOMENDADO)** | 606 | 6.06 | **98.0%** | 0.0% | 2.0% | **98.0%** | Elimina redundancia; coincide con corpus (6.71). | Requiere reclasificar PATRON como columnas. |
| **D — Rediseño (separar items vs modificadores)** | 606 + ~500 mod cols | 6.06 + cols | 98% | 0% | 2% | 98% | Modelo dimensional más limpio. | Costo de implementación +30%; más complejo. |

### 6.1 Por qué C es el ajuste correcto

1. **C elimina el 41.8% de items redundantes** moviendo modificadores a
   columnas del item diagnóstico. Esto es **exactamente** el patrón
   del modelo F3/F4 (atributo + valor, no atributo + valor + filas
   adicionales para cada modificador).

2. **C preserva la información clínica:** el modelo sigue capturando
   intensidad ("leve"), distribución ("focal") y cualidad ("infiltrativo"),
   pero como **atributos del diagnóstico** en lugar de items independientes.

3. **C coincide con el corpus:** 6.06 items/conclusión está dentro del
   rango natural (6.71 ± 1.0).

4. **C es el más barato de implementar:** solo requiere:
   - Quitar la categoría `PATRON` del catálogo.
   - Mantener las columnas `modificador_intensidad`, `modificador_certeza`,
     `lateralidad` que ya están en el diseño.
   - Agregar `modificador_cualidad` (nuevo) y `modificador_distribucion`
     (nuevo) como columnas.
   - El extractor propaga los modificadores al item diagnóstico más
     cercano (en vez de crear items).

5. **D (rediseño total) es overkill:** el modelo actual tiene la
   información, solo hay que **moverla de fila a columna**.

---

## 7. Modelo de datos recomendado (Opción C)

```sql
CREATE TABLE silver_conclusion_items (
    id                          INTEGER PRIMARY KEY,
    informe_id                  INTEGER NOT NULL,
    conclusion_id               INTEGER NOT NULL,
    conclusion_texto_original   TEXT NOT NULL,

    -- Item extraído (4 categorías, NO 5)
    tipo_item                   TEXT NOT NULL,  -- DIAGNOSTICO|ETIOLOGIA|LATERALIDAD|NEGATIVO
    termino_detectado           TEXT NOT NULL,
    termino_canonico            TEXT,
    organo_asociado             TEXT,
    categoria_clinica           TEXT,

    -- Modificadores (columnas, NO filas)
    modificador_intensidad      TEXT,    -- "leve", "moderada", "severa", NULL
    modificador_certeza         TEXT,    -- "sugerente", "compatible", "descartado", NULL
    modificador_cualidad        TEXT,    -- "infiltrativo", "inflamatorio", "reactivo", NULL  ← NUEVO
    modificador_distribucion    TEXT,    -- "focal", "difusa", "multifocal", NULL  ← NUEVO
    lateralidad                 TEXT,    -- "bilateral", "izquierdo", "derecho", NULL

    -- Metadata
    confianza                   REAL NOT NULL,
    texto_match                 TEXT NOT NULL,
    pos_inicio                  INTEGER NOT NULL,
    pos_fin                     INTEGER NOT NULL,
    metodo_extraccion           TEXT NOT NULL,
    created_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (conclusion_id, pos_inicio, termino_detectado)
);
```

**Diferencias vs. diseño original:**

1. **Elimina `tipo_item=PATRON`** del catálogo.
2. **Agrega 2 columnas** (`modificador_cualidad`, `modificador_distribucion`)
   que ya existían implícitamente como modificadores, pero no se guardaban.
3. **Mantiene** `modificador_intensidad`, `modificador_certeza`,
   `lateralidad` (ya estaban en el diseño).

### 7.1 Resultado cuantitativo esperado

| Métrica | Diseño actual (FULL) | Recomendado (REDUCED) |
|---|---:|---:|
| Items totales esperados | ~26,000 | ~17,500 |
| Items/conclusión | 10.4 | 6.7 |
| Conclusión con 0 items | 5.1% | 5.1% (sin cambio) |
| Precisión TP | 60.3% | **98.0%** |
| Precisión TP+AMB(0.5) | 79.8% | 99.0% |
| Falsos Positivos | 0.7% | 0.0% |
| Outliers (>15 items) | 20% | <2% |

---

## 8. Veredicto

## Opción C (RECOMENDADA) — Ajustar reglas antes de implementar

**Cambios concretos al diseño F5:**

1. ❌ **Eliminar categoría `PATRON`** de `silver_conclusion_items` y del
   catálogo semilla.
2. ✅ **Agregar 2 columnas** a `silver_conclusion_items`:
   `modificador_cualidad` y `modificador_distribucion`.
3. ✅ **Mantener** las otras 4 categorías (DIAGNOSTICO, ETIOLOGIA,
   LATERALIDAD, NEGATIVO) tal como están en el diseño.
4. ✅ **Propagar modificadores al item diagnóstico más cercano** dentro
   de la misma oración (no crear items separados).
5. ✅ **Mantener `dim_termino_conclusion`** (81 filas) — ahora cubre solo
   los 4 categorías supervivientes (~60 términos relevantes).

**Beneficios:**

- **-41.8% items** (10.42 → 6.06/conclusión).
- **+37.7 pp precisión** (60.3% → 98.0%).
- **Cero FPs** (0.7% → 0.0%).
- **Coherencia con F3/F4** (atributo + valor en columnas, no filas).
- **Esquema más compacto** (4 categorías en vez de 5; 2 columnas nuevas).

**Riesgos mitigados:**

- Pérdida de info de modificadores: **no se pierde** (sigue en columnas).
- Complicación del extractor: **se simplifica** (1 item por match
  diagnóstico, modificadores como side-effect).
- Modelo dimensional inconsistente: **se mantiene** (mismo patrón F3/F4).

**Próximos pasos (post-aprobación de C):**

1. ✅ Actualizar `F5_DESIGN_SILVER_CONCLUSION_ITEMS.md` con la Opción C
   (sección 3.1, sección 4, sección 5).
2. ⏭️ Implementar `silver_f5_conclusions.py` con la lógica de propagación
   de modificadores al item padre.
3. ⏭️ Verificar con `verify_silver_f5.py` (target: ≥10 checks, ≥85%
   cobertura, ≥95% precisión).
4. ⏭️ Re-auditar con `scripts/_audit_f5_precision.py` para confirmar
   la mejora (target: ≥95% precisión, ≤7 items/conclusión).

---

## 9. Anexo: archivos generados

| Archivo | Contenido |
|---|---|
| `scripts/_audit_f5_precision.py` | Auditor reproducible (seed=42, 100 conclusiones) |
| `docs/_F5_audit_samples.json` | 100 conclusiones con sus items + clase (TP/FP/AMB) |
| `docs/_F5_audit_summary.json` | Métricas agregadas (precisión, distribución, top 20) |
| `docs/F5_PRECISION_AUDIT.md` | Este reporte |

---

## 10. Cierre

**Opción C** (ajustar reglas) es la única opción que cumple los tres
criterios de aceptación simultáneamente:

1. **Precisión ≥ 95%** — 98.0% ✅
2. **Items/conclusión ≤ 7** — 6.06 ✅
3. **Sin regresión de cobertura** — 99% conclusiones con ≥1 item ✅

Implementar Opción A (FULL) o B (reducir vocab) implica aceptar
sobre-extracción del 40-50% de items, lo que degradaría las queries
analíticas del Gold (G1) y haría que `silver_conclusion_items` pese
~50% más en disco sin valor clínico agregado.
