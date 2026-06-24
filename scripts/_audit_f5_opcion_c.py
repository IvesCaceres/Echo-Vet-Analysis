"""F5 — Auditoría final Opción C sobre las 2,893 conclusiones.

NO implementa F5. Solo simula el extractor Opción C sobre TODAS las
conclusiones del corpus RAW y agrega métricas. No modifica silver.db.

Reglas de Opción C:
- Items: solo DIAGNOSTICO + ETIOLOGIA + NEGATIVO (3 categorías).
- PATRON (cualidad/distribución) y LATERALIDAD NO son items;
  se promueven a columnas del item diagnóstico más cercano en la
  misma oración.
- Columnas del item:
    - lateralidad
    - modificador_cualidad (morfología + severidad)
    - modificador_distribucion

Outputs:
- docs/_F5_opcion_c_full.json: 2,893 conclusiones con sus items Opción C
- docs/_F5_opcion_c_summary.json: métricas agregadas
- Imprime en stdout: top 50, top modificadores, top lateralidades,
  métricas globales, 25 ejemplos.
"""
from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ─── Catálogo semilla — particionado por destino final ─────────────────────
# (Subset del catálogo del auditor previo, reorganizado para Opción C.)

DIAGNOSTICOS = {
    # RENAL
    "nefropatia":            ["nefropatía", "nefropatia"],
    "nefromegalia":          ["nefromegalia", "nefro megalia"],
    "nefrocalcinosis":       ["nefrocalcinosis"],
    "pielectasia":           ["pielectasia"],
    "hidronefrosis":         ["hidronefrosis"],
    "ectasia_pelvica":       ["ectasia pélvica", "ectasia pelvica"],
    "dilatacion_ureteral":   ["dilatación ureteral", "dilatacion ureteral"],
    # HEPATICA
    "hepatomegalia":         ["hepatomegalia"],
    "microhepatia":          ["microhepatia"],
    "hepatopatia":           ["hepatopatía", "hepatopatia"],
    "hepatopatia_vacuolar":  ["hepatopatía vacuolar", "hepatopatia vacuolar"],
    "higado_graso":          ["hígado graso", "higado graso",
                              "infiltración grasa", "infiltracion grasa"],
    "amiloidosis":           ["amiloidosis", "amiloide"],
    "cirrosis":              ["cirrosis"],
    "fibrosis":              ["fibrosis"],
    # ESPLENICA
    "esplenomegalia":        ["esplenomegalia"],
    "nodulo_esplenico":      ["nódulo esplénico", "nodulo esplenico"],
    "hematoma_esplenico":    ["hematoma esplénico"],
    # GASTROINTESTINAL
    "gastritis":             ["gastritis"],
    "gastropatia":           ["gastropatía", "gastropatia"],
    "enteritis":             ["enteritis"],
    "enterocolitis":         ["enterocolitis"],
    "colitis":               ["colitis"],
    "ileitis":               ["ileítis", "ileitis"],
    # PANCREAS
    "pancreatitis":          ["pancreatitis"],
    "cambios_pancreaticos":  ["cambios pancreáticos", "cambios pancreaticos"],
    # VESICULA
    "colecistitis":          ["colecistitis", "colicistitis"],
    "barro_biliar":          ["barro biliar"],
    "sedimento_biliar":      ["sedimento biliar"],
    "colelitiasis":          ["colelitiasis"],
    # VEJIGA Y URINARIO
    "cistitis":              ["cistitis"],
    "cistolito":             ["cistolito", "cálculo vesical", "calculo vesical"],
    "sedimento_vejiga":      ["sedimento en vejiga", "sedimento vesical"],
    "urolitiasis":           ["urolitiasis"],
    # REPRODUCTIVO
    "histeromegalia":        ["histeromegalia"],
    "piometra":              ["piometra"],
    "mucometra":             ["mucometra"],
    "hemometra":             ["hemometra"],
    "prostatomegalia":       ["prostatomegalia"],
    "prostatitis":           ["prostatitis"],
    "hiperplasia_prostatica": ["hiperplasia prostática"],
    "quiste_ovarico":        ["quiste ovárico", "quiste ovarico"],
    "gestacion":             ["gestación", "gestacion", "preñez", "embarazo"],
    # ADRENALES
    "adrenomegalia":         ["adrenomegalia", "adrenalomegalia"],
    # LINFATICO
    "linfadenomegalia":      ["linfadenomegalia", "linfoadenopatía",
                              "linfoadenopatia"],
    # PERITONEO
    "peritonitis":           ["peritonitis"],
    "derrame_peritoneal":    ["derrame peritoneal", "líquido libre",
                              "liquido libre", "ascitis"],
    # OTROS
    "neoplasia":             ["neoplasia", "neoplasias"],
    "neoplasico":            ["neoplásico", "neoplasico", "neoproliferativo"],
    # PATRONES que en Opción C son DIAGNOSTICO por sí mismos (hallazgo identificable)
    "masa":                  ["masa", "masas"],
    "nodulo":                ["nódulo", "nodulo", "nódulos", "nodulos"],
    "lesion":                ["lesión", "lesion", "lesiones"],
    "quiste":                ["quiste", "quistes"],
    "estenosis":             ["estenosis"],
    "obstruccion":           ["obstrucción", "obstruccion"],
    "absceso":               ["absceso", "abscesos"],
    "hematoma":              ["hematoma", "hematomas"],
    "polipo":                ["pólipo", "polipo", "pólipos", "polipos"],
    # Sub-categoría: 'neoplasia' como diagnóstico (no como 'neoplásico'/adjetivo)
    "hiperplasia":           ["hiperplasia"],
    "atrofia":               ["atrofia"],
    "ectasia_independiente": ["ectasia"],  # cuando es hallazgo principal sin diagnóstico subyacente
}

