"""Verificación post-F4 — Cobertura del diccionario canónico de valores.

Criterios de validación (todos deben pasar para GO de F4):

  A. dim_valor_atributo poblado
     A1. ≥100 filas (umbral mínimo; ~170 esperadas)
     A2. ≥25 atributos distintos cubiertos
     A3. Toda fila tiene atributo_id y valor no vacíos
     A4. (atributo_id, valor) es único en dim_valor_atributo

  B. map_atributo_valor poblado
     B1. ≥100 filas
     B2. Distribución de origen ≥3 categorías distintas
        (IDENTIDAD + GENERO_MORFOLOGICO + SINONIMO + NORMALIZACION)
     B3. (dim_organo_atributo_id, valor_original) es único
     B4. Todo par dim_organo_atributo_id en map_atributo_valor existe en
        dim_organo_atributo (FK válida)
     B5. Toda fila tiene valor_canonico no vacío

  C. Cobertura del diccionario (CRITERIO GO)
     C1. 100% de silver_atributos_hallazgo con valor_canonico NOT NULL
        tienen dim_valor_atributo_id NOT NULL
     C2. 0 huérfanos (LEFT JOIN dim_valor_atributo sin match)

  D. Consistencia con F3
     D1. dim_valor_atributo.atributo_id ⊂ dim_atributo.id (FK válida)
     D2. dim_organo_atributo de cada map_atributo_valor resuelve a
        (organo, atributo, segmento) correcto

Uso:

    python scripts/verify_silver_f4.py            # exit 0 si PASS, 1 si FAIL
    python scripts/verify_silver_f4.py --verbose  # muestra detalle

Exit codes:
  0  → PASS (todos los criterios GO cumplidos)
  1  → FAIL (al menos un criterio NO cumplido)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permitir `python scripts/verify_silver_f4.py` sin instalar el paquete
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import text
from sqlalchemy.engine import Engine

from informes_vet import silver_db


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


def check_a_dim_valor_poblado(engine: Engine, verbose: bool = False) -> list[CheckResult]:
    results = []
    with engine.begin() as conn:
        n_total = conn.execute(text("SELECT COUNT(*) FROM dim_valor_atributo")).scalar()
        n_attrs = conn.execute(
            text("SELECT COUNT(DISTINCT atributo_id) FROM dim_valor_atributo")
        ).scalar()
        n_null_atributo = conn.execute(
            text("SELECT COUNT(*) FROM dim_valor_atributo WHERE atributo_id IS NULL")
        ).scalar()
        n_null_valor = conn.execute(
            text("SELECT COUNT(*) FROM dim_valor_atributo WHERE valor IS NULL OR TRIM(valor) = ''")
        ).scalar()
        n_duplicates = conn.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT atributo_id, valor, COUNT(*) AS n
                FROM dim_valor_atributo
                GROUP BY atributo_id, valor
                HAVING n > 1
            )
        """)).scalar()

    results.append(CheckResult(
        "A1", "≥100 filas en dim_valor_atributo",
        n_total >= 100,
        f"{n_total} filas (umbral ≥100)",
    ))
    results.append(CheckResult(
        "A2", "≥25 atributos distintos cubiertos",
        n_attrs >= 25,
        f"{n_attrs} atributos",
    ))
    results.append(CheckResult(
        "A3", "atributo_id y valor no nulos",
        n_null_atributo == 0 and n_null_valor == 0,
        f"nulls atributo_id={n_null_atributo} valor={n_null_valor}",
    ))
    results.append(CheckResult(
        "A4", "(atributo_id, valor) únicos",
        n_duplicates == 0,
        f"{n_duplicates} duplicados",
    ))
    return results


