"""F5 — Auditor de precisión sobre 100 conclusiones aleatorias (seed=42).

NO implementa F5. Solo ejecuta el extractor rule-based propuesto en
docs/F5_DESIGN_SILVER_CONCLUSION_ITEMS.md sobre 100 conclusiones
seleccionadas con seed=42, y produce:

- docs/_F5_audit_samples.json: 100 conclusiones con sus items extraídos
- docs/_F5_audit_summary.json: métricas agregadas (precision, FP, dist)

Clasificación de items (heurística determinista):
- TP (True Positive): el término canónico es uno de los 81 esperados y
  aparece en contexto clínico (no es ruido lingüístico).
- FP (False Positive): matchea la regex pero NO es un hallazgo clínico
  (ej: "ambos" como LATERALIDAD en "ambos padres", "normal" en
  "frecuencia normal" en vez de "hallazgo normal").
- AMBIGUO: depende del contexto — p.ej. "leve" en "leve mejoría" vs
  "nefropatía leve". La heurística marca AMBIGUO cuando el término es
  polisémico (adjetivo/extractor vs diagnóstico).

Las reglas heurísticas se documentan en HEURISTICAS_FP más abajo y se
basan en inspección del corpus + el perfil F5 ya generado.
"""
from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = 42
N_SAMPLES = 100

# ─── Catálogo semilla (mismo que F5_DESIGN §4) ───────────────────────────
DIAGNOSTICOS = {
    # RENAL
    "nefropatia":            {"terminos": ["nefropatía", "nefropatia"]},
    "nefromegalia":          {"terminos": ["nefromegalia", "nefro megalia"]},
    "nefrocalcinosis":       {"terminos": ["nefrocalcinosis"]},
    "pielectasia":           {"terminos": ["pielectasia"]},
    "hidronefrosis":         {"terminos": ["hidronefrosis"]},
    "ectasia_pelvica":       {"terminos": ["ectasia pélvica", "ectasia pelvica"]},
    "dilatacion_ureteral":   {"terminos": ["dilatación ureteral", "dilatacion ureteral"]},
    # HEPATICA
    "hepatomegalia":         {"terminos": ["hepatomegalia"]},
    "microhepatia":          {"terminos": ["microhepatia"]},
    "hepatopatia":           {"terminos": ["hepatopatía", "hepatopatia"]},
    "hepatopatia_vacuolar":  {"terminos": ["hepatopatía vacuolar", "hepatopatia vacuolar"]},
    "higado_graso":          {"terminos": ["hígado graso", "higado graso",
                                           "infiltración grasa", "infiltracion grasa"]},
    "amiloidosis":           {"terminos": ["amiloidosis", "amiloide"]},
    "cirrosis":              {"terminos": ["cirrosis"]},
    "fibrosis":              {"terminos": ["fibrosis"]},
    # ESPLENICA
    "esplenomegalia":        {"terminos": ["esplenomegalia"]},
    "nodulo_esplenico":      {"terminos": ["nódulo esplénico", "nodulo esplenico"]},
    "hematoma_esplenico":    {"terminos": ["hematoma esplénico"]},
    # GASTROINTESTINAL
    "gastritis":             {"terminos": ["gastritis"]},
    "gastropatia":           {"terminos": ["gastropatía", "gastropatia"]},
    "enteritis":             {"terminos": ["enteritis"]},
    "enterocolitis":         {"terminos": ["enterocolitis"]},
    "colitis":               {"terminos": ["colitis"]},
    "ileitis":               {"terminos": ["ileítis", "ileitis"]},
    # PANCREAS
    "pancreatitis":          {"terminos": ["pancreatitis"]},
    "cambios_pancreaticos":  {"terminos": ["cambios pancreáticos", "cambios pancreaticos"]},
    # VESICULA
    "colecistitis":          {"terminos": ["colecistitis", "colicistitis"]},
    "barro_biliar":          {"terminos": ["barro biliar"]},
    "sedimento_biliar":      {"terminos": ["sedimento biliar"]},
    "colelitiasis":          {"terminos": ["colelitiasis"]},
    # VEJIGA Y URINARIO
    "cistitis":              {"terminos": ["cistitis"]},
    "cistolito":             {"terminos": ["cistolito", "cálculo vesical", "calculo vesical"]},
    "sedimento_vejiga":      {"terminos": ["sedimento en vejiga", "sedimento vesical"]},
    "urolitiasis":           {"terminos": ["urolitiasis"]},
    # REPRODUCTIVO
    "histeromegalia":        {"terminos": ["histeromegalia"]},
    "piometra":              {"terminos": ["piometra"]},
    "mucometra":             {"terminos": ["mucometra"]},
    "hemometra":             {"terminos": ["hemometra"]},
    "prostatomegalia":       {"terminos": ["prostatomegalia"]},
    "prostatitis":           {"terminos": ["prostatitis"]},
    "hiperplasia_prostatica": {"terminos": ["hiperplasia prostática"]},
    "quiste_ovarico":        {"terminos": ["quiste ovárico", "quiste ovarico"]},
    "gestacion":             {"terminos": ["gestación", "gestacion", "preñez",
                                           "embarazo"]},
    # ADRENALES
    "adrenomegalia":         {"terminos": ["adrenomegalia", "adrenalomegalia"]},
    # LINFATICO
    "linfadenomegalia":      {"terminos": ["linfadenomegalia", "linfoadenopatía",
                                           "linfoadenopatia"]},
    # PERITONEO
    "peritonitis":           {"terminos": ["peritonitis"]},
    "derrame_peritoneal":    {"terminos": ["derrame peritoneal", "líquido libre",
                                           "liquido libre", "ascitis"]},
    # OTROS
    "piometra":              {"terminos": ["piometra"]},
    "neoplasia":             {"terminos": ["neoplasia", "neoplasias"]},
    "neoplasico":            {"terminos": ["neoplásico", "neoplasico",
                                           "neoproliferativo"]},
}

