"""F3.1 — Propuesta de dim_valor_atributo basada en corpus.

Para cada (organo, atributo) define valores canónicos + regex de extracción.
Cuenta frecuencia en RAW. Genera propuesta concreta para poblar
dim_valor_atributo.

No escribe en silver.db.

**Ajustes aprobados (F3.0):**
1. Riñones.relacion_corticomedular: regex captura 'cortico medular' opcional
2. Riñones.ecogenicidad: agregados patrones AUMENTADA_DE / DISMINUIDA_DE / CORTICAL_*
3. Gestación.prenez: ELIMINADO (0% cobertura)
4. Bazo.forma / Bazo.margenes: MANTENIDOS (decisión diferida)
5. Próstata.tamano: normalizado a NORMAL único
6. dim_valor_atributo: agregada columna patron_extraccion, eliminada organo_id
"""
from __future__ import annotations

import io
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from sqlalchemy import text  # noqa: E402

from informes_vet import db  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "F3_1_DIM_VALOR_PROPUESTA.md"

# ════════════════════════════════════════════════════════════════════════
# PROPUESTAS DE VALORES CANÓNICOS
# Formato: (organo, atributo) -> [(valor_canonico, regex), ...]
# Orden: más específico primero (ej: "semi pletorica" antes que "pletorica")
# ════════════════════════════════════════════════════════════════════════

