"""F5 — Clasificacion manual de los 67 stg_conclusion_no_match.

Categorias:
  A) Sin informacion clinica relevante (ruido / admin)
  B) Ya cubierto por terminos existentes (falla de regex)
  C) Nuevo diagnostico clinicamente relevante
  D) Nueva etiologia clinicamente relevante
  E) Nuevo termino negativo clinicamente relevante
  F) Texto ambiguo o fuera de scope

Solo lectura; no modifica tablas.
"""
from __future__ import annotations

import sqlite3
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = r"C:\Proyectos python\vectorizacion informes veterinarios"
silver = sqlite3.connect(f"{ROOT}/silver.db")
sc = silver.cursor()

rows = sc.execute("""
    SELECT conclusion_id, texto_no_matcheado
    FROM stg_conclusion_no_match
    ORDER BY conclusion_id
""").fetchall()

# Clasificacion manual
CLASS = {
    # ── Tiroides (12 cids) ── Nuevo C
    314:  ("C", "cambios_tiroideos", "TIROIDES (12 cids) — 'Cambios tiroideos' no en catálogo"),
    371:  ("C", "cambios_tiroideos", "TIROIDES"),
    414:  ("C", "cambios_tiroideos", "TIROIDES"),
    530:  ("C", "cambios_tiroideos", "TIROIDES"),
    642:  ("C", "cambios_tiroideos", "TIROIDES"),
    702:  ("C", "cambios_tiroideos", "TIROIDES"),
    897:  ("C", "cambios_tiroideos", "TIROIDES"),
    1003: ("C", "cambios_tiroideos", "TIROIDES"),
    1602: ("C", "cambios_tiroideos", "TIROIDES"),
    1643: ("C", "cambios_tiroideos", "TIROIDES"),
    1747: ("C", "cambios_tiroideos", "TIROIDES"),
    2768: ("C", "cambios_tiroideos", "TIROIDES"),

    # ── Criptorquidia (9 cids) ── Nuevo C
    1519: ("C", "criptorquidismo", "CRIPTORQUIDIA (9 cids)"),
    1555: ("C", "criptorquidismo", "CRIPTORQUIDIA"),
    1621: ("C", "criptorquidismo", "CRIPTORQUIDIA"),
    1805: ("C", "criptorquidismo", "CRIPTORQUIDIA"),
    2339: ("C", "criptorquidismo", "CRIPTORQUIDIA"),
    2377: ("C", "criptorquidismo", "CRIPTORQUIDIA"),
    2435: ("C", "criptorquidismo", "CRIPTORQUIDIA"),
    2526: ("C", "criptorquidismo", "CRIPTORQUIDIA"),
    2728: ("C", "criptorquidismo", "CRIPTORQUIDIA"),

    # ── Cuerpo extraño (8 cids) ── Nuevo C
    224:  ("C", "cuerpo_extrano", "CUERPO EXTRAÑO (8 cids)"),
    612:  ("C", "cuerpo_extrano", "CUERPO EXTRAÑO"),
    715:  ("C", "cuerpo_extrano", "CUERPO EXTRAÑO"),
    1153: ("C", "cuerpo_extrano", "CUERPO EXTRAÑO (texto con sufijo administrativo)"),
    2162: ("C", "cuerpo_extrano", "CUERPO EXTRAÑO"),
    2311: ("C", "cuerpo_extrano", "CUERPO EXTRAÑO"),
    2836: ("C", "cuerpo_extrano", "CUERPO EXTRAÑO"),
    2860: ("C", "cuerpo_extrano", "CUERPO EXTRAÑO"),

    # ── Distension (5 cids) ── Nuevo C (algunos son B con regex)
    612:  ("C", "distension_gastrica", "DISTENSION (incluido en CUERPO EXTRAÑO arriba)"),  # ref counted in cuerpo_extrano
    1431: ("C", "distension_intestinal", "DISTENSION INTESTINAL"),
    1489: ("C", "distension_gastrica", "DISTENSION GASTRICA"),
    2144: ("C", "distension_colonica", "DISTENSION COLONICA"),
    2860: ("C", "distension_gastrointestinal", "DISTENSION (incluido en CUERPO EXTRAÑO arriba)"),  # ref counted

    # ── Sedimento (5 cids) ── B (regex falla; 'sedimento' solo en lugar de 'sedimento en vejiga')
    668:  ("B", "sedimento_vejiga", "SEDIMENTO — regex debería matchear 'sedimento' solo"),
    794:  ("B", "sedimento_vejiga", "SEDIMENTO"),
    1620: ("B", "sedimento_vejiga", "SEDIMENTO"),
    1774: ("B", "sedimento_vejiga", "SEDIMENTO + 'litos vesicales'"),
    2887: ("B", "sedimento_vejiga", "SEDIMENTO"),

    # ── Cistolito (4 cids) ── B (regex falla: 'lito vesical', 'lito en vejiga', 'cálculo en vejiga')
    1030: ("B", "cistolito", "LITO VESICAL — variantes no en catálogo"),
    2000: ("B", "cistolito", "LITO EN VEJIGA"),
    2660: ("B", "cistolito", "CÁLCULO EN VEJIGA"),

    # ── Hepatica variante (2 cids) ── B
    1631: ("B", "hepatopatia", "CAMBIOS HEPÁTICOS — variante no en catálogo"),
    1909: ("B", "hepatopatia", "CAMBIOS HEPÁTICOS"),

    # ── Pancreatica variante (1 cid) ── B
    1648: ("B", "cambios_pancreaticos", "CAMBIOS EN PÁNCREAS — variante con preposición"),

    # ── Linfatica variante (1 cid) ── B
    320:  ("B", "linfadenomegalia", "LINFONODOPATÍA — variante léxica"),

    # ── Sin cambios (3 cids) ── B/A
    478:  ("A", "sin_evidencia", "EXAMEN OK — 'no se observa cambios' ruido clínico"),
    2717: ("A", "sin_evidencia", "EXAMEN OK — 'sin cambios anatómicos'"),

    # ── Ileo (3 cids) ── Nuevo C
    379:  ("C", "ileo", "ILEO INTESTINAL"),
    456:  ("C", "ileo", "ILEO INTESTINAL (typo sin tilde)"),
    2660: ("C", "ileo", "ILEO PARALÍTICO"),

    # ── Distension uretral / vejiga (1 cid) ── B
    1091: ("B", "dilatacion_ureteral", "DILATACIÓN URETRAL (typo de ureteral)"),

    # ── Cistitis (1 cid) ── B
    990:  ("B", "cistitis", "PROCESO INFLAMATORIO EN VEJIGA — equivalente a cistitis"),

    # ── Derrame pleural (1 cid) ── B parcial
    144:  ("B/C", "derrame_pleural", "DERRAME PLEURAL — peritoneal sí, pleural no"),

    # ── Vejiga dilatada (1 cid) ── F
    92:   ("F", None, "VEJIGA DILATADA — ambiguo: ¿obstructiva? contexto sin conclusión"),

    # ── Útero/ovarios proestro (2 cids) ── Nuevo C
    5:    ("C", "actividad_estral", "ACTIVIDAD ESTRAL / PROESTRO"),
    1821: ("C", "actividad_estral", "INICIANDO PROESTRO"),

    # ── Paniculitis (1 cid) ── C
    79:   ("C", "paniculitis", "PANICULITIS GRASA"),

    # ── Desgarro muscular (1 cid) ── C (mixed with B for linfonodopatía)
    320:  ("C", "desgarro_muscular", "DESGARRO MUSCULAR — ortopedia, fuera scope"),

    # ── Tiflitis (1 cid) ── Nuevo C
    667:  ("C", "tiflitis", "TIFLITIS (ciego)"),

    # ── Ulcera intestinal (1 cid) ── Nuevo C
    667:  ("C", "ulcera_intestinal", "ULCERA INTESTINAL"),

    # ── Remanente ovarico (1 cid) ── Nuevo C
    1008: ("C", "remanente_ovarico", "REMANENTE OVÁRICO"),

    # ── Hipomotilidad (1 cid) ── Nuevo C
    1026: ("C", "hipomotilidad_intestinal", "HIPOMOTILIDAD INTESTINAL"),

    # ── Mielolipoma (1 cid) ── Nuevo C
    2016: ("C", "mielolipoma_esplenico", "MIELOLIPOMA ESPLÉNICO"),

    # ── Ovario poliquístico (1 cid) ── Nuevo C (already counted in 2000)
    2000: ("C", "ovario_poliquistico", "OVARIO POLIQUÍSTICO"),

    # ── Gastroenterocolitis (1 cid) ── B (exists in catalog)
    2561: ("B", "enterocolitis", "GASTROENTEROCOLITIS — existe en catálogo como variante"),

    # ── Cambios prostáticos (1 cid) ── Nuevo C
    1620: ("C", "hiperplasia_prostatica", "CAMBIOS PROSTÁTICOS HIPERPLÁSICOS"),

    # ── Ortopedia rodilla (4 cids) ── F (fuera scope ecografía abdominal)
    376:  ("F", None, "ORTOPEDIA RODILLA — fuera scope ecografía abdominal"),
    399:  ("F", None, "ORTOPEDIA RODILLA"),
    893:  ("F", None, "ORTOPEDIA RODILLA"),
    907:  ("F", None, "ORTOPEDIA RODILLA"),

    # ── Bursitis (1 cid) ── F
    1303: ("F", None, "BURSITIS BICIPITAL — ortopedia, fuera scope"),

    # ── Acumulo grasa subcutanea (1 cid) ── F
    1612: ("F", None, "ACÚMULO GRASA SUBCUTÁNEA — ambiguo, no es diagnóstico claro"),

    # ── Tejido blando laringe (1 cid) ── F
    1794: ("F", None, "TEJIDO BLANDO LARINGE — origen indeterminado, ambiguo"),
}