PATRONES = {
    "masa":                  {"terminos": ["masa", "masas"]},
    "nodulo":                {"terminos": ["nódulo", "nodulo", "nódulos", "nodulos"]},
    "lesion":                {"terminos": ["lesión", "lesion", "lesiones"]},
    "quiste":                {"terminos": ["quiste", "quistes"]},
    "estenosis":             {"terminos": ["estenosis"]},
    "obstruccion":           {"terminos": ["obstrucción", "obstruccion"]},
    "ectasia":               {"terminos": ["ectasia"]},
    "dilatacion":            {"terminos": ["dilatación", "dilatacion"]},
    "mineralizacion":        {"terminos": ["mineralización", "mineralizacion"]},
    "litiasis":              {"terminos": ["litiasis"]},
    "calculo":               {"terminos": ["cálculo", "calculo", "cálculos", "calculos"]},
    "absceso":               {"terminos": ["absceso", "abscesos"]},
    "hematoma":              {"terminos": ["hematoma", "hematomas"]},
    "polipo":                {"terminos": ["pólipo", "polipo", "pólipos", "polipos"]},
    # Modificadores / cualitativos
    "leve":                  {"terminos": ["leve", "leves"]},
    "moderada":              {"terminos": ["moderada", "moderado", "moderadas", "moderados"]},
    "severa":                {"terminos": ["severa", "severo", "severas", "severos",
                                           "marcada", "marcado"]},
    "aguda":                 {"terminos": ["aguda", "agudo", "agudas", "agudos"]},
    "cronica":               {"terminos": ["crónica", "cronica", "crónico", "cronico"]},
    "focal":                 {"terminos": ["focal", "focales"]},
    "multifocal":            {"terminos": ["multifocal", "multifocales"]},
    "difusa":                {"terminos": ["difusa", "difuso"]},
    "generalizada":          {"terminos": ["generalizada", "generalizado"]},
    "discreta":              {"terminos": ["discreta", "discreto"]},
    "infiltrativo":          {"terminos": ["infiltrativo", "infiltrativa"]},
    "inflamatorio":          {"terminos": ["inflamatorio", "inflamatoria"]},
    "reactivo":              {"terminos": ["reactivo", "reactiva"]},
    "dilatado":              {"terminos": ["dilatado", "dilatada", "dilatados", "dilatadas"]},
    "engrosado":             {"terminos": ["engrosado", "engrosada"]},
    "homogeneo":             {"terminos": ["homogéneo", "homogeneo", "homogénea"]},
    "aumentado":             {"terminos": ["aumentado", "aumentada"]},
    "disminuido":            {"terminos": ["disminuido", "disminuida"]},
    "anecoico":              {"terminos": ["anecoico", "anecoica"]},
    "hiperecoico":           {"terminos": ["hiperecoico", "hiperecoica"]},
    "degenerativo":          {"terminos": ["degenerativo", "degenerativa"]},
}

