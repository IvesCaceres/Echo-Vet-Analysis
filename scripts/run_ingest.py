"""CLI driver para ingesta de informes ecográficos a SQLite o PostgreSQL."""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
import time
import traceback
from pathlib import Path

# Permitir `python scripts/run_ingest.py` sin instalar el paquete
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from informes_vet import db, docx_io, extract  # noqa: E402


def _log_error(log_path: Path, archivo: str, ruta: str, exc: BaseException) -> None:
    """Escribe una línea en el log plano de errores."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(
            f"{ts}\tERROR\t{archivo}\t{type(exc).__name__}: {exc}\n"
        )


def _parse_year_filter(values: list[str]) -> list[int]:
    out: list[int] = []
    for v in values:
        for piece in v.split(","):
            piece = piece.strip()
            if piece:
                out.append(int(piece))
    return sorted(set(out))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ingesta de informes .docx -> SQLite|PostgreSQL")
    p.add_argument("--db", choices=("sqlite", "postgres"), default="sqlite")
    p.add_argument("--reset", action="store_true", help="DROP y recrea el esquema (WIPE)")
    p.add_argument("--dry-run", action="store_true", help="No escribe en BD; solo parsea")
    p.add_argument("--year-filter", action="append", default=[], help="Filtrar por año (repetible)")
    p.add_argument("--limit", type=int, default=0, help="Procesar solo los primeros N archivos")
    p.add_argument("--root", type=Path, default=Path.cwd(), help="Raíz del proyecto")
    p.add_argument("--log-errores", type=Path, default=Path("errores_ingest.log"))
    args = p.parse_args(argv)

    root: Path = args.root.resolve()
    year_filter = _parse_year_filter(args.year_filter)

    files = docx_io.iter_docx(root, year_filter=year_filter or None)
    if args.limit and args.limit > 0:
        files = files[: args.limit]

    print(f"[ingest] root={root}")
    print(f"[ingest] db={args.db}  reset={args.reset}  dry_run={args.dry_run}")
    print(f"[ingest] year_filter={year_filter or 'ALL'}  limit={args.limit or 'NONE'}")
    print(f"[ingest] archivos a procesar: {len(files)}")

    engine = None
    if not args.dry_run:
        engine = db.get_engine(args.db, root)
        if args.reset:
            print(f"[ingest] --reset: borrando y recreando esquema en {args.db}...")
            db.reset_schema(engine)
        else:
            db.create_schema(engine)

    counts = {"inserted": 0, "skipped": 0, "errors": 0, "hallazgos": 0, "conclusiones": 0}
    t0 = time.monotonic()

    for i, path in enumerate(files, start=1):
        try:
            record = extract.parse_docx(path)
        except extract.ExtractionError as e:
            counts["errors"] += 1
            _log_error(args.log_errores, path.name, str(path), e)
            if engine is not None:
                db.log_error(engine, path.name, str(path), e)
            print(f"[{i}/{len(files)}] ERROR {path.name}: {e}")
            continue
        except Exception as e:  # noqa: BLE001
            counts["errors"] += 1
            tb = traceback.format_exc()
            _log_error(args.log_errores, path.name, str(path), e)
            if engine is not None:
                try:
                    with engine.begin() as conn:
                        conn.execute(
                            db.errores_ingesta.insert().values(
                                archivo=path.name,
                                ruta=str(path),
                                error=f"{type(e).__name__}: {e}",
                                traceback=tb,
                            )
                        )
                except Exception:
                    pass
            print(f"[{i}/{len(files)}] CRASH {path.name}: {e}")
            continue

        if args.dry_run:
            counts["inserted"] += 1
            counts["hallazgos"] += len(record["hallazgos"])
            if record.get("conclusiones_texto"):
                counts["conclusiones"] += 1
            if i % 200 == 0 or i == len(files):
                print(
                    f"[{i}/{len(files)}] dry-run ok: {path.name} "
                    f"(hallazgos={len(record['hallazgos'])}, concl={'s' if record.get('conclusiones_texto') else 'n'})"
                )
            continue

        try:
            with engine.begin() as conn:
                informe_id = db.upsert_informe(conn, record)
            if informe_id is None:
                counts["skipped"] += 1
                if i % 200 == 0 or i == len(files):
                    print(f"[{i}/{len(files)}] skip (dup): {path.name}")
                continue

            with engine.begin() as conn:
                counts["hallazgos"] += db.insert_hallazgos(conn, informe_id, record["hallazgos"])
                counts["conclusiones"] += db.insert_conclusion(
                    conn, informe_id, record.get("conclusiones_texto") or ""
                )
            counts["inserted"] += 1
            if i % 200 == 0 or i == len(files):
                print(
                    f"[{i}/{len(files)}] ok: {path.name} "
                    f"(hallazgos={len(record['hallazgos'])})"
                )
        except Exception as e:  # noqa: BLE001
            counts["errors"] += 1
            tb = traceback.format_exc()
            _log_error(args.log_errores, path.name, str(path), e)
            try:
                with engine.begin() as conn:
                    conn.execute(
                        db.errores_ingesta.insert().values(
                            archivo=path.name,
                            ruta=str(path),
                            error=f"{type(e).__name__}: {e}",
                            traceback=tb,
                        )
                    )
            except Exception:
                pass
            print(f"[{i}/{len(files)}] DB-ERROR {path.name}: {e}")

    elapsed = time.monotonic() - t0
    print("-" * 60)
    print(f"[ingest] OK en {elapsed:.1f}s")
    print(f"[ingest] insertados : {counts['inserted']}")
    print(f"[ingest] skipped    : {counts['skipped']}")
    print(f"[ingest] errores    : {counts['errors']}")
    print(f"[ingest] hallazgos  : {counts['hallazgos']}")
    print(f"[ingest] conclusio. : {counts['conclusiones']}")
    if engine is not None:
        engine.dispose()
    return 0 if counts["errors"] == 0 else 0  # no abortamos por errores


if __name__ == "__main__":
    raise SystemExit(main())
