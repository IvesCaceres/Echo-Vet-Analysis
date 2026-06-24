"""CLI driver para la construcción de la capa SILVER.

Uso típico:

    python scripts/build_silver.py --init                # crea silver.db con esquema vacío
    python scripts/build_silver.py --phase f1            # bootstrap dims + silver_informes
    python scripts/build_silver.py --phase f2            # map_* + dim_raza + staging
    python scripts/build_silver.py --phase f2_1          # refactor dim_raza + edad_meses
    python scripts/build_silver.py --reset --phase f1    # wipe + rebuild desde cero

Fase 1 sólo construye:
- 6 dimensiones base (dim_organo, dim_especie, dim_sexo,
  dim_estado_reproductivo, dim_estudio, dim_edad_categoria)
- silver_informes (1 fila por raw.informes)
- silver_etl_runs (operativa)

Fase 2 puebla map_especie/sexo/estudio, dim_raza, map_raza, stg_*.

Fase 2.1 (v2.1) consolida dim_raza (7 fusiones + DPC/DPL renames) y
re-calcula silver_informes.edad_meses + edad_parse_ok con parser robusto.

Fase 3 (v3.0) siembra dim_atributo (31) + dim_organo_atributo (62) +
dim_segmento_anatomico (6) + dim_valor_atributo (172) y extrae atributos
de silver_hallazgos via regex con soporte para segmento intestinal
(duodeno_yeyuno vs colon) y lateralidad (Riñones/Adrenales).

Fase 4 (v4.0) siembra el diccionario canónico de valores observados:
dim_valor_atributo (consolidado) + map_atributo_valor (por par
organo-atributo) y puebla silver_atributos_hallazgo.dim_valor_atributo_id
vía JOIN. Aplica consolidaciones de género morfológico, sinónimos y
presencia binaria.

Fase 5 (v5.0) siembra dim_termino_conclusion (catálogo de términos de
conclusiones, Opción C: DIAGNOSTICO + ETIOLOGIA + NEGATIVO), extrae los
ítems de raw.conclusiones con modificadores promovidos a columnas
(lateralidad, modificador_cualidad, modificador_distribucion) y los carga
en silver_conclusion_items + stg_conclusion_no_match. 100% basado en
regex + diccionarios (sin NLP, sin embeddings, sin LLMs).
"""

from __future__ import annotations

import argparse
import getpass
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# Forzar UTF-8 en stdout (Windows cp1252 rompe con caracteres acentuados y emojis)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Permitir `python scripts/build_silver.py` sin instalar el paquete
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy.engine import Engine  # noqa: E402

from informes_vet import db, silver_db, silver_dims, silver_etl  # noqa: E402
from informes_vet.silver_f4_values import build_f4 as _build_f4  # noqa: E402
from informes_vet.silver_f5_conclusions import build_f5 as _build_f5  # noqa: E402


