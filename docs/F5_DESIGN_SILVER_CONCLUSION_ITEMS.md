# F5 — Diseño de `silver_conclusion_items`

> **Versión**: F5 v1.0 — **Diseño** (NO implementado)
> **Fecha**: 2026-06-23
> **Estado**: pendiente de aprobación previa implementación
> **Pre-requisito**: F4 ✅ cerrado (cobertura 100%)

---

## 1. Resumen ejecutivo

Las **conclusiones** son el componente más lingüístico y menos
estructurado de los informes. A diferencia de los hallazgos (que son
oraciones descriptivas de imágenes), las conclusiones son
**oraciones diagnósticas** que pueden contener:

- **Diagnósticos** explícitos ("nefropatía bilateral leve")
- **Sospechas** ("sugerente de piometra")
- **Descartes** ("descartar obstrucción urinaria")
- **Negaciones** ("no se observan alteraciones")
- **Múltiples ítems** por conclusión ("Cistitis. Nefropatía bilateral
  moderada. Pancreatitis severa.")

F5 extrae cada ítem diagnóstico de la conclusión y lo modela en
`silver_conclusion_items` con su modificador, lateralidad, certeza y
tipo.

**Decisión arquitectónica clave**: F5 NO usa NLP, embeddings ni LLM.
Es **extracción basada en reglas + catálogo semilla** construido a
partir del corpus real.

---

## 2. Perfil del corpus `raw.conclusiones`

Datos del análisis del corpus:

| Métrica | Valor |
|---|---|
| Total conclusiones | **2,893** (1:1 con raw.informes) |
| Con texto no vacío | 2,893 (100%) |
| Textos únicos | 2,586 (**89.4%**) — alta variedad |
| Longitud promedio | 199 chars |
| Longitud p50 / p90 | 172 / 367 |
| Oraciones por conclusión | avg **3.18** |
| Conclusión multi-ítem (>1 diagnóstico) | ~60% |

### 2.1 Patrones lingüísticos

| Patrón | Frecuencia | Significado |
|---|---|---|
| `\bde aspecto\b` | **79.8%** | modificador cualitativo ("de aspecto inflamatorio") |
| `\bleve\b` | 69.9% | intensidad |
| `\bmoderad[oa]\b` | 47.1% | intensidad |
| `\bsever[oa]\b` | 21.2% | intensidad |
| `\bdescartar?\b` | 26.5% | diferencial |
| `\bsugerente\b` | 22.8% | sospecha |
| `\bno se observan\b` | 6.4% | negación |
| `\bcompatible\b` | 3.1% | compatibilidad |
| `\bbilateral\b` | **54.2%** | lateralidad |
| `\bizquierd[oa]\b` | 13.8% | lateralidad |
| `\bderech[oa]\b` | 10.4% | lateralidad |

### 2.2 Términos diagnósticos más frecuentes

| # | Término | Frecuencia | Tipo |
|---|---|---|---|
| 1 | nefropatía | 1,602 | DIAGNOSTICO |
| 2 | nefro-* (prefijo) | 1,609 | (incluye nefropatía, nefromegalia, nefrocalcinosis) |
| 3 | hepatomegalia | 1,107 | DIAGNOSTICO |
| 4 | hepatopatía | 556 | DIAGNOSTICO |
| 5 | gastritis | 547 | DIAGNOSTICO |
| 6 | cistitis | 519 | DIAGNOSTICO |
| 7 | barro biliar | 473 | PATRON |
| 8 | sedimento | 458 | PATRON |
| 9 | colitis | 268 | DIAGNOSTICO |
| 10 | pancreatitis | 233 | DIAGNOSTICO |
| 11 | esplenomegalia | 217 | DIAGNOSTICO |
| 12 | peritonitis | 204 | DIAGNOSTICO |
| 13 | adrenomegalia | 198 | DIAGNOSTICO |
| 14 | derrame | 272 | PATRON |
| 15 | piometra | 49 | ETIOLOGIA |
| 16 | cálculo | 34 | ETIOLOGIA |
| 17 | neoplasia / nódulo / masa | 249+217+217 | PATRON |

### 2.3 Distribución por tipo (heurística)

| Categoría | Conteo | % |
|---|---|---|
| Con término diagnóstico (DIAGNOSTICO/PATRON/ETIOLOGIA) | 2,428 | 83.9% |
| Con frase negativa (NEGATIVO) | 315 | 10.9% |
| Con marcador gestacional (preñada, fetos) | 140 | 4.8% |
| Con sospecha explícita | 1,329 | 45.9% |

> **Nota**: Las categorías se solapan (ej. "nefropatía" + "leve"
> es DIAGNOSTICO + modificador de intensidad).

---

## 3. Modelo de datos

### 3.1 Tabla propuesta: `silver_conclusion_items`

```sql
CREATE TABLE silver_conclusion_items (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    informe_id                  INTEGER NOT NULL,
    conclusion_id               INTEGER NOT NULL,   -- raw.conclusiones.id
    conclusion_texto_original   TEXT NOT NULL,      -- texto completo para contexto

    -- Item extraído
    tipo_item                   TEXT NOT NULL,       -- DIAGNOSTICO|PATRON|ETIOLOGIA|NEGATIVO
    termino_detectado           TEXT NOT NULL,       -- ej. "nefropatía", "hepatomegalia"
    termino_canonico            TEXT,                -- versión consolidada (post-F4-style)
    organo_asociado             TEXT,                -- "riñón", "hígado", "vejiga", NULL
    categoria_clinica           TEXT,                -- agrupamiento: "RENAL", "HEPATICA", etc.

    -- Modificadores extraídos
    modificador_intensidad      TEXT,                -- "leve", "moderada", "severa", NULL
    modificador_certeza         TEXT,                -- "sugerente", "compatible", "probable", NULL
    modificador_temporal        TEXT,                -- "crónico", "agudo", NULL
    lateralidad                 TEXT,                -- "bilateral", "izquierdo", "derecho", NULL

    -- Metadata
    confianza                   REAL NOT NULL,       -- 0.0-1.0 según match (1.0 = match exacto)
    texto_match                 TEXT NOT NULL,       -- substring exacto que matchea
    pos_inicio                  INTEGER NOT NULL,    -- offset en conclusion_texto_original
    pos_fin                     INTEGER NOT NULL,

    -- Auditoría
    metodo_extraccion           TEXT NOT NULL,       -- "rule_v1" o "no_match"
    created_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (informe_id) REFERENCES silver_informes(informe_id)
);

CREATE UNIQUE INDEX ix_silver_conclusion_items_unique
    ON silver_conclusion_items (conclusion_id, pos_inicio, termino_detectado);

CREATE INDEX ix_silver_conclusion_items_informe
    ON silver_conclusion_items (informe_id);

CREATE INDEX ix_silver_conclusion_items_tipo
    ON silver_conclusion_items (tipo_item);

CREATE INDEX ix_silver_conclusion_items_termino
    ON silver_conclusion_items (termino_canonico);
```

### 3.2 Tabla propuesta: `dim_termino_conclusion` (catálogo)

```sql
CREATE TABLE dim_termino_conclusion (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_canonico     TEXT NOT NULL UNIQUE,        -- "nefropatía", "barro_biliar"
    terminos_match      TEXT NOT NULL,               -- JSON: ["nefropatía", "nefropatía bilateral"]
    tipo_item           TEXT NOT NULL,               -- DIAGNOSTICO|PATRON|ETIOLOGIA|NEGATIVO
    organo_asociado     TEXT,                        -- "riñón", "hígado", "vejiga", NULL
    categoria_clinica   TEXT,                        -- "RENAL", "HEPATICA", "VESICULA"
    sinonimos           TEXT,                        -- JSON: ["nefropatía", "nefropatia"]
    patron_extraccion   TEXT,                        -- regex principal
    activo              BOOLEAN NOT NULL DEFAULT 1,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 3.3 Tabla propuesta: `stg_conclusion_no_match`

Para auditoría de términos no matcheados (similar a `stg_valores_no_mapeados`):

```sql
CREATE TABLE stg_conclusion_no_match (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    conclusion_id       INTEGER NOT NULL,
    informe_id          INTEGER NOT NULL,
    texto_no_matcheado  TEXT NOT NULL,               -- texto que no matchea el catálogo
    tipo_no_match       TEXT NOT NULL,               -- "sin_terminos", "longitud_cero"
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Catálogo semilla (Fase 1)

**Total esperado**: ~80-100 términos canónicos.

### 4.1 Diagnósticos (~50 términos)

```python
DIAGNOSTICOS = {
    # RENAL (15)
    "nefropatía":          {"terminos": ["nefropatía", "nefropatia"], "organo": "riñón", "categoria": "RENAL"},
    "nefromegalia":        {"terminos": ["nefromegalia", "nefro megalia"], "organo": "riñón", "categoria": "RENAL"},
    "nefrocalcinosis":     {"terminos": ["nefrocalcinosis"], "organo": "riñón", "categoria": "RENAL"},
    "pielectasia":         {"terminos": ["pielectasia"], "organo": "riñón", "categoria": "RENAL"},
    "hidronefrosis":       {"terminos": ["hidronefrosis"], "organo": "riñón", "categoria": "RENAL"},
    "ectasia_pelvica":     {"terminos": ["ectasia pélvica", "ectasia pelvica"], "organo": "riñón", "categoria": "RENAL"},
    "dilatación_ureteral": {"terminos": ["dilatación ureteral", "dilatacion ureteral"], "organo": "uréter", "categoria": "RENAL"},

    # HEPÁTICA (10)
    "hepatomegalia":       {"terminos": ["hepatomegalia"], "organo": "hígado", "categoria": "HEPATICA"},
    "microhepatia":        {"terminos": ["microhepatia"], "organo": "hígado", "categoria": "HEPATICA"},
    "hepatopatía":         {"terminos": ["hepatopatía", "hepatopatia"], "organo": "hígado", "categoria": "HEPATICA"},
    "hepatopatía_vacuolar": {"terminos": ["hepatopatía vacuolar", "hepatopatia vacuolar"], "organo": "hígado", "categoria": "HEPATICA"},
    "hígado_graso":        {"terminos": ["hígado graso", "higado graso", "infiltración grasa", "infiltracion grasa"], "organo": "hígado", "categoria": "HEPATICA"},
    "amiloidosis":         {"terminos": ["amiloidosis", "amiloide"], "organo": "hígado", "categoria": "HEPATICA"},
    "cirrosis":            {"terminos": ["cirrosis"], "organo": "hígado", "categoria": "HEPATICA"},
    "fibrosis":            {"terminos": ["fibrosis"], "organo": "hígado", "categoria": "HEPATICA"},

    # ESPLÉNICA (5)
    "esplenomegalia":      {"terminos": ["esplenomegalia"], "organo": "bazo", "categoria": "ESPLENICA"},
    "nódulo_esplénico":    {"terminos": ["nódulo esplénico", "nodulo esplenico"], "organo": "bazo", "categoria": "ESPLENICA"},
    "hematoma_esplénico":  {"terminos": ["hematoma esplénico"], "organo": "bazo", "categoria": "ESPLENICA"},

    # GASTROINTESTINAL (15)
    "gastritis":           {"terminos": ["gastritis"], "organo": "estómago", "categoria": "GASTROINTESTINAL"},
    "gastropatía":         {"terminos": ["gastropatía", "gastropatia"], "organo": "estómago", "categoria": "GASTROINTESTINAL"},
    "enteritis":           {"terminos": ["enteritis"], "organo": "intestino", "categoria": "GASTROINTESTINAL"},
    "enterocolitis":       {"terminos": ["enterocolitis"], "organo": "intestino", "categoria": "GASTROINTESTINAL"},
    "colitis":             {"terminos": ["colitis"], "organo": "colon", "categoria": "GASTROINTESTINAL"},
    "ileitis":             {"terminos": ["ileítis", "ileitis"], "organo": "íleon", "categoria": "GASTROINTESTINAL"},

    # PÁNCREAS (5)
    "pancreatitis":        {"terminos": ["pancreatitis"], "organo": "páncreas", "categoria": "PANCREATICA"},
    "cambios_pancreáticos": {"terminos": ["cambios pancreáticos", "cambios pancreaticos"], "organo": "páncreas", "categoria": "PANCREATICA"},

    # VESÍCULA BILIAR (5)
    "colecistitis":        {"terminos": ["colecistitis", "colicistitis"], "organo": "vesícula", "categoria": "VESICULA"},
    "barro_biliar":        {"terminos": ["barro biliar"], "organo": "vesícula", "categoria": "VESICULA"},
    "sedimento_biliar":    {"terminos": ["sedimento biliar"], "organo": "vesícula", "categoria": "VESICULA"},
    "colelitiasis":        {"terminos": ["colelitiasis"], "organo": "vesícula", "categoria": "VESICULA"},

    # VEJIGA Y URINARIO (5)
    "cistitis":            {"terminos": ["cistitis"], "organo": "vejiga", "categoria": "URINARIO"},
    "cistolito":           {"terminos": ["cistolito", "cálculo vesical", "calculo vesical"], "organo": "vejiga", "categoria": "URINARIO"},
    "sedimento_vejiga":    {"terminos": ["sedimento en vejiga", "sedimento vesical"], "organo": "vejiga", "categoria": "URINARIO"},
    "urolitiasis":         {"terminos": ["urolitiasis"], "organo": "vejiga", "categoria": "URINARIO"},

    # REPRODUCTIVO (10)
    "histeromegalia":      {"terminos": ["histeromegalia"], "organo": "útero", "categoria": "REPRODUCTIVO"},
    "piometra":            {"terminos": ["piometra"], "organo": "útero", "categoria": "REPRODUCTIVO"},
    "mucometra":           {"terminos": ["mucometra"], "organo": "útero", "categoria": "REPRODUCTIVO"},
    "hemometra":           {"terminos": ["hemometra"], "organo": "útero", "categoria": "REPRODUCTIVO"},
    "prostatomegalia":     {"terminos": ["prostatomegalia"], "organo": "próstata", "categoria": "REPRODUCTIVO"},
    "prostatitis":         {"terminos": ["prostatitis"], "organo": "próstata", "categoria": "REPRODUCTIVO"},
    "hiperplasia_prostática": {"terminos": ["hiperplasia prostática"], "organo": "próstata", "categoria": "REPRODUCTIVO"},
    "quisteovárico":       {"terminos": ["quiste ovárico", "quiste ovarico"], "organo": "ovario", "categoria": "REPRODUCTIVO"},
    "gestación":           {"terminos": ["gestación", "gestacion", "preñez", "preñez", "embarazo"], "organo": "útero", "categoria": "REPRODUCTIVO"},

    # ADRENALES (3)
    "adrenomegalia":       {"terminos": ["adrenomegalia", "adrenalomegalia"], "organo": "adrenal", "categoria": "ENDOCRINO"},

    # LINFÁTICO (3)
    "linfadenomegalia":    {"terminos": ["linfadenomegalia", "linfoadenopatía", "linfoadenopatia"], "organo": "linfonodo", "categoria": "LINFATICO"},

    # PERITONEO (2)
    "peritonitis":         {"terminos": ["peritonitis"], "organo": "peritoneo", "categoria": "PERITONEO"},
    "derrame_peritoneal":  {"terminos": ["derrame peritoneal", "líquido libre", "liquido libre", "ascitis"], "organo": "peritoneo", "categoria": "PERITONEO"},
}
```

### 4.2 Patrones (no son diagnósticos estrictos, hallazgos ecográficos)

```python
PATRONES = {
    "neoplasia":           {"terminos": ["neoplasia"], "categoria": "NEOPLASIA"},
    "masa":                {"terminos": ["masa", "masas"], "categoria": "MASA"},
    "nódulo":              {"terminos": ["nódulo", "nodulo"], "categoria": "NODULO"},
    "lesión":              {"terminos": ["lesión", "lesion"], "categoria": "LESION"},
    "quiste":              {"terminos": ["quiste", "quistes"], "categoria": "QUISTE"},
    "estenosis":           {"terminos": ["estenosis"], "categoria": "ESTENOSIS"},
    "obstrucción":         {"terminos": ["obstrucción", "obstruccion"], "categoria": "OBSTRUCCION"},
    "ectasia":             {"terminos": ["ectasia"], "categoria": "ECTASIA"},
    "dilatación":          {"terminos": ["dilatación", "dilatacion"], "categoria": "DILATACION"},
    "mineralización":      {"terminos": ["mineralización", "mineralizacion"], "categoria": "MINERALIZACION"},
    "litiasis":            {"terminos": ["litiasis"], "categoria": "LITIASIS"},
    "cálculo":             {"terminos": ["cálculo", "calculo", "cálculos", "calculos"], "categoria": "CALCULO"},
}
```

### 4.3 Etiologías

```python
ETIOLOGIAS = {
    "sospecha_inflamatoria":   {"terminos": ["aspecto inflamatorio"], "categoria": "INFLAMATORIA"},
    "sospecha_neoplásica":     {"terminos": ["aspecto neoplásico", "sugerente de neoplasia"], "categoria": "NEOPLASIA"},
    "sospecha_infecciosa":     {"terminos": ["infecciosa", "infeccioso"], "categoria": "INFECCIOSA"},
}
```

### 4.4 Negativos

```python
NEGATIVOS = {
    "sin_alteraciones":  {"terminos": ["no se observan alteraciones", "sin alteraciones"], "categoria": "NORMAL"},
    "sin_cambios":       {"terminos": ["sin cambios patológicos", "sin cambios"], "categoria": "NORMAL"},
    "sin_hallazgos":     {"terminos": ["sin hallazgos"], "categoria": "NORMAL"},
    "dentro_de_límites": {"terminos": ["dentro de límites", "dentro de parámetros"], "categoria": "NORMAL"},
    "normal":            {"terminos": ["normal"], "categoria": "NORMAL"},  # sólo si la conclusión es 100% "normal"
}
```

---

## 5. Extracción (rule-based, NO LLM)

### 5.1 Pipeline

```
conclusión_texto (string)
   │
   ├─ 1. Limpieza
   │     - strip whitespace, lowercase? (no, preservar acentos)
   │     - normalizar comillas, guiones
   │
   ├─ 2. Split por oraciones (heurística: split por "." + manejar abreviaturas)
   │
   ├─ 3. Por cada oración:
   │     - Aplicar regex del catálogo de DIAGNOSTICOS + PATRONES + ETIOLOGIAS
   │     - Si no matchea ninguno, intentar regex de NEGATIVOS
   │     - Extraer modificadores adyacentes:
   │         * intensidad: window ±3 palabras desde match
   │         * certeza: "sugerente de", "compatible con", "probable"
   │         * temporal: "crónico", "agudo"
   │         * lateralidad: "bilateral", "izquierdo", "derecho"
   │
   └─ 4. Generar silver_conclusion_items rows
         - Si 0 matches, INSERT en stg_conclusion_no_match
```

### 5.2 Algoritmo de extracción

```python
def extract_items(conclusion_text: str, catalogo: dict) -> list[dict]:
    """Devuelve lista de items extraídos."""
    items = []
    texto_lower = conclusion_text.lower()

    for canonico, spec in catalogo.items():
        for termino in spec["terminos"]:
            patron = re.compile(r'\b' + re.escape(termino) + r'\b', re.IGNORECASE)
            for match in patron.finditer(texto_lower):
                # Contexto: ventana ±50 chars
                ctx_start = max(0, match.start() - 50)
                ctx_end = min(len(conclusion_text), match.end() + 50)
                contexto = conclusion_text[ctx_start:ctx_end]

                # Extraer modificadores
                intensidad = _extract_intensidad(contexto)
                certeza = _extract_certeza(contexto)
                lateralidad = _extract_lateralidad(contexto)

                items.append({
                    "tipo_item": spec["tipo"],
                    "termino_detectado": match.group(0),
                    "termino_canonico": canonico,
                    "organo_asociado": spec.get("organo"),
                    "categoria_clinica": spec.get("categoria"),
                    "modificador_intensidad": intensidad,
                    "modificador_certeza": certeza,
                    "lateralidad": lateralidad,
                    "confianza": 1.0 if match.exact else 0.95,
                    "texto_match": match.group(0),
                    "pos_inicio": match.start(),
                    "pos_fin": match.end(),
                })

    # Deduplicar por (pos_inicio, termino_canonico)
    items = _dedupe_items(items)
    return items
```

### 5.3 Extracción de modificadores (regex)

```python
INTENSIDAD = {
    r'\bleve\b': 'leve',
    r'\bmoderad[oa]\b': 'moderada',
    r'\bsever[oa]\b': 'severa',
    r'\bagud[oa]\b': 'aguda',  # también es temporal
}

CERTEZA = {
    r'\bsugerente\s+(de|del)\b': 'sugerente',
    r'\bcompatible\s+con\b': 'compatible',
    r'\bprobable\b': 'probable',
    r'\bposible\b': 'posible',
    r'\bdescartar?\b': 'descartado',  # "se descart[óó]..."
}

LATERALIDAD = {
    r'\bbilateral(es?)?\b': 'bilateral',
    r'\bizquierd[oa]\b': 'izquierdo',
    r'\bderech[oa]\b': 'derecho',
    r'\bamb[oa]s\b': 'bilateral',
}
```

---

## 6. Cobertura esperada

Estimaciones basadas en el perfil del corpus:

| Métrica | Estimación | Método |
|---|---|---|
| Conclusiones con ≥1 item | ~85% (2,460 / 2,893) | Catálogo cubre top 40 términos = ~85% freq acumulada |
| Items totales esperados | ~6,000-8,000 | avg 2.5 items/conclusión × 2,460 |
| Cobertura por término top-1 (nefropatía) | 1,602 items | match directo |
| Cobertura por término top-10 | ~5,500 items | acumulado |
| Conclusiones en `stg_conclusion_no_match` | ~15% (430) | las que no matchean ningún término |

### 6.1 Validación

Para validar cobertura:
```sql
-- Conclusiones con al menos 1 item extraído
SELECT COUNT(DISTINCT conclusion_id)
FROM silver_conclusion_items;

-- Items promedio por conclusión
SELECT AVG(items_per_conclusion) FROM (
  SELECT conclusion_id, COUNT(*) AS items_per_conclusion
  FROM silver_conclusion_items GROUP BY conclusion_id
);

-- Conclusiones sin items
SELECT COUNT(*) FROM raw.conclusiones c
WHERE NOT EXISTS (
  SELECT 1 FROM silver_conclusion_items sci
  WHERE sci.conclusion_id = c.id
);
```

**Criterio GO F5**: ≥85% de conclusiones con al menos 1 item extraído.

---

## 7. Plan de implementación

### 7.1 Estructura de archivos

```
src/informes_vet/
  silver_f5_conclusions.py       # módulo principal F5
  catalog/
    conclusion_terms.py          # catálogo semilla (DIAGNOSTICOS, PATRONES, etc.)

scripts/
  build_silver.py                # +--phase f5
  verify_silver_f5.py            # 8-10 checks automatizados
  audit_f5_conclusions.py        # auditoría previa (perfil corpus)

docs/
  F5_DESIGN_SILVER_CONCLUSION_ITEMS.md  # este doc
  F5_CATALOG_REVIEW.md                  # revisión del catálogo
  F5_IMPLEMENTATION_REPORT.md           # reporte post-implementación
```

### 7.2 Fases

| # | Fase | Tarea | Salida |
|---|---|---|---|
| 1 | F5.0 | Auditoría previa del corpus | `audit_f5_conclusions.py` ejecutable |
| 2 | F5.1 | Catálogo semilla (80-100 términos) | `conclusion_terms.py` |
| 3 | F5.2 | Schema SQL (migración silver_db) | 3 tablas nuevas |
| 4 | F5.3 | Extractor rule-based | `silver_f5_conclusions.py` con `extract_items()` |
| 5 | F5.4 | Build CLI | `build_silver.py --phase f5` |
| 6 | F5.5 | Verificación | `verify_silver_f5.py` con ≥10 checks |
| 7 | F5.6 | Reporte + veredicto GO/NO-GO | `F5_IMPLEMENTATION_REPORT.md` |

### 7.3 Orden de dependencias

```
F4 (dim_valor_atributo) ← YA cerrado
  ↓
F5.0 (auditoría corpus) ← profile del corpus ya está en §2
  ↓
F5.1 (catálogo semilla) ← basado en §2.2
  ↓
F5.2 (schema) ← §3
  ↓
F5.3 (extractor) ← §5
  ↓
F5.4 (build CLI)
  ↓
F5.5 (verificación) ← §6
  ↓
F5.6 (reporte) ← veredicto GO/NO-GO
```

---

## 8. Riesgos y mitigaciones

### 8.1 Términos no cubiertos por el catálogo

**Riesgo**: Hay ~15% de conclusiones con términos diagnósticos que
no están en el catálogo.

**Mitigación**:
- Revisar manualmente las ~430 conclusiones en `stg_conclusion_no_match`.
- Iterar el catálogo.
- Decisión de GO: 85% de cobertura es aceptable para F5 v1.0.

### 8.2 Falsos positivos por regex parcial

**Riesgo**: "nefrocalcinosis" contiene "nefro" → matchea como "nefro*".

**Mitigación**:
- Orden de evaluación: matching más específico primero (longest match wins).
- Regex con word boundaries (`\b`).
- Deduplicación por posición: si dos matches se solapan, priorizar el más largo.

### 8.3 Ambigüedad de contexto

**Riesgo**: "descartar obstrucción" — ¿es un hallazgo o un descarte?

**Mitigación**:
- Detectar "descartar" como certeza `descartado` con confianza <1.0.
- Mantener el término (obstrucción) como `tipo_item=PATRON` con modificador_certeza="descartado".

### 8.4 Modificadores lejanos

**Riesgo**: "nefropatía bilateral leve de aspecto inflamatorio" →
"leve" está adyacente pero "bilateral" precede. ¿Ventana de ±3 palabras
es suficiente?

**Mitigación**:
- Usar ventana ±50 chars (más permisiva).
- Priorizar modificadores que aparecen en la misma oración (split por ".").

### 8.5 Conclusiones multi-ítem con modificadores compartidos

**Riesgo**: "Gastritis y colitis leves" — "leves" se aplica a ambos.

**Mitigación**:
- Asignar "leve" a cada ítem detectado en la oración.
- Documentar como heurística (no hay forma determinística de saber si
  "leve" aplica a uno o ambos sin NLP).

### 8.6 Idempotencia y migraciones

**Riesgo**: Cambios al catálogo en iteraciones futuras deben ser
idempotentes (no duplicar items).

**Mitigación**:
- UNIQUE INDEX (conclusion_id, pos_inicio, termino_detectado) previene duplicados.
- UPSERT (INSERT ... ON CONFLICT DO NOTHING) en el extractor.

---

## 9. Salidas esperadas (post-implementación)

### 9.1 Métricas

| Métrica | Estimación |
|---|---|
| Total items en `silver_conclusion_items` | ~6,500 |
| Conclusiones con ≥1 item | ~85% (2,460) |
| Items/conclusión (avg) | ~2.5 |
| Términos canónicos en `dim_termino_conclusion` | ~80 |
| Conclusiones sin match | ~430 |

### 9.2 Queries típicas Gold-ready

```sql
-- Top 10 diagnósticos por especie
SELECT sci.termino_canonico, COUNT(*) AS n
FROM silver_conclusion_items sci
JOIN silver_informes si ON si.informe_id = sci.informe_id
JOIN dim_especie de ON de.id = si.dim_especie_id
GROUP BY sci.termino_canonico
ORDER BY n DESC LIMIT 10;

-- Prevalencia de nefropatía bilateral por especie/edad
SELECT de.nombre_canonico AS especie,
       dec.nombre AS edad_cat,
       COUNT(*) AS n,
       SUM(CASE WHEN sci.lateralidad = 'bilateral' THEN 1 ELSE 0 END) AS bilateral,
       SUM(CASE WHEN sci.modificador_intensidad = 'leve' THEN 1 ELSE 0 END) AS leve,
       SUM(CASE WHEN sci.modificador_intensidad = 'severa' THEN 1 ELSE 0 END) AS severa
FROM silver_conclusion_items sci
JOIN silver_informes si ON si.informe_id = sci.informe_id
JOIN dim_especie de ON de.id = si.dim_especie_id
LEFT JOIN dim_edad_categoria dec ON dec.id = si.dim_edad_categoria_id
WHERE sci.termino_canonico = 'nefropatía'
GROUP BY de.nombre_canonico, dec.nombre
ORDER BY n DESC;

-- Casos con sospecha vs diagnóstico confirmado
SELECT sci.termino_canonico,
       sci.modificador_certeza,
       COUNT(*) AS n
FROM silver_conclusion_items sci
WHERE sci.modificador_certeza IS NOT NULL
GROUP BY sci.termino_canonico, sci.modificador_certeza
ORDER BY n DESC;
```

---

## 10. Decisiones pendientes (para revisión)

| # | Decisión | Propuesta | Alternativa |
|---|---|---|---|
| 1 | ¿Conclusiones vacías / NULL怎么处理? | Saltar (no insertar item) | INSERT NULL en silver_conclusion_items |
| 2 | ¿Multi-match en misma posición? | Longest match wins | Sumar ambos |
| 3 | ¿"normal" como término? | Sí, pero solo si conclusión entera es "normal" | Solo en NEGATIVOS |
| 4 | ¿Limpiar acentos en matching? | NO preservar tildes | Normalizar (nefropatía = nefropatia) |
| 5 | ¿Window para modificadores? | ±50 chars | ±3 palabras |
| 6 | ¿Catalogar sinonimos en tabla? | Sí, JSON column | Tabla separada map_termino_sinonimo |
| 7 | ¿Detalle de F5.5 (verificación)? | 10 checks: cobertura, unicidad, FK, idempotencia, distribuciones | Más estricto |

---

## 11. Cierre

**Diseño completo**: pendiente de aprobación.

**No se ejecuta implementación** hasta que se valide:
1. ✅ Catálogo semilla aceptable
2. ✅ Schema SQL correcto
3. ✅ Pipeline de extracción razonable
4. ✅ Criterios GO alineados

Tras aprobación, implementación en 5-6 horas (estimación):
- F5.0 ya completo (perfil §2).
- F5.1 catálogo: 1h.
- F5.2 schema: 30min.
- F5.3 extractor: 2h.
- F5.4 build CLI: 30min.
- F5.5 verificación: 1h.
- F5.6 reporte: 30min.