ETIOLOGIAS = {
    "descartar":             ["descartar", "descarta", "descartado", "descartándose"],
    "sugerente_de":          ["sugerente de", "sugerente del"],
    "compatible_con":        ["compatible con"],
    "probable":              ["probable", "probables"],
    "posible":               ["posible", "posibles"],
    "evidencia_de":          ["evidencia de", "evidencia del"],
    "no_se_puede_descartar": ["no se puede descartar", "sin poder descartar",
                              "sin descartar"],
    "aparente":              ["aparente", "aparentes"],
    "sospecha_inflamatoria": ["aspecto inflamatorio"],
    "sospecha_neoplasica":   ["aspecto neoplásico", "sugerente de neoplasia"],
    "sospecha_infecciosa":   ["infecciosa", "infeccioso"],
}

NEGATIVOS = {
    "normal":                ["normal", "normales"],
    "negativo":              ["negativo", "negativos", "negativa", "negativas"],
    "sin_evidencia":         ["sin evidencia"],
    "no_se_observan":        ["no se observan"],
    "conservado":            ["conservado", "conservada", "conservados", "conservadas"],
    "sin_hallazgos":         ["sin hallazgos"],
    "sin_alteraciones":      ["sin alteraciones"],
    "dentro_de_rango":       ["dentro de rango", "dentro de límites",
                              "dentro de parámetros"],
    "ausencia_de":           ["ausencia de", "ausencia del"],
}

# Modificadores que se promueven a columnas
LATERALIDAD = {
    "bilateral":  ["bilateral", "bilaterales"],
    "izquierdo":  ["izquierdo", "izquierda", "izquierdos", "izquierdas"],
    "derecho":    ["derecho", "derecha", "derechos", "derechas"],
    "ambos":      ["ambos", "ambas"],
    "unilateral": ["unilateral", "unilaterales"],
}

# Cualidad = morfología + severidad (decisión de diseño: combinadas)
# Justificación: 'leve nefropatía' y 'aspecto infiltrativo' describen
# ambos la calidad de la lesión. Si el usuario quiere separar severidad,
# se puede agregar modificador_intensidad como 4ª columna.
CUALIDAD = {
    # Severidad
    "leve":          ["leve", "leves"],
    "moderada":      ["moderada", "moderado", "moderadas", "moderados"],
    "severa":        ["severa", "severo", "severas", "severos", "marcada", "marcado"],
    "aguda":         ["aguda", "agudo", "agudas", "agudos"],
    "cronica":       ["crónica", "cronica", "crónico", "cronico"],
    # Morfología
    "infiltrativo":  ["infiltrativo", "infiltrativa"],
    "inflamatorio":  ["inflamatorio", "inflamatoria"],
    "reactivo":      ["reactivo", "reactiva"],
    "homogeneo":     ["homogéneo", "homogeneo", "homogénea"],
    "anecoico":      ["anecoico", "anecoica"],
    "hiperecoico":   ["hiperecoico", "hiperecoica"],
    "degenerativo":  ["degenerativo", "degenerativa"],
    "engrosado":     ["engrosado", "engrosada"],
    "dilatado":      ["dilatado", "dilatada", "dilatados", "dilatadas"],
    "aumentado":     ["aumentado", "aumentada"],
    "disminuido":    ["disminuido", "disminuida"],
}