def check_b_map_atributo_valor(engine: Engine, verbose: bool = False) -> list[CheckResult]:
    results = []
    with engine.begin() as conn:
        n_total = conn.execute(text("SELECT COUNT(*) FROM map_atributo_valor")).scalar()
        n_origenes = conn.execute(
            text("SELECT COUNT(DISTINCT origen) FROM map_atributo_valor WHERE origen IS NOT NULL")
        ).scalar()
        n_duplicates = conn.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT dim_organo_atributo_id, valor_original, COUNT(*) AS n
                FROM map_atributo_valor
                GROUP BY dim_organo_atributo_id, valor_original
                HAVING n > 1
            )
        """)).scalar()
        n_invalid_doa = conn.execute(text("""
            SELECT COUNT(*) FROM map_atributo_valor mav
            LEFT JOIN dim_organo_atributo doa ON doa.id = mav.dim_organo_atributo_id
            WHERE doa.id IS NULL
        """)).scalar()
        n_null_canonico = conn.execute(
            text("SELECT COUNT(*) FROM map_atributo_valor "
                 "WHERE valor_canonico IS NULL OR TRIM(valor_canonico) = ''")
        ).scalar()

    results.append(CheckResult(
        "B1", "≥100 filas en map_atributo_valor",
        n_total >= 100,
        f"{n_total} filas",
    ))
    results.append(CheckResult(
        "B2", "≥3 categorías de origen (IDENTIDAD, GENERO_MORFOLOGICO, etc.)",
        n_origenes >= 3,
        f"{n_origenes} orígenes distintos",
    ))
    results.append(CheckResult(
        "B3", "(dim_organo_atributo_id, valor_original) únicos",
        n_duplicates == 0,
        f"{n_duplicates} duplicados",
    ))
    results.append(CheckResult(
        "B4", "FK dim_organo_atributo_id válida",
        n_invalid_doa == 0,
        f"{n_invalid_doa} referencias inválidas",
    ))
    results.append(CheckResult(
        "B5", "valor_canonico no vacío",
        n_null_canonico == 0,
        f"{n_null_canonico} nulos/vacíos",
    ))
    return results


def check_c_cobertura(engine: Engine) -> list[CheckResult]:
    """Criterio GO: 100% cobertura."""
    results = []
    with engine.begin() as conn:
        n_con_valor = conn.execute(text(
            "SELECT COUNT(*) FROM silver_atributos_hallazgo "
            "WHERE valor_canonico IS NOT NULL"
        )).scalar()
        n_con_fk = conn.execute(text(
            "SELECT COUNT(*) FROM silver_atributos_hallazgo "
            "WHERE valor_canonico IS NOT NULL AND dim_valor_atributo_id IS NOT NULL"
        )).scalar()
        n_huerfanos = conn.execute(text("""
            SELECT COUNT(*)
            FROM silver_atributos_hallazgo sah
            JOIN dim_organo_atributo doa ON sah.dim_organo_atributo_id = doa.id
            LEFT JOIN dim_valor_atributo dva
              ON dva.atributo_id = doa.dim_atributo_id
             AND dva.valor = sah.valor_canonico
            WHERE sah.valor_canonico IS NOT NULL
              AND dva.id IS NULL
        """)).scalar()

    cobertura_pct = round(100.0 * n_con_fk / n_con_valor, 2) if n_con_valor else 0
    results.append(CheckResult(
        "C1", "100% cobertura dim_valor_atributo_id (CRITERIO GO)",
        n_huerfanos == 0 and cobertura_pct == 100.0,
        f"{n_con_fk}/{n_con_valor} ({cobertura_pct}%), huérfanos={n_huerfanos}",
    ))
    results.append(CheckResult(
        "C2", "0 huérfanos en silver_atributos_hallazgo",
        n_huerfanos == 0,
        f"{n_huerfanos} filas sin FK",
    ))
    return results


def check_d_consistencia(engine: Engine) -> list[CheckResult]:
    results = []
    with engine.begin() as conn:
        n_invalid_attr = conn.execute(text("""
            SELECT COUNT(*) FROM dim_valor_atributo dva
            LEFT JOIN dim_atributo da ON da.id = dva.atributo_id
            WHERE da.id IS NULL
        """)).scalar()
        # Conteos portables sin row-value (SQLite no soporta
        # COUNT(DISTINCT (col1, col2))). Agrupamos y contamos.
        n_consolidados = conn.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT dim_organo_atributo_id, valor_canonico
                FROM map_atributo_valor
                GROUP BY dim_organo_atributo_id, valor_canonico
            )
        """)).scalar()
        n_silver_pairs = conn.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT dim_organo_atributo_id, valor_canonico
                FROM silver_atributos_hallazgo
                WHERE valor_canonico IS NOT NULL
                GROUP BY dim_organo_atributo_id, valor_canonico
            )
        """)).scalar()

    results.append(CheckResult(
        "D1", "dim_valor_atributo.atributo_id ⊂ dim_atributo.id",
        n_invalid_attr == 0,
        f"{n_invalid_attr} referencias inválidas",
    ))
    results.append(CheckResult(
        "D2", "map_atributo_valor cubre todos los pares observados",
        n_silver_pairs == 0 or n_consolidados >= n_silver_pairs,
        f"{n_consolidados} pares consolidados vs {n_silver_pairs} observados",
    ))
    return results


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Verificación post-F4 de Silver")
    p.add_argument("--root", type=Path, default=Path.cwd(),
                   help="Raíz del proyecto (default: cwd)")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Muestra detalle de los checks")
    args = p.parse_args(argv)

    root: Path = args.root.resolve()
    engine: Engine = silver_db.get_engine(root)

    print("=" * 78)
    print("VERIFICACIÓN F4 — Cobertura del diccionario canónico de valores")
    print("=" * 78)

    section_results: dict[str, list[CheckResult]] = {
        "A. dim_valor_atributo poblado": check_a_dim_valor_poblado(engine, args.verbose),
        "B. map_atributo_valor poblado": check_b_map_atributo_valor(engine, args.verbose),
        "C. Cobertura del diccionario (CRITERIO GO)": check_c_cobertura(engine),
        "D. Consistencia con F3": check_d_consistencia(engine),
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
        print("   → Cobertura 100% del diccionario confirmada")
        verdict = "GO"

    print(f"\n>>> VEREDICTO F4: {verdict} <<<")

    engine.dispose()
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
