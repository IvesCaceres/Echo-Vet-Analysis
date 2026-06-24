"""Inventario detallado: extracción de atributos por regex con captura de valor."""
import sqlite3
import re
from collections import Counter, defaultdict

conn = sqlite3.connect('informes.db')
cur = conn.cursor()
hallazgos = list(cur.execute("SELECT id, organo, descripcion, estado FROM hallazgos"))
print(f"Hallazgos cargados: {len(hallazgos):,}\n")

PATTERNS = {
    'Hígado': {
        'tamaño':           re.compile(r'tama[ñn]o\s+(?:severamente\s+|moderadamente\s+|levemente\s+|discretamente\s+|muy\s+)?(disminuido|aumentado(?:s)?|dentro de rango|normal|conservado)', re.I),
        'márgenes':         re.compile(r'm[áa]rgenes\s+(lisos|irregulares|conservados?|conservando|mal definidos)', re.I),
        'bordes':           re.compile(r'(?<![a-záéíóú])bordes?\s+(?:de\s+|con\s+)?(aguzados|redondeados|regulares|irregulares|lisos|conservados|conservando)', re.I),
        'ecogenicidad':     re.compile(r'ecogenicidad\s+((?:discretamente|levemente|moderadamente|severamente|muy|hipo|hiper)?\s*(?:hipoecoica|hiperecoica|conservada|normal|aumentada|disminuida|discreta))', re.I),
        'granulado':        re.compile(r'granulado\s+(fino|grueso)', re.I),
        'arquitectura':     re.compile(r'arquitectura\s+(conservada|alterada|conservando|preservada)', re.I),
        'patron_vascular':  re.compile(r'patr[oó]n\s+vascular\s+(conservado|alterado|conservando|aumentado|disminuido)', re.I),
    },
    'Riñones': {
        'forma':                re.compile(r'aspecto\s+(reniforme|ovalado|redondeado|irregular|globoso)', re.I),
        'tamaño':               re.compile(r'tama[ñn]o\s+(?:severamente\s+|moderadamente\s+|levemente\s+|discretamente\s+)?(disminuido|aumentado(?:s)?|dentro de rango|normal|conservado)', re.I),
        'bordes':               re.compile(r'bordes?\s+(?:de\s+|con\s+)?(regulares|irregulares|levemente\s+irregulares|lisos|conservados)', re.I),
        'ecogenicidad_cortical':re.compile(r'corteza\s+(hipoecoica|hiperecoica|discretamente\s+hiperecoica|levemente\s+hiperecoica|ecogenicidad\s+conservada|ecogenicidad\s+aumentada)', re.I),
        'diferenciacion_cm':    re.compile(r'diferenciaci[oó]n\s+(?:c[oó]rtico\s+medular|c[oó]rtico-medular)\s+(bien|mal)\s+definida', re.I),
        'relacion_cm':          re.compile(r'relaci[oó]n\s+(?:c[oó]rtico\s+medular|c[oó]rtico-medular)\s+(conservada|alterada|preservada|conservando)', re.I),
        'compromiso_pelvico':   re.compile(r'compromiso\s+p[ée]lvico\s+(presente|ausente|si|no|bilateral)', re.I),
    },
    'Vejiga': {
        'replecion':       re.compile(r'(semi\s+plet[oó]rica|semi\s+depletada|plet[oó]rica|depletada|distendida)', re.I),
        'contenido':       re.compile(r'contenido\s+(anecoico|anecoica|hiperecoico|hipoecoico|hiperecog[ée]nico|con\s+patr[oó]n|con\s+\w+|lito|homog[ée]neo)', re.I),
        'bordes_internos': re.compile(r'bordes?\s+internos?\s+(regulares|irregulares|levemente\s+irregulares|lisos)', re.I),
        'grosor_pared':    re.compile(r'grosor\s+(?:de\s+pared\s+|pared\s+|de\s+)?(conservado|levemente\s+aumentado|discretamente\s+aumentado|aumentado|moderadamente\s+aumentado|severamente\s+aumentado|disminuido|normal)', re.I),
    },
    'Vesícula': {
        'distension':      re.compile(r'(semi\s+distendida|distendida|plet[oó]rica|semi\s+plet[oó]rica|depletada)', re.I),
        'contenido':       re.compile(r'contenido\s+(anecoico|anecoica|hiperecoico|hipoecoico|hiperecog[ée]nico|con\s+\w+|homog[ée]neo)', re.I),
        'bordes_internos': re.compile(r'bordes?\s+internos?\s+(regulares|irregulares|levemente\s+irregulares)', re.I),
        'grosor_pared':    re.compile(r'grosor\s+(?:de\s+pared\s+|pared\s+|de\s+)?(conservado|conservados|levemente\s+aumentado|discretamente\s+aumentado|aumentado|moderadamente\s+aumentado|severamente\s+aumentado|disminuido|normal)', re.I),
    },
    'Bazo': {
        'tamaño':      re.compile(r'tama[ñn]o\s+(?:severamente\s+|moderadamente\s+|levemente\s+|discretamente\s+)?(disminuido|aumentado(?:s)?|normal|conservado|dentro\s+de\s+rango)', re.I),
        'forma':       re.compile(r'forma\s+(normal|conservada|conservando|caracter[íi]stica)', re.I),
        'márgenes':    re.compile(r'm[áa]rgenes\s+(lisos|irregulares|conservados|conservando)', re.I),
        'arquitectura':re.compile(r'arquitectura\s+(conservada|alterada|conservando|preservada|heterog[ée]nea)', re.I),
    },
    'Próstata': {
        'aspecto':      re.compile(r'(?:^|\.\s)aspecto\s+(ovalad[oa](?:\s+bilobulad[oa])?|bilobulad[oa](?:\s+y\s+globos[oa])?|globos[oa]|reniforme)', re.I),
        'tamaño':       re.compile(r'tama[ñn]o\s+(?:severamente\s+|moderadamente\s+|levemente\s+|discretamente\s+)?(disminuido|aumentado(?:s)?|dentro\s+de\s+rango|normal|conservado|severamente\s+disminuido)', re.I),
        'ecogenicidad': re.compile(r'\b(hiperecoica|hipoecoica|ecogenicidad\s+conservada|ecogenicidad\s+aumentada|ecogenicidad\s+disminuida)\b', re.I),
        'homogeneidad': re.compile(r'\b(homog[ée]ne[ao](?:s)?|heterog[ée]ne[ao](?:s)?|discretamente\s+heterog[ée]ne[ao])\b', re.I),
    },
    'Estómago': {
        'distension':     re.compile(r'\b(semi\s+distendido|distendido|repleci[oó]n\s+conservada|depletado)\b', re.I),
        'contenido':      re.compile(r'contenido\s+(alimenticio|gas|mucoso|alimenticio\s+y\s+gas|con\s+predominio\s+\w+|l[ií]quido)', re.I),
        'grosor_pared':   re.compile(r'grosor\s+(conservado|levemente\s+aumentado|discretamente\s+aumentado|aumentado|moderadamente\s+aumentado|severamente\s+aumentado|conservadas|aumentadas)', re.I),
        'peristaltismo':  re.compile(r'peristaltismo\s+(normal|aumentado|disminuido|conservado|discretamente\s+aumentado)', re.I),
    },
    'Intestino': {
        'distension':     re.compile(r'\b(semi\s+distendidos?|distendidos?|marcadamente\s+distendidos?|repleci[oó]n\s+conservada)\b', re.I),
        'contenido':      re.compile(r'contenido\s+(con\s+)?(\w+(?:\s+\w+)?)', re.I),
        'grosor_pared':   re.compile(r'grosor\s+(conservado|aumentado|levemente\s+aumentado|discretamente\s+aumentado|moderadamente\s+aumentado|severamente\s+aumentado|disminuido)', re.I),
        'peristaltismo':  re.compile(r'peristaltismo\s+(normal|aumentado|disminuido|conservado|discretamente\s+aumentado|levemente\s+aumentado)', re.I),
    },
    'Páncreas': {
        'ecogenicidad': re.compile(r'ecogenicidad\s+(conservada|aumentada|disminuida|hiperecog[ée]nica|hipoecoica|normal|hiperecoica)', re.I),
        'tamaño':       re.compile(r'tama[ñn]o\s+(normal|conservado|aumentado|disminuido|dentro\s+de\s+rango)', re.I),
    },
    'Adrenales': {
        'tamaño': re.compile(r'tama[ñn]o\s+(normal|conservado(?:s)?|aumentado(?:s)?|disminuido(?:s)?|dentro\s+de\s+rango)', re.I),
        'forma':  re.compile(r'forma\s+(normal|conservada|conservando)', re.I),
    },
    'Linfonodos': {
        'tamaño':       re.compile(r'tama[ñn]o\s+(normal|conservado(?:s)?|aumentado(?:s)?|disminuido(?:s)?|dentro\s+de\s+rango|levemente\s+aumentado)', re.I),
        'forma':        re.compile(r'forma\s+(normal|conservada|conservando|oval|ovalados|redondeados)', re.I),
        'ecogenicidad': re.compile(r'ecogenicidad\s+(conservada|hiperecoica|hipoecoica|aumentada|disminuida|normal)', re.I),
        'homogeneidad': re.compile(r'\b(homog[ée]neos?|heterog[ée]neos?)\b', re.I),
    },
    'Útero': {
        'tamaño':       re.compile(r'tama[ñn]o\s+(normal|conservado|aumentado|disminuido|levemente\s+aumentado|moderadamente\s+aumentado|severamente\s+aumentado)', re.I),
        'contenido':    re.compile(r'contenido\s+(anecoico|hiperecoico|ecog[ée]nico|homog[ée]neo|heterog[ée]neo|l[ií]quido)', re.I),
        'grosor_pared': re.compile(r'grosor\s+(?:de\s+pared\s+|pared\s+)?(conservado|aumentado|disminuido|levemente\s+aumentado)', re.I),
    },
    'Ovarios': {
        'tamaño': re.compile(r'tama[ñn]o\s+(normal|conservado|aumentado|disminuido|levemente\s+aumentado)', re.I),
        'forma':  re.compile(r'forma\s+(normal|conservada|conservando|ovalados|redondeados)', re.I),
    },
    'Testículos': {
        'tamaño':       re.compile(r'tama[ñn]o\s+(normal|conservado(?:s)?|aumentado(?:s)?|disminuido(?:s)?|dentro\s+de\s+rango)', re.I),
        'forma':        re.compile(r'forma\s+(normal|conservada|conservando)', re.I),
        'ecogenicidad': re.compile(r'ecogenicidad\s+(conservada|hiperecoica|hipoecoica|aumentada|disminuida|normal)', re.I),
        'homogeneidad': re.compile(r'\b(homog[ée]neos?|heterog[ée]neos?)\b', re.I),
    },
    'Gestación': {
        'fetos':     re.compile(r'\b(\d+|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\s+fetos?\b', re.I),
        'preñez':    re.compile(r'\b(pre[ñn]ez|gestaci[oó]n)\b', re.I),
    },
}

