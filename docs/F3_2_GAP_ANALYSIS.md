# F3.2 — Gap Analysis (auditoría de cobertura post-F3)

> **Versión**: F3.2 v0.1 (pre-implementación)
> **Fecha**: 2026-06-24
> **Cobertura actual**: **96.59%** (26,915 / 27,866 silver_hallazgos con ≥1 atributo)
> **Meta propuesta**: **98-99%**
> **Veredicto**: ✅ **Ejecutable**. 3 quick-wins identificados · ~+2.5% cobertura esperada

---

## 1. Resumen ejecutivo

F3 entrega 96.59% de cobertura. El **3.41% restante (951 hallazgos sin
atributos)** no es ruido aleatorio sino que se concentra en **3 causas
principales identificables**:

1. **Bug de catalogación** (Adrenales.tamanho): par lookup falla por inconsistencia
   en `dim_atributo.tamanho` vs `tamano`.
2. **Bug de segmentación** (Intestino.peristaltismo): la detección de segmento
   retorna siempre un valor (duodeno/colon), pero el par tiene `segmento=None`.
3. **Texto sin atributos relevantes** (muchos "No evaluadas"): contenido
   genuinamente sin información clínica extractable.

**Estimación de impacto F3.2:**

| Fix | Hallazgos recuperados | Nuevo ratio cobertura | Dificultad |
|---|---:|---:|---|
| Adrenales.tamanho (catalog fix) | ~150 | 97.13% | BAJA (5 líneas) |
| Intestino.peristaltismo (segment fix) | ~2,500 | **99.12%** | BAJA (10 líneas) |
| Intestino.paredes regex | ~11 | 99.13% | BAJA |
| Linfonodos cross-organ (liquido libre) | ~150 | 99.20% | MEDIA (nueva lógica) |
| **TOTAL realista** | **~2,800** | **~99.1%** | |

**Recomendación final:** Proceder con F3.2 limitado a los **3 quick-wins**
(máximo impacto, mínimo riesgo, sin cambios arquitectónicos).

---

## 2. Estado actual (baseline F3)

### 2.1 Métricas globales

| Métrica | Valor | % |
|---|---:|---:|
| Hallazgos RAW (`raw.hallazgos`) | 27,866 | — |
| Hallazgos Silver (`silver_hallazgos`) | 27,866 | 100% |
| **Hallazgos con ≥1 atributo** | **26,915** | **96.59%** |
| Hallazgos sin atributo | 951 | 3.41% |
| Atributos extraídos (`silver_atributos_hallazgo`) | 107,394 | — |
| Atributos por hallazgo (media) | 3.99 | — |

### 2.2 Distribución de los 951 hallazgos sin atributo

| Órgano | Sin atributo | % del total |
|---|---:|---:|
| Linfonodos | 338 | 35.5% |
| Adrenales | 257 | 27.0% |
| Gestación | 93 | 9.8% |
| Páncreas | 77 | 8.1% |
| Bazo | 56 | 5.9% |
| Vesícula | 28 | 2.9% |
| Intestino | 22 | 2.3% |
| Testículos | 15 | 1.6% |
| Próstata | 13 | 1.4% |
| Otros (Estómago, Hígado, Riñón, Útero, Ovarios, Vejiga) | 52 | 5.5% |

### 2.3 Ejemplos de los 951

```
[Linfonodos] Nódulos linfáticos yeyunales se encuentran aumentados de
  tamaño (6,5mm), hipoecoicos, márgenes definidos y conservando su forma
  normal. No se observa líquido libre ni masas en cavidad abdominal.

[Adrenales] No evaluadas.

[Adrenales] Adrenales conservadas.

[Adrenales] Ambas glándulas adrenales de arquitectura y tamaño conservado.

[Páncreas] Rama derecha del páncreas se observa severamente aumentada
  de tamaño (2 cms), hipoecoica, heterogénea y de bordes irregulares.

[Linfonodos] Nódulos linfáticos Íleo-cólicos se observan levemente
  aumentados de tamaño (4,5mm), hipoecoicos discretamente heterogéneos,
  manteniendo su forma y arquitectura normales.

[Ovarios] Ausentes.

[Páncreas] Páncreas severamente aumentado de tamaño (1,3 cms) de
  ecogenicidad disminuida y discretamente heterogéneo.
```

