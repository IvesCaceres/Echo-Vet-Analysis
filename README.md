# Informes Ecográficos Veterinarios

Pipeline reproducible para extraer información estructurada desde informes ecográficos veterinarios en formato `.docx` y cargarlos en una base de datos relacional (SQLite local o PostgreSQL).

## Estructura

```
.
├── Ecografía 2022/   # ~3 informes
├── Ecografía 2023/
├── Ecografía 2024/
├── Ecografía 2025/
├── Ecografía 2026/
├── src/informes_vet/   # paquete principal
├── scripts/run_ingest.py
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## Instalación

```bash
python -m venv venvvector
venvvector\Scripts\activate
pip install -r requirements.txt
```

## Uso

```bash
# 1) Validar localmente (SQLite, fresh start)
python scripts/run_ingest.py --db sqlite --reset

# 2) Smoke test de un año
python scripts/run_ingest.py --year-filter 2024 --limit 20 --dry-run

# 3) Wipear y poblar el VPS (PostgreSQL)
python scripts/run_ingest.py --db postgres --reset

# 4) Re-ejecución idempotente (no --reset, salta duplicados)
python scripts/run_ingest.py --db sqlite
```

## Tests

```bash
python -m unittest discover tests
```

## Configuración PostgreSQL

Copiar `.env.example` a `.env` y editar `PG_DSN` con la cadena de conexión real:

```
PG_DSN=postgresql+psycopg://usuario:password@host:puerto/dbname
```

## Capas de datos

- **`veterinaria_raw`** — extracción original, inmutable, recreable desde DOCX. Tablas: `informes`, `hallazgos`, `conclusiones`, `errores_ingesta`, `embeddings` (vacía en v1).
- **`veterinaria_analytics`** — futura, se construye con Pandas desde RAW.
- **`veterinaria_features`** — documentada, no implementada en v1.

## Edge cases manejados

- Tablas 6×6 (antiguas) y 7×7 (modernas con fila vacía inicial).
- Merges horizontales en `Antecedentes` y `Fecha` (celdas repetidas → dedupe).
- Estudios gestacionales (sin lista de órganos canónicos → fallback `organo="Gestación"`).
- Archivos basura filtrados al escanear: `~$*` (Word lock), `._*` (macOS AppleDouble), `.DS_Store`, `*.pdf`.

## Próximas etapas (no en v1)

- Validación de calidad de RAW.
- Construcción de `veterinaria_analytics` con Pandas.
- Generación de embeddings (script aparte: `scripts/generate_embeddings.py`) sobre `hallazgos.descripcion` y `conclusiones.texto_completo`.
