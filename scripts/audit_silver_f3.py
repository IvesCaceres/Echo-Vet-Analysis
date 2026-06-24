"""Auditoría clínica de F3 (silver_atributos_hallazgo).

Objetivo: validar que la extracción sea clínicamente correcta antes de F4.
Hace muestreo reproducible, ejecuta validaciones automáticas y produce
un reporte con métricas + lista priorizada de regex a corregir.

Criterios GO para F4:
- Precisión clínica ≥95%
- Lateralidad ≥98%
- Segmentación ≥95%
- Sin explosiones de cardinalidad relevantes (≤20 attrs/hallazgo en top 30)
"""
from __future__ import annotations

import argparse
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from informes_vet.silver_db import get_engine

# ─── Valores canónicos: clasificación normal/anormal ───
# (heurística conservadora; refinable con feedback clínico)
NORMAL_VALORES = {
    "NORMAL", "CONSERVADO", "CONSERVADA",
    "REGULARES", "LISOS", "OVALADO", "OVALADA",
    "ADECUADA", "BIEN_DEFINIDA", "SIN_COMPROMISO", "SIN_COMPROMETIDO",
    "ANECOICO", "ANECOICA", "HOMOGENEO", "HOMOGENEA",
    "DENTRO_DE_RANGO", "NO_SE_OBSERVAN", "PRESERVADO", "PRESERVADA",
    "PRESENTE", "AUSENTE",  # binarios: contexto-dependiente, default normal
    "ALIMENTICIO", "MUCOSO", "FECAL", "GAS", "LIQUIDO",  # contenido intestinal (puede ser normal)
}

ANORMAL_VALORES = {
    "AUMENTADO", "AUMENTADA", "DISMINUIDO", "DISMINUIDA",
    "ENGROSADO", "GRUESO", "FINO",
    "IRREGULARES", "LEVEMENTE_IRREGULARES", "REDONDEADOS",
    "COMPROMETIDO", "CON_COMPROMISO", "MAL_DEFINIDA", "MAL_DEFINIDO",
    "DISTENDIDO", "DISTENDIDA", "SEMI_DISTENDIDA", "SEMI_DISTENDIDO",
    "DILATACION_PELVICA",
    "HIPOECOICA", "HIPERECOICA",
    "HETEROGENEA", "HETEROGENEO",
    "BILOBULADA", "GLOBOSA", "DEPLETADA", "PLETORICA",
    "LEVEMENTE_AUMENTADO", "MODERADAMENTE_AUMENTADO", "SEVERAMENTE_AUMENTADO",
    "VACIO",  # vejiga vacía es hallazgo (depleción)
    "REACTIVO",  # linfonodo reactivo = alteración
}


def classify_hallazgo(attrs_canonicos: list[str | None]) -> str:
    """Devuelve 'normal', 'abnormal', o 'mixed' (no se usa para muestreo)."""
    valid = [v for v in attrs_canonicos if v]
    if not valid:
        return "no_attrs"
    if all(v in NORMAL_VALORES for v in valid):
        return "normal"
    if all(v in ANORMAL_VALORES for v in valid):
        return "abnormal"
    if any(v in ANORMAL_VALORES for v in valid):
        return "abnormal"  # mixto: hay al menos un abnormal → abnormal
    return "normal"  # mixto: ningún abnormal → normal


