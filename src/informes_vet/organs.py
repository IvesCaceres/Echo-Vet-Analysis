"""Lista de órganos, segmentación por regex y clasificación de estado.

Portado de `local_massive_sync_v7.py:7-66` con ajustes.

Cambios 2026-06-17 (post-auditoría):
- H1: 'Renal' / 'Renales' reconocido como sinónimo de 'Riñones'.
- H2: 'Estomago' (sin tilde) reconocido como sinónimo de 'Estómago'.
- H4: boundary antes del encabezado acepta '.', ';', whitespace y saltos
      de línea (antes solo '\\n' o ' '), para tolerar encabezados pegados.
- H5: 'Yeyuno' se normaliza a 'Intestino' tras la segmentación canónica.
- H3: si el segmentador canónico devuelve <5 hallazgos, se activa un
      segmentador narrativo conservador.
"""

import re

ORGANS: list[str] = [
    "Vejiga",
    "Próstata",
    "Riñones",
    "Bazo",
    "Estómago",
    "Hígado",
    "Vesícula",
    "Intestino",
    "Páncreas",
    "Adrenales",
    "Linfonodos",
    "Cavidad abdominal",
    "Útero",
    "Ovarios",
    "Testículos",
]

ORGANS_SYNONYMS: dict[str, list[str]] = {
    "Riñones":  ["Renal", "Renales"],
    "Estómago": ["Estomago"],
}

ORGANS_ABSORBED: dict[str, str] = {
    # Intestino
    "Yeyuno":  "Intestino",
    "Duodeno": "Intestino",
    "Íleon":   "Intestino",
    "Ileon":   "Intestino",
    "Colon":   "Intestino",
    "Colón":   "Intestino",
    "Colon descendente": "Intestino",
    "Colón descendente": "Intestino",
    "Ciego":   "Intestino",
    "Recto":   "Intestino",
    "Intestino delgado": "Intestino",
    # Riñones (singular y variantes con/sin tildes)
    "Riñón":     "Riñones",
    "Rinon":     "Riñones",
    # Vesícula (la biliar es la única mencionada, pero generalizamos)
    "Vesícula biliar":  "Vesícula",
    "Vesícula  biliar": "Vesícula",
    "Vesicula biliar":  "Vesícula",
    "Vesicula  biliar": "Vesícula",
    "Vesicula":         "Vesícula",
    # Pares singulares
    "Testículo": "Testículos",
    "Testiculo": "Testículos",
    "Ovario":    "Ovarios",
    "Linfonodo": "Linfonodos",
    # Útero (subregiones)
    "Cuerpo uterino":  "Útero",
    "Cuerpo  uterino": "Útero",
    # Adrenales (consolidación plural/singular con y sin "Glándula(s)")
    "Glándula adrenal":   "Adrenales",
    "Glándulas adrenales":"Adrenales",
}

# Palabras de prosa clínica que típicamente siguen a un órgano en formato
# narrativo (no encabezado). Se usan SOLO en segment_findings_narrative().
# Mantener conservador: pocas palabras, todas en presente/pretérito del
# estilo "se observa", "se aprecian", etc. Si una palabra no está aquí,
# NO se captura la mención como hallazgo narrativo.
_NARRATIVE_POST_PATTERNS: tuple[str, ...] = (
    r"se\s+observ[oáa]",
    r"se\s+apreci[ao]n?",
    r"se\s+encuentr[ao]n?",
    r"se\s+visualiz[ao]n?",
    r"se\s+identific[aoé]",
    r"se\s+reconoc[ae]",
    r"muestra\s+",
    r"present[aoáe]\s+",
    r"de\s+aspecto\s+",
    r"se\s+describe",
    r"se\s+evalu[oóá]",
    r"se\s+explor[oóá]",
    r"se\s+interrog[oóá]",
    r"\s+se\s+",
    r"\s+es\s+",
    r"\s+est[aá]\s+",
    r"\s+con\s+",
    r"\s+del?\s+",
    r"\s+al?\s+",
)

_ALERT_ROOTS: list[str] = [
    "irregular",
    "heterogene",
    "alterad",
    "presencia de",
    "lesión",
    "masa",
    "nódulo",
    "lodo",
    "sediment",
    "reacción",
    "efusión",
    "líquido libre",
    "urolito",
    "arenilla",
    "coleccion",
    "reactiv",
    "dilatad",
    "proliferación",
    "quiste",
    "mineraliz",
]

_NEGATIONS: list[str] = [
    "no se ",
    "sin ",
    "ausencia de",
    "no presenta",
    "no evidenc",
    "normal",
    "conservado",
    "dentro de rango",
]


