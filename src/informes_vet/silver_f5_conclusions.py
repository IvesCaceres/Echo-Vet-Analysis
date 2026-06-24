"""F5 — Extracción de ítems desde CONCLUSIONES (Opción C, capa SILVER).

Convierte cada `raw.conclusiones.texto_completo` en una lista de ítems
estructurados (DIAGNOSTICO + ETIOLOGIA + NEGATIVO) con sus modificadores
promovidos a columnas (lateralidad, modificador_cualidad,
modificador_distribucion). 100% basado en regex + diccionarios +
reglas determinísticas (sin NLP, sin embeddings, sin fuzzy matching).

Diseño (validado en `docs/F5_PRECISION_AUDIT.md` y `docs/F5_DISTRIBUTION_AUDIT.md`):
- 3 tipos de item: DIAGNOSTICO, ETIOLOGIA, NEGATIVO.
- 3 modificadores promovidos a columnas del item diagnóstico más cercano
  en la MISMA oración (ventana ±60 chars).
- Negación: campo booleano `negado` por item.
- Idempotencia: UNIQUE INDEX
  (conclusion_id, termino_conclusion_id, pos_inicio, pos_fin).

Pasos del build_f5():
  1. seed_dim_termino_conclusion — UPSERT del catálogo canónico.
  2. extract_conclusions — para cada raw.conclusiones genera items.
  3. populate_silver_conclusion_items — INSERT con ON CONFLICT DO NOTHING.
  4. populate_stg_conclusion_no_match — UPSERT de conclusiones sin items.
  5. update_dim_frecuencias — refresca n_menciones_corpus / frecuencia_rank.
"""
from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .models_silver import (
    dim_termino_conclusion,
    silver_conclusion_items,
    stg_conclusion_no_match,
)

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CATÁLOGO DE TÉRMINOS (catálogo semilla validado en F5_DISTRIBUTION_AUDIT)
# ═══════════════════════════════════════════════════════════════════════════
#
# Estructura:
#   CANONICOS_DIAG / CANONICOS_ETIOL / CANONICOS_NEG → nombre_canonico: [variantes]
# CANONICOS_DIAG y CANONICOS_NEG se siembran en dim_termino_conclusion.
# CANONICOS_ETIOL también. Las variantes son los strings exactos buscados
# en el texto (case-insensitive, con word boundaries).

CANONICOS_DIAG: dict[str, list[str]] = {
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
    "hiperplasia":           ["hiperplasia"],
    "atrofia":               ["atrofia"],
    "ectasia_independiente": ["ectasia"],  # hallazgo principal sin diagnóstico subyacente
}