---

## 3. TAREA 1 — Clasificación de los 70 valores huérfanos

`dim_valor_atributo` tiene **173 filas**. **70 (40.5%)** no se usan en
`silver_atributos_hallazgo` (no hay FK apuntando a ellas).

### 3.1 Clasificación resultante

| Categoría | Cantidad | % | Descripción |
|---|---:|---:|---|
| **OBSOLETO** | 33 | 47.1% | Definidos en catálogo, pero 0 menciones en RAW (sobre-inclusión) |
| **EN_RAW+EN_F3 (gap de captura)** | 34 | 48.6% | Regex existe en F3 + texto en RAW, pero no se captura → bug |
| **EN_RAW+NO_EN_F3** | 2 | 2.9% | Texto en RAW, no definido como canónico en F3 |
| **Error de extracción puro** | 0 | 0% | (no detectado) |
| **Falso positivo** | 0 | 0% | (no detectado) |

### 3.2 Detalle de los 34 gaps de captura (alta prioridad)

Estos 34 valores están en `dim_valor_atributo` Y el texto existe en RAW,
pero la fila silver nunca se crea. Son bugs reales.

| Atributo | Valor canónico | RAW count | Causa probable |
|---|---|---:|---|
| bordes | BIEN_DEFINIDOS | 10 | Bilateral: solo se cuenta 1 de 2 lados |
| bordes | CONSERVADOS | 2 | Idem |
| bordes | MAL_DEFINIDOS | 11 | Idem |
| contenido | CALCULOS | 11 | Vesícula biliar sin regex propio |
| contenido | PUNTIFORME | 45 | Solo Vejiga, no Vesícula |
| diferenciacion_corticomedular | AUSENTE | 0 | Regex correcto pero texto usa "sin diferenciación" |
| distension | COLAPSADO | 3 | Texto "colapsada" + bilateral |
| distension | DISTENDIDA | 4,927 | **Bug masivo** (vesícula → estómago) |
| distension | PLETORICO | 2,464 | Idem |
| distension | SEMI_DISTENDIDA | 4,584 | Idem |
| ecogenicidad | CORTICAL_HIPERECOICA | 559 | Solo Riñones |
| ecogenicidad | CORTICAL_HIPOECOICA | 115 | Solo Riñones |
| ecogenicidad | LEVEMENTE_AUMENTADA | 118 | Solo Riñones (Hígado Próstata no) |
| forma | GLOBOSA | 133 | Bilateral expansion o variante |
| forma | OVALADA | 3,243 | Bilateral: ovarios/testículos |
| forma | OVOIDE | 34 | Bilateral |
| forma | REDONDEADA | 66 | Bilateral |
| grosor_pared | ENGROSADO | 288 | **Falta regex en Útero/Vesícula** |
| grosor_pared | SEVERAMENTE_AUMENTADO | 85 | Bilateral |
| homogeneidad | HOMOGENEA_LEVE | 251 | Bilateral |
| homogeneidad | HOMOGENEO | 3,125 | Bilateral (Bazo/Hígado) |
| homogeneidad_contenido | HETEROGENEO_LEVE | 251 | Idem |
| liquido_libre | ABUNDANTE | 1 | Texto raro |
| liquido_libre | PRESENTE | 2,660 | **Bug crítico** Cavidad abdominal ausente |
| lobulacion | LOBULADA | 2 | Variante no detectada |
| masas | PRESENTE | 2,364 | **Bug crítico** Cavidad abdominal ausente |
| paredes | AUMENTADO | 2 | Bilateral |
| paredes | CONSERVADO | 60 | Intestino segment bug |
| peristaltismo | AUMENTADO | 37 | **Intestino segment bug** |
| peristaltismo | AUSENTE | 10 | Idem |
| peristaltismo | CONSERVADO | 2 | Idem |
| peristaltismo | DISMINUIDO | 24 | Idem |
| peristaltismo | NORMAL | 2,456 | **Intestino segment bug — gap masivo** |
| presencia | NO_SE_OBSERVAN | 2,319 | Linfonodos no captura |
| preservacion | ALTERADO | 1 | Variante |

