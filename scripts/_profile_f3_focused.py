"""Profile F3 refinado: extracción enfocada + análisis de ambigüedad."""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import text  # noqa: E402

from informes_vet import db  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Patrones con captura de valor (group 1 = valor)
# Cada patrón: (regex, atributo) → matchea en el contexto del órgano
VALUE_PATTERNS: dict[str, list[tuple[str, str]]] = {
    # Hígado
    "Hígado": [
        # tamaño: "tamaño X" o "X de tamaño"
        (r"tama[ñn]o\s+(?:se\s+encuentra\s+|esta\s+|se\s+observa\s+)?(normal|dentro\s+de\s+rango|conservado|levemente\s+aumentad[oa]|moderadamente\s+aumentad[oa]|severamente\s+aumentad[oa]|disminuid[oa]|aumentad[oa]|reducid[oa]|m[áa]s?\s+grande|menor)", "tamaño"),
        (r"(normal|conservado|levemente\s+aumentad[oa]|aumentad[oa]|disminuid[oa])\s+(?:de\s+)?tama[ñn]o", "tamaño"),
        # márgenes
        (r"m[áa]rgenes\s+(lisos|irregulares|conservados|mal\s+definidos|regulares|redondeados)", "márgenes"),
        (r"(lisos|irregulares|conservados|mal\s+definidos|regulares|redondeados)\s+m[áa]rgenes", "márgenes"),
        # bordes
        (r"bordes\s+(aguzados|redondeados|regulares|irregulares|lisos|conservados|mal\s+definidos)", "bordes"),
        # ecogenicidad
        (r"ecogenicidad\s+(hipoecoica|hiperecoica|conservada|normal|levemente\s+aumentada|levemente\s+disminuida|aumentada|disminuida|ecog[eé]nica)", "ecogenicidad"),
        (r"(hipoecoic[oa]|hiperecoic[oa]|normoecoic[oa])\s+(?:de\s+ecogenicidad\s+)?(?:par[eé]nquima|parenquimatosa)?", "ecogenicidad"),
        # granulado
        (r"granulad[oa]\s+(fino|grueso)", "granulado"),
        (r"(fino|grueso)\s+granulad", "granulado"),
        # arquitectura
        (r"arquitectura\s+(conservada|alterada|preservada|homog[eé]nea|heterog[eé]nea)", "arquitectura"),
        # patrón vascular
        (r"patr[óo]n\s+vascular\s+(conservado|alterado|aumentado|disminuido|preservado)", "patron_vascular"),
        (r"vasculatura\s+(conservada|alterada|aumentada|disminuida|preservada)", "patron_vascular"),
    ],
    # Riñones
    "Riñones": [
        (r"(?:aspecto\s+)?(ovalad[oa]s?|reniformes?|redondead[oa]s?|irregulares?|globoso[s]?)", "forma"),
        (r"tama[ñn]o\s+(normal|dentro\s+de\s+rango|conservado|levemente\s+aumentad[oa]|aumentad[oa]|disminuid[oa]|reducid[oa])", "tamaño"),
        (r"bordes\s+(regulares|irregulares|levemente\s+irregulares|lisos|conservados)", "bordes"),
        (r"ecogenicidad\s+(?:cortical\s+)?(hipoecoica|hiperecoica|conservada|normal|levemente\s+hiperecoica|levemente\s+hipoecoica|discretamente\s+hiperecoica|aumentada|disminuida|adecuada)", "ecogenicidad_cortical"),
        (r"diferenciaci[óo]n\s+(c[óo]rtico[- ]?medular\s+)?(bien\s+definida|mal\s+definida|definida|adecuada|conservada|p[eé]rdida)", "diferenciacion_cm"),
        (r"relaci[óo]n\s+(c[óo]rtico[- ]?medular\s+)?(conservada|alterada|preservada|adecuada|invertida|aumentada|disminuida)", "relacion_cm"),
        (r"(?:sin\s+)?compromiso\s+p[ée]lvic[oa]\s*\.?\s*(presente|ausente|sin)", "compromiso_pelvico"),
        (r"pelvis\s+(?:renal\s+)?(dilatada|conservada|sin\s+dilataci[óo]n|comprometida)", "compromiso_pelvico"),
    ],
    # Vejiga
    "Vejiga": [
        (r"\b(semi\s+plet[óo]ric[oa]|plet[óo]ric[oa]|semi\s+depletad[oa]|depletad[oa]|distendida|replecci[óo]n\s+conservada|replecci[óo]n\s+conservado|vac[ií]a)\b", "replecion"),
        (r"contenido\s+(anecoico|hiperecoico|hipoecoico|homog[eé]neo|con\s+ecos|ecog[eé]nico|sedimento|cristales|mineralizado)", "contenido"),
        (r"(?:pared(es)?\s+con\s+|con\s+)?bordes\s+internos?\s+(regulares|irregulares|levemente\s+irregulares|lisos)", "bordes_internos"),
        (r"grosor\s+(conservado|levemente\s+aumentado|discretamente\s+aumentado|aumentado|moderadamente\s+aumentado|severamente\s+aumentado|normal|disminuido)", "grosor_pared"),
        (r"pared(es)?\s+(conservad[oa]s?|engrosad[oa]s?|aumentad[oa]s?)\s+de\s+grosor", "grosor_pared"),
    ],
    # Vesícula
    "Vesícula": [
        (r"\b(semi\s+distendida|distendida|plet[óo]ric[oa]|semi\s+plet[óo]ric[oa]|depletada|replecci[óo]n\s+conservada)\b", "distension"),
        (r"contenido\s+(anecoico|hiperecoico|hipoecoico|homog[eé]neo|con\s+ecos|ecog[eé]nico|barro\s+biliar|mineralizado|con\s+c[áa]lculos)", "contenido"),
        (r"bordes\s+internos?\s+(regulares|irregulares|levemente\s+irregulares|lisos)", "bordes_internos"),
        (r"grosor\s+(conservado|levemente\s+aumentado|discretamente\s+aumentado|aumentado|moderadamente\s+aumentado|severamente\s+aumentado|normal|disminuido)", "grosor_pared"),
    ],
    # Bazo
    "Bazo": [
        (r"tama[ñn]o\s+(normal|dentro\s+de\s+rango|conservado|levemente\s+aumentad[oa]|aumentad[oa]|disminuid[oa]|reducid[oa])", "tamaño"),
        (r"forma\s+(normal|conservada|caracter[ií]stica|conservado)", "forma"),
        (r"m[áa]rgenes\s+(lisos|irregulares|conservados|regulares|redondeados)", "márgenes"),
        (r"arquitectura\s+(conservada|alterada|heterog[eé]nea|homog[eé]nea|preservada)", "arquitectura"),
    ],
    # Próstata
    "Próstata": [
        (r"aspecto\s+(ovalad[oa]|bilobulad[oa]|globos[ao]|reniforme|normal|caracter[ií]stico|conservad[oa])", "aspecto"),
        (r"tama[ñn]o\s+(normal|dentro\s+de\s+rango|conservado|levemente\s+aumentad[oa]|moderadamente\s+aumentad[oa]|aumentad[oa]|disminuid[oa])", "tamaño"),
        (r"\b(hipoecoic[oa]|hiperecoic[oa]|ecogenicidad\s+conservada|ecog[eé]nic[oa])\b", "ecogenicidad"),
        (r"\b(homog[eé]ne[oa]|heterog[eé]ne[oa]|discretamente\s+heterog[eé]ne[oa])\b", "homogeneidad"),
    ],
    # Estómago
    "Estómago": [
        (r"\b(semi\s+distendid[oa]|distendid[oa]|repleci[óo]n\s+conservada|depletad[oa]|colapsad[oa]|vac[ií]o|lleno)\b", "distension"),
        (r"contenido\s+(alimenticio|alimenticio\s+y\s+gas|gas|mucos[oa]|l[ií]quido|alimenticio\s+y\s+mucos[oa]|predominantemente\s+\w+|mixto)", "contenido"),
        (r"(?:pared(es)?\s+)?estratificad[oa]s?\s+(?:de\s+|con\s+)?grosor\s+(conservado|levemente\s+aumentado|discretamente\s+aumentado|aumentado|moderadamente\s+aumentado|engrosad[oa]s?)", "grosor_pared"),
        (r"grosor\s+(conservado|levemente\s+aumentado|discretamente\s+aumentado|aumentado|moderadamente\s+aumentado|severamente\s+aumentado)", "grosor_pared"),
        (r"peristaltismo\s+(normal|aumentado|disminuido|conservado|discretamente\s+aumentado|preservado|ausente|ausente)", "peristaltismo"),
    ],
    # Intestino
    "Intestino": [
        (r"\b(distendid[oa]s?|marcadamente\s+distendid[oa]s?|semi\s+distendid[oa]s?|repleci[óo]n\s+conservada|colapsad[oa]s?|planas?)\b", "distension"),
        (r"contenido\s+(mucos[oa]|alimenticio|fecal|con\s+predominio|heces?|patr[óo]n\s+\w+|abundante)", "contenido"),
        (r"(?:pared(es)?\s+)?estratificad[oa]s?\s+(?:de\s+|con\s+)?grosor\s+(conservado|levemente\s+aumentado|discretamente\s+aumentado|aumentado|moderadamente\s+aumentado|engrosad[oa]s?)", "grosor_pared"),
        (r"grosor\s+(conservado|levemente\s+aumentado|discretamente\s+aumentado|aumentado|moderadamente\s+aumentado|severamente\s+aumentado)", "grosor_pared"),
        (r"peristaltismo\s+(normal|aumentado|disminuido|conservado|discretamente\s+aumentado|preservado|ausente|ausente)", "peristaltismo"),
    ],
    # Páncreas
    "Páncreas": [
        (r"\b(hipoecoic[oa]|hiperecoic[oa]|ecogenicidad\s+conservada|ecog[eé]nic[oa]|normoecoic[oa])\b", "ecogenicidad"),
        (r"tama[ñn]o\s+(normal|conservado|aumentad[oa]|disminuid[oa]|dentro\s+de\s+rango)", "tamaño"),
    ],
    # Adrenales
    "Adrenales": [
        (r"tama[ñn]o\s+(normal|conservado|aumentad[oa]|disminuid[oa]|dentro\s+de\s+rango)", "tamaño"),
        (r"\b(forma|arquitectura)\s+(normal|conservad[oa])\b", "forma"),
    ],
    # Linfonodos
    "Linfonodos": [
        (r"tama[ñn]o\s+(normal|conservado|aumentad[oa]|disminuid[oa]|dentro\s+de\s+rango|levemente\s+aumentad[oa])", "tamaño"),
        (r"\b(oval(es|ados)?|redond[oa]s?|forma\s+normal|forma\s+conservada)\b", "forma"),
        (r"\b(hipoecoic[oa]|hiperecoic[oa]|ecogenicidad\s+conservada|ecogenicidad\s+aumentada|ecogenicidad\s+disminuida)\b", "ecogenicidad"),
        (r"\b(homog[eé]ne[oa]s?|heterog[eé]ne[oa]s?)\b", "homogeneidad"),
    ],
    # Útero
    "Útero": [
        (r"tama[ñn]o\s+(normal|conservado|aumentad[oa]|disminuid[oa]|levemente\s+aumentad[oa]|moderadamente\s+aumentad[oa])", "tamaño"),
        (r"contenido\s+(anecoico|hiperecoico|ecog[eé]nico|homog[eé]neo|heterog[eé]neo|l[ií]quido)", "contenido"),
        (r"pared(es)?\s+(conservad[oa]|aumentad[oa]|engrosad[oa]|disminuid[oa])", "grosor_pared"),
    ],
    # Ovarios
    "Ovarios": [
        (r"tama[ñn]o\s+(normal|conservado|aumentad[oa]|disminuid[oa]|levemente\s+aumentad[oa])", "tamaño"),
        (r"\b(oval(es|ados)?|redond[oa]s?|forma\s+normal|forma\s+conservada)\b", "forma"),
    ],
    # Testículos
    "Testículos": [
        (r"tama[ñn]o\s+(normal|conservado|aumentad[oa]|disminuid[oa]|dentro\s+de\s+rango)", "tamaño"),
        (r"\b(forma|arquitectura)\s+(normal|conservad[oa])\b", "forma"),
        (r"\b(hipoecoic[oa]|hiperecoic[oa]|ecogenicidad\s+conservada|ecog[eé]nic[oa])\b", "ecogenicidad"),
        (r"\b(homog[eé]ne[oa]s?|heterog[eé]ne[oa]s?)\b", "homogeneidad"),
    ],
    # Gestación
    "Gestación": [
        (r"(?:al\s+menos\s+|m[áa]s\s+de\s+|aproximadamente\s+)?(\d+)\s+(?:a\s+\d+\s+)?feto[s]?", "fetos"),
        (r"(\d+)\s+cr[ií]as?\b", "fetos"),
        (r"pre[ñn]ez\s+(confirmada|presente|diagnosticada|ausente|sospechada)", "preñez"),
        (r"\b(gestante|pre[ñn]ada|pre[ñn]ez\s+confirmada|gestaci[óo]n\s+activa|gestaci[óo]n\s+en\s+curso)\b", "preñez"),
    ],
}