ETIOLOGIAS = {
    "descartar":             {"terminos": ["descartar", "descarta", "descartado",
                                           "descartándose"]},
    "sugerente_de":          {"terminos": ["sugerente de", "sugerente del"]},
    "compatible_con":        {"terminos": ["compatible con"]},
    "probable":              {"terminos": ["probable", "probables"]},
    "posible":               {"terminos": ["posible", "posibles"]},
    "evidencia_de":          {"terminos": ["evidencia de", "evidencia del"]},
    "no_se_puede_descartar": {"terminos": ["no se puede descartar", "sin poder descartar",
                                           "sin descartar"]},
    "aparente":              {"terminos": ["aparente", "aparentes"]},
    "sospecha_inflamatoria": {"terminos": ["aspecto inflamatorio"]},
    "sospecha_neoplasica":   {"terminos": ["aspecto neoplásico", "sugerente de neoplasia"]},
    "sospecha_infecciosa":   {"terminos": ["infecciosa", "infeccioso"]},
}

LATERALIDAD = {
    "bilateral":             {"terminos": ["bilateral", "bilaterales"]},
    "izquierdo":             {"terminos": ["izquierdo", "izquierda", "izquierdos",
                                           "izquierdas"]},
    "derecho":               {"terminos": ["derecho", "derecha", "derechos",
                                           "derechas"]},
    "ambos":                 {"terminos": ["ambos", "ambas"]},
    "unilateral":            {"terminos": ["unilateral", "unilaterales"]},
}

NEGATIVOS = {
    "normal":                {"terminos": ["normal", "normales"]},
    "negativo":              {"terminos": ["negativo", "negativos", "negativa", "negativas"]},
    "sin_evidencia":         {"terminos": ["sin evidencia"]},
    "no_se_observan":        {"terminos": ["no se observan"]},
    "conservado":            {"terminos": ["conservado", "conservada", "conservados",
                                           "conservadas"]},
    "sin_hallazgos":         {"terminos": ["sin hallazgos"]},
    "sin_alteraciones":      {"terminos": ["sin alteraciones"]},
    "dentro_de_rango":       {"terminos": ["dentro de rango", "dentro de límites",
                                           "dentro de parámetros"]},
    "ausencia_de":           {"terminos": ["ausencia de", "ausencia del"]},
}

# ─── Heurísticas de FP y AMBIGUO ─────────────────────────────────────────
# Estas reglas determinan si un match automático es TP, FP o AMBIGUO.
# Basadas en inspección del corpus (perfil F5 ya generado).