def classify_state(text: str) -> str:
    """Devuelve 'normal' | 'anormal' | 'no evaluado' según el texto del hallazgo."""
    t = text.lower()
    if any(x in t for x in ["no evaluad", "no se evalu", "no visualiz"]):
        return "no_evaluado"

    if ("aumentad" in t or "disminuid" in t) and "tamaño normal" not in t:
        is_size_issue = True
    else:
        is_size_issue = False

    is_anormal = is_size_issue
    if not is_anormal:
        for root in _ALERT_ROOTS:
            idx = t.find(root)
            if idx == -1:
                continue
            negated = False
            for neg in _NEGATIONS:
                idx_neg = t.rfind(neg, 0, idx)
                if idx_neg != -1 and (idx - idx_neg) < 40:
                    negated = True
                    break
            if not negated:
                is_anormal = True
                break

    if ("normal" in t or "conservado" in t) and len(t) < 50:
        return "normal"

    return "anormal" if is_anormal else "normal"


def _canonicalize_organ(name: str) -> str:
    """Mapea sinónimos al nombre canónico. Sin match → devuelve name tal cual."""
    n = name.strip().capitalize()
    for canon, synonyms in ORGANS_SYNONYMS.items():
        if n == canon.capitalize():
            return canon
        if n in {s.capitalize() for s in synonyms}:
            return canon
    if n in {k.capitalize(): v for k, v in ORGANS_ABSORBED.items()}:
        return ORGANS_ABSORBED[n.capitalize()]
    return n


def _build_split_pattern() -> re.Pattern:
    tokens: list[str] = list(ORGANS)
    for synonyms in ORGANS_SYNONYMS.values():
        tokens.extend(synonyms)
    escaped = sorted({re.escape(o) for o in tokens}, key=len, reverse=True)
    pattern = rf"(?:^|[\n.;\s])({'|'.join(escaped)}):"
    return re.compile(pattern, re.IGNORECASE)


_PATTERN = _build_split_pattern()


def segment_findings(text: str) -> list[dict]:
    """Divide el bloque de hallazgos por delimitador `Organo:`.

    Devuelve lista de dicts con keys: organo, descripcion, estado, orden.
    Si no se detecta ningún órgano canónico (caso gestacional), devuelve un único
    hallazgo con organo='Gestación' y el texto completo.

    Cambios 2026-06-17:
    - H1+H2: acepta sinónimos (Renal/Renales/Estomago) y los normaliza al
      nombre canónico.
    - H4:   acepta boundary '.', ';', '\\s' antes del encabezado.
    - H5:   consolida 'Yeyuno' en 'Intestino'.
    """
    if not text:
        return []
    parts = _PATTERN.split(text)
    results: list[dict] = []
    if len(parts) <= 1:
        clean = re.sub(r"\s+", " ", text).strip()
        if clean:
            results.append(
                {
                    "organo": "Gestación",
                    "descripcion": clean,
                    "estado": classify_state(clean),
                    "orden": 0,
                }
            )
        return results

    order = 0
    for i in range(1, len(parts), 2):
        organo_raw = parts[i].strip()
        organo = _canonicalize_organ(organo_raw)
        descripcion = parts[i + 1].strip() if (i + 1) < len(parts) else ""
        descripcion = re.sub(r"\s+", " ", descripcion).strip()
        for other in ORGANS:
            token = f"{other}:"
            if token in descripcion:
                descripcion = descripcion.split(token)[0].strip()
        if not descripcion:
            continue
        results.append(
            {
                "organo": organo,
                "descripcion": descripcion,
                "estado": classify_state(descripcion),
                "orden": order,
            }
        )
        order += 1
    return results


