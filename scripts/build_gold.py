"""CLI driver para la construcción de la capa GOLD.

Uso típico:

    python scripts/build_gold.py --init                  # crea gold.db con esquema vacío
    python scripts/build_gold.py --phase all             # todas las tablas + views
    python scripts/build_gold.py --phase diag            # solo gold_diagnosticos
    python scripts/build_gold.py --phase demo            # solo gold_demografia
    python scripts/build_gold.py --phase hall            # solo gold_hallazgos
    python scripts/build_gold.py --phase views           # solo recrea las 2 VIEWs
    python scripts/build_gold.py --reset --phase all     # wipe + rebuild desde cero

Orden de dependencias:
    diag  →  demo  →  hall  →  views
    (las VIEWs referencian tablas gold_*, por eso se crean al final)

Por cada fase, build_gold:
1. Abre conexión a gold.db
2. ATTACH silver.db (siempre que la fase requiera leer de Silver)
3. ATTACH raw.db (solo si la fase incluye demo, por cross-layer a raza_raw)
4. DELETE + INSERT (idempotente)
5. Loguea en gold_etl_runs
6. DETACH / dispose

Si una fase falla, registra el error en gold_etl_runs (status='error')
y devuelve exit code 1.
"""

from __future__ import annotations

import argparse
import getpass
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# Forzar UTF-8 en stdout (Windows cp1252 rompe con caracteres acentuados)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Permitir `python scripts/build_gold.py` sin instalar el paquete
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy.engine import Engine  # noqa: E402

from informes_vet import db as raw_db  # noqa: E402
from informes_vet import gold  # noqa: E402
from informes_vet import silver_db  # noqa: E402


def _print_metrics(metrics: dict, label: str) -> None:
    print(f"\n[{label}] métricas:")
    for k, v in metrics.items():
        print(f"  {k:30} {v}")


def _phase_needs_silver(phase: str) -> bool:
    return phase in ("diag", "demo", "hall", "all")


def _phase_needs_raw(phase: str) -> bool:
    """raw.db solo es necesario para demografia (cross-layer a raza_raw)."""
    return phase in ("demo", "all")