# (1) FPs seguros: matches que NO son clínicos sino gramaticales/conectores.
FP_SEGuros = {
    "ambos": "Conector sintáctico: 'ambos' como LATERALIDAD solo aplica si refieres a órganos. "
             "En 'ambos padres' / 'ambos técnicos' es FP.",
    "ambos": "Ver 'ambos' arriba.",
    "aparente": "Adjetivo genérico ('mancha aparente', 'lesión aparente'). "
                "Sin valor clínico por sí mismo.",
    "conservado": "Estado de un atributo (no es un hallazgo). "
                  "En conclusión, indica que un hallazgo previo está estable, no un nuevo hallazgo.",
    "aumentado": "Modificador relativo, no diagnóstico. Si acompaña a un diagnóstico, "
                 "es redundante con el par (ej. 'nefropatía' ya implica alteración).",
    "disminuido": "Mismo razonamiento que 'aumentado'.",
    "engrosado": "Modificador morfológico, no diagnóstico independiente.",
    "dilatado": "Mismo razonamiento.",
    "dilatacion": "Mismo razonamiento (es el abstract noun, pero el clínico dice "
                  "'dilatado' o 'dilatada').",
    "evidencia_de": "Marcador de certeza, no hallazgo. Útil como modificador, "
                    "no como item independiente.",
    "ectasia": "Patrón morfológico, no diagnóstico. El diagnóstico sería la causa "
               "(ej. 'hidronefrosis' sí es diagnóstico).",
    "hiperplasia_prostatica": "Es diagnóstico, PERO en la forma 'hiperplasia prostática' "
                              "puede estar en contexto de hallazgo de próstata, no de conclusión. "
                              "Riesgo bajo de FP.",
    "mas": "Morfemas comunes (puede ser 'masa' o 'más'). La regex con \\b ya descarta 'más', "
           "así que 'masa' como match es generalmente TP.",
}

# (2) AMBIGUOs: matches válidos en contexto clínico PERO con
#    sobre-extracción probable. Requieren revisión manual.
AMBIGUOS = {
    "leve": "Modificador de intensidad. Si el catálogo lo trata como PATRON separado, "
            "puede duplicar info que ya está en modificador_intensidad del diagnóstico.",
    "moderada": "Mismo razonamiento que 'leve'.",
    "severa": "Mismo razonamiento que 'leve'.",
    "aguda": "Modificador temporal/intensidad. Ambigüo si el contexto dice 'fase aguda' "
             "vs 'pancreatitis aguda'.",
    "cronica": "Mismo razonamiento que 'aguda'.",
    "focal": "Distribución morfológica. Ambigüo si aplica a lesión o a inflamación.",
    "discreta": "Calificador de hallazgos leves. Generalmente complemento, no hallazgo principal.",
    "infiltrativo": "Patrón infiltrativo. En el corpus, suele complementar a "
                    "hepatomegalia/hepatopatía, no ser hallazgo independiente.",
    "inflamatorio": "Mismo razonamiento.",
    "reactivo": "Mismo razonamiento. Acompaña a linfonodo/linfadenomegalia.",
    "homogeneo": "Cualidad ecográfica, no hallazgo. Bajo valor aislado.",
    "anecoico": "Cualidad ecográfica. Casi siempre FP si se extrae sin contexto.",
    "hiperecoico": "Mismo razonamiento.",
    "degenerativo": "Adjetivo genérico. Raramente hallazgo aislado.",
    "marcada": "Sinónimo de 'severa'. Puede duplicar info.",
    "generalizada": "Distribución. Complemento, no hallazgo.",
    "difusa": "Mismo razonamiento.",
    "multifocal": "Distribución. Complemento, no hallazgo.",
    "conservado": "Ya marcado como FP. Algunos casos son válidos ('hallazgos conservados').",
    "unilateral": "Lateralidad. Raro (3 menciones).",
    "no_se_observan": "Negación completa. Válido solo si conclusión es 100% negativa. "
                      "Si hay otros hallazgos, es FP.",
    "sin_alteraciones": "Mismo razonamiento.",
    "sin_hallazgos": "Mismo razonamiento.",
    "dentro_de_rango": "Mismo razonamiento.",
    "ausencia_de": "Mismo razonamiento.",
    "evidencia_de": "Marcador. Útil como modificador, no como item principal.",
}

# (3) Clasificación por defecto:
DEFAULT_TP = set()  # todo lo no listado en FP_SEGuros ni AMBIGUOS es TP