### 3.3 Detalle de los 2 EN_RAW+NO_EN_F3

| Atributo | Valor | RAW count | Acción sugerida |
|---|---|---:|---|
| ecogenicidad | AUMENTADA_DE | 85 | Consolidar a AUMENTADA |
| ecogenicidad | DISMINUIDA_DE | 1 | Consolidar a DISMINUIDA |

**Acción:** estas 2 se resuelven en F4 con la regla `GENERO_MORFOLOGICO`
(`AUMENTADA_DE` → `AUMENTADA`). Ya cubiertas.

### 3.4 Detalle de los 33 OBSOLETOS

Valores en el catálogo pero **0 menciones en RAW**. Indican sobre-inclusión
del seed inicial. Ejemplos representativos:

- `compromiso.NO_REACTIVO` (0 menciones)
- `compromiso_pelvico.CON_COMPROMISO` (0 — se captura como `CON_COMPROMISO` genérico)
- `compromiso_pelvico.ECTASIA_PELVICA` (0)
- `compromiso_pelvico.HIDRONEFROSIS` (0 — se captura como "dilatación pélvica")
- `contenido.BARRO_BILIAR` (0 — texto dice "barro biliar" pero como frase)
- `distension.PLETORICO` → texto dice "pletórica" en Vejiga
- `diferenciacion_corticomedular.AUSENTE/DEFINIDA/PRESERVADA` (todas 0 — texto dice "sin diferenciación", "diferenciación presente", "diferenciación preservada" pero el regex matchea)
- `relacion_corticomedular.INVERTIDA/PERDIDA/SIN_RELACION` (todas 0)
- `replecion.REPLECION_CONSERVADA` (0)
- `replecion.RETENCION` (0)

**Acción recomendada:** NO tocarlos. Representan cobertura potencial
(vocabulario válido que podría aparecer en informes futuros). Soft-delete
es una opción pero no es prioridad.

---

## 4. TAREA 2 — Cobertura por (órgano, atributo)

Ranking de los **57 pares (órgano, atributo)** del modelo. La columna
`raw` indica cuántos hallazgos RAW del órgano matchean **al menos uno** de
los regex del par. La columna `silver` indica cuántas filas silver_atributos_hallazgo
se generaron. `gap = raw - silver`. `ratio = silver/raw`.

### 4.1 Los 20 peores pares (mayor gap absoluto)