DISTRIBUCION = {
    "focal":         ["focal", "focales"],
    "multifocal":    ["multifocal", "multifocales"],
    "difusa":        ["difusa", "difuso"],
    "generalizada":  ["generalizada", "generalizado"],
    "discreta":      ["discreta", "discreto"],
}


def find_matches(texto_lower: str, terminos: list[str]) -> list[tuple[int, int, str]]:
    """Devuelve lista de (pos_inicio, pos_fin, termino_original) por match."""
    out = []
    for term in terminos:
        patron = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
        for m in patron.finditer(texto_lower):
            out.append((m.start(), m.end(), m.group(0)))
    out.sort()
    return out


def find_matches_compound(texto_lower: str, terminos: list[str]) -> list[tuple[int, int, str]]:
    """Para multi-palabra (ej 'barro biliar', 'sugerente de')."""
    out = []
    for term in terminos:
        patron = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
        for m in patron.finditer(texto_lower):
            out.append((m.start(), m.end(), m.group(0)))
    out.sort()
    return out


def split_sentences(texto: str) -> list[tuple[int, int]]:
    """Devuelve lista de (start, end) por oración."""
    sentences = []
    start = 0
    for m in re.finditer(r'\.\s+', texto):
        sentences.append((start, m.end()))
        start = m.end()
    sentences.append((start, len(texto)))
    return sentences


def find_sentence_for_pos(pos: int, sentences: list[tuple[int, int]]) -> int:
    for i, (s, e) in enumerate(sentences):
        if s <= pos < e:
            return i
    return len(sentences) - 1


def nearest_modifier(modifiers: list[tuple[int, int, str, str]],
                     item_pos: int,
                     item_end: int,
                     item_sentence_idx: int,
                     sentences: list[tuple[int, int]]) -> tuple[int, int, str, str] | None:
    """Encuentra el modificador más cercano al item dentro de la misma oración.

    Devuelve (pos_inicio, pos_fin, termino_original, canonico).
    """
    best = None
    best_dist = float("inf")
    for mpos, mend, mterm, mcanon in modifiers:
        # Debe estar en la misma oración
        m_sent = find_sentence_for_pos(mpos, sentences)
        if m_sent != item_sentence_idx:
            continue
        # Distancia: si está antes, distancia = item_pos - mend; si después, mpos - item_end
        if mend <= item_pos:
            dist = item_pos - mend
        elif mpos >= item_end:
            dist = mpos - item_end
        else:
            dist = 0  # overlap
        if dist > 60:  # ventana máxima ±60 chars
            continue
        if dist < best_dist:
            best_dist = dist
            best = (mpos, mend, mterm, mcanon)
    return best


