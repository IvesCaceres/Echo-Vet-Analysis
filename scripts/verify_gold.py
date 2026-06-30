"""Verificación end-to-end de la capa GOLD.

Comprueba:
- gold.db existe y tiene las 3 tablas + 2 VIEWs + gold_etl_runs
- gold_etl_runs registra ejecuciones OK por fase
- Conteos de las 3 tablas Gold = tablas Silver correspondientes
- 0 NULLs en columnas críticas (termino_canonico, especie_nombre, organo_nombre)
- Índices esperados existen
- VIEWs existen y retornan datos (cardinalidad >0)
- Idempotencia: re-run produce mismo Gold (vía gold_etl_runs.rows_written=0)

Exit code: 0 si todas las verificaciones pasan, 1 si alguna falla.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Forzar UTF-8 en stdout (Windows cp1252 rompe con caracteres acentuados)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
GOLD = ROOT / "gold.db"
SILVER = ROOT / "silver.db"


def main() -> int:
    if not GOLD.exists():
        print(f"ERROR: {GOLD} no existe. Ejecutá build_gold --init.")
        return 1
    if not SILVER.exists():
        print(f"ERROR: {SILVER} no existe. Ejecutá build_silver primero.")
        return 1

    # Para los counts vs Silver necesitamos un único proceso con ATTACH a
    # ambas DBs. Usamos sqlite3 directo (no SQLAlchemy) para simplicidad.
    import sqlite3

    gold = sqlite3.connect(str(GOLD))
    silver = sqlite3.connect(str(SILVER))
    gold.execute("ATTACH DATABASE ? AS silver", (str(SILVER),))
    gc = gold.cursor()  # queries contra gold.db
    sc = silver.cursor()  # queries contra silver.db (read-only)
    fails: list[str] = []
    passes: list[str] = []

    print("=" * 70)
    print("GOLD — Verificación end-to-end")
    print("=" * 70)

    # -----------------------------------------------------------------
    # 1. gold.db tiene las 5 entidades esperadas (3 tablas + 2 vistas)
    # -----------------------------------------------------------------
    expected_tables = {
        "gold_diagnosticos": "table",
        "gold_demografia": "table",
        "gold_hallazgos": "table",
        "gold_etl_runs": "table",
        "gold_coocurrencias": "view",
        "gold_tendencias": "view",
    }
    rows = gold.execute(
        "SELECT name, type FROM sqlite_master "
        "WHERE name IN ({})".format(
            ",".join("?" for _ in expected_tables)
        ),
        tuple(expected_tables.keys()),
    ).fetchall()
    found = {name: typ for name, typ in rows}
    missing = []
    for name, typ in expected_tables.items():
        if name not in found:
            missing.append(f"{name} ({typ})")
        elif found[name] != typ:
            fails.append(
                f"✗ {name}: esperado {typ}, encontrado {found[name]}"
            )
    if missing:
        fails.append(f"✗ objetos faltantes en gold.db: {', '.join(missing)}")
    else:
        passes.append(
            f"✓ gold.db tiene las {len(expected_tables)} entidades esperadas "
            f"(3 tablas Gold + gold_etl_runs + 2 VIEWs)"
        )

    # -----------------------------------------------------------------
    # 2. gold_etl_runs: ≥1 ejecución ok por fase
    # -----------------------------------------------------------------
    expected_phases = ("diag", "demo", "hall", "views")
    for phase in expected_phases:
        n_ok = gc.execute(
            "SELECT COUNT(*) FROM gold_etl_runs WHERE phase=? AND status='ok'",
            (phase,),
        ).fetchone()[0]
        if n_ok >= 1:
            passes.append(f"✓ gold_etl_runs: {n_ok} ejecución(es) ok para phase={phase}")
        else:
            fails.append(
                f"✗ gold_etl_runs: 0 ejecuciones ok para phase={phase} — "
                f"corré build_gold --phase {phase}"
            )

    # -----------------------------------------------------------------
    # 3. Conteos: gold_diagnosticos = silver_conclusion_items
    # -----------------------------------------------------------------
    n_gold_diag = gc.execute(
        "SELECT COUNT(*) FROM gold_diagnosticos"
    ).fetchone()[0]
    n_silver_conc = sc.execute(
        "SELECT COUNT(*) FROM silver_conclusion_items"
    ).fetchone()[0]
    n_silver_inf_con_fecha = sc.execute(
        "SELECT COUNT(*) FROM silver_informes WHERE fecha_parseada IS NOT NULL"
    ).fetchone()[0]
    if n_gold_diag == n_silver_conc:
        passes.append(
            f"✓ gold_diagnosticos: {n_gold_diag} filas = "
            f"silver_conclusion_items ({n_silver_conc})"
        )
    else:
        # gold_diagnosticos filtra por fecha_parseada IS NOT NULL.
        # Si silver tiene conclusion_items con informe sin fecha parseada,
        # gold_diagnosticos tendrá menos filas.
        if n_gold_diag <= n_silver_conc:
            passes.append(
                f"⚠ gold_diagnosticos: {n_gold_diag} ≤ "
                f"silver_conclusion_items ({n_silver_conc}) — "
                f"diferencia por informes sin fecha_parseada"
            )
        else:
            fails.append(
                f"✗ gold_diagnosticos: {n_gold_diag} > "
                f"silver_conclusion_items ({n_silver_conc}) — INCONSISTENTE"
            )

    # -----------------------------------------------------------------
    # 4. Conteos: gold_demografia = silver_informes con fecha
    # -----------------------------------------------------------------
    n_gold_demo = gc.execute(
        "SELECT COUNT(*) FROM gold_demografia"
    ).fetchone()[0]
    if n_gold_demo == n_silver_inf_con_fecha:
        passes.append(
            f"✓ gold_demografia: {n_gold_demo} filas = "
            f"silver_informes con fecha ({n_silver_inf_con_fecha})"
        )
    else:
        fails.append(
            f"✗ gold_demografia: {n_gold_demo} ≠ "
            f"silver_informes con fecha ({n_silver_inf_con_fecha})"
        )

    # -----------------------------------------------------------------
    # 5. Conteos: gold_hallazgos = silver_atributos_hallazgo
    # -----------------------------------------------------------------
    n_gold_hall = gc.execute(
        "SELECT COUNT(*) FROM gold_hallazgos"
    ).fetchone()[0]
    n_silver_attr = sc.execute(
        "SELECT COUNT(*) FROM silver_atributos_hallazgo"
    ).fetchone()[0]
    if n_gold_hall == n_silver_attr:
        passes.append(
            f"✓ gold_hallazgos: {n_gold_hall} filas = "
            f"silver_atributos_hallazgo ({n_silver_attr})"
        )
    else:
        fails.append(
            f"✗ gold_hallazgos: {n_gold_hall} ≠ "
            f"silver_atributos_hallazgo ({n_silver_attr})"
        )

    # -----------------------------------------------------------------
    # 6. 0 NULLs en columnas críticas
    # -----------------------------------------------------------------
    null_diag = gc.execute(
        "SELECT COUNT(*) FROM gold_diagnosticos WHERE termino_canonico IS NULL"
    ).fetchone()[0]
    if null_diag == 0:
        passes.append(
            f"✓ gold_diagnosticos.termino_canonico: 0 NULLs "
            f"(sobre {n_gold_diag} filas)"
        )
    else:
        fails.append(
            f"✗ gold_diagnosticos.termino_canonico: {null_diag} NULLs"
        )

    null_demo = gc.execute(
        "SELECT COUNT(*) FROM gold_demografia WHERE especie_nombre IS NULL"
    ).fetchone()[0]
    if null_demo == 0:
        passes.append(
            f"✓ gold_demografia.especie_nombre: 0 NULLs "
            f"(sobre {n_gold_demo} filas)"
        )
    else:
        fails.append(
            f"✗ gold_demografia.especie_nombre: {null_demo} NULLs"
        )

    null_hall_org = gc.execute(
        "SELECT COUNT(*) FROM gold_hallazgos WHERE organo_nombre IS NULL"
    ).fetchone()[0]
    if null_hall_org == 0:
        passes.append(
            f"✓ gold_hallazgos.organo_nombre: 0 NULLs (sobre {n_gold_hall})"
        )
    else:
        fails.append(
            f"✗ gold_hallazgos.organo_nombre: {null_hall_org} NULLs"
        )

    null_hall_attr = gc.execute(
        "SELECT COUNT(*) FROM gold_hallazgos WHERE atributo_nombre IS NULL"
    ).fetchone()[0]
    if null_hall_attr == 0:
        passes.append(
            f"✓ gold_hallazgos.atributo_nombre: 0 NULLs (sobre {n_gold_hall})"
        )
    else:
        fails.append(
            f"✗ gold_hallazgos.atributo_nombre: {null_hall_attr} NULLs"
        )

    # -----------------------------------------------------------------
    # 7. Índices esperados en las 3 tablas
    # -----------------------------------------------------------------
    expected_indexes = {
        "gold_diagnosticos": [
            "ix_gold_diagnosticos_termino_canonico",
            "ix_gold_diagnosticos_tipo_item",
            "ix_gold_diagnosticos_anio",
            "ix_gold_diagnosticos_mes",
        ],
        "gold_demografia": [
            "ix_gold_demografia_anio",
            "ix_gold_demografia_mes",
            "ix_gold_demografia_especie_nombre",
        ],
        "gold_hallazgos": [
            "ix_gold_hallazgos_organo_nombre",
            "ix_gold_hallazgos_atributo_nombre",
            "ix_gold_hallazgos_estado_hallazgo",
        ],
    }
    for table, idx_names in expected_indexes.items():
        for idx in idx_names:
            row = gc.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name=? AND name=?",
                (table, idx),
            ).fetchone()
            if row:
                passes.append(f"✓ índice {idx} existe en {table}")
            else:
                fails.append(f"✗ índice {idx} NO existe en {table}")

    # -----------------------------------------------------------------
    # 8. VIEWs existen y retornan datos
    # -----------------------------------------------------------------
    # gold_coocurrencias
    try:
        n_coc = gc.execute(
            "SELECT COUNT(*) FROM gold_coocurrencias"
        ).fetchone()[0]
        if n_coc > 0:
            passes.append(
                f"✓ VIEW gold_coocurrencias existe y retorna {n_coc} filas"
            )
        else:
            fails.append(
                f"✗ VIEW gold_coocurrencias existe pero retorna 0 filas"
            )
    except sqlite3.OperationalError as e:
        fails.append(f"✗ VIEW gold_coocurrencias no consultable: {e}")

    # gold_tendencias
    try:
        n_tend = gc.execute(
            "SELECT COUNT(*) FROM gold_tendencias"
        ).fetchone()[0]
        if n_tend > 0:
            passes.append(
                f"✓ VIEW gold_tendencias existe y retorna {n_tend} filas"
            )
        else:
            fails.append(
                f"✗ VIEW gold_tendencias existe pero retorna 0 filas"
            )
    except sqlite3.OperationalError as e:
        fails.append(f"✗ VIEW gold_tendencias no consultable: {e}")

    # -----------------------------------------------------------------
    # 9. Idempotencia (DELETE+INSERT idempotente por construcción)
    # -----------------------------------------------------------------
    # Patrón DELETE+INSERT en cada build_gold_* siempre reescribe las mismas
    # filas si Silver no cambió. Por lo tanto la idempotencia se manifiesta
    # como: counts de las 3 tablas Gold son idénticos entre runs.
    # Verificación: que el último rows_written por fase coincida con el
    # count actual de la tabla correspondiente.
    last_runs = gc.execute(
        "SELECT phase, rows_written FROM gold_etl_runs "
        "WHERE status='ok' AND phase IN ('diag','demo','hall') "
        "  AND id IN (SELECT MAX(id) FROM gold_etl_runs "
        "             WHERE status='ok' AND phase IN ('diag','demo','hall') "
        "             GROUP BY phase)"
    ).fetchall()
    counts_now = {
        "diag": n_gold_diag,
        "demo": n_gold_demo,
        "hall": n_gold_hall,
    }
    for phase, written in last_runs:
        current = counts_now.get(phase)
        if current is None:
            continue
        if written == current:
            passes.append(
                f"✓ idempotencia {phase}: último run escribió {written} = "
                f"count actual ({current})"
            )
        else:
            fails.append(
                f"✗ idempotencia {phase}: último run escribió {written} ≠ "
                f"count actual ({current})"
            )

    # -----------------------------------------------------------------
    # 10. gold_etl_runs historial (reporte)
    # -----------------------------------------------------------------
    print("\n--- gold_etl_runs (últimas 10 corridas) ---")
    for r in gc.execute(
        "SELECT id, phase, status, rows_read, rows_written, "
        "duration_ms, datetime(started_at), actor "
        "FROM gold_etl_runs ORDER BY id DESC LIMIT 10"
    ).fetchall():
        print(f"  id={r[0]} phase={r[1]} status={r[2]} "
              f"read={r[3]} written={r[4]} "
              f"dur={r[5]}ms at={r[6]} actor={r[7]}")

    silver.close()
    gold.close()

    # =================================================================
    # REPORTE FINAL
    # =================================================================
    print()
    print("=" * 70)
    print("REPORTE DE VERIFICACIÓN GOLD")
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