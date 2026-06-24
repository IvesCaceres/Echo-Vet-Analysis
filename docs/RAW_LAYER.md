# Capa RAW — Documentación técnica

**Versión:** 2026-06-17 (post-reingesta SQLite + PostgreSQL)
**Propósito:** documentar completamente la capa `veterinaria_raw` para que pueda entenderse y reconstruirse sin revisar el código fuente.

---

## Índice

1. [Esquema completo de tablas](#1-esquema-completo-de-tablas)
2. [Diccionario de datos](#2-diccionario-de-datos)
3. [Reglas de normalización implementadas](#3-reglas-de-normalización-implementadas)
4. [Métricas finales de producción](#4-métricas-finales-de-producción)
5. [Diagrama lógico de relaciones](#5-diagrama-lógico-de-relaciones)
6. [Limitaciones conocidas y decisiones de diseño](#6-limitaciones-conocidas-y-decisiones-de-diseño)
7. [Recomendaciones para `veterinaria_analytics`](#7-recomendaciones-para-veterinaria_analytics)

---

## 1. Esquema completo de tablas

La capa RAW está compuesta por **5 tablas** dentro del esquema `public` (PostgreSQL) o del archivo `informes.db` (SQLite). El esquema es **idempotente y recreable** mediante `python scripts/run_ingest.py --db {sqlite|postgres} --reset`.

### 1.1 `informes`

Cabecera del informe. Una fila por archivo `.docx` procesado con éxito.

| Columna | Tipo SQL | Constraints | Notas |
|---|---|---|---|
| `id` | INTEGER | PK, autoincrement | Asignado al insertar |
| `archivo` | VARCHAR(512) | NOT NULL | basename (ej. `"Tonka, Particular.docx"`) |
| `ruta_relativa` | VARCHAR(1024) | NOT NULL | path POSIX desde la raíz del proyecto |
| `anio` | INTEGER | NOT NULL, INDEX | derivado de la carpeta `Ecografía YYYY/` |
| `sha256` | VARCHAR(64) | NOT NULL, **UNIQUE**, INDEX | clave de idempotencia |
| `nombre` | VARCHAR(255) |  | mascota |
| `especie` | VARCHAR(128) |  |  |
| `raza` | VARCHAR(255) |  |  |
| `genero` | VARCHAR(64) |  | "Hembra" / "Macho" |
| `edad` | VARCHAR(64) |  | tal cual aparece |
| `peso` | VARCHAR(64) |  |  |
| `tutor` | VARCHAR(255) |  |  |
| `doctor_solicitante` | VARCHAR(255) |  |  |
| `fecha` | VARCHAR(128) |  | fecha del estudio, formato variable |
| `antecedentes` | TEXT |  |  |
| `motivo` | TEXT |  |  |
| `anamnesis` | TEXT |  |  |
| `n_ficha` | VARCHAR(64) |  | normalmente NULL en este corpus |
| `estudio` | VARCHAR(255) |  | "Abdominal" / "Gestacional" / etc. |
| `hallazgos_crudos` | TEXT |  | bloque hallazgos completo, pre-segmentación |
| `paciente_json` | TEXT |  | respaldo estructurado del bloque paciente |
| `ingested_at` | TIMESTAMP | server_default NOW() | cuándo se incorporó al sistema |

**Índices:** `id` (PK), `sha256` (UNIQUE), `anio`, `nombre`, `especie`.

### 1.2 `hallazgos`

Un informe abdominal estándar produce **~10 hallazgos** (uno por órgano canónico). Los gestacionales y otros producen 1 hallazgo (`Gestación`).

| Columna | Tipo SQL | Constraints | Notas |
|---|---|---|---|
| `id` | INTEGER | PK, autoincrement |  |
| `informe_id` | INTEGER | FK→`informes.id` ON DELETE CASCADE, NOT NULL, INDEX |  |
| `organo` | VARCHAR(64) | NOT NULL, INDEX | nombre canónico (15 valores) o `"Gestación"` |
| `descripcion` | TEXT | NOT NULL | texto del hallazgo |
| `estado` | VARCHAR(16) | INDEX | `normal` / `anormal` / `no_evaluado` |
| `orden` | INTEGER | NOT NULL, default 0 | posición en el documento original |
| `hallazgo_hash` | VARCHAR(64) | INDEX | SHA-256(`organo.lower() + descripcion`) |

**Índices:** `id` (PK), `informe_id`, `organo`, `estado`, `hallazgo_hash`.

### 1.3 `conclusiones`

Una fila por informe. **No se fragmenta** ni se aplica NLP al texto.

| Columna | Tipo SQL | Constraints | Notas |
|---|---|---|---|
| `id` | INTEGER | PK, autoincrement |  |
| `informe_id` | INTEGER | FK→`informes.id` ON DELETE CASCADE, NOT NULL, INDEX | ratio 1:1 con `informes` |
| `texto_completo` | TEXT | NOT NULL | bloque entero entre `Conclusiones Ecográficas:` y `Atte.` |
| `created_at` | TIMESTAMP | server_default NOW() |  |

**Índices:** `id` (PK), `informe_id`.

### 1.4 `errores_ingesta`

Auditoría de archivos que fallaron al parsear. **Vacía en el corpus actual** (0 errores).

| Columna | Tipo SQL | Constraints | Notas |
|---|---|---|---|
| `id` | INTEGER | PK, autoincrement |  |
| `archivo` | VARCHAR(512) |  | basename del .docx |
| `ruta` | VARCHAR(1024) |  | path completo |
| `error` | TEXT |  | tipo + mensaje |
| `traceback` | TEXT |  | traceback completo |
| `created_at` | TIMESTAMP | server_default NOW() |  |

### 1.5 `embeddings`

**Vacía en v1.** Estructura polimórfica para vectorización futura.

| Columna | Tipo SQL | Constraints | Notas |
|---|---|---|---|
| `id` | INTEGER | PK, autoincrement |  |
| `source_type` | VARCHAR(32) | NOT NULL, INDEX (compuesto) | `"hallazgo"` o `"conclusion"` |
| `source_id` | INTEGER | NOT NULL, INDEX (compuesto) | PK de la entidad vectorizada |
| `texto_original` | TEXT | NOT NULL | texto exacto enviado al modelo (auditoría, reindexación) |
| `modelo` | VARCHAR(64) | INDEX | ej. `"text-embedding-3-small"` |
| `dimension` | INTEGER |  | ej. 1536 |
| `vector_json` | JSON |  | lista de floats (NO pickle, NO LargeBinary) |
| `created_at` | TIMESTAMP | server_default NOW() |  |

**Índices:** `id` (PK), `(source_type, source_id)`, `modelo`.

**Decisión de diseño:** polimórfica por `(source_type, source_id)` y no FK dura, porque SQLite no soporta FK polimórficas y porque los embeddings pueden generarse sobre cualquier entidad textual.

---

## 2. Diccionario de datos

### 2.1 Tabla `informes`

| Campo | Tipo | Descripción | Ejemplo real |
|---|---|---|---|
| `id` | INTEGER | autoincrement | `2` |
| `archivo` | VARCHAR | basename del .docx | `"Tonka, Particular.docx"` |
| `ruta_relativa` | VARCHAR | path POSIX | `"C:/Proyectos python/.../Ecografía 2022/Tonka, Particular.docx"` |
| `anio` | INTEGER | carpeta de origen | `2022` |
| `sha256` | VARCHAR | hex SHA-256 del texto canónico | `"0a6fd51235c9ff99ebb8c7f11f094ad738f77699fe8552dc30c6d55eed690470"` |
| `nombre` | VARCHAR | mascota | `"Tonka"` |
| `especie` | VARCHAR | `"Canino"` / `"Felino"` | `"Canino"` |
| `raza` | VARCHAR | raza declarada | `"Terranova"` |
| `genero` | VARCHAR | macho/hembra/sexo | `"Hembra"` |
| `edad` | VARCHAR | tal cual aparece | `"7 años"` |
| `peso` | VARCHAR | puede ser NULL | `"28 kg"` o NULL |
| `tutor` | VARCHAR | dueño | `"Claudia Riedermann"` |
| `doctor_solicitante` | VARCHAR | médico derivador | `"Dr. Óscar Baeza"` |
| `fecha` | VARCHAR | fecha del estudio (formato libre) | `"15-03-2024"` |
| `antecedentes` | TEXT | antecedentes clínicos | `"Sin antecedentes."` |
| `motivo` | TEXT | motivo de consulta | `"Control de gestación."` |
| `anamnesis` | TEXT | anamnesis | `"..."` |
| `n_ficha` | VARCHAR | número de ficha (raras veces presente) | `"12345"` o NULL |
| `estudio` | VARCHAR | tipo de estudio | `"Abdominal"` |
| `hallazgos_crudos` | TEXT | texto completo del bloque hallazgos | `"Vejiga: ... Riñones: ..."` |
| `paciente_json` | TEXT | respaldo JSON del bloque paciente | `'{"nombre":"Tonka",...}'` |
| `ingested_at` | TIMESTAMP | cuándo se ingirió | `"2026-06-17 14:32:18"` |

### 2.2 Tabla `hallazgos`

| Campo | Tipo | Descripción | Ejemplo real |
|---|---|---|---|
| `id` | INTEGER | autoincrement | `1284` |
| `informe_id` | INTEGER | FK al informe padre | `2` |
| `organo` | VARCHAR | nombre canónico | `"Vejiga"` |
| `descripcion` | TEXT | texto del hallazgo | `"Vejiga semi pletórica con contenido anecoico, homogéneo, pared de bordes internos regulares y grosor conservado."` |
| `estado` | VARCHAR | clasificación | `"normal"` |
| `orden` | INTEGER | posición en el doc | `0` |
| `hallazgo_hash` | VARCHAR | SHA-256 deduplicación | `"fe4e181429027f8f964c47d37832d6203992ca17a72a7d20ce64ffc5bd8456d4"` |

### 2.3 Tabla `conclusiones`

| Campo | Tipo | Descripción | Ejemplo real |
|---|---|---|---|
| `id` | INTEGER | autoincrement | `1092` |
| `informe_id` | INTEGER | FK al informe padre | `2` |
| `texto_completo` | TEXT | bloque entero sin fragmentar | `"Nefropatía bilateral leve de aspecto inflamatorio. Histeromegalia sugerente de piometra."` |
| `created_at` | TIMESTAMP | timestamp de inserción | `"2026-06-17 14:32:19"` |

### 2.4 Tabla `errores_ingesta`

| Campo | Tipo | Descripción | Ejemplo real |
|---|---|---|---|
| `id` | INTEGER | autoincrement | (vacía en v1) |
| `archivo` | VARCHAR | basename | — |
| `ruta` | VARCHAR | path completo | — |
| `error` | TEXT | tipo + mensaje | — |
| `traceback` | TEXT | stacktrace | — |
| `created_at` | TIMESTAMP | timestamp | — |

### 2.5 Tabla `embeddings`

| Campo | Tipo | Descripción | Ejemplo real |
|---|---|---|---|
| `id` | INTEGER | autoincrement | (vacía en v1) |
| `source_type` | VARCHAR | `"hallazgo"` o `"conclusion"` | — |
| `source_id` | INTEGER | PK de la entidad | — |
| `texto_original` | TEXT | texto enviado al modelo | — |
| `modelo` | VARCHAR | nombre del modelo | — |
| `dimension` | INTEGER | dimensión del vector | — |
| `vector_json` | JSON | lista de floats | — |
| `created_at` | TIMESTAMP | timestamp | — |

---

## 3. Reglas de normalización implementadas

### 3.1 Catálogo canónico de órganos (15)

```
Vejiga, Próstata, Riñones, Bazo, Estómago, Hígado, Vesícula,
Intestino, Páncreas, Adrenales, Linfonodos, Cavidad abdominal,
Útero, Ovarios, Testículos
```

Más un **fallback**: `Gestación` (no es un órgano, sino el contenedor para informes que el parser no logra segmentar).

### 3.2 `ORGANS_SYNONYMS` — sinónimos aceptados

Mapeo `sinónimo → canónico`. La detección de sinónimos ocurre en la fase de parsing regex (extienden la lista de tokens reconocidos).

| Canónico | Sinónimos aceptados |
|---|---|
| `Riñones` | `Renal`, `Renales` |
| `Estómago` | `Estomago` (sin tilde) |

### 3.3 `ORGANS_ABSORBED` — variantes consolidadas

Mapeo `variante → canónico`. Se aplica **después** de la detección regex, normalizando el nombre capturado. Esto evita que existan múltiples filas en `hallazgos.organo` para lo que clínicamente es el mismo órgano.

| Variante detectada | → Canónico persistido |
|---|---|
| Yeyuno, Duodeno, Íleon, Ileon, Colon, Colón, Colon descendente, Colón descendente, Ciego, Recto, Intestino delgado | `Intestino` |
| Riñón, Rinon | `Riñones` |
| Vesícula biliar, Vesícula  biliar, Vesicula biliar, Vesicula  biliar, Vesicula | `Vesícula` |
| Testículo, Testiculo | `Testículos` |
| Ovario | `Ovarios` |
| Linfonodo | `Linfonodos` |
| Cuerpo uterino, Cuerpo  uterino | `Útero` |
| Glándula adrenal, Glándulas adrenales | `Adrenales` |

### 3.4 Fallback `Gestación`

Cuando el parser canónico **no detecta ningún órgano canónico** en el bloque de hallazgos, produce **un único hallazgo** con `organo = "Gestación"` y `descripcion = <texto crudo completo>`. Esto sucede en 200 informes (5.7% del corpus), correspondientes a:

- 118 gestacionales puros (texto describe gestación/fetos)
- 35 cervicales / tiroides
- 14 abdominales con contenido limitado
- 33 otros (rodilla, ojo, partes blandas, reproductivo, etc.)

### 3.5 Parser narrativo H3 (post-2026-06-17)

**Problema resuelto:** algunos informes abdominales describen hallazgos en prosa (sin el formato `Organo:`), p. ej. *"La vejiga se observa semi pletórica. Los riñones se observan en posición normal..."*. El parser canónico devolvía un único `Gestación` falso.

**Solución:** cuando el canónico devuelve **<5 hallazgos**, se activa un segmentador narrativo conservador que:

1. Localiza menciones de órganos con regex tolerante a mayúsculas y tildes alternativas:
   - `Riñ[oó]n(?:es)?`, `[Ee]st[oó]mago`, `[Hh][ií]gado`, `[Vv]es[ií]cula(?:\s+biliar)?`, `[Pp][aá]ncreas`, `[Úú]tero`, `[Pp]r[oó]stata`, `[Aa]drenales?|[Gg]l[aá]ndulas?\s+adrenales?`, `[Tt]est[ií]culos?`, `[Oo]varios?`, `[Ii]ntestino|[Yy]eyuno|[Dd]uodeno|[Ii]le[oó]n|[Cc]iego|[Cc]ol[oó]n(?:\s+descendente)?|[Rr]ecto`, `[Vv]ejiga`, `[Bb]azo`, `[Ll]infonodos?|[Gg]anglios?\s+linf[aá]ticos?`
2. **Requiere contexto clínico posterior** (palabra de prosa clínica de `_NARRATIVE_POST_PATTERNS`): `se observa`, `se aprecia`, `presenta`, `de aspecto`, etc. Sin este contexto, la mención se descarta.
3. Cada hallazgo cubre desde su mención hasta la siguiente mención de otro órgano.
4. Trunca descripciones a **600 caracteres** y descarta chunks <20 caracteres.
5. Requiere **mínimo 5 canónicos** para activarse (umbral conservador).

**Resultado:** 11 informes narrativos rescatados (5 H3 aprobados originalmente). Todos producen hallazgos con `organo` en el catálogo canónico de 15.

### 3.6 Salvaguarda gestacional

**Problema:** un informe gestacional que menciona brevemente un órgano fetal (ej. *"Riñón de fetos presenta clara delimitación"*) podría activar la narrativa H3 y recategorizar el informe como abdominal, perdiendo la etiqueta `Gestación`.

**Solución:** la narrativa H3 **NO se activa** si el campo `estudio` declarado en el DOCX contiene la palabra `estacional` (case-insensitive). Esto preserva la clasificación `Gestación` para informes gestacionales, incluso si el parser narrativo habría encontrado menciones.

La salvaguarda se basa en `estudio` (verdad declarada) y no en `organo='Gestación'` (ver heurística), porque los abdominales con contenido narrativo también producen `organo='Gestación'` por el fallback canónico y DEBEN ser mejorados por la narrativa.

### 3.7 `estudio` — heurística

```
si DOCX trae campo "Estudio":
    estudio = valor del campo (verdad declarada)
si no trae campo "Estudio":
    si no hay hallazgos canónicos O todos los hallazgos son 'Gestación':
        estudio = "Gestacional"
    si no:
        estudio = "Abdominal"
```

### 3.8 Clasificación de estado (`classify_state`)

Para cada hallazgo segmentado se asigna uno de tres estados:

| Estado | Criterio |
|---|---|
| `normal` | sin alertas, sin alertas de tamaño, o longitud del texto <50 chars y contiene "normal"/"conservado" |
| `anormal` | contiene al menos una alerta (`irregular`, `heterogéne`, `alterad`, `presencia de`, `lesión`, `masa`, `nódulo`, `lodo`, `sediment`, `reacción`, `efusión`, `líquido libre`, `urolito`, `arenilla`, `coleccion`, `reactiv`, `dilatad`, `proliferación`, `quiste`, `mineraliz`) **y** no está negada por contexto cercano (`no`, `sin`, `ausencia de`, `normal`, `conservado`) |
| `no_evaluado` | contiene `no evaluad`, `no se evalu`, `no visualiz` |

---

## 4. Métricas finales de producción

**Fecha de corte:** 2026-06-17. Datos medidos directamente sobre `informes.db` (SQLite) — `veterinaria_raw` en Postgres es bit-a-bit idéntico.

### 4.1 Conteos globales

| Métrica | Valor |
|---|---|
| Total informes | **2 893** |
| Total conclusiones | **2 893** |
| Total hallazgos | **27 866** |
| Total errores_ingesta | 0 |
| Total embeddings | 0 (vacía en v1) |
| Archivos .docx en disco (walker) | 2 927 |
| Archivos insertados | 2 893 (34 saltados por duplicado sha256) |
| Promedio hallazgos / informe | 9.63 |

### 4.2 Distribución por año

| Año | # informes |
|---|---|
| 2022 | 6 |
| 2023 | 477 |
| 2024 | 968 |
| 2025 | 1 102 |
| 2026 | 340 |
| **Total** | **2 893** |

### 4.3 Distribución por estudio declarado

| Estudio | # informes |
|---|---|
| Abdominal | 2 676 |
| Gestacional | 119 |
| Cervical | 35 |
| Abdominal. | 16 |
| Reproductivo | 14 |
| Partes blandas | 4 |
| Otros (rodilla, ojo, hombro, etc.) | 29 |

### 4.4 Distribución de hallazgos por órgano (top-16)

| Órgano | # hallazgos | # informes |
|---|---|---|
| Vejiga | 2 690 | 2 676 |
| Riñones | 2 688 | 2 675 |
| Estómago | 2 688 | 2 675 |
| Intestino | 2 688 | 2 675 |
| Páncreas | 2 688 | 2 675 |
| Hígado | 2 687 | 2 674 |
| Adrenales | 2 687 | 2 673 |
| Bazo | 2 684 | 2 670 |
| Linfonodos | 2 681 | 2 668 |
| Vesícula | 2 667 | 2 637 |
| Próstata | 737 | 737 |
| Gestación (fallback) | 200 | 200 |
| Útero | 49 | 49 |
| Testículos | 27 | 27 |
| Ovarios | 5 | 5 |
| Cavidad abdominal | 0 | 0 |

### 4.5 Distribución de hallazgos por estado

| Estado | # hallazgos | % |
|---|---|---|
| normal | 20 976 | 75.3% |
| anormal | 6 556 | 23.5% |
| no_evaluado | 334 | 1.2% |

### 4.6 Distribución percentiles de órganos por informe

```
Mínimo  : 1
P50     : 10
P90     : 11
P95     : 11
P99     : 11
Máximo  : 12
Promedio: 9.63
```

Moda: 10 órganos (1 893 informes, abdominales típicos completos).

---

## 5. Diagrama lógico de relaciones

```
┌─────────────────────────────────────────────────────────────────┐
│                      veterinaria_raw                            │
│                                                                 │
│  ┌─────────────────────────┐                                    │
│  │       informes          │                                    │
│  │─────────────────────────│                                    │
│  │ PK id                  │                                    │
│  │    archivo             │                                    │
│  │    ruta_relativa       │                                    │
│  │    anio                │                                    │
│  │ UQ sha256              │                                    │
│  │    nombre, especie,    │                                    │
│  │    raza, genero,       │                                    │
│  │    edad, peso,         │                                    │
│  │    tutor, doctor,      │                                    │
│  │    fecha, antecedentes,│                                    │
│  │    motivo, anamnesis,  │                                    │
│  │    n_ficha, estudio,   │                                    │
│  │    hallazgos_crudos    │                                    │
│  │    paciente_json       │                                    │
│  │    ingested_at         │                                    │
│  └──────────┬──────────────┘                                    │
│             │ 1                                                 │
│             │                                                   │
│             │ N                                                │
│  ┌──────────▼──────────────┐    ┌──────────────────────────┐   │
│  │       hallazgos         │    │      conclusiones         │   │
│  │─────────────────────────│    │──────────────────────────│   │
│  │ PK id                  │    │ PK id                    │   │
│  │ FK informe_id ─────────┼─┐  │ FK informe_id ───────────┼─┐ │
│  │    organo              │ │  │    texto_completo         │ │ │
│  │    descripcion         │ │  │    created_at             │ │ │
│  │    estado              │ │  └──────────────────────────┘ │ │
│  │    orden               │ │                                │ │
│  │    hallazgo_hash       │ │                                │ │
│  └────────────────────────┘ │                                │ │
│                              │                                │ │
│  ┌─────────────────────────┐ │  ┌──────────────────────────┐ │ │
│  │   errores_ingesta       │ │  │       embeddings          │ │ │
│  │─────────────────────────│ │  │──────────────────────────│ │ │
│  │ PK id                  │ │  │ PK id                    │ │ │
│  │    archivo, ruta       │ │  │    source_type            │ │ │
│  │    error, traceback    │ │  │    source_id ──── (polimór│ │ │
│  │    created_at          │ │  │    texto_original         │ │ │
│  │ (sin FK, errores son   │ │  │    modelo                 │ │ │
│  │  huérfanos intencional)│ │  │    dimension              │ │ │
│  └─────────────────────────┘ │  │    vector_json            │ │ │
│                              │  │    created_at             │ │ │
│                              │  │ (sin FK dura — polimorf)  │ │ │
│                              │  └──────────────────────────┘ │ │
│                              │                                │ │
└──────────────────────────────┼────────────────────────────────┘
                               │
                          ON DELETE CASCADE
                               │
              todas las hijas se borran con el padre
```

### Cardinalidades

- `informes` 1—N `hallazgos` (un informe produce 1-12 hallazgos; típico: 10)
- `informes` 1—1 `conclusiones` (ratio 1:1 estricto)
- `informes` 1—N `errores_ingesta` (posible, pero en v1: 0 filas)
- `hallazgos` o `conclusiones` 1—N `embeddings` (v1: 0 filas; polimórfica por `source_type` + `source_id`)

### Integridad referencial (validada 2026-06-17)

| Regla | Estado |
|---|---|
| `hallazgos.informe_id` ∈ `informes.id` | ✅ 0 huérfanos |
| `conclusiones.informe_id` ∈ `informes.id` | ✅ 0 huérfanas |
| `informes` con conclusión | ✅ 2 893 / 2 893 |
| `informes` con al menos 1 hallazgo | ✅ 2 893 / 2 893 |
| `conclusiones` 1:1 con `informes` | ✅ 0 informes con >1 conclusión |

---

## 6. Limitaciones conocidas y decisiones de diseño

### 6.1 Limitaciones del parser

1. **14 abdominales mal catalogados quedan como `Gestación`.** Sus textos describen regiones específicas (lumbar, subcutánea, mama, rodilla, perianal, cervical) sin usar formato `Organo:` ni prosa narrativa reconocible. No es un bug del parser — es información limitada en el DOCX original. Ver lista en §4 de la auditoría.

2. **26 informes con descripciones "No evaluado" repetidas.** Provienen de órganos listados sin descripción adicional en el DOCX. Son contenido del DOCX preservado por la filosofía RAW — se deduplicarán en `analytics`.

3. **Falsos negativos del parser narrativo en informes con texto corto.** Caso notorio: `id=2215 Kalú Rucalaf control 1` tiene texto `"Colon... Estómago, duodeno yeyuno..."` sin formato `Organo:`. El umbral de 5 hallazgos canónicos para activar narrativa no aplica aquí porque hay 0 canónicos, pero la narrativa tampoco dispara (probablemente porque no encuentra contexto clínico post-mención).

4. **`hallazgo_hash` no es UNIQUE.** Dos informes diferentes pueden tener hallazgos con descripción idéntica — esto es esperable (muchos informes tienen hallazgos rutinarios como "Bazo: Imagen esplénica de tamaño y forma normales..."). El índice sirve para búsqueda rápida, no para unicidad.

5. **Clasificación de estado imperfecta para chunks narrativos largos.** El `classify_state` fue diseñado para chunks canónicos cortos; cuando la narrativa produce chunks de 200-600 caracteres que abarcan múltiples oraciones, la detección de negaciones por ventana de 40 caracteres puede fallar. Aceptado como trade-off del parser conservador.

### 6.2 Decisiones de diseño explícitas

| Decisión | Justificación |
|---|---|
| **`paciente_json` además de columnas estructuradas** | Respaldo permanente de la extracción. Si se modifica el esquema, regenerar con `--reset` y ambos quedan en sync. |
| **`hallazgos_crudos` además de `hallazgos.descripcion`** | Permite resegmentar sin re-parsear el DOCX. Útil para comparar algoritmos de segmentación. |
| **`conclusiones` no se fragmenta** | NLP sobre conclusiones es responsabilidad de `analytics`. RAW preserva el bloque entero. |
| **`embeddings` con `texto_original` obligatorio** | Permite reindexar con un modelo distinto sin re-parsear DOCX. Auditable. |
| **`embeddings` polimórfica sin FK dura** | SQLite no soporta FK polimórficas. La integridad se valida en aplicación. |
| **`estudio` se re-deriva por heurística si el DOCX no lo trae** | El campo "Estudio" del DOCX es la verdad; si falta, inferencia por contenido. |
| **DENYLIST por path completo en `docx_io.py`** | 2 archivos quedaron locked por Windows al moverlos a purgatorio. La denylist garantiza que no vuelvan a aparecer en reingestas futuras. |
| **`--reset` transaccional** | DROP + CREATE en una sola transacción atómica. Si la conexión falla, el COMMIT no ocurre y la BD queda intacta. |

### 6.3 Datos no capturados

- **Imágenes embebidas en los .docx** — descartadas en `hashutil.canonical_text` (no afectan al texto clínico).
- **Medios (video, audio)** — no aplica al corpus (solo texto + imágenes).
- **Estilo/ formato del documento original** — solo se extrae texto.
- **Errores tipográficos médicos** — se preservan tal cual ("hiperecoica" vs "hiperecoico", etc.).
- **Versiones anteriores del informe** — el corpus no tiene versionado.

### 6.4 Catálogo cerrado

Los 15 órganos canónicos son **cerrados** para v1. Cualquier mención fuera del catálogo se conserva en `hallazgos_crudos` para procesamiento futuro en `analytics`, pero **no se persiste como hallazgo separado**.

---

## 7. Recomendaciones para `veterinaria_analytics`

La capa `veterinaria_analytics` debe construirse **leyendo desde `veterinaria_raw`** (no modificándola) y normalizando los datos para análisis clínico, Power BI y ML.

### 7.1 Normalizaciones recomendadas

| Campo RAW | Normalización sugerida | Tabla analytics |
|---|---|---|
| `informes.especie` | lower + strip + catálogo (`canino`, `felino`, …) | `dim_especie` |
| `informes.genero` | lower + mapear variantes (`Hembra`/`Macho`/`Sexo`/`F`/`M`) | `dim_genero` |
| `informes.edad` | parsear a meses (regex sobre `"7 años"` → `84`) | `dim_paciente.edad_meses` |
| `informes.peso` | parsear a kg (regex sobre `"28 kg"` → `28.0`) | `dim_paciente.peso_kg` |
| `hallazgos.organo` | ya canónico (15 valores + `Gestación`) | 그대로 |
| `hallazgos.estado` | ya canónico | 그대로 |
| `hallazgos.descripcion` | extraer atributos clínicos (tamaño, ecogenicidad, bordes) | `analytics_organo_atributos` |
| `informes.fecha` | parsear a DATE | `dim_tiempo` |

### 7.2 Tablas sugeridas para v1.5

- **`dim_paciente`** (paciente × especie × raza × edad × peso × tutor)
- **`dim_tiempo`** (fecha del estudio, año, mes, trimestre, estación)
- **`dim_veterinaria`** (clínica extraída de `ruta_relativa`)
- **`fact_hallazgo`** (1 fila por hallazgo con FK a dims + métricas)
- **`fact_conclusion`** (1 fila por conclusión con FK a dims + métricas NLP)
- **`analytics_organo_atributos`** (tamaño, ecogenicidad, bordes, contenido, paredes, márgenes) — alimentada por extractor NLP sobre `descripcion`
- **`diccionario_especies`**, **`diccionario_organos`**, **`diccionario_patologias`**, **`diccionario_diagnosticos`** — catálogos para mapear variantes

### 7.3 Decisiones a tomar antes de construir

1. **Persistencia de analytics:** ¿nueva BD (`veterinaria_analytics`) o schema separado en el mismo Postgres? Recomendación: **nueva BD** o schema, para mantener RAW intacta.
2. **Deduplicación de "No evaluado":** aplicar en `analytics` como limpieza, no en RAW.
3. **Detección de duplicados entre informes:** usar `hallazgo_hash` para agrupar descripciones idénticas a través de informes — útil para epidemiología (cuántos perros presentan el mismo hallazgo).
4. **NLP sobre `descripcion`:** considerar spaCy con modelo en español o reglas regex para extraer atributos (`aumentado de tamaño`, `ecogenicidad aumentada`, `bordes irregulares`, etc.). Mínimo viable: regex por atributo × valor.
5. **NLP sobre `conclusiones_texto`:** fragmentar en oraciones, mapear a hallazgos vinculados si es posible.
6. **Manejo de los 14 abdominales con `Gestación` falso:** decidir si se reclasifican manualmente o se aceptan como cobertura parcial.

### 7.4 Métricas target para `analytics`

- Cobertura de catálogo de órganos: **98.1%** (2 676 / 2 727 abdominales típicos)
- % informes con al menos 1 hallazgo `anormal`: ~22% (provisional, validar)
- % informes con conclusión `anormal` detectable por NLP: TBD

### 7.5 Riesgos identificados

1. **El campo `estudio` es inconsistente** (variantes: `"Abdominal"`, `"Abdominal."`, `"abdominal"`, `"Abdominal/reproductivo"`, etc.). En `analytics`, normalizar a un set cerrado de ~10 valores antes de cualquier JOIN.
2. **El campo `fecha` es texto libre** — los médicos escriben fechas en formatos distintos. Necesita parser robusto antes de análisis temporal.
3. **`hallazgos.descripcion` no está normalizado** — usa sinónimos, abreviaciones y español clínico variable. Cualquier análisis textual requiere un diccionario de sinónimos o embeddings.
4. **El parser es RAW, no clínico** — no debe interpretarse como verdad diagnóstica. La limpieza clínica debe ocurrir en `analytics` o en `features`.

### 7.6 Próximo paso recomendado

Construir `analytics.py` (módulo) + `scripts/build_analytics.py` que:

1. Lee `veterinaria_raw` completa vía SQLAlchemy.
2. Construye DataFrames de Pandas normalizados.
3. Aplica las normalizaciones descritas en §7.1.
4. Persiste en `veterinaria_analytics` (nueva BD o schema).
5. Genera reporte de cobertura y métricas de calidad.

---

**Fin del documento.**

Para reconstruir esta capa desde cero:

```bash
# 1. Crear venv e instalar deps
python -m venv venvvector
source venvvector/Scripts/activate  # o venvvector\Scripts\activate en Windows
pip install -r requirements.txt

# 2. Configurar .env (PG_DSN)
cp .env.example .env
# editar .env con credenciales reales

# 3. Ingerir
python scripts/run_ingest.py --db sqlite --reset
python scripts/run_ingest.py --db postgres --reset

# 4. Validar (consultas en §5 del plan maestro)
```

Rollback completo disponible en:

| Componente | Ubicación |
|---|---|
| Código fuente | `backup-20260617/{src,scripts,tests}/` |
| SQLite previo | `backup-20260617/informes.db` (21 MB) |
| Postgres previo | `snapshots/pg_pre_reset_20260617_095555.dump` (2.3 MB) |
| Archivos purgados | `_purgatorio/{Mike, Olga}.docx` |
| Denylist | `src/informes_vet/docx_io.py:DENYLIST` |
