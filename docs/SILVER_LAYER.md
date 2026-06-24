# Capa SILVER — Diseño técnico (versión final)

**Versión:** 2026-06-19 (versión final aprobada)
**Estado:** ✅ diseño locked
**Audiencia:** arquitecto de datos + implementador
**Predecesor:** `docs/RAW_LAYER.md` (cerrada y congelada)

---

## Índice

0. [Resumen ejecutivo](#0-resumen-ejecutivo)
1. [Arquitectura propuesta](#1-arquitectura-propuesta)
2. [Diagrama de flujo](#2-diagrama-de-flujo)
3. [Tablas Silver (facts)](#3-tablas-silver-facts)
4. [Dimensiones](#4-dimensiones)
5. [Tablas de mapeo](#5-tablas-de-mapeo)
6. [Tablas staging](#6-tablas-staging)
7. [Tabla de auditoría](#7-tabla-de-auditoría)
8. [Estrategia de normalización](#8-estrategia-de-normalización)
9. [Estrategia de gobernanza de catálogos](#9-estrategia-de-gobernanza-de-catálogos)
10. [Orden de implementación por fases](#10-orden-de-implementación-por-fases)
11. [Registro de decisiones arquitectónicas](#11-registro-de-decisiones-arquitectónicas)
12. [Riesgos](#12-riesgos)
13. [Anexo A: `dim_atributo` y `dim_organo_atributo` (catálogo clínico)](#13-anexo-a-dim_atributo-y-dim_organo_atributo-catálogo-clínico)
14. [Anexo B: `silver_conclusion_items` con `tipo_item`](#14-anexo-b-silver_conclusion_items-con-tipo_item)

---

## 0. Resumen ejecutivo

La capa **SILVER** transforma la capa RAW en datos **trusted, normalizados y trazables**. La estructura clínica del corpus se modela como **Órgano → atributo → valor → conclusión**, sin romper la separación entre hallazgos (observaciones ecográficas) y conclusiones (interpretaciones clínicas).

### 0.1 Decisiones arquitectónicas locked

| # | Decisión | Justificación |
|---|---|---|
| D1 | `silver.db` separado de `informes.db` (SQLite, misma raíz) | RAW intocable; reset de Silver barato. |
| D2 | `silver_conclusion_items` referencia `informe_id` lógicamente; texto vive en RAW | Sin duplicación; trazabilidad por JOIN O(1). |
| D3 | `dim_atributo` organo-AGNÓSTICA (22 filas) + `dim_organo_atributo` junction (57 filas) | "tamaño" se reutiliza entre órganos; metadatos clínicos van en el par. |
| D4 | `silver_conclusion_items.termino_canonico` es TEXTO, no FK | Sin governance de dim_diagnostico en v1. Normalización por función pura. |
| D5 | `silver_conclusion_items.tipo_item` clasifica `diagnostico` / `patron` / `etiologia` | Una conclusión mezcla las 3 categorías; el campo permite filtrar y graficar. |
| D6 | `silver_metricas_informe` **diferido** | Corpus pequeño; queries de agregación <50ms. No justificado precomputar. |
| D7 | `stg_atributos_valores` + `map_atributo_valor` priorizados | Base de la normalización clínica futura. |
| D8 | `dim_diagnostico` **diferido** a fase futura | La estructura primaria del corpus es Órgano→Atributo→Valor, no Diagnóstico. |
| D9 | Extracción clínica por **regex**, no ML | Corpus pequeño y altamente templado. Cobertura >95% en 8 órganos. |
| D10 | `dim_sexo` y `dim_estado_reproductivo` separados | "Macho entero" combina dos cosas; cada una es dim propia. |
| D11 | Stack: SQLite + SQLAlchemy Core + scripts ETL | Paridad con RAW; ETL reproducible. |
| D12 | Idempotencia: re-ejecutar el ETL produce la misma Silver | Necesario para re-builds seguros. |

### 0.2 Inventario de tablas

```
FACTS              (4): silver_informes, silver_hallazgos, silver_atributos_hallazgo, silver_conclusion_items
DIMENSIONES        (10): dim_organo, dim_atributo, dim_organo_atributo, dim_especie, dim_raza,
                        dim_sexo, dim_estado_reproductivo, dim_estudio, dim_edad_categoria
                        (dim_diagnostico: diferido)
MAPEOS             (6): map_especie, map_raza, map_sexo, map_estado_reproductivo, map_estudio,
                        map_atributo_valor (PRIORIDAD)
STAGING            (3): stg_razas_detectadas, stg_especies_detectadas, stg_atributos_valores (PRIORIDAD)
AUDITORÍA          (1): silver_revision_log
```

**Total: 24 tablas en `silver.db`.**

### 0.3 Métricas target v1

| Métrica | Target | Crítico si no se cumple |
|---|---|---|
| Cobertura `silver_informes` sobre RAW | 100% (2.893/2.893) | Sí |
| Cobertura `silver_hallazgos` sobre RAW | 100% (27.866/27.866) | Sí |
| Hallazgos con ≥1 atributo extraído (Hígado/Riñones/Vejiga/Vesícula/Próstata/Bazo/Estómago/Intestino) | ≥95% | Sí |
| Conclusiones con ≥1 `silver_conclusion_items` detectado | ≥80% | No |
| Huérfanos de FK | 0 | Sí |
| Atributos sin `texto_original` | 0 | Sí |
| Items en `stg_atributos_valores` al cierre de v1 | <300 | No (gobierno) |
| Items en `stg_razas_detectadas` al cierre de v1 | <80 | No (gobierno) |

---

## 1. Arquitectura propuesta

### 1.1 Stack y ubicación

```
C:/Proyectos python/vectorizacion informes veterinarios/
├── informes.db          ← RAW (intacto, frozen)
├── silver.db            ← SILVER (nuevo, recreable)
├── src/informes_vet/
│   ├── models.py          ← modelo RAW (no se toca)
│   ├── models_silver.py   ← NUEVO: esquema SQLAlchemy Core para Silver
│   ├── extract.py         ← parser DOCX (no se toca)
│   ├── organs.py          ← órganos canónicos (no se toca)
│   ├── silver_etl.py      ← NUEVO: ETL RAW → Silver
│   ├── silver_dims.py     ← NUEVO: bootstrap + seeds de dims
│   ├── silver_attr.py     ← NUEVO: extractor de atributos por regex
│   ├── silver_conc.py     ← NUEVO: extractor de items de conclusión
│   └── silver_review.py   ← NUEVO: CLI para stg_*
├── scripts/
│   ├── run_ingest.py      ← ingestión RAW (no se toca)
│   ├── build_silver.py    ← NUEVO: CLI orquestador
│   ├── review_silver.py   ← NUEVO: CLI para revisión de stg
│   └── inventory_silver.py ← NUEVO: herramienta de exploración
├── tests/
│   ├── test_7x7.py
│   ├── test_gestacional.py
│   └── test_silver_*.py   ← NUEVO: cobertura de extractores
└── docs/
    ├── RAW_LAYER.md
    └── SILVER_LAYER.md    ← este documento
```

### 1.2 Principios arquitectónicos

1. **RAW es sagrada.** Silver se reconstruye desde RAW. Cero `UPDATE` sobre `informes.db`.
2. **Idempotencia total.** Re-correr `build_silver.py` sobre la misma RAW produce la misma Silver.
3. **PK = FK al RAW.** `silver_*.informe_id` siempre es un `informes.id` válido (validado en build, no enforced por SQLite cross-DB).
4. **Atributos extraídos, no inferidos.** Cada valor en `silver_atributos_hallazgo` tiene un `texto_original` que lo respalda.
5. **Catálogo cerrado + cola abierta.** Dims inician con set cerrado. Valores nuevos van a `stg_atributos_valores` y se promueven manualmente.
6. **Sin ML en v1.** Todo es regex + diccionario. Auditable, ejecutable en CPU, replicable.
7. **Trazabilidad por JOIN, no por copia.** `silver_conclusion_items.informe_id` → `raw.informes.id` → `raw.conclusiones.texto_completo` (O(1)).

### 1.3 Físico vs lógico

Mismo proyecto, **dos archivos SQLite** (`informes.db` y `silver.db`). Las FKs cross-DB son **lógicas** (validadas en build por el ETL), no enforced por DDL.

Migración futura a Postgres: trivial. Cross-schema FKs (`silver.x.informe_id REFERENCES raw.informes(id)`) son nativas.

---

## 2. Diagrama de flujo

```
┌────────────────────────────────────────────────────────────────────────┐
│                         PIPELINE SILVER                               │
└────────────────────────────────────────────────────────────────────────┘

   ┌────────────────────────┐
   │  RAW (read-only)       │
   │  informes    2.893     │
   │  hallazgos  27.866     │
   │  conclusiones 2.893    │
   └────────────┬───────────┘
                │ SELECT
                ▼
   ┌────────────────────────────────────────────────────────┐
   │ FASE 1: BOOTSTRAP DIMS (idempotente)                   │
   │  - dim_organo           (15 + Gestación)               │
   │  - dim_atributo         (22 organo-agnósticos)         │
   │  - dim_organo_atributo  (57 pares con metadatos)       │
   │  - dim_especie          (9 canónicos)                  │
   │  - dim_raza             (80+ auto-aprobados)           │
   │  - dim_sexo             (3)                            │
   │  - dim_estado_reproductivo (4)                         │
   │  - dim_estudio          (7-10)                         │
   │  - dim_edad_categoria   (5)                            │
   │                                                        │
   │  Solo INSERT si no existe (idempotente)                │
   └────────────┬───────────────────────────────────────────┘
                │
                ▼
   ┌────────────────────────────────────────────────────────┐
   │ FASE 2: RESOLUCIÓN DE MAPEOS                           │
   │  - map_especie, map_raza, map_sexo, map_estado,        │
   │    map_estudio, map_atributo_valor                     │
   │  - Auto-aprueba por frecuencia (80/20)                 │
   │  - Pendientes → stg_*                                   │
   └────────────┬───────────────────────────────────────────┘
                │
                ▼
   ┌────────────────────────────────────────────────────────┐
   │ FASE 3: BUILD FACTS                                    │
   │  - silver_informes             (1 fila por informe)    │
   │  - silver_hallazgos            (1 fila por hallazgo)   │
   │  - silver_atributos_hallazgo   (N filas por hallazgo)  │
   │  - silver_conclusion_items     (N filas por conclusión)│
   │  - (NO silver_metricas_informe: diferido)              │
   └────────────┬───────────────────────────────────────────┘
                │
                ▼
   ┌────────────────────────────────────────────────────────┐
   │ FASE 4: VALIDACIÓN                                     │
   │  - Cobertura 100% RAW                                  │
   │  - 0 huérfanos                                         │
   │  - 0 atributos sin texto_original                      │
   │  - Métricas impresas                                   │
   │  - ROLLBACK atómico si falla                           │
   └────────────┬───────────────────────────────────────────┘
                │
                ▼
   ┌────────────────────┐
   │  silver.db         │  ← listo para Gold
   └────────────────────┘
```

### 2.1 Flujo de revisión humana

```
stg_atributos_valores  ←  (operador edita propuesta_valor_canonico)
        │                     vía review_silver.py o SQL directo
        ▼
   aprobada ──>  INSERT en map_atributo_valor
        │
        │  próxima ejecución de build_silver.py usa los maps aprobados
        ▼
   silver_atributos_hallazgo (poblado con valor_canonico)
```

---

## 3. Tablas Silver (facts)

Las facts materializan el modelo clínico. **Ninguna duplica texto de RAW.**

### 3.1 `silver_informes`

| Columna | Tipo | Constraints | Notas |
|---|---|---|---|
| `informe_id` | INTEGER | PK, FK lógica → `informes.id` | |
| `sha256` | VARCHAR(64) | NOT NULL, UNIQUE | |
| `anio` | INTEGER | NOT NULL, INDEX | De RAW |
| `fecha_raw` | VARCHAR(128) |  | Texto original |
| `fecha_parseada` | DATE | NULL, INDEX | Parser → DATE |
| `fecha_confianza` | REAL |  | 1.0 / 0.5 / 0.0 |
| `dim_especie_id` | INTEGER | FK → `dim_especie.id`, INDEX | |
| `dim_raza_id` | INTEGER | FK → `dim_raza.id`, NULL, INDEX | |
| `dim_sexo_id` | INTEGER | FK → `dim_sexo.id`, NOT NULL, INDEX | |
| `dim_estado_reproductivo_id` | INTEGER | FK → `dim_estado_reproductivo.id`, NOT NULL, INDEX | Default "No especificado" |
| `dim_estudio_id` | INTEGER | FK → `dim_estudio.id`, NOT NULL, INDEX | |
| `dim_edad_categoria_id` | INTEGER | FK → `dim_edad_categoria.id`, NULL, INDEX | |
| `edad_meses` | INTEGER | NULL | Numérico |
| `edad_origen_raw` | VARCHAR(64) |  | Texto original |
| `peso_kg` | REAL | NULL | **0% cobertura en RAW actual**; reservado para futuro |
| `nombre_paciente` | VARCHAR(255) |  | |
| `tutor` | VARCHAR(255) |  | |
| `doctor_solicitante` | VARCHAR(255) |  | 87.9% cobertura |
| `n_ficha` | VARCHAR(64) |  | 0.1% cobertura |
| `silver_built_at` | TIMESTAMP | server_default NOW() | |

**Índices:** PK en `informe_id`; `dim_especie_id`, `dim_raza_id`, `dim_sexo_id`, `dim_estudio_id`, `dim_edad_categoria_id`, `fecha_parseada`, `anio`.

### 3.2 `silver_hallazgos`

| Columna | Tipo | Constraints | Notas |
|---|---|---|---|
| `hallazgo_id` | INTEGER | PK (= RAW.hallazgos.id) | |
| `informe_id` | INTEGER | FK lógica → `informes.id`, NOT NULL, INDEX | |
| `dim_organo_id` | INTEGER | FK → `dim_organo.id`, NOT NULL, INDEX | |
| `estado` | VARCHAR(16) | NOT NULL, INDEX | Heredado de RAW |
| `orden` | INTEGER | NOT NULL | Posición en DOCX |
| `descripcion` | TEXT | NOT NULL | Copia del texto (es RAW, no derivado) |
| `n_atributos_extraidos` | INTEGER | NOT NULL | Conteo de silver_atributos_hallazgo |
| `longitud_caracteres` | INTEGER | NOT NULL | Útil para QA |
| `hallazgo_hash` | VARCHAR(64) | NOT NULL, INDEX | Copia |
| `es_gestacion_fallback` | BOOLEAN | NOT NULL, DEFAULT 0 | TRUE si organo='Gestación' y es fallback del parser |
| `silver_built_at` | TIMESTAMP | server_default NOW() | |

**Índices:** PK en `hallazgo_id`; `informe_id`, `dim_organo_id`, `estado`, `hallazgo_hash`.

### 3.3 `silver_atributos_hallazgo` ⭐ (tabla estrella)

Cardinalidad esperada: ~4-6 atributos por hallazgo abdominal típico; 0-2 para hallazgos breves ("X conservado").

| Columna | Tipo | Constraints | Notas |
|---|---|---|---|
| `id` | INTEGER | PK, autoincrement | |
| `hallazgo_id` | INTEGER | FK lógica → `hallazgos.id`, NOT NULL, INDEX | |
| `informe_id` | INTEGER | FK lógica → `informes.id`, NOT NULL, INDEX | Denormalizado |
| `dim_organo_atributo_id` | INTEGER | FK → `dim_organo_atributo.id`, NOT NULL, INDEX | Junction canónica |
| `dim_organo_id` | INTEGER | FK → `dim_organo.id`, NOT NULL, INDEX | Denormalizado |
| `valor_texto` | VARCHAR(255) | NOT NULL | Texto extraído tal cual aparece |
| `valor_canonico` | VARCHAR(64) | NULL, INDEX | Valor normalizado (catálogo del atributo) |
| `valor_numerico` | REAL | NULL | Si aplica (mm, cm) |
| `unidad` | VARCHAR(16) | NULL | `mm`, `cm` |
| `confianza` | REAL | NOT NULL | 1.0 exacta; 0.7 contexto; 0.4 fuzzy |
| `metodo_extraccion` | VARCHAR(32) | NOT NULL | `regex_anchor`, `regex_contexto`, `diccionario` |
| `texto_original` | TEXT | NOT NULL | Fragmento que originó el valor |
| `pos_inicio` | INTEGER | NOT NULL | Offset en `descripcion` |
| `pos_fin` | INTEGER | NOT NULL | |
| `silver_built_at` | TIMESTAMP | server_default NOW() | |

**Índices:** PK en `id`; `UNIQUE (hallazgo_id, dim_organo_atributo_id)`; `dim_organo_id`, `dim_organo_atributo_id`, `valor_canonico`, `informe_id`.

**Regla de unicidad:** UNIQUE `(hallazgo_id, dim_organo_atributo_id)`. Si una regex matchea dos veces (raro), gana la de mayor confianza; las demás se loguean en `silver_revision_log`.

### 3.4 `silver_conclusion_items` (sin `silver_conclusiones`)

**Decisión locked:** el texto de la conclusión vive en `raw.conclusiones.texto_completo`. Silver NO copia el texto. La trazabilidad se resuelve con 1 JOIN: `silver_conclusion_items.informe_id → raw.conclusiones.informe_id` (UNIQUE).

| Columna | Tipo | Constraints | Notas |
|---|---|---|---|
| `id` | INTEGER | PK, autoincrement | |
| `informe_id` | INTEGER | FK lógica → `informes.id`, NOT NULL, INDEX | |
| `termino_original` | VARCHAR(128) | NOT NULL | Verbatim del texto |
| `termino_canonico` | VARCHAR(64) | NOT NULL, INDEX | Normalizado (función pura) |
| `tipo_item` | VARCHAR(16) | NOT NULL, INDEX | `diagnostico` / `patron` / `etiologia` |
| `modificador` | VARCHAR(64) | NULL, INDEX | `leve` / `moderada` / `severa` / `aguda` / `cronica` |
| `lateralidad` | VARCHAR(16) | NULL, INDEX | `bilateral` / `izquierdo` / `derecho` |
| `pos_inicio` | INTEGER | NOT NULL | En `raw.conclusiones.texto_completo` |
| `pos_fin` | INTEGER | NOT NULL | |
| `confianza` | REAL | NOT NULL | |
| `metodo_extraccion` | VARCHAR(32) | NOT NULL | `diccionario_exacto` / `diccionario_fuzzy` / `regex` |
| `silver_built_at` | TIMESTAMP | server_default NOW() | |

**Índices:** PK en `id`; `(informe_id, termino_canonico, pos_inicio)` UNIQUE; `termino_canonico`, `tipo_item`, `modificador`.

**`tipo_item`:**

| Valor | Significado | Ejemplos |
|---|---|---|
| `diagnostico` | Enfermedad/condición identificada | nefropatía, hepatomegalia, cistitis, piometra, barro biliar |
| `patron` | Patrón morfológico/funcional que modifica un diagnóstico | inflamatorio, neoproliferativo, hiperplásico, infiltrativo, graso, vacuolar |
| `etiologia` | Descriptor causal o de origen | idiopático, isquémico, traumático, infeccioso, congénito, idiopática |

Para el detalle del diccionario seed, ver Anexo B.

---

## 4. Dimensiones

### 4.1 `dim_organo`

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `nombre_canonico` | VARCHAR(64) | NOT NULL, UNIQUE |
| `sistema` | VARCHAR(32) | NOT NULL, INDEX |
| `es_gestacion_fallback` | BOOLEAN | NOT NULL, DEFAULT 0 |
| `created_at` | TIMESTAMP | server_default NOW() |

**Seed (16 filas):** Vejiga, Próstata, Riñones, Bazo, Estómago, Hígado, Vesícula, Intestino, Páncreas, Adrenales, Linfonodos, Cavidad abdominal, Útero, Ovarios, Testículos, Gestación.

### 4.2 `dim_atributo` (organo-AGNÓSTICA) ⭐

Catálogo de **nombres de atributo reutilizables**. Una fila por nombre único.

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `nombre_canonico` | VARCHAR(64) | NOT NULL, UNIQUE |
| `descripcion_clinica` | TEXT | NULL |
| `created_at` | TIMESTAMP | server_default NOW() |

**Seed v1 (22 filas)** — derivado del inventario real del corpus:

| # | nombre_canonico | descripción_clinica |
|---:|---|---|
| 1 | tamaño | Tamaño o dimensión general del órgano |
| 2 | forma | Forma del órgano (ovalado, redondeado, etc.) |
| 3 | aspecto | Aspecto general (próstata) |
| 4 | bordes | Bordes externos del órgano |
| 5 | bordes_internos | Bordes internos de la luz (vejiga, vesícula) |
| 6 | márgenes | Márgenes del órgano |
| 7 | ecogenicidad | Ecogenicidad general (hipo/hiper/normo) |
| 8 | ecogenicidad_cortical | Ecogenicidad de la corteza renal |
| 9 | granulado | Textura granular del parénquima |
| 10 | arquitectura | Arquitectura interna del parénquima |
| 11 | patron_vascular | Patrón vascular (Doppler) |
| 12 | homogeneidad | Homogeneidad del parénquima |
| 13 | contenido | Contenido de la luz/vesícula |
| 14 | grosor_pared | Grosor de la pared (vejiga, vesícula, estómago, intestino) |
| 15 | distension | Distensión de la luz |
| 16 | replecion | Replieción específica de la vejiga |
| 17 | peristaltismo | Peristaltismo del tubo digestivo |
| 18 | diferenciacion_cm | Diferenciación corticomedular (riñón) |
| 19 | relacion_cm | Relación corticomedular (riñón) |
| 20 | compromiso_pelvico | Compromiso pélvico renal |
| 21 | fetos | Número de fetos detectados |
| 22 | preñez | Presencia/ausencia de preñez |

### 4.3 `dim_organo_atributo` (junction con metadatos clínicos) ⭐

Catálogo de **pares válidos** con reglas específicas por (órgano, atributo).

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `dim_organo_id` | INTEGER | FK → `dim_organo.id`, NOT NULL, INDEX |
| `dim_atributo_id` | INTEGER | FK → `dim_atributo.id`, NOT NULL, INDEX |
| `tipo_dato` | VARCHAR(16) | NOT NULL |
| `unidad_default` | VARCHAR(16) | NULL |
| `valores_canonicos_csv` | TEXT | NULL |
| `cobertura_corpus_pct` | REAL | NOT NULL |
| `n_hallazgos_corpus` | INTEGER | NOT NULL |
| `orden_visualizacion` | INTEGER | DEFAULT 0 |
| `created_at` | TIMESTAMP | server_default NOW() |

**UNIQUE:** `(dim_organo_id, dim_atributo_id)`.

**`tipo_dato`:**

| Valor | Significado |
|---|---|
| `categorico` | Solo valores de catálogo cerrado |
| `numerico` | Solo valor numérico (con unidad) |
| `mixto` | Categórico + numérico (ej. grosor_pared: "aumentado (5,4mm)") |
| `booleano` | `presente` / `ausente` |
| `texto` | Libre, sin catálogo |

**Seed v1 (57 filas)** — derivado del inventario. Ver Anexo A para la tabla completa con valores canónicos y cobertura.

### 4.4 `dim_especie`

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `nombre_canonico` | VARCHAR(64) | NOT NULL, UNIQUE |
| `nombre_cientifico` | VARCHAR(64) | NULL |
| `es_exotica` | BOOLEAN | NOT NULL, DEFAULT 0 |
| `fuente` | VARCHAR(32) | NOT NULL |
| `created_at` | TIMESTAMP | server_default NOW() |

**Seed v1 (9):** Canino, Felino, Conejo, Cobaya, Hurón, Hámster, Erizo, Ratón, Cuy.

### 4.5 `dim_raza`

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `dim_especie_id` | INTEGER | FK → `dim_especie.id`, NOT NULL, INDEX |
| `nombre_canonico` | VARCHAR(128) | NOT NULL |
| `es_mestizo` | BOOLEAN | NOT NULL, DEFAULT 0 |
| `agrupacion` | VARCHAR(64) | NULL |
| `fuente` | VARCHAR(32) | NOT NULL |
| `created_at` | TIMESTAMP | server_default NOW() |

**UNIQUE:** `(dim_especie_id, nombre_canonico)`.

**Seed v1:** ~80 razas auto-aprobadas (freq≥3 en RAW). Las 79 con freq=1 quedan en `stg_razas_detectadas`.

### 4.6 `dim_sexo`

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `nombre_canonico` | VARCHAR(32) | NOT NULL, UNIQUE |
| `codigo` | CHAR(1) | NOT NULL, UNIQUE |
| `created_at` | TIMESTAMP | server_default NOW() |

**Seed v1 (3):** Hembra (H), Macho (M), Indeterminado (I).

### 4.7 `dim_estado_reproductivo`

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `nombre_canonico` | VARCHAR(32) | NOT NULL, UNIQUE |
| `codigo` | VARCHAR(8) | NOT NULL |
| `created_at` | TIMESTAMP | server_default NOW() |

**Seed v1 (4):** Entero (ENT), Castrado (CAS), OVH (OVH), No especificado (NE).

### 4.8 `dim_estudio`

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `nombre_canonico` | VARCHAR(64) | NOT NULL, UNIQUE |
| `abreviatura` | VARCHAR(16) | NULL |
| `parent_id` | INTEGER | FK → `dim_estudio.id`, NULL |
| `created_at` | TIMESTAMP | server_default NOW() |

**Seed v1 (~8):** Abdominal, Gestacional, Cervical, Reproductivo, Partes blandas, Musculoesquelético, Ocular, Otro.

### 4.9 `dim_edad_categoria`

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `codigo` | VARCHAR(8) | NOT NULL, UNIQUE |
| `nombre` | VARCHAR(32) | NOT NULL |
| `min_meses` | INTEGER | NOT NULL |
| `max_meses` | INTEGER | NULL |

**Seed v1 (5):**

| codigo | nombre | min_meses | max_meses |
|---|---|---:|---:|
| CACH | Cachorro | 0 | 12 |
| JUV | Juvenil | 12 | 24 |
| ADU | Adulto | 24 | 96 |
| MAD | Maduro | 96 | 132 |
| GER | Geriátrico | 132 | NULL |

---

## 5. Tablas de mapeo

Los mapas traducen valores RAW a IDs canónicos. Son la pieza central de la normalización.

### 5.1 `map_especie`

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `valor_original` | VARCHAR(128) | NOT NULL, UNIQUE |
| `dim_especie_id` | INTEGER | FK → `dim_especie.id`, NOT NULL, INDEX |
| `confianza` | REAL | NOT NULL |
| `fuente` | VARCHAR(32) | NOT NULL |
| `created_at` | TIMESTAMP | server_default NOW() |

### 5.2 `map_raza`

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `valor_original` | VARCHAR(255) | NOT NULL, UNIQUE |
| `dim_raza_id` | INTEGER | FK → `dim_raza.id`, NULL, INDEX |
| `dim_especie_id` | INTEGER | FK → `dim_especie.id`, NOT NULL, INDEX |
| `frecuencia` | INTEGER | NOT NULL |
| `confianza` | REAL | NOT NULL |
| `fuente` | VARCHAR(32) | NOT NULL |
| `created_at` | TIMESTAMP | server_default NOW() |

### 5.3 `map_sexo`

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `valor_original` | VARCHAR(128) | NOT NULL, UNIQUE |
| `dim_sexo_id` | INTEGER | FK → `dim_sexo.id`, NOT NULL, INDEX |
| `confianza` | REAL | NOT NULL |
| `fuente` | VARCHAR(32) | NOT NULL |
| `created_at` | TIMESTAMP | server_default NOW() |

### 5.4 `map_estado_reproductivo`

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `valor_original` | VARCHAR(128) | NOT NULL, UNIQUE |
| `dim_estado_reproductivo_id` | INTEGER | FK → `dim_estado_reproductivo.id`, NOT NULL, INDEX |
| `confianza` | REAL | NOT NULL |
| `fuente` | VARCHAR(32) | NOT NULL |
| `created_at` | TIMESTAMP | server_default NOW() |

### 5.5 `map_estudio`

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `valor_original` | VARCHAR(128) | NOT NULL, UNIQUE |
| `dim_estudio_id` | INTEGER | FK → `dim_estudio.id`, NOT NULL, INDEX |
| `confianza` | REAL | NOT NULL |
| `fuente` | VARCHAR(32) | NOT NULL |
| `created_at` | TIMESTAMP | server_default NOW() |

### 5.6 `map_atributo_valor` ⭐ (PRIORIDAD)

Traduce `valor_texto` extraído por regex a `valor_canonico` del catálogo del atributo. **Es la base de la normalización clínica futura.**

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `dim_organo_atributo_id` | INTEGER | FK → `dim_organo_atributo.id`, NOT NULL, INDEX |
| `valor_original` | VARCHAR(128) | NOT NULL |
| `valor_canonico` | VARCHAR(64) | NOT NULL |
| `orden` | INTEGER | NULL |
| `fuente` | VARCHAR(32) | NOT NULL |
| `created_at` | TIMESTAMP | server_default NOW() |

**UNIQUE:** `(dim_organo_atributo_id, valor_original)`.

**`orden`:** para valores ordinales (1=normal, 2=leve, 3=moderado, 4=severo). Permite ordenar en queries sin re-parsear.

---

## 6. Tablas staging

Almacenan valores aún no canónicos para revisión humana. **No se usan en queries de producción.**

### 6.1 `stg_razas_detectadas`

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `valor_original` | VARCHAR(255) | NOT NULL, UNIQUE |
| `frecuencia` | INTEGER | NOT NULL, INDEX |
| `dim_especie_inferida_id` | INTEGER | FK → `dim_especie.id`, NULL |
| `propuesta_canonica` | VARCHAR(128) | NULL |
| `dim_raza_propuesta_id` | INTEGER | FK → `dim_raza.id`, NULL |
| `estado_revision` | VARCHAR(16) | NOT NULL, INDEX |
| `revisado_por` | VARCHAR(64) | NULL |
| `revisado_at` | TIMESTAMP | NULL |
| `observaciones` | TEXT | NULL |
| `created_at` | TIMESTAMP | server_default NOW() |

**Estados:** `pendiente` / `aprobada` / `nuevo` / `rechazada`.

### 6.2 `stg_especies_detectadas`

Análogo a `stg_razas_detectadas` para especies. En el corpus actual solo tendría 9 entries; se mantiene para simetría y crecimiento futuro.

### 6.3 `stg_atributos_valores` ⭐ (PRIORIDAD)

Términos de atributo extraídos por regex que **no matchearon** ningún `valor_canonico` del catálogo. **Es la pieza de retroalimentación que mejora la normalización clínica iterativamente.**

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `dim_organo_atributo_id` | INTEGER | FK → `dim_organo_atributo.id`, NOT NULL, INDEX |
| `valor_original` | VARCHAR(255) | NOT NULL |
| `frecuencia` | INTEGER | NOT NULL, INDEX |
| `primera_vez_visto` | TIMESTAMP | NOT NULL |
| `ultima_vez_visto` | TIMESTAMP | NOT NULL |
| `contexto_ejemplo` | TEXT | NULL | Frase de `descripcion` donde apareció |
| `propuesta_canonico` | VARCHAR(64) | NULL | Sugerencia del ETL |
| `estado_revision` | VARCHAR(16) | NOT NULL, INDEX |
| `revisado_por` | VARCHAR(64) | NULL |
| `revisado_at` | TIMESTAMP | NULL |
| `observaciones` | TEXT | NULL |
| `created_at` | TIMESTAMP | server_default NOW() |

**Estados:** `pendiente` / `aprobada` / `nuevo` / `rechazada`.

**UNIQUE:** `(dim_organo_atributo_id, valor_original)`.

**Workflow:**

```
silver_atributos_hallazgo (valor_canonico = NULL porque no matchea)
        │
        ▼
stg_atributos_valores (estado_revision='pendiente')
        │
        │ operador edita (CLI o SQL)
        ▼
stg_atributos_valores (estado_revision in {aprobada, nuevo, rechazada})
        │
        │ próxima ejecución de build_silver.py
        ▼
map_atributo_valor (poblado)
        │
        ▼
silver_atributos_hallazgo (valor_canonico != NULL)
```

---

## 7. Tabla de auditoría

### 7.1 `silver_revision_log`

Auditoría transversal de toda promoción/descarte.

| Columna | Tipo | Constraints |
|---|---|---|
| `id` | INTEGER | PK, autoincrement |
| `tabla_origen` | VARCHAR(64) | NOT NULL, INDEX |
| `operacion` | VARCHAR(16) | NOT NULL |
| `valor_original` | VARCHAR(255) | NOT NULL |
| `valor_canonico` | VARCHAR(255) | NULL |
| `contexto_id` | INTEGER | NULL |
| `motivo` | TEXT | NULL |
| `actor` | VARCHAR(64) | NOT NULL |
| `created_at` | TIMESTAMP | server_default NOW() |

**`operacion`:** `descartado` / `mapeado_auto` / `promovido_manual` / `conflicto` / `fuzzy_match`.

---

## 8. Estrategia de normalización

### 8.1 Especie

```
1. lowercase + strip whitespace + strip puntuación final
2. corregir encoding (cp1252 → utf-8)
3. lookup en map_especie
4. si no match: fuzzy match (Levenshtein ≤ 2)
5. si no: insertar en stg_especies_detectadas
6. errores obvios (género capturado en especie, "Raza:"): dim_especie_id = NULL
```

### 8.2 Raza

```
1. strip + lowercase + fix encoding
2. lookup exacto en map_raza
3. si no match: detectar abreviaturas (DPC, DPL) y sigla PL/PC
4. fuzzy match (Levenshtein ≤ 2) contra dim_raza top-N
5. si match ≥ 0.8: auto-aprobar (confianza 0.7)
6. si match 0.5-0.8: stg_razas_detectadas
7. errores obvios: NULL
```

### 8.3 Sexo y estado reproductivo (separados)

```
"Hembra entera"
  → aplicar map_sexo       → dim_sexo_id = 1 (Hembra)
  → aplicar map_estado_reproductivo → dim_estado_reproductivo_id = 1 (Entero)

"Macho castrado"
  → map_sexo → 2 (Macho)
  → map_estado_reproductivo → 2 (Castrado)
```

Ambos maps son **independientes** y se aplican en secuencia sobre el mismo string.

### 8.4 Edad → meses → categoría

```python
def parse_edad_meses(s):
    s = normalize(s)
    s = replace_text_numbers(s)        # "un año" → "1 año", "dos años" → "2 años"
    s = replace_compact(s)             # "1año" → "1 año", "3meses" → "3 meses"
    
    # Años + meses
    m = re.search(r'(\d+)\s*a[ñn]os?(?:\s+y\s*(\d+)\s*m|\s*(\d+)\s*m)?', s)
    if m: return int(m[1]) * 12 + int(m[2] or m[3] or 0)
    
    # Solo meses
    m = re.search(r'(\d+)\s*m(?:es)?(?!\w)', s)
    if m: return int(m[1])
    
    # Días
    m = re.search(r'(\d+)\s*d[íi]as?', s)
    if m: return max(0, int(m[1]) // 30)
    
    return None  # Inserción en stg_ si freq > 1
```

| Entrada | Salida (edad_meses) |
|---|---|
| `3 años` | 36 |
| `1 año 6 meses` | 18 |
| `1a 7m` | 19 |
| `45 días aprox` | 1 |
| `Edad:` (error captura) | NULL |
| `5 a` (truncado) | NULL |

**Categoría:** `LOOKUP(dim_edad_categoria, min_meses <= edad_meses < max_meses)`.

### 8.5 Estudio

```
1. lowercase + strip + replace('  ', ' ')
2. normalizar separadores (., /, -)
3. consolidar a uno de los 7-10 canónicos
```

### 8.6 Órgano

Silver **no normaliza** el órgano: RAW ya lo entrega canónico. Silver solo lo referencia vía FK a `dim_organo` y agrega metadatos (sistema afectado, es_gestacion_fallback).

### 8.7 Atributos (extracción por regex por órgano)

**Estructura:**

```python
ATTRIBUTE_RULES: dict[int, dict[int, list[AttributeRule]]] = {
    # dim_organo_id → {dim_atributo_id → [reglas]}
}

# Ejemplo (Hígado × tamaño):
AttributeRule(
    dim_organo_atributo_id=1,  # Hígado × tamaño
    pattern=r'tamaño\s+(?:severamente\s+|moderadamente\s+|levemente\s+|discretamente\s+|muy\s+)?(disminuido|aumentado(?:s)?|dentro de rango|normal|conservado)',
    captura_grupo=1,
    metodo='regex_anchor',
)
```

**Reglas refinadas en Fase 3** (3 regex a corregir detectadas en inventario):

1. **Riñones × `relacion_cm`**: aceptar variantes con guión (`cortico-medular`).
2. **Intestino × `contenido`**: excluir captura de "con" suelta; requerir sustantivo clínico.
3. **Estómago × `peristaltismo`**: aceptar frases de 1-3 palabras (hoy solo captura 16 hallazgos vs 2.500 esperados).

**Cobertura objetivo por órgano** (basado en inventario real):

| Órgano | Cobertura corpus | Attrs/hallazgo |
|---|---:|---:|
| Hígado | 99,3% | 6,00 |
| Vejiga | 99,8% | 3,82 |
| Vesícula | 99,0% | 3,85 |
| Riñones | 97,9% | 4,01 |
| Intestino | 98,7% | 2,89 |
| Estómago | 98,0% | 2,67 |
| Bazo | 96,6% | 2,79 |
| Próstata | 98,2% | 3,76 |
| Adrenales | 90,4% | 0,93 |
| Gestación | 53,5% | 0,54 |
| Linfonodos | 13,3% | 0,15 |
| Páncreas | 1,6% | 0,02 |
| Útero | 16,3% | 0,20 |
| Testículos | 29,6% | 0,37 |
| Ovarios | 0,0% | 0,00 |

**Nota sobre cobertura baja en Páncreas/Linfonodos/Adrenales/Útero/Testículos/Ovarios:** el corpus real tiene descripciones breves para estos órganos. No es bug de extracción.

### 8.8 Conclusiones → `silver_conclusion_items` con `tipo_item`

**Pipeline:**

```
1. JOIN a raw.conclusiones por informe_id (1:1)
2. Tokenizar texto en frases
3. Para cada término del diccionario CONCLUSION_TERMS:
   - matchear (exacto o fuzzy con Levenshtein ≤ 1)
   - asignar tipo_item según diccionario
   - extraer modificador en ventana de 3 palabras antes/después
   - extraer lateralidad en ventana de 2 palabras
   - registrar pos_inicio, pos_fin
4. Si el término no está en el diccionario:
   - término_canonico = lowercase + strip
   - tipo_item = 'diagnostico' (default conservador)
   - log en silver_revision_log con operacion='termino_nuevo'
5. Si no se detecta nada: el informe queda con silver_conclusion_items vacío
   (se loguea como cobertura < 100% en el reporte de validación)
```

**Diccionario seed de CONCLUSION_TERMS** — ver Anexo B.

---

## 9. Estrategia de gobernanza de catálogos

### 9.1 Principios

1. **Regla 80/20:** alta frecuencia (≥80% de la masa) se auto-aprueba con `fuente='auto_frecuente'`. La cola de revisión es la cola larga.
2. **Auditoría obligatoria:** toda promoción deja un rastro en `silver_revision_log`.
3. **No hay eliminación silenciosa:** un valor que se descarta queda registrado con `operacion='descartado'`.
4. **Reversibilidad:** la promoción es aditiva. Si una raza se aprobó por error, se cambia su `dim_raza_id` en `map_raza` a NULL; la fila RAW sigue ahí.

### 9.2 Umbrales de auto-aprobación

| Tabla | Umbral auto-aprobación | Razón |
|---|---|---|
| `map_especie` | freq ≥ 1 | 9 spp totales |
| `map_raza` | freq ≥ 3 | 84% de la masa |
| `map_sexo` | freq ≥ 1 | 20 variantes, todas seguras |
| `map_estado_reproductivo` | freq ≥ 1 | Pocas variantes |
| `map_estudio` | freq ≥ 1 | ~10 canónicos consolidados |
| `map_atributo_valor` | match exacto en `dim_organo_atributo.valores_canonicos_csv` | Diccionario cerrado |
| `dim_atributo` (new attrs) | freq ≥ 50 | Un atributo nuevo debe ser común para entrar al catálogo |
| `dim_organo_atributo` (new pairs) | freq ≥ 50 | Un par nuevo debe ser común |

### 9.3 Workflow de revisión humana

**Opción A: SQL directo:**

```sql
-- Ver cola
SELECT valor_original, frecuencia, propuesta_canonico
FROM stg_atributos_valores
WHERE estado_revision = 'pendiente'
ORDER BY frecuencia DESC
LIMIT 50;

-- Aprobar
UPDATE stg_atributos_valores
SET estado_revision = 'aprobada',
    valor_canonico = 'aumentado_leve',  -- propuesto
    revisado_por = 'op1',
    revisado_at = CURRENT_TIMESTAMP
WHERE id = 123;

-- Crear nuevo (caso valor genuinamente nuevo)
INSERT INTO map_atributo_valor (dim_organo_atributo_id, valor_original, valor_canonico, fuente)
VALUES (5, 'levemente raro', 'irregular_leve', 'manual');
```

**Opción B: CLI (`scripts/review_silver.py`):**

```bash
python scripts/review_silver.py --tabla atributos --pendientes --limit 50
python scripts/review_silver.py --tabla atributos --aprobar 123 --canonico "aumentado_leve"
python scripts/review_silver.py --tabla atributos --nuevo 456 --canonico "irregular_leve" --atributo-id 5
```

### 9.4 Política de re-running

El ETL es **idempotente**:

- Stg en `aprobada` / `nuevo` → próxima ejecución promueve a dim+map.
- Stg en `pendiente` → preserva, no re-genera.
- Stg en `rechazada` → NO promueve.
- Dim_* → solo INSERT si no existe (nunca UPDATE).

### 9.5 Política de versionado de dims

- Dims son **inmutables en contenido pero crecientes**.
- No se renombran canónicos; cambios semánticos crean nuevos y re-mapean.
- Si se retira un atributo: se deja en `dim_atributo` pero `dim_organo_atributo` se marca con `estado='deprecated'` (columna a agregar en v2 si se necesita).

---

## 10. Orden de implementación por fases

| Fase | Descripción | Tiempo | Acumulado |
|---|---|---|---|
| 1 | Bootstrap mínimo: dims básicas + silver_informes | 2-3 d | 2-3 d |
| 2 | Hallazgos y órganos: dim_organo + silver_hallazgos | 2-3 d | 4-6 d |
| 3 | Atributos clínicos: dim_organo_atributo + silver_atributos_hallazgo + map_atributo_valor + stg_atributos_valores | 5-7 d | 9-13 d |
| 4 | Edad y categorías: dim_edad_categoria + parseo de edad | 2-3 d | 11-16 d |
| 5 | Conclusiones: silver_conclusion_items con tipo_item | 2-3 d | 13-19 d |
| 6 | Razas: stg_razas_detectadas + CLI de revisión | 1-2 d | 14-21 d |
| 7 | Validación final + métricas | 1 d | 15-22 d |

**Total: 15-22 días (3-5 semanas).**

> ⚠️ **NO hay Fase de métricas precomputadas** (silver_metricas_informe está diferido por decisión locked).

### Detalle por fase

#### Fase 1 — Bootstrap mínimo (2-3 días)

**Construye:**
- `models_silver.py` con todas las 24 tablas declaradas.
- `silver_dims.py::bootstrap_basico()` puebla: dim_especie, dim_sexo, dim_estado_reproductivo, dim_estudio, dim_edad_categoria, dim_organo.
- `silver_etl.py::build_f1()` lee `RAW.informes`, construye `silver_informes`.
- `scripts/build_silver.py` CLI con `--reset --fase 1`.

**Tests:**
- `test_silver_informes_cantidad.py` — 2.893 filas, 0 huérfanos.
- `test_silver_informes_campos.py` — 100% cobertura de especie/género/estudio.

#### Fase 2 — Hallazgos y órganos (2-3 días)

**Construye:**
- `silver_hallazgos` con FK lógica a `informe_id` y FK real a `dim_organo`.

**Tests:**
- `test_silver_hallazgos_cantidad.py` — 27.866 filas.
- `test_silver_hallazgos_organos.py` — distribución igual a RAW.

#### Fase 3 — Atributos clínicos (5-7 días) ⭐ PRIORIDAD

**Construye:**
- `dim_atributo` (22 filas) y `dim_organo_atributo` (57 filas) — semillas desde Anexo A.
- `silver_attr.py` con las 57 reglas de extracción.
- `silver_atributos_hallazgo` poblada.
- `map_atributo_valor` semilla con los top-3 valores canónicos por par.
- `stg_atributos_valores` recibe los valores no matcheados.

**Refinamientos pendientes (detectados en inventario):**
1. Riñones × `relacion_cm` — aceptar variantes con guión.
2. Intestino × `contenido` — excluir "con" suelta.
3. Estómago × `peristaltismo` — permitir frases de 1-3 palabras.

**Tests:**
- `test_silver_attr_cobertura_organos.py` — ≥95% por órgano principal.
- `test_silver_attr_ejemplos_reales.py` — 20 hallazgos manuales vs extracción.
- `test_silver_attr_canonizacion.py` — fuzzy + exact match contra map_atributo_valor.

**Entregable:** Silver.clinica completa. Query de ejemplo: "todos los hígados con ecogenicidad aumentada en 2024".

#### Fase 4 — Edad y categorías (2-3 días)

**Construye:**
- `parse_edad_meses()` con regex completo.
- `dim_edad_categoria` (5 filas).
- `silver_informes.edad_meses` y `dim_edad_categoria_id` poblados.

**Tests:**
- `test_silver_edad_cobertura.py` — ≥99% parseable.
- `test_silver_edad_casos_raros.py` — "1a 7m" → 19, "45 días" → 1.

#### Fase 5 — Conclusiones con `tipo_item` (2-3 días)

**Construye:**
- `silver_conc.py` con `CONCLUSION_TERMS` (diccionario seed de 3 tipos, Anexo B).
- `silver_conclusion_items` poblada.
- `silver_revision_log` recibe matches fuzzy y términos nuevos.

**Tests:**
- `test_silver_conc_cobertura.py` — ≥80% con al menos 1 item.
- `test_silver_conc_tipo_item.py` — verificar clasificación (diagnostico/patron/etiologia).
- `test_silver_conc_modificadores.py` — "nefropatía bilateral leve" → 3 campos.

**Entregable:** Silver.diagnostico: "Top 10 patrones en nefropatías" — primer query de Gold-ready.

#### Fase 6 — Razas: cola de revisión (1-2 días)

**Construye:**
- `stg_razas_detectadas` poblada con freq < 3.
- `scripts/review_silver.py` CLI para raza y atributo.

**Entregable:** proceso de revisión manual funcional.

#### Fase 7 — Validación final (1 día)

**Construye:**
- `scripts/validate_silver.py` — corre todas las aserciones de §0.3.

**Entregable:** Silver.validada y certificada.

---

## 11. Registro de decisiones arquitectónicas

Esta sección es la **bitácora completa** de todas las decisiones locked en el diseño Silver. Futuros lectores deben consultar aquí antes de proponer cambios.

| ID | Decisión | Estado | Origen |
|---|---|---|---|
| D1 | `silver.db` separado de `informes.db` | ✅ Locked | Diseño inicial |
| D2 | Sin `silver_conclusiones`. Texto vive solo en RAW. | ✅ Locked | Revisión 1 |
| D3 | `silver_conclusion_items` con FK lógica a `informe_id` (no copia de texto) | ✅ Locked | Revisión 1 |
| D4 | `dim_atributo` organo-AGNÓSTICA (22 filas) | ✅ Locked | Revisión 2 |
| D5 | `dim_organo_atributo` junction con metadatos clínicos (57 filas) | ✅ Locked | Revisión 2 |
| D6 | `silver_conclusion_items.tipo_item` ∈ {diagnostico, patron, etiologia} | ✅ Locked | Aprobación final |
| D7 | `silver_metricas_informe` DIFERIDO a fase futura | ✅ Locked | Aprobación final |
| D8 | `dim_diagnostico` DIFERIDO a fase futura | ✅ Locked | Aprobación final |
| D9 | `stg_atributos_valores` + `map_atributo_valor` PRIORIZADOS | ✅ Locked | Aprobación final |
| D10 | Estructura clínica priorizada: Órgano → atributo → valor → conclusión | ✅ Locked | Aprobación final |
| D11 | `dim_sexo` y `dim_estado_reproductivo` separados | ✅ Locked | Diseño inicial |
| D12 | Extracción por regex + diccionario, NO ML | ✅ Locked | Diseño inicial |
| D13 | Idempotencia total del ETL | ✅ Locked | Diseño inicial |
| D14 | FK cross-DB son lógicas (validadas en build) | ✅ Locked | Diseño inicial |
| D15 | Stack: SQLite + SQLAlchemy Core | ✅ Locked | Diseño inicial |
| D16 | Atributos extraídos (no inferidos): cada valor tiene `texto_original` | ✅ Locked | Diseño inicial |
| D17 | Dims crecen, no se modifican | ✅ Locked | Diseño inicial |
| D18 | Razas: auto-aprobación freq≥3; cola de revisión freq<3 | ✅ Locked | Diseño inicial |

---

## 12. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|---|
| R1 | Cobertura atributos <85% en algún órgano principal | Media | Alto | F3 incluye test con umbral por órgano. Si falla, agregar más reglas. |
| R2 | Catálogo de órganos desincronizado entre RAW y Silver | Baja | Alto | Test `test_organos_sync.py` verifica que `dim_organo` contiene los mismos nombres que `ORGANS` en `organs.py`. |
| R3 | Cola de revisión crece sin atender | Media | Bajo | Métrica expuesta en validación. SLA: revisar al menos 1x/mes. |
| R4 | Términos fuzzy de conclusión generan falsos positivos | Media | Medio | `confianza < 0.7` se registra en `silver_revision_log`. Operador puede invalidar. |
| R5 | Edad mal parseada → NULL masivo | Baja | Bajo | Reportado en métricas. Operador revisa manualmente. |
| R6 | Ingesta de nuevos DOCX no actualiza Silver | Alta | Alto | README: "post-ingest: re-run silver". El script es idempotente. |
| R7 | Cambios en `dim_organo_atributo` invalidan `silver_atributos_hallazgo` | Baja | Alto | Cambios se hacen vía `silver_revision_log` con `motivo='atributo_retirado'`. No se borra histórico. |
| R8 | Encoding corrupto (CP1252 vs UTF-8) | Media | Medio | Normalización en `silver_etl.py::normalize_value()`. Test dedicado. |
| R9 | Conclusiones con términos no estándar | Media | Bajo | `silver_conclusion_items` queda con `termino_canonico` + log. Operador puede agregar manualmente. |
| R10 | Corpus crece 10x | Baja | Bajo | Arquitectura escala. Único punto a revisar: fuzzy match para razas. |
| R11 | Tipos `tipo_item` mal asignados | Media | Medio | Diccionario seed revisado. Términos no conocidos → default `diagnostico` (conservador). |
| R12 | `silver_conclusion_items.termino_canonico` con demasiados valores únicos | Alta | Medio | Sin dim_diagnostico en v1, los typos generan valores distintos. Solución: revisar `stg_atributos_valores` y map_atributo_valor en iteraciones. |

---

## 13. Anexo A: `dim_atributo` y `dim_organo_atributo` (catálogo clínico)

### A.1 `dim_atributo` — 22 filas organo-agnósticas

Ver §4.2 para la tabla completa. Cada atributo es reusable entre órganos.

### A.2 `dim_organo_atributo` — 57 filas (pares con metadatos)

**Hígado (7 pares):**

| atributo | tipo_dato | unidad | valores_canonicos_csv | cobertura | n |
|---|---|---|---|---:|---:|
| tamaño | mixto | cm | normal;disminuido;aumentado_leve;aumentado_moderado;aumentado_severo | 65% | 1.754 |
| márgenes | categorico |  | lisos;irregulares;conservados;mal_definidos | 98% | 2.622 |
| bordes | categorico |  | aguzados;redondeados;regulares;irregulares;lisos | 92% | 2.473 |
| ecogenicidad | mixto |  | hipoecoica;hiperecoica;conservada;normal;levemente_aumentada;levemente_disminuida | 94% | 2.515 |
| granulado | categorico |  | fino;grueso | 94% | 2.535 |
| arquitectura | categorico |  | conservada;alterada;preservada | 65% | 1.756 |
| patron_vascular | categorico |  | conservado;alterado;aumentado;disminuido | 92% | 2.474 |

**Riñones (7 pares):**

| atributo | tipo_dato | unidad | valores_canonicos_csv | cobertura | n |
|---|---|---|---|---:|---:|
| forma | categorico |  | ovalado;reniforme;redondeado;irregular;globoso | 95% | 2.540 |
| tamaño | mixto | cm | dentro_de_rango;aumentado;disminuido;normal | 93% | 2.494 |
| bordes | categorico |  | regulares;irregulares;levemente_irregulares;lisos | 93% | 2.506 |
| ecogenicidad_cortical | mixto |  | hipoecoica;hiperecoica;ecogenicidad_conservada;levemente_hiperecoica;discretamente_hiperecoica | 33% | 898 |
| diferenciacion_cm | booleano |  | bien_definida;mal_definida | 86% | 2.316 |
| relacion_cm | categorico |  | conservada;alterada;preservada | 0,4% ⚠️ | 12 |
| compromiso_pelvico | booleano |  | presente;ausente | (alto) | (no medido) |

**Vejiga (4 pares):**

| atributo | tipo_dato | unidad | valores_canonicos_csv | cobertura | n |
|---|---|---|---|---:|---:|
| replecion | categorico |  | semi_pletorica;pletorica;semi_depletada;depletada;distendida | 99% | 2.669 |
| contenido | texto |  | (sin catálogo cerrado) | 93% | 2.507 |
| bordes_internos | categorico |  | regulares;irregulares;levemente_irregulares;lisos | 95% | 2.546 |
| grosor_pared | mixto | mm | conservado;levemente_aumentado;discretamente_aumentado;aumentado;moderadamente_aumentado;severamente_aumentado;normal | 95% | 2.542 |

**Vesícula (4 pares):**

| atributo | tipo_dato | unidad | valores_canonicos_csv | cobertura | n |
|---|---|---|---|---:|---:|
| distension | categorico |  | semi_distendida;distendida;pletorica;semi_pletorica;depletada | 99% | 2.640 |
| contenido | mixto |  | anecoico;hiperecoico;con_ecos;homogeneo | 95% | 2.536 |
| bordes_internos | categorico |  | regulares;irregulares;levemente_irregulares | 95% | 2.541 |
| grosor_pared | mixto | mm | conservado;levemente_aumentado;discretamente_aumentado;aumentado;moderadamente_aumentado;severamente_aumentado;normal | 96% | 2.548 |

**Bazo (4 pares):**

| atributo | tipo_dato | unidad | valores_canonicos_csv | cobertura | n |
|---|---|---|---|---:|---:|
| tamaño | mixto | cm | normal;aumentado;disminuido;conservado;dentro_de_rango | 7% ⚠️ | 191 |
| forma | categorico |  | normal;conservada;caracteristica | 90% | 2.418 |
| márgenes | categorico |  | lisos;irregulares;conservados | 94% | 2.519 |
| arquitectura | categorico |  | conservada;alterada;heterogenea | 88% | 2.365 |

**Próstata (4 pares):**

| atributo | tipo_dato | unidad | valores_canonicos_csv | cobertura | n |
|---|---|---|---|---:|---:|
| aspecto | categorico |  | ovalada;bilobulada;globosa;reniforme | 93% | 687 |
| tamaño | mixto | cm | dentro_de_rango;aumentado;disminuido;normal;conservado | 89% | 654 |
| ecogenicidad | categorico |  | hipoecoica;hiperecoica;ecogenicidad_conservada | 96% | 708 |
| homogeneidad | categorico |  | homogenea;heterogenea;discretamente_heterogenea | 98% | 719 |

**Estómago (4 pares):**

| atributo | tipo_dato | unidad | valores_canonicos_csv | cobertura | n |
|---|---|---|---|---:|---:|
| distension | categorico |  | semi_distendido;distendido;replecion_conservada;depletado | 82% | 2.195 |
| contenido | categorico |  | alimenticio;gas;mucoso;alimenticio_y_gas;liquido | 90% | 2.429 |
| grosor_pared | mixto | mm | conservado;levemente_aumentado;discretamente_aumentado;aumentado;moderadamente_aumentado | 94% | 2.528 |
| peristaltismo | categorico |  | normal;aumentado;disminuido;conservado | 0,6% ⚠️ | 16 |

**Intestino (4 pares):**

| atributo | tipo_dato | unidad | valores_canonicos_csv | cobertura | n |
|---|---|---|---|---:|---:|
| distension | categorico |  | distendido;marcadamente_distendido;semi_distendido;replecion_conservada | 2% ⚠️ | 54 |
| contenido | mixto |  | mucoso;alimenticio;fecal;con_predominio | 98% | 2.641 |
| grosor_pared | mixto | mm | conservado;levemente_aumentado;discretamente_aumentado;aumentado;moderadamente_aumentado;severamente_aumentado | 95% | 2.560 |
| peristaltismo | categorico |  | normal;aumentado;disminuido;conservado;discretamente_aumentado | 93% | 2.505 |

**Páncreas (2 pares):**

| atributo | tipo_dato | unidad | valores_canonicos_csv | cobertura | n |
|---|---|---|---|---:|---:|
| ecogenicidad | categorico |  | conservada;aumentada;disminuida;hiperecogenica;hipoecoica | 0,6% | 15 |
| tamaño | mixto | cm | normal;conservado;aumentado;disminuido;dentro_de_rango | 1,1% | 30 |

**Adrenales (2 pares):**

| atributo | tipo_dato | unidad | valores_canonicos_csv | cobertura | n |
|---|---|---|---|---:|---:|
| tamaño | mixto | cm | normal;conservado;aumentado;disminuido;dentro_de_rango | 4,5% | 121 |
| forma | categorico |  | normal;conservada | 89% | 2.390 |

**Linfonodos (4 pares):**

| atributo | tipo_dato | unidad | valores_canonicos_csv | cobertura | n |
|---|---|---|---|---:|---:|
| tamaño | mixto | cm | normal;conservado;aumentado;disminuido;dentro_de_rango;levemente_aumentado | 0,4% | 12 |
| forma | categorico |  | normal;conservada;oval;ovalados;redondeados | 2,9% | 78 |
| ecogenicidad | categorico |  | conservada;hiperecoica;hipoecoica;aumentada;disminuida;normal | 0,6% | 15 |
| homogeneidad | categorico |  | homogeneos;heterogeneos | 11% | 307 |

**Útero (3 pares):**

| atributo | tipo_dato | unidad | valores_canonicos_csv | cobertura | n |
|---|---|---|---|---:|---:|
| tamaño | mixto | cm | normal;conservado;aumentado;disminuido;levemente_aumentado;moderadamente_aumentado | (bajo) | (bajo) |
| contenido | mixto |  | anecoico;hiperecoico;ecogenico;homogeneo;heterogeneo | 14% | 7 |
| grosor_pared | mixto | mm | conservado;aumentado;disminuido;levemente_aumentado | 6% | 3 |

**Ovarios (2 pares):**

| atributo | tipo_dato | unidad | valores_canonicos_csv | cobertura | n |
|---|---|---|---|---:|---:|
| tamaño | mixto | cm | normal;conservado;aumentado;disminuido;levemente_aumentado | (bajo) | (bajo) |
| forma | categorico |  | normal;conservada;ovalados;redondeados | (bajo) | (bajo) |

**Testículos (4 pares):**

| atributo | tipo_dato | unidad | valores_canonicos_csv | cobertura | n |
|---|---|---|---|---:|---:|
| tamaño | mixto | cm | normal;conservado;aumentado;disminuido;dentro_de_rango | 7% | 2 |
| forma | categorico |  | normal;conservada | 4% | 1 |
| ecogenicidad | categorico |  | conservada;hiperecoica;hipoecoica;aumentada;disminuida;normal | 4% | 1 |
| homogeneidad | categorico |  | homogeneos;heterogeneos | 22% | 6 |

**Gestación (2 pares):**

| atributo | tipo_dato | unidad | valores_canonicos_csv | cobertura | n |
|---|---|---|---|---:|---:|
| fetos | numerico |  | (sin catálogo cerrado) | 54% | 107 |
| preñez | booleano |  | presente;ausente | (medio) | (medio) |

**Cavidad abdominal (0 pares):** RAW tiene 0 hallazgos; se reserva en `dim_organo` pero sin atributos. Se agregan `liquido_libre` y `masas` si en el futuro hay datos.

### A.3 Notas sobre cobertura

- **Cobertura >90%** (≥8/8 objetivos primarios): Hígado, Vejiga, Vesícula, Riñones, Intestino, Estómago, Bazo, Próstata.
- **Cobertura media (50-90%):** Adrenales, Gestación.
- **Cobertura baja (<30%):** Linfonodos, Páncreas, Útero, Testículos, Ovarios — descripciones breves en el corpus real. No es bug.
- **Regex a refinar en F3:** ⚠️ marcadas en las tablas (relacion_cm, contenido de Intestino, peristaltismo de Estómago, tamaño de Bazo).

---

## 14. Anexo B: `silver_conclusion_items` con `tipo_item`

### B.1 Definición de los 3 tipos

| `tipo_item` | Definición clínica | Rol en la conclusión |
|---|---|---|
| `diagnostico` | Enfermedad, condición o hallazgo interpretativo | Es el núcleo. "Nefropatía bilateral", "hepatomegalia severa". |
| `patron` | Descriptor morfológico o funcional que modifica un diagnóstico | Califica al diagnóstico. "Inflamatorio", "neoproliferativo", "infiltrativo", "graso". |
| `etiologia` | Descriptor causal o de origen | Explica el porqué. "Idiopático", "isquémico", "traumático", "infeccioso". |

**Ejemplo:**

Texto: *"Nefropatía bilateral moderada de aspecto inflamatorio. Hepatomegalia severa de aspecto infiltrativo graso."*

| término_original | termino_canonico | tipo_item | modificador | lateralidad |
|---|---|---|---|---|
| nefropatía | nefropatia | diagnostico | moderada | bilateral |
| inflamatorio | inflamatorio | patron | (heredado) | (n/a) |
| hepatomegalia | hepatomegalia | diagnostico | severa | (n/a) |
| infiltrativo | infiltrativo | patron | (n/a) | (n/a) |
| graso | graso | patron | (n/a) | (n/a) |

**Relación entre tipos:** un `diagnostico` se asocia a uno o más `patron` por ventana de texto; un `diagnostico` puede tener cero o un `etiologia`. No se modela la asociación como FK en v1 (se hace por proximidad textual).

### B.2 Diccionario seed `CONCLUSION_TERMS`

**Tipo `diagnostico` (18 términos):**

```python
DIAGNOSTICOS = {
    'nefropatía', 'hepatomegalia', 'microhepatia', 'hepatopatía',
    'cistitis', 'barro biliar', 'sedimento', 'colitis',
    'pancreatitis', 'esplenomegalia', 'enteritis', 'adrenomegalia',
    'colecistitis', 'quiste', 'piometra', 'litiasis', 'metritis',
    'hiperplasia', 'atrofia',
}
```

**Tipo `patron` (10 términos):**

```python
PATRONES = {
    'inflamatorio', 'neoproliferativo', 'hiperplasico',
    'infiltrativo', 'graso', 'vacuolar', 'mixto',
    'severo', 'agudo', 'crónico',
}
```

**Tipo `etiologia` (6 términos):**

```python
ETIOLOGIAS = {
    'idiopático', 'isquémico', 'traumático', 'infeccioso',
    'congénito', 'hereditario',
}
```

**Total seed: 34 términos** (algunos pueden solaparse con el catálogo de `dim_organo_atributo`; eso es OK porque viven en dimensiones distintas).

### B.3 Algoritmo de asignación de `tipo_item`

```python
CONCLUSION_TERMS = {
    'diagnostico': DIAGNOSTICOS,
    'patron': PATRONES,
    'etiologia': ETIOLOGIAS,
}

def extract_items(texto: str, informe_id: int) -> list[dict]:
    items = []
    texto_lower = texto.lower()
    seen_positions = set()  # evitar duplicados por overlap
    
    # 1. Detección por diccionario
    for tipo, terminos in CONCLUSION_TERMS.items():
        for termino in terminos:
            # Búsqueda por palabra completa
            for m in re.finditer(rf'\b{re.escape(termino)}\b', texto_lower):
                pos_key = (m.start(), m.end())
                if pos_key in seen_positions:
                    continue
                seen_positions.add(pos_key)
                
                termino_canonico = normalize(termino)
                modificador = extract_modifier(texto_lower, m.start(), m.end(), window=3)
                lateralidad = extract_lateralidad(texto_lower, m.start(), m.end(), window=2)
                
                items.append({
                    'informe_id': informe_id,
                    'termino_original': texto[m.start():m.end()],
                    'termino_canonico': termino_canonico,
                    'tipo_item': tipo,
                    'modificador': modificador,
                    'lateralidad': lateralidad,
                    'pos_inicio': m.start(),
                    'pos_fin': m.end(),
                    'confianza': 1.0,
                    'metodo_extraccion': 'diccionario_exacto',
                })
    
    # 2. Fuzzy match para typos (Levenshtein ≤ 1)
    #    Solo si freq en corpus > 2 (control de ruido)
    #    Default tipo_item = 'diagnostico' (conservador)
    
    return items
```

### B.4 Modificadores y lateralidad (transversal)

**Modificadores** (ventana de 3 palabras antes del término):

```python
MODIFICADORES = {
    r'\bleve(s)?\b': 'leve',
    r'\bmoderad[oa](s)?\b': 'moderada',
    r'\bsever[oa](s)?\b': 'severa',
    r'\bagud[oa](s)?\b': 'aguda',
    r'\bcr[oó]nic[oa](s)?\b': 'cronica',
}
```

**Lateralidad** (ventana de 2 palabras antes del término):

```python
LATERALIDADES = {
    r'\bbilateral(es)?\b': 'bilateral',
    r'\b(izquierd[oa]|izq\.?)\b': 'izquierdo',
    r'\b(derech[oa]|der\.?)\b': 'derecho',
}
```

### B.5 Términos no matcheados → fuzzy + log

Si un término aparece ≥2 veces en el corpus y no está en el diccionario, se inserta en `silver_conclusion_items` con `tipo_item='diagnostico'` (default conservador) y se loguea en `silver_revision_log` con `operacion='termino_nuevo'`. El operador decide en la revisión periódica si se agrega al diccionario o se descarta.

### B.6 Caso especial: `termino_canonico` no se queda en RAW

`termino_canonico` es una **normalización textual** (lowercase, strip, sin acentos opcionales), no una FK. Esto:

- Permite queries de Gold del tipo `GROUP BY termino_canonico` sin governance de dim.
- Permite agregar/editar la normalización sin migración de esquema.
- Si en el futuro hace falta un `dim_diagnostico` estricto (ej. con códigos CIE-10 veterinarios), se introduce como **dim derivada** a partir de `termino_canonico`, sin tocar la fact.

---

**Fin del documento.**

Próximos pasos al aprobar:

1. Crear `src/informes_vet/models_silver.py` con las 24 tablas.
2. Implementar `silver_dims.py::bootstrap_basico()` (Fase 1).
3. Crear `scripts/build_silver.py` CLI.
4. Configurar tests de cobertura.
5. Iterar Fases 2-7 según §10.
