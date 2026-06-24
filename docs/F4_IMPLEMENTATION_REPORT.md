# F4 — Reporte de Implementación

> **Versión**: F4 v1.0
> **Fecha**: 2026-06-23
> **Fase**: Silver → Gold Gate
> **Veredicto**: ✅ **GO** — Cobertura 100% (13/13 checks)

---

## 1. Resumen ejecutivo

F4 implementa el **diccionario canónico de valores clínicos** que sirve como
puente entre la capa Silver y la capa Gold. Aplica tres tipos de
consolidaciones (género morfológico, sinónimos, normalización binaria) a
las 107,394 observaciones de atributos clínicos extraídos por F3, y
materializa el resultado como FK en `silver_atributos_hallazgo`.

**Resultado clave**:
- 10,687 observaciones consolidadas (9.95% del corpus)
- 100% cobertura del diccionario (criterio GO cumplido)
- 13/13 checks automatizados en verde
- Idempotencia verificada (2da ejecución es no-op efectiva)

---

## 2. Entregables

| # | Entregable | Ubicación |
|---|---|---|
| 1 | Módulo F4 | `src/informes_vet/silver_f4_values.py` |
| 2 | CLI F4 integrado | `scripts/build_silver.py --phase f4` |
| 3 | Verificación automatizada | `scripts/verify_silver_f4.py` |
| 4 | Documentación del diccionario | `docs/F4_VALUE_DICTIONARY.md` |
| 5 | Pre-seed audit | `docs/F4_PRESEED_AUDIT.md` |
| 6 | Reporte de revisión clínica | `docs/F4_VALUE_DICTIONARY_REVIEW.md` |
| 7 | **Este reporte** | `docs/F4_IMPLEMENTATION_REPORT.md` |

---

## 3. Cambios respecto al plan original

### 3.1 Hallazgo crítico: FK apuntaba a forma raw (no consolidada)

**Síntoma**: Tras la primera ejecución de F4, la verificación mostró
13/13 checks ✅ pero un análisis posterior reveló que los FK apuntaban
a la forma **raw** de F3 (OVALADO 5,072 + OVALADA 673) en lugar de la
forma **consolidada** (OVAL 5,745).

**Causa raíz**: El orden original era:
1. `seed_dim_valor_atributo`
2. `seed_map_atributo_valor`
3. `populate_fk_dim_valor`

El FK se poblaba contra el `valor_canonico` que aún estaba en forma raw.

**Fix**: Se añadió un nuevo paso:
3'. `apply_consolidation_to_silver` → `UPDATE silver.valor_canonico` a
la forma consolidada (OVAL, no OVALADO).

Y se relajó el filtro de `populate_fk_dim_valor` para re-asignar FKs
incluso cuando ya existían (idempotencia vía JOIN determinístico).

**Resultado**:
- silver.valor_canonico = `OVAL` (5,745) ← consolidado
- silver.dim_valor_atributo_id → dim_valor_atributo.OVAL ← FK a forma consolidada
- map_atributo_valor: (doa_id, "OVALADO", "OVAL") ← audit trail preservado

### 3.2 Otros ajustes

- **SQLite portabilidad**: Reemplazado `COUNT(DISTINCT (col1, col2))` por
  `COUNT(*) FROM (SELECT col1, col2 GROUP BY col1, col2)` (SQLite no
  soporta row-value syntax en agregación).
- **Idempotencia FK**: Eliminado el filtro `dim_valor_atributo_id IS NULL`
  del UPDATE en `populate_fk_dim_valor`. Ahora re-asigna siempre (la
  query es determinística por JOIN, así que la 2da ejecución es no-op
  efectiva — verificado en métricas: 107,394 cambios pero todos al
  mismo valor).

---

## 4. Métricas de la primera ejecución (post-fix)

