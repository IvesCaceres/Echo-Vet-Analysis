"""F3.1 — Cobertura de atributos clínicos sobre el corpus RAW.

No escribe en silver.db. Solo profiling.
"""
from __future__ import annotations

import io
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sqlalchemy import text  # noqa: E402

from informes_vet import db  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Catálogo clínico oficial — fuente primaria
CLINICAL_CATALOG: dict[str, dict[str, list[str]]] = {
    "Vejiga": {
        "replecion":              [r"\breplecci[oó]n\b", r"\bplet[oó]ric[ao]\b", r"\bsemi\s*-?\s*plet[oó]ric[ao]\b", r"\bdepletad[oa]\b", r"\bdistendid[oa]\b", r"\bvac[ií]o\b", r"\bvac[ií]a\b", r"\bretenci[oó]n\b"],
        "contenido":              [r"\bcontenido\b", r"\banecoic[oa]?\b", r"\bhiperecoic[oa]?\b", r"\bhomog[ée]ne[oa]\b", r"\bsediment", r"\bgranular\b", r"\bpuntiform"],
        "homogeneidad_contenido": [r"\bcontenido\s+(homog[ée]ne[oa]|heterog[ée]ne[oa])", r"\bhomog[ée]ne[oa]\b", r"\bheterog[ée]ne[oa]\b"],
        "bordes_internos":        [r"\bbordes?\s+intern", r"\bpared\s+de\s+bordes?"],
        "grosor_pared":           [r"\bgrosor\b", r"\bpared(es)?\s+(conservad|engrosad|aumentad)", r"\bpared(es)?\s+de\s+grosor"],
    },
    "Próstata": {
        "forma":         [r"\bforma\b", r"\baspecto\s+(ovalad|reniform|redondead)"],
        "lobulacion":    [r"\blobulad[oa]?\b", r"\bbilobulad[oa]?\b"],
        "tamaño":        [r"\btama[ñn]o\b"],
        "ecogenicidad":  [r"\becogenicidad\b", r"\bhipoecoic[oa]?\b", r"\bhiperecoic[oa]?\b"],
        "homogeneidad":  [r"\bhomog[ée]ne[oa]s?\b", r"\bheterog[ée]ne[oa]s?\b"],
    },
    "Riñones": {
        "forma":                       [r"\bforma\b", r"\baspecto\s+(ovalad|reniform|redondead|irregular|globoso)"],
        "tamaño":                      [r"\btama[ñn]o\b"],
        "bordes":                      [r"\bbordes\b"],
        "ecogenicidad_cortical":       [r"\becogenicidad\s+(cortical|de\s+la\s+corteza|c[oó]rtex)", r"\bhipoecoic[oa]?\b", r"\bhiperecoic[oa]?\b", r"\becoic[oa]?\b"],
        "diferenciacion_corticomedular":[r"\bdiferenciaci[oó]n\s+(c[oó]rtico|cortico)\s*[-]?\s*medul", r"\bdiferenciaci[oó]n\s+cm\b", r"\bc[oó]rtex\s+y\s+m[ée]dula\b"],
        "relacion_corticomedular":     [r"\brelaci[oó]n\s+(cort|c[oó]rtex|c[oó]rtico|cm)\b", r"\brelaci[oó]n\s+c[oó]rtico[- ]?medular", r"\brelaci[oó]n\s+adecuada", r"\brelaci[oó]n\s+c[oó]rtico\s+medular\s+adecuada"],
        "compromiso_pelvico":          [r"\bcompromiso\s+p[ée]lvic", r"\bpelvis\s+(dilatad|comprometid)", r"\bhidronefrosis", r"\bectasia\s+p[ée]lvic"],
    },
    "Bazo": {
        "tamaño":       [r"\btama[ñn]o\b"],
        "forma":        [r"\bforma\b"],
        "margenes":     [r"\bm[áa]rgenes\b"],
        "arquitectura": [r"\barquitectura\b"],
    },
    "Estómago": {
        "distension":            [r"\bdistendid[oa]\b", r"\bsemi\s*-?\s*distendid[oa]\b", r"\bplet[oó]ric[ao]\b", r"\bcolapsad[oa]\b", r"\bvac[ií]o\b"],
        "contenido":             [r"\bcontenido\b", r"\balimenticio\b", r"\bgas\b", r"\bmucos[oa]\b", r"\bl[ií]quid[oa]\b"],
        "estratificacion_pared": [r"\bpared(es)?\s+estratificad"],
        "grosor_pared":          [r"\bgrosor\b", r"\bpared(es)?\s+(conservad|engrosad|aumentad)", r"\bpared(es)?\s+de\s+grosor"],
    },
    "Hígado": {
        "tamaño":          [r"\btama[ñn]o\b"],
        "margenes":        [r"\bm[áa]rgenes\b"],
        "bordes":          [r"\bbordes\b"],
        "ecogenicidad":    [r"\becogenicidad\b", r"\bhipoecoic[oa]?\b", r"\bhiperecoic[oa]?\b", r"\becoic[oa]?\b"],
        "granulado":       [r"\bgranulad[oa]\b", r"\bgranular\b"],
        "arquitectura":    [r"\barquitectura\b"],
        "patron_vascular": [r"\bpatr[óo]n\s+vascular\b", r"\bvasculatura?\b"],
    },
    "Vesícula": {
        "distension":      [r"\bdistendid[oa]\b", r"\bsemi\s*-?\s*distendid[oa]\b", r"\bplet[oó]ric[ao]\b", r"\bdepletad[oa]\b"],
        "contenido":       [r"\bcontenido\b", r"\banecoic[oa]?\b", r"\bhiperecoic[oa]?\b", r"\bhomog[ée]ne[oa]\b", r"\bbarro\s+biliar", r"\bc[áa]lcul[oa]s?\b", r"\bsediment"],
        "bordes_internos": [r"\bbordes?\s+intern"],
        "grosor_pared":    [r"\bgrosor\b", r"\bpared(es)?\s+(conservad|engrosad|aumentad)", r"\bpared(es)?\s+de\s+grosor"],
    },
    "Intestino_duodeno_yeyuno": {
        "contenido":             [r"\bcontenido\b", r"\bmucos[oa]\b", r"\balimenticio\b", r"\bfecal\b", r"\bpredominio\b", r"\bpatr[óo]n\s+mucos", r"\bpatr[óo]n\s+alimenticio", r"\bheces?\b"],
        "grosor_pared":          [r"\bgrosor\b", r"\bpared(es)?\s+(conservad|engrosad|aumentad)", r"\bpared(es)?\s+de\s+grosor"],
        "estratificacion_pared": [r"\bpared(es)?\s+estratificad"],
    },
    "Intestino_peristaltismo": {
        "peristaltismo": [r"\bperistaltismo\b"],
    },
    "Intestino_colon": {
        "contenido": [r"\bcontenido\b", r"\bmucos[oa]\b", r"\balimenticio\b", r"\bfecal\b", r"\bheces?\b", r"\bpredominio"],
        "paredes":    [r"\bpared(es)?\s+(conservad|engrosad|aumentad)", r"\bpared(es)?\s+de\s+grosor", r"\bgrosor\b"],
    },
    "Páncreas": {
        "preservacion":          [r"\bpreservad[oa]\b", r"\bconservad[oa]\b", r"\bn[oó]rmal\b", r"\bno\s+se\s+evalu[oó]", r"\bno\s+evaluad[oa]"],
        "aspecto_peripancreatico":[r"\bperipancre[aá]tic", r"\bgrasa\s+peripancre[aá]tic", r"\bpancreatitis", r"\binflamaci[oó]n\s+pancre[aá]tic"],
    },
    "Adrenales": {
        "forma":        [r"\bforma\b"],
        "tamaño":       [r"\btama[ñn]o\b", r"\bconservad[oa]\b"],
        "arquitectura": [r"\barquitectura\b"],
    },
    "Linfonodos": {
        "presencia":  [r"\bpresente\b", r"\bpresentes\b", r"\bse\s+observ", r"\bausente\b", r"\bausentes\b", r"\bno\s+se\s+observ", r"\bvisualiz"],
        "compromiso": [r"\bcomprometid[oa]s?\b", r"\breactiv[oa]s?\b", r"\bnormal\b", r"\bconservad[oa]s?\b"],
    },
    "Cavidad abdominal": {
        "liquido_libre": [r"\bl[ií]quido\s+libre\b", r"\bascitis\b", r"\bderrame\b", r"\bpresencia\s+de\s+l[ií]quido"],
        "masas":         [r"\bmasa\b", r"\bmasas\b", r"\btumor\b", r"\bneoplasia\b", r"\blesi[oó]n\s+(ocupante|s[oó]lida|qu[ií]stic)"],
    },
}