MOD_PATTERN = re.compile(r'\b(leve(?:s)?|moderad[oa](?:s)?|sever[oa](?:s)?|agud[oa](?:s)?|cr[oó]nic[oa](?:s)?)\b', re.I)
LAT_PATTERN = re.compile(r'\b(bilateral(?:es)?|izquierd[oa]|derech[oa])\b', re.I)

por_organo = defaultdict(lambda: {'atributos': defaultdict(Counter), 'n': 0, 'con_attrs': 0, 'n_mods': 0, 'n_lat': 0})

for hid, organo, desc, estado in hallazgos:
    if not desc:
        continue
    por_organo[organo]['n'] += 1
    d = desc.lower()
    patterns = PATTERNS.get(organo, {})
    found = 0
    for attr, pat in patterns.items():
        m = pat.search(d)
        if m:
            # Capturar el primer grupo no-None (algunos patrones tienen grupos opcionales)
            val = None
            if m.lastindex:
                for gi in range(1, m.lastindex + 1):
                    g = m.group(gi)
                    if g:
                        val = g
                        break
            if val is None:
                val = m.group(0)
            val = val.strip()
            por_organo[organo]['atributos'][attr][val] += 1
            found += 1
    if found > 0:
        por_organo[organo]['con_attrs'] += 1
    if MOD_PATTERN.search(d):
        por_organo[organo]['n_mods'] += 1
    if LAT_PATTERN.search(d):
        por_organo[organo]['n_lat'] += 1