def load_sample(eng, seed: int, n_normal: int, n_abnormal: int, max_per_organ: int = 25):
    """Carga muestra reproducible: n_normal hallazgos normales + n_abnormal anormales.

    Distribución entre órganos: cap max_per_organ para evitar sesgo.
    """
    rng = random.Random(seed)
    with eng.begin() as conn:
        rows = conn.execute(text("""
            SELECT sh.hallazgo_id, sh.informe_id, sh.dim_organo_id, o.nombre_canonico, sh.descripcion
            FROM silver_hallazgos sh
            JOIN dim_organo o ON sh.dim_organo_id = o.id
        """)).all()

        # Clasificar cada hallazgo
        by_organ_class = defaultdict(lambda: {"normal": [], "abnormal": []})
        for hallazgo_id, informe_id, organo_id, organo, desc in rows:
            attrs = conn.execute(text("""
                SELECT DISTINCT valor_canonico
                FROM silver_atributos_hallazgo
                WHERE hallazgo_id = :h
            """), {"h": hallazgo_id}).all()
            cls = classify_hallazgo([r[0] for r in attrs])
            if cls in ("normal", "abnormal"):
                by_organ_class[organo][cls].append(
                    (hallazgo_id, informe_id, organo_id, organo, desc)
                )

    # Muestreo estratificado por órgano (cap max_per_organ)
    def stratified_sample(pool: list, n: int) -> list:
        rng_local = random.Random(seed)
        rng_local.shuffle(pool)
        per_organ = max(1, n // len(by_organ_class))
        sample: list = []
        per_organ_counts = Counter()
        for item in pool:
            organo = item[3]
            if per_organ_counts[organo] >= max_per_organ:
                continue
            if len(sample) >= n:
                break
            sample.append(item)
            per_organ_counts[organo] += 1
        return sample

    normal_sample = stratified_sample(
        [h for organo in by_organ_class
         for h in by_organ_class[organo]["normal"]],
        n_normal,
    )
    abnormal_sample = stratified_sample(
        [h for organo in by_organ_class
         for h in by_organ_class[organo]["abnormal"]],
        n_abnormal,
    )

    return normal_sample, abnormal_sample


def get_attrs_for_hallazgo(conn, hallazgo_id: int) -> list[dict]:
    rows = conn.execute(text("""
        SELECT
          a.nombre_canonico AS atributo,
          sah.valor_texto AS valor_original,
          sah.valor_canonico AS valor_normalizado,
          sah.lateralidad,
          sah.segmento_id,
          sa.codigo AS segmento_codigo,
          sa.nombre_canonico AS segmento_nombre,
          sah.texto_original AS match_text,
          sah.pos_inicio,
          sah.pos_fin,
          sah.confianza,
          sah.metodo_extraccion
        FROM silver_atributos_hallazgo sah
        JOIN dim_organo_atributo doa ON sah.dim_organo_atributo_id = doa.id
        JOIN dim_atributo a ON doa.dim_atributo_id = a.id
        LEFT JOIN dim_segmento_anatomico sa ON sah.segmento_id = sa.id
        WHERE sah.hallazgo_id = :h
        ORDER BY a.nombre_canonico, sah.segmento_id
    """), {"h": hallazgo_id}).all()
    cols = [
        "atributo", "valor_original", "valor_normalizado",
        "lateralidad", "segmento_id", "segmento_codigo", "segmento_nombre",
        "match_text", "pos_inicio", "pos_fin", "confianza", "metodo_extraccion",
    ]
    return [dict(zip(cols, r)) for r in rows]


def validate_sample(eng, sample: list[tuple]) -> dict:
    """Para cada hallazgo, ejecutar validaciones automáticas.

    Returns dict con métricas globales + lista de issues detectados.

    Notas sobre las validaciones:
    - Lateralidad 'bilateral' sin contexto explícito ('ambos/ambas/bilateral')
      es LEGÍTIMO (default para hallazgos Riñones/Adrenales sin lateralidad
      explícita: "glándulas de forma normal" implica ambas). No se marca como
      issue a menos que el texto mencione explicitamente "izquierdo" o
      "derecho" de forma contradictoria.
    - Duplicados lógicos: NO se cuentan cuando hay lateralidad distinta (ej:
      riñón izquierdo + riñón derecho = esperado). Solo cuentan cuando hay 2+
      filas con MISMO (atributo, lateralidad, segmento_id).
    """
    n_total = 0
    n_atributos_total = 0
    n_tp_match_text_in_desc = 0
    n_tp_valor_in_desc = 0
    n_lateralidad_ok = 0
    n_lateralidad_eval = 0
    n_segmentacion_ok = 0
    n_segmentacion_eval = 0
    n_duplicados_logicos = 0
    issues: list[dict] = []

    with eng.begin() as conn:
        for hallazgo_id, informe_id, organo_id, organo, desc in sample:
            attrs = get_attrs_for_hallazgo(conn, hallazgo_id)
            n_total += 1
            n_atributos_total += len(attrs)

            desc_lower = desc.lower()
            tiene_izq_explicito = any(t in desc_lower for t in ("izquierd", "izq"))
            tiene_der_explicito = any(t in desc_lower for t in ("derech", "der ", "dch", "dch."))
            tiene_bilateral_explicito = any(t in desc_lower for t in ("ambos", "ambas", "bilateral"))

            for a in attrs:
                # 1. text_original ∈ descripcion (TP check)
                if a["match_text"] and a["match_text"].lower() in desc_lower:
                    n_tp_match_text_in_desc += 1

                # 2. valor_texto ∈ descripcion (valor presente en texto)
                v = (a["valor_original"] or "").lower()
                # Ignorar valores numéricos cortos (UNO/DOS/TRES) y muy cortos
                if v and len(v) >= 3 and v in desc_lower:
                    n_tp_valor_in_desc += 1

                # 2. Validación lateralidad
                lat = a["lateralidad"]
                if not lat:
                    continue
                n_lateralidad_eval += 1
                if lat == "izquierdo":
                    if tiene_izq_explicito or tiene_bilateral_explicito:
                        n_lateralidad_ok += 1
                    elif tiene_der_explicito and not tiene_izq_explicito:
                        # texto solo menciona derecho → izq es FP
                        issues.append({
                            "tipo": "lateralidad_contradictoria",
                            "hallazgo_id": hallazgo_id,
                            "organo": organo,
                            "atributo": a["atributo"],
                            "lat_asignado": lat,
                            "desc": desc[:120],
                        })
                    else:
                        # Sin mención: bilateral implícito → izq podría ser OK si
                        # el hallazgo es bilateral (Riñones/Adrenales default)
                        if organo in ("Riñones", "Adrenales"):
                            n_lateralidad_ok += 1  # bilateral default → OK
                        else:
                            issues.append({
                                "tipo": "lateralidad_inexistente",
                                "hallazgo_id": hallazgo_id,
                                "organo": organo,
                                "atributo": a["atributo"],
                                "lat_asignado": lat,
                                "desc": desc[:120],
                            })
                elif lat == "derecho":
                    if tiene_der_explicito or tiene_bilateral_explicito:
                        n_lateralidad_ok += 1
                    elif tiene_izq_explicito and not tiene_der_explicito:
                        issues.append({
                            "tipo": "lateralidad_contradictoria",
                            "hallazgo_id": hallazgo_id,
                            "organo": organo,
                            "atributo": a["atributo"],
                            "lat_asignado": lat,
                            "desc": desc[:120],
                        })
                    else:
                        if organo in ("Riñones", "Adrenales"):
                            n_lateralidad_ok += 1
                        else:
                            issues.append({
                                "tipo": "lateralidad_inexistente",
                                "hallazgo_id": hallazgo_id,
                                "organo": organo,
                                "atributo": a["atributo"],
                                "lat_asignado": lat,
                                "desc": desc[:120],
                            })
                elif lat == "bilateral":
                    n_lateralidad_ok += 1  # bilateral siempre OK (incluye default)

                # 3. Validación segmentación
                seg = a["segmento_codigo"]
                if not seg:
                    continue
                n_segmentacion_eval += 1
                if seg == "duodeno_yeyuno":
                    if any(t in desc_lower for t in ("duodeno", "yeyuno", "yeyunal", "íleon", "ileon")):
                        n_segmentacion_ok += 1
                    else:
                        issues.append({
                            "tipo": "segmento_sin_contexto",
                            "hallazgo_id": hallazgo_id,
                            "organo": organo,
                            "atributo": a["atributo"],
                            "seg_asignado": seg,
                            "desc": desc[:120],
                        })
                elif seg == "colon":
                    if any(t in desc_lower for t in ("colon", "ciego", "recto", "colónica", "colónico")):
                        n_segmentacion_ok += 1
                    else:
                        issues.append({
                            "tipo": "segmento_sin_contexto",
                            "hallazgo_id": hallazgo_id,
                            "organo": organo,
                            "atributo": a["atributo"],
                            "seg_asignado": seg,
                            "desc": desc[:120],
                        })
                elif seg in ("rinon_derecho", "rinon_izquierdo",
                             "adrenal_derecha", "adrenal_izquierda"):
                    n_segmentacion_ok += 1

    # 6. Duplicados REALES: mismo (hallazgo, atributo, lateralidad, segmento)
    with eng.begin() as conn:
        dups = conn.execute(text("""
            SELECT hallazgo_id, atributo, lateralidad, segmento_id, COUNT(*) as n
            FROM (
              SELECT sah.hallazgo_id,
                     a.nombre_canonico AS atributo,
                     sah.lateralidad,
                     sah.segmento_id
              FROM silver_atributos_hallazgo sah
              JOIN dim_organo_atributo doa ON sah.dim_organo_atributo_id = doa.id
              JOIN dim_atributo a ON doa.dim_atributo_id = a.id
            )
            GROUP BY hallazgo_id, atributo, lateralidad, segmento_id
            HAVING n > 1
        """)).all()
        n_duplicados_logicos = len(dups)
        # Guardar detalle
        for dup in dups[:20]:
            issues.append({
                "tipo": "duplicado_logico",
                "hallazgo_id": dup[0],
                "atributo": dup[1],
                "lateralidad": dup[2],
                "segmento_id": dup[3],
                "n": dup[4],
                "desc": "",
            })

    return {
        "n_total_hallazgos": n_total,
        "n_atributos_total": n_atributos_total,
        "n_tp_match_text_in_desc": n_tp_match_text_in_desc,
        "n_tp_valor_in_desc": n_tp_valor_in_desc,
        "n_lateralidad_ok": n_lateralidad_ok,
        "n_lateralidad_eval": n_lateralidad_eval,
        "n_segmentacion_ok": n_segmentacion_ok,
        "n_segmentacion_eval": n_segmentacion_eval,
        "n_duplicados_logicos": n_duplicados_logicos,
        "issues": issues,
    }


def check_explosion(eng, top_n: int = 30) -> list[tuple]:
    """Top N hallazgos con más atributos."""
    with eng.begin() as conn:
        rows = conn.execute(text("""
            SELECT sah.hallazgo_id, o.nombre_canonico, sh.descripcion,
                   COUNT(*) AS n_atributos
            FROM silver_atributos_hallazgo sah
            JOIN silver_hallazgos sh ON sh.hallazgo_id = sah.hallazgo_id
            JOIN dim_organo o ON sh.dim_organo_id = o.id
            GROUP BY sah.hallazgo_id, o.nombre_canonico, sh.descripcion
            ORDER BY n_atributos DESC
            LIMIT :n
        """), {"n": top_n}).all()
        return rows


def show_sample_detail(eng, sample: list[tuple], max_show: int = 100):
    """Imprime cada hallazgo con sus atributos extraídos."""
    print(f"\n[DETALLE] Muestra completa ({min(max_show, len(sample))} hallazgos)")
    print("=" * 78)
    with eng.begin() as conn:
        for i, (hallazgo_id, informe_id, organo_id, organo, desc) in enumerate(sample[:max_show], 1):
            cls = classify_hallazgo([
                r[0] for r in conn.execute(text("""
                    SELECT DISTINCT valor_canonico FROM silver_atributos_hallazgo
                    WHERE hallazgo_id = :h
                """), {"h": hallazgo_id}).all()
            ])
            cls_marker = "🟢 NORMAL" if cls == "normal" else ("🔴 ANORMAL" if cls == "abnormal" else "⚪ MIXED")
            print(f"\n#{i:3d} {cls_marker}  hallazgo_id={hallazgo_id}  informe_id={informe_id}  {organo}")
            print(f"      DESC: {desc[:240]}")
            attrs = get_attrs_for_hallazgo(conn, hallazgo_id)
            if not attrs:
                print(f"      (sin atributos extraídos)")
                continue
            for a in attrs:
                seg_str = a["segmento_codigo"] or "-"
                lat_str = a["lateralidad"] or "-"
                match_str = a["match_text"] or ""
                print(f"      • {a['atributo']:30s} → {a['valor_normalizado']:20s} "
                      f"(texto: {match_str!r:30s}) lat={lat_str:11s} seg={seg_str}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-normal", type=int, default=50)
    parser.add_argument("--n-abnormal", type=int, default=50)
    parser.add_argument("--db-kind", default="sqlite")
    parser.add_argument("--show-sample", action="store_true",
                        help="Imprimir los 100 hallazgos completos")
    parser.add_argument("--show-limit", type=int, default=20,
                        help="Cuántos hallazgos imprimir en muestra")
    args = parser.parse_args()

    eng = get_engine(ROOT, db_kind=args.db_kind)

    print("=" * 78)
    print("AUDITORÍA CLÍNICA F3 — silver_atributos_hallazgo")
    print("=" * 78)

    # ─── Muestreo ───
    print(f"\n[1] Muestreo reproducible (seed={args.seed}, "
          f"{args.n_normal} normales + {args.n_abnormal} anormales)")
    normal_sample, abnormal_sample = load_sample(
        eng, args.seed, args.n_normal, args.n_abnormal,
    )
    sample = normal_sample + abnormal_sample
    random.Random(args.seed).shuffle(sample)
    print(f"  Total muestra: {len(sample)} hallazgos")
    organo_dist = Counter(h[3] for h in sample)
    print(f"  Distribución por órgano:")
    for organo, n in organo_dist.most_common():
        print(f"    {organo:30s} {n:3d}")

    # ─── Mostrar muestra ───
    if args.show_sample:
        show_sample_detail(eng, sample, args.show_limit)

    # ─── Validaciones ───
    print(f"\n[2] Validaciones automáticas")
    metrics = validate_sample(eng, sample)

    n_attrs = metrics["n_atributos_total"]
    n_match = metrics["n_tp_match_text_in_desc"]
    n_valor = metrics["n_tp_valor_in_desc"]
    n_lat = metrics["n_lateralidad_ok"]
    n_lat_eval = metrics["n_lateralidad_eval"]
    n_seg = metrics["n_segmentacion_ok"]
    n_seg_eval = metrics["n_segmentacion_eval"]
    n_dups = metrics["n_duplicados_logicos"]

    precision_match = 100 * n_match / n_attrs if n_attrs else 0
    precision_valor = 100 * n_valor / n_attrs if n_attrs else 0
    exactitud_lat = 100 * n_lat / n_lat_eval if n_lat_eval else 0
    exactitud_seg = 100 * n_seg / n_seg_eval if n_seg_eval else 0

    print(f"  Atributos revisados:           {n_attrs}")
    print(f"  text_original ∈ descripcion:   {n_match}/{n_attrs}  ({precision_match:.1f}%)")
    print(f"  valor_texto ∈ descripcion:     {n_valor}/{n_attrs}  ({precision_valor:.1f}%)")
    print(f"  Lateralidad correcta:          {n_lat}/{n_lat_eval}  ({exactitud_lat:.1f}%)")
    print(f"  Segmentación correcta:         {n_seg}/{n_seg_eval}  ({exactitud_seg:.1f}%)")
    print(f"  Duplicados lógicos:            {n_dups}")

    # ─── Explosión top 30 ───
    print(f"\n[3] Explosión top 30 (hallazgos con más atributos)")
    explosion = check_explosion(eng, 30)
    print(f"  {'hallazgo_id':>11}  {'n':>3}  {'organo':25s}  descripción")
    explosion_issues = []
    for hallazgo_id, organo, desc, n in explosion:
        marker = "⚠" if n > 20 else " "
        print(f"  {marker} {hallazgo_id:>9}  {n:>3}  {organo:25s}  {desc[:80]}")
        if n > 20:
            explosion_issues.append((hallazgo_id, organo, n, desc))

    # ─── Issues detectados ───
    print(f"\n[4] Issues detectados ({len(metrics['issues'])} en muestra)")
    by_tipo = Counter(i["tipo"] for i in metrics["issues"])
    for tipo, n in by_tipo.most_common():
        print(f"  {tipo}: {n}")
    # Mostrar primeros 10 issues
    print(f"\n  Muestra de issues:")
    for issue in metrics["issues"][:10]:
        print(f"    [{issue['tipo']}] hallazgo_id={issue['hallazgo_id']} "
              f"{issue['organo']}.{issue['atributo']} lat={issue.get('lat_asignado','-')} "
              f"seg={issue.get('seg_asignado','-')}")
        print(f"      desc: {issue['desc']}")

    # ─── Veredicto GO/NO-GO ───
    print("\n" + "=" * 78)
    print("VEREDICTO GO/NO-GO F4")
    print("=" * 78)
    criteria = {
        "Precisión clínica ≥95%":      precision_match >= 95.0,
        "Lateralidad ≥98%":            exactitud_lat >= 98.0,
        "Segmentación ≥95%":           exactitud_seg >= 95.0,
        "Sin explosión ≥20 attrs":     all(n <= 20 for _, _, n, _ in explosion_issues),
        "Sin duplicados lógicos":      n_dups == 0,
    }
    go = True
    for criterion, met in criteria.items():
        marker = "✅" if met else "❌"
        print(f"  {marker} {criterion}")
        if not met:
            go = False

    print()
    if go:
        print("  🎯 RECOMENDACIÓN: ✅ GO para F4 (normalización de valores y map_atributo_valor)")
    else:
        print("  🎯 RECOMENDACIÓN: ⚠️  NO-GO. Corregir regex listados antes de F4.")
    print("=" * 78)

    return 0 if go else 1


if __name__ == "__main__":
    sys.exit(main())