"""Verificación post-F5 — Extracción de ítems de CONCLUSIONES (Opción C).

Criterios de validación (todos deben pasar para GO de F5):

  A. Esquema silver_conclusion_items (Opción C)
     A1. La tabla existe con las 13 columnas esperadas (incluidas las 3
         modificadoras y `negado`).
     A2. La tabla NO tiene columnas del esquema antiguo (termino_original,
         termino_canonico, tipo_item, modificador).
     A3. Existe UNIQUE INDEX
         (conclusion_id, termino_conclusion_id, pos_inicio, pos_fin).

  B. dim_termino_conclusion poblado
     B1. ≥80 filas en dim_termino_conclusion (catálogo semilla).
     B2. 3 valores distintos de tipo_item (DIAGNOSTICO, ETIOLOGIA, NEGATIVO).
     B3. (nombre_canonico) es único.
     B4. Todos los termino_conclusion_id en silver_conclusion_items
         resuelven a dim_termino_conclusion (0 huérfanos).

  C. Volumen y cobertura (CRITERIO GO)
     C1. silver_conclusion_items tiene entre 10,000 y 25,000 filas.
     C2. ≥85% de las raw.conclusiones tienen ≥1 ítem extraído.
     C3. items/conclusión (media) está entre 4 y 7.
     C4. 0 duplicados en la clave UNIQUE.

  D. Distribución por tipo_item (CRITERIO GO)
     D1. DIAGNOSTICO ≥ 40% del total.
     D2. ETIOLOGIA entre 5% y 40%.
     D3. NEGATIVO entre 1% y 30%.

  E. Cardinalidad de modificadores (CRITERIO GO)
     E1. modificador_cualidad ≤ 30 valores distintos.
     E2. modificador_distribucion ≤ 10 valores distintos.
     E3. lateralidad ≤ 8 valores distintos.

  F. No-match staging
     F1. stg_conclusion_no_match poblada para las conclusiones sin ítems.
     F2. Suma (silver_conclusion_items.conclusion_id) +
         stg_conclusion_no_match.conclusion_id ≥ raw.conclusiones.

Uso:

    python scripts/verify_silver_f5.py            # exit 0 si PASS, 1 si FAIL
    python scripts/verify_silver_f5.py --verbose  # muestra detalle

Exit codes:
  0  → PASS (todos los criterios GO cumplidos)
  1  → FAIL (al menos un criterio NO cumplido)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permitir `python scripts/verify_silver_f5.py` sin instalar el paquete
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import text
from sqlalchemy.engine import Engine

from informes_vet import db, silver_db


# ═══════════════════════════════════════════════════════════════════════════
# CHECKS
# ═══════════════════════════════════════════════════════════════════════════

class CheckResult:
    def __init__(self, code: str, label: str, passed: bool, detail: str = ""):
        self.code = code
        self.label = label
        self.passed = passed
        self.detail = detail

    def __repr__(self) -> str:
        status = "✅" if self.passed else "❌"
        return f"  {status} {self.code} {self.label}: {self.detail}"


# Columnas esperadas en silver_conclusion_items (Opción C)
EXPECTED_COLUMNS_SCI = {
    "id", "conclusion_id", "informe_id", "termino_conclusion_id",
    "lateralidad", "modificador_cualidad", "modificador_distribucion",
    "negado", "pos_inicio", "pos_fin", "termino_detectado",
    "confianza", "metodo_extraccion", "created_at",
}

# Columnas del esquema viejo que NO deben existir
FORBIDDEN_COLUMNS_SCI = {
    "termino_original", "termino_canonico", "tipo_item", "modificador",
    "silver_built_at",
}


def _get_columns(engine: Engine, table: str) -> set[str]:
    with engine.begin() as conn:
        if engine.dialect.name == "sqlite":
            rows = conn.exec_driver_sql(
                f"PRAGMA table_info({table})"
            ).fetchall()
            return {r[1] for r in rows}
        rows = conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = :t"
            ).params(t=table)
        ).fetchall()
    return {r[0] for r in rows}


def _index_exists(engine: Engine, index_name: str) -> bool:
    with engine.begin() as conn:
        if engine.dialect.name == "sqlite":
            rows = conn.exec_driver_sql(
                f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'"
            ).fetchall()
        else:
            rows = conn.execute(
                text(
                    "SELECT indexname FROM pg_indexes WHERE indexname = :n"
                ).params(n=index_name)
            ).fetchall()
    return bool(rows)


def check_a_esquema(engine: Engine) -> list[CheckResult]:
    results = []
    cols = _get_columns(engine, "silver_conclusion_items")
    missing = EXPECTED_COLUMNS_SCI - cols
    forbidden = FORBIDDEN_COLUMNS_SCI & cols
    idx_exists = _index_exists(engine, "uq_silver_conc_items_unique")

    results.append(CheckResult(
        "A1", "13 columnas Opción C presentes en silver_conclusion_items",
        len(missing) == 0,
        f"faltan {len(missing)}: {sorted(missing) if missing else 'ninguna'}",
    ))
    results.append(CheckResult(
        "A2", "0 columnas del esquema antiguo",
        len(forbidden) == 0,
        f"presentes (no deberían): {sorted(forbidden) if forbidden else 'ninguna'}",
    ))
    results.append(CheckResult(
        "A3", "UNIQUE INDEX uq_silver_conc_items_unique existe",
        idx_exists,
        "existe" if idx_exists else "FALTA",
    ))
    return results


def check_b_dim_termino(engine: Engine) -> list[CheckResult]:
    results = []
    with engine.begin() as conn:
        n_total = conn.execute(text(
            "SELECT COUNT(*) FROM dim_termino_conclusion"
        )).scalar()
        n_tipos = conn.execute(text(
            "SELECT COUNT(DISTINCT tipo_item) FROM dim_termino_conclusion"
        )).scalar()
        n_duplicates = conn.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT nombre_canonico, COUNT(*) AS n
                FROM dim_termino_conclusion
                GROUP BY nombre_canonico
                HAVING n > 1
            )
        """)).scalar()
        n_huerfanos = conn.execute(text("""
            SELECT COUNT(*)
            FROM silver_conclusion_items sci
            LEFT JOIN dim_termino_conclusion dtc
              ON dtc.id = sci.termino_conclusion_id
            WHERE dtc.id IS NULL
        """)).scalar()

    results.append(CheckResult(
        "B1", "≥80 filas en dim_termino_conclusion",
        n_total >= 80,
        f"{n_total} filas",
    ))
    results.append(CheckResult(
        "B2", "3 valores distintos de tipo_item",
        n_tipos == 3,
        f"{n_tipos} valores distintos",
    ))
    results.append(CheckResult(
        "B3", "nombre_canonico único",
        n_duplicates == 0,
        f"{n_duplicates} duplicados",
    ))
    results.append(CheckResult(
        "B4", "0 huérfanos silver_conclusion_items → dim_termino_conclusion",
        n_huerfanos == 0,
        f"{n_huerfanos} huérfanos",
    ))
    return results