print("=" * 110)
print(f"{'ORGANO':<14} {'#HAL':>7} {'#CON_ATTR':>11} {'COV%':>7} {'AVG_ATTR':>10} {'#MOD':>6} {'#LAT':>6}")
print("=" * 110)
for organo in sorted(por_organo, key=lambda k: -por_organo[k]['n']):
    d = por_organo[organo]
    n = d['n']
    cov = 100 * d['con_attrs'] / n if n else 0
    avg = sum(sum(c.values()) for c in d['atributos'].values()) / n if n else 0
    print(f"{organo:<14} {n:>7,} {d['con_attrs']:>11,} {cov:>6.1f}% {avg:>9.2f} {d['n_mods']:>6,} {d['n_lat']:>6,}")

print("\n" + "=" * 110)
print("DETALLE: ATRIBUTOS DETECTADOS Y TOP VALORES POR ORGANO")
print("=" * 110)
for organo in ['Hígado', 'Riñones', 'Vejiga', 'Vesícula', 'Bazo', 'Próstata', 'Estómago', 'Intestino', 'Linfonodos', 'Páncreas', 'Adrenales', 'Útero', 'Testículos', 'Ovarios', 'Gestación']:
    if organo not in por_organo:
        continue
    d = por_organo[organo]
    print(f"\n--- {organo} (n={d['n']:,}) ---")
    for attr, counter in sorted(d['atributos'].items()):
        total = sum(counter.values())
        top5 = counter.most_common(5)
        s = ", ".join(f"{v[:25]}x{c}" for v, c in top5)
        print(f"  {attr:25} {total:>5} hallazgos  ->  {s}")

print("\n" + "=" * 110)
print("MODIFICADORES Y LATERALIDAD — cobertura global (transversal)")
print("=" * 110)
print(f"Hallazgos con >=1 modificador (leve/moderado/severo/...):  "
      f"{sum(d['n_mods'] for d in por_organo.values()):,} / {len(hallazgos):,}")
print(f"Hallazgos con >=1 lateralidad (bilateral/izq/der):        "
      f"{sum(d['n_lat'] for d in por_organo.values()):,} / {len(hallazgos):,}")
