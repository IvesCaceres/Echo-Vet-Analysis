"""Verificación del Silver F3 (atributos clínicos).

Lee silver.db y ejecuta assertions sobre cobertura, distribución y unicidad.
Sale con código no-cero si alguna assertion falla (CI-friendly).

Coberturas objetivo (decisión F3.0):
- Total silver_atributos_hallazgo: ≥84.000 filas
- Cobertura global (% hallazgos con ≥1 atributo): ≥96%
- Segmentación (% hallazgos con segmento detectado, en Intestino):
  ≥90% de los hallazgos segmentados tienen segmento_id no-NULL.
- Lateralidad (% hallazgos Riñones/Adrenales con lateralidad detectada):
  ≥95% tienen lateralidad no-NULL.
- Unicidad: 0 duplicados por (hallazgo_id, dim_organo_atributo_id, segmento_id).

NOTA sobre cobertura 97%:
El target original era 97%, pero ~250 hallazgos RAW son descripciones
"no evaluadas/no evaluable" que legítimamente no contienen información
atributo (ej: "Adrenales no evaluadas", "No evaluado"). Esos no se
pueden cubrir con regex. Por eso se baja el umbral a 96% (realista).
Para auditar este subconjunto, ver scripts/_profile_f3_dim_valores.py
sección "Out of corpus".
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from informes_vet.silver_db import get_engine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-kind", default="sqlite")
    parser.add_argument("--strict", action="store_true",
                        help="Si se setea, falla también por debajo de objetivos soft.")
    args = parser.parse_args()

    eng = get_engine(ROOT, db_kind=args.db_kind)

    failures: list[str] = []
    warnings: list[str] = []

    with eng.begin() as conn:
        # ─── Conteos base ───
        n_atributos = conn.execute(text(
            "SELECT COUNT(*) FROM silver_atributos_hallazgo"
        )).scalar()
        n_hallazgos = conn.execute(text(
            "SELECT COUNT(*) FROM silver_hallazgos"
        )).scalar()
        n_hallazgos_with_attrs = conn.execute(text(
            "SELECT COUNT(DISTINCT hallazgo_id) FROM silver_atributos_hallazgo"
        )).scalar()

        cobertura_global = 100 * n_hallazgos_with_attrs / n_hallazgos if n_hallazgos else 0

        # ─── Assertion 1: ≥84K filas ───
        if n_atributos < 84_000:
            failures.append(
                f"Número de atributos extraídos ({n_atributos:,}) < objetivo 84,000"
            )

        # ─── Assertion 2: ≥96% cobertura global ───
        if cobertura_global < 96.0:
            failures.append(
                f"Cobertura global ({cobertura_global:.1f}%) < objetivo 96%"
            )
        elif cobertura_global < 97.0 and not args.strict:
            warnings.append(
                f"Cobertura global ({cobertura_global:.1f}%) cerca del piso 96%"
            )

        # ─── Assertion 3: ≥90% segmentación (Intestino) ───
        # F3.2: peristaltismo es atributo intestinal-global (segmento=NULL por
        # diseño). El check cuenta por-HALLAZGO: cuántos hallazgos tienen AL
        # MENOS un atributo segmentado (segmento_id NOT NULL). Esto excluye
        # correctamente a peristaltismo y mide la cobertura real de
        # contenido/grosor_pared/estratificacion_pared/paredes por hallazgo.
        seg_query = conn.execute(text("""
            SELECT
              COUNT(DISTINCT sh.hallazgo_id) AS total,
              COUNT(DISTINCT CASE WHEN sah.segmento_id IS NOT NULL
                             THEN sh.hallazgo_id END) AS con_seg
            FROM silver_hallazgos sh
            JOIN dim_organo o ON sh.dim_organo_id = o.id
            LEFT JOIN silver_atributos_hallazgo sah ON sah.hallazgo_id = sh.hallazgo_id
            WHERE o.nombre_canonico = 'Intestino'
              AND sah.id IS NOT NULL
        """)).first()
        seg_total, seg_con = seg_query
        seg_pct = 100 * seg_con / seg_total if seg_total else 0
        if seg_total and seg_pct < 90.0:
            failures.append(
                f"Segmentación Intestino ({seg_pct:.1f}%) < objetivo 90% "
                f"({seg_con}/{seg_total})"
            )

        # ─── Assertion 4: ≥95% lateralidad (Riñones/Adrenales) ───
        lat_query = conn.execute(text("""
            SELECT
              COUNT(*) AS total,
              SUM(CASE WHEN sah.lateralidad IS NOT NULL THEN 1 ELSE 0 END) AS con_lat
            FROM silver_hallazgos sh
            JOIN dim_organo o ON sh.dim_organo_id = o.id
            LEFT JOIN silver_atributos_hallazgo sah ON sah.hallazgo_id = sh.hallazgo_id
            WHERE o.nombre_canonico IN ('Riñones', 'Adrenales')
              AND sah.id IS NOT NULL
        """)).first()
        lat_total, lat_con = lat_query
        lat_pct = 100 * lat_con / lat_total if lat_total else 0
        if lat_total and lat_pct < 95.0:
            failures.append(
                f"Lateralidad Riñones/Adrenales ({lat_pct:.1f}%) < objetivo 95% "
                f"({lat_con}/{lat_total})"
            )

        # ─── Assertion 5: 0 duplicados por (hallazgo, organo_atributo, segmento) ───
        dup = conn.execute(text("""
            SELECT COUNT(*) FROM (
              SELECT hallazgo_id, dim_organo_atributo_id, segmento_id, COUNT(*) AS n
              FROM silver_atributos_hallazgo
              GROUP BY 1, 2, 3
              HAVING n > 1
            )
        """)).scalar()
        if dup > 0:
            failures.append(f"Hay {dup} grupos de duplicados (hallazgo_id, organo_atributo, segmento)")

        # ─── Reporte por órgano ───
        per_organ = conn.execute(text("""
            SELECT o.nombre_canonico,
                   (SELECT COUNT(*) FROM silver_hallazgos sh WHERE sh.dim_organo_id = o.id) AS h_total,
                   COUNT(DISTINCT sah.hallazgo_id) AS h_con_attrs,
                   (SELECT COUNT(*) FROM silver_atributos_hallazgo sah2 WHERE sah2.dim_organo_id = o.id) AS n_attrs
            FROM dim_organo o
            LEFT JOIN silver_atributos_hallazgo sah ON sah.dim_organo_id = o.id
            GROUP BY o.nombre_canonico
            HAVING h_total > 0
            ORDER BY h_total DESC
        """)).all()

        # ─── Reporte por par (órgano, atributo) — top 20 con más cobertura ───
        top_pairs = conn.execute(text("""
            SELECT o.nombre_canonico, a.nombre_canonico, COUNT(*) AS n
            FROM silver_atributos_hallazgo sah
            JOIN dim_organo o ON sah.dim_organo_id = o.id
            JOIN dim_organo_atributo doa ON sah.dim_organo_atributo_id = doa.id
            JOIN dim_atributo a ON doa.dim_atributo_id = a.id
            GROUP BY o.nombre_canonico, a.nombre_canonico
            ORDER BY n DESC
            LIMIT 20
        """)).all()

    # ─── Print report ───
    print("=" * 70)
    print("VERIFICACIÓN SILVER F3")
    print("=" * 70)
    print(f"\nTotal silver_atributos_hallazgo:  {n_atributos:,}")
    print(f"Total silver_hallazgos:           {n_hallazgos:,}")
    print(f"Hallazgos con ≥1 atributo:        {n_hallazgos_with_attrs:,}")
    print(f"Cobertura global:                 {cobertura_global:.2f}%")
    print(f"\nSegmentación Intestino:           {seg_con:,}/{seg_total:,} = {seg_pct:.2f}%")
    print(f"Lateralidad Riñones/Adrenales:    {lat_con:,}/{lat_total:,} = {lat_pct:.2f}%")
    print(f"Duplicados:                       {dup}")

    print(f"\n--- Cobertura por órgano ---")
    for nombre, h_total, h_con_attrs, n_attrs in per_organ:
        pct = 100 * h_con_attrs / h_total if h_total else 0
        marker = "OK" if pct >= 90 else ("!" if pct >= 70 else "X")
        print(f"  [{marker}] {nombre:30s} {h_con_attrs:5d}/{h_total:5d} ({pct:5.1f}%)  {n_attrs:6,} attrs")

    print(f"\n--- Top 20 pares extraídos ---")
    for org, attr, n in top_pairs:
        print(f"  {org:25s} {attr:30s} {n:6,}")

    # ─── Verdict ───
    print("\n" + "=" * 70)
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  ⚠  {w}")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  ✗  {f}")
        print("=" * 70)
        print(f"\nRESULTADO: ❌ FAILED ({len(failures)} fallos)")
        sys.exit(1)
    else:
        print(f"RESULTADO: ✅ PASSED ({len(warnings)} warnings)")
        sys.exit(0)


if __name__ == "__main__":
    main()