def _run_phase(
    gold_engine: Engine,
    silver_engine: Engine | None,
    raw_engine: Engine | None,
    phase: str,
    actor: str,
) -> dict[str, Any]:
    """Ejecuta UNA fase de Gold (diag/demo/hall/views). Devuelve metrics."""
    t0 = time.monotonic()
    started_at = datetime.now()
    rows_read = 0
    rows_written = 0
    status = "ok"
    notes_extra: dict[str, Any] = {}

    try:
        with gold_engine.begin() as conn:
            # ATTACH solo si la fase lo requiere
            attached: dict[str, bool] = {}
            if _phase_needs_silver(phase):
                silver_path = silver_engine.url.database
                attached.update(gold.attach_databases(
                    conn, silver_path=silver_path
                ))
            if _phase_needs_raw(phase):
                raw_path = raw_engine.url.database
                attached.update(gold.attach_databases(
                    conn, raw_path=raw_path
                ))
            notes_extra["attached"] = attached

            if phase == "diag":
                rows_written = gold.build_gold_diagnosticos(conn)
            elif phase == "demo":
                rows_written = gold.build_gold_demografia(conn)
            elif phase == "hall":
                rows_written = gold.build_gold_hallazgos(conn)
            elif phase == "views":
                n_views = gold.create_gold_views(conn)
                rows_written = n_views
                notes_extra["n_views_created"] = n_views

            # DETACH best-effort (se cierra la tx de todas formas)
            gold.detach_databases(conn, "silver", "raw")

        elapsed_ms = int((time.monotonic() - t0) * 1000)
        finished_at = datetime.now()

        notes = f"{notes_extra}"
        gold.log_run(
            gold_engine, phase, started_at, finished_at, status,
            rows_read=rows_read,
            rows_written=rows_written,
            rows_skipped=0,
            rows_errored=0,
            duration_ms=elapsed_ms,
            actor=actor,
            notes=notes,
        )

        return {
            "phase": phase,
            "status": status,
            "rows_read": rows_read,
            "rows_written": rows_written,
            "duration_ms": elapsed_ms,
            **notes_extra,
        }

    except Exception as e:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        finished_at = datetime.now()
        status = "error"
        tb = traceback.format_exc()
        print(f"[{phase}] ERROR: {e}\n{tb}")
        gold.log_run(
            gold_engine, phase, started_at, finished_at, status,
            rows_read=0,
            rows_written=0,
            rows_skipped=0,
            rows_errored=1,
            duration_ms=elapsed_ms,
            actor=actor,
            notes=f"{type(e).__name__}: {e}",
        )
        raise


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build de la capa GOLD")
    p.add_argument("--init", action="store_true",
                   help="Crea gold.db con el esquema completo vacío (idempotente)")
    p.add_argument(
        "--phase",
        choices=("diag", "demo", "hall", "views", "all"),
        default="all",
        help="Fase del ETL a ejecutar (default: all)",
    )
    p.add_argument("--reset", action="store_true",
                   help="DROP + CREATE del esquema antes de la fase (WIPE)")
    p.add_argument("--db", choices=("sqlite", "postgres"), default="sqlite",
                   help="Motor de DB (default: sqlite)")
    p.add_argument("--root", type=Path, default=Path.cwd(),
                   help="Raíz del proyecto (default: cwd)")
    p.add_argument("--actor", type=str, default=None,
                   help="Identificador del ejecutor (default: usuario del SO)")
    p.add_argument("--verbose", "-v", action="store_true")
    args = p.parse_args(argv)

    root: Path = args.root.resolve()
    actor = args.actor or getpass.getuser() or "build_gold"

    if args.verbose:
        print(f"[build_gold] root={root}")
        print(f"[build_gold] init={args.init}  phase={args.phase}  "
              f"reset={args.reset}  db={args.db}  actor={actor}")

    gold_path = root / "gold.db"
    if args.reset and gold_path.exists():
        print(f"[build_gold] --reset: borrando {gold_path.name}")
        gold_path.unlink()

    gold_engine: Engine = gold.get_engine(root, db_kind=args.db)
    silver_engine: Engine | None = (
        silver_db.get_engine(root, db_kind=args.db)
        if _phase_needs_silver(args.phase) else None
    )
    raw_engine: Engine | None = (
        raw_db.get_engine("sqlite", root)  # SQLite hardcoded para raw
        if _phase_needs_raw(args.phase) else None
    )

    if args.init:
        print(f"[build_gold] creando esquema en {gold_path}...")
        gold.create_schema(gold_engine)
        print("[build_gold] esquema creado. Tablas:")
        with gold_engine.begin() as conn:
            rows = conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).all()
        for (name,) in rows:
            print(f"  - {name}")
        # Crear también las VIEWs (--init deja el gold.db listo para usar)
        print("[build_gold] creando VIEWs...")
        with gold_engine.begin() as conn:
            n = gold.create_gold_views(conn)
        print(f"[build_gold] {n} VIEWs creadas.")
        gold_engine.dispose()
        if silver_engine is not None:
            silver_engine.dispose()
        if raw_engine is not None:
            raw_engine.dispose()
        return 0

    if args.reset:
        print("[build_gold] --reset: drop + create del esquema Gold")
        gold.reset_schema(gold_engine)

    # Garantizar que el esquema existe aunque no se haya pasado --init
    gold.create_schema(gold_engine)

    # Determinar fases a ejecutar (en orden: diag → demo → hall → views)
    if args.phase == "all":
        phases = ("diag", "demo", "hall", "views")
    else:
        phases = (args.phase,)

    overall_metrics: list[dict] = []
    print(f"[build_gold] === Fases a ejecutar: {phases} ===")
    for phase in phases:
        print(f"\n[build_gold] --- Fase {phase} ---")
        try:
            metrics = _run_phase(
                gold_engine, silver_engine, raw_engine, phase, actor,
            )
        except Exception:
            gold_engine.dispose()
            if silver_engine is not None:
                silver_engine.dispose()
            if raw_engine is not None:
                raw_engine.dispose()
            return 1

        print(f"[{phase}] OK en {metrics['duration_ms']}ms — "
              f"rows_written={metrics['rows_written']}")
        _print_metrics({k: v for k, v in metrics.items()
                        if k not in ("phase",)}, phase)
        overall_metrics.append(metrics)

    # Reporte final
    print("\n" + "=" * 70)
    print("RESUMEN GOLD")
    print("=" * 70)
    for m in overall_metrics:
        print(f"  {m['phase']:8} status={m['status']:6} "
              f"written={m['rows_written']:>8} dur={m['duration_ms']:>5}ms")
    total_rows = sum(m["rows_written"] for m in overall_metrics)
    total_ms = sum(m["duration_ms"] for m in overall_metrics)
    print(f"\n  TOTAL: {total_rows} filas escritas, {total_ms}ms")

    # Conteos finales en gold.db
    print("\n[build_gold] conteos finales en gold.db:")
    counts = gold.get_table_counts(gold_engine)
    for name, n in counts.items():
        print(f"  {name:25} {n:>8}")

    gold_engine.dispose()
    if silver_engine is not None:
        silver_engine.dispose()
    if raw_engine is not None:
        raw_engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())