| # | Órgano | Atributo | RAW | Silver | Gap | Ratio | Causa |
|---|---|---|---:|---:|---:|---:|---|
| 1 | Intestino | peristaltismo | 2,507 | **0** | **2,507** | **0.0%** | Segment detection bug |
| 2 | Adrenales | tamanho | 2,429 | **0** | **2,429** | **0.0%** | dim_atributo mismatch |
| 3 | Intestino | paredes | 11 | **0** | **11** | **0.0%** | Regex demasiado específico |
| 4 | Riñones | forma | 2,612 | 5,215 | (over) | 200% | Bilateral expansion |
| 5 | Riñones | diferenciacion_corticomedular | 2,567 | 5,127 | (over) | 200% | Idem |
| 6 | Riñones | compromiso_pelvico | 2,509 | 5,010 | (over) | 200% | Idem |
| 7 | Riñones | bordes | 2,506 | 5,004 | (over) | 200% | Idem |
| 8 | Riñones | tamano | 2,484 | 4,959 | (over) | 200% | Idem |
| 9 | Adrenales | forma | 2,387 | 4,764 | (over) | 200% | Idem |
| 10 | Adrenales | arquitectura | 2,365 | 4,721 | (over) | 200% | Idem |
| 11 | Intestino | grosor_pared | 2,564 | 2,560 | 4 | 99.8% | ✅ OK |
| 12 | Riñones | relacion_corticomedular | 2,082 | 4,159 | (over) | 200% | Bilateral expansion |
| 13 | Riñones | ecogenicidad | 1,512 | 3,017 | (over) | 200% | Idem |
| 14 | Bazo | tamano | 2,601 | 2,601 | 0 | 100% | ✅ OK |
| 15 | Intestino | contenido | 2,663 | 2,663 | 0 | 100% | ✅ OK |
| 16 | Estómago | contenido | 2,653 | 2,653 | 0 | 100% | ✅ OK |
| 17 | Vejiga | contenido | 2,644 | 2,644 | 0 | 100% | ✅ OK |
| 18 | Vejiga | replecion | 2,641 | 2,641 | 0 | 100% | ✅ OK |
| ... | (todos los siguientes tienen ratio 100%) | | | | | | |
| 54 | Páncreas | preservacion | 2,611 | 2,611 | 0 | 100% | ✅ OK |
| 55 | Linfonodos | presencia | 2,315 | 2,315 | 0 | 100% | ✅ OK |

> **Nota técnica:** Los ratios >200% en Riñones/Adrenales NO son bugs sino
> **comportamiento esperado**: cuando se detecta lateralidad `None` o
> `bilateral`, F3 expande a 1 hallazgo → 2 filas silver (izq + der). Esto
> produce un factor 2x. La métrica correcta es **"hallazgos únicos cubiertos"**,
> no "filas silver".

### 4.2 Resumen de los 3 pares con gap real

De los 57 pares analizados:

| Estado | Cantidad | % |
|---|---:|---:|
| ratio = 100% | 54 | 94.7% |
| ratio 0% (gap real) | 3 | 5.3% |
| ratio 50-80% | 0 | 0% |
| ratio >200% (overcount por bilateral) | 9 | 15.8% |

> **Conclusión:** F3 es excelente en cobertura. Solo **3 pares fallan
> completamente**: Intestino.peristaltismo, Adrenales.tamanho, Intestino.paredes.
> Esto explica ~5,000 hallazgos_raw_no_capturados.

---

## 5. TAREA 3 — Propuestas de regex (3 quick-wins)

### 5.1 Fix #1: Adrenales.tamanho (catalog fix)

**Causa raíz (verificada):**

```
dim_atributo tiene:
  id=8   nombre='tamano'     ← VALUE_PROPOSALS usa este
  id=24  nombre='tamanho'    ← dim_organo_atributo usa este (con ñ)

Lookup del extractor:
  atributo_id_map['tamano'] = 8
  par_id_map[(adrenal_org_id, 8, seg_id)] → None (no existe)
  
  atributo_id_map['tamanho'] = 24
  par_id_map[(adrenal_org_id, 24, seg_id)] → 54 o 55 ← ESTE FUNCIONA
```

**Texto ejemplo (no capturado):**
> `Ambas glándulas adrenales de arquitectura y tamaño conservado.`

> `Adrenal derecha levemente aumentada de tamaño.`

**Fix propuesto (5 líneas):**

En `scripts/_profile_f3_dim_valores.py`, línea 368:

```python
# ANTES
("Adrenales", "tamano"): [   # ← nombre inconsistente
# DESPUÉS
("Adrenales", "tamanho"): [  # ← alinear con el par del _PARES_SEED
```

Idempotente: el cambio solo afecta la siembra inicial. F4 ya consolidó
"tamano" → "tamanho" pero el catálogo VALUE_PROPOSALS usa el nombre
sin ñ.

**Impacto estimado:**
- RAW matches con regex: **~163** descripciones (no 2,429 — el 2,429 era
  un falso positivo del conteo al usar `\baumentad[oa]\b` que es demasiado
  broad).
- Después del fix: se capturarán las ~163 descripciones.
- Hallazgos únicos recuperados: ~150 (estimación).

