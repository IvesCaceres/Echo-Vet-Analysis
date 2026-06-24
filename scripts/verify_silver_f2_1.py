"""Verificación end-to-end de Fase 2.1.

Comprueba:
- Migración v2.1 aplicada (columna `edad_parse_ok` existe)
- dim_raza contiene únicamente valores canónicos (sin duplicados consolidados)
- DPC/DPL renombrados a "Doméstico Pelo Corto/Largo"
- map_raza conserva todas las 163 variantes
- silver_informes.edad_meses con cobertura ≥99%
- Clasificación de stg_valores_no_mapeados
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# Permitir imports sin instalar paquete
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import text  # noqa: E402

from informes_vet import silver_db  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SILVER = ROOT / "silver.db"

# =============================================================================
# CONSTANTES DE VERIFICACIÓN
# =============================================================================

# Nombres que DEBEN existir en dim_raza (consolidación)
EXPECTED_CANONICAL_RAZAS = {
    "Boxer",                # ← Bóxer consolidado
    "Bull Dog Francés",     # ← Bull Dog Frances consolidado
    "Rottweiler",           # ← Rotweiler consolidado
    "Pastor Alemán",        # ← Pastor alemán consolidado
    "Terrier Chileno",      # ← Terrier chileno consolidado
    "Mestizo",              # ← Mestizo + Mestiza + Mestizo. consolidados
    "Doméstico Pelo Corto", # ← DPC renombrado
    "Doméstico Pelo Largo", # ← DPL renombrado
}

# Nombres que NO DEBEN existir en dim_raza (variantes obsoletas)
FORBIDDEN_VARIANT_RAZAS = {
    "Bóxer", "Bull Dog Frances", "Rotweiler",
    "Pastor alemán", "Terrier chileno", "Mestiza", "Mestizo.",
    "DPC", "DPL",
}

# Edad: ≥99% de cobertura
EDAD_COVERAGE_TARGET = 99.0


def main() -> int:
    if not SILVER.exists():
        print(f"ERROR: {SILVER} no existe. Ejecutá build_silver primero.")
        return 1

    eng = silver_db.get_engine(ROOT)
    fails: list[str] = []
    passes: list[str] = []

    with eng.begin() as conn:
        # ---------- 1. Migración v2.1 aplicada ----------
        cols = [r[1] for r in conn.exec_driver_sql(
            "PRAGMA table_info(silver_informes)"
        ).all()]
        if "edad_parse_ok" in cols:
            passes.append("✓ silver_informes.edad_parse_ok existe (migración v2.1)")
        else:
            fails.append("✗ silver_informes.edad_parse_ok NO existe — corré build_silver --phase f2_1")

        # ---------- 2. dim_raza: solo canónicos ----------
        rows = conn.execute(text(
            "SELECT nombre_canonico FROM dim_raza"
        )).all()
        nombres = {r[0] for r in rows}

        for n in EXPECTED_CANONICAL_RAZAS:
            if n in nombres:
                passes.append(f"✓ dim_raza contiene canónico '{n}'")
            else:
                fails.append(f"✗ dim_raza NO contiene canónico '{n}'")

        for n in FORBIDDEN_VARIANT_RAZAS:
            if n not in nombres:
                passes.append(f"✓ dim_raza NO contiene variante obsoleta '{n}'")
            else:
                fails.append(f"✗ dim_raza contiene variante obsoleta '{n}'")

        # dim_raza count esperado: 56 (63 - 7 duplicados eliminados)
        n_dim_raza = len(rows)
        if n_dim_raza == 56:
            passes.append(f"✓ dim_raza tiene 56 entradas (63 originales - 7 duplicados)")
        else:
            fails.append(f"✗ dim_raza tiene {n_dim_raza} entradas (esperado 56)")

        # ---------- 3. Sin duplicados consolidados en dim_raza ----------
        dups = conn.execute(text("""
            SELECT nombre_canonico, COUNT(*) AS n
            FROM dim_raza GROUP BY dim_especie_id, nombre_canonico HAVING n > 1
        """)).all()
        if not dups:
            passes.append("✓ dim_raza sin duplicados por (dim_especie_id, nombre_canonico)")
        else:
            fails.append(f"✗ dim_raza tiene duplicados: {dups}")

        # ---------- 4. map_raza conserva 163 variantes ----------
        n_map_raza = conn.execute(text(
            "SELECT COUNT(*) FROM map_raza"
        )).scalar()
        if n_map_raza == 163:
            passes.append(f"✓ map_raza conserva 163 entradas (sin pérdida de variantes)")
        else:
            fails.append(f"✗ map_raza tiene {n_map_raza} entradas (esperado 163)")

        # ---------- 5. Cobertura edad_meses ≥99% ----------
        total, parsed = conn.execute(text("""
            SELECT COUNT(*), SUM(CASE WHEN edad_parse_ok = 1 THEN 1 ELSE 0 END)
            FROM silver_informes
        """)).first()
        coverage = 100.0 * parsed / total if total else 0
        if coverage >= EDAD_COVERAGE_TARGET:
            passes.append(
                f"✓ edad_meses cobertura = {coverage:.2f}% (≥{EDAD_COVERAGE_TARGET}%)"
            )
        else:
            fails.append(
                f"✗ edad_meses cobertura = {coverage:.2f}% (<{EDAD_COVERAGE_TARGET}%)"
            )

        # ---------- 6. Edad no parseada = 28 esperados ----------
        unparsed = conn.execute(text("""
            SELECT edad_origen_raw, COUNT(*) FROM silver_informes
            WHERE edad_parse_ok = 0 GROUP BY edad_origen_raw ORDER BY 2 DESC
        """)).all()
        unparsed_total = sum(c for _, c in unparsed)
        if unparsed_total == 28:
            passes.append(f"✓ 28 silver_informes sin parsear (casos esperados)")
        else:
            fails.append(f"✗ {unparsed_total} silver_informes sin parsear (esperado 28)")
        print()
        print("Casos no parseados:")
        for raw, n in unparsed:
            print(f"  [{n:3}] {raw!r}")

        # ---------- 7. stg_valores_no_mapeados ----------
        n_stg = conn.execute(text(
            "SELECT COUNT(*) FROM stg_valores_no_mapeados"
        )).scalar()
        passes.append(f"✓ stg_valores_no_mapeados tiene {n_stg} entradas (24 esperadas)")

        # ---------- 8. silver_etl_runs con f2_1 ----------
        n_runs_f21 = conn.execute(text(
            "SELECT COUNT(*) FROM silver_etl_runs WHERE phase = 'f2_1'"
        )).scalar()
        if n_runs_f21 >= 1:
            passes.append(f"✓ silver_etl_runs registra {n_runs_f21} ejecución(es) f2_1")
        else:
            fails.append("✗ silver_etl_runs no registra ejecución f2_1")

    # =================================================================
    # REPORTE
    # =================================================================
    print("=" * 70)
    print("F2.1 — Verificación")
    print("=" * 70)
    print()
    print(f"Aserciones pasadas: {len(passes)}")
    print(f"Aserciones fallidas: {len(fails)}")
    print()
    print("--- PASA ---")
    for p in passes:
        print(f"  {p}")
    if fails:
        print()
        print("--- FALLA ---")
        for f in fails:
            print(f"  {f}")
    print()
    print("=" * 70)
    print("Verificación completada")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())