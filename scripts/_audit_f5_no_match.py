"""F5 — Auditoria de stg_conclusion_no_match (helper de profiling).

Genera metricas de los 67 no-match: longitud, patrones repetidos,
clasificacion manual tentativa. Solo lectura; no modifica tablas.
"""
from __future__ import annotations

import re
import sqlite3
import sys
from collections import Counter

# Forzar UTF-8 en stdout
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = r"C:\Proyectos python\vectorizacion informes veterinarios"
silver = sqlite3.connect(f"{ROOT}/silver.db")
sc = silver.cursor()

rows = sc.execute("""
    SELECT conclusion_id, informe_id, texto_no_matcheado, n_caracteres, n_oraciones, tipo_no_match
    FROM stg_conclusion_no_match
    ORDER BY conclusion_id
""").fetchall()

print("=" * 78)
print(f"F5 AUDITORIA no_match — {len(rows)} conclusiones")
print("=" * 78)

# ── 1) Perfilado de longitud ─────────────────────────────────────────────
nchars = [r[3] for r in rows]
noraciones = [r[4] for r in rows]
nwords = [len((r[2] or "").split()) for r in rows]

print("\n=== 1. PERFILADO ===")
print(f"  total: {len(rows)}")
print(f"  unicas (por texto normalizado): {len(set(re.sub(r'\\s+', ' ', (r[2] or '').lower().strip().rstrip('.')) for r in rows))}")
print(f"  caracteres: min={min(nchars)} max={max(nchars)} avg={sum(nchars)/len(nchars):.1f} median={sorted(nchars)[len(nchars)//2]}")
print(f"  oraciones:  min={min(noraciones)} max={max(noraciones)} avg={sum(noraciones)/len(noraciones):.2f}")
print(f"  palabras:   min={min(nwords)} max={max(nwords)} avg={sum(nwords)/len(nwords):.1f} median={sorted(nwords)[len(nwords)//2]}")

print("\n  Distribución por palabras:")
buckets = [(1, 5), (6, 10), (11, 15), (16, 20), (21, 30), (31, 100)]
for lo, hi in buckets:
    n = sum(1 for nw in nwords if lo <= nw <= hi)
    pct = 100 * n / len(nwords)
    print(f"    {lo:2}-{hi:3} palabras: {n:2} ({pct:.0f}%)")

# ── 2) Patrones repetidos ────────────────────────────────────────────────
print("\n=== 2. PATRONES REPETIDOS ===")

patterns = [
    ("cambios tiroideos", "Tiroides patologia"),
    ("cambios hepaticos", "Hepatica variante"),
    ("cambios en pancreas", "Pancreas variante"),
    ("cambios pancreaticos", "Pancreas variante"),
    ("criptorquid", "Criptorquidia"),
    ("criptor", "Criptorquidia"),
    ("cuerpo extra", "Cuerpo extraño"),
    ("cuerpos extra", "Cuerpos extraños"),
    ("distencion", "Distención"),
    ("distension", "Distensión"),
    ("sedimento", "Sedimento urinario"),
    ("lito vesical", "Urolitiasis"),
    ("lito en vejiga", "Urolitiasis"),
    ("calculo en vejiga", "Urolitiasis"),
    ("artrosis", "Artrosis"),
    ("patella", "Luxacion patelar"),
    ("luxacion", "Luxacion"),
    ("surco troclear", "Ortopedia rodilla"),
    ("bursitis", "Bursitis"),
    ("tiflitis", "Tiflitis (ciego)"),
    ("remanente ovarico", "Remanente ovárico"),
    ("dilatacion", "Dilatacion"),
    ("obstructivo", "Cuerpo extraño obstructivo"),
    ("hiperplasico", "Hiperplasia"),
    ("pleural", "Derrame pleural"),
    ("peritoneal", "Derrame peritoneal"),
    ("paniculitis", "Paniculitis"),
    ("tiroideo", "Tiroides"),
    ("linfonodo", "Linfonodopatia"),
    ("utero y ovarios", "Actividad estral"),
    ("mielo lipoma", "Mielolipoma"),
    ("lipoma", "Lipoma"),
    ("tejido blando", "Tejido blando adyacente"),
    ("proestro", "Proestro"),
    ("criptor", "Criptorquidia"),
    ("tiflitis", "Tiflitis"),
    ("remamente", "Remanente"),
    ("aplanado", "Surco troclear"),
    ("pleura", "Derrame pleural"),
    ("sin cambios anatomicos", "Sin cambios"),
    ("no se observa cambios", "Sin cambios"),
    ("artrosis", "Artrosis"),
]

texts = [(r[2] or "").lower() for r in rows]
results = []
for pat, label in patterns:
    n = sum(1 for t in texts if pat in t)
    if n > 0:
        cids = [r[0] for r, t in zip(rows, texts) if pat in t]
        results.append((n, pat, label, cids))

results.sort(key=lambda x: -x[0])
for n, pat, label, cids in results:
    print(f"  {n:2}x  '{pat}'  [{label}]")
    print(f"       cids: {cids}")

# ── 3) Lista de textos completos para clasificacion ─────────────────────
print("\n=== 3. TODOS LOS 67 TEXTOS ===")
for r in rows:
    cid, iid, txt, nc, nor, tnm = r
    # También mostrar las primeras 30 palabras
    pwords = (txt or "").split()[:15]
    print(f"  cid={cid:5} chars={nc:3} w={len((txt or '').split()):2}  {' '.join(pwords)}{'...' if len((txt or '').split())>15 else ''}")

silver.close()