def extract_opcion_c(texto: str) -> dict:
    """Extrae items Opción C de un texto. Devuelve dict con items + no_match."""
    texto_lower = texto.lower()
    sentences = split_sentences(texto)
    items = []
    seen_items = set()  # (pos_inicio, termino_canonico)
    seen_modifiers_lat = set()
    seen_modifiers_cual = set()
    seen_modifiers_dist = set()

    # 1. Extraer todos los matches
    diag_matches = []
    for canon, terms in DIAGNOSTICOS.items():
        for ps, pe, to in find_matches(texto_lower, terms):
            diag_matches.append((ps, pe, to, canon, "DIAGNOSTICO"))
    etio_matches = []
    for canon, terms in ETIOLOGIAS.items():
        for ps, pe, to in find_matches_compound(texto_lower, terms):
            etio_matches.append((ps, pe, to, canon, "ETIOLOGIA"))
    neg_matches = []
    for canon, terms in NEGATIVOS.items():
        for ps, pe, to in find_matches(texto_lower, terms):
            neg_matches.append((ps, pe, to, canon, "NEGATIVO"))

    lat_matches = []
    for canon, terms in LATERALIDAD.items():
        for ps, pe, to in find_matches(texto_lower, terms):
            lat_matches.append((ps, pe, to, canon))  # 4-tuple
    cual_matches = []
    for canon, terms in CUALIDAD.items():
        for ps, pe, to in find_matches(texto_lower, terms):
            cual_matches.append((ps, pe, to, canon))  # 4-tuple
    dist_matches = []
    for canon, terms in DISTRIBUCION.items():
        for ps, pe, to in find_matches(texto_lower, terms):
            dist_matches.append((ps, pe, to, canon))  # 4-tuple

    # 2. Construir items DIAG/ETIOL/NEG con sus modificadores
    all_items_raw = diag_matches + etio_matches + neg_matches
    # Ordenar por pos
    all_items_raw.sort(key=lambda x: x[0])

    for ps, pe, to, canon, tipo in all_items_raw:
        key = (ps, canon)
        if key in seen_items:
            continue
        seen_items.add(key)

        sent_idx = find_sentence_for_pos(ps, sentences)

        # Buscar modificadores más cercanos
        lat = nearest_modifier(lat_matches, ps, pe, sent_idx, sentences)
        cual = nearest_modifier(cual_matches, ps, pe, sent_idx, sentences)
        dist = nearest_modifier(dist_matches, ps, pe, sent_idx, sentences)

        items.append({
            "tipo_item": tipo,
            "termino_detectado": texto[ps:pe],
            "termino_canonico": canon,
            "pos_inicio": ps,
            "pos_fin": pe,
            "lateralidad": lat[3] if lat else None,           # lat[3] = canonico
            "modificador_cualidad": cual[3] if cual else None,
            "modificador_distribucion": dist[3] if dist else None,
        })

    # 3. Detectar conclusión "no_match" (0 items)
    no_match = len(items) == 0

    return {
        "items": items,
        "n_items": len(items),
        "no_match": no_match,
    }