```
[f4] dim_valor_atributo:
  filas insertadas:           0   ← ya poblado por F3
  atributos distintos:        25
  observaciones únicas:       107394

[f4] map_atributo_valor:
  filas insertadas:           11  ← 11 nuevas (post-consolidation observations)
  pares únicos:               205

[f4] apply_consolidation_to_silver:
  filas leídas:               107394
  filas modificadas:          10687
  por regla de consolidación:
    GENERO_MORFOLOGICO:       8351  (forma, distension)
    NORMALIZACION:            2308  (presencia: NO_SE_OBSERVAN→AUSENTE)
    SINONIMO:                 28    (grosor_pared: ENGROSADO→AUMENTADO)

[f4] silver_atributos_hallazgo.dim_valor_atributo_id:
  pobladas en este run:       107394  ← todas re-asignadas
  huérfanos pre-update:       0
  huérfanos post-update:      0

[f4] cobertura: 107394 / 107394 (100.0%)  ✅ CRITERIO GO CUMPLIDO
```

### 4.1 Segunda ejecución (idempotencia)

```
[f4] dim_valor_atributo:
  filas insertadas:           0

[f4] map_atributo_valor:
  filas insertadas:           0   ← idempotente

[f4] apply_consolidation_to_silver:
  filas modificadas:          0    ← idempotente

[f4] populate_fk_dim_valor:
  pobladas en este run:       107394  ← re-asignadas al mismo valor (no-op)

[f4] cobertura: 107394 / 107394 (100.0%)  ✅
```

> **Conclusión**: La idempotencia se mantiene porque (a) los UPSERT
> usan ON CONFLICT DO NOTHING, (b) `apply_consolidation_to_silver`
> sólo UPDATE si el valor cambia, y (c) `populate_fk_dim_valor`
> resuelve al mismo FK via JOIN determinístico.

---

## 5. Veredicto del criterio GO

| Criterio | Esperado | Observado | Status |
|---|---|---|---|
| Cobertura `silver_atributos_hallazgo.dim_valor_atributo_id` | 100% | 100.0% (107,394/107,394) | ✅ |
| Huérfanos post-F4 | 0 | 0 | ✅ |
| `dim_valor_atributo` poblado | ≥100 filas | 173 | ✅ |
| `map_atributo_valor` poblado | ≥100 filas | 218 | ✅ |
| Atributos distintos cubiertos | ≥25 | 29 | ✅ |
| Categorías de consolidación | ≥3 | 4 (IDENTIDAD, GENERO_MORFOLOGICO, SINONIMO, NORMALIZACION) | ✅ |
| Idempotencia | no-op en 2da ejecución | Verificado | ✅ |
| Consolidación propagada a silver | sí | 10,687 filas modificadas | ✅ |

**Veredicto final**: ✅ **GO para Gold**

---

## 6. Veredicto del checklist completo (verify_silver_f4.py)

```
[A. dim_valor_atributo poblado]
  ✅ A1 ≥100 filas: 173
  ✅ A2 ≥25 atributos: 29
  ✅ A3 nulos: 0
  ✅ A4 únicos: 0 dup

[B. map_atributo_valor poblado]
  ✅ B1 ≥100 filas: 218
  ✅ B2 ≥3 orígenes: 4 (IDENTIDAD, GENERO_MORFOLOGICO, SINONIMO, NORMALIZACION)
  ✅ B3 únicos: 0 dup
  ✅ B4 FK válida: 0 inválidas
  ✅ B5 canonicos no vacíos: 0 nulos

[C. Cobertura del diccionario (CRITERIO GO)]
  ✅ C1 100% cobertura: 107394/107394
  ✅ C2 0 huérfanos

[D. Consistencia con F3]
  ✅ D1 dim_atributo FK: 0 inválidas
  ✅ D2 map cubre observados: 205 vs 205

RESULTADO: 13/13 checks pasaron
✅ PASS — Todos los criterios cumplidos
>>> VEREDICTO F4: GO <<<
```

---

## 7. Cómo correr

### 7.1 Build

```bash
# Asegurar que F1, F2, F2_1, F3 ya corrieron
python scripts/build_silver.py --phase f4
```

Salida esperada:
```
[f4] OK en ~1.4s
[f4] cobertura dim_valor_atributo_id: 107394 / 107394  (100.0%)
[f4] ✅ cobertura 100% — diccionario completo
```

### 7.2 Verificación

```bash
python scripts/verify_silver_f4.py
```

Exit code 0 si PASS, 1 si FAIL.

### 7.3 Re-correr (idempotente)

```bash
# Cualquiera de las dos es segura de re-correr:
python scripts/build_silver.py --phase f4
python scripts/verify_silver_f4.py
```