def _print_metrics(metrics: dict, label: str) -> None:
    print(f"\n[{label}] métricas:")
    for k, v in metrics.items():
        print(f"  {k:30} {v}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build de la capa SILVER (Fase 1)")
    p.add_argument("--init", action="store_true",
                   help="Crea silver.db con el esquema completo vacío (idempotente)")
    p.add_argument("--phase", choices=("f1", "f2", "f2_1", "f3", "f4", "f5"), default="f1",
                   help="Fase del ETL a ejecutar (default: f1)")
    p.add_argument("--reset", action="store_true",
                   help="DROP + CREATE del esquema antes de la fase (WIPE)")
    p.add_argument("--dry-run", action="store_true",
                   help="No escribe en Silver; sólo imprime lo que haría")
    p.add_argument("--root", type=Path, default=Path.cwd(),
                   help="Raíz del proyecto (default: cwd)")
    p.add_argument("--actor", type=str, default=None,
                   help="Identificador del ejecutor (default: usuario del SO)")
    p.add_argument("--verbose", "-v", action="store_true")
    args = p.parse_args(argv)

    root: Path = args.root.resolve()
    actor = args.actor or getpass.getuser() or "build_silver"

    if args.verbose:
        print(f"[build_silver] root={root}")
        print(f"[build_silver] init={args.init}  phase={args.phase}  "
              f"reset={args.reset}  dry_run={args.dry_run}  actor={actor}")

    silver_path = root / "silver.db"
    if args.reset and silver_path.exists():
        print(f"[build_silver] --reset: borrando {silver_path.name}")
        silver_path.unlink()

    silver_engine: Engine = silver_db.get_engine(root)
    raw_engine: Engine = db.get_engine("sqlite", root)

    if args.init:
        print(f"[build_silver] creando esquema en {silver_path}...")
        silver_db.create_schema(silver_engine)
        print(f"[build_silver] esquema creado. Tablas:")
        with silver_engine.begin() as conn:
            rows = conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).all()
        for (name,) in rows:
            print(f"  - {name}")
        silver_engine.dispose()
        raw_engine.dispose()
        return 0

    if args.reset:
        print("[build_silver] --reset: drop + create del esquema Silver")
        silver_db.reset_schema(silver_engine)

    # Garantizar que el esquema existe aunque no se haya pasado --init
    silver_db.create_schema(silver_engine)

    # Aplicar migraciones pendientes (incluye v5.0 — DROP+CREATE de
    # silver_conclusion_items con esquema Opción C). Idempotente.
    print("[build_silver] aplicando migraciones pendientes...")
    mig_results = silver_db.migrate(silver_engine)
    for m in mig_results:
        if m["applied"]:
            print(f"  [OK] {m['version']} {m['name']}")
        # Silenciar las 'already_applied' (ruido en cada run)

    if args.dry_run:
        print("[build_silver] --dry-run: Bootstrap dims (en memoria, no escribe) y build_f1 omitido")
        silver_engine.dispose()
        raw_engine.dispose()
        return 0

    print(f"[build_silver] === Fase {args.phase.upper()} ===")

    if args.phase == "f1":
        t0 = time.monotonic()
        # 1) Bootstrap dims (idempotente)
        print("[f1] bootstrap de 6 dimensiones base...")
        dim_counts = silver_dims.bootstrap_basico(silver_engine)
        for nombre, n in dim_counts.items():
            print(f"  {nombre}: {n} filas insertadas (0 si ya existían)")

        # 2) Build silver_informes
        print("[f1] construyendo silver_informes desde raw.informes...")
        try:
            metrics = silver_etl.build_f1(silver_engine, raw_engine, actor=actor)
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[f1] ERROR: {e}\n{tb}")
            silver_etl._log_run(  # noqa: SLF001
                silver_engine, "f1", datetime.now(), datetime.now(), "error",
                rows_read=0, rows_written=0, rows_skipped=0,
                duration_ms=int((time.monotonic() - t0) * 1000),
                actor=actor, notes=f"{type(e).__name__}: {e}",
            )
            silver_engine.dispose()
            raw_engine.dispose()
            return 1

        elapsed = time.monotonic() - t0
        print(f"\n[f1] OK en {elapsed:.1f}s")
        _print_metrics(metrics, "f1")

        # 3) Verificación de cobertura
        with silver_engine.begin() as conn:
            n_silver = conn.exec_driver_sql(
                "SELECT COUNT(*) FROM silver_informes"
            ).scalar_one()
            n_raw = conn.exec_driver_sql(
                "SELECT COUNT(*) FROM raw.informes"
            ).scalar_one() if False else 0  # cross-db, evitamos
        with raw_engine.begin() as conn:
            n_raw = conn.exec_driver_sql("SELECT COUNT(*) FROM informes").scalar_one()
        print(f"\n[f1] cobertura silver_informes / raw.informes: {n_silver} / {n_raw}")
        if n_silver != n_raw:
            print(f"[f1] WARN: cobertura no es 100% (diff={n_silver - n_raw})")
        else:
            print(f"[f1] ✅ cobertura 100%")

        # 4) Distribución de dim_sexo/estudio
        with silver_engine.begin() as conn:
            print("\n[f1] distribución dim_sexo:")
            for r in conn.exec_driver_sql(
                "SELECT s.nombre_canonico, COUNT(*) FROM silver_informes si "
                "JOIN dim_sexo s ON s.id = si.dim_sexo_id GROUP BY s.nombre_canonico "
                "ORDER BY 2 DESC"
            ).all():
                print(f"  {r[0]}: {r[1]}")
            print("\n[f1] distribución dim_estudio:")
            for r in conn.exec_driver_sql(
                "SELECT e.nombre_canonico, COUNT(*) FROM silver_informes si "
                "JOIN dim_estudio e ON e.id = si.dim_estudio_id GROUP BY e.nombre_canonico "
                "ORDER BY 2 DESC"
            ).all():
                print(f"  {r[0]}: {r[1]}")
            print("\n[f1] distribución dim_edad_categoria:")
            for r in conn.exec_driver_sql(
                "SELECT ec.nombre, COUNT(*) FROM silver_informes si "
                "LEFT JOIN dim_edad_categoria ec ON ec.id = si.dim_edad_categoria_id "
                "GROUP BY ec.nombre ORDER BY 2 DESC"
            ).all():
                print(f"  {r[0]}: {r[1]}")
            print("\n[f1] distribución dim_especie:")
            for r in conn.exec_driver_sql(
                "SELECT e.nombre_canonico, COUNT(*) FROM silver_informes si "
                "LEFT JOIN dim_especie e ON e.id = si.dim_especie_id "
                "GROUP BY e.nombre_canonico ORDER BY 2 DESC"
            ).all():
                print(f"  {r[0]}: {r[1]}")
            print("\n[f1] distribución dim_estado_reproductivo:")
            for r in conn.exec_driver_sql(
                "SELECT er.nombre_canonico, COUNT(*) FROM silver_informes si "
                "JOIN dim_estado_reproductivo er ON er.id = si.dim_estado_reproductivo_id "
                "GROUP BY er.nombre_canonico ORDER BY 2 DESC"
            ).all():
                print(f"  {r[0]}: {r[1]}")
            print("\n[f1] cobertura fecha_parseada:")
            for r in conn.exec_driver_sql(
                "SELECT "
                "  COUNT(*) AS total, "
                "  SUM(CASE WHEN fecha_parseada IS NOT NULL THEN 1 ELSE 0 END) AS con_fecha, "
                "  ROUND(100.0 * SUM(CASE WHEN fecha_parseada IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct "
                "FROM silver_informes"
            ).all():
                print(f"  total={r[0]}  con_fecha={r[1]}  cobertura={r[2]}%")

        # 5) silver_etl_runs
        with silver_engine.begin() as conn:
            print("\n[f1] silver_etl_runs (último run):")
            for r in conn.exec_driver_sql(
                "SELECT id, phase, status, rows_read, rows_written, duration_ms, actor "
                "FROM silver_etl_runs ORDER BY id DESC LIMIT 1"
            ).all():
                print(f"  id={r[0]}  phase={r[1]}  status={r[2]}  "
                      f"read={r[3]}  written={r[4]}  dur={r[5]}ms  actor={r[6]}")

    if args.phase == "f2":
        t0 = time.monotonic()
        print("[f2] poblando map_especie/sexo/estudio, dim_raza, map_raza, stg_*...")
        try:
            metrics = silver_etl.build_f2(silver_engine, raw_engine, actor=actor)
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[f2] ERROR: {e}\n{tb}")
            silver_etl._log_run(  # noqa: SLF001
                silver_engine, "f2", datetime.now(), datetime.now(), "error",
                rows_read=0, rows_written=0, rows_skipped=0,
                duration_ms=int((time.monotonic() - t0) * 1000),
                actor=actor, notes=f"{type(e).__name__}: {e}",
            )
            silver_engine.dispose()
            raw_engine.dispose()
            return 1

        elapsed = time.monotonic() - t0
        print(f"\n[f2] OK en {elapsed:.2f}s")
        _print_metrics(metrics, "f2")

        with silver_engine.begin() as conn:
            print("\n[f2] cobertura por dimensión (sil → dim_id NO NULL):")
            for tabla, col in [
                ("map_especie", "dim_especie_id"),
                ("map_sexo", "dim_sexo_id"),
                ("map_estudio", "dim_estudio_id"),
                ("map_raza", "dim_raza_id"),
            ]:
                r = conn.exec_driver_sql(
                    f"SELECT COUNT(*), "
                    f"SUM(CASE WHEN {col} IS NOT NULL THEN 1 ELSE 0 END) "
                    f"FROM {tabla}"
                ).first()
                if r[0]:
                    pct = round(100.0 * r[1] / r[0], 2)
                    print(f"  {tabla}.{col}: {r[1]} / {r[0]}  ({pct}%)")

            print("\n[f2] distribución map_raza.estado_revision:")
            for r in conn.exec_driver_sql(
                "SELECT estado_revision, COUNT(*) FROM map_raza "
                "GROUP BY estado_revision ORDER BY 2 DESC"
            ).all():
                print(f"  {r[0]}: {r[1]}")

            print("\n[f2] stg_valores_no_mapeados (por dimension):")
            for r in conn.exec_driver_sql(
                "SELECT dimension, COUNT(*) FROM stg_valores_no_mapeados "
                "GROUP BY dimension ORDER BY 2 DESC"
            ).all():
                print(f"  {r[0]}: {r[1]}")

            print("\n[f2] stg_razas_detectadas (top 10 por frecuencia):")
            for r in conn.exec_driver_sql(
                "SELECT valor_original, frecuencia, estado_revision FROM stg_razas_detectadas "
                "ORDER BY frecuencia DESC LIMIT 10"
            ).all():
                print(f"  {r[0]!r:40} freq={r[1]:4} estado={r[2]}")

            print("\n[f2] dim_raza:")
            for r in conn.exec_driver_sql(
                "SELECT nombre_canonico, dim_especie_id, es_mestizo FROM dim_raza "
                "ORDER BY id LIMIT 30"
            ).all():
                print(f"  {r[0]!r:40}  esp_id={r[1]}  mestizo={r[2]}")

            print("\n[f2] silver_etl_runs (último run):")
            for r in conn.exec_driver_sql(
                "SELECT id, phase, status, rows_read, rows_written, duration_ms, actor "
                "FROM silver_etl_runs ORDER BY id DESC LIMIT 1"
            ).all():
                print(f"  id={r[0]}  phase={r[1]}  status={r[2]}  "
                      f"read={r[3]}  written={r[4]}  dur={r[5]}ms  actor={r[6]}")

    if args.phase == "f2_1":
        t0 = time.monotonic()
        print("[f2_1] refactor dim_raza + DPC/DPL + backfill edad_meses...")
        try:
            metrics = silver_etl.build_f2_1(silver_engine, raw_engine, actor=actor)
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[f2_1] ERROR: {e}\n{tb}")
            silver_etl._log_run(  # noqa: SLF001
                silver_engine, "f2_1", datetime.now(), datetime.now(), "error",
                rows_read=0, rows_written=0, rows_skipped=0,
                duration_ms=int((time.monotonic() - t0) * 1000),
                actor=actor, notes=f"{type(e).__name__}: {e}",
            )
            silver_engine.dispose()
            raw_engine.dispose()
            return 1

        elapsed = time.monotonic() - t0
        print(f"\n[f2_1] OK en {elapsed:.2f}s")
        _print_metrics(metrics, "f2_1")

        # Reporte de migrations aplicadas
        print("\n[f2_1] migraciones aplicadas:")
        for m in metrics["migrations"]:
            print(f"  {m}")

        # Reporte de refactor dim_raza
        ref = metrics["refactor_dim_raza"]
        print(f"\n[f2_1] refactor dim_raza:")
        print(f"  ya aplicado: {ref['already_applied']}")
        print(f"  merges: {ref['merges']}")
        print(f"  renames: {ref['renames']}")
        print(f"  deletes: {ref['deletes']}")
        print(f"  map_raza redirects: {ref['map_redirects']}")

        # Reporte de cobertura edad
        ed = metrics["edad"]
        print(f"\n[f2_1] cobertura edad_meses:")
        print(f"  rows_scanned: {ed['rows_scanned']}")
        print(f"  rows_updated: {ed['rows_updated']}")
        print(f"  parse_cobertura: {ed['parse_coverage_pct']}%")
        print(f"  n_unparsed: {ed['n_unparsed']}")
        if ed["unparsed_examples"]:
            print(f"  ejemplos no parseados:")
            for k, v in sorted(ed["unparsed_examples"].items(), key=lambda x: -x[1]):
                print(f"    [{v:3}] {k!r}")

        # dim_raza final
        with silver_engine.begin() as conn:
            print(f"\n[f2_1] dim_raza final:")
            for r in conn.exec_driver_sql(
                "SELECT nombre_canonico, dim_especie_id, es_mestizo FROM dim_raza "
                "ORDER BY id"
            ).all():
                print(f"  {r[0]!r:40}  esp_id={r[1]}  mestizo={r[2]}")

            # Cobertura map_raza
            print(f"\n[f2_1] map_raza: cobertura dim_raza_id:")
            r = conn.exec_driver_sql(
                "SELECT COUNT(*), "
                "SUM(CASE WHEN dim_raza_id IS NOT NULL THEN 1 ELSE 0 END) "
                "FROM map_raza"
            ).first()
            if r[0]:
                pct = round(100.0 * r[1] / r[0], 2)
                print(f"  map_raza.dim_raza_id NOT NULL: {r[1]} / {r[0]}  ({pct}%)")

            # Edad distribución
            print(f"\n[f2_1] distribución dim_edad_categoria (post-refactor):")
            for r in conn.exec_driver_sql(
                "SELECT ec.nombre, COUNT(*) FROM silver_informes si "
                "LEFT JOIN dim_edad_categoria ec ON ec.id = si.dim_edad_categoria_id "
                "GROUP BY ec.nombre ORDER BY 2 DESC"
            ).all():
                print(f"  {r[0]}: {r[1]}")

            # silver_etl_runs
            print("\n[f2_1] silver_etl_runs (último run):")
            for r in conn.exec_driver_sql(
                "SELECT id, phase, status, rows_read, rows_written, duration_ms, actor "
                "FROM silver_etl_runs ORDER BY id DESC LIMIT 1"
            ).all():
                print(f"  id={r[0]}  phase={r[1]}  status={r[2]}  "
                      f"read={r[3]}  written={r[4]}  dur={r[5]}ms  actor={r[6]}")

    if args.phase == "f3":
        t0 = time.monotonic()
        print("[f3] extrayendo atributos clínicos (Fase 3)...")
        try:
            metrics = silver_etl.build_f3(silver_engine, raw_engine, actor=actor)
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[f3] ERROR: {e}\n{tb}")
            silver_etl._log_run(  # noqa: SLF001
                silver_engine, "f3", datetime.now(), datetime.now(), "error",
                rows_read=0, rows_written=0, rows_skipped=0,
                duration_ms=int((time.monotonic() - t0) * 1000),
                actor=actor, notes=f"{type(e).__name__}: {e}",
            )
            silver_engine.dispose()
            raw_engine.dispose()
            return 1

        elapsed = time.monotonic() - t0
        print(f"\n[f3] OK en {elapsed:.2f}s")
        _print_metrics(metrics, "f3")

        print("\n[f3] migraciones aplicadas:")
        for m in metrics["migrations"]:
            print(f"  {m}")

        bdf3 = metrics["bootstrap_dims_f3"]
        print("\n[f3] bootstrap dimensiones F3:")
        for k, v in bdf3.items():
            print(f"  {k}: {v} filas insertadas")
        dva = metrics["bootstrap_dim_valor_atributo"]
        print(f"\n[f3] dim_valor_atributo: {dva['dim_valor_atributo']} filas insertadas "
              f"({dva['n_valores_propuestos']} propuestas)")

        ext = metrics["extract"]
        print("\n[f3] extracción de atributos:")
        print(f"  hallazgos leídos:            {ext['n_hallazgos_leidos']}")
        print(f"  hallazgos con ≥1 atributo:   {ext['n_hallazgos_with_attrs']}")
        print(f"  atributos extraídos:         {ext['n_atributos_extraidos']}")
        print(f"  atributos insertados:        {ext['n_atributos_insertados']}")
        if ext["n_segmented"]:
            print("  hallazgos segmentados:")
            for k, v in ext["n_segmented"].items():
                print(f"    {k}: {v}")
        if ext["n_lateralidad"]:
            print("  hallazgos con lateralidad:")
            for k, v in ext["n_lateralidad"].items():
                print(f"    {k}: {v}")

        with silver_engine.begin() as conn:
            print("\n[f3] top 15 pares (organo, atributo) extraídos:")
            rows = conn.exec_driver_sql(
                "SELECT o.nombre_canonico, a.nombre_canonico, COUNT(*) AS n "
                "FROM silver_atributos_hallazgo s "
                "JOIN dim_organo o ON o.id = s.dim_organo_id "
                "JOIN dim_organo_atributo oa ON oa.id = s.dim_organo_atributo_id "
                "JOIN dim_atributo a ON a.id = oa.dim_atributo_id "
                "GROUP BY o.nombre_canonico, a.nombre_canonico "
                "ORDER BY n DESC LIMIT 15"
            ).all()
            for org, attr, n in rows:
                print(f"  {org:25} {attr:30} {n:6}")

            print("\n[f3] distribución lateralidad (Riñones/Adrenales):")
            for r in conn.exec_driver_sql(
                "SELECT COALESCE(lateralidad,'(sin)') AS lat, COUNT(*) "
                "FROM silver_atributos_hallazgo "
                "WHERE dim_organo_id IN (SELECT id FROM dim_organo "
                "                         WHERE nombre_canonico IN ('Riñones','Adrenales')) "
                "GROUP BY lat ORDER BY 2 DESC"
            ).all():
                print(f"  {r[0]:12} {r[1]}")

            print("\n[f3] silver_etl_runs (último run):")
            for r in conn.exec_driver_sql(
                "SELECT id, phase, status, rows_read, rows_written, duration_ms, actor "
                "FROM silver_etl_runs ORDER BY id DESC LIMIT 1"
            ).all():
                print(f"  id={r[0]}  phase={r[1]}  status={r[2]}  "
                      f"read={r[3]}  written={r[4]}  dur={r[5]}ms  actor={r[6]}")

    if args.phase == "f4":
        t0 = time.monotonic()
        print("[f4] construyendo diccionario canónico de valores clínicos...")
        try:
            metrics = _build_f4(silver_engine)
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[f4] ERROR: {e}\n{tb}")
            silver_etl._log_run(  # noqa: SLF001
                silver_engine, "f4", datetime.now(), datetime.now(), "error",
                rows_read=0, rows_written=0, rows_skipped=0,
                duration_ms=int((time.monotonic() - t0) * 1000),
                actor=actor, notes=f"{type(e).__name__}: {e}",
            )
            silver_engine.dispose()
            raw_engine.dispose()
            return 1

        elapsed = time.monotonic() - t0
        print(f"\n[f4] OK en {elapsed:.2f}s")
        _print_metrics(metrics, "f4")

        # dim_valor_atributo
        dva = metrics["dim_valor_atributo"]
        print(f"\n[f4] dim_valor_atributo:")
        print(f"  filas insertadas:           {dva['n_dim_valor']}")
        print(f"  atributos distintos:        {dva['n_atributos']}")
        print(f"  observaciones únicas:       {dva['n_observaciones_unicas']}")
        print(f"  huérfanos (sin cobertura):  {dva['n_huérfanos']}")

        # map_atributo_valor
        mav = metrics["map_atributo_valor"]
        print(f"\n[f4] map_atributo_valor:")
        print(f"  filas insertadas:           {mav['n_map']}")
        print(f"  pares (doe_id, val_orig) únicos: {mav['n_pairs_unicos']}")
        print(f"  observaciones cubiertas:    {mav['n_observaciones']}")

        # consolidation
        cons = metrics["consolidation"]
        print(f"\n[f4] apply_consolidation_to_silver:")
        print(f"  filas leídas:               {cons['n_total']}")
        print(f"  filas modificadas:          {cons['n_changed']}")
        print(f"  filas sin cambio:           {cons['n_unchanged']}")
        if cons["by_rule"]:
            print(f"  por regla de consolidación:")
            for regla, n in sorted(cons["by_rule"].items(), key=lambda x: -x[1]):
                print(f"    {regla}: {n}")

        # FK
        fk = metrics["fk"]
        print(f"\n[f4] silver_atributos_hallazgo.dim_valor_atributo_id:")
        print(f"  filas con valor_canonico:   {fk['n_filas_con_valor']}")
        print(f"  pobladas en este run:       {fk['n_poblados']}")
        print(f"  huérfanos pre-update:       {fk['n_huérfanos_pre']}")
        print(f"  huérfanos post-update:      {fk['n_huérfanos_post']}")

        # Cobertura global y cobertura final
        with silver_engine.begin() as conn:
            n_con_valor = conn.exec_driver_sql(
                "SELECT COUNT(*) FROM silver_atributos_hallazgo "
                "WHERE valor_canonico IS NOT NULL"
            ).scalar_one()
            n_con_fk = conn.exec_driver_sql(
                "SELECT COUNT(*) FROM silver_atributos_hallazgo "
                "WHERE dim_valor_atributo_id IS NOT NULL"
            ).scalar_one()
        cobertura_pct = round(100.0 * n_con_fk / n_con_valor, 2) if n_con_valor else 0
        print(f"\n[f4] cobertura dim_valor_atributo_id: "
              f"{n_con_fk} / {n_con_valor}  ({cobertura_pct}%)")
        if cobertura_pct == 100.0:
            print("[f4] ✅ cobertura 100% — diccionario completo")
        else:
            print(f"[f4] ⚠ cobertura {cobertura_pct}% — revisar huérfanos")

        # Distribución origen de consolidación
        with silver_engine.begin() as conn:
            print("\n[f4] map_atributo_valor.origen (distribución):")
            for r in conn.exec_driver_sql(
                "SELECT origen, COUNT(*) FROM map_atributo_valor "
                "GROUP BY origen ORDER BY 2 DESC"
            ).all():
                print(f"  {r[0] or '(NULL)'}: {r[1]}")

            # Top valores consolidados (los que más se repiten)
            print("\n[f4] top 10 valores consolidados (dim_valor_atributo):")
            for r in conn.exec_driver_sql(
                "SELECT da.nombre_canonico AS atributo, dva.valor, dva.orden, "
                "       (SELECT COUNT(*) FROM silver_atributos_hallazgo s "
                "        WHERE s.dim_valor_atributo_id = dva.id) AS freq "
                "FROM dim_valor_atributo dva "
                "JOIN dim_atributo da ON da.id = dva.atributo_id "
                "ORDER BY freq DESC LIMIT 10"
            ).all():
                print(f"  {r[0]:25} {r[1]:25} orden={r[2]:2} freq={r[3]}")

        # silver_etl_runs (no se loguea dentro de build_f4; lo logueamos acá)
        silver_etl._log_run(  # noqa: SLF001
            silver_engine, "f4", datetime.now(), datetime.now(), "ok",
            rows_read=metrics["dim_valor_atributo"]["n_observaciones_unicas"],
            rows_written=(
                metrics["dim_valor_atributo"]["n_dim_valor"]
                + metrics["map_atributo_valor"]["n_map"]
            ),
            rows_skipped=metrics["fk"]["n_huérfanos_post"],
            duration_ms=int((time.monotonic() - t0) * 1000),
            actor=actor, notes=str(metrics),
        )
        with silver_engine.begin() as conn:
            print("\n[f4] silver_etl_runs (último run):")
            for r in conn.exec_driver_sql(
                "SELECT id, phase, status, rows_read, rows_written, duration_ms, actor "
                "FROM silver_etl_runs ORDER BY id DESC LIMIT 1"
            ).all():
                print(f"  id={r[0]}  phase={r[1]}  status={r[2]}  "
                      f"read={r[3]}  written={r[4]}  dur={r[5]}ms  actor={r[6]}")

    if args.phase == "f5":
        t0 = time.monotonic()
        print("[f5] construyendo silver_conclusion_items (Opción C)...")
        try:
            metrics = _build_f5(silver_engine, raw_engine)
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[f5] ERROR: {e}\n{tb}")
            silver_etl._log_run(  # noqa: SLF001
                silver_engine, "f5", datetime.now(), datetime.now(), "error",
                rows_read=0, rows_written=0, rows_skipped=0,
                duration_ms=int((time.monotonic() - t0) * 1000),
                actor=actor, notes=f"{type(e).__name__}: {e}",
            )
            silver_engine.dispose()
            raw_engine.dispose()
            return 1

        elapsed = time.monotonic() - t0
        print(f"\n[f5] OK en {elapsed:.2f}s")
        _print_metrics(metrics["extract"], "f5 extract")

        # Métricas de seed
        dtc = metrics["dim_termino_conclusion"]
        print(f"\n[f5] dim_termino_conclusion:")
        print(f"  filas nuevas en este run: {dtc['n_insertados']}")
        print(f"  filas totales:            {dtc['n_total']}")

        # Métricas de silver_conclusion_items
        sci = metrics["silver_conclusion_items"]
        print(f"\n[f5] silver_conclusion_items:")
        print(f"  filas eliminadas (rebuild): {sci['n_deleted']}")
        print(f"  filas insertadas:           {sci['n_inserted']}")

        # Métricas de stg_conclusion_no_match
        stg = metrics["stg_conclusion_no_match"]
        print(f"\n[f5] stg_conclusion_no_match:")
        print(f"  filas eliminadas (rebuild): {stg['n_deleted']}")
        print(f"  filas insertadas:           {stg['n_inserted']}")

        # Métricas de dim_frecuencias
        df = metrics["dim_frecuencias"]
        print(f"\n[f5] dim_termino_conclusion.frecuencia_rank:")
        print(f"  actualizados con datos:     {df['n_actualizados']}")
        print(f"  marcados sin uso:           {df['n_sin_uso']}")

        # Cobertura
        ext = metrics["extract"]
        pct = round(100.0 * ext["n_conclusiones_con_items"] / ext["n_conclusiones_total"], 2)
        print(f"\n[f5] cobertura:")
        print(f"  conclusiones con >=1 item:  {ext['n_conclusiones_con_items']} / "
              f"{ext['n_conclusiones_total']} ({pct}%)")
        print(f"  items/conclusion:           {ext['items_per_conclusion']}")

        # Top 20 términos
        counters = metrics["_counters"]
        print(f"\n[f5] Top 20 términos canónicos:")
        for i, (term, freq) in enumerate(list(counters["term"].items())[:20], 1):
            print(f"  {i:>2}. {term:30s} {freq:>6,}")

        # Distribución por tipo_item (JOIN con dim_termino_conclusion)
        with silver_engine.begin() as conn:
            print(f"\n[f5] distribución por tipo_item:")
            for r in conn.exec_driver_sql(
                "SELECT dtc.tipo_item, COUNT(*) "
                "FROM silver_conclusion_items sci "
                "JOIN dim_termino_conclusion dtc ON dtc.id = sci.termino_conclusion_id "
                "GROUP BY dtc.tipo_item ORDER BY 2 DESC"
            ).all():
                print(f"  {r[0]:14} {r[1]:>6,}")

            # Distribución de modificadores
            print(f"\n[f5] top modificador_cualidad:")
            for r in conn.exec_driver_sql(
                "SELECT COALESCE(modificador_cualidad,'(sin)') AS m, COUNT(*) "
                "FROM silver_conclusion_items "
                "GROUP BY m ORDER BY 2 DESC LIMIT 10"
            ).all():
                print(f"  {r[0]:15} {r[1]:>6,}")

            print(f"\n[f5] top modificador_distribucion:")
            for r in conn.exec_driver_sql(
                "SELECT COALESCE(modificador_distribucion,'(sin)') AS m, COUNT(*) "
                "FROM silver_conclusion_items "
                "GROUP BY m ORDER BY 2 DESC LIMIT 10"
            ).all():
                print(f"  {r[0]:15} {r[1]:>6,}")

            print(f"\n[f5] top lateralidad:")
            for r in conn.exec_driver_sql(
                "SELECT COALESCE(lateralidad,'(sin)') AS m, COUNT(*) "
                "FROM silver_conclusion_items "
                "GROUP BY m ORDER BY 2 DESC LIMIT 10"
            ).all():
                print(f"  {r[0]:15} {r[1]:>6,}")

            # Items negados
            print(f"\n[f5] items con negado=TRUE:")
            n_neg = conn.exec_driver_sql(
                "SELECT COUNT(*) FROM silver_conclusion_items WHERE negado = 1"
            ).scalar_one()
            n_total = conn.exec_driver_sql(
                "SELECT COUNT(*) FROM silver_conclusion_items"
            ).scalar_one()
            print(f"  {n_neg} / {n_total} ({round(100*n_neg/n_total, 2) if n_total else 0}%)")

        # silver_etl_runs
        silver_etl._log_run(  # noqa: SLF001
            silver_engine, "f5", datetime.now(), datetime.now(), "ok",
            rows_read=ext["n_conclusiones_total"],
            rows_written=sci["n_inserted"] + stg["n_inserted"],
            rows_skipped=0,
            duration_ms=int((time.monotonic() - t0) * 1000),
            actor=actor, notes=str(metrics["extract"]),
        )
        with silver_engine.begin() as conn:
            print(f"\n[f5] silver_etl_runs (último run):")
            for r in conn.exec_driver_sql(
                "SELECT id, phase, status, rows_read, rows_written, duration_ms, actor "
                "FROM silver_etl_runs ORDER BY id DESC LIMIT 1"
            ).all():
                print(f"  id={r[0]}  phase={r[1]}  status={r[2]}  "
                      f"read={r[3]}  written={r[4]}  dur={r[5]}ms  actor={r[6]}")

    silver_engine.dispose()
    raw_engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())