def check_c_volumen_cobertura(
    engine: Engine, raw_engine: Engine
) -> list[CheckResult]:
    results = []
    with engine.begin() as conn:
        n_items = conn.execute(text(
            "SELECT COUNT(*) FROM silver_conclusion_items"
        )).scalar()
        n_concl_items = conn.execute(text(
            "SELECT COUNT(DISTINCT conclusion_id) "
            "FROM silver_conclusion_items"
        )).scalar()
        n_dups = conn.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT conclusion_id, termino_conclusion_id, pos_inicio, pos_fin, COUNT(*) AS n
                FROM silver_conclusion_items
                GROUP BY conclusion_id, termino_conclusion_id, pos_inicio, pos_fin
                HAVING n > 1
            )
        """)).scalar()
        avg = conn.execute(text(
            "SELECT ROUND(1.0 * COUNT(*) / NULLIF(COUNT(DISTINCT conclusion_id), 0), 2) "
            "FROM silver_conclusion_items"
        )).scalar()
        # avg puede ser None si no hay datos
        avg_val = float(avg) if avg is not None else 0.0
    with raw_engine.begin() as conn:
        n_concl_total = conn.execute(text(
            "SELECT COUNT(*) FROM conclusiones"
        )).scalar()

    pct = round(100.0 * n_concl_items / n_concl_total, 2) if n_concl_total else 0

    results.append(CheckResult(
        "C1", "10k ≤ items ≤ 25k",
        10000 <= n_items <= 25000,
        f"{n_items:,} items",
    ))
    results.append(CheckResult(
        "C2", "≥85% de conclusiones con ≥1 item",
        pct >= 85.0,
        f"{n_concl_items}/{n_concl_total} ({pct}%)",
    ))
    results.append(CheckResult(
        "C3", "items/conclusión entre 4 y 7",
        4.0 <= avg_val <= 7.0,
        f"{avg_val} items/conclusión",
    ))
    results.append(CheckResult(
        "C4", "0 duplicados en UNIQUE (conclusion_id, termino_conclusion_id, pos_inicio, pos_fin)",
        n_dups == 0,
        f"{n_dups} duplicados",
    ))
    return results


def check_d_distribucion_tipo(engine: Engine) -> list[CheckResult]:
    results = []
    with engine.begin() as conn:
        n_total = conn.execute(text(
            "SELECT COUNT(*) FROM silver_conclusion_items"
        )).scalar()
        rows = conn.execute(text(
            "SELECT dtc.tipo_item, COUNT(*) "
            "FROM silver_conclusion_items sci "
            "JOIN dim_termino_conclusion dtc ON dtc.id = sci.termino_conclusion_id "
            "GROUP BY dtc.tipo_item"
        )).fetchall()
    by_tipo = {r[0]: r[1] for r in rows}

    n_diag = by_tipo.get("DIAGNOSTICO", 0)
    n_etio = by_tipo.get("ETIOLOGIA", 0)
    n_neg = by_tipo.get("NEGATIVO", 0)
    pct_diag = round(100.0 * n_diag / n_total, 2) if n_total else 0
    pct_etio = round(100.0 * n_etio / n_total, 2) if n_total else 0
    pct_neg = round(100.0 * n_neg / n_total, 2) if n_total else 0

    results.append(CheckResult(
        "D1", "DIAGNOSTICO ≥ 40% del total",
        pct_diag >= 40.0,
        f"{n_diag} ({pct_diag}%)",
    ))
    results.append(CheckResult(
        "D2", "ETIOLOGIA entre 5% y 40%",
        5.0 <= pct_etio <= 40.0,
        f"{n_etio} ({pct_etio}%)",
    ))
    results.append(CheckResult(
        "D3", "NEGATIVO entre 1% y 30%",
        1.0 <= pct_neg <= 30.0,
        f"{n_neg} ({pct_neg}%)",
    ))
    return results


def check_e_modificadores(engine: Engine) -> list[CheckResult]:
    results = []
    with engine.begin() as conn:
        n_cual = conn.execute(text(
            "SELECT COUNT(DISTINCT modificador_cualidad) "
            "FROM silver_conclusion_items "
            "WHERE modificador_cualidad IS NOT NULL"
        )).scalar()
        n_dist = conn.execute(text(
            "SELECT COUNT(DISTINCT modificador_distribucion) "
            "FROM silver_conclusion_items "
            "WHERE modificador_distribucion IS NOT NULL"
        )).scalar()
        n_lat = conn.execute(text(
            "SELECT COUNT(DISTINCT lateralidad) "
            "FROM silver_conclusion_items "
            "WHERE lateralidad IS NOT NULL"
        )).scalar()

    results.append(CheckResult(
        "E1", "cardinalidad modificador_cualidad ≤ 30",
        n_cual <= 30,
        f"{n_cual} valores distintos",
    ))
    results.append(CheckResult(
        "E2", "cardinalidad modificador_distribucion ≤ 10",
        n_dist <= 10,
        f"{n_dist} valores distintos",
    ))
    results.append(CheckResult(
        "E3", "cardinalidad lateralidad ≤ 8",
        n_lat <= 8,
        f"{n_lat} valores distintos",
    ))
    return results


def check_f_no_match(
    engine: Engine, raw_engine: Engine
) -> list[CheckResult]:
    results = []
    with engine.begin() as conn:
        n_stg = conn.execute(text(
            "SELECT COUNT(*) FROM stg_conclusion_no_match"
        )).scalar()
        n_sci_cids = conn.execute(text(
            "SELECT COUNT(DISTINCT conclusion_id) FROM silver_conclusion_items"
        )).scalar()
        n_stg_cids = conn.execute(text(
            "SELECT COUNT(*) FROM stg_conclusion_no_match"
        )).scalar()
    with raw_engine.begin() as conn:
        n_concl_total = conn.execute(text(
            "SELECT COUNT(*) FROM conclusiones"
        )).scalar()

    n_covered = n_sci_cids + n_stg_cids

    results.append(CheckResult(
        "F1", "stg_conclusion_no_match poblada",
        n_stg > 0,
        f"{n_stg} filas",
    ))
    results.append(CheckResult(
        "F2", "sci.conclusion_id ∪ stg.conclusion_id cubre raw.conclusiones",
        n_covered >= n_concl_total,
        f"{n_covered} cubiertas / {n_concl_total} totales",
    ))
    return results


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verificación post-F5 de Silver")
    p.add_argument("--root", type=Path, default=Path.cwd(),
                   help="Raíz del proyecto (default: cwd)")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Muestra detalle de los checks")
    args = p.parse_args(argv)

    root: Path = args.root.resolve()
    engine: Engine = silver_db.get_engine(root)
    raw_engine: Engine = db.get_engine("sqlite", root)

    print("=" * 78)
    print("VERIFICACIÓN F5 — Extracción de ítems de CONCLUSIONES (Opción C)")
    print("=" * 78)

    section_results: dict[str, list[CheckResult]] = {
        "A. Esquema silver_conclusion_items": check_a_esquema(engine),
        "B. dim_termino_conclusion poblado": check_b_dim_termino(engine),
        "C. Volumen y cobertura (CRITERIO GO)": check_c_volumen_cobertura(engine, raw_engine),
        "D. Distribución por tipo_item": check_d_distribucion_tipo(engine),
        "E. Cardinalidad de modificadores": check_e_modificadores(engine),
        "F. No-match staging": check_f_no_match(engine, raw_engine),
    }

    total = 0
    passed = 0
    failed: list[CheckResult] = []

    for section, results in section_results.items():
        print(f"\n[{section}]")
        for r in results:
            print(repr(r))
            total += 1
            if r.passed:
                passed += 1
            else:
                failed.append(r)

    print("\n" + "=" * 78)
    print(f"RESULTADO: {passed}/{total} checks pasaron")

    if failed:
        print(f"\n❌ FAIL — {len(failed)} check(s) no cumplido(s):")
        for r in failed:
            print(f"   {r.code}: {r.label}")
            print(f"      {r.detail}")
        verdict = "NO-GO"
    else:
        print("\n✅ PASS — Todos los criterios cumplidos")
        print("   → F5 listo para proceder a capa Gold")
        verdict = "GO"

    print(f"\n>>> VEREDICTO F5: {verdict} <<<")

    engine.dispose()
    raw_engine.dispose()
    return 0 if not failed else 1


if __name__ == "__main__":
    # Forzar UTF-8 en stdout (Windows cp1252 rompe con caracteres acentuados)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())