---

## 8. Riesgos y mitigaciones

### 8.1 dim_valor_atributo tiene formas raw pre-existentes

**Riesgo**: dim_valor_atributo contiene 173 filas, muchas en forma raw
(OVALADO, GLOBOSA, DISTENDIDA, ENGROSADO) del seed F3. Aunque no se
usan para el FK actual, ocupan espacio.

**Mitigación**:
- Aceptable a corto plazo (no afecta cobertura).
- Limpieza opcional: TRUNCATE dim_valor_atributo + re-seed desde
  valores consolidados. **No recomendado** sin auditoría previa — los
  valores raw son vocabulario válido para variantes futuras.

### 8.2 Doble fila en map_atributo_valor post-consolidation

**Riesgo**: Tras consolidar silver.valor_canonico, map_atributo_valor
tiene tanto la fila original (`OVALADO → OVAL`) como la nueva
(`OVAL → OVAL` desde silver post-consolidado). Esto produce 11 filas
redundantes.

**Mitigación**: Aceptable. La unicidad `(dim_organo_atributo_id,
valor_original)` se preserva (los 11 nuevos tienen valor_original
distinto).

### 8.3 ~10% de silver modificado por F4

**Riesgo**: El cambio de silver.valor_canonico de raw a consolidado es
un cambio de **significado** (OVALADO → OVAL). Cualquier código que
asumía la forma raw verá diferencias.

**Mitigación**:
- No se identificó código dependiente de la forma raw.
- Gold queries ahora pueden usar directamente `dva.valor` (forma
  consolidada) sin JOIN a map.

---

## 9. Decisiones arquitectónicas

### 9.1 ¿Por qué consolidar en silver y no dejar solo en map?

**Decisión**: Consolidar también `silver.valor_canonico` (no solo
registrar en `map_atributo_valor`).

**Rationale**:
- Gold queries no requieren JOIN adicional para análisis.
- `dim_valor_atributo` sirve como dimensión Gold-ready.
- `map_atributo_valor` queda como audit trail.

**Trade-off**: Pérdida de la forma raw en silver (se preserva en
map.valor_original).

### 9.2 ¿Por qué map_atributo_valor usa (doa_id, valor_original) y no (doa_id, valor_canonico)?

**Decisión**: PK de map_atributo_valor es `(dim_organo_atributo_id,
valor_original)`.

**Rationale**:
- Permite registrar MÚLTIPLES originales que consolidan al MISMO canónico
  (ej. OVALADO y OVALADA → OVAL).
- Si PK fuera por canónico, perderíamos la distinción.
- El "original" es la observación RAW — debe ser inmutable.

### 9.3 ¿Por qué `orden` se calcula por frecuencia?

**Decisión**: `dim_valor_atributo.orden` rank por frecuencia
descendente dentro del atributo.

**Rationale**:
- Default ORDER BY en UIs Gold-friendly.
- El más frecuente (orden=1) suele ser el "valor típico" (OVAL,
  NORMAL, CONSERVADO, PRESENTE).

---

## 10. Próximos pasos

### 10.1 Pre-Gold

Antes de avanzar a Gold, completar:
- [x] Cerrar F4 — **completado en este reporte**
- [ ] Definir contrato Gold (entregable G0)
- [ ] Validar manualmente 2-3 queries Gold contra F4 output

### 10.2 Gold (G1, G2)

Plan tentativo:
- **G1**: Crear `fact_informe_atributo` como vista materializada de
  `silver_atributos_hallazgo` JOIN `dim_valor_atributo`. PK: (informe_id,
  dim_organo_id, dim_segmento_id, dim_atributo_id, lateralidad).
- **G2**: Métricas de cohorte (prevalencia por atributo × especie ×
  rango etario × sexo).

---

## 11. Conclusión

F4 cumple todos los criterios GO definidos en el plan original:
- ✅ Cobertura 100% del diccionario
- ✅ Consolidación propagada a silver (10,687 filas modificadas)
- ✅ Audit trail en map_atributo_valor (218 filas)
- ✅ Idempotente
- ✅ Verificación automatizada (13/13 checks)
- ✅ Documentación completa

**La fase F4 está cerrada y la pre-condición para Gold está cumplida.**