CANONICOS_ETIOL: dict[str, list[str]] = {
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

CANONICOS_NEG: dict[str, list[str]] = {
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

# Modificadores que se promueven a columnas del item
LATERALIDAD: dict[str, list[str]] = {
    "bilateral":  ["bilateral", "bilaterales"],
    "izquierdo":  ["izquierdo", "izquierda", "izquierdos", "izquierdas"],
    "derecho":    ["derecho", "derecha", "derechos", "derechas"],
    "ambos":      ["ambos", "ambas"],
    "unilateral": ["unilateral", "unilaterales"],
}

# Cualidad = morfología + severidad (decisión de diseño: combinadas)
CUALIDAD: dict[str, list[str]] = {
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

DISTRIBUCION: dict[str, list[str]] = {
    "focal":         ["focal", "focales"],
    "multifocal":    ["multifocal", "multifocales"],
    "difusa":        ["difusa", "difuso"],
    "generalizada":  ["generalizada", "generalizado"],
    "discreta":      ["discreta", "discreto"],
}

# Marcadores de negación explícita que preceden a un término
NEGADORES = [
    r"\bsin\s+",
    r"\bno\s+se\s+observa[n]?\s+",
    r"\bausencia\s+de\s+",
    r"\bnegativo\s+",
]


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS DE EXTRACCIÓN
# ═══════════════════════════════════════════════════════════════════════════

def find_matches(texto_lower: str, terminos: list[str]) -> list[tuple[int, int, str]]:
    """Devuelve lista de (pos_inicio, pos_fin, termino_original) por match."""
    out = []
    for term in terminos:
        patron = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
        for m in patron.finditer(texto_lower):
            out.append((m.start(), m.end(), m.group(0)))
    out.sort()
    return out


def split_sentences(texto: str) -> list[tuple[int, int]]:
    """Devuelve lista de (start, end) por oración."""
    sentences = []
    start = 0
    for m in re.finditer(r"\.\s+", texto):
        sentences.append((start, m.end()))
        start = m.end()
    sentences.append((start, len(texto)))
    return sentences


def find_sentence_for_pos(pos: int, sentences: list[tuple[int, int]]) -> int:
    for i, (s, e) in enumerate(sentences):
        if s <= pos < e:
            return i
    return len(sentences) - 1


def nearest_modifier(
    modifiers: list[tuple[int, int, str, str]],
    item_pos: int,
    item_end: int,
    item_sentence_idx: int,
    sentences: list[tuple[int, int]],
    window: int = 60,
) -> tuple[int, int, str, str] | None:
    """Encuentra el modificador más cercano al item dentro de la misma oración.

    Devuelve (pos_inicio, pos_fin, termino_original, canonico).
    """
    best = None
    best_dist = float("inf")
    for mpos, mend, mterm, mcanon in modifiers:
        m_sent = find_sentence_for_pos(mpos, sentences)
        if m_sent != item_sentence_idx:
            continue
        if mend <= item_pos:
            dist = item_pos - mend
        elif mpos >= item_end:
            dist = mpos - item_end
        else:
            dist = 0
        if dist > window:
            continue
        if dist < best_dist:
            best_dist = dist
            best = (mpos, mend, mterm, mcanon)
    return best


def is_negated(texto: str, pos_inicio: int) -> bool:
    """¿Hay un negador (sin / no se observa / ausencia de / negativo) en los
    30 chars inmediatamente anteriores a la posición?
    """
    ventana = texto[max(0, pos_inicio - 30):pos_inicio].lower()
    for neg in NEGADORES:
        if re.search(neg, ventana):
            return True
    return False


# ═══════════════════════════════════════════════════════════════════════════
# EXTRACTOR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

def extract_items(texto: str) -> list[dict]:
    """Extrae ítems Opción C de un texto.

    Devuelve lista de dicts con:
      - tipo_item
      - termino_canonico
      - termino_detectado (texto original con case preservado)
      - pos_inicio, pos_fin
      - lateralidad, modificador_cualidad, modificador_distribucion (o None)
      - negado (bool)
    """
    texto_lower = texto.lower()
    sentences = split_sentences(texto)
    items: list[dict] = []
    seen_items: set[tuple[int, str]] = set()

    diag_matches: list[tuple[int, int, str, str, str]] = []
    for canon, terms in CANONICOS_DIAG.items():
        for ps, pe, to in find_matches(texto_lower, terms):
            diag_matches.append((ps, pe, to, canon, "DIAGNOSTICO"))
    etio_matches: list[tuple[int, int, str, str, str]] = []
    for canon, terms in CANONICOS_ETIOL.items():
        for ps, pe, to in find_matches(texto_lower, terms):
            etio_matches.append((ps, pe, to, canon, "ETIOLOGIA"))
    neg_matches: list[tuple[int, int, str, str, str]] = []
    for canon, terms in CANONICOS_NEG.items():
        for ps, pe, to in find_matches(texto_lower, terms):
            neg_matches.append((ps, pe, to, canon, "NEGATIVO"))

    lat_matches: list[tuple[int, int, str, str]] = []
    for canon, terms in LATERALIDAD.items():
        for ps, pe, to in find_matches(texto_lower, terms):
            lat_matches.append((ps, pe, to, canon))
    cual_matches: list[tuple[int, int, str, str]] = []
    for canon, terms in CUALIDAD.items():
        for ps, pe, to in find_matches(texto_lower, terms):
            cual_matches.append((ps, pe, to, canon))
    dist_matches: list[tuple[int, int, str, str]] = []
    for canon, terms in DISTRIBUCION.items():
        for ps, pe, to in find_matches(texto_lower, terms):
            dist_matches.append((ps, pe, to, canon))

    all_items_raw = diag_matches + etio_matches + neg_matches
    all_items_raw.sort(key=lambda x: x[0])

    for ps, pe, to, canon, tipo in all_items_raw:
        key = (ps, canon)
        if key in seen_items:
            continue
        seen_items.add(key)

        sent_idx = find_sentence_for_pos(ps, sentences)

        lat = nearest_modifier(lat_matches, ps, pe, sent_idx, sentences)
        cual = nearest_modifier(cual_matches, ps, pe, sent_idx, sentences)
        dist = nearest_modifier(dist_matches, ps, pe, sent_idx, sentences)

        items.append({
            "tipo_item": tipo,
            "termino_canonico": canon,
            "termino_detectado": texto[ps:pe],
            "pos_inicio": ps,
            "pos_fin": pe,
            "lateralidad": lat[3] if lat else None,
            "modificador_cualidad": cual[3] if cual else None,
            "modificador_distribucion": dist[3] if dist else None,
            "negado": is_negated(texto, ps),
        })

    return items


# ═══════════════════════════════════════════════════════════════════════════
# UPSERT PORTABLE
# ═══════════════════════════════════════════════════════════════════════════

def _upsert_ignore(table, rows: list[dict], engine: Engine, index_elements) -> int:
    """INSERT ... ON CONFLICT DO NOTHING portable (SQLite + Postgres)."""
    if not rows:
        return 0
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    insert_fn = sqlite_insert if engine.dialect.name == "sqlite" else pg_insert
    stmt = insert_fn(table).values(rows)
    stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        return result.rowcount or 0


def _delete_table(engine: Engine, table_name: str) -> int:
    """DELETE ALL portable (no usar en producción; aquí solo para rebuild
    idempotente de silver_conclusion_items)."""
    with engine.begin() as conn:
        result = conn.execute(text(f"DELETE FROM {table_name}"))
        return result.rowcount or 0


# ═══════════════════════════════════════════════════════════════════════════
# SEED DIM_TERMINO_CONCLUSION
# ═══════════════════════════════════════════════════════════════════════════

# Categorías clínicas: mapeo manual por inspección de los términos
_CATEGORIA_POR_TERMINO: dict[str, str] = {
    # RENAL
    "nefropatia": "RENAL", "nefromegalia": "RENAL", "nefrocalcinosis": "RENAL",
    "pielectasia": "RENAL", "hidronefrosis": "RENAL",
    "ectasia_pelvica": "RENAL", "dilatacion_ureteral": "RENAL",
    # HEPATICA
    "hepatomegalia": "HEPATICA", "microhepatia": "HEPATICA",
    "hepatopatia": "HEPATICA", "hepatopatia_vacuolar": "HEPATICA",
    "higado_graso": "HEPATICA", "amiloidosis": "HEPATICA",
    "cirrosis": "HEPATICA", "fibrosis": "HEPATICA",
    # ESPLENICA
    "esplenomegalia": "ESPLENICA", "nodulo_esplenico": "ESPLENICA",
    "hematoma_esplenico": "ESPLENICA",
    # GASTROINTESTINAL
    "gastritis": "GASTROINTESTINAL", "gastropatia": "GASTROINTESTINAL",
    "enteritis": "GASTROINTESTINAL", "enterocolitis": "GASTROINTESTINAL",
    "colitis": "GASTROINTESTINAL", "ileitis": "GASTROINTESTINAL",
    # PANCREATICA
    "pancreatitis": "PANCREATICA", "cambios_pancreaticos": "PANCREATICA",
    # VESICULA
    "colecistitis": "VESICULA", "barro_biliar": "VESICULA",
    "sedimento_biliar": "VESICULA", "colelitiasis": "VESICULA",
    # URINARIO
    "cistitis": "URINARIO", "cistolito": "URINARIO",
    "sedimento_vejiga": "URINARIO", "urolitiasis": "URINARIO",
    # REPRODUCTIVO
    "histeromegalia": "REPRODUCTIVO", "piometra": "REPRODUCTIVO",
    "mucometra": "REPRODUCTIVO", "hemometra": "REPRODUCTIVO",
    "prostatomegalia": "REPRODUCTIVO", "prostatitis": "REPRODUCTIVO",
    "hiperplasia_prostatica": "REPRODUCTIVO",
    "quiste_ovarico": "REPRODUCTIVO", "gestacion": "REPRODUCTIVO",
    # ENDOCRINO
    "adrenomegalia": "ENDOCRINO",
    # LINFATICO
    "linfadenomegalia": "LINFATICO",
    # PERITONEO
    "peritonitis": "PERITONEO", "derrame_peritoneal": "PERITONEO",
    # MISC
    "neoplasia": "MISC_NEOPLASIA", "neoplasico": "MISC_NEOPLASIA",
    "masa": "MISC_MORFOLOGIA", "nodulo": "MISC_MORFOLOGIA",
    "lesion": "MISC_MORFOLOGIA", "quiste": "MISC_MORFOLOGIA",
    "estenosis": "MISC_MORFOLOGIA", "obstruccion": "MISC_MORFOLOGIA",
    "absceso": "MISC_MORFOLOGIA", "hematoma": "MISC_MORFOLOGIA",
    "polipo": "MISC_MORFOLOGIA", "hiperplasia": "MISC_MORFOLOGIA",
    "atrofia": "MISC_MORFOLOGIA", "ectasia_independiente": "MISC_MORFOLOGIA",
}


def seed_dim_termino_conclusion(engine: Engine) -> dict:
    """Siembra dim_termino_conclusion con todos los canónicos.

    Idempotente: usa UPSERT por nombre_canonico.
    Returns: { "n_insertados": int, "n_total": int }
    """
    rows: list[dict] = []
    for canon, variants in CANONICOS_DIAG.items():
        rows.append({
            "nombre_canonico": canon,
            "tipo_item": "DIAGNOSTICO",
            "organo_asociado": None,
            "categoria_clinica": _CATEGORIA_POR_TERMINO.get(canon),
            "sinonimos": None,
            "patron_extraccion": "|".join(variants),
            "activo": True,
        })
    for canon, variants in CANONICOS_ETIOL.items():
        rows.append({
            "nombre_canonico": canon,
            "tipo_item": "ETIOLOGIA",
            "organo_asociado": None,
            "categoria_clinica": None,
            "sinonimos": None,
            "patron_extraccion": "|".join(variants),
            "activo": True,
        })
    for canon, variants in CANONICOS_NEG.items():
        rows.append({
            "nombre_canonico": canon,
            "tipo_item": "NEGATIVO",
            "organo_asociado": None,
            "categoria_clinica": "NEGATIVO",
            "sinonimos": None,
            "patron_extraccion": "|".join(variants),
            "activo": True,
        })

    n_insertados = _upsert_ignore(
        dim_termino_conclusion, rows, engine,
        index_elements=["nombre_canonico"],
    )
    with engine.begin() as conn:
        n_total = conn.execute(text(
            "SELECT COUNT(*) FROM dim_termino_conclusion"
        )).scalar()
    return {"n_insertados": n_insertados, "n_total": n_total}


# ═══════════════════════════════════════════════════════════════════════════
# EXTRACTOR SOBRE RAW.CONCLUSIONES
# ═══════════════════════════════════════════════════════════════════════════

def _read_conclusiones(raw_engine: Engine) -> list[tuple[int, int, str]]:
    """Lee TODAS las conclusiones de RAW."""
    with raw_engine.begin() as conn:
        rows = conn.execute(text(
            "SELECT id, informe_id, texto_completo FROM conclusiones"
        )).all()
    return [(r[0], r[1], r[2]) for r in rows]


def _read_dim_termino_map(engine: Engine) -> dict[str, int]:
    """Devuelve dict {nombre_canonico: id} para JOIN."""
    with engine.begin() as conn:
        rows = conn.execute(text(
            "SELECT id, nombre_canonico FROM dim_termino_conclusion"
        )).all()
    return {r[1]: r[0] for r in rows}


def extract_all_conclusions(
    raw_engine: Engine,
    silver_engine: Engine,
) -> dict:
    """Aplica extract_items a TODAS las conclusiones y devuelve métricas.

    No escribe en silver; sólo computa. populate_silver_conclusion_items
    se encarga del INSERT.

    Returns dict con:
      - n_conclusiones_total
      - n_conclusiones_con_items
      - n_conclusiones_sin_items
      - n_items_total
      - items_per_conclusion_stats
      - term_counter (Counter termino_canonico → n)
      - lat_counter, cual_counter, dist_counter
      - all_items (lista de dicts lista para INSERT)
      - all_no_match (lista de dicts lista para INSERT en stg_*)
    """
    raw_rows = _read_conclusiones(raw_engine)
    dim_map = _read_dim_termino_map(silver_engine)

    items_per_concl: list[int] = []
    all_items: list[dict] = []
    all_no_match: list[dict] = []
    term_counter: Counter = Counter()
    lat_counter: Counter = Counter()
    cual_counter: Counter = Counter()
    dist_counter: Counter = Counter()

    n_with_items = 0
    for cid, iid, texto in raw_rows:
        items = extract_items(texto or "")
        items_per_concl.append(len(items))
        if items:
            n_with_items += 1
        else:
            # Clasificar el tipo de no_match
            t_lower = (texto or "").lower().strip()
            if len(t_lower) < 8:
                tipo_no_match = "demasiado_corto"
            else:
                tipo_no_match = "sin_patron"
            all_no_match.append({
                "conclusion_id": cid,
                "informe_id": iid,
                "texto_no_matcheado": texto or "",
                "n_caracteres": len(texto or ""),
                "n_oraciones": len(split_sentences(texto or "")),
                "tipo_no_match": tipo_no_match,
            })

        for it in items:
            tcid = dim_map.get(it["termino_canonico"])
            if tcid is None:
                # Término extraído pero no en catálogo: skip con warning.
                # En práctica no debería pasar (catálogo exhaustivo).
                log.warning("[f5] término '%s' extraído pero sin id en dim_termino_conclusion",
                            it["termino_canonico"])
                continue
            all_items.append({
                "conclusion_id": cid,
                "informe_id": iid,
                "termino_conclusion_id": tcid,
                "lateralidad": it["lateralidad"],
                "modificador_cualidad": it["modificador_cualidad"],
                "modificador_distribucion": it["modificador_distribucion"],
                "negado": bool(it["negado"]),
                "pos_inicio": it["pos_inicio"],
                "pos_fin": it["pos_fin"],
                "termino_detectado": it["termino_detectado"],
                "confianza": 1.0,
                "metodo_extraccion": "REGEX_RULE",
            })
            term_counter[it["termino_canonico"]] += 1
            if it["lateralidad"]:
                lat_counter[it["lateralidad"]] += 1
            if it["modificador_cualidad"]:
                cual_counter[it["modificador_cualidad"]] += 1
            if it["modificador_distribucion"]:
                dist_counter[it["modificador_distribucion"]] += 1

    sorted_per = sorted(items_per_concl)
    n_total = len(raw_rows)
    items_stats = {
        "media": round(sum(items_per_concl) / n_total, 2) if n_total else 0,
        "mediana": sorted_per[n_total // 2] if n_total else 0,
        "max": max(items_per_concl) if items_per_concl else 0,
        "min": min(items_per_concl) if items_per_concl else 0,
    }

    return {
        "n_conclusiones_total": n_total,
        "n_conclusiones_con_items": n_with_items,
        "n_conclusiones_sin_items": n_total - n_with_items,
        "n_items_total": len(all_items),
        "items_per_conclusion": items_stats,
        "term_counter": term_counter,
        "lat_counter": lat_counter,
        "cual_counter": cual_counter,
        "dist_counter": dist_counter,
        "all_items": all_items,
        "all_no_match": all_no_match,
    }


# ═══════════════════════════════════════════════════════════════════════════
# POBLAR SILVER_CONCLUSION_ITEMS + STG_CONCLUSION_NO_MATCH
# ═══════════════════════════════════════════════════════════════════════════

def populate_silver_conclusion_items(
    silver_engine: Engine,
    items: list[dict],
) -> dict:
    """UPSERT los items en silver_conclusion_items.

    Estrategia idempotente: DELETE + INSERT en una transacción. Más simple
    que ON CONFLICT y correcto porque la tabla se reconstruye desde RAW en
    cada build (es staging derivable).

    Returns: { "n_deleted": int, "n_inserted": int }
    """
    n_deleted = _delete_table(silver_engine, "silver_conclusion_items")
    n_inserted = 0
    if items:
        CHUNK = 500
        with silver_engine.begin() as conn:
            for i in range(0, len(items), CHUNK):
                chunk = items[i:i + CHUNK]
                result = conn.execute(silver_conclusion_items.insert(), chunk)
                n_inserted += result.rowcount or 0
    return {"n_deleted": n_deleted, "n_inserted": n_inserted}


def populate_stg_conclusion_no_match(
    silver_engine: Engine,
    no_match: list[dict],
) -> dict:
    """UPSERT stg_conclusion_no_match por conclusion_id (UNIQUE)."""
    n_deleted = _delete_table(silver_engine, "stg_conclusion_no_match")
    n_inserted = 0
    if no_match:
        CHUNK = 500
        with silver_engine.begin() as conn:
            for i in range(0, len(no_match), CHUNK):
                chunk = no_match[i:i + CHUNK]
                result = conn.execute(stg_conclusion_no_match.insert(), chunk)
                n_inserted += result.rowcount or 0
    return {"n_deleted": n_deleted, "n_inserted": n_inserted}


# ═══════════════════════════════════════════════════════════════════════════
# UPDATE FRECUENCIAS EN dim_termino_conclusion
# ═══════════════════════════════════════════════════════════════════════════

def update_dim_frecuencias(
    silver_engine: Engine,
    term_counter: Counter,
) -> dict:
    """Actualiza n_menciones_corpus y frecuencia_rank en dim_termino_conclusion.

    frecuencia_rank: 1 = más frecuente, NULL = nunca observado.
    """
    if not term_counter:
        return {"n_actualizados": 0, "n_sin_uso": 0}

    # Ordenar por frecuencia desc → rank
    sorted_terms = sorted(term_counter.items(), key=lambda x: -x[1])
    rank_map = {term: rank + 1 for rank, (term, _) in enumerate(sorted_terms)}

    n_actualizados = 0
    with silver_engine.begin() as conn:
        for term, count in term_counter.items():
            result = conn.execute(
                dim_termino_conclusion.update()
                .where(dim_termino_conclusion.c.nombre_canonico == term)
                .values(
                    n_menciones_corpus=count,
                    frecuencia_rank=rank_map[term],
                )
            )
            n_actualizados += result.rowcount or 0
        # Marcar n_menciones_corpus=0 para los no observados
        no_uso = 0
        for canon in (
            list(CANONICOS_DIAG.keys())
            + list(CANONICOS_ETIOL.keys())
            + list(CANONICOS_NEG.keys())
        ):
            if canon not in term_counter:
                result = conn.execute(
                    dim_termino_conclusion.update()
                    .where(dim_termino_conclusion.c.nombre_canonico == canon)
                    .values(n_menciones_corpus=0, frecuencia_rank=None)
                )
                no_uso += result.rowcount or 0

    return {"n_actualizados": n_actualizados, "n_sin_uso": no_uso}


# ═══════════════════════════════════════════════════════════════════════════
# API PÚBLICA
# ═══════════════════════════════════════════════════════════════════════════

def build_f5(silver_engine: Engine, raw_engine: Engine) -> dict:
    """Ejecuta F5 completo. Idempotente.

    Pasos:
      1. seed_dim_termino_conclusion — UPSERT del catálogo.
      2. extract_all_conclusions — extracción completa desde RAW.
      3. populate_silver_conclusion_items — DELETE + INSERT.
      4. populate_stg_conclusion_no_match — DELETE + INSERT.
      5. update_dim_frecuencias — refresca n_menciones_corpus y rank.
    """
    metrics: dict = {}
    log.info("[f5] seeding dim_termino_conclusion...")
    metrics["dim_termino_conclusion"] = seed_dim_termino_conclusion(silver_engine)

    log.info("[f5] extracting items from raw.conclusiones...")
    ext = extract_all_conclusions(raw_engine, silver_engine)
    metrics["extract"] = {
        "n_conclusiones_total": ext["n_conclusiones_total"],
        "n_conclusiones_con_items": ext["n_conclusiones_con_items"],
        "n_conclusiones_sin_items": ext["n_conclusiones_sin_items"],
        "n_items_total": ext["n_items_total"],
        "items_per_conclusion": ext["items_per_conclusion"],
    }

    log.info("[f5] populating silver_conclusion_items (%d items)...", len(ext["all_items"]))
    metrics["silver_conclusion_items"] = populate_silver_conclusion_items(
        silver_engine, ext["all_items"]
    )

    log.info("[f5] populating stg_conclusion_no_match (%d rows)...", len(ext["all_no_match"]))
    metrics["stg_conclusion_no_match"] = populate_stg_conclusion_no_match(
        silver_engine, ext["all_no_match"]
    )

    log.info("[f5] updating dim_termino_conclusion.frecuencia_rank...")
    metrics["dim_frecuencias"] = update_dim_frecuencias(
        silver_engine, ext["term_counter"]
    )

    # Mantener los counters accesibles para el reporte
    metrics["_counters"] = {
        "term": dict(ext["term_counter"].most_common()),
        "lateralidad": dict(ext["lat_counter"].most_common()),
        "cualidad": dict(ext["cual_counter"].most_common()),
        "distribucion": dict(ext["dist_counter"].most_common()),
    }

    return metrics