def main() -> None:
    eng = db.get_engine("sqlite", ROOT)
    with eng.begin() as conn:
        rows = conn.execute(text("SELECT organo, descripcion FROM hallazgos")).all()
    total = len(rows)
    organo_to_descs: dict[str, list[str]] = defaultdict(list)
    for org, desc in rows:
        organo_to_descs[org].append(desc)

    # ============== TOP 100 VALORES POR (organo, atributo) ==============
    print("# TOP 30 VALORES OBSERVADOS POR (ORGANO, ATRIBUTO)\n")
    all_coverage: list[tuple[str, str, int, int, float]] = []
    for organo, patterns in VALUE_PATTERNS.items():
        for attr in sorted({a for _, a in patterns}):
            attr_patterns = [(p, a) for p, a in patterns if a == attr]
            compiled = [(re.compile(p, re.IGNORECASE), a) for p, a in attr_patterns]
            value_counter: Counter = Counter()
            n_match = 0
            for desc in organo_to_descs[organo]:
                matched = False
                for p, _ in compiled:
                    m = p.search(desc)
                    if m:
                        # value is group(1), clipped
                        v = (m.group(1) or "").strip()
                        if v:
                            value_counter[v] += 1
                        matched = True
                        break
                if matched:
                    n_match += 1
            n_organo = len(organo_to_descs[organo])
            pct = 100.0 * n_match / n_organo if n_organo else 0
            all_coverage.append((organo, attr, n_match, n_organo, pct))
            if value_counter:
                print(f"### {organo}.{attr}  ({n_match}/{n_organo} = {pct:.1f}%)")
                for v, n in value_counter.most_common(30):
                    print(f"  {n:5}  {v!r}")
                print()
    print()

    # ============== RESUMEN DE COBERTURA POR ATRIBUTO ==============
    print("\n## COBERTURA POR ATRIBUTO (sumando todos los órganos)\n")
    attr_total: dict[str, int] = defaultdict(int)
    attr_match: dict[str, int] = defaultdict(int)
    for organo, attr, n_match, n_organo, pct in all_coverage:
        attr_match[attr] += n_match
        attr_total[attr] += n_organo
    print(f"  {'atributo':25} {'match':>7} / {'total':>6}   {'pct':>6}   status")
    for attr in sorted(attr_match):
        m, t = attr_match[attr], attr_total[attr]
        pct = 100 * m / t if t else 0
        status = "✅" if pct >= 70 else ("⚠️" if pct >= 30 else "❌")
        print(f"  {attr:25} {m:7} / {t:6} {pct:6.1f}%   {status}")

    # ============== ANÁLISIS DE AMBIGÜEDAD ==============
    print("\n## ANÁLISIS DE AMBIGÜEDAD\n")
    # 1) "tamaño" aparece en casi todos los órganos. ¿Cuántas veces se repite
    #    la palabra "tamaño" en descripciones de un órgano donde NO es atributo?
    # 2) "conservado/a" es muy polisémico.
    # 3) Bordes vs bordes_internos.

    # Misma palabra "tamaño" en Hígado (size attr válido) vs en otros órganos
    # donde "tamaño" puede ser ruido.
    print("### 'tamaño' como keyword polisémico")
    for organo in ["Hígado", "Riñones", "Bazo", "Próstata", "Linfonodos", "Testículos"]:
        n_with_tam = sum(1 for d in organo_to_descs[organo] if re.search(r"\btama[ñn]o\b", d, re.I))
        n_organo = len(organo_to_descs[organo])
        print(f"  {organo}: {n_with_tam}/{n_organo} ({100*n_with_tam/n_organo:.1f}%) mencionan 'tamaño'")

    print("\n### 'conservado/a' como polisémico")
    for organo in ["Hígado", "Riñones", "Vejiga", "Bazo", "Páncreas", "Adrenales", "Linfonodos", "Útero", "Ovarios", "Testículos"]:
        n_with_cons = sum(1 for d in organo_to_descs[organo] if re.search(r"\bconservad[oa]\b", d, re.I))
        n_organo = len(organo_to_descs[organo])
        print(f"  {organo}: {n_with_cons}/{n_organo} ({100*n_with_cons/n_organo:.1f}%) mencionan 'conservado/a'")

    # 'bordes' vs 'bordes_internos'
    print("\n### 'bordes' / 'bordes_internos' / 'pared(es)'")
    for organo in ["Vejiga", "Vesícula"]:
        n_bordes_int = sum(1 for d in organo_to_descs[organo] if re.search(r"\bbordes?\s+intern", d, re.I))
        n_pared = sum(1 for d in organo_to_descs[organo] if re.search(r"\bpared(es)?\s+de\s+borde", d, re.I))
        n_organo = len(organo_to_descs[organo])
        print(f"  {organo}: bordes_internos={n_bordes_int}, pared(es) de borde={n_pared} (total={n_organo})")

    # ============== ATRIBUTOS QUE REQUIEREN REGEX ESPECÍFICA ==============
    print("\n## ATRIBUTOS QUE REQUIEREN REGEX ESPECÍFICA\n")
    # Aquellos con cobertura <50% en el catálogo original
    LOW_COV = [r for r in all_coverage if r[4] < 50]
    print(f"Pares con cobertura <50%: {len(LOW_COV)}")
    for organo, attr, n_match, n_organo, pct in LOW_COV:
        print(f"  {organo}.{attr}: {pct:.1f}% ({n_match}/{n_organo}) — requiere regex más permisiva")

    # ============== ÓRDEN DE IMPLEMENTACIÓN ==============
    print("\n## PROPUESTA DE ORDEN DE IMPLEMENTACIÓN (por cobertura esperada)\n")
    # Score = pct * n_hallazgos / 10000  (ponderado por tamaño del órgano)
    scored = []
    for organo, attr, n_match, n_organo, pct in all_coverage:
        if pct >= 50:
            score = pct * n_organo / 100.0  # absoluto de matches esperados
            scored.append((score, organo, attr, n_match, n_organo, pct))
    scored.sort(key=lambda x: -x[0])
    print(f"  {'rank':>4} {'organo':12} {'atributo':25} {'matches_esperados':>17}  pct")
    for i, (s, organo, attr, n_match, n_organo, pct) in enumerate(scored, 1):
        print(f"  {i:>4} {organo:12} {attr:25} {n_match:>10} / {n_organo:>5}  ({pct:.0f}%)")


if __name__ == "__main__":
    main()