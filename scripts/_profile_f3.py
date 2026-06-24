"""Profile de 27,866 hallazgos vs catálogo de 22 atributos × 57 pares.

Genera salida a stdout que se guarda en docs/F3_ATTRIBUTE_DISCOVERY.md.
No modifica silver.db ni crea tablas.
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Permitir imports sin instalar paquete
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import text  # noqa: E402

from informes_vet import db  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# =============================================================================
# CATÁLOGO: para cada par (organo, atributo) del Anexo A defino las regex
# que matchearían al atributo en la descripcion. Las regex son permisivas
# (lowercase + tolerant de typos) — el objetivo es ESTIMAR cobertura, no
# extraer valores exactos.
# =============================================================================
ATTR_PATTERNS: dict[tuple[str, str], list[str]] = {
    # Hígado (7)
    ("Hígado", "tamaño"):          [r"\btama[ñn]o\b"],
    ("Hígado", "márgenes"):        [r"\bm[áa]rgenes\b"],
    ("Hígado", "bordes"):          [r"\bbordes\b"],
    ("Hígado", "ecogenicidad"):    [r"\becogenicidad\b", r"\becoic[oa]\b", r"\bhiperecoic", r"\bhipoecoic"],
    ("Hígado", "granulado"):       [r"\bgranulad[oa]\b", r"\bgranular\b"],
    ("Hígado", "arquitectura"):    [r"\barquitectura\b"],
    ("Hígado", "patron_vascular"): [r"\bpatr[óo]n\s+vascular\b", r"\bvasculatura?\b"],
    # Riñones (7)
    ("Riñones", "forma"):          [r"\bforma\b", r"\baspecto\s+(ovalad|reniform|redondead|irregular|globoso)"],
    ("Riñones", "tamaño"):         [r"\btama[ñn]o\b"],
    ("Riñones", "bordes"):         [r"\bbordes\b"],
    ("Riñones", "ecogenicidad_cortical"): [r"\becogenicidad\s+(cortical|de\s+la\s+corteza|c[óo]rtex)", r"\becoic[oa]\b", r"\bhiperecoic", r"\bhipoecoic"],
    ("Riñones", "diferenciacion_cm"): [r"\bdiferenciaci[óo]n\s+(c[óo]rtico|cortico)\s*[-]?\s*medul", r"\bdiferenciaci[óo]n\s+cm\b", r"\bc[óo]rtex\s+y\s+m[ée]dula\b"],
    ("Riñones", "relacion_cm"):    [r"\brelaci[óo]n\s+(cort|c[óo]rtex|c[óo]rtico|cm)\b", r"\brelaci[óo]n\s+c[óo]rtico[- ]?medular", r"\brelaci[óo]n\s+adecuada"],
    ("Riñones", "compromiso_pelvico"): [r"\bcompromiso\s+p[ée]lvic", r"\bpelvis\s+(dilatad|comprometid)", r"\bhidronefrosis", r"\bectasia\s+p[ée]lvic"],
    # Vejiga (4)
    ("Vejiga", "replecion"):       [r"\bplet[óo]ric[ao]\b", r"\bsemi\s*-?\s*plet[óo]ric[ao]\b", r"\bde\s*-?\s*pletad[oa]\b", r"\bdistendid[oa]\b", r"\breplecci[óo]n\b", r"\bretenci[óo]n"],
    ("Vejiga", "contenido"):       [r"\bcontenido\b", r"\banecoic", r"\bhiperecoic", r"\bhomog[ée]ne[oa]\b", r"\bsediment", r"\bsedimento"],
    ("Vejiga", "bordes_internos"): [r"\bborde(s)?\s+intern", r"\bpared(es)?\s+de\s+borde"],
    ("Vejiga", "grosor_pared"):    [r"\bgrosor\b", r"\bpared(es)?\s+de\s+grosor", r"\bpared(es)?\s+(conservad|engrosad|aumentad)"],
    # Vesícula (4)
    ("Vesícula", "distension"):    [r"\bdistendid[ao]\b", r"\bsemi\s*-?\s*distendid[ao]\b", r"\bplet[óo]ric[ao]\b", r"\bde\s*-?\s*pletad[oa]\b", r"\bdepletad[oa]\b"],
    ("Vesícula", "contenido"):     [r"\bcontenido\b", r"\banecoic", r"\bhiperecoic", r"\bcon\s+ecos\b", r"\bhomog[ée]ne[oa]\b", r"\bbarro\s+biliar", r"\bc[áa]lcul[oa]s?\b"],
    ("Vesícula", "bordes_internos"): [r"\bborde(s)?\s+intern", r"\bpared(es)?\s+de\s+borde"],
    ("Vesícula", "grosor_pared"):  [r"\bgrosor\b", r"\bpared(es)?\s+de\s+grosor", r"\bpared(es)?\s+(conservad|engrosad|aumentad)"],
    # Bazo (4)
    ("Bazo", "tamaño"):            [r"\btama[ñn]o\b"],
    ("Bazo", "forma"):             [r"\bforma\b"],
    ("Bazo", "márgenes"):          [r"\bm[áa]rgenes\b"],
    ("Bazo", "arquitectura"):      [r"\barquitectura\b"],
    # Próstata (4)
    ("Próstata", "aspecto"):       [r"\baspecto\b"],
    ("Próstata", "tamaño"):        [r"\btama[ñn]o\b"],
    ("Próstata", "ecogenicidad"):  [r"\becogenicidad\b", r"\bhipoecoic", r"\bhiperecoic"],
    ("Próstata", "homogeneidad"):  [r"\bhomog[ée]ne[oa]\b", r"\bheterog[ée]ne[oa]\b"],
    # Estómago (4)
    ("Estómago", "distension"):    [r"\bdistendid[oa]\b", r"\bsemi\s*-?\s*distendid[oa]\b", r"\bplet[óo]ric[oa]\b", r"\brepleci[óo]n\s+conservad", r"\bdepletad[oa]\b", r"\bvac[íi]o\b", r"\bcolapsad[oa]\b"],
    ("Estómago", "contenido"):     [r"\bcontenido\b", r"\balimenticio\b", r"\bgas\b", r"\bmucos[oa]\b", r"\bl[ií]quid[oa]\b"],
    ("Estómago", "grosor_pared"):  [r"\bpared(es)?\s+estratificad", r"\bgrosor\b", r"\bpared(es)?\s+(conservad|engrosad|aumentad)"],
    ("Estómago", "peristaltismo"): [r"\bperistaltismo\b"],
    # Intestino (4)
    ("Intestino", "distension"):   [r"\bdistendid[oa]\b", r"\bmarcadamente\s+distendid", r"\bsemi\s*-?\s*distendid", r"\brepleci[óo]n\s+conservad", r"\bcolapsad[oa]\b", r"\bplana?\b"],
    ("Intestino", "contenido"):    [r"\bcontenido\b", r"\bmucos[oa]\b", r"\balimenticio\b", r"\bfecal\b", r"\bpredominio\b", r"\bpatr[óo]n\s+mucos", r"\bpatr[óo]n\s+alimenticio", r"\bheces?\b"],
    ("Intestino", "grosor_pared"): [r"\bpared(es)?\s+estratificad", r"\bgrosor\b"],
    ("Intestino", "peristaltismo"): [r"\bperistaltismo\b"],
    # Páncreas (2)
    ("Páncreas", "ecogenicidad"):  [r"\becogenicidad\b", r"\bhipoecoic", r"\bhiperecoic", r"\bconservad[oa]\b"],
    ("Páncreas", "tamaño"):        [r"\btama[ñn]o\b", r"\bconservad[oa]\b"],
    # Adrenales (2)
    ("Adrenales", "tamaño"):       [r"\btama[ñn]o\b", r"\bconservad[oa]\b"],
    ("Adrenales", "forma"):        [r"\bforma\b", r"\barquitectura\b"],
    # Linfonodos (4)
    ("Linfonodos", "tamaño"):      [r"\btama[ñn]o\b", r"\baumentad[oa]\b", r"\bconservad[oa]\b"],
    ("Linfonodos", "forma"):       [r"\bforma\b", r"\boval(es|ados)?\b", r"\bovalad[oa]s?\b", r"\bredond[oa]s?\b"],
    ("Linfonodos", "ecogenicidad"): [r"\becogenicidad\b", r"\bhipoecoic", r"\bhiperecoic"],
    ("Linfonodos", "homogeneidad"): [r"\bhomog[ée]ne[oa]s?\b", r"\bheterog[ée]ne[oa]s?\b"],
    # Útero (3)
    ("Útero", "tamaño"):           [r"\btama[ñn]o\b", r"\baumentad[oa]\b", r"\bconservad[oa]\b"],
    ("Útero", "contenido"):        [r"\bcontenido\b", r"\banecoic", r"\bhiperecoic", r"\bhomog[ée]ne[oa]\b", r"\bheterog[ée]ne[oa]\b", r"\bl[ií]quid[oa]\b"],
    ("Útero", "grosor_pared"):     [r"\bpared(es)?\b", r"\bgrosor\b"],
    # Ovarios (2)
    ("Ovarios", "tamaño"):         [r"\btama[ñn]o\b", r"\baumentad[oa]\b", r"\bconservad[oa]\b"],
    ("Ovarios", "forma"):          [r"\bforma\b", r"\boval(es|ados)?\b", r"\bredond[oa]s?\b"],
    # Testículos (4)
    ("Testículos", "tamaño"):      [r"\btama[ñn]o\b", r"\bconservad[oa]\b"],
    ("Testículos", "forma"):       [r"\bforma\b", r"\bconservad[oa]\b"],
    ("Testículos", "ecogenicidad"): [r"\becogenicidad\b", r"\bhipoecoic", r"\bhiperecoic"],
    ("Testículos", "homogeneidad"): [r"\bhomog[ée]ne[oa]s?\b", r"\bheterog[ée]ne[oa]s?\b"],
    # Gestación (2)
    ("Gestación", "fetos"):        [r"\bfetos?\b", r"\dal\s+menos\s+\d+\s+feto", r"\d+\s+fetos?\b", r"\d+\s+cr[íi]as"],
    ("Gestación", "preñez"):       [r"\bpre[ñn]ez\b", r"\bgestaci[óo]n\b", r"\bgestante\b"],
}

# Atributos organo-AGNÓSTICOS (los 22 nombres únicos)
ATTR_NAMES = sorted({a for _, a in ATTR_PATTERNS.keys()})
print(f"Atributos organo-agnósticos (22 esperados): {len(ATTR_NAMES)}")
for a in ATTR_NAMES:
    print(f"  {a!r}")


def main() -> None:
    eng = db.get_engine("sqlite", ROOT)
    with eng.begin() as conn:
        # Cargar todos los hallazgos (27.866)
        rows = conn.execute(text("SELECT organo, descripcion FROM hallazgos")).all()
    total = len(rows)
    print(f"\nTotal hallazgos: {total}")

    # Frecuencia por órgano
    organo_counts: Counter = Counter()
    organo_to_descs: dict[str, list[str]] = defaultdict(list)
    for org, desc in rows:
        organo_counts[org] += 1
        organo_to_descs[org].append(desc)

    # Cobertura por par
    coverage: list[tuple[str, str, int, int, float]] = []
    for (organo, attr), patterns in ATTR_PATTERNS.items():
        compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
        n_match = 0
        for desc in organo_to_descs[organo]:
            if any(p.search(desc) for p in compiled):
                n_match += 1
        n_organo = organo_counts[organo]
        pct = 100.0 * n_match / n_organo if n_organo else 0
        coverage.append((organo, attr, n_match, n_organo, pct))

    # Top valores por atributo (tokenización naive)
    # Para cada atributo global, encontrar las palabras que más siguen al keyword
    # en la descripcion
    top_values: dict[str, Counter] = defaultdict(Counter)
    for org, desc in rows:
        for _, attr, patterns in [(None, a, [r"\btama[ñn]o\b", r"\bforma\b", r"\becogenicidad\b", r"\bhomog[ée]ne[oa]s?\b", r"\bheterog[ée]ne[oa]s?\b", r"\bbordes\b", r"\bm[áa]rgenes\b", r"\bgranulad[oa]\b", r"\barquitectura\b", r"\bpatr[óo]n\s+vascular\b", r"\bvasculatura?\b", r"\bcontenido\b", r"\bgrosor\b", r"\bperistaltismo\b", r"\bfetos?\b", r"\bpre[ñn]ez\b"]) for a in [attr]]:
            for p in patterns:
                m = re.search(p, desc, re.IGNORECASE)
                if m:
                    # Tomar siguientes 3 palabras
                    after = desc[m.end():m.end()+80]
                    # Filtrar palabras de parada
                    words = re.findall(r"\b\w+\b", after.lower())[:3]
                    value = " ".join(w for w in words if len(w) > 2)[:40]
                    if value:
                        top_values[attr][value] += 1
                    break

    # Salida
    print("\n" + "="*70)
    print("F3 ATTRIBUTE DISCOVERY — RESULTADOS")
    print("="*70)
    print()
    print("## Frecuencia de cada órgano")
    for org, n in organo_counts.most_common():
        pct = 100.0 * n / total
        print(f"  {org!r:25} {n:6} ({pct:5.2f}%)")
    print()
    print("## Frecuencia de cada atributo candidato por órgano")
    print(f"  {'organo':15} {'atributo':25} {'match':>6} / {'total':>5}   {'pct':>6}")
    for r in sorted(coverage, key=lambda x: (-x[4], x[0], x[1])):
        status = "✅" if r[4] >= 50 else ("⚠️" if r[4] >= 10 else "❌")
        print(f"  {r[0]:13} {r[1]:25} {r[2]:6} / {r[3]:5} {r[4]:6.1f}%  {status}")
    print()
    print("## Top 10 valores observados para cada atributo")
    for attr in ATTR_NAMES:
        top = top_values[attr].most_common(10)
        if not top:
            continue
        print(f"  {attr}:")
        for v, n in top:
            print(f"    {n:5}  {v!r}")
    print()
    print("## Resumen")
    ok = sum(1 for r in coverage if r[4] >= 50)
    mid = sum(1 for r in coverage if 10 <= r[4] < 50)
    low = sum(1 for r in coverage if r[4] < 10)
    print(f"  Pares con cobertura >=50%: {ok}/{len(coverage)}")
    print(f"  Pares con cobertura 10-50%: {mid}/{len(coverage)}")
    print(f"  Pares con cobertura <10%: {low}/{len(coverage)}")
    total_hallazgos_with_attr = sum(r[2] for r in coverage)
    print(f"  Estimación: {total_hallazgos_with_attr} matches en {total} hallazgos")
    print(f"  Cobertura global bruta: {100*total_hallazgos_with_attr/(total*len(coverage)):.1f}% matches/hallazgo")


if __name__ == "__main__":
    main()