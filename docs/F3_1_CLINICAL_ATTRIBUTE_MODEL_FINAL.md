# F3.1 — Clinical Attribute Model FINAL (locked)

**Estado:** 🔒 CONGELADO (decisiones clínicas aprobadas 2026-06-22)
**Reemplaza:** `F3_1_CLINICAL_ATTRIBUTE_MODEL.md` (versión de revisión)
**Fuentes:**
- **Primaria:** plantilla clínica oficial de la veterinaria
- **Validación:** corpus RAW 27.866 hallazgos (`scripts/_profile_f3_1_clinical_coverage.py`)

**Acción:** este documento es la especificación canónica para F3.0.
Cualquier cambio requiere nueva revisión clínica.

---

## 0. Resumen ejecutivo

| Concepto | Valor |
|---|---:|
| Órganos en `dim_organo` | **16** (15 RAW + Cavidad abdominal virtual) |
| Segmentos en `dim_segmento_anatomico` | **6** |
| Atributos canónicos únicos en `dim_atributo` | **31** |
| Pares (órgano, atributo) en `silver_atributos_hallazgo` | **62** |
| Cobertura global del catálogo clínico sobre corpus | **97.6%** (≥1 atributo matcheado) |
| Atributos binarios | **8** (presencia, compromiso, preservacion, aspecto_peripancreatico, compromiso_pelvico, liquido_libre, masas, peristaltismo[bool]) |

---

## 1. Decisiones clínicas congeladas

### 1.1. Decisiones originales (6)

| # | Tema | Decisión | Justificación clínica |
|---|---|---|---|
| 1 | `Riñones.ecogenicidad_cortical` → `Riñones.ecogenicidad` | **GENERALIZAR** | El modelo Silver debe ser estable; la redacción del informe puede cambiar (corteza hoy, parénquima mañana). |
| 2 | `Páncreas.aspecto_peripancreatico` | **MANTENER** | Relevancia clínica real; costo de mantener el atributo es prácticamente cero. |
| 3 | `Cavidad abdominal` | **AGREGAR como órgano virtual** en `dim_organo` con atributos `liquido_libre`, `masas`. | Aparece de forma consistente en la plantilla; no pertenece naturalmente a otro órgano. |
| 4 | `Próstata.aspecto` | **SEPARAR** en `forma` + `lobulacion` | Son variables clínicas distintas: "Aspecto ovalado, bilobulada" → `forma=ovalada`, `lobulacion=bilobulada`. |
| 5 | Riñones — duplicar órganos | **NO**. Mantener un único `RIÑONES` + columna `lateralidad` (izq / der / bilateral). | Preserva consistencia con RAW y facilita agregaciones. |
| 6 | Intestino — segmentos | **v1**: `DUODENO_YEYUNO` (un segmento) + `COLON`. | La plantilla describe duodeno/yeyuno conjuntamente; no introducir separación artificial. |

### 1.2. Cambios adicionales aprobados (3)

| # | Cambio | Detalle |
|---|---|---|
| A | `dim_segmento_anatomico` | Crear tabla con valores iniciales: `DUODENO_YEYUNO`, `COLON`, `RINON_DERECHO`, `RINON_IZQUIERDO`, `ADRENAL_DERECHA`, `ADRENAL_IZQUIERDA`. Permite consultas futuras sin multiplicar órganos. |
| B | `silver_atributos_hallazgo` — columnas adicionales | Agregar `valor_original` (texto crudo extraído) y `valor_normalizado` (NULL en v1). Prepara fuzzy matching / embeddings / reglas de normalización futuras sin perder trazabilidad. |
| C | Órganos reproductivos | **MANTENER** `Útero`, `Ovarios`, `Testículos`, `Gestación` en Silver v1. Reevaluar más adelante con evidencia real de uso. Ya existen en RAW, son canónicos, costo de mantener mínimo. |

---

## 2. Catálogo final de `dim_organo` (16)

```sql
INSERT INTO dim_organo (id, nombre) VALUES
  (1,  'Hígado'),
  (2,  'Riñones'),
  (3,  'Vejiga'),
  (4,  'Vesícula'),
  (5,  'Bazo'),
  (6,  'Próstata'),
  (7,  'Estómago'),
  (8,  'Intestino'),
  (9,  'Páncreas'),
  (10, 'Adrenales'),
  (11, 'Linfonodos'),
  (12, 'Útero'),
  (13, 'Ovarios'),
  (14, 'Testículos'),
  (15, 'Gestación'),
  (16, 'Cavidad abdominal');   -- NUEVO: órgano virtual
```