# Órganos del corpus que NO están en plantilla clínica (a ELIMINAR)
NOT_IN_CLINICAL = {"Útero", "Ovarios", "Testículos", "Gestación"}

# Atributos actuales del catálogo (Anexo A) que están SOBRANTES
EXTRA_ATTRIBUTES = {
    "Intestino.distension",        # no en clinical
    "Estómago.peristaltismo",      # movido a Intestino
    "Páncreas.ecogenicidad",       # reemplazado por preservacion/aspecto_peripancreatico
    "Páncreas.tamaño",             # reemplazado
    "Linfonodos.tamaño",           # reemplazado por binario
    "Linfonodos.forma",            # reemplazado
    "Linfonodos.ecogenicidad",     # reemplazado
    "Linfonodos.homogeneidad",     # reemplazado
    "Próstata.aspecto",            # reemplazado por forma+lobulacion
    "Útero.tamaño", "Útero.contenido", "Útero.grosor_pared",
    "Ovarios.tamaño", "Ovarios.forma",
    "Testículos.tamaño", "Testículos.forma", "Testículos.ecogenicidad", "Testículos.homogeneidad",
    "Gestación.fetos", "Gestación.preñez",
}


def main() -> None:
    eng = db.get_engine("sqlite", ROOT)
    with eng.begin() as conn:
        rows = conn.execute(text("SELECT organo, descripcion FROM hallazgos")).all()
    total = len(rows)

    organo_to_descs = defaultdict(list)
    for org, desc in rows:
        organo_to_descs[org].append(desc)

    # Calcular cobertura por (órgano clínico, atributo)
    print("=" * 80)
    print(f"COBERTURA DEL CATÁLOGO CLÍNICO SOBRE {total} HALLAZGOS")
    print("=" * 80)
    print()

    results: list[tuple[str, str, int, int, float]] = []

    for organo, attrs in CLINICAL_CATALOG.items():
        n_organo = len(organo_to_descs.get(organo, []))
        if n_organo == 0:
            continue
        for attr, patterns in attrs.items():
            compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
            n_match = 0
            for desc in organo_to_descs.get(organo, []):
                if any(p.search(desc) for p in compiled):
                    n_match += 1
            pct = 100.0 * n_match / n_organo if n_organo else 0
            results.append((organo, attr, n_match, n_organo, pct))

    # Resumen
    print(f"{'ÓRGANO':25} {'ATRIBUTO':30} {'MATCH':>6} / {'TOTAL':>5}   {'PCT':>6}   STATUS")
    print("-" * 90)
    for organo, attr, n_match, n_organo, pct in sorted(results, key=lambda x: (x[0], -x[4])):
        status = "✅" if pct >= 50 else ("⚠️" if pct >= 10 else "❌")
        print(f"{organo:25} {attr:30} {n_match:6} / {n_organo:5} {pct:6.1f}%  {status}")
    print()

    # Resumen por órgano (sumando todos los atributos)
    print("RESUMEN POR ÓRGANO (al menos 1 atributo clínico matcheado):")
    print("-" * 60)
    organo_min_match = defaultdict(int)
    organo_n = defaultdict(int)
    organo_attrs = defaultdict(list)
    for organo, attr, n_match, n_organo, pct in results:
        organo_attrs[organo].append((attr, n_match, n_organo, pct))
        organo_n[organo] = n_organo
    for organo, attrs in organo_attrs.items():
        # Para cada hallazgo del órgano, ¿matchea AL MENOS 1 atributo clínico?
        any_match = 0
        all_patterns = []
        for attr, _, _, _ in attrs:
            all_patterns.extend(CLINICAL_CATALOG[organo][attr])
        compiled = [re.compile(p, re.IGNORECASE) for p in all_patterns]
        for desc in organo_to_descs.get(organo, []):
            if any(p.search(desc) for p in compiled):
                any_match += 1
        n = organo_n[organo]
        pct = 100.0 * any_match / n if n else 0
        print(f"  {organo:30} {any_match:5} / {n:5} ({pct:5.1f}%) — matchea ≥1 atributo")

    # Órganos no en plantilla
    print()
    print("ÓRGANOS NO EN PLANTILLA CLÍNICA (a ELIMINAR del catálogo F3):")
    for org in NOT_IN_CLINICAL:
        n = organo_n[org] if org in organo_n else len(organo_to_descs.get(org, []))
        print(f"  {org:30} {n:5} hallazgos — sin plantilla clínica")

    # ─── Intestino por segmento (duodeno/yeyuno vs colon) ───
    print()
    print("=" * 80)
    print("INTESTINO — DISTRIBUCIÓN POR SEGMENTO ANATÓMICO")
    print("=" * 80)
    segmento_pat = {
        "duodeno":   r"\bduodeno\b",
        "yeyuno":    r"\byeyuno\b",
        "yeyuno_alt":r"\byeyunal\b",
        "ileon":     r"\b[ií]leon\b",
        "colon":     r"\bcolon\b",
        "ciego":     r"\bciego\b",
        "recto":     r"\brecto\b",
        "general":   r"\bintestino\b",
    }
    segmento_counts: dict[str, int] = {k: 0 for k in segmento_pat}
    n_intestino = 0
    for desc in organo_to_descs.get("Intestino", []):
        n_intestino += 1
        matched_any = False
        for seg, pat in segmento_pat.items():
            if re.search(pat, desc, re.IGNORECASE):
                segmento_counts[seg] += 1
                matched_any = True
        if not matched_any:
            segmento_counts["general"] += 1
    print(f"Total hallazgos Intestino: {n_intestino}")
    for seg, n in sorted(segmento_counts.items(), key=lambda x: -x[1]):
        pct = 100.0 * n / n_intestino if n_intestino else 0
        print(f"  {seg:15} {n:5} ({pct:5.1f}%)")

    # ─── Riñones por lateralidad ───
    print()
    print("=" * 80)
    print("RIÑONES — DISTRIBUCIÓN POR LATERALIDAD")
    print("=" * 80)
    lateralidad_pat = {
        "izquierdo":  r"\b(izquierd[oa]|izq\.?|ri[ñn][oó]n\s+izquierdo|ri[ñn][oó]n\s+izq)\b",
        "derecho":    r"\b(derech[oa]|der\.?|ri[ñn][oó]n\s+derecho|ri[ñn][oó]n\s+der)\b",
        "ambos":      r"\b(ambos|ambas|bilateral|bi)\b",
        "sin_lateralidad": r"",  # placeholder
    }
    n_rinones = len(organo_to_descs.get("Riñones", []))
    lateralidad_counts = {k: 0 for k in lateralidad_pat if k != "sin_lateralidad"}
    sin_lat_count = 0
    for desc in organo_to_descs.get("Riñones", []):
        izq = re.search(lateralidad_pat["izquierdo"], desc, re.IGNORECASE)
        der = re.search(lateralidad_pat["derecho"], desc, re.IGNORECASE)
        ambos = re.search(lateralidad_pat["ambos"], desc, re.IGNORECASE)
        if izq:
            lateralidad_counts["izquierdo"] += 1
        if der:
            lateralidad_counts["derecho"] += 1
        if ambos:
            lateralidad_counts["ambos"] += 1
        if not (izq or der or ambos):
            sin_lat_count += 1
    print(f"Total hallazgos Riñones: {n_rinones}")
    print(f"  izquierdo (solo o con izq): {lateralidad_counts['izquierdo']}")
    print(f"  derecho (solo o con der):   {lateralidad_counts['derecho']}")
    print(f"  ambos/bilateral:             {lateralidad_counts['ambos']}")
    print(f"  sin lateralidad explícita:   {sin_lat_count}")

    # ─── Cavidad abdominal ───
    print()
    print("=" * 80)
    print("CAVIDAD ABDOMINAL — ¿Existe como órgano en corpus?")
    print("=" * 80)
    n_cav = len(organo_to_descs.get("Cavidad abdominal", []))
    print(f"  Hallazgos RAW con organo='Cavidad abdominal': {n_cav}")
    if n_cav == 0:
        # buscar menciones en descripciones de otros órganos
        n_mencion = 0
        for org, descs in organo_to_descs.items():
            for desc in descs:
                if re.search(r"\bl[ií]quido\s+libre\b", desc, re.IGNORECASE):
                    n_mencion += 1
                    break
        print(f"  Menciones de 'líquido libre' en descripciones: {n_mencion} órganos diferentes")


if __name__ == "__main__":
    main()