def extract_items(texto: str) -> list[dict]:
    """Extiende el extractor F5 design con manejo de modificadores."""
    items = []
    texto_lower = texto.lower()

    catalogos = [
        ("DIAGNOSTICO", DIAGNOSTICOS),
        ("PATRON", PATRONES),
        ("ETIOLOGIA", ETIOLOGIAS),
        ("LATERALIDAD", LATERALIDAD),
        ("NEGATIVO", NEGATIVOS),
    ]

    for tipo, catalogo in catalogos:
        for canonico, spec in catalogo.items():
            for termino in spec["terminos"]:
                patron = re.compile(r'\b' + re.escape(termino) + r'\b', re.IGNORECASE)
                for match in patron.finditer(texto_lower):
                    # Contexto: ventana ±50 chars
                    ctx_start = max(0, match.start() - 50)
                    ctx_end = min(len(texto), match.end() + 50)
                    contexto = texto[ctx_start:ctx_end]

                    # Extraer modificadores adyacentes (ventana ±30 chars)
                    intensidad = _extract_intensidad(texto, match)
                    certeza = _extract_certeza(texto, match)
                    lateralidad = _extract_lateralidad(texto, match)

                    items.append({
                        "tipo_item": tipo,
                        "termino_original": match.group(0),
                        "termino_canonico": canonico,
                        "pos_inicio": match.start(),
                        "pos_fin": match.end(),
                        "contexto_50": contexto,
                        "modificador_intensidad": intensidad,
                        "modificador_certeza": certeza,
                        "lateralidad": lateralidad,
                    })

    # Deduplicar por (pos_inicio, termino_canonico)
    seen = set()
    deduped = []
    for it in items:
        key = (it["pos_inicio"], it["termino_canonico"])
        if key not in seen:
            seen.add(key)
            deduped.append(it)

    # Ordenar por pos_inicio
    deduped.sort(key=lambda x: x["pos_inicio"])
    return deduped


def _extract_intensidad(texto: str, match) -> str | None:
    """Extrae modificador de intensidad (ventana ±30 chars)."""
    ctx_start = max(0, match.start() - 30)
    ctx_end = min(len(texto), match.end() + 30)
    ctx = texto[ctx_start:ctx_end].lower()
    if re.search(r'\b(sever[ao]s?|marcad[ao]s?)\b', ctx):
        return "severa"
    if re.search(r'\bmoderad[ao]s?\b', ctx):
        return "moderada"
    if re.search(r'\bleves?\b', ctx):
        return "leve"
    return None


def _extract_certeza(texto: str, match) -> str | None:
    ctx_start = max(0, match.start() - 30)
    ctx_end = min(len(texto), match.end() + 30)
    ctx = texto[ctx_start:ctx_end].lower()
    if re.search(r'sugerente\s+(de|del)', ctx):
        return "sugerente"
    if re.search(r'compatible\s+con', ctx):
        return "compatible"
    if re.search(r'\bprobable\b', ctx):
        return "probable"
    if re.search(r'\bposible\b', ctx):
        return "posible"
    if re.search(r'descartar|descarta', ctx):
        return "descartado"
    return None


def _extract_lateralidad(texto: str, match) -> str | None:
    ctx_start = max(0, match.start() - 30)
    ctx_end = min(len(texto), match.end() + 30)
    ctx = texto[ctx_start:ctx_end].lower()
    if re.search(r'\bbilateral(es)?\b', ctx):
        return "bilateral"
    if re.search(r'\b(izquierd[ao]s?)\b', ctx):
        return "izquierdo"
    if re.search(r'\b(derech[ao]s?)\b', ctx):
        return "derecho"
    return None


def classify_item(item: dict, texto: str) -> tuple[str, str]:
    """Devuelve (clase, razón) — TP/FP/AMBIGUO."""
    canonico = item["termino_canonico"]

    if canonico in FP_SEGuros:
        return ("FP", FP_SEGuros[canonico])

    if canonico in AMBIGUOS:
        return ("AMBIGUO", AMBIGUOS[canonico])

    # Heurísticas contextuales
    if canonico == "masa" and "masa" in texto.lower():
        # 'masa' puede ser FP si es coloquial ('masa muscular')
        if re.search(r'\bmasa\s+muscular\b', texto, re.IGNORECASE):
            return ("FP", "'masa muscular' no es hallazgo clínico.")

    if canonico == "ectasia" and re.search(r'\bectasia\s+(sin|s\/)', texto, re.IGNORECASE):
        return ("FP", "Forma negativa 'ectasia sin [patología]' — solo es relevante la negación.")

    if canonico == "ambos" and not re.search(r'\b(riñón|riñones|hígado|adrenal|órgano)\b',
                                              texto, re.IGNORECASE):
        return ("FP", "'ambos' sin órgano adyacente — no es lateralidad clínica.")

    if canonico == "normal" and item["tipo_item"] == "NEGATIVO":
        # 'normal' como NEGATIVO es ambiguo: depende de si la conclusión
        # completa es negativa o si 'normal' acompaña a un diagnóstico
        if any(c in texto.lower() for c in ["nefropatía", "hepatomegalia",
                                              "gastritis", "pancreatitis"]):
            return ("AMBIGUO", "'normal' acompaña a un diagnóstico. Probable FP como item "
                        "independiente — debería ser modificador, no hallazgo.")
        return ("TP", "'normal' como hallazgo principal (conclusión 100% normal).")

    if canonico in ("biliar", "hepatic", "vesical") and item["tipo_item"] == "DIAGNOSTICO":
        # Términos anatómicos detectados como diagnósticos — son ambiguos
        return ("AMBIGUO", f"'{canonico}' es término anatómico, no diagnóstico. "
                    f"Puede ser parte de un compuesto (ej. 'barro biliar').")

    return ("TP", "Match en contexto clínico.")


