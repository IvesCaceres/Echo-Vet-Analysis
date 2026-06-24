"""Reporte de revisión clínica de valores canónicos (F4 review).

Para cada atributo (agrupado por nombre canónico, no por par órgano+atributo)
muestra los valores distintos observados en silver_atributos_hallazgo,
ordenados por frecuencia, con cobertura acumulada top 5.

Objetivo: validación MANUAL previa a poblar dim_valor_atributo.
NO modifica datos; sólo lee y emite docs/F4_VALUE_DICTIONARY_REVIEW.md.

Agrupación: por `dim_atributo.nombre_canonico` (no por par órgano+atributo).
Cuando el mismo atributo existe en varios órganos (ej. `tamano` en Hígado,
Bazo, Riñones, etc.) los valores se consolidan en una sola tabla de revisión.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from informes_vet.silver_db import get_engine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-kind", default="sqlite")
    parser.add_argument("--top", type=int, default=20,
                        help="Valores top a mostrar por atributo (default 20)")
    args = parser.parse_args()

    eng = get_engine(ROOT, db_kind=args.db_kind)

    # ─── 1. Datos: total + frecuencias por atributo ───
    sql = text("""
        SELECT
            a.nombre_canonico AS atributo,
            sah.valor_canonico AS valor,
            COUNT(*) AS n,
            COUNT(DISTINCT sah.hallazgo_id) AS n_hallazgos
        FROM silver_atributos_hallazgo sah
        JOIN dim_organo_atributo doa ON sah.dim_organo_atributo_id = doa.id
        JOIN dim_atributo a ON doa.dim_atributo_id = a.id
        WHERE sah.valor_canonico IS NOT NULL
        GROUP BY a.nombre_canonico, sah.valor_canonico
        ORDER BY a.nombre_canonico, n DESC
    """)
    with eng.connect() as c:
        rows = c.execute(sql).all()

    # ─── 2. Agrupar por atributo ───
    by_attr: dict[str, list[tuple[str, int, int]]] = defaultdict(list)
    for atributo, valor, n, n_hallazgos in rows:
        by_attr[atributo].append((valor, n, n_hallazgos))

    # ─── 3. Para cada atributo: en qué órganos aparece + tabla top-N ───
    organs_sql = text("""
        SELECT
            a.nombre_canonico AS atributo,
            GROUP_CONCAT(DISTINCT o.nombre_canonico) AS organos,
            COUNT(DISTINCT o.id) AS n_organos
        FROM silver_atributos_hallazgo sah
        JOIN dim_organo o ON sah.dim_organo_id = o.id
        JOIN dim_organo_atributo doa ON sah.dim_organo_atributo_id = doa.id
        JOIN dim_atributo a ON doa.dim_atributo_id = a.id
        WHERE sah.valor_canonico IS NOT NULL
        GROUP BY a.nombre_canonico
    """)
    with eng.connect() as c:
        organs_map = {row[0]: (row[1], row[2]) for row in c.execute(organs_sql).all()}

    # ─── 4. Construir markdown ───
    md: list[str] = []
    md.append("# F4 — Revisión clínica del diccionario de valores canónicos\n")
    md.append("**Fecha:** 2026-06-23  ")
    md.append("**Fuente:** `silver_atributos_hallazgo.valor_canonico` (post-F3, 107,409 filas)  ")
    md.append(f"**Agrupación:** por `dim_atributo.nombre_canonico` (NO por par órgano+atributo).  ")
    md.append(f"**Objetivo:** validación manual antes de poblar `dim_valor_atributo` y `map_atributo_valor`.\n")
    md.append("**Instrucciones de revisión:**")
    md.append("- ¿Todos los valores canónicos tienen sentido clínico para el atributo?")
    md.append("- ¿Hay sinónimos que deberían mapearse al mismo canónico? (ej. AUMENTADO ↔ AUMENTADA)")
    md.append("- ¿Algún valor es ruido o artefacto de regex que debe limpiarse?")
    md.append("- ¿La cobertura top-5 ≥95% indica que el resto es marginal o hay un valor importante en cola larga?\n")
    md.append("---\n")

    # Resumen
    md.append("## Resumen\n")
    md.append(f"- **Atributos únicos:** {len(by_attr)}")
    md.append(f"- **Total valores distintos (suma):** {sum(len(v) for v in by_attr.values())}")
    md.append("")
    md.append("| # | Atributo | Observaciones | Hallazgos únicos | Valores | Órganos |")
    md.append("|--:|----------|--------------:|-----------------:|--------:|---------|")
    for i, (atributo, valores) in enumerate(sorted(by_attr.items()), 1):
        total_n = sum(n for _, n, _ in valores)
        total_h = sum(h for _, _, h in valores)
        organs, n_orgs = organs_map.get(atributo, ("?", 0))
        md.append(f"| {i} | `{atributo}` | {total_n:,} | {total_h:,} | {len(valores)} | {n_orgs} ({organs}) |")

    md.append("\n---\n")

    # Detalle por atributo
    md.append("## Detalle por atributo\n")
    for atributo in sorted(by_attr.keys()):
        valores = by_attr[atributo]
        total_n = sum(n for _, n, _ in valores)
        n_distintos = len(valores)
        organs, n_orgs = organs_map.get(atributo, ("?", 0))

        # Cobertura acumulada
        sorted_vals = sorted(valores, key=lambda x: -x[1])
        top5 = sorted_vals[:5]
        top5_n = sum(n for _, n, _ in top5)
        top5_pct = 100 * top5_n / total_n if total_n else 0
        top5_distintos_pct = 100 * len(top5) / n_distintos

        md.append(f"### `{atributo}`\n")
        md.append(f"- **Observaciones:** {total_n:,}  ")
        md.append(f"- **Hallazgos únicos:** {sum(h for _, _, h in valores):,}  ")
        md.append(f"- **Valores distintos:** {n_distintos}  ")
        md.append(f"- **Órganos donde aplica ({n_orgs}):** {organs}  ")
        md.append(f"- **Top-5 cobertura:** {top5_pct:.1f}% ({top5_n:,}/{total_n:,}, {len(top5)}/{n_distintos} valores = {top5_distintos_pct:.0f}% de los distintos)  ")
        if top5_pct >= 95:
            md.append(f"- ✅ **Distribución saludable:** top-5 cubre ≥95%")
        elif top5_pct >= 80:
            md.append(f"- ⚠️ **Distribución moderadamente dispersa:** top-5 cubre {top5_pct:.1f}%")
        else:
            md.append(f"- ❌ **Cola larga relevante:** top-5 cubre solo {top5_pct:.1f}%")
        md.append("")
        md.append("| # | Valor canónico | Frecuencia | % | Acumulado % |")
        md.append("|--:|----------------|-----------:|--:|------------:|")
        cumul = 0
        for rank, (v, n, _) in enumerate(sorted_vals[:args.top], 1):
            cumul += n
            pct = 100 * n / total_n
            cum_pct = 100 * cumul / total_n
            md.append(f"| {rank} | `{v}` | {n:,} | {pct:.2f}% | {cum_pct:.2f}% |")

        # Cola más allá del top
        if len(sorted_vals) > args.top:
            tail = sorted_vals[args.top:]
            tail_n = sum(n for _, n, _ in tail)
            md.append(f"| … | _(resto: {len(tail)} valores)_ | {tail_n:,} | "
                      f"{100*tail_n/total_n:.2f}% | 100.00% |")
        md.append("")

    # ─── 5. Escribir ───
    out_path = ROOT / "docs" / "F4_VALUE_DICTIONARY_REVIEW.md"
    out_path.write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] Reporte: {out_path}")
    print(f"     Atributos: {len(by_attr)}")
    print(f"     Valores distintos totales: {sum(len(v) for v in by_attr.values())}")


if __name__ == "__main__":
    main()