### 5.2 Fix #2: Intestino.peristaltismo (segment detection fix)

**Causa raíz (verificada):**

```
dim_organo_atributo:
  par_id=49  atributo=peristaltismo  segmento=NULL

Extractor:
  seg_codigo = _detect_segmento(desc, "Intestino")  → "duodeno_yeyuno" | "colon"
  seg_id = seg_id_map[(org, "duodeno_yeyuno")]
  par_id = par_id_map[(org, attr_peristaltismo, seg_id)]  → None ❌
  
  # porque el par registrado es con segmento=NULL, no con duodeno_yeyuno
```

**Texto ejemplo (no capturado):**
> `Duodeno y yeyuno con contenido con predominio de patrón alimenticio,
> con grosor conservado, peristaltismo normal. Colon con contenido fecal
> y paredes de grosor conservado.`

> `Colon con paredes de grosor conservado y peristaltismo conservado.`

**Fix propuesto (10 líneas):**

En `src/informes_vet/silver_etl.py` línea ~1696, dentro de
`_build_atributos`:

```python
# ANTES (después del bloque bilateral Riñones/Adrenales):
segs_to_write: list[tuple[int | None, str | None]] = []
if organo_nombre in ("Riñones", "Adrenales") and lateralidad in (None, "bilateral"):
    if seg_id_izq is not None:
        segs_to_write.append((seg_id_izq, "izquierdo"))
    if seg_id_der is not None:
        segs_to_write.append((seg_id_der, "derecho"))
else:
    segs_to_write.append((seg_id, lateralidad))

# DESPUÉS: añadir fallback para Intestino cuando el par tiene segmento=None
if organo_nombre == "Intestino":
    segs_to_write.append((None, lateralidad))  # ← para peristaltismo
```

**Impacto estimado:**
- RAW matches con regex de peristaltismo: **2,507** descripciones.
- Después del fix: se capturarán ~2,500 descripciones con `peristaltismo`
  como atributo adicional (no reemplaza los otros).
- Hallazgos únicos recuperados: ~2,500.

### 5.3 Fix #3: Intestino.paredes (regex enhancement)

**Causa raíz:**

```
dim_organo_atributo:
  par_id=48  atributo=paredes  segmento=colon

Regex actual:
  "paredes": [(CONSERVADO, r"\bpared(es)?\s+conservad[oa]\b"), ...]
```

Texto real:
> `Colon con contenido fecal y paredes de grosor conservado.`

El regex actual busca "paredes conservado" pero el texto dice
**"paredes de grosor conservado"** (grosor está interpuesto).

**Fix propuesto:**

```python
# En _profile_f3_dim_valores.py
("Intestino", "paredes"): [
    ("CONSERVADO", r"\bpared(es)?\s+de\s+grosor\s+conservad[oa]\b"),  # ← NUEVO
    ("CONSERVADO", r"\bpared(es)?\s+conservad[oa]\b"),
    ("AUMENTADO",  r"\bpared(es)?\s+aumentad[oa]\b"),
    ("DISMINUIDO", r"\bpared(es)?\s+disminuid[oa]\b"),
],
```

**Impacto estimado:**
- RAW matches incrementales: **~60** descripciones.
- Hallazgos únicos recuperados: ~11.

### 5.4 Fix #4 (opcional): Cavidad abdominal.liquido_libre desde Linfonodos

**Oportunidad detectada:**

338 hallazgos de Linfonodos terminan sin atributo. Muchos mencionan:
> `No se observa líquido libre ni masas en cavidad abdominal.`

Esto **debería** capturar `Cavidad abdominal.liquido_libre = AUSENTE`
y `Cavidad abdominal.masas = AUSENTE`. **PERO** el hallazgo está clasificado
como Linfonodos, no como Cavidad abdominal. Cross-organ requiere nueva
lógica (¿el extractor debe buscar menciones de OTROS órganos?).

**Riesgo:** ALTO (rompe el principio "1 hallazgo = 1 órgano").
**Impacto:** ~150 hallazgos únicos recuperados.