def main():
    raw = sqlite3.connect(ROOT / "informes.db")
    cur = raw.cursor()

    # Selección reproducible: ORDER BY RANDOM() con seed=42
    # Para reproducibilidad exacta en SQLite, usamos random semilla via Python.
    import random
    rng = random.Random(SEED)
    all_ids = [r[0] for r in cur.execute("SELECT id FROM conclusiones").fetchall()]
    sample_ids = rng.sample(all_ids, N_SAMPLES)
    sample_ids.sort()  # orden estable

    # Cargar los textos
    samples = []
    for cid in sample_ids:
        row = cur.execute("SELECT id, informe_id, texto_completo FROM conclusiones WHERE id = ?",
                          (cid,)).fetchone()
        if row:
            samples.append({"id": row[0], "informe_id": row[1], "texto": row[2]})

    raw.close()

    # Extraer y clasificar items
    results = []
    for s in samples:
        items = extract_items(s["texto"])
        for it in items:
            clase, razon = classify_item(it, s["texto"])
            it["clase"] = clase
            it["razon_clase"] = razon
        results.append({
            "conclusion_id": s["id"],
            "informe_id": s["informe_id"],
            "texto": s["texto"],
            "n_items": len(items),
            "items": items,
        })

    # ─── Métricas globales ───
    all_items = [it for r in results for it in r["items"]]
    n_total = len(all_items)
    n_tp = sum(1 for it in all_items if it["clase"] == "TP")
    n_fp = sum(1 for it in all_items if it["clase"] == "FP")
    n_amb = sum(1 for it in all_items if it["clase"] == "AMBIGUO")

    precision_ajustada = n_tp / n_total if n_total else 0
    precision_ajustada_con_amb = (n_tp + 0.5 * n_amb) / n_total if n_total else 0

    # Items por conclusión
    items_per_concl = [r["n_items"] for r in results]

    # Top 20 términos con TP%/FP%
    term_stats = defaultdict(lambda: {"TP": 0, "FP": 0, "AMBIGUO": 0})
    for it in all_items:
        term_stats[it["termino_canonico"]][it["clase"]] += 1
    top20 = sorted(term_stats.items(), key=lambda x: -(x[1]["TP"] + x[1]["FP"] + x[1]["AMBIGUO"]))[:20]
    top20_out = []
    for term, stats in top20:
        n = sum(stats.values())
        top20_out.append({
            "termino": term,
            "n_total": n,
            "n_tp": stats["TP"],
            "n_fp": stats["FP"],
            "n_ambiguo": stats["AMBIGUO"],
            "pct_tp": round(100 * stats["TP"] / n, 1),
            "pct_fp": round(100 * stats["FP"] / n, 1),
            "pct_amb": round(100 * stats["AMBIGUO"] / n, 1),
        })

    # FP por categoría
    fp_por_categoria = Counter()
    for it in all_items:
        if it["clase"] == "FP":
            fp_por_categoria[it["tipo_item"]] += 1

    # Distribución items/conclusión
    dist_items = Counter(items_per_concl)
    dist_items_sorted = sorted(dist_items.items())

    # Conclusiones con 0 items
    n_sin_items = sum(1 for r in results if r["n_items"] == 0)

    # ─── Output ───
    summary = {
        "seed": SEED,
        "n_samples": len(results),
        "n_total_items": n_total,
        "precision": {
            "n_tp": n_tp,
            "n_fp": n_fp,
            "n_ambiguo": n_amb,
            "precision_ajustada_tp_solo": round(precision_ajustada, 4),
            "precision_con_ambiguo_como_05": round(precision_ajustada_con_amb, 4),
        },
        "items_por_conclusion": {
            "media": round(sum(items_per_concl) / len(items_per_concl), 2),
            "mediana": sorted(items_per_concl)[len(items_per_concl) // 2],
            "max": max(items_per_concl),
            "min": min(items_per_concl),
            "distribucion": [{"items": k, "conclusiones": v} for k, v in dist_items_sorted],
            "conclusiones_sin_items": n_sin_items,
        },
        "fp_por_categoria": dict(fp_por_categoria),
        "top20_terminos": top20_out,
    }

    out_dir = ROOT / "docs"
    with open(out_dir / "_F5_audit_samples.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(out_dir / "_F5_audit_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # ─── Print resumen ───
    print("=" * 70)
    print(f"F5 AUDITORÍA DE PRECISIÓN — seed={SEED}, n={len(results)}")
    print("=" * 70)
    print(f"\nTotal items extraídos:  {n_total}")
    print(f"  TP:                   {n_tp} ({100*n_tp/n_total:.1f}%)")
    print(f"  FP:                   {n_fp} ({100*n_fp/n_total:.1f}%)")
    print(f"  AMBIGUO:              {n_amb} ({100*n_amb/n_total:.1f}%)")
    print(f"\nPrecisión ajustada (TP / total):           {100*precision_ajustada:.1f}%")
    print(f"Precisión (TP + 0.5*AMBIGUO) / total:      {100*precision_ajustada_con_amb:.1f}%")

    print(f"\nItems por conclusión:")
    print(f"  Media:    {summary['items_por_conclusion']['media']}")
    print(f"  Mediana:  {summary['items_por_conclusion']['mediana']}")
    print(f"  Max:      {summary['items_por_conclusion']['max']}")
    print(f"  Min:      {summary['items_por_conclusion']['min']}")
    print(f"  Conclusión sin items: {n_sin_items}")

    print(f"\nFP por categoría:")
    for cat, n in fp_por_categoria.most_common():
        print(f"  {cat:15s} {n}")

    print(f"\nTop 20 términos con TP%/FP%:")
    print(f"  {'Término':30s} {'N':>4s} {'TP':>4s} {'FP':>4s} {'AMB':>4s} {'%TP':>6s} {'%FP':>6s}")
    for t in top20_out:
        print(f"  {t['termino']:30s} {t['n_total']:>4d} {t['n_tp']:>4d} {t['n_fp']:>4d} "
              f"{t['n_ambiguo']:>4d} {t['pct_tp']:>5.1f}% {t['pct_fp']:>5.1f}%")


if __name__ == "__main__":
    main()
