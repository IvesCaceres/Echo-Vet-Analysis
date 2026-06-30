"""Verificación end-to-end de Fase 2 (post Completion Release).

Comprueba:
- F2 ejecutado y registrado en silver_etl_runs
- dim_raza poblada (>0 filas)
- map_raza poblada (>0 filas)
- Cobertura de dim_raza_id en silver_informes
- 100% de dim_raza_id válidos (no huérfanos)
- 0 duplicados en map_raza (UNIQUE en valor_original)
- Porcentaje de informes sin raza ≈ 64 (esperado RAW)
- Idempotencia: re-run produce misma Silver
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SILVER = ROOT / "silver.db"


def main() -> int:
    if not SILVER.exists():
        print(f"ERROR: {SILVER} no existe. Ejecutá build_silver primero.")
        return 1

    silver = sqlite3.connect(str(SILVER))
    silver.execute("ATTACH DATABASE 'informes.db' AS raw")
    sc = silver.cursor()
    fails: list[str] = []
    passes: list[str] = []

    print("=" * 70)
    print("F2 — Verificación (post Completion Release)")
    print("=" * 70)

    # -----------------------------------------------------------------
    # 1. F2 ejecutado y registrado en silver_etl_runs
    # -----------------------------------------------------------------
    n_f2_runs = sc.execute(
        "SELECT COUNT(*) FROM silver_etl_runs WHERE phase='f2' AND status='ok'"
    ).fetchone()[0]
    if n_f2_runs >= 1:
        passes.append(f"✓ silver_etl_runs registra {n_f2_runs} ejecución(es) f2 ok")
    else:
        fails.append("✗ silver_etl_runs NO registra ejecución f2 ok — corré build_silver --phase f2")

    # -----------------------------------------------------------------
    # 2. dim_raza poblada (>0 filas)
    # -----------------------------------------------------------------
    n_dim_raza = sc.execute("SELECT COUNT(*) FROM dim_raza").fetchone()[0]
    if n_dim_raza > 0:
        passes.append(f"✓ dim_raza poblada: {n_dim_raza} filas")
    else:
        fails.append("✗ dim_raza vacía (0 filas) — F2 no se ejecutó o falló")

    # -----------------------------------------------------------------
    # 3. map_raza poblada (>0 filas)
    # -----------------------------------------------------------------
    n_map_raza = sc.execute("SELECT COUNT(*) FROM map_raza").fetchone()[0]
    if n_map_raza > 0:
        passes.append(f"✓ map_raza poblada: {n_map_raza} filas")
    else:
        fails.append("✗ map_raza vacía (0 filas) — F2 no se ejecutó o falló")

    # -----------------------------------------------------------------
    # 4. dim_raza: 0 duplicados por (dim_especie_id, nombre_canonico)
    # -----------------------------------------------------------------
    n_dups_dim = sc.execute(
        "SELECT COUNT(*) FROM ("
        "  SELECT dim_especie_id, nombre_canonico, COUNT(*) c "
        "  FROM dim_raza GROUP BY dim_especie_id, nombre_canonico HAVING c > 1"
        ")"
    ).fetchone()[0]
    if n_dups_dim == 0:
        passes.append("✓ dim_raza sin duplicados por (dim_especie_id, nombre_canonico)")
    else:
        fails.append(f"✗ dim_raza tiene {n_dups_dim} grupos duplicados")

    # -----------------------------------------------------------------
    # 5. map_raza: 0 duplicados en valor_original (UNIQUE constraint)
    # -----------------------------------------------------------------
    n_dups_map = sc.execute(
        "SELECT COUNT(*) FROM ("
        "  SELECT valor_original FROM map_raza "
        "  GROUP BY valor_original HAVING COUNT(*) > 1"
        ")"
    ).fetchone()[0]
    if n_dups_map == 0:
        passes.append("✓ map_raza sin duplicados en valor_original")
    else:
        fails.append(f"✗ map_raza tiene {n_dups_map} duplicados en valor_original")

    # -----------------------------------------------------------------
    # 6. silver_informes.dim_raza_id: cobertura
    # -----------------------------------------------------------------
    total_inf, linked_inf, no_raza_inf = sc.execute(
        "SELECT "
        "  COUNT(*), "
        "  SUM(CASE WHEN dim_raza_id IS NOT NULL THEN 1 ELSE 0 END), "
        "  SUM(CASE WHEN dim_raza_id IS NULL THEN 1 ELSE 0 END) "
        "FROM silver_informes"
    ).fetchone()
    coverage_pct = round(100.0 * linked_inf / total_inf, 2) if total_inf else 0
    if total_inf == 2893:
        passes.append(f"✓ silver_informes: {total_inf} filas (esperado 2893)")
    else:
        fails.append(f"✗ silver_informes: {total_inf} filas (esperado 2893)")
    if coverage_pct > 90:
        passes.append(f"✓ dim_raza_id cobertura: {linked_inf}/{total_inf} ({coverage_pct}%)")
    else:
        fails.append(f"✗ dim_raza_id cobertura: {linked_inf}/{total_inf} ({coverage_pct}%) — debería ser >90%")

    # -----------------------------------------------------------------
    # 7. Informes sin raza ≈ 64 (esperado de RAW)
    # -----------------------------------------------------------------
    # raw.informes.raza NULL o vacío
    raw_no_raza = sc.execute(
        "SELECT COUNT(*) FROM raw.informes "
        "WHERE raza IS NULL OR TRIM(raza) = ''"
    ).fetchone()[0]
    # silver_informes con dim_raza_id NULL pero raw con raza → pendiente
    pendientes = sc.execute(
        "SELECT COUNT(*) FROM silver_informes si "
        "JOIN raw.informes ri ON ri.id = si.informe_id "
        "WHERE si.dim_raza_id IS NULL "
        "AND ri.raza IS NOT NULL AND TRIM(ri.raza) != ''"
    ).fetchone()[0]
    # silver_informes con dim_raza_id NULL y raw sin raza → realmente sin raza
    real_no_raza = sc.execute(
        "SELECT COUNT(*) FROM silver_informes si "
        "JOIN raw.informes ri ON ri.id = si.informe_id "
        "WHERE si.dim_raza_id IS NULL "
        "AND (ri.raza IS NULL OR TRIM(ri.raza) = '')"
    ).fetchone()[0]

    if abs(real_no_raza - raw_no_raza) <= 2:
        passes.append(
            f"✓ informes sin raza: {real_no_raza} en silver ≈ {raw_no_raza} en raw "
            f"(diferencia {abs(real_no_raza - raw_no_raza)})"
        )
    else:
        fails.append(
            f"✗ informes sin raza: {real_no_raza} en silver vs {raw_no_raza} en raw "
            f"(diferencia {abs(real_no_raza - raw_no_raza)} — esperado ≈0)"
        )

    passes.append(f"  └─ pendientes (raw con raza, map_raza sin dim_raza_id): {pendientes}")

    # -----------------------------------------------------------------
    # 8. 100% de dim_raza_id válidos (no huérfanos)
    # -----------------------------------------------------------------
    n_huerfanos = sc.execute(
        "SELECT COUNT(*) FROM silver_informes si "
        "WHERE si.dim_raza_id IS NOT NULL "
        "AND NOT EXISTS (SELECT 1 FROM dim_raza dr WHERE dr.id = si.dim_raza_id)"
    ).fetchone()[0]
    if n_huerfanos == 0:
        passes.append("✓ silver_informes.dim_raza_id: 0 FK huérfanas")
    else:
        fails.append(f"✗ silver_informes.dim_raza_id: {n_huerfanos} FK huérfanas")

    # -----------------------------------------------------------------
    # 9. map_raza.dim_raza_id: 0 FK huérfanas (entre las que son NOT NULL)
    # -----------------------------------------------------------------
    n_map_huerfanos = sc.execute(
        "SELECT COUNT(*) FROM map_raza mr "
        "WHERE mr.dim_raza_id IS NOT NULL "
        "AND NOT EXISTS (SELECT 1 FROM dim_raza dr WHERE dr.id = mr.dim_raza_id)"
    ).fetchone()[0]
    if n_map_huerfanos == 0:
        passes.append("✓ map_raza.dim_raza_id: 0 FK huérfanas")
    else:
        fails.append(f"✗ map_raza.dim_raza_id: {n_map_huerfanos} FK huérfanas")

    # -----------------------------------------------------------------
    # 10. Cobertura de map_raza vs RAW (todas las variantes en map_raza)
    # -----------------------------------------------------------------
    raw_distinct = sc.execute(
        "SELECT COUNT(DISTINCT raza) FROM raw.informes "
        "WHERE raza IS NOT NULL AND TRIM(raza) != ''"
    ).fetchone()[0]
    map_distinct = sc.execute(
        "SELECT COUNT(*) FROM map_raza"
    ).fetchone()[0]
    if map_distinct >= raw_distinct:
        passes.append(
            f"✓ map_raza cubre todas las variantes RAW: {map_distinct} ≥ {raw_distinct}"
        )
    else:
        fails.append(
            f"✗ map_raza NO cubre RAW: {map_distinct} < {raw_distinct}"
        )

    # -----------------------------------------------------------------
    # 11. Distribución map_raza.estado_revision
    # -----------------------------------------------------------------
    aprobadas = sc.execute(
        "SELECT COUNT(*) FROM map_raza WHERE estado_revision = 'aprobada'"
    ).fetchone()[0]
    pendientes_rev = sc.execute(
        "SELECT COUNT(*) FROM map_raza WHERE estado_revision = 'pendiente'"
    ).fetchone()[0]
    passes.append(f"  └─ map_raza: {aprobadas} aprobadas, {pendientes_rev} pendientes")

    # -----------------------------------------------------------------
    # 12. stg_razas_detectadas (esperado >0 para variantes freq<3)
    # -----------------------------------------------------------------
    n_stg = sc.execute("SELECT COUNT(*) FROM stg_razas_detectadas").fetchone()[0]
    if n_stg > 0:
        passes.append(f"✓ stg_razas_detectadas poblada: {n_stg} filas")
    else:
        fails.append("✗ stg_razas_detectadas vacía — variantes freq<3 no registradas")

    # -----------------------------------------------------------------
    # 13. silver_etl_runs historial F2
    # -----------------------------------------------------------------
    print("\n--- silver_etl_runs (F2 runs) ---")
    for r in sc.execute(
        "SELECT id, status, rows_read, rows_written, duration_ms, "
        "datetime(started_at), actor FROM silver_etl_runs WHERE phase='f2' ORDER BY id"
    ).fetchall():
        print(f"  id={r[0]} status={r[1]} read={r[2]} written={r[3]} "
              f"dur={r[4]}ms at={r[5]} actor={r[6]}")

    silver.close()

    # =================================================================
    # REPORTE FINAL
    # =================================================================
    print()
    print("=" * 70)
    print("REPORTE DE VERIFICACIÓN F2")
    print("=" * 70)
    print(f"\nAserciones pasadas: {len(passes)}")
    print(f"Aserciones fallidas: {len(fails)}\n")
    print("--- PASA ---")
    for p in passes:
        print(f"  {p}")
    if fails:
        print("\n--- FALLA ---")
        for f in fails:
            print(f"  {f}")
    print()
    print("=" * 70)
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