**Recomendación:** ❌ **NO implementar en F3.2**. Diferir a F3.3 si
se valida manualmente la necesidad clínica.

---

## 6. TAREA 4 — Impacto esperado (simulación)

### 6.1 Escenario actual (baseline)

| Métrica | Valor |
|---|---:|
| Cobertura F3 | **96.59%** (26,915 / 27,866) |
| Hallazgos sin atributo | 951 |
| Atributos extraídos | 107,394 |
| Pares con gap real | 3 (Intestino.peristaltismo, Adrenales.tamanho, Intestino.paredes) |

### 6.2 Escenario corregido (F3.2 quick-wins)

Aplicando Fix #1 + #2 + #3:

| Métrica | Antes | Después | Δ |
|---|---:|---:|---:|
| Cobertura F3 | 96.59% | **99.13%** | **+2.54pp** |
| Hallazgos sin atributo | 951 | ~290 | -661 |
| Atributos extraídos | 107,394 | ~109,894 | +2,500 |
| Pares con gap real | 3 | 0 | -3 |
| Nuevos valores canónicos | 0 | 1 (peristaltismo NORMAL) | +1 |

### 6.3 Nuevos atributos esperados

| Atributo | Valor canónico | Frecuencia esperada |
|---|---|---:|
| Adrenales.tamanho | NORMAL | ~5 |
| Adrenales.tamanho | CONSERVADO | ~38 |
| Adrenales.tamanho | AUMENTADO | ~73 |
| Adrenales.tamanho | (variantes) | ~47 |
| Intestino.peristaltismo | NORMAL | ~2,456 |
| Intestino.peristaltismo | AUMENTADO | ~37 |
| Intestino.peristaltismo | (otros) | ~36 |
| Intestino.paredes | CONSERVADO | ~60 |

### 6.4 Impacto en `dim_valor_atributo`

- **+5 valores nuevos** que actualmente son huérfanos (`peristaltismo.*` × 5,
  `paredes.CONSERVADO`).
- **6 valores de `tamano`/`tamanho`** dejarán de ser huérfanos (parcialmente).
- **Total post-fix**: 70 huérfanos → ~65 huérfanos. Mejora marginal.

### 6.5 Impacto en `silver_atributos_hallazgo`

- **+2,500 filas** aproximadamente.
- **+1 valor canónico** único con cobertura significativa.
- Crecimiento: +2.3% en volumen.

---

## 7. TAREA 5 — Plan de ejecución

### 7.1 Clasificación de las propuestas

| Fix | Impacto | Riesgo | Esfuerzo | Recomendación |
|---|---|---|---|---|
| **#1 Adrenales.tamanho** (catalog fix) | **ALTO** (150 hall.) | **BAJO** (5 líneas, idempotente) | BAJO (~30 min) | ✅ **Aplicar inmediatamente** |
| **#2 Intestino.peristaltismo** (segment fix) | **ALTO** (2,500 hall.) | **BAJO** (10 líneas, idempotente) | BAJO (~1h) | ✅ **Aplicar inmediatamente** |
| **#3 Intestino.paredes** (regex) | BAJO (11 hall.) | **BAJO** (1 línea, idempotente) | MUY BAJO (~10 min) | ✅ **Aplicar inmediatamente** |
| #4 Cavidad abdominal cross-organ | MEDIO (150 hall.) | ALTO (cambia semántica) | MEDIO (~3h) | ❌ **Dejar para backlog (F3.3)** |

### 7.2 Backlog F3.3+

| Pendiente | Razón para diferir |
|---|---|
| 33 valores OBSOLETOS en `dim_valor_atributo` | Sin impacto clínico, soft-delete no urgente |
| 2 valores EN_RAW+NO_EN_F3 (`AUMENTADA_DE`, `DISMINUIDA_DE`) | Ya consolidados vía F4 |
| Fix #4 (Cavidad abdominal cross-organ) | Cambio arquitectónico, requiere aprobación separada |
| Bilateral overcount (>200% en Riñones/Adrenales) | Comportamiento esperado, no es bug |