# Contar categorias
from collections import Counter
cats = Counter()
new_terms = Counter()
for cid, (cat, term, note) in CLASS.items():
    cats[cat] += 1
    if term:
        new_terms[term] += 1

print("=" * 78)
print(f"F5 CLASIFICACION MANUAL — {len(CLASS)} no-match (de 67 totales)")
print("=" * 78)

print("\n=== DISTRIBUCION POR CATEGORIA ===")
total = sum(cats.values())
for c in ["A", "B", "C", "D", "E", "F"]:
    n = cats.get(c, 0)
    pct = 100 * n / total
    label = {
        "A": "Sin información clínica (ruido/admin)",
        "B": "Ya cubierto, falla de regex",
        "C": "Nuevo diagnóstico relevante",
        "D": "Nueva etiología relevante",
        "E": "Nuevo término negativo",
        "F": "Texto ambiguo / fuera de scope",
    }.get(c, c)
    print(f"  {c}) {n:2} ({pct:5.1f}%) — {label}")

print("\n=== TERMINOS NUEVOS PROPUESTOS (Top por impacto) ===")
for term, n in new_terms.most_common():
    print(f"  {n:2}x  {term}")

print("\n=== LISTADO COMPLETO ===")
print(f"{'cid':>5}  {'cat':3}  {'texto':60}  accion")
for cid, texto in rows:
    cat, term, note = CLASS.get(cid, ("?", None, "FALTA CLASIFICAR"))
    txt_short = texto[:60]
    acc = f"+{term}" if term else "—"
    print(f"{cid:>5}  {cat:3}  {txt_short:60}  {acc}")

silver.close()
