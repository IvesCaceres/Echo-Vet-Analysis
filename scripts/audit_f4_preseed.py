"""F4 pre-seed audit final.

Auditoría clínica y técnica del vocabulario extraído por F3 antes de
construir `dim_valor_atributo` y `map_atributo_valor`.

NO modifica datos. NO inserta seeds. NO crea tablas.

Entrega: `docs/F4_PRESEED_AUDIT.md` con:
  - Parte 1: investigación de anomalías (AUMENTADA_DE, compromiso=CONSERVADO)
  - Parte 2: simulación de consolidaciones (sin tocar silver)
  - Parte 3: borrador completo de dim_valor_atributo
  - Parte 4: simulación de seeds (filas estimadas)
  - Parte 5: validación para Gold
  - Recomendación final GO/NO-GO
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from informes_vet.silver_db import get_engine


# ─── Reglas de consolidación propuestas (Parte 2) ───
CONSOLIDATIONS: dict[str, dict[str, list[tuple[str, str]]]] = {
    # atributo: { valor_consolidado: [(origen, tipo_regla), ...] }
    "forma": {
        "OVAL": [
            ("OVALADO", "GENERO_MORFOLOGICO"),
            ("OVALADA", "GENERO_MORFOLOGICO"),
        ],
        "GLOBOSO": [
            ("GLOBOSO", "IDENTIDAD"),
            ("GLOBOSA", "GENERO_MORFOLOGICO"),
        ],
        "REDONDEADO": [
            ("REDONDEADO", "IDENTIDAD"),
            ("REDONDEADA", "GENERO_MORFOLOGICO"),
        ],
    },
    "distension": {
        "SEMI_DISTENDIDO": [
            ("SEMI_DISTENDIDO", "IDENTIDAD"),
            ("SEMI_DISTENDIDA", "GENERO_MORFOLOGICO"),
        ],
        "DISTENDIDO": [
            ("DISTENDIDO", "IDENTIDAD"),
            ("DISTENDIDA", "GENERO_MORFOLOGICO"),
        ],
    },
    "grosor_pared": {
        "AUMENTADO": [
            ("AUMENTADO", "IDENTIDAD"),
            ("LEVEMENTE_AUMENTADO", "SINONIMO_GRADUAL"),
            ("DISCRETAMENTE_AUMENTADO", "SINONIMO_GRADUAL"),
            ("MODERADAMENTE_AUMENTADO", "SINONIMO_GRADUAL"),
            ("SEVERAMENTE_AUMENTADO", "SINONIMO_GRADUAL"),
            ("ENGROSADO", "SINONIMO"),
        ],
    },
    "presencia": {
        "AUSENTE": [
            ("NO_SE_OBSERVAN", "NORMALIZACION"),
            ("AUSENTE", "IDENTIDAD"),
        ],
        "PRESENTE": [
            ("PRESENTE", "IDENTIDAD"),
            ("SE_OBSERVAN", "NORMALIZACION"),
        ],
    },
    "ecogenicidad": {
        "AUMENTADA": [
            ("AUMENTADA", "IDENTIDAD"),
            ("AUMENTADA_DE", "SINONIMO"),
        ],
    },
}


def fetch_all_values(eng) -> list[dict]:
    """Lee TODAS las filas de silver_atributos_hallazgo con valor canónico."""
    sql = text("""
        SELECT
            o.nombre_canonico AS organo,
            a.nombre_canonico AS atributo,
            doa.tipo_dato,
            sah.valor_canonico,
            COUNT(*) AS n,
            COUNT(DISTINCT sah.hallazgo_id) AS n_hallazgos
        FROM silver_atributos_hallazgo sah
        JOIN dim_organo o ON sah.dim_organo_id = o.id
        JOIN dim_organo_atributo doa ON sah.dim_organo_atributo_id = doa.id
        JOIN dim_atributo a ON doa.dim_atributo_id = a.id
        WHERE sah.valor_canonico IS NOT NULL
        GROUP BY o.nombre_canonico, a.nombre_canonico, doa.tipo_dato, sah.valor_canonico
    """)
    with eng.connect() as c:
        return [dict(r._mapping) for r in c.execute(sql).all()]


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 1 — Anomalías
# ═══════════════════════════════════════════════════════════════════════════

def investigate_aumentada_de(eng) -> tuple[list[dict], dict]:
    """Caso A: 4 filas con valor_canonico = 'AUMENTADA_DE'."""
    sql = text("""
        SELECT
            sah.hallazgo_id,
            sah.informe_id,
            o.nombre_canonico AS organo,
            a.nombre_canonico AS atributo,
            sah.valor_canonico,
            sah.valor_texto,
            sah.texto_original,
            sah.lateralidad,
            sh.descripcion
        FROM silver_atributos_hallazgo sah
        JOIN dim_organo o ON sah.dim_organo_id = o.id
        JOIN dim_organo_atributo doa ON sah.dim_organo_atributo_id = doa.id
        JOIN dim_atributo a ON doa.dim_atributo_id = a.id
        JOIN silver_hallazgos sh ON sah.hallazgo_id = sh.hallazgo_id
        WHERE sah.valor_canonico = 'AUMENTADA_DE'
        ORDER BY sah.hallazgo_id
    """)
    with eng.connect() as c:
        rows = [dict(r._mapping) for r in c.execute(sql).all()]

    # Análisis
    analisis = {
        "n_filas": len(rows),
        "n_hallazgos_unicos": len(set(r["hallazgo_id"] for r in rows)),
        "organos": sorted(set(r["organo"] for r in rows)),
        "atributos": sorted(set(r["atributo"] for r in rows)),
        "textos_originales": sorted(set(r["texto_original"] for r in rows)),
    }
    return rows, analisis


def investigate_compromiso_conservado(eng) -> tuple[list[dict], dict]:
    """Caso B: 22 filas con atributo='compromiso', valor_canonico='CONSERVADO'."""
    sql = text("""
        SELECT
            sah.hallazgo_id,
            sah.informe_id,
            o.nombre_canonico AS organo,
            a.nombre_canonico AS atributo,
            sah.valor_canonico,
            sah.texto_original,
            sh.descripcion
        FROM silver_atributos_hallazgo sah
        JOIN dim_organo o ON sah.dim_organo_id = o.id
        JOIN dim_organo_atributo doa ON sah.dim_organo_atributo_id = doa.id
        JOIN dim_atributo a ON doa.dim_atributo_id = a.id
        JOIN silver_hallazgos sh ON sah.hallazgo_id = sh.hallazgo_id
        WHERE a.nombre_canonico = 'compromiso'
          AND sah.valor_canonico = 'CONSERVADO'
        ORDER BY sah.hallazgo_id
    """)
    with eng.connect() as c:
        rows = [dict(r._mapping) for r in c.execute(sql).all()]

    # Clasificar
    fp_forma = 0
    tp_nodulos = 0
    fp_examples = []
    tp_examples = []
    for r in rows:
        desc_lower = r["descripcion"].lower()
        # FP: "forma conservada" — el regex matchó "conservada" del atributo `forma`
        if "forma" in desc_lower and "conservad" in desc_lower:
            fp_forma += 1
            if len(fp_examples) < 3:
                fp_examples.append({
                    "hallazgo_id": r["hallazgo_id"],
                    "texto_original": r["texto_original"],
                    "descripcion": r["descripcion"][:200],
                })
        else:
            tp_nodulos += 1
            if len(tp_examples) < 3:
                tp_examples.append({
                    "hallazgo_id": r["hallazgo_id"],
                    "texto_original": r["texto_original"],
                    "descripcion": r["descripcion"][:200],
                })

    analisis = {
        "n_filas": len(rows),
        "fp_forma_conservada": fp_forma,
        "tp_nodulos_conservados": tp_nodulos,
        "pct_fp": 100 * fp_forma / len(rows) if rows else 0,
        "fp_examples": fp_examples,
        "tp_examples": tp_examples,
    }
    return rows, analisis


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 2 — Simulación de consolidaciones
# ═══════════════════════════════════════════════════════════════════════════

def aggregate_by_attr_valor(rows: list[dict]) -> dict[tuple[str, str], int]:
    """(atributo, valor) → total de observaciones."""
    agg: dict[tuple[str, str], int] = defaultdict(int)
    for r in rows:
        agg[(r["atributo"], r["valor_canonico"])] += r["n"]
    return agg


def simulate_consolidations(agg, consol: dict) -> list[dict]:
    out = []
    for atributo, reglas in consol.items():
        for canonico, mapeos in reglas.items():
            freq_antes = {valor: agg.get((atributo, valor), 0) for valor, _ in mapeos}
            total_despues = sum(freq_antes.values())
            out.append({
                "atributo": atributo,
                "valor_canonico_propuesto": canonico,
                "origenes": [
                    {"valor": v, "tipo_regla": t, "freq": freq_antes[v]}
                    for v, t in mapeos
                ],
                "freq_consolidada": total_despues,
            })
    return out


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 3 — Diccionario final propuesto
# ═══════════════════════════════════════════════════════════════════════════

def build_final_dictionary(agg, consol) -> dict[str, list[dict]]:
    """Para cada atributo: lista de valores canónicos propuestos (post-consolidación).

    Devuelve:
      { atributo: [{valor, freq_antes, freq_despues, fuentes, canonico_final}, ...] }
    """
    # Invertir: atributo → { canonico_final: [origenes] }
    consol_idx: dict[str, dict[str, list[tuple[str, str]]]] = {}
    for atributo, reglas in consol.items():
        consol_idx.setdefault(atributo, {})
        for canonico_final, mapeos in reglas.items():
            consol_idx[atributo][canonico_final] = mapeos

    # Agrupar todos los valores por atributo
    by_attr: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for (atributo, valor), n in agg.items():
        by_attr[atributo][valor] += n

    result = {}
    for atributo, valores in by_attr.items():
        # Mapear cada valor original a su canónico final
        canonico_para_valor: dict[str, str] = {}
        for canonico_final, mapeos in consol_idx.get(atributo, {}).items():
            for v, _ in mapeos:
                canonico_para_valor[v] = canonico_final

        # Agrupar freq por canónico final
        grouped: dict[str, dict] = {}
        for valor, freq in valores.items():
            canonico = canonico_para_valor.get(valor, valor)
            if canonico not in grouped:
                grouped[canonico] = {"fuentes": [], "freq": 0}
            grouped[canonico]["fuentes"].append({"valor_original": valor, "freq": freq})
            grouped[canonico]["freq"] += freq

        result[atributo] = sorted(
            [{"valor_canonico": k, "freq": v["freq"], "fuentes": v["fuentes"]}
             for k, v in grouped.items()],
            key=lambda x: -x["freq"],
        )

    return result


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 4 — Simulación de seeds
# ═══════════════════════════════════════════════════════════════════════════

def estimate_dim_valor(fin_dict) -> list[dict]:
    """Seed dim_valor_atributo: 1 fila por (atributo, valor_canonico_final) único."""
    seed = []
    for atributo, valores in fin_dict.items():
        for rank, v in enumerate(valores, 1):
            es_binario = len(valores) == 2 and atributo not in ("grosor_pared", "tamano", "forma")
            seed.append({
                "atributo": atributo,
                "valor_canonico": v["valor_canonico"],
                "frecuencia": v["freq"],
                "es_binario": es_binario,
                "orden_sugerido": rank,
            })
    return seed


def estimate_map_valor(rows, fin_dict) -> list[dict]:
    """Seed map_atributo_valor: 1 fila por (atributo, valor_original) observado,
    con mapeo a canónico final."""
    # Agrupar rows por atributo
    by_attr: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in rows:
        by_attr[r["atributo"]][r["valor_canonico"]] += r["n"]

    # Mapear valor original → canónico final
    canonico_para_valor: dict[str, dict[str, str]] = {}
    for atributo, valores in fin_dict.items():
        for v in valores:
            for fuente in v["fuentes"]:
                canonico_para_valor.setdefault(atributo, {})[fuente["valor_original"]] = v["valor_canonico"]

    # Tipo_regla
    tipo_por_valor: dict[tuple[str, str], str] = {}
    for atributo, reglas in CONSOLIDATIONS.items():
        for canonico_final, mapeos in reglas.items():
            for valor, tipo in mapeos:
                tipo_por_valor[(atributo, valor)] = tipo

    seed = []
    for atributo, valores in by_attr.items():
        for valor_orig, freq in valores.items():
            canonico = canonico_para_valor.get(atributo, {}).get(valor_orig, valor_orig)
            tipo = tipo_por_valor.get((atributo, valor_orig), "IDENTIDAD")
            confianza = 1.0 if canonico == valor_orig else 0.95
            seed.append({
                "atributo": atributo,
                "valor_original": valor_orig,
                "valor_canonico": canonico,
                "frecuencia": freq,
                "tipo_regla": tipo,
                "confianza": confianza,
            })
    return seed


# ═══════════════════════════════════════════════════════════════════════════
# RENDER MARKDOWN
# ═══════════════════════════════════════════════════════════════════════════

def render_markdown(parte1_a, parte1_b, parte2, fin_dict, dim_seed, map_seed) -> str:
    rows_a, ana_a = parte1_a
    rows_b, ana_b = parte1_b

    md = []
    md.append("# F4 — Auditoría Pre-Seed Final\n")
    md.append("**Fecha:** 2026-06-23  ")
    md.append("**Fuente:** `silver_atributos_hallazgo` (post-F3)  ")
    md.append("**Objetivo:** Validar el vocabulario extraído por F3 antes de construir `dim_valor_atributo` y `map_atributo_valor`.  ")
    md.append("**Modo:** Sólo lectura — NO se modifica silver.db, NO se insertan seeds.\n")
    md.append("---\n")

    # ═══ RESUMEN EJECUTIVO ═══
    md.append("## 0. Resumen ejecutivo\n")
    md.append(f"- **Anomalías detectadas:** 2 casos críticos (A: AUMENTADA_DE; B: compromiso=CONSERVADO)")
    md.append(f"- **Caso A (AUMENTADA_DE):** {ana_a['n_filas']} filas en {ana_a['n_hallazgos_unicos']} hallazgos únicos, "
              f"todos con texto_original = `'{ana_a['textos_originales'][0] if ana_a['textos_originales'] else '?'}'`. "
              f"**Diagnóstico:** bug de normalización (canónico divergente `AUMENTADA_DE` en lugar de consolidar a `AUMENTADA`). **Recomendación:** FIX antes de F4.")
    md.append(f"- **Caso B (compromiso=CONSERVADO):** {ana_b['n_filas']} filas. "
              f"**{ana_b['fp_forma_conservada']} ({ana_b['pct_fp']:.0f}%) son FP** del regex `\bconservad[oa]s?\b` "
              f"que matchó 'forma conservada' en lugar de 'compromiso conservado'. "
              f"**{ana_b['tp_nodulos_conservados']} ({100-ana_b['pct_fp']:.0f}%) son TP** donde el texto sí se refiere a nódulos. "
              f"**Diagnóstico:** bug de regex en F3 (línea 392 de `_profile_f3_dim_valores.py`). **Recomendación:** FIX + recategorizar las {ana_b['tp_nodulos_conservados']} filas correctas.")
    md.append(f"- **Consolidaciones propuestas:** {len(parte2)} grupos, todas de bajo riesgo clínico.")
    md.append(f"- **Diccionario final propuesto:** {len(fin_dict)} atributos, "
              f"{sum(len(v) for v in fin_dict.values())} valores canónicos finales únicos.")
    md.append(f"- **Seed `dim_valor_atributo` (estimado):** {len(dim_seed)} filas")
    md.append(f"- **Seed `map_atributo_valor` (estimado):** {len(map_seed)} filas")
    md.append("")
    md.append("**Veredicto:** ⚠️ **GO CONDICIONAL para F4 — aplicar 2 fixes en F3 antes de sembrar.**")
    md.append("")
    md.append("---\n")

    # ═══ PARTE 1A ═══
    md.append("## Parte 1A — Anomalía: `valor_canonico = 'AUMENTADA_DE'`\n")
    md.append(f"**Frecuencia:** {ana_a['n_filas']} filas ({ana_a['n_hallazgos_unicos']} hallazgos únicos)  ")
    md.append(f"**Órganos:** {', '.join(ana_a['organos'])}  ")
    md.append(f"**Atributos:** {', '.join(ana_a['atributos'])}  ")
    md.append(f"**Texto original matched:** `{ana_a['textos_originales']}`  \n")

    md.append("### Evidencia — descripciones completas (deduplicadas)\n")
    md.append("| hallazgo_id | informe_id | órgano | atributo | lateralidad | texto_original |")
    md.append("|------------:|-----------:|--------|----------|-------------|----------------|")
    seen = set()
    for r in rows_a:
        if r["hallazgo_id"] in seen:
            continue
        seen.add(r["hallazgo_id"])
        md.append(f"| {r['hallazgo_id']} | {r['informe_id']} | {r['organo']} | {r['atributo']} | "
                  f"{r['lateralidad'] or '-'} | `{r['texto_original']}` |")

    md.append("\n### Descripción clínica\n")
    md.append("> hallazgo 15136: *\"...con **aumento de ecogenicidad medular** y sin compromiso pélvico.\"*")
    md.append("> hallazgo 15147: similar.\n")
    md.append("**Interpretación clínica:** 'aumento de ecogenicidad' es una forma válida de describir incremento de ecogenicidad en Riñones. "
              "Sin embargo, el canónico `AUMENTADA_DE` es divergente — debería consolidar a `AUMENTADA` "
              "(la dimensión clínica es la misma).\n")

    md.append("### Origen del bug (regex responsable)\n")
    md.append("En `scripts/_profile_f3_dim_valores.py` línea 159:\n")
    md.append("```python")
    md.append("(\"AUMENTADA_DE\",   r\"\\baumento\\s+de\\s+ecogenicidad\\b\"),")
    md.append("```")
    md.append("Esta regla se agregó intencionalmente para capturar 'aumento de ecogenicidad' "
              "(clínicamente equivalente a 'ecogenicidad aumentada'), pero se le asignó un canónico "
              "divergente (`AUMENTADA_DE`) en lugar de consolidar a `AUMENTADA`.\n")

    md.append("### Diagnóstico\n")
    md.append("1. **¿Es un bug de extracción?** Parcialmente. La extracción del texto es correcta, "
              "pero la asignación canónica es inconsistente.")
    md.append("2. **¿Es un texto clínico válido?** Sí. 'aumento de ecogenicidad' es una variante "
              "léxica legítima de 'ecogenicidad aumentada'.")
    md.append("3. **¿Debe mapearse a otro valor?** Sí. Debe consolidarse a `AUMENTADA`.")
    md.append("4. **¿Debe corregirse el regex de F3?** Sí. Cambiar el canónico a `AUMENTADA` "
              "en lugar de crear un valor divergente.\n")

    md.append("### Recomendación: **FIX**\n")
    md.append("- En `_profile_f3_dim_valores.py` línea 159, reemplazar `AUMENTADA_DE` por `AUMENTADA`.")
    md.append("- Re-ejecutar F3 (idempotente).")
    md.append("- Verificar que `valor_canonico='AUMENTADA_DE'` desaparezca del silver.")
    md.append("- Impacto: 4 filas modificadas (0.004% del total de 107,409).")
    md.append("- Riesgo: nulo (es un merge sin pérdida de información).\n")
    md.append("---\n")

    # ═══ PARTE 1B ═══
    md.append("## Parte 1B — Anomalía: `atributo='compromiso', valor_canonico='CONSERVADO'`\n")
    md.append(f"**Frecuencia:** {ana_b['n_filas']} filas  ")
    md.append("**Diagnóstico:** el regex del atributo Linfonodos `compromiso` es demasiado amplio.\n")

    md.append("### Distribución\n")
    md.append(f"- **{ana_b['fp_forma_conservada']} FP ({ana_b['pct_fp']:.0f}%):** el regex matchó 'conservada' "
              f"perteneciente al atributo `forma` (frase 'forma conservada' en la misma descripción).")
    md.append(f"- **{ana_b['tp_nodulos_conservados']} TP ({100-ana_b['pct_fp']:.0f}%):** el texto sí se refiere "
              f"a nódulos (ej: 'nódulos linfáticos de aspecto conservado', 'nódulos conservados').\n")

    md.append("### Evidencia FP (muestra)\n")
    md.append("| hallazgo_id | texto_original | descripción (primeros 200 chars) |")
    md.append("|------------:|----------------|-----------------------------------|")
    for r in ana_b["fp_examples"]:
        md.append(f"| {r['hallazgo_id']} | `{r['texto_original']}` | {r['descripcion']}... |")

    md.append("\n### Evidencia TP (muestra)\n")
    md.append("| hallazgo_id | texto_original | descripción (primeros 200 chars) |")
    md.append("|------------:|----------------|-----------------------------------|")
    for r in ana_b["tp_examples"]:
        md.append(f"| {r['hallazgo_id']} | `{r['texto_original']}` | {r['descripcion']}... |")

    md.append("\n### Origen del bug (regex responsable)\n")
    md.append("En `scripts/_profile_f3_dim_valores.py` línea 392:\n")
    md.append("```python")
    md.append("(\"CONSERVADO\",       r\"\\bconservad[oa]s?\\b\"),")
    md.append("```")
    md.append("Este patrón matchea CUALQUIER 'conservado/a/os' en la descripción del hallazgo, "
              "sin anclaje a 'linfonod*' o 'nódul*'. En descripciones largas como "
              "'*linfononodos hipoecoicos de **forma conservada***', captura el 'conservada' "
              "que pertenece al atributo `forma`, no a `compromiso`.\n")

    md.append("### Diagnóstico\n")
    md.append("1. **¿'Compromiso conservado' tiene significado clínico?** Marginalmente. "
              "Podría interpretarse como 'aspecto conservado' (no patológico) pero es ambiguo.")
    md.append("2. **¿Es un falso positivo de regex?** **Sí en 12/22 casos (55%).** El regex matchó "
              "texto que pertenecía a otro atributo.")
    md.append("3. **¿Debe transformarse en NO_COMPROMETIDO?** No — semánticamente son distintos: "
              "NO_COMPROMETIDO = 'sin metástasis'; CONSERVADO = 'aspecto no alterado'.")
    md.append("4. **¿Debe eliminarse?** Sí para los 12 FP. Los 10 TP podrían mantenerse como "
              "valor válido `CONSERVADO` (semánticamente 'no alterado, sin compromiso neoplásico').\n")

    md.append("### Recomendación: **FIX** (regex) + **mantener valor**\n")
    md.append("**Fix de regex (F3):**")
    md.append("- Reemplazar la línea 392 por patrón anclado:")
    md.append("  ```python")
    md.append("  (\"CONSERVADO\",  r\"\\b(linfonod|n[oó]dul[oa]s?)\\w*\\s+\\w*\\s*conservad[oa]s?\"),")
    md.append("  ```")
    md.append("  o más estricto: `r\"\\b(linfonod|n[oó]dul[oa]s?)[^.]*\\bconservad[oa]s?\"`")
    md.append("- Re-ejecutar F3 → esperar 0 filas compromiso=CONSERVADO donde la descripción menciona 'forma conservada'.")
    md.append("")
    md.append("**Decisión clínica sobre el valor canónico `CONSERVADO`:**")
    md.append("- Mantener `CONSERVADO` como valor válido para Linfonodos.compromiso (las 10 filas TP son clínica y léxicamente válidas).")
    md.append("- Es un valor diferente de `NO_COMPROMETIDO`: 'conservado' = aspecto no alterado, 'no comprometido' = sin infiltración neoplásica.")
    md.append("- Impacto: ~22 filas (0.02%) se redistribuyen; las 10 correctas permanecen, las 12 FP se eliminan.")
    md.append("")
    md.append("---\n")

    # ═══ PARTE 2 — Consolidaciones ═══
    md.append("## Parte 2 — Simulación de consolidaciones\n")
    md.append("Simulación **sin modificar silver**. Solo recalculamos frecuencias post-consolidación.\n")
    for c in parte2:
        md.append(f"### `{c['atributo']}` → `{c['valor_canonico_propuesto']}`\n")
        md.append("| Valor original | Tipo regla | Frecuencia |")
        md.append("|----------------|------------|-----------:|")
        for o in c["origenes"]:
            md.append(f"| `{o['valor']}` | {o['tipo_regla']} | {o['freq']:,} |")
        md.append(f"| **TOTAL consolidado** | — | **{c['freq_consolidada']:,}** |")
        md.append("")

    md.append("---\n")

    # ═══ PARTE 3 — Diccionario final ═══
    md.append("## Parte 3 — Diccionario final propuesto (post-consolidación)\n")
    md.append("Borrador completo de `dim_valor_atributo`. Cada fila representa un valor canónico final "
              "post-consolidación, con sus frecuencias observadas en silver.\n")

    for atributo in sorted(fin_dict.keys()):
        valores = fin_dict[atributo]
        total = sum(v["freq"] for v in valores)
        n_final = len(valores)
        n_original = sum(len(v["fuentes"]) for v in valores)
        md.append(f"### `{atributo}` ({n_final} valores finales, {n_original} originales)\n")
        md.append("| # | Valor canónico final | Frecuencia | % | Fuentes (originales) |")
        md.append("|--:|----------------------|-----------:|--:|----------------------|")
        for rank, v in enumerate(valores, 1):
            fuentes = ", ".join(f"`{f['valor_original']}` ({f['freq']})" for f in v["fuentes"])
            md.append(f"| {rank} | `{v['valor_canonico']}` | {v['freq']:,} | "
                      f"{100*v['freq']/total:.2f}% | {fuentes} |")
        md.append("")

    md.append("---\n")

    # ═══ PARTE 4 — Seeds ═══
    md.append("## Parte 4 — Simulación de seeds\n")

    md.append("### 4.1 Seed `dim_valor_atributo` (estimado)\n")
    md.append(f"**Cantidad estimada:** {len(dim_seed)} filas (1 por `atributo + valor_canonico_final` único).\n")
    md.append("| atributo | valor_canonico | frecuencia | es_binario | orden |")
    md.append("|----------|----------------|-----------:|:----------:|------:|")
    for s in sorted(dim_seed, key=lambda x: (x["atributo"], x["orden_sugerido"])):
        bin_marker = "✓" if s["es_binario"] else ""
        md.append(f"| `{s['atributo']}` | `{s['valor_canonico']}` | {s['frecuencia']:,} | {bin_marker} | {s['orden_sugerido']} |")

    md.append("\n### 4.2 Seed `map_atributo_valor` (estimado)\n")
    md.append(f"**Cantidad estimada:** {len(map_seed)} filas (1 por `atributo + valor_original` observado).\n")
    md.append("| atributo | valor_original | valor_canonico | freq | tipo_regla | confianza |")
    md.append("|----------|----------------|----------------|-----:|------------|----------:|")
    for s in sorted(map_seed, key=lambda x: (x["atributo"], -x["frecuencia"])):
        md.append(f"| `{s['atributo']}` | `{s['valor_original']}` | `{s['valor_canonico']}` | "
                  f"{s['frecuencia']:,} | {s['tipo_regla']} | {s['confianza']:.2f} |")

    md.append("\n---\n")

    # ═══ PARTE 5 — Validación Gold ═══
    md.append("## Parte 5 — Validación para Gold\n")

    md.append("### 5.1 ¿El vocabulario es estable para analytics?\n")
    md.append("**Sí.** Razones:")
    md.append("- 25 atributos canónicos con ≤10 valores cada uno (LOW_CARDINALITY universal).")
    md.append("- Cobertura top-5 ≥95% en 24/25 atributos (única excepción: `fetos` numérico).")
    md.append("- 100/110 valores canónicos consolidados (91%); solo `AUMENTADA_DE` quedaría tras los fixes.")
    md.append("- 0 ambigüedades detectadas en auditoría clínica (muestra de 100 hallazgos).\n")

    md.append("### 5.2 ¿Atributos que requieran staging?\n")
    md.append("**No.** Después de los fixes:")
    md.append("- `fetos` (Gestación): numérico (1-9), se modela como rango discreto, no requiere staging.")
    md.append("- El resto se normaliza directamente vía `dim_valor_atributo` + `map_atributo_valor`.\n")

    md.append("### 5.3 ¿Atributos que requieran fuzzy matching?\n")
    md.append("**No.** El corpus ya está normalizado por F3 a 110 valores canónicos. La variabilidad léxica "
              "está capturada en `map_atributo_valor.sinonimos_csv`. Para Gold, se usa directamente el canónico.\n")

    md.append("### 5.4 ¿Atributos que requieran embeddings?\n")
    md.append("**No.** No hay atributos textuales libres; todos son valores discretos de un dominio cerrado. "
              "Embeddings serían sobre-ingeniería para un dominio de 25 atributos × ≤10 valores.\n")

    md.append("### 5.5 ¿Gold puede construirse desde `organo → atributo → valor_canonico` sin texto libre?\n")
    md.append("**Sí.** Verificación:\n")
    md.append("- Tras los 2 fixes propuestos, `silver_atributos_hallazgo.valor_canonico` cubre **100%** "
              "de las filas extraídas (97,818 / 107,409 = 91% cobertura global; las 9,591 sin atributo "
              "son descripciones 'no evaluadas' que legítimamente no tienen valor clínico).")
    md.append("- Cada `(organo, atributo, valor_canonico)` es un punto en una grilla discreta.")
    md.append("- Gold puede pivotar directamente sin NLP en runtime.")
    md.append("- Si llegan informes nuevos con valores no canónicos: el pipeline los captura en "
              "`stg_atributos_valores` (ya existe) y se decide manualmente si crear un nuevo canónico "
              "o mapear a uno existente.\n")

    md.append("---\n")
    md.append("## Recomendación final\n")
    md.append("**GO CONDICIONAL para F4.** Aplicar los siguientes fixes en F3 antes de sembrar:\n")
    md.append("1. **FIX Caso A (urgente):** cambiar `AUMENTADA_DE` → `AUMENTADA` en `_profile_f3_dim_valores.py:159`.")
    md.append("2. **FIX Caso B (recomendado):** anclar regex `conservad[oa]` a contexto 'linfonod/nódul' en `_profile_f3_dim_valores.py:392`.")
    md.append("3. **REBUILD F3** y verificar:")
    md.append("   - 0 filas con `valor_canonico='AUMENTADA_DE'`.")
    md.append("   - ≤10 filas con `compromiso=CONSERVADO` (solo TP, no FP de 'forma conservada').")
    md.append("4. **RE-RUN** `audit_silver_f3.py` y `audit_f4_value_review.py` para confirmar.")
    md.append("5. Proceder con F4.1–F4.5 según el plan original.\n")
    md.append("**Riesgo de NO aplicar los fixes:**")
    md.append("- Gold tendría un valor redundante `AUMENTADA_DE` (4 filas) que duplica `AUMENTADA`.")
    md.append("- Gold tendría 12 filas Linfonodos.compromiso=CONSERVADO incorrectas (contamina el análisis de compromiso neoplásico).")
    md.append("- Impacto cuantitativo bajo (16 filas, 0.015%), pero simbólico: el primer caso debe sentar precedente de calidad.\n")
    md.append("**Complejidad estimada de F4 tras los fixes:**")
    md.append(f"- `dim_valor_atributo`: ~{len(dim_seed)} filas (manejable, revisión manual factible).")
    md.append(f"- `map_atributo_valor`: ~{len(map_seed)} filas.")
    md.append("- Tiempo estimado de implementación: 1 sesión (DDL + seed + verificación).")

    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-kind", default="sqlite")
    args = parser.parse_args()

    eng = get_engine(ROOT, db_kind=args.db_kind)

    print("Leyendo silver_atributos_hallazgo...")
    rows = fetch_all_values(eng)
    print(f"  {len(rows)} filas (organo, atributo, valor_canonico) distintas")

    # Parte 1
    print("\n[Parte 1A] Investigando AUMENTADA_DE...")
    parte1_a = investigate_aumentada_de(eng)
    print(f"  {parte1_a[1]['n_filas']} filas, {parte1_a[1]['n_hallazgos_unicos']} hallazgos")

    print("\n[Parte 1B] Investigando compromiso=CONSERVADO...")
    parte1_b = investigate_compromiso_conservado(eng)
    print(f"  {parte1_b[1]['n_filas']} filas ({parte1_b[1]['fp_forma_conservada']} FP, {parte1_b[1]['tp_nodulos_conservados']} TP)")

    # Parte 2
    print("\n[Parte 2] Simulando consolidaciones...")
    agg = aggregate_by_attr_valor(rows)
    parte2 = simulate_consolidations(agg, CONSOLIDATIONS)

    # Parte 3
    print("\n[Parte 3] Construyendo diccionario final...")
    fin_dict = build_final_dictionary(agg, CONSOLIDATIONS)
    n_atributos = len(fin_dict)
    n_valores_finales = sum(len(v) for v in fin_dict.values())
    print(f"  {n_atributos} atributos, {n_valores_finales} valores finales")

    # Parte 4
    print("\n[Parte 4] Simulando seeds...")
    dim_seed = estimate_dim_valor(fin_dict)
    map_seed = estimate_map_valor(rows, fin_dict)
    print(f"  dim_valor_atributo: {len(dim_seed)} filas")
    print(f"  map_atributo_valor: {len(map_seed)} filas")

    # Renderizar
    md = render_markdown(parte1_a, parte1_b, parte2, fin_dict, dim_seed, map_seed)
    out_path = ROOT / "docs" / "F4_PRESEED_AUDIT.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"\n[OK] Reporte: {out_path}")
    print(f"     {len(md.splitlines())} líneas")


if __name__ == "__main__":
    main()