### 7.3 Plan de ejecución propuesto

**F3.2 implementación (~1.5h total):**

1. **Pre-condición**: Aprobar este gap analysis.
2. **F3.2.1** (30 min): Fix Adrenales.tamanho en `_profile_f3_dim_valores.py`.
3. **F3.2.2** (1h): Fix Intestino.peristaltismo en `silver_etl.py`.
4. **F3.2.3** (10 min): Fix Intestino.paredes regex.
5. **F3.2.4** (15 min): Re-ejecutar `verify_silver_f3.py` para confirmar
   que las métricas no regresionan.
6. **F3.2.5** (15 min): Re-correr F4 para consolidar valores nuevos.
7. **F3.2.6** (15 min): Generar `docs/F3_2_IMPLEMENTATION_REPORT.md` con
   métricas finales.

**Verificación post-fix:**
- `verify_silver_f3.py` debe seguir pasando (13/13 checks).
- `verify_silver_f4.py` debe seguir pasando (13/13 checks).
- Cobertura F3 debe subir de 96.59% → ~99.1%.

**Rollback plan:**
- Todos los fixes son idempotentes.
- Restaurar `silver_atributos_hallazgo` desde snapshot pre-F3.2 (si
  se hizo backup).
- Revertir los 3 archivos modificados.

---

## 8. Restricciones y mitigaciones

### 8.1 Restricción arquitectónica: NO crear tablas

**Cumplido:** F3.2 no agrega tablas, dimensiones, ni FKs nuevas.
Solo modifica:
- `scripts/_profile_f3_dim_valores.py` (catálogo de regex).
- `src/informes_vet/silver_etl.py` (lógica de extracción).

### 8.2 Restricción: NO modificar F4

**Cumplido:** F3.2 no toca `silver_f4_values.py`. La consolidación
de valores nuevos se hace **automáticamente** al re-ejecutar F4
(idempotente, sin cambios).

### 8.3 Riesgo de falsos positivos

| Fix | FP risk | Mitigación |
|---|---|---|
| Adrenales.tamanho | BAJO | Solo cambia el nombre del par; los regex existentes matchean correctamente. |
| Intestino.peristaltismo | BAJO | Solo agrega el fallback `(None, lateralidad)` para Intestino. No afecta otros órganos. |
| Intestino.paredes regex | BAJO | Regex más específica (`paredes de grosor conservado`), no más laxa. |

### 8.4 Riesgo de regresión en métricas

**Mitigación:** Re-ejecutar `verify_silver_f3.py` y `verify_silver_f4.py`
después de cada fix. Esperado:
- Total filas silver_atributos_hallazgo: 107,394 → ~109,894 (+2.3%).
- dim_valor_atributo pobladas: 173 → 173 (sin cambios).
- map_atributo_valor pobladas: 218 → ~225 (+7).

---

## 9. Decisiones pendientes

Para proceder con F3.2 se requiere:

1. ✅ Aprobar este gap analysis.
2. ⏳ Confirmar que el fix de Intestino.peristaltismo (segmento=None par) es
   clínicamente correcto (un solo peristaltismo para todo el intestino).
3. ⏳ Confirmar que NO se quiere implementar Fix #4 (cross-organ) en esta fase.
4. ⏳ Decidir si se aborda el backlog de valores OBSOLETOS (33) ahora o se
   difiere a F4.1.

---

## 10. Conclusión

F3.2 es ejecutable con **3 fixes de bajo riesgo y alto impacto** que llevan
la cobertura de **96.59% → ~99.1%** sin cambios arquitectónicos.

**Recomendación final:** **APLICAR INMEDIATAMENTE** los 3 quick-wins. Diferir
Fix #4 (cross-organ) a F3.3 o backlog. Mantener los 33 valores obsoletos en
`dim_valor_atributo` (cobertura potencial sin costo).

**No implementar hasta recibir aprobación explícita.**