VALUE_PROPOSALS: dict[tuple[str, str], list[tuple[str, str]]] = {
    # ─── VEJIGA ───
    ("Vejiga", "replecion"): [
        ("SEMI_PLETORICA",  r"\bsemi\s+plet[oó]ric[ao]\b"),
        ("PLETORICA",        r"\bplet[oó]ric[ao]\b"),
        ("SEMI_DEPLETADA",   r"\bsemi\s+depletad[oa]\b"),
        ("DEPLETADA",        r"\bdepletad[oa]\b"),
        ("DISTENDIDA",       r"\bdistendid[oa]\b"),
        ("VACIA",            r"\bvac[ií][oa]\b"),
        ("REPLECION_CONSERVADA", r"\breplecci[oó]n\s+conservad[oa]\b"),
        ("RETENCION",        r"\bretenci[oó]n\b"),
    ],
    ("Vejiga", "contenido"): [
        ("ANECOICO",         r"\banecoic[oa]?\b"),
        ("HIPERECOICO",      r"\bhiperecoic[oa]?\b"),
        ("HOMOGENEO",        r"\bhomog[ée]ne[oa]\b"),
        ("HETEROGENEO",      r"\bheterog[ée]ne[oa]\b"),
        ("SEDIMENTO",        r"\bsediment[oa]?\b"),
        ("GRANULAR",         r"\bgranular\b"),
        ("PUNTIFORME",       r"\bpuntiform"),
    ],
    ("Vejiga", "homogeneidad_contenido"): [
        ("HOMOGENEO",            r"\bhomog[ée]ne[oa]\b"),
        ("HETEROGENEO",          r"\bheterog[ée]ne[oa]\b"),
        ("HETEROGENEO_LEVE",     r"\b(leve|levemente|discretamente)\s+heterog[ée]ne[oa]\b"),
        ("HETEROGENEO_MODERADO", r"\bmoderad[oa]?\s+heterog[ée]ne[oa]\b"),
    ],
    ("Vejiga", "bordes_internos"): [
        ("REGULARES",   r"\bbordes?\s+intern[oa]s?\s+regular(es)?\b"),
        ("IRREGULARES", r"\bbordes?\s+intern[oa]s?\s+irregular(es)?\b"),
        ("LISOS",       r"\bbordes?\s+intern[oa]s?\s+l[io]s[oa]s?\b"),
        ("CONSERVADOS", r"\bbordes?\s+intern[oa]s?\s+conservad[oa]s?\b"),
    ],
    ("Vejiga", "grosor_pared"): [
        ("CONSERVADO",  r"\bgrosor\s+conservad[oa]\b"),
        ("ENGROSADO",   r"\bengrosad[oa]\b"),
        ("AUMENTADO",   r"\bgrosor\s+[a-záéíóúñ]+\s+aumentad[oa]\b"),
        ("AUMENTADO",   r"\bgrosor\s+aumentad[oa]\b"),
        ("DISMINUIDO",  r"\bgrosor\s+[a-záéíóúñ]+\s+disminuid[oa]\b"),
        ("DISMINUIDO",  r"\bgrosor\s+disminuid[oa]\b"),
        ("NORMAL",      r"\bgrosor\s+normal\b"),
    ],
    # ─── PRÓSTATA ───
    ("Próstata", "forma"): [
        ("OVALADA",     r"\b(forma\s+)?ovalad[oa]\b"),
        ("REDONDEADA",  r"\b(forma\s+)?redondead[oa]\b"),
        ("GLOBOSA",     r"\b(forma\s+)?globos[oa]\b"),
        ("OVOIDE",      r"\b(forma\s+)?ovoid(e|al)\b"),
        ("IRREGULAR",   r"\bforma\s+irregular\b"),
        ("CONSERVADA",  r"\bforma\s+conservad[oa]\b"),
    ],
    ("Próstata", "lobulacion"): [
        ("BILOBULADA",   r"\bbilobulad[oa]\b"),
        ("UNILOBULADA",  r"\bunilobulad[oa]\b"),
        ("LOBULADA",     r"\blobulad[oa]\b"),
        ("NO_LOBULADA",  r"\bno\s+lobulad[oa]\b"),
    ],
    ("Próstata", "tamano"): [
        ("NORMAL",              r"\btama[ñn]o\s+normal\b"),
        ("NORMAL",              r"\btama[ñn]o\s+dentro\s+de\s+rango\b"),
        ("NORMAL",              r"\btama[ñn]o\s+conservad[oa]\b"),
        ("NORMAL",              r"\bdentro\s+de\s+rango\b"),
        ("AUMENTADO",           r"\btama[ñn]o\s+aumentad[oa]\b"),
        ("DISMINUIDO",          r"\btama[ñn]o\s+disminuid[oa]\b"),
        ("LEVEMENTE_AUMENTADO", r"\b(leve|levemente)\s+(de\s+)?tama[ñn]o\b"),
        ("MODERADAMENTE_AUMENTADO", r"\b(moderad[oa]|moderadamente)\s+(de\s+)?tama[ñn]o\b"),
        ("SEVERAMENTE_AUMENTADO",  r"\b(sever[oa]|severamente)\s+(de\s+)?tama[ñn]o\b"),
    ],
    ("Próstata", "ecogenicidad"): [
        ("HIPOECOICA",   r"\bhipoecoic[oa]\b"),
        ("HIPERECOICA",  r"\bhiperecoic[oa]\b"),
        ("AUMENTADA",    r"\becogenicidad\s+aumentad[oa]\b"),
        ("DISMINUIDA",   r"\becogenicidad\s+disminuid[oa]\b"),
        ("CONSERVADA",   r"\becogenicidad\s+conservad[oa]\b"),
        ("NORMAL",       r"\becogenicidad\s+normal\b"),
    ],
    ("Próstata", "homogeneidad"): [
        ("HOMOGENEA",       r"\bhomog[ée]ne[oa]\b"),
        ("HETEROGENEA",     r"\bheterog[ée]ne[oa]\b"),
        ("HOMOGENEA_LEVE",  r"\b(leve|levemente)\s+heterog[ée]ne[oa]\b"),
        ("HOMOGENEA_MODERADA", r"\bmoderad[oa]\s+heterog[ée]ne[oa]\b"),
    ],
    # ─── RIÑONES ───
    ("Riñones", "forma"): [
        ("OVALADO",      r"\b(forma\s+)?ovalad[oa]\b"),
        ("RENAL",        r"\bren(al|iform)\b"),
        ("GLOBOSO",      r"\b(forma\s+)?globos[oa]\b"),
        ("REDONDEADO",   r"\b(forma\s+)?redondead[oa]\b"),
        ("IRREGULAR",    r"\bforma\s+irregular\b"),
        ("CONSERVADA",   r"\bforma\s+conservad[oa]\b"),
        ("NORMAL",       r"\bforma\s+y\s+tama[ñn]o\s+normales?\b"),
    ],
    ("Riñones", "tamano"): [
        ("NORMAL",              r"\btama[ñn]o\s+normal\b"),
        ("DENTRO_DE_RANGO",     r"\btama[ñn]o\s+dentro\s+de\s+rango\b"),
        ("CONSERVADO",          r"\btama[ñn]o\s+conservad[oa]\b"),
        ("AUMENTADO",           r"\btama[ñn]o\s+aumentad[oa]\b"),
        ("DISMINUIDO",          r"\btama[ñn]o\s+disminuid[oa]\b"),
        ("LEVEMENTE_AUMENTADO", r"\b(leve|levemente)\s+aumentad[oa]\b"),
        ("MODERADAMENTE_AUMENTADO", r"\b(moderad[oa]|moderadamente)\s+aumentad[oa]\b"),
        ("SEVERAMENTE_AUMENTADO",  r"\b(sever[oa]|severamente|marcadamente)\s+aumentad[oa]\b"),
    ],
    ("Riñones", "bordes"): [
        ("LISOS",          r"\bbordes\s+l[io]s[oa]s?\b"),
        ("REGULARES",      r"\bbordes\s+regular(es)?\b"),
        ("IRREGULARES",    r"\bbordes\s+irregular(es)?\b"),
        ("LEVEMENTE_IRREGULARES", r"\bbordes\s+levemente\s+irregular(es)?\b"),
        ("MAL_DEFINIDOS",  r"\bbordes\s+mal\s+definidos?\b"),
        ("BIEN_DEFINIDOS", r"\bbordes\s+bien\s+definidos?\b"),
        ("CONSERVADOS",    r"\bbordes\s+conservad[oa]s?\b"),
    ],
    ("Riñones", "ecogenicidad"): [
        ("HIPOECOICA",     r"\bhipoecoic[oa]\b"),
        ("HIPERECOICA",    r"\bhiperecoic[oa]\b"),
        ("CONSERVADA",     r"\becogenicidad\s+conservad[oa]\b"),
        ("AUMENTADA",      r"\becogenicidad\s+aumentad[oa]\b"),
        ("DISMINUIDA",     r"\becogenicidad\s+disminuid[oa]\b"),
        ("ADECUADA",       r"\becogenicidad\s+adecuada\b"),
        ("NORMAL",         r"\becogenicidad\s+normal\b"),
        ("AUMENTADA",      r"\baumento\s+de\s+ecogenicidad\b"),
        ("DISMINUIDA",     r"\bdisminuci[oó]n\s+de\s+ecogenicidad\b"),
        ("CORTICAL_HIPOECOICA", r"\b(corteza|c[oó]rtex|cortical)\s+hipoecoic[oa]\b"),
        ("CORTICAL_HIPERECOICA", r"\b(corteza|c[oó]rtex|cortical)\s+hiperecoic[oa]\b"),
        # Adverbio entre ecogenicidad y adjetivo (corteza ecogenicidad levemente disminuida)
        ("DISMINUIDA",     r"\becogenicidad\s+(leve|levemente|discreta|discretamente|moderada|moderadamente|severa|severamente)\s+disminuid[oa]\b"),
        ("AUMENTADA",      r"\becogenicidad\s+(leve|levemente|discreta|discretamente|moderada|moderadamente|severa|severamente)\s+aumentad[oa]\b"),
        # Hígado-style patterns also apply here
        ("CONSERVADA",     r"\b(ecogenicidad\s+)?(corteza|c[oó]rtex)\s+conservad[oa]\b"),
    ],
    ("Riñones", "diferenciacion_corticomedular"): [
        ("BIEN_DEFINIDA",   r"\bbien\s+definid[oa]\b"),
        ("DEFINIDA",        r"\bdiferenciaci[oó]n\s+(definid[oa]|presente)\b"),
        ("MAL_DEFINIDA",    r"\b(mal|pobremente)\s+definid[oa]\b"),
        ("PRESERVADA",      r"\bdiferenciaci[oó]n\s+(preservad[oa]|conservad[oa])\b"),
        ("AUSENTE",         r"\bsin\s+diferenciaci[oó]n\b"),
    ],
    ("Riñones", "relacion_corticomedular"): [
        ("ADECUADA",    r"\brelaci[oó]n\s+(cort[io]co[- ]?medular\s+)?(adecuada|normal|conservad[oa])\b"),
        ("AUMENTADA",   r"\brelaci[oó]n\s+(cort[io]co[- ]?medular\s+)?aumentad[oa]\b"),
        ("DISMINUIDA",  r"\brelaci[oó]n\s+(cort[io]co[- ]?medular\s+)?disminuid[oa]\b"),
        ("INVERTIDA",   r"\brelaci[oó]n\s+(cort[io]co[- ]?medular\s+)?invertid[oa]\b"),
        ("PERDIDA",     r"\b(perdid[oa]|ausentad[oa])\s+la\s+relaci[oó]n\s+(cort[io]co[- ]?medular|c[- ]?m)\b"),
        ("SIN_RELACION", r"\bsin\s+relaci[oó]n\s+(cort[io]co[- ]?medular|c[- ]?m)\b"),
    ],
    ("Riñones", "compromiso_pelvico"): [
        ("SIN_COMPROMISO",       r"\bsin\s+compromiso\s+p[ée]lvic[oa]?\b"),
        ("CON_COMPROMISO",       r"\bcon\s+compromiso\s+p[ée]lvic[oa]?\b"),
        ("ECTASIA_PELVICA",      r"\bectasia\s+p[ée]lvic[oa]?\b"),
        ("DILATACION_PELVICA",   r"\b(dilataci[oó]n|pelvis\s+dilatad[oa])\b"),
        ("HIDRONEFROSIS",        r"\bhidronefrosis\b"),
    ],
    # ─── BAZO ───
    ("Bazo", "tamano"): [
        ("NORMAL",            r"\btama[ñn]o\s+normal\b"),
        ("NORMAL",            r"\btama[ñn]o\s+[y,]\s+\w+\s+normales?\b"),
        ("DENTRO_DE_RANGO",   r"\bdentro\s+de\s+rango\b"),
        ("AUMENTADO",         r"\baumentad[oa]\b"),
        ("DISMINUIDO",        r"\bdisminuid[oa]\b"),
        ("CONSERVADO",        r"\btama[ñn]o\s+conservad[oa]\b"),
    ],
    ("Bazo", "forma"): [
        ("CONSERVADA", r"\bforma\s+conservad[oa]\b"),
        ("NORMAL",     r"\bforma\s+normal\b"),
    ],
    ("Bazo", "margenes"): [
        ("REGULARES",   r"\bm[áa]rgenes\s+regular(es)?\b"),
        ("IRREGULARES", r"\bm[áa]rgenes\s+irregular(es)?\b"),
        ("CONSERVADOS", r"\bm[áa]rgenes\s+conservad[oa]s?\b"),
    ],
    ("Bazo", "arquitectura"): [
        ("CONSERVADA", r"\barquitectura\s+conservad[oa]\b"),
        ("ALTERADA",   r"\barquitectura\s+alterad[oa]\b"),
        ("NORMAL",     r"\barquitectura\s+normal\b"),
    ],
    # ─── ESTÓMAGO ───
    ("Estómago", "distension"): [
        ("SEMI_DISTENDIDO", r"\bsemi\s+distendid[oa]\b"),
        ("DISTENDIDO",      r"\bdistendid[oa]\b"),
        ("PLETORICO",       r"\bplet[oó]ric[oa]\b"),
        ("COLAPSADO",       r"\bcolapsad[oa]\b"),
        ("VACIO",           r"\bvac[ií]o\b"),
    ],
    ("Estómago", "contenido"): [
        ("ALIMENTICIO", r"\balimenticio\b"),
        ("MUCOSO",      r"\bmucos[oa]\b"),
        ("LIQUIDO",     r"\bl[ií]quid[oa]\b"),
        ("GAS",         r"\bgas\b"),
        ("SIN_CONTENIDO", r"\bsin\s+contenido\b"),
    ],
    ("Estómago", "estratificacion_pared"): [
        ("PRESENTE", r"\bpared(es)?\s+estratificad[oa]s?\b"),
        ("AUSENTE",  r"\bpared(es)?\s+no\s+estratificad[oa]s?\b"),
    ],
    ("Estómago", "grosor_pared"): [
        ("CONSERVADO", r"\bgrosor\s+conservad[oa]\b"),
        ("AUMENTADO",  r"\bgrosor\s+[a-záéíóúñ]+\s+aumentad[oa]\b"),
        ("AUMENTADO",  r"\bgrosor\s+aumentad[oa]\b"),
        ("DISMINUIDO", r"\bgrosor\s+[a-záéíóúñ]+\s+disminuid[oa]\b"),
        ("DISMINUIDO", r"\bgrosor\s+disminuid[oa]\b"),
        ("NORMAL",     r"\bgrosor\s+normal\b"),
    ],
    # ─── HÍGADO ───
    ("Hígado", "tamano"): [
        ("NORMAL",              r"\btama[ñn]o\s+normal\b"),
        ("AUMENTADO",           r"\btama[ñn]o\s+aumentad[oa]\b"),
        ("DISMINUIDO",          r"\btama[ñn]o\s+disminuid[oa]\b"),
        ("LEVEMENTE_AUMENTADO", r"\b(leve|levemente)\s+(de\s+)?tama[ñn]o\b"),
        ("MODERADAMENTE_AUMENTADO", r"\b(moderad[oa]|moderadamente)\s+(de\s+)?tama[ñn]o\b"),
        ("SEVERAMENTE_AUMENTADO",  r"\b(sever[oa]|severamente)\s+(de\s+)?tama[ñn]o\b"),
        ("CONSERVADO",          r"\btama[ñn]o\s+conservad[oa]\b"),
    ],
    ("Hígado", "margenes"): [
        ("LISOS",         r"\bm[áa]rgenes\s+l[io]s[oa]s?\b"),
        ("REDONDEADOS",   r"\bm[áa]rgenes\s+redondead[oa]s?\b"),
        ("IRREGULARES",   r"\bm[áa]rgenes\s+irregular(es)?\b"),
        ("MAL_DEFINIDOS", r"\bm[áa]rgenes\s+mal\s+definidos?\b"),
        ("CONSERVADOS",   r"\bm[áa]rgenes\s+conservad[oa]s?\b"),
    ],
    ("Hígado", "bordes"): [
        ("LISOS",       r"\bbordes\s+l[io]s[oa]s?\b"),
        ("REGULARES",   r"\bbordes\s+regular(es)?\b"),
        ("IRREGULARES", r"\bbordes\s+irregular(es)?\b"),
        ("CONSERVADOS", r"\bbordes\s+conservad[oa]s?\b"),
    ],
    ("Hígado", "ecogenicidad"): [
        ("HIPOECOICA",            r"\bhipoecoic[oa]\b"),
        ("HIPERECOICA",           r"\bhiperecoic[oa]\b"),
        ("AUMENTADA",             r"\becogenicidad\s+aumentad[oa]\b"),
        ("DISMINUIDA",            r"\becogenicidad\s+disminuid[oa]\b"),
        ("NORMAL",                r"\becogenicidad\s+normal\b"),
        ("CONSERVADA",            r"\becogenicidad\s+conservad[oa]\b"),
        ("LEVEMENTE_AUMENTADA",   r"\b(leve|levemente)\s+(de\s+)?ecogenicidad\b"),
    ],
    ("Hígado", "granulado"): [
        ("FINO",    r"\bgranulad[oa]?\s+fino\b"),
        ("GRUESO",  r"\bgranulad[oa]?\s+grues[oa]\b"),
    ],
    ("Hígado", "arquitectura"): [
        ("CONSERVADA", r"\barquitectura\s+conservad[oa]\b"),
        ("ALTERADA",   r"\barquitectura\s+alterad[oa]\b"),
        ("NORMAL",     r"\barquitectura\s+normal\b"),
    ],
    ("Hígado", "patron_vascular"): [
        ("CONSERVADO",          r"\bpatr[óo]n\s+vascular\s+conservad[oa]\b"),
        ("ALTERADO",            r"\bpatr[óo]n\s+vascular\s+alterad[oa]\b"),
        ("NORMAL",              r"\bpatr[óo]n\s+vascular\s+normal\b"),
        ("VASOS_CONSERVADOS",   r"\bvasculatura?\s+conservad[oa]\b"),
    ],
    # ─── VESÍCULA ───
    ("Vesícula", "distension"): [
        ("SEMI_DISTENDIDA", r"\bsemi\s+distendid[oa]\b"),
        ("DISTENDIDA",      r"\bdistendid[oa]\b"),
        ("PLETORICA",       r"\bplet[oó]ric[oa]\b"),
        ("DEPLETADA",       r"\bdepletad[oa]\b"),
    ],
    ("Vesícula", "contenido"): [
        ("ANECOICO",      r"\banecoic[oa]?\b"),
        ("HIPERECOICO",   r"\bhiperecoic[oa]?\b"),
        ("BARRO_BILIAR",  r"\bbarro\s+biliar\b"),
        ("CALCULOS",      r"\bc[áa]lcul[oa]s?\b"),
        ("SEDIMENTO",     r"\bsediment[oa]?\b"),
    ],
    ("Vesícula", "bordes_internos"): [
        ("REGULARES",   r"\bbordes?\s+intern[oa]s?\s+regular(es)?\b"),
        ("IRREGULARES", r"\bbordes?\s+intern[oa]s?\s+irregular(es)?\b"),
        ("LISOS",       r"\bbordes?\s+intern[oa]s?\s+l[io]s[oa]s?\b"),
    ],
    ("Vesícula", "grosor_pared"): [
        ("CONSERVADO", r"\bgrosor\s+conservad[oa]\b"),
        ("ENGROSADO",  r"\bengrosad[oa]\b"),
        ("AUMENTADO",  r"\bgrosor\s+[a-záéíóúñ]+\s+aumentad[oa]\b"),
        ("AUMENTADO",  r"\bgrosor\s+aumentad[oa]\b"),
    ],
    # ─── INTESTINO (segmentos) ───
    # Nota: contenido/grosor_pared/estratificacion_pared aplican al segmento
    # duodeno_yeyuno. Colon usa 'paredes' en su lugar (más simple y específico).
    # Los pares Intestino.contenido × 2 segmentos comparten el mismo catálogo
    # de valores canónicos.
    ("Intestino", "contenido"): [
        ("ALIMENTICIO",               r"\balimenticio\b"),
        ("MUCOSO",                    r"\bmucos[oa]\b"),
        ("FECAL",                     r"\bfec[ao]l\b"),
        ("LIQUIDO",                   r"\bl[ií]quid[oa]\b"),
        ("CON_PREDOMINIO_ALIMENTICIO", r"\bpredominio\s+(de\s+)?alimenticio\b"),
        ("CON_PREDOMINIO_FECAL",      r"\bpredominio\s+(de\s+)?fec[ao]l\b"),
    ],
    ("Intestino", "grosor_pared"): [
        ("CONSERVADO",                r"\bgrosor\s+conservad[oa]\b"),
        ("DISCRETAMENTE_AUMENTADO",   r"\b(discret[oa]|discretamente)\s+aumentad[oa]\b"),
        ("LEVEMENTE_AUMENTADO",       r"\b(leve|levemente)\s+aumentad[oa]\b"),
        ("MODERADAMENTE_AUMENTADO",   r"\b(moderad[oa]|moderadamente)\s+aumentad[oa]\b"),
        ("SEVERAMENTE_AUMENTADO",     r"\b(sever[oa]|severamente|marcadamente)\s+aumentad[oa]\b"),
        ("AUMENTADO",                 r"\bgrosor\s+aumentad[oa]\b"),
    ],
    ("Intestino", "estratificacion_pared"): [
        ("PRESENTE", r"\bpared(es)?\s+estratificad[oa]s?\b"),
        ("AUSENTE",  r"\bpared(es)?\s+no\s+estratificad[oa]s?\b"),
    ],
    ("Intestino", "paredes"): [
        # F3.2 fix: regex previo solo capturaba "paredes conservado" pero el
        # texto real dice "paredes de grosor conservado" (grosor interpuesto).
        ("CONSERVADO", r"\bpared(es)?\s+de\s+grosor\s+conservad[oa]\b"),
        ("CONSERVADO", r"\bpared(es)?\s+conservad[oa]\b"),
        ("AUMENTADO",  r"\bpared(es)?\s+aumentad[oa]\b"),
        ("DISMINUIDO", r"\bpared(es)?\s+disminuid[oa]\b"),
    ],
    ("Intestino", "peristaltismo"): [
        ("NORMAL",     r"\bperistaltismo\s+normal\b"),
        ("AUMENTADO",  r"\bperistaltismo\s+aumentad[oa]\b"),
        ("DISMINUIDO", r"\bperistaltismo\s+disminuid[oa]\b"),
        ("AUSENTE",    r"\bperistaltismo\s+ausente\b"),
        ("CONSERVADO", r"\bperistaltismo\s+conservad[oa]\b"),
    ],
    # ─── PÁNCREAS ───
    ("Páncreas", "preservacion"): [
        ("CONSERVADO",    r"\bconservad[oa]\b"),
        ("PRESERVADO",    r"\bpreservad[oa]\b"),
        ("ALTERADO",      r"\balterad[oa]\b"),
        ("NORMAL",        r"\bnormal\b"),
        ("NO_EVALUADO",   r"\bno\s+evaluad[oa]\b"),
    ],
    ("Páncreas", "aspecto_peripancreatico"): [
        ("NORMAL",   r"\bnormal\b"),
        ("ALTERADO", r"\balterad[oa]\b"),
    ],
    # ─── ADRENALES ───
    ("Adrenales", "forma"): [
        ("OVALADA",     r"\b(forma\s+)?ovalad[oa]\b"),
        ("CONSERVADA",  r"\bforma\s+conservad[oa]\b"),
        ("NORMAL",      r"\bforma\s+normal\b"),
    ],
    # F3.2 fix: usar 'tamanho' (con ñ) para alinear con el par en _PARES_SEED.
    # Antes 'tamano' (sin ñ) provocaba lookup miss en dim_organo_atributo
    # porque el par está registrado como (Adrenales, tamanho, ...).
    ("Adrenales", "tamanho"): [
        ("NORMAL",       r"\btama[ñn]o\s+normal\b"),
        ("NORMAL",       r"\btama[ñn]o\s+[y,]\s+[a-záéíóúñ]+\s+normales?\b"),
        ("AUMENTADO",    r"\baumentad[oa]\b"),
        ("DISMINUIDO",   r"\bdisminuid[oa]\b"),
        ("CONSERVADO",   r"\btama[ñn]o\s+[y,]\s+[a-záéíóúñ]+\s+conservad[oa]\b"),
        ("CONSERVADO",   r"\bconservad[oa]\b"),
    ],
    ("Adrenales", "arquitectura"): [
        ("CONSERVADA",   r"\barquitectura\s+conservad[oa]\b"),
        ("CONSERVADA",   r"\barquitectura\s+[y,]\s+[a-záéíóúñ]+\s+conservad[oa]\b"),
        ("NORMAL",       r"\barquitectura\s+normales?\b"),
    ],
    # ─── LINFONODOS ───
    ("Linfonodos", "presencia"): [
        ("PRESENTE",        r"\bpresente\b"),
        ("AUSENTE",         r"\bausente\b"),
        ("NO_SE_OBSERVAN",  r"\bno\s+se\s+observ[ao]n\b"),
    ],
    ("Linfonodos", "compromiso"): [
        ("NO_COMPROMETIDO",  r"\bno\s+(se\s+)?(observan|observan\s+n[oó]dulos?\s+)?comprometid[oa]s?\b"),
        ("NO_COMPROMETIDO",  r"\bno\s+(se\s+)?observan\s+[a-záéíóúñ\s]+comprometid[oa]s?\b"),
        ("NO_COMPROMETIDO",  r"\bsin\s+(n[oó]dulos?\s+)?comprometid[oa]s?\b"),
        ("COMPROMETIDO",     r"\bcomprometid[oa]s?\b"),
        # Anclado a "linfonodo*/linfátic*/nódulo* + aspecto + conservad*".
        # Requiere la palabra "aspecto" entre el sujeto (nódulo/linfonodo)
        # y "conservad*" para evitar FP del tipo "linfonodos ... de forma
        # conservada" donde "conservada" pertenece al atributo `forma`.
        ("CONSERVADO",       r"\b(linfonod[oa]s?|linf[aá]tic[oa]s?|n[oó]dul[oa]s?)[^.,;]{0,80}?\baspecto[s]?\s+conservad[oa]s?\b"),
        # Variante: nódulo aislado "nódulos conservados" sin "aspecto" interpuesto
        ("CONSERVADO",       r"\bn[oó]dul[oa]s?\s+conservad[oa]s?\b"),
        # Variante: "nódulo linfático conservado" / "linfonodos conservados" sin "aspecto"
        # Restringido a gap corto (≤5 palabras) y SIN "forma" en el medio.
        ("CONSERVADO",       r"\b(linfonod[oa]s?|linf[aá]tic[oa]s?)[^.,;]{0,40}?\b(?!forma\b)\bconservad[oa]s?\b"),
        ("REACTIVO",         r"\breactiv[oa]s?\b"),
        ("NO_REACTIVO",      r"\bno\s+reactiv[oa]s?\b"),
    ],
    # ─── ÚTERO ───
    ("Útero", "tamano"): [
        ("AUMENTADO",        r"\baumentad[oa]\b"),
        ("DISMINUIDO",       r"\bdisminuid[oa]\b"),
        ("NORMAL",           r"\bnormal\b"),
        ("DENTRO_DE_RANGO",  r"\bdentro\s+de\s+rango\b"),
    ],
    ("Útero", "contenido"): [
        ("ANECOICO",       r"\banecoic[oa]?\b"),
        ("HIPERECOICO",    r"\bhiperecoic[oa]?\b"),
        ("HOMOGENEO",      r"\bhomog[ée]ne[oa]\b"),
        ("HETEROGENEO",    r"\bheterog[ée]ne[oa]\b"),
        ("LIQUIDO",        r"\bl[ií]quid[oa]\b"),
    ],
    ("Útero", "grosor_pared"): [
        ("ENGROSADO",      r"\bengrosad[oa]\b"),
        ("DELGADO",        r"\bdelgad[oa]s?\b"),
        ("CONSERVADO",     r"\bpared\s+conservad[oa]\b"),
        ("CONSERVADO",     r"\bgrosor\s+conservad[oa]\b"),
    ],
    # ─── OVARIOS ───
    ("Ovarios", "tamano"): [
        ("NORMAL",     r"\btama[ñn]o\s+normal\b"),
        ("AUMENTADO",  r"\baumentad[oa]\b"),
        ("DISMINUIDO", r"\bdisminuid[oa]\b"),
    ],
    ("Ovarios", "forma"): [
        ("OVALADO",    r"\bovalad[oa]\b"),
        ("REDONDEADO", r"\bredondead[oa]\b"),
    ],
    # ─── TESTÍCULOS ───
    ("Testículos", "tamano"): [
        ("NORMAL",     r"\btama[ñn]o\s+normal\b"),
        ("NORMAL",     r"\btama[ñn]o\s+conservad[oa]\b"),
        ("AUMENTADO",  r"\baumentad[oa]\b"),
        ("DISMINUIDO", r"\bdisminuid[oa]\b"),
    ],
    ("Testículos", "forma"): [
        ("OVALADO",    r"\bovalad[oa]\b"),
        ("CONSERVADA", r"\bforma\s+conservad[oa]\b"),
        ("NORMAL",     r"\bforma\s+normal\b"),
    ],
    ("Testículos", "ecogenicidad"): [
        ("HIPOECOICA",  r"\bhipoecoic[oa]\b"),
        ("HIPERECOICA", r"\bhiperecoic[oa]\b"),
        ("NORMAL",      r"\becogenicidad\s+normal\b"),
        ("CONSERVADA",  r"\becogenicidad\s+conservad[oa]\b"),
    ],
    ("Testículos", "homogeneidad"): [
        ("HOMOGENEO",   r"\bhomog[ée]ne[oa]\b"),
        ("HETEROGENEO", r"\bheterog[ée]ne[oa]\b"),
    ],
    # ─── GESTACIÓN ───
    # NOTA: "Gestación.prenez" eliminado por cobertura 0%. El corpus no usa
    # explícitamente el término "preñez". La presencia de gestación activa se
    # infiere por la existencia de la fila en raw.hallazgos con organo='Gestación'.
    ("Gestación", "fetos"): [
        ("UNO",          r"\b(al\s+menos\s+)?1\s+feto\b"),
        ("DOS",          r"\b(al\s+menos\s+)?2\s+fetos?\b"),
        ("TRES",         r"\b(al\s+menos\s+)?3\s+fetos?\b"),
        ("CUATRO",       r"\b(al\s+menos\s+)?4\s+fetos?\b"),
        ("CINCO",        r"\b(al\s+menos\s+)?5\s+fetos?\b"),
        ("SEIS",         r"\b(al\s+menos\s+)?6\s+fetos?\b"),
        ("SIETE",        r"\b(al\s+menos\s+)?7\s+fetos?\b"),
        ("OCHO",         r"\b(al\s+menos\s+)?8\s+fetos?\b"),
        ("NUEVE_O_MAS",  r"\b(al\s+menos\s+)?(9|10|11|12|\d{2,})\s+fetos?\b"),
    ],
    # ─── CAVIDAD ABDOMINAL ───
    ("Cavidad abdominal", "liquido_libre"): [
        ("PRESENTE",   r"\bl[ií]quido\s+libre\b"),
        ("AUSENTE",    r"\bno\s+se\s+observ[ao]\s+l[ií]quido\s+libre\b"),
        ("ABUNDANTE",  r"\babundante\s+l[ií]quido\s+libre\b"),
        ("MODERADO",   r"\bmoderad[oa]\s+l[ií]quido\s+libre\b"),
        ("ESCASO",     r"\bescaso\s+l[ií]quido\s+libre\b"),
    ],
    ("Cavidad abdominal", "masas"): [
        ("PRESENTE", r"\bmasa(s)?\b"),
        ("AUSENTE",  r"\bsin\s+masa(s)?\b"),
    ],
}