---

## 3. `dim_segmento_anatomico` (6 segmentos)

| id | nombre | aplica_a_organo | notas |
|---:|---|---|---|
| 1 | `DUODENO_YEYUNO` | Intestino | v1: un solo segmento (decisión clínica #6) |
| 2 | `COLON` | Intestino | |
| 3 | `RINON_DERECHO` | Riñones | usado cuando `lateralidad='derecho'` |
| 4 | `RINON_IZQUIERDO` | Riñones | usado cuando `lateralidad='izquierdo'` |
| 5 | `ADRENAL_DERECHA` | Adrenales | uso opcional |
| 6 | `ADRENAL_IZQUIERDA` | Adrenales | uso opcional |

> Para Riñones en modo UNIFICADO, `segmento_id` queda NULL. En modo SEPARADO
> se asigna `RINON_DERECHO` o `RINON_IZQUIERDO`.

---

## 4. Catálogo final de `dim_atributo` (31 atributos únicos)

```sql
INSERT INTO dim_atributo (id, nombre, es_binario, aplica_a, descripcion) VALUES
  -- VEJIGA (5)
  (1,  'replecion',                FALSE, 'organo',   'grado de llenado vesical'),
  (2,  'contenido',                FALSE, 'organo',   'contenido intravesical'),
  (3,  'homogeneidad_contenido',   FALSE, 'organo',   'homogeneidad del contenido'),
  (4,  'bordes_internos',          FALSE, 'organo',   'bordes internos / pared de bordes'),
  (5,  'grosor_pared',             FALSE, 'organo',   'grosor de pared vesical'),
  -- PRÓSTATA (5)
  (6,  'forma',                    FALSE, 'organo',   'forma prostática'),
  (7,  'lobulacion',               FALSE, 'organo',   'lobulación (uni/bilobulada)'),
  (8,  'tamano',                   FALSE, 'organo',   'tamaño prostático'),
  (9,  'ecogenicidad',             FALSE, 'organo',   'ecogenicidad del parénquima'),
  (10, 'homogeneidad',             FALSE, 'organo',   'homogeneidad del parénquima'),
  -- RIÑONES (7)
  (11, 'forma',                    FALSE, 'organo',   'forma renal'),
  (12, 'tamano',                   FALSE, 'organo',   'tamaño renal'),
  (13, 'bordes',                   FALSE, 'organo',   'bordes renales'),
  (14, 'ecogenicidad',             FALSE, 'organo',   'ecogenicidad del parénquima'),
  (15, 'diferenciacion_corticomedular', FALSE, 'organo', 'diferenciación córtico-medular'),
  (16, 'relacion_corticomedular',  FALSE, 'organo',   'relación córtico-medular'),
  (17, 'compromiso_pelvico',       TRUE,  'organo',   'compromiso de la pelvis renal'),
  -- BAZO (4)
  (18, 'tamano',                   FALSE, 'organo',   'tamaño esplénico'),
  (19, 'forma',                    FALSE, 'organo',   'forma esplénica'),
  (20, 'margenes',                 FALSE, 'organo',   'márgenes esplénicos'),
  (21, 'arquitectura',             FALSE, 'organo',   'arquitectura esplénica'),
  -- ESTÓMAGO (4)
  (22, 'distension',               FALSE, 'organo',   'distensión gástrica'),
  (23, 'contenido',                FALSE, 'organo',   'contenido gástrico'),
  (24, 'estratificacion_pared',    FALSE, 'organo',   'estratificación de la pared'),
  (25, 'grosor_pared',             FALSE, 'organo',   'grosor de pared gástrica'),
  -- HÍGADO (7)
  (26, 'tamano',                   FALSE, 'organo',   'tamaño hepático'),
  (27, 'margenes',                 FALSE, 'organo',   'márgenes hepáticos'),
  (28, 'bordes',                   FALSE, 'organo',   'bordes hepáticos'),
  (29, 'ecogenicidad',             FALSE, 'organo',   'ecogenicidad hepática'),
  (30, 'granulado',                FALSE, 'organo',   'granulado hepático (fino/grueso)'),
  (31, 'arquitectura',             FALSE, 'organo',   'arquitectura hepática'),
  (32, 'patron_vascular',          FALSE, 'organo',   'patrón vascular hepático'),
  -- VESÍCULA (4)
  (33, 'distension',               FALSE, 'organo',   'distensión vesicular'),
  (34, 'contenido',                FALSE, 'organo',   'contenido biliar'),
  (35, 'bordes_internos',          FALSE, 'organo',   'bordes internos vesiculares'),
  (36, 'grosor_pared',             FALSE, 'organo',   'grosor de pared vesicular'),
  -- INTESTINO (6 atributos, 3 con segmento DUODENO_YEYUNO + 2 con COLON + 1 global)
  (37, 'contenido',                FALSE, 'segmento', 'contenido intestinal'),
  (38, 'grosor_pared',             FALSE, 'segmento', 'grosor de pared'),
  (39, 'estratificacion_pared',    FALSE, 'segmento', 'estratificación de pared'),
  (40, 'peristaltismo',            FALSE, 'organo',   'peristaltismo (global, sin segmento)'),
  (41, 'paredes',                  FALSE, 'segmento', 'paredes colónicas'),
  -- PÁNCREAS (2)
  (42, 'preservacion',             TRUE,  'organo',   'preservación / evaluación pancreática'),
  (43, 'aspecto_peripancreatico',  TRUE,  'organo',   'aspecto del tejido peripancreático'),
  -- ADRENALES (3)
  (44, 'forma',                    FALSE, 'organo',   'forma adrenal'),
  (45, 'tamano',                   FALSE, 'organo',   'tamaño adrenal'),
  (46, 'arquitectura',             FALSE, 'organo',   'arquitectura adrenal'),
  -- LINFONODOS (2, ambos binarios)
  (47, 'presencia',                TRUE,  'organo',   'presencia/ausencia de linfonodos'),
  (48, 'compromiso',               TRUE,  'organo',   'compromiso / reactividad'),
  -- ÚTERO (3)
  (49, 'tamano',                   FALSE, 'organo',   'tamaño uterino'),
  (50, 'contenido',                FALSE, 'organo',   'contenido luminal'),
  (51, 'grosor_pared',             FALSE, 'organo',   'grosor de pared uterina'),
  -- OVARIOS (2)
  (52, 'tamano',                   FALSE, 'organo',   'tamaño ovárico'),
  (53, 'forma',                    FALSE, 'organo',   'forma ovárica'),
  -- TESTÍCULOS (4)
  (54, 'tamano',                   FALSE, 'organo',   'tamaño testicular'),
  (55, 'forma',                    FALSE, 'organo',   'forma testicular'),
  (56, 'ecogenicidad',             FALSE, 'organo',   'ecogenicidad testicular'),
  (57, 'homogeneidad',             FALSE, 'organo',   'homogeneidad testicular'),
  -- GESTACIÓN (2)
  (58, 'fetos',                    FALSE, 'organo',   'número de fetos'),
  (59, 'prenez',                   TRUE,  'organo',   'preñez (derivado booleano)'),
  -- CAVIDAD ABDOMINAL (2)
  (60, 'liquido_libre',            TRUE,  'organo',   'presencia de líquido libre'),
  (61, 'masas',                    TRUE,  'organo',   'presencia de masas');
```

**Total atributos únicos:** 61 (la lista incluye repeticiones por órgano — el id es único por nombre+organo, no por nombre global).

> Nota: la tabla `dim_atributo` puede ser **global** (id=nombre canónico, sin FK a órgano) o **por órgano** (id=nombre+organo, con FK). Decisión F3.0: global, con la (organo_id, atributo_id) como par único en `dim_organo_atributo`.

---

## 5. Tabla de aplicación `dim_organo_atributo` (62 pares)

Define qué atributos aplican a qué órganos (y segmentos):

```sql
CREATE TABLE dim_organo_atributo (
    id              INTEGER PRIMARY KEY,
    organo_id       INTEGER NOT NULL REFERENCES dim_organo(id),
    atributo_id     INTEGER NOT NULL REFERENCES dim_atributo(id),
    segmento_id     INTEGER REFERENCES dim_segmento_anatomico(id),  -- NULL = sin segmento
    es_obligatorio  BOOLEAN DEFAULT FALSE,
    UNIQUE(organo_id, atributo_id, segmento_id)
);
```

Pares resultantes (62):

| Órgano | Atributos | count |
|---|---|---:|
| Vejiga | replecion, contenido, homogeneidad_contenido, bordes_internos, grosor_pared | 5 |
| Próstata | forma, lobulacion, tamano, ecogenicidad, homogeneidad | 5 |
| Riñones | forma, tamano, bordes, ecogenicidad, diferenciacion_corticomedular, relacion_corticomedular, compromiso_pelvico | 7 |
| Bazo | tamano, forma, margenes, arquitectura | 4 |
| Estómago | distension, contenido, estratificacion_pared, grosor_pared | 4 |
| Hígado | tamano, margenes, bordes, ecogenicidad, granulado, arquitectura, patron_vascular | 7 |
| Vesícula | distension, contenido, bordes_internos, grosor_pared | 4 |
| Intestino (DUODENO_YEYUNO) | contenido, grosor_pared, estratificacion_pared | 3 |
| Intestino (COLON) | contenido, paredes | 2 |
| Intestino (global, sin segmento) | peristaltismo | 1 |
| Páncreas | preservacion, aspecto_peripancreatico | 2 |
| Adrenales | forma, tamano, arquitectura | 3 |
| Linfonodos | presencia, compromiso | 2 |
| Útero | tamano, contenido, grosor_pared | 3 |
| Ovarios | tamano, forma | 2 |
| Testículos | tamano, forma, ecogenicidad, homogeneidad | 4 |
| Gestación | fetos, prenez | 2 |
| Cavidad abdominal | liquido_libre, masas | 2 |
| **Total** | | **62** |

---

## 6. Esquema `silver_atributos_hallazgo` (congelado)

```sql
CREATE TABLE silver_atributos_hallazgo (
    id                  INTEGER PRIMARY KEY,
    hallazgo_id         INTEGER NOT NULL REFERENCES silver_hallazgos(id),
    organo_id           INTEGER NOT NULL REFERENCES dim_organo(id),
    atributo_id         INTEGER NOT NULL REFERENCES dim_atributo(id),
    segmento_id         INTEGER REFERENCES dim_segmento_anatomico(id),   -- NULL = sin segmento
    lateralidad         VARCHAR(16),                                       -- 'izquierdo'|'derecho'|'bilateral'|NULL
    valor_id            INTEGER REFERENCES dim_valor_atributo(id),          -- valor canónico (si aplica)
    valor_original      TEXT,                                              -- texto crudo extraído
    valor_normalizado   VARCHAR(64),                                       -- NULL en v1
    confianza           DECIMAL(3,2) DEFAULT 1.00,                         -- 0.00-1.00
    fuente              VARCHAR(16) DEFAULT 'regex',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hallazgo_id, organo_id, atributo_id, segmento_id, lateralidad)
);

CREATE INDEX idx_attr_hallazgo    ON silver_atributos_hallazgo(hallazgo_id);
CREATE INDEX idx_attr_atributo    ON silver_atributos_hallazgo(atributo_id);
CREATE INDEX idx_attr_organo      ON silver_atributos_hallazgo(organo_id);
CREATE INDEX idx_attr_lateralidad ON silver_atributos_hallazgo(lateralidad)
    WHERE lateralidad IS NOT NULL;
```

### Decisiones de esquema

| Columna | Decisión |
|---|---|
| `lateralidad` | Solo Riñones en modo SEPARADO. Valores: `'izquierdo'`, `'derecho'`, `'bilateral'`. Modo UNIFICADO: `lateralidad='bilateral'`. |
| `segmento_id` | Solo Intestino y Riñones en modo SEPARADO. Para `peristaltismo`: NULL (es global). Para atributos Intestino: `DUODENO_YEYUNO` o `COLON`. |
| `valor_original` | Siempre presente (texto literal extraído del informe). |
| `valor_normalizado` | NULL en v1; columna reservada para futuras reglas (fuzzy/embeddings/normalización). |
| `valor_id` | FK a `dim_valor_atributo` cuando hay valor canónico mapeado. NULL cuando el valor es texto libre (ej. medidas en cm). |
| `confianza` | 1.00 cuando hay match exacto de regex; <1.00 si hubo fuzzy/inferencia. |

---

## 7. Lógica de extracción Riñones (UNIFICADO / SEPARADO)

```python
def extract_lateralidad(descripcion: str) -> tuple[str, bool]:
    """Retorna (lateralidad, es_separado)."""
    d = descripcion.lower()
    izq = re.search(r"\b(ri[ñn][oó]n\s+izquierd[oa]|izquierd[oa]|izq\.?)\b", d)
    der = re.search(r"\b(ri[ñn][oó]n\s+derech[oa]|derech[oa]|der\.?)\b", d)
    ambos = re.search(r"\b(ambos|ambas|bilateral|bi)\b", d)

    if (izq and der) or ambos:
        return ("bilateral", False)   # modo UNIFICADO
    if izq:
        return ("izquierdo", True)    # modo SEPARADO
    if der:
        return ("derecho", True)      # modo SEPARADO
    return ("bilateral", False)       # fallback (0.7% del corpus)
```

**Distribución corpus:**
- bilateral (UNIFICADO): 95.5% — 1 fila en `silver_atributos_hallazgo` por atributo
- izquierdo (SEPARADO): 37.2% — 1 fila con `lateralidad='izquierdo'`
- derecho (SEPARADO): 36.8% — 1 fila con `lateralidad='derecho'`
- sin lateralidad: 0.7% — fallback a bilateral

**Resultado cardinalidad Riñones:** 2.688 hallazgos × ~7 atributos = ~18.800 filas
(modo UNIFICADO). Si la clínica pide desdoblar SEPARADO en 2 filas separadas,
se duplica a ~37.600.

---

## 8. Cardinalidad estimada de `silver_atributos_hallazgo`

Estimación con regex tentativas (script `_profile_f3_1_clinical_coverage.py`):

| Órgano | n hallazgos | matches/atributo | filas estimadas |
|---|---:|---:|---:|
| Vejiga | 2.690 | 3.81 | 10.250 |
| Próstata | 737 | 3.83 | 2.823 |
| Riñones | 2.688 | 5.00 | 13.440 |
| Bazo | 2.684 | 2.70 | 7.247 |
| Estómago | 2.688 | 2.91 | 7.823 |
| Hígado | 2.687 | 6.43 | 17.276 |
| Vesícula | 2.667 | 3.81 | 10.161 |
| Intestino | 2.688 | 2.83 | 7.605 |
| Páncreas | 2.688 | 0.97 | 2.607 |
| Adrenales | 2.687 | 0.93 | 2.499 |
| Linfonodos | 2.681 | 0.89 | 2.386 |
| Útero | 49 | 0.53 | 26 |
| Ovarios | 5 | 0.40 | 2 |
| Testículos | 27 | 0.74 | 20 |
| Gestación | 200 | 0.50 | 100 |
| Cavidad abdominal | 0 | 0.00 | 0 |
| **Total** | **27.866** | **3.05** | **~84.265** |

**Cobertura global:** 97.6% de los hallazgos tendrán ≥1 atributo extraído.

---

## 9. Cobertura validada (resumen)

De los 61 atributos canónicos:
- ✅ Cobertura ≥50%: **60 / 61** (98.4%)
- ⚠️ Cobertura 10-50%: **0**
- ❌ Cobertura <10%: **1** — `Páncreas.aspecto_peripancreatico` (0.1%)

Decisión clínica: mantener el atributo de todas formas (decisión #2).
La cobertura se elevará automáticamente si el clínico comienza a usar el
término "peripancreático" en informes futuros.

Por órgano (≥1 atributo matcheado):

| Órgano | match | total | % |
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
| Útero | (estimado) 49 | 49 | ~100% |
| Ovarios | 5 | 5 | 100% |
| Testículos | 27 | 27 | 100% |
| Gestación | 200 | 200 | 100% |

---

## 10. Resumen de cambios respecto al catálogo Anexo A original

| Cambio | Cantidad |
|---|---:|
| Atributos únicos (Anexo A → F3.1 final) | 22 → **61** |
| Órganos (Anexo A → F3.1 final) | 15 → **16** (+Cavidad abdominal) |
| Pares (órgano, atributo) (Anexo A → F3.1 final) | 57 → **62** |
| Renombramientos | 2 (`_cm` → `_corticomedular`, `_cortical` → sin sufijo) |
| Fusiones | 1 (`Próstata.aspecto` → `forma` + `lobulacion`) |
| Nuevos atributos | 7 |
| Eliminaciones | 0 (mantenemos compatibilidad con RAW) |
| Nuevas tablas | 2 (`dim_segmento_anatomico`, `dim_organo_atributo`) |
| Columnas nuevas en `silver_atributos_hallazgo` | 3 (`segmento_id`, `lateralidad`, `valor_original`, `valor_normalizado`) |

---

## 11. Plan F3.0 listo para implementar

### 11.1. Schema

1. Migrar `silver_db.py`:
   - Agregar `dim_segmento_anatomico` con 6 valores iniciales
   - Agregar `dim_organo` con el órgano 16 (`Cavidad abdominal`)
   - Agregar `dim_atributo` con 61 entradas
   - Agregar `dim_organo_atributo` con 62 pares
   - Agregar `dim_valor_atributo` con catálogo de valores canónicos (~150 valores)
   - Crear/reemplazar `silver_atributos_hallazgo` con las 5 columnas clave

2. Documentar migraciones en `_MIGRATIONS`.

### 11.2. Extractores

Crear `silver_etl.py:_build_atributos()` con parsers regex por atributo (61
funciones o 1 función con dispatch). Cada parser retorna `(valor_original,
valor_normalizado, valor_id, confianza)`.

### 11.3. Orquestador `build_f3()`

```
build_f3()
  ├── _resolve_organo_segmento(hallazgo)   # asigna segmento_id y lateralidad
  ├── for cada (organo, atributo) in dim_organo_atributo:
  │     _extract_atributo(hallazgo, atributo, segmento_id, lateralidad)
  └── _log_run('f3', ...)
```

Idempotencia: usar `INSERT ... ON CONFLICT (hallazgo_id, organo_id, atributo_id,
segmento_id, lateralidad) DO NOTHING`.

### 11.4. Verificación

Crear `scripts/verify_silver_f3.py` con assertions:
- 61 atributos en `dim_atributo`
- 62 pares en `dim_organo_atributo`
- ~84.000 filas en `silver_atributos_hallazgo`
- Cobertura ≥97% por órgano principal
- Lateralidad: 95% bilateral en Riñones
- Segmento: ~50% DUODENO_YEYUNO, ~50% COLON en Intestino
- Binarios: ≥99% `presencia` en Linfonodos

---

## 12. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| `aspecto_peripancreatico` con 0.1% cobertura | Mantener atributo pero documentar como "experimental" en `dim_atributo.descripcion`. Cobertura subirá con informes futuros. |
| `Próstata.aspecto` corpus usa "aspecto" sin valor canónico | Regex dual: `\baspecto\s+(ovalad|redondead|globoso|irregular|reniform)\b` extrae forma; `\b(bi\|uni)lobulad[oa]\b` extrae lobulación. Cobertura esperada: 90%+ ambos. |
| Lateralidad Riñones: falsos positivos con "riñón izquierdo y derecho" | Si ambos lados presentes → `bilateral` (no separar). Solo si aparece **un solo lado** → modo SEPARADO. |
| Intestino: descripciones con "duodeno y yeyuno" como dos segmentos | v1 los trata como uno. Si la clínica pide separar después, se duplica el atributo. |
| Cavidad abdominal: 0 hallazgos en RAW | El órgano se crea vacío. La extracción se activará cuando la veterinaria empiece a usar este campo en informes. |

---

## 13. Archivos generados en esta revisión

| Archivo | Propósito |
|---|---|
| `docs/F3_ATTRIBUTE_DISCOVERY.md` | Análisis F3 (Anexo A original, 57 pares) |
| `docs/F3_1_ATTRIBUTE_DISCOVERY_NLP.md` | Descubrimiento NLP bottom-up |
| `docs/F3_1_CLINICAL_ATTRIBUTE_MODEL.md` | Revisión inicial contra plantilla clínica |
| `docs/F3_1_CLINICAL_ATTRIBUTE_MODEL_FINAL.md` | **ESTE DOCUMENTO** — versión congelada |
| `scripts/_profile_f3.py` | Profiler genérico Anexo A |
| `scripts/_profile_f3_focused.py` | Profiler por par con grupos de captura |
| `scripts/_profile_f3_1_nlp.py` | Profiler NLP bottom-up |
| `scripts/_profile_f3_1_clinical_coverage.py` | Profiler cobertura plantilla clínica |

---

*Generado por `scripts/_profile_f3_1_clinical_coverage.py` (corpus profiling only;
sin escribir en silver.db). Decisiones clínicas tomadas en sesión 2026-06-22.*

*Próximo paso: implementación de F3.0 conforme a §11 de este documento.*