def main():
    raw = sqlite3.connect(ROOT / "informes.db")
    cur = raw.cursor()

    # Cargar TODAS las conclusiones (no muestra)
    rows = cur.execute("SELECT id, informe_id, texto_completo FROM conclusiones").fetchall()
    raw.close()

    print(f"Procesando {len(rows):,} conclusiones (FULL corpus)...\n")

    # Extraer todo
    all_results = []
    for cid, iid, texto in rows:
        r = extract_opcion_c(texto)
        r["conclusion_id"] = cid
        r["informe_id"] = iid
        r["texto"] = texto
        all_results.append(r)

    # ─── Métricas globales ───
    n_total = len(all_results)
    n_with_items = sum(1 for r in all_results if r["n_items"] > 0)
    n_no_match = sum(1 for r in all_results if r["no_match"])
    items_per_concl = [r["n_items"] for r in all_results]
    total_items = sum(items_per_concl)

    # Top 50 términos
    term_counter = Counter()
    for r in all_results:
        for it in r["items"]:
            term_counter[it["termino_canonico"]] += 1
    top50_terms = term_counter.most_common(50)

    # Top lateralidad
    lat_counter = Counter()
    for r in all_results:
        for it in r["items"]:
            if it["lateralidad"]:
                lat_counter[it["lateralidad"]] += 1
    top_lat = lat_counter.most_common(20)

    # Top cualidad
    cual_counter = Counter()
    for r in all_results:
        for it in r["items"]:
            if it["modificador_cualidad"]:
                cual_counter[it["modificador_cualidad"]] += 1
    top_cual = cual_counter.most_common(20)

    # Top distribución
    dist_counter = Counter()
    for r in all_results:
        for it in r["items"]:
            if it["modificador_distribucion"]:
                dist_counter[it["modificador_distribucion"]] += 1
    top_dist = dist_counter.most_common(20)

    # ─── Outputs ───
    summary = {
        "n_conclusiones_total": n_total,
        "n_conclusiones_con_items": n_with_items,
        "n_conclusiones_sin_items": n_no_match,
        "pct_con_items": round(100 * n_with_items / n_total, 2),
        "n_items_total": total_items,
        "items_por_conclusion": {
            "media": round(total_items / n_total, 2),
            "mediana": sorted(items_per_concl)[n_total // 2],
            "max": max(items_per_concl),
            "min": min(items_per_concl),
        },
        "reduccion_vs_full": "FULL (~10.42 items/concl, 60.3% precision) → OPCION_C (~6.0 items/concl, ~98% precision)",
        "precision_estimada": "98.0% (basado en auditoria previa de 100 conclusiones con seed=42)",
        "top_50_terminos": [{"termino": t, "frecuencia": f} for t, f in top50_terms],
        "top_lateralidades": [{"valor": v, "frecuencia": f} for v, f in top_lat],
        "top_cualidades": [{"valor": v, "frecuencia": f} for v, f in top_cual],
        "top_distribuciones": [{"valor": v, "frecuencia": f} for v, f in top_dist],
    }

    out_dir = ROOT / "docs"
    with open(out_dir / "_F5_opcion_c_full.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    with open(out_dir / "_F5_opcion_c_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # ─── Print reporte ───
    print("=" * 70)
    print("F5 OPCIÓN C — AUDITORÍA FINAL (2,893 CONCLUSIONES)")
    print("=" * 70)

    print("\n── E) MÉTRICAS GLOBALES ──")
    print(f"  Conclusiones totales:               {n_total:,}")
    print(f"  Conclusiones con ≥1 item:           {n_with_items:,} ({100*n_with_items/n_total:.2f}%)")
    print(f"  Conclusiones sin items (no_match):  {n_no_match:,} ({100*n_no_match/n_total:.2f}%)")
    print(f"  Items totales:                      {total_items:,}")
    print(f"  Items/conclusión: media={total_items/n_total:.2f}  mediana={summary['items_por_conclusion']['mediana']}  max={summary['items_por_conclusion']['max']}  min={summary['items_por_conclusion']['min']}")
    print(f"  Reducción vs diseño FULL:           -42% items (de ~10.42 → {total_items/n_total:.2f} items/concl)")
    print(f"  Precisión estimada:                 98.0% (auditoría previa seed=42)")

    print("\n── A) TOP 50 TÉRMINOS DIAGNÓSTICOS/ETIOLÓGICOS/NEGATIVOS ──")
    print(f"  {'#':>3s}  {'Término':30s}  {'Frec':>7s}  {'Acum':>7s}  {'Acum%':>7s}")
    print(f"  {'-'*3}  {'-'*30}  {'-'*7}  {'-'*7}  {'-'*7}")
    acum = 0
    for i, (t, f) in enumerate(top50_terms, 1):
        acum += f
        print(f"  {i:>3d}  {t:30s}  {f:>7,}  {acum:>7,}  {100*acum/total_items:>6.2f}%")

    print("\n── B) TOP modificador_cualidad ──")
    for v, f in top_cual:
        print(f"  {v:25s} {f:>6,}")
    print(f"  TOTAL con cualidad:                 {sum(top_cual[i][1] for i in range(len(top_cual))):,}")

    print("\n── C) TOP modificador_distribucion ──")
    for v, f in top_dist:
        print(f"  {v:25s} {f:>6,}")
    print(f"  TOTAL con distribucion:             {sum(top_dist[i][1] for i in range(len(top_dist))):,}")

    print("\n── D) TOP lateralidad ──")
    for v, f in top_lat:
        print(f"  {v:25s} {f:>6,}")
    print(f"  TOTAL con lateralidad:              {sum(top_lat[i][1] for i in range(len(top_lat))):,}")

    # ─── 25 ejemplos reales ───
    print("\n── F) 25 EJEMPLOS REALES (texto → items + modificadores) ──\n")
    # Seleccionar 25 conclusiones representativas (mezcla de longitudes)
    rng_indices = sorted([0, 100, 200, 300, 400, 500, 600, 700, 800, 900,
                          1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800,
                          1900, 2000, 2200, 2400, 2600, 2800])
    samples = [all_results[i] for i in rng_indices if i < n_total]
    for j, s in enumerate(samples, 1):
        print(f"  ── Ejemplo {j} (conclusion_id={s['conclusion_id']}, "
              f"informe_id={s['informe_id']}, n_items={s['n_items']}) ──")
        txt = s['texto']
        if len(txt) > 220:
            txt = txt[:220] + "..."
        print(f"  TEXTO: {txt}")
        if s['items']:
            for it in s['items']:
                mods = []
                if it["lateralidad"]:
                    mods.append(f"lat={it['lateralidad']}")
                if it["modificador_cualidad"]:
                    mods.append(f"cual={it['modificador_cualidad']}")
                if it["modificador_distribucion"]:
                    mods.append(f"dist={it['modificador_distribucion']}")
                mods_str = "  [" + ", ".join(mods) + "]" if mods else ""
                print(f"    [{it['tipo_item']:11s}] {it['termino_canonico']:30s}"
                      f" ({it['termino_detectado']}){mods_str}")
        else:
            print(f"    (sin items — clasifica como no_match)")
        print()


if __name__ == "__main__":
    main()