BINARY_ATRIBUTOS = {
    "Linfonodos.presencia",
    "Linfonodos.compromiso",
    "Páncreas.preservacion",
    "Páncreas.aspecto_peripancreatico",
    "Riñones.compromiso_pelvico",
    "Cavidad abdominal.liquido_libre",
    "Cavidad abdominal.masas",
}

NUMERIC_ATRIBUTOS = {"Gestación.fetos"}


def main():
    eng = db.get_engine("sqlite", ROOT)
    with eng.begin() as conn:
        rows = conn.execute(text("SELECT organo, descripcion FROM hallazgos")).all()

    organo_to_descs = defaultdict(list)
    for org, desc in rows:
        organo_to_descs[org].append(desc)

    total_hallazgos = len(rows)
    L = []
    P = L.append

    P("# F3.1 — dim_valor_atributo: propuesta basada en corpus")
    P("")
    P("**Estado:** 📋 PROPUESTA (pre-implementación)")
    P("**Generado:** 2026-06-22")
    P("**Método:** para cada (órgano, atributo) se define un set de regex con")
    P("valor canónico asociado. Se corre contra las 27.866 descripciones RAW y")
    P("se reportan las frecuencias observadas.")
    P("")
    P("**No escribe en silver.db.** La propuesta es para revisión antes de")
    P("implementar `dim_valor_atributo`.")
    P("")
    P("---")
    P("")

    # ─── §0 Resumen ejecutivo ───
    P("## 0. Resumen ejecutivo")
    P("")
    # Deduplicar: si el mismo (atributo, canon) aparece en varios órganos,
    # cuenta solo 1 fila en dim_valor_atributo (modelo global).
    pares_unicos: set[tuple[str, str]] = set()
    valores_unicos: set[tuple[str, str]] = set()
    for (organo, atributo), proposals in VALUE_PROPOSALS.items():
        pares_unicos.add((organo, atributo))
        for canon, _pat in proposals:
            valores_unicos.add((atributo, canon))
    pares = len(pares_unicos)
    total_canonicos_unicos = len(valores_unicos)

    # Conteos raw: filas propuestas (con duplicados organo/atributo) y duplicadas
    total_canonicos_con_dup = sum(len(p) for p in VALUE_PROPOSALS.values())

    P(f"- Pares (órgano, atributo) con propuesta: **{pares_unicos}**")
    P(f"- Filas propuestas (con dup organo): **{sum(len(p) for p in VALUE_PROPOSALS.values())}**")
    P(f"- Valores canónicos únicos (atributo, valor): **{total_canonicos_unicos}**")
    P(f"- Cardinalidad final estimada de `dim_valor_atributo` (FK atributo_id): **{total_canonicos_unicos} filas**")
    P("")
    P("**Decisión clave:** `dim_valor_atributo` se modela **global** (sin `organo_id`).")
    P("Justificación: el mismo par `(atributo_id, valor)` puede reutilizarse en")
    P("varios órganos (ej: `tamano.NORMAL` aplica a Próstata, Riñones, Hígado,")
    P("Bazo, Adrenales, Útero, Ovarios, Testículos). La dimensión anatómica se")
    P("resuelve vía `dim_organo_atributo.organo_id`, no en `dim_valor_atributo`.")
    P("El sinonimo text es independiente del órgano (mismo patrón regex funciona")
    P("en cualquier descripción). Esto reduce duplicación y permite consolidar")
    P("ajustes de catálogo.")
    P("")
    P("**Atributos binarios:** " + ", ".join(f"`{a}`" for a in sorted(BINARY_ATRIBUTOS)))
    P("")
    P("**Atributos numéricos:** " + ", ".join(f"`{a}`" for a in sorted(NUMERIC_ATRIBUTOS)))
    P("")
    P("**Ajustes aplicados al modelo:**")
    P("- ✅ Riñones.relacion_corticomedular: regex ahora captura 'relación cortico medular adecuada'")
    P("- ✅ Riñones.ecogenicidad: agregados patrones AUMENTADA_DE / DISMINUIDA_DE / CORTICAL_HIPOECOICA / CORTICAL_HIPERECOICA")
    P("- ✅ Gestación.prenez: ELIMINADO (cobertura 0% en corpus)")
    P("- ✅ Bazo.forma / Bazo.margenes: MANTENIDOS temporalmente (decisión diferida a F4)")
    P("- ✅ Próstata.tamano: normalizado a un único valor canónico NORMAL (absorbe DENTRO_DE_RANGO + CONSERVADO)")
    P("- ✅ dim_valor_atributo: agregada columna `patron_extraccion TEXT`")
    P("- ✅ dim_valor_atributo: eliminada columna `organo_id` (justificación arriba)")
    P("")
    P("---")
    P("")

    # ─── §A Tabla maestra ───
    P("## A. Distribución por (órgano, atributo)")
    P("")
    for (organo, atributo), proposals in VALUE_PROPOSALS.items():
        n_total = len(organo_to_descs.get(organo, []))
        canon_counts = Counter()
        uncaptured = 0
        for desc in organo_to_descs.get(organo, []):
            matched = None
            for canon, pat in proposals:
                if re.search(pat, desc, re.IGNORECASE):
                    matched = canon
                    break
            if matched:
                canon_counts[matched] += 1
            else:
                uncaptured += 1

        # Coverage of proposals
        matched_sum = sum(canon_counts.values())
        cobertura_propuestas = 100.0 * matched_sum / n_total if n_total else 0
        key = f"{organo}.{atributo}"
        es_bin = "🔘 binario" if key in BINARY_ATRIBUTOS else ""
        es_num = "🔢 numérico" if key in NUMERIC_ATRIBUTOS else ""

        P(f"### {organo}.{atributo} (n={n_total}) {es_bin} {es_num}")
        P("")
        P(f"| valor_canonico | patron_extraccion | n | % |")
        P(f"|---|---|---:|---:|")
        for canon, pat in proposals:
            n = canon_counts[canon]
            pct = 100.0 * n / n_total if n_total else 0
            pat_display = pat[:100]
            P(f"| `{canon}` | `{pat_display}` | {n} | {pct:.1f}% |")
        if uncaptured > 0:
            pct = 100.0 * uncaptured / n_total if n_total else 0
            P(f"| _(sin match)_ | — | {uncaptured} | {pct:.1f}% |")
        P(f"| **TOTAL matched** | | **{matched_sum}** | **{cobertura_propuestas:.1f}%** |")
        P("")

    # ─── §B Cardinalidad final ───
    P("---")
    P("")
    P("## B. Cardinalidad final propuesta para `dim_valor_atributo`")
    P("")
    P("Esquema objetivo:")
    P("")
    P("```sql")
    P("CREATE TABLE dim_valor_atributo (")
    P("    id              INTEGER PRIMARY KEY,")
    P("    atributo_id     INTEGER NOT NULL REFERENCES dim_atributo(id),")
    P("    valor           VARCHAR(64) NOT NULL,")
    P("    sinonimos       TEXT,                       -- lista textual de variantes")
    P("    patron_extraccion TEXT,                     -- regex canónica que detecta este valor")
    P("    es_binario_true BOOLEAN,                    -- si atributo es binario y este es el valor \"TRUE\"")
    P("    es_default      BOOLEAN DEFAULT FALSE,      -- valor por defecto cuando no hay match")
    P("    orden           INTEGER DEFAULT 0,           -- orden de display en UI")
    P("    activo          BOOLEAN DEFAULT TRUE,        -- soft-delete")
    P("    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
    P("    UNIQUE(atributo_id, valor)")
    P(");")
    P("```")
    P("")
    P("**Notas de diseño:**")
    P("- ❌ Sin `organo_id`: `dim_valor_atributo` es **global**. La dimensión anatómica")
    P("  se obtiene vía join `dim_organo_atributo`.")
    P("- ✅ `patron_extraccion`: regex que el ETL usa para detectar este valor en cualquier")
    P("  descripción del órgano correspondiente. Permite trazabilidad y reproducción.")
    P("- ✅ `es_binario_true`: para atributos binarios, marca cuál de los valores es \"TRUE\"")
    P("  (ej: en `Linfonodos.presencia`, `PRESENTE` es TRUE, `AUSENTE` es FALSE).")
    P("- ✅ `es_default`: valor fallback cuando no se detecta ninguno (típicamente NORMAL).")
    P("- ✅ UNIQUE(atributo_id, valor): un valor canónico aparece UNA vez por atributo.")
    P("")
    P("**Inserción propuesta (en orden de prioridad, deduplicada por atributo):**")
    P("")
    P("| atributo_id | valor | patron_extraccion | es_binario_true | es_default |")
    P("|---|---|---|---|---|")
    seen_atributo_valor: set[tuple[str, str]] = set()
    for (organo, atributo), proposals in VALUE_PROPOSALS.items():
        key_attr = f"{organo}.{atributo}"
        es_bin = key_attr in BINARY_ATRIBUTOS
        for canon, pat in proposals:
            key = (atributo, canon)
            if key in seen_atributo_valor:
                continue
            seen_atributo_valor.add(key)
            es_bin_true = "TRUE" if (es_bin and canon.upper() in {"PRESENTE", "SI", "SI_COMPROMISO", "CON_COMPROMISO", "NORMAL", "CONSERVADO", "PRESERVADO"}) else "FALSE"
            es_default = "TRUE" if canon.upper() == "NORMAL" else "FALSE"
            pat_display = pat[:80]
            P(f"| `{atributo}` | `{canon}` | `{pat_display}` | {es_bin_true} | {es_default} |")
    P("")
    P(f"**Total filas en `dim_valor_atributo`:** {len(seen_atributo_valor)}")
    P("")
    P("---")
    P("")
    P("## C. Distribución de cardinalidad por atributo (global, deduplicada)")
    P("")
    P("| atributo | n_valores_canonicos_unicos |")
    P("|---|---:|")
    attr_counts: dict[str, set[str]] = {}
    for (organo, atributo), proposals in VALUE_PROPOSALS.items():
        attr_counts.setdefault(atributo, set()).update(c for c, _ in proposals)
    for atributo in sorted(attr_counts):
        P(f"| {atributo} | {len(attr_counts[atributo])} |")
    P("")
    P(f"**Total atributos únicos:** {len(attr_counts)}")
    P("")
    P("---")
    P("")
    P("## D. Cobertura global estimada")
    P("")
    organos_with_proposals = {org for (org, _attr) in VALUE_PROPOSALS.keys()}
    total_hallazgos_global = sum(len(d) for d in organo_to_descs.values())
    n_covered_global = 0
    for organo, descs in organo_to_descs.items():
        if organo not in organos_with_proposals:
            continue
        all_patterns: list[str] = []
        for (org, _attr), props in VALUE_PROPOSALS.items():
            if org == organo:
                for _, pat in props:
                    all_patterns.append(pat)
        compiled = [re.compile(p, re.IGNORECASE) for p in all_patterns]
        for desc in descs:
            if any(c.search(desc) for c in compiled):
                n_covered_global += 1
    cobertura_global = 100.0 * n_covered_global / total_hallazgos_global if total_hallazgos_global else 0
    P(f"- Total hallazgos en corpus: **{total_hallazgos_global}**")
    P(f"- Hallazgos con ≥1 atributo detectado: **{n_covered_global}**")
    P(f"- Cobertura global: **{cobertura_global:.1f}%**")
    P("")

    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Total pares: {pares}, total canonicos (dedup): {total_canonicos_unicos}")
    print(f"Cobertura global estimada: {cobertura_global:.1f}%")


if __name__ == "__main__":
    main()