def segment_findings_narrative(text: str) -> list[dict]:
    """Segmentador narrativo conservador para informes sin encabezados `Organo:`.

    SOLO se debe llamar cuando `segment_findings()` devuelve <5 hallazgos.
    Estrategia:
    1. Localizar menciones de órganos en prosa con regex tolerante a mayúsculas
       y tildes alternativas.
    2. Para cada mención, requerir que esté seguida por una palabra/frase de
       prosa clínica (ver _NARRATIVE_POST_PATTERNS). Si no, descartar.
    3. Cada hallazgo narrativo cubre desde su mención hasta la siguiente mención
       de otro órgano, o hasta el final del texto.
    4. Limitar descripciones a 600 caracteres para evitar absorber párrafos
       completos sin sentido.

    Devuelve lista de dicts con keys: organo, descripcion, estado, orden.
    """
    if not text:
        return []

    organos_canonicos = list(ORGANS) + list(ORGANS_SYNONYMS.keys())
    organos_canonicos = sorted(set(organos_canonicos), key=len, reverse=True)

    pattern_parts: list[str] = []
    for org in organos_canonicos:
        # Tolerar mayúsculas y tildes alternativas
        if org == "Riñones":
            pat = r"[Rr]i[ñn][oó]n(?:es)?"
        elif org == "Estómago":
            pat = r"[Ee]st[oó]mago"
        elif org == "Hígado":
            pat = r"[Hh][ií]gado"
        elif org == "Vesícula":
            pat = r"[Vv]es[ií]cula(?:\s+biliar)?"
        elif org == "Páncreas":
            pat = r"[Pp][aá]ncreas"
        elif org == "Útero":
            pat = r"[Úú]tero"
        elif org == "Próstata":
            pat = r"[Pp]r[oó]stata"
        elif org == "Adrenales":
            pat = r"[Aa]drenales?|[Gg]l[aá]ndulas?\s+adrenales?"
        elif org == "Testículos":
            pat = r"[Tt]est[ií]culos?"
        elif org == "Ovarios":
            pat = r"[Oo]varios?"
        elif org == "Intestino":
            pat = r"[Ii]ntestino|[Yy]eyuno|[Dd]uodeno|[Ii]le[oó]n|[Cc]iego|[Cc]ol[oó]n(?:\s+descendente)?|[Rr]ecto"
        elif org == "Vejiga":
            pat = r"[Vv]ejiga"
        elif org == "Bazo":
            pat = r"[Bb]azo"
        elif org == "Linfonodos":
            pat = r"[Ll]infonodos?|[Gg]anglios?\s+linf[aá]ticos?"
        else:
            pat = re.escape(org)
        pattern_parts.append(pat)
    pattern_parts.append(r"linfonodos?")

    organ_pattern = re.compile(
        r"\b(" + "|".join(pattern_parts) + r")\b",
        re.IGNORECASE,
    )
    # Tolerar 0+ whitespaces entre el órgano y la palabra clínica.
    post_patterns_regex = (
        r"(?:\s*)(?:" + "|".join(_NARRATIVE_POST_PATTERNS) + r")"
    )
    require_post_ctx = re.compile(
        r"(?i)\b(" + "|".join(pattern_parts) + r")\b" + post_patterns_regex
    )

    matches: list[tuple[int, str]] = []
    for m in organ_pattern.finditer(text):
        ctx_start = m.start()
        ctx_end = min(len(text), m.end() + 80)
        window = text[ctx_start:ctx_end]
        if require_post_ctx.search(window):
            raw_name = m.group(0)
            canon = _canonicalize_organ(raw_name)
            matches.append((m.start(), canon))

    if not matches:
        return []

    matches.sort(key=lambda x: x[0])
    deduped: list[tuple[int, str]] = []
    for pos, name in matches:
        if deduped and deduped[-1][0] == pos:
            continue
        deduped.append((pos, name))

    results: list[dict] = []
    for idx, (pos, organo) in enumerate(deduped):
        next_pos = deduped[idx + 1][0] if idx + 1 < len(deduped) else len(text)
        chunk = text[pos:next_pos]
        chunk = re.sub(r"\s+", " ", chunk).strip()
        if len(chunk) > 600:
            sent_end = chunk[:600].rfind(".")
            if sent_end > 100:
                chunk = chunk[: sent_end + 1]
            else:
                chunk = chunk[:600]
        if not chunk or len(chunk) < 20:
            continue
        results.append(
            {
                "organo": organo,
                "descripcion": chunk,
                "estado": classify_state(chunk),
                "orden": idx,
            }
        )
    return results


def segment_findings_smart(
    text: str, estudio: str = "", min_canonic: int = 5,
) -> list[dict]:
    """Canónico primero; narrativa solo si el canónico devuelve < min_canonic.

    Si el canónico no detecta nada, devuelve el fallback 'Gestación' sin
    activar la narrativa (es el comportamiento previo).

    Salvaguarda (2026-06-17, post-auditoría): si el `estudio` declarado en
    el DOCX es 'Gestacional' (o contiene 'estacional'), NO se activa la
    narrativa. Esto evita que un informe gestacional que menciona
    brevemente un órgano fetal (ej. 'Riñón de fetos presenta clara
    delimitación') pierda la clasificación 'Gestación' y se recategorice
    erróneamente como 'Riñón' fetal.

    La salvaguarda se basa en el `estudio` declarado (campo del DOCX) y no
    en el `organo='Gestación'` del fallback del parser, porque los
    abdominales con contenido narrativo (id=72, 112, 625, 709, 2334)
    también producen `organo='Gestación'` por el fallback canónico y DEBEN
    ser mejorados por la narrativa.
    """
    canonicos = segment_findings(text)
    if not canonicos:
        return canonicos
    if len(canonicos) >= min_canonic:
        return canonicos
    if "estacional" in (estudio or "").lower():
        return canonicos
    narrativos = segment_findings_narrative(text)
    return narrativos if narrativos else canonicos
