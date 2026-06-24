# F3.1 — dim_valor_atributo: propuesta basada en corpus

**Estado:** 📋 PROPUESTA (pre-implementación)
**Generado:** 2026-06-22
**Método:** para cada (órgano, atributo) se define un set de regex con
valor canónico asociado. Se corre contra las 27.866 descripciones RAW y
se reportan las frecuencias observadas.

**No escribe en silver.db.** La propuesta es para revisión antes de
implementar `dim_valor_atributo`.

---

## 0. Resumen ejecutivo

- Pares (órgano, atributo) con propuesta: **{('Vejiga', 'homogeneidad_contenido'), ('Riñones', 'tamano'), ('Estómago', 'estratificacion_pared'), ('Próstata', 'homogeneidad'), ('Vesícula', 'contenido'), ('Riñones', 'forma'), ('Próstata', 'ecogenicidad'), ('Bazo', 'arquitectura'), ('Hígado', 'arquitectura'), ('Intestino', 'peristaltismo'), ('Páncreas', 'preservacion'), ('Riñones', 'compromiso_pelvico'), ('Adrenales', 'arquitectura'), ('Útero', 'contenido'), ('Estómago', 'contenido'), ('Próstata', 'tamano'), ('Intestino_duodeno_yeyuno', 'grosor_pared'), ('Útero', 'tamano'), ('Testículos', 'homogeneidad'), ('Riñones', 'bordes'), ('Linfonodos', 'compromiso'), ('Próstata', 'forma'), ('Vesícula', 'grosor_pared'), ('Cavidad abdominal', 'liquido_libre'), ('Vejiga', 'contenido'), ('Riñones', 'diferenciacion_corticomedular'), ('Intestino_colon', 'contenido'), ('Hígado', 'ecogenicidad'), ('Páncreas', 'aspecto_peripancreatico'), ('Útero', 'grosor_pared'), ('Estómago', 'grosor_pared'), ('Testículos', 'ecogenicidad'), ('Vejiga', 'replecion'), ('Testículos', 'tamano'), ('Bazo', 'tamano'), ('Hígado', 'tamano'), ('Riñones', 'relacion_corticomedular'), ('Vesícula', 'bordes_internos'), ('Adrenales', 'tamano'), ('Vesícula', 'distension'), ('Testículos', 'forma'), ('Próstata', 'lobulacion'), ('Hígado', 'patron_vascular'), ('Bazo', 'forma'), ('Intestino_duodeno_yeyuno', 'estratificacion_pared'), ('Adrenales', 'forma'), ('Vejiga', 'grosor_pared'), ('Linfonodos', 'presencia'), ('Intestino_colon', 'paredes'), ('Ovarios', 'tamano'), ('Estómago', 'distension'), ('Bazo', 'margenes'), ('Hígado', 'margenes'), ('Hígado', 'granulado'), ('Riñones', 'ecogenicidad'), ('Cavidad abdominal', 'masas'), ('Hígado', 'bordes'), ('Gestación', 'fetos'), ('Ovarios', 'forma'), ('Intestino_duodeno_yeyuno', 'contenido'), ('Vejiga', 'bordes_internos')}**
- Filas propuestas (con dup organo): **281**
- Valores canónicos únicos (atributo, valor): **172**
- Cardinalidad final estimada de `dim_valor_atributo` (FK atributo_id): **172 filas**

**Decisión clave:** `dim_valor_atributo` se modela **global** (sin `organo_id`).
Justificación: el mismo par `(atributo_id, valor)` puede reutilizarse en
varios órganos (ej: `tamano.NORMAL` aplica a Próstata, Riñones, Hígado,
Bazo, Adrenales, Útero, Ovarios, Testículos). La dimensión anatómica se
resuelve vía `dim_organo_atributo.organo_id`, no en `dim_valor_atributo`.
El sinonimo text es independiente del órgano (mismo patrón regex funciona
en cualquier descripción). Esto reduce duplicación y permite consolidar
ajustes de catálogo.

**Atributos binarios:** `Cavidad abdominal.liquido_libre`, `Cavidad abdominal.masas`, `Linfonodos.compromiso`, `Linfonodos.presencia`, `Páncreas.aspecto_peripancreatico`, `Páncreas.preservacion`, `Riñones.compromiso_pelvico`

**Atributos numéricos:** `Gestación.fetos`

**Ajustes aplicados al modelo:**
- ✅ Riñones.relacion_corticomedular: regex ahora captura 'relación cortico medular adecuada'
- ✅ Riñones.ecogenicidad: agregados patrones AUMENTADA_DE / DISMINUIDA_DE / CORTICAL_HIPOECOICA / CORTICAL_HIPERECOICA
- ✅ Gestación.prenez: ELIMINADO (cobertura 0% en corpus)
- ✅ Bazo.forma / Bazo.margenes: MANTENIDOS temporalmente (decisión diferida a F4)
- ✅ Próstata.tamano: normalizado a un único valor canónico NORMAL (absorbe DENTRO_DE_RANGO + CONSERVADO)
- ✅ dim_valor_atributo: agregada columna `patron_extraccion TEXT`
- ✅ dim_valor_atributo: eliminada columna `organo_id` (justificación arriba)

---

## A. Distribución por (órgano, atributo)

### Vejiga.replecion (n=2690)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `SEMI_PLETORICA` | `\bsemi\s+plet[oó]ric[ao]\b` | 2182 | 81.1% |
| `PLETORICA` | `\bplet[oó]ric[ao]\b` | 234 | 8.7% |
| `SEMI_DEPLETADA` | `\bsemi\s+depletad[oa]\b` | 155 | 5.8% |
| `DEPLETADA` | `\bdepletad[oa]\b` | 54 | 2.0% |
| `DISTENDIDA` | `\bdistendid[oa]\b` | 4 | 0.1% |
| `VACIA` | `\bvac[ií][oa]\b` | 12 | 0.4% |
| `REPLECION_CONSERVADA` | `\breplecci[oó]n\s+conservad[oa]\b` | 0 | 0.0% |
| `RETENCION` | `\bretenci[oó]n\b` | 0 | 0.0% |
| _(sin match)_ | — | 49 | 1.8% |
| **TOTAL matched** | | **2641** | **98.2%** |

### Vejiga.contenido (n=2690)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `ANECOICO` | `\banecoic[oa]?\b` | 2194 | 81.6% |
| `HIPERECOICO` | `\bhiperecoic[oa]?\b` | 430 | 16.0% |
| `HOMOGENEO` | `\bhomog[ée]ne[oa]\b` | 4 | 0.1% |
| `HETEROGENEO` | `\bheterog[ée]ne[oa]\b` | 3 | 0.1% |
| `SEDIMENTO` | `\bsediment[oa]?\b` | 3 | 0.1% |
| `GRANULAR` | `\bgranular\b` | 10 | 0.4% |
| `PUNTIFORME` | `\bpuntiform` | 0 | 0.0% |
| _(sin match)_ | — | 46 | 1.7% |
| **TOTAL matched** | | **2644** | **98.3%** |

### Vejiga.homogeneidad_contenido (n=2690)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `HOMOGENEO` | `\bhomog[ée]ne[oa]\b` | 2106 | 78.3% |
| `HETEROGENEO` | `\bheterog[ée]ne[oa]\b` | 20 | 0.7% |
| `HETEROGENEO_LEVE` | `\b(leve|levemente|discretamente)\s+heterog[ée]ne[oa]\b` | 0 | 0.0% |
| `HETEROGENEO_MODERADO` | `\bmoderad[oa]?\s+heterog[ée]ne[oa]\b` | 0 | 0.0% |
| _(sin match)_ | — | 564 | 21.0% |
| **TOTAL matched** | | **2126** | **79.0%** |

### Vejiga.bordes_internos (n=2690)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `REGULARES` | `\bbordes?\s+intern[oa]s?\s+regular(es)?\b` | 2383 | 88.6% |
| `IRREGULARES` | `\bbordes?\s+intern[oa]s?\s+irregular(es)?\b` | 123 | 4.6% |
| `LISOS` | `\bbordes?\s+intern[oa]s?\s+l[io]s[oa]s?\b` | 1 | 0.0% |
| `CONSERVADOS` | `\bbordes?\s+intern[oa]s?\s+conservad[oa]s?\b` | 0 | 0.0% |
| _(sin match)_ | — | 183 | 6.8% |
| **TOTAL matched** | | **2507** | **93.2%** |

### Vejiga.grosor_pared (n=2690)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `CONSERVADO` | `\bgrosor\s+conservad[oa]\b` | 2149 | 79.9% |
| `ENGROSADO` | `\bengrosad[oa]\b` | 23 | 0.9% |
| `AUMENTADO` | `\bgrosor\s+aumentad[oa]\b` | 170 | 6.3% |
| `DISMINUIDO` | `\bgrosor\s+disminuid[oa]\b` | 0 | 0.0% |
| `NORMAL` | `\bgrosor\s+normal\b` | 1 | 0.0% |
| _(sin match)_ | — | 347 | 12.9% |
| **TOTAL matched** | | **2343** | **87.1%** |

### Próstata.forma (n=737)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `OVALADA` | `\b(forma\s+)?ovalad[oa]\b` | 673 | 91.3% |
| `REDONDEADA` | `\b(forma\s+)?redondead[oa]\b` | 1 | 0.1% |
| `GLOBOSA` | `\b(forma\s+)?globos[oa]\b` | 25 | 3.4% |
| `OVOIDE` | `\b(forma\s+)?ovoid(e|al)\b` | 0 | 0.0% |
| `IRREGULAR` | `\bforma\s+irregular\b` | 0 | 0.0% |
| `CONSERVADA` | `\bforma\s+conservad[oa]\b` | 0 | 0.0% |
| _(sin match)_ | — | 38 | 5.2% |
| **TOTAL matched** | | **699** | **94.8%** |

### Próstata.lobulacion (n=737)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `BILOBULADA` | `\bbilobulad[oa]\b` | 719 | 97.6% |
| `UNILOBULADA` | `\bunilobulad[oa]\b` | 0 | 0.0% |
| `LOBULADA` | `\blobulad[oa]\b` | 0 | 0.0% |
| `NO_LOBULADA` | `\bno\s+lobulad[oa]\b` | 0 | 0.0% |
| _(sin match)_ | — | 18 | 2.4% |
| **TOTAL matched** | | **719** | **97.6%** |

### Próstata.tamano (n=737)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `NORMAL` | `\btama[ñn]o\s+normal\b` | 582 | 79.0% |
| `NORMAL` | `\btama[ñn]o\s+dentro\s+de\s+rango\b` | 582 | 79.0% |
| `NORMAL` | `\btama[ñn]o\s+conservad[oa]\b` | 582 | 79.0% |
| `NORMAL` | `\bconservad[oa]\b` | 582 | 79.0% |
| `NORMAL` | `\bdentro\s+de\s+rango\b` | 582 | 79.0% |
| `AUMENTADO` | `\btama[ñn]o\s+aumentad[oa]\b` | 27 | 3.7% |
| `DISMINUIDO` | `\btama[ñn]o\s+disminuid[oa]\b` | 40 | 5.4% |
| `LEVEMENTE_AUMENTADO` | `\b(leve|levemente)\s+(de\s+)?tama[ñn]o\b` | 0 | 0.0% |
| `MODERADAMENTE_AUMENTADO` | `\b(moderad[oa]|moderadamente)\s+(de\s+)?tama[ñn]o\b` | 0 | 0.0% |
| `SEVERAMENTE_AUMENTADO` | `\b(sever[oa]|severamente)\s+(de\s+)?tama[ñn]o\b` | 0 | 0.0% |
| _(sin match)_ | — | 88 | 11.9% |
| **TOTAL matched** | | **649** | **88.1%** |

### Próstata.ecogenicidad (n=737)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `HIPOECOICA` | `\bhipoecoic[oa]\b` | 462 | 62.7% |
| `HIPERECOICA` | `\bhiperecoic[oa]\b` | 253 | 34.3% |
| `AUMENTADA` | `\becogenicidad\s+aumentad[oa]\b` | 0 | 0.0% |
| `DISMINUIDA` | `\becogenicidad\s+disminuid[oa]\b` | 0 | 0.0% |
| `CONSERVADA` | `\becogenicidad\s+conservad[oa]\b` | 0 | 0.0% |
| `NORMAL` | `\becogenicidad\s+normal\b` | 0 | 0.0% |
| _(sin match)_ | — | 22 | 3.0% |
| **TOTAL matched** | | **715** | **97.0%** |

### Próstata.homogeneidad (n=737)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `HOMOGENEA` | `\bhomog[ée]ne[oa]\b` | 555 | 75.3% |
| `HETEROGENEA` | `\bheterog[ée]ne[oa]\b` | 163 | 22.1% |
| `HOMOGENEA_LEVE` | `\b(leve|levemente)\s+heterog[ée]ne[oa]\b` | 0 | 0.0% |
| `HOMOGENEA_MODERADA` | `\bmoderad[oa]\s+heterog[ée]ne[oa]\b` | 0 | 0.0% |
| _(sin match)_ | — | 19 | 2.6% |
| **TOTAL matched** | | **718** | **97.4%** |

### Riñones.forma (n=2688)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `OVALADO` | `\b(forma\s+)?ovalad[oa]\b` | 2537 | 94.4% |
| `RENAL` | `\bren(al|iform)\b` | 64 | 2.4% |
| `GLOBOSO` | `\b(forma\s+)?globos[oa]\b` | 2 | 0.1% |
| `REDONDEADO` | `\b(forma\s+)?redondead[oa]\b` | 3 | 0.1% |
| `IRREGULAR` | `\bforma\s+irregular\b` | 1 | 0.0% |
| `CONSERVADA` | `\bforma\s+conservad[oa]\b` | 0 | 0.0% |
| `NORMAL` | `\bforma\s+y\s+tama[ñn]o\s+normales?\b` | 5 | 0.2% |
| _(sin match)_ | — | 76 | 2.8% |
| **TOTAL matched** | | **2612** | **97.2%** |

### Riñones.tamano (n=2688)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `NORMAL` | `\btama[ñn]o\s+normal\b` | 27 | 1.0% |
| `DENTRO_DE_RANGO` | `\btama[ñn]o\s+dentro\s+de\s+rango\b` | 2095 | 77.9% |
| `CONSERVADO` | `\btama[ñn]o\s+conservad[oa]\b` | 8 | 0.3% |
| `AUMENTADO` | `\btama[ñn]o\s+aumentad[oa]\b` | 168 | 6.2% |
| `DISMINUIDO` | `\btama[ñn]o\s+disminuid[oa]\b` | 59 | 2.2% |
| `LEVEMENTE_AUMENTADO` | `\b(leve|levemente)\s+aumentad[oa]\b` | 89 | 3.3% |
| `MODERADAMENTE_AUMENTADO` | `\b(moderad[oa]|moderadamente)\s+aumentad[oa]\b` | 16 | 0.6% |
| `SEVERAMENTE_AUMENTADO` | `\b(sever[oa]|severamente|marcadamente)\s+aumentad[oa]\b` | 22 | 0.8% |
| _(sin match)_ | — | 204 | 7.6% |
| **TOTAL matched** | | **2484** | **92.4%** |

### Riñones.bordes (n=2688)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `LISOS` | `\bbordes\s+l[io]s[oa]s?\b` | 17 | 0.6% |
| `REGULARES` | `\bbordes\s+regular(es)?\b` | 1635 | 60.8% |
| `IRREGULARES` | `\bbordes\s+irregular(es)?\b` | 470 | 17.5% |
| `LEVEMENTE_IRREGULARES` | `\bbordes\s+levemente\s+irregular(es)?\b` | 384 | 14.3% |
| `MAL_DEFINIDOS` | `\bbordes\s+mal\s+definidos?\b` | 0 | 0.0% |
| `BIEN_DEFINIDOS` | `\bbordes\s+bien\s+definidos?\b` | 0 | 0.0% |
| `CONSERVADOS` | `\bbordes\s+conservad[oa]s?\b` | 0 | 0.0% |
| _(sin match)_ | — | 182 | 6.8% |
| **TOTAL matched** | | **2506** | **93.2%** |

### Riñones.ecogenicidad (n=2688)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `HIPOECOICA` | `\bhipoecoic[oa]\b` | 193 | 7.2% |
| `HIPERECOICA` | `\bhiperecoic[oa]\b` | 844 | 31.4% |
| `CONSERVADA` | `\becogenicidad\s+conservad[oa]\b` | 257 | 9.6% |
| `AUMENTADA` | `\becogenicidad\s+aumentad[oa]\b` | 163 | 6.1% |
| `DISMINUIDA` | `\becogenicidad\s+disminuid[oa]\b` | 44 | 1.6% |
| `ADECUADA` | `\becogenicidad\s+adecuada\b` | 7 | 0.3% |
| `NORMAL` | `\becogenicidad\s+normal\b` | 2 | 0.1% |
| `AUMENTADA_DE` | `\baumento\s+de\s+ecogenicidad\b` | 2 | 0.1% |
| `DISMINUIDA_DE` | `\bdisminuci[oó]n\s+de\s+ecogenicidad\b` | 0 | 0.0% |
| `CORTICAL_HIPOECOICA` | `\b(corteza|c[oó]rtex|cortical)\s+hipoecoic[oa]\b` | 0 | 0.0% |
| `CORTICAL_HIPERECOICA` | `\b(corteza|c[oó]rtex|cortical)\s+hiperecoic[oa]\b` | 0 | 0.0% |
| `DISMINUIDA` | `\becogenicidad\s+(leve|levemente|discreta|discretamente|moderada|moderadamente|severa|severamente)\s` | 44 | 1.6% |
| `AUMENTADA` | `\becogenicidad\s+(leve|levemente|discreta|discretamente|moderada|moderadamente|severa|severamente)\s` | 163 | 6.1% |
| `CONSERVADA` | `\b(ecogenicidad\s+)?(corteza|c[oó]rtex)\s+conservad[oa]\b` | 257 | 9.6% |
| _(sin match)_ | — | 1176 | 43.8% |
| **TOTAL matched** | | **1512** | **56.2%** |

### Riñones.diferenciacion_corticomedular (n=2688)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `BIEN_DEFINIDA` | `\bbien\s+definid[oa]\b` | 2208 | 82.1% |
| `DEFINIDA` | `\bdiferenciaci[oó]n\s+(definid[oa]|presente)\b` | 0 | 0.0% |
| `MAL_DEFINIDA` | `\b(mal|pobremente)\s+definid[oa]\b` | 359 | 13.4% |
| `PRESERVADA` | `\bdiferenciaci[oó]n\s+(preservad[oa]|conservad[oa])\b` | 0 | 0.0% |
| `AUSENTE` | `\bsin\s+diferenciaci[oó]n\b` | 0 | 0.0% |
| _(sin match)_ | — | 121 | 4.5% |
| **TOTAL matched** | | **2567** | **95.5%** |

### Riñones.relacion_corticomedular (n=2688)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `ADECUADA` | `\brelaci[oó]n\s+(cort[io]co[- ]?medular\s+)?(adecuada|normal|conservad[oa])\b` | 1612 | 60.0% |
| `AUMENTADA` | `\brelaci[oó]n\s+(cort[io]co[- ]?medular\s+)?aumentad[oa]\b` | 290 | 10.8% |
| `DISMINUIDA` | `\brelaci[oó]n\s+(cort[io]co[- ]?medular\s+)?disminuid[oa]\b` | 180 | 6.7% |
| `INVERTIDA` | `\brelaci[oó]n\s+(cort[io]co[- ]?medular\s+)?invertid[oa]\b` | 0 | 0.0% |
| `PERDIDA` | `\b(perdid[oa]|ausentad[oa])\s+la\s+relaci[oó]n\s+(cort[io]co[- ]?medular|c[- ]?m)\b` | 0 | 0.0% |
| `SIN_RELACION` | `\bsin\s+relaci[oó]n\s+(cort[io]co[- ]?medular|c[- ]?m)\b` | 0 | 0.0% |
| _(sin match)_ | — | 606 | 22.5% |
| **TOTAL matched** | | **2082** | **77.5%** |

### Riñones.compromiso_pelvico (n=2688) 🔘 binario 

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `SIN_COMPROMISO` | `\bsin\s+compromiso\s+p[ée]lvic[oa]?\b` | 2469 | 91.9% |
| `CON_COMPROMISO` | `\bcon\s+compromiso\s+p[ée]lvic[oa]?\b` | 0 | 0.0% |
| `ECTASIA_PELVICA` | `\bectasia\s+p[ée]lvic[oa]?\b` | 0 | 0.0% |
| `DILATACION_PELVICA` | `\b(dilataci[oó]n|pelvis\s+dilatad[oa])\b` | 40 | 1.5% |
| `HIDRONEFROSIS` | `\bhidronefrosis\b` | 0 | 0.0% |
| _(sin match)_ | — | 179 | 6.7% |
| **TOTAL matched** | | **2509** | **93.3%** |

### Bazo.tamano (n=2684)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `NORMAL` | `\btama[ñn]o\s+normal\b` | 71 | 2.6% |
| `DENTRO_DE_RANGO` | `\bdentro\s+de\s+rango\b` | 1 | 0.0% |
| `AUMENTADO` | `\baumentad[oa]\b` | 242 | 9.0% |
| `DISMINUIDO` | `\bdisminuid[oa]\b` | 3 | 0.1% |
| `CONSERVADO` | `\bconservad[oa]\b` | 2225 | 82.9% |
| _(sin match)_ | — | 142 | 5.3% |
| **TOTAL matched** | | **2542** | **94.7%** |

### Bazo.forma (n=2684)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `CONSERVADA` | `\bforma\s+conservad[oa]\b` | 5 | 0.2% |
| `NORMAL` | `\bforma\s+normal\b` | 97 | 3.6% |
| _(sin match)_ | — | 2582 | 96.2% |
| **TOTAL matched** | | **102** | **3.8%** |

### Bazo.margenes (n=2684)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `REGULARES` | `\bm[áa]rgenes\s+regular(es)?\b` | 9 | 0.3% |
| `IRREGULARES` | `\bm[áa]rgenes\s+irregular(es)?\b` | 20 | 0.7% |
| `CONSERVADOS` | `\bm[áa]rgenes\s+conservad[oa]s?\b` | 2 | 0.1% |
| _(sin match)_ | — | 2653 | 98.8% |
| **TOTAL matched** | | **31** | **1.2%** |

### Bazo.arquitectura (n=2684)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `CONSERVADA` | `\barquitectura\s+conservad[oa]\b` | 2358 | 87.9% |
| `ALTERADA` | `\barquitectura\s+alterad[oa]\b` | 0 | 0.0% |
| `NORMAL` | `\barquitectura\s+normal\b` | 10 | 0.4% |
| _(sin match)_ | — | 316 | 11.8% |
| **TOTAL matched** | | **2368** | **88.2%** |

### Estómago.distension (n=2688)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `SEMI_DISTENDIDO` | `\bsemi\s+distendid[oa]\b` | 2112 | 78.6% |
| `DISTENDIDO` | `\bdistendid[oa]\b` | 176 | 6.5% |
| `PLETORICO` | `\bplet[oó]ric[oa]\b` | 0 | 0.0% |
| `COLAPSADO` | `\bcolapsad[oa]\b` | 0 | 0.0% |
| `VACIO` | `\bvac[ií]o\b` | 324 | 12.1% |
| _(sin match)_ | — | 76 | 2.8% |
| **TOTAL matched** | | **2612** | **97.2%** |

### Estómago.contenido (n=2688)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `ALIMENTICIO` | `\balimenticio\b` | 2157 | 80.2% |
| `MUCOSO` | `\bmucos[oa]\b` | 356 | 13.2% |
| `LIQUIDO` | `\bl[ií]quid[oa]\b` | 55 | 2.0% |
| `GAS` | `\bgas\b` | 80 | 3.0% |
| `SIN_CONTENIDO` | `\bsin\s+contenido\b` | 5 | 0.2% |
| _(sin match)_ | — | 35 | 1.3% |
| **TOTAL matched** | | **2653** | **98.7%** |

### Estómago.estratificacion_pared (n=2688)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `PRESENTE` | `\bpared(es)?\s+estratificad[oa]s?\b` | 2552 | 94.9% |
| `AUSENTE` | `\bpared(es)?\s+no\s+estratificad[oa]s?\b` | 0 | 0.0% |
| _(sin match)_ | — | 136 | 5.1% |
| **TOTAL matched** | | **2552** | **94.9%** |

### Estómago.grosor_pared (n=2688)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `CONSERVADO` | `\bgrosor\s+conservad[oa]\b` | 1964 | 73.1% |
| `AUMENTADO` | `\bgrosor\s+aumentad[oa]\b` | 81 | 3.0% |
| `DISMINUIDO` | `\bgrosor\s+disminuid[oa]\b` | 0 | 0.0% |
| `NORMAL` | `\bgrosor\s+normal\b` | 9 | 0.3% |
| _(sin match)_ | — | 634 | 23.6% |
| **TOTAL matched** | | **2054** | **76.4%** |

### Hígado.tamano (n=2687)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `NORMAL` | `\btama[ñn]o\s+normal\b` | 1436 | 53.4% |
| `AUMENTADO` | `\btama[ñn]o\s+aumentad[oa]\b` | 5 | 0.2% |
| `DISMINUIDO` | `\btama[ñn]o\s+disminuid[oa]\b` | 2 | 0.1% |
| `LEVEMENTE_AUMENTADO` | `\b(leve|levemente)\s+(de\s+)?tama[ñn]o\b` | 4 | 0.1% |
| `MODERADAMENTE_AUMENTADO` | `\b(moderad[oa]|moderadamente)\s+(de\s+)?tama[ñn]o\b` | 4 | 0.1% |
| `SEVERAMENTE_AUMENTADO` | `\b(sever[oa]|severamente)\s+(de\s+)?tama[ñn]o\b` | 1 | 0.0% |
| `CONSERVADO` | `\btama[ñn]o\s+conservad[oa]\b` | 2 | 0.1% |
| _(sin match)_ | — | 1233 | 45.9% |
| **TOTAL matched** | | **1454** | **54.1%** |

### Hígado.margenes (n=2687)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `LISOS` | `\bm[áa]rgenes\s+l[io]s[oa]s?\b` | 2615 | 97.3% |
| `REDONDEADOS` | `\bm[áa]rgenes\s+redondead[oa]s?\b` | 16 | 0.6% |
| `IRREGULARES` | `\bm[áa]rgenes\s+irregular(es)?\b` | 5 | 0.2% |
| `MAL_DEFINIDOS` | `\bm[áa]rgenes\s+mal\s+definidos?\b` | 2 | 0.1% |
| `CONSERVADOS` | `\bm[áa]rgenes\s+conservad[oa]s?\b` | 0 | 0.0% |
| _(sin match)_ | — | 49 | 1.8% |
| **TOTAL matched** | | **2638** | **98.2%** |

### Hígado.bordes (n=2687)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `LISOS` | `\bbordes\s+l[io]s[oa]s?\b` | 8 | 0.3% |
| `REGULARES` | `\bbordes\s+regular(es)?\b` | 0 | 0.0% |
| `IRREGULARES` | `\bbordes\s+irregular(es)?\b` | 1 | 0.0% |
| `CONSERVADOS` | `\bbordes\s+conservad[oa]s?\b` | 0 | 0.0% |
| _(sin match)_ | — | 2678 | 99.7% |
| **TOTAL matched** | | **9** | **0.3%** |

### Hígado.ecogenicidad (n=2687)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `HIPOECOICA` | `\bhipoecoic[oa]\b` | 1976 | 73.5% |
| `HIPERECOICA` | `\bhiperecoic[oa]\b` | 497 | 18.5% |
| `AUMENTADA` | `\becogenicidad\s+aumentad[oa]\b` | 32 | 1.2% |
| `DISMINUIDA` | `\becogenicidad\s+disminuid[oa]\b` | 9 | 0.3% |
| `NORMAL` | `\becogenicidad\s+normal\b` | 0 | 0.0% |
| `CONSERVADA` | `\becogenicidad\s+conservad[oa]\b` | 10 | 0.4% |
| `LEVEMENTE_AUMENTADA` | `\b(leve|levemente)\s+(de\s+)?ecogenicidad\b` | 0 | 0.0% |
| _(sin match)_ | — | 163 | 6.1% |
| **TOTAL matched** | | **2524** | **93.9%** |

### Hígado.granulado (n=2687)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `FINO` | `\bgranulad[oa]?\s+fino\b` | 612 | 22.8% |
| `GRUESO` | `\bgranulad[oa]?\s+grues[oa]\b` | 1922 | 71.5% |
| _(sin match)_ | — | 153 | 5.7% |
| **TOTAL matched** | | **2534** | **94.3%** |

### Hígado.arquitectura (n=2687)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `CONSERVADA` | `\barquitectura\s+conservad[oa]\b` | 1756 | 65.4% |
| `ALTERADA` | `\barquitectura\s+alterad[oa]\b` | 0 | 0.0% |
| `NORMAL` | `\barquitectura\s+normal\b` | 1 | 0.0% |
| _(sin match)_ | — | 930 | 34.6% |
| **TOTAL matched** | | **1757** | **65.4%** |

### Hígado.patron_vascular (n=2687)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `CONSERVADO` | `\bpatr[óo]n\s+vascular\s+conservad[oa]\b` | 2474 | 92.1% |
| `ALTERADO` | `\bpatr[óo]n\s+vascular\s+alterad[oa]\b` | 0 | 0.0% |
| `NORMAL` | `\bpatr[óo]n\s+vascular\s+normal\b` | 34 | 1.3% |
| `VASOS_CONSERVADOS` | `\bvasculatura?\s+conservad[oa]\b` | 0 | 0.0% |
| _(sin match)_ | — | 179 | 6.7% |
| **TOTAL matched** | | **2508** | **93.3%** |

### Vesícula.distension (n=2667)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `SEMI_DISTENDIDA` | `\bsemi\s+distendid[oa]\b` | 2468 | 92.5% |
| `DISTENDIDA` | `\bdistendid[oa]\b` | 112 | 4.2% |
| `PLETORICA` | `\bplet[oó]ric[oa]\b` | 42 | 1.6% |
| `DEPLETADA` | `\bdepletad[oa]\b` | 8 | 0.3% |
| _(sin match)_ | — | 37 | 1.4% |
| **TOTAL matched** | | **2630** | **98.6%** |

### Vesícula.contenido (n=2667)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `ANECOICO` | `\banecoic[oa]?\b` | 2158 | 80.9% |
| `HIPERECOICO` | `\bhiperecoic[oa]?\b` | 462 | 17.3% |
| `BARRO_BILIAR` | `\bbarro\s+biliar\b` | 0 | 0.0% |
| `CALCULOS` | `\bc[áa]lcul[oa]s?\b` | 0 | 0.0% |
| `SEDIMENTO` | `\bsediment[oa]?\b` | 0 | 0.0% |
| _(sin match)_ | — | 47 | 1.8% |
| **TOTAL matched** | | **2620** | **98.2%** |

### Vesícula.bordes_internos (n=2667)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `REGULARES` | `\bbordes?\s+intern[oa]s?\s+regular(es)?\b` | 2528 | 94.8% |
| `IRREGULARES` | `\bbordes?\s+intern[oa]s?\s+irregular(es)?\b` | 10 | 0.4% |
| `LISOS` | `\bbordes?\s+intern[oa]s?\s+l[io]s[oa]s?\b` | 0 | 0.0% |
| _(sin match)_ | — | 129 | 4.8% |
| **TOTAL matched** | | **2538** | **95.2%** |

### Vesícula.grosor_pared (n=2667)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `CONSERVADO` | `\bgrosor\s+conservad[oa]\b` | 44 | 1.6% |
| `ENGROSADO` | `\bengrosad[oa]\b` | 4 | 0.1% |
| `AUMENTADO` | `\bgrosor\s+aumentad[oa]\b` | 40 | 1.5% |
| _(sin match)_ | — | 2579 | 96.7% |
| **TOTAL matched** | | **88** | **3.3%** |

### Intestino_duodeno_yeyuno.contenido (n=0)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `ALIMENTICIO` | `\balimenticio\b` | 0 | 0.0% |
| `MUCOSO` | `\bmucos[oa]\b` | 0 | 0.0% |
| `FECAL` | `\bfec[ao]l\b` | 0 | 0.0% |
| `LIQUIDO` | `\bl[ií]quid[oa]\b` | 0 | 0.0% |
| `CON_PREDOMINIO_ALIMENTICIO` | `\bpredominio\s+(de\s+)?alimenticio\b` | 0 | 0.0% |
| **TOTAL matched** | | **0** | **0.0%** |

### Intestino_duodeno_yeyuno.grosor_pared (n=0)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `CONSERVADO` | `\bgrosor\s+conservad[oa]\b` | 0 | 0.0% |
| `DISCRETAMENTE_AUMENTADO` | `\b(discret[oa]|discretamente)\s+aumentad[oa]\b` | 0 | 0.0% |
| `LEVEMENTE_AUMENTADO` | `\b(leve|levemente)\s+aumentad[oa]\b` | 0 | 0.0% |
| `MODERADAMENTE_AUMENTADO` | `\b(moderad[oa]|moderadamente)\s+aumentad[oa]\b` | 0 | 0.0% |
| `SEVERAMENTE_AUMENTADO` | `\b(sever[oa]|severamente|marcadamente)\s+aumentad[oa]\b` | 0 | 0.0% |
| `AUMENTADO` | `\bgrosor\s+aumentad[oa]\b` | 0 | 0.0% |
| **TOTAL matched** | | **0** | **0.0%** |

### Intestino_duodeno_yeyuno.estratificacion_pared (n=0)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `PRESENTE` | `\bpared(es)?\s+estratificad[oa]s?\b` | 0 | 0.0% |
| `AUSENTE` | `\bpared(es)?\s+no\s+estratificad[oa]s?\b` | 0 | 0.0% |
| **TOTAL matched** | | **0** | **0.0%** |

### Intestino_colon.contenido (n=0)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `FECAL` | `\bfec[ao]l\b` | 0 | 0.0% |
| `MUCOSO` | `\bmucos[oa]\b` | 0 | 0.0% |
| `ALIMENTICIO` | `\balimenticio\b` | 0 | 0.0% |
| `CON_PREDOMINIO_FECAL` | `\bpredominio\s+(de\s+)?fec[ao]l\b` | 0 | 0.0% |
| **TOTAL matched** | | **0** | **0.0%** |

### Intestino_colon.paredes (n=0)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `CONSERVADO` | `\bpared(es)?\s+conservad[oa]\b` | 0 | 0.0% |
| `AUMENTADO` | `\bpared(es)?\s+aumentad[oa]\b` | 0 | 0.0% |
| `DISMINUIDO` | `\bpared(es)?\s+disminuid[oa]\b` | 0 | 0.0% |
| **TOTAL matched** | | **0** | **0.0%** |

### Intestino.peristaltismo (n=2688)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `NORMAL` | `\bperistaltismo\s+normal\b` | 2451 | 91.2% |
| `AUMENTADO` | `\bperistaltismo\s+aumentad[oa]\b` | 23 | 0.9% |
| `DISMINUIDO` | `\bperistaltismo\s+disminuid[oa]\b` | 24 | 0.9% |
| `AUSENTE` | `\bperistaltismo\s+ausente\b` | 8 | 0.3% |
| `CONSERVADO` | `\bperistaltismo\s+conservad[oa]\b` | 1 | 0.0% |
| _(sin match)_ | — | 181 | 6.7% |
| **TOTAL matched** | | **2507** | **93.3%** |

### Páncreas.preservacion (n=2688) 🔘 binario 

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `CONSERVADO` | `\bconservad[oa]\b` | 2559 | 95.2% |
| `PRESERVADO` | `\bpreservad[oa]\b` | 0 | 0.0% |
| `ALTERADO` | `\balterad[oa]\b` | 0 | 0.0% |
| `NORMAL` | `\bnormal\b` | 0 | 0.0% |
| `NO_EVALUADO` | `\bno\s+evaluad[oa]\b` | 52 | 1.9% |
| _(sin match)_ | — | 77 | 2.9% |
| **TOTAL matched** | | **2611** | **97.1%** |

### Páncreas.aspecto_peripancreatico (n=2688) 🔘 binario 

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `NORMAL` | `\bnormal\b` | 5 | 0.2% |
| `ALTERADO` | `\balterad[oa]\b` | 0 | 0.0% |
| _(sin match)_ | — | 2683 | 99.8% |
| **TOTAL matched** | | **5** | **0.2%** |

### Adrenales.forma (n=2687)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `OVALADA` | `\b(forma\s+)?ovalad[oa]\b` | 0 | 0.0% |
| `CONSERVADA` | `\bforma\s+conservad[oa]\b` | 0 | 0.0% |
| `NORMAL` | `\bforma\s+normal\b` | 2387 | 88.8% |
| _(sin match)_ | — | 300 | 11.2% |
| **TOTAL matched** | | **2387** | **88.8%** |

### Adrenales.tamano (n=2687)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `NORMAL` | `\btama[ñn]o\s+normal\b` | 5 | 0.2% |
| `AUMENTADO` | `\baumentad[oa]\b` | 179 | 6.7% |
| `DISMINUIDO` | `\bdisminuid[oa]\b` | 0 | 0.0% |
| `CONSERVADO` | `\bconservad[oa]\b` | 42 | 1.6% |
| _(sin match)_ | — | 2461 | 91.6% |
| **TOTAL matched** | | **226** | **8.4%** |

### Adrenales.arquitectura (n=2687)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `CONSERVADA` | `\barquitectura\s+conservad[oa]\b` | 18 | 0.7% |
| `NORMAL` | `\barquitectura\s+normal\b` | 46 | 1.7% |
| _(sin match)_ | — | 2623 | 97.6% |
| **TOTAL matched** | | **64** | **2.4%** |

### Linfonodos.presencia (n=2681) 🔘 binario 

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `PRESENTE` | `\bpresente\b` | 7 | 0.3% |
| `AUSENTE` | `\bausente\b` | 0 | 0.0% |
| `NO_SE_OBSERVAN` | `\bno\s+se\s+observ[ao]n\b` | 2308 | 86.1% |
| _(sin match)_ | — | 366 | 13.7% |
| **TOTAL matched** | | **2315** | **86.3%** |

### Linfonodos.compromiso (n=2681) 🔘 binario 

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `NO_COMPROMETIDO` | `\bno\s+comprometid[oa]s?\b` | 0 | 0.0% |
| `COMPROMETIDO` | `\bcomprometid[oa]s?\b` | 2306 | 86.0% |
| `CONSERVADO` | `\bconservad[oa]s?\b` | 22 | 0.8% |
| `REACTIVO` | `\breactiv[oa]s?\b` | 2 | 0.1% |
| `NO_REACTIVO` | `\bno\s+reactiv[oa]s?\b` | 0 | 0.0% |
| _(sin match)_ | — | 351 | 13.1% |
| **TOTAL matched** | | **2330** | **86.9%** |

### Útero.tamano (n=49)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `AUMENTADO` | `\baumentad[oa]\b` | 17 | 34.7% |
| `DISMINUIDO` | `\bdisminuid[oa]\b` | 0 | 0.0% |
| `NORMAL` | `\bnormal\b` | 5 | 10.2% |
| `DENTRO_DE_RANGO` | `\bdentro\s+de\s+rango\b` | 0 | 0.0% |
| _(sin match)_ | — | 27 | 55.1% |
| **TOTAL matched** | | **22** | **44.9%** |

### Útero.contenido (n=49)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `ANECOICO` | `\banecoic[oa]?\b` | 18 | 36.7% |
| `HIPERECOICO` | `\bhiperecoic[oa]?\b` | 15 | 30.6% |
| `HOMOGENEO` | `\bhomog[ée]ne[oa]\b` | 1 | 2.0% |
| `HETEROGENEO` | `\bheterog[ée]ne[oa]\b` | 0 | 0.0% |
| `LIQUIDO` | `\bl[ií]quid[oa]\b` | 0 | 0.0% |
| _(sin match)_ | — | 15 | 30.6% |
| **TOTAL matched** | | **34** | **69.4%** |

### Útero.grosor_pared (n=49)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `ENGROSADO` | `\bengrosad[oa]\b` | 1 | 2.0% |
| `DELGADO` | `\bdelgad[oa]s?\b` | 6 | 12.2% |
| `CONSERVADO` | `\bconservad[oa]\b` | 4 | 8.2% |
| _(sin match)_ | — | 38 | 77.6% |
| **TOTAL matched** | | **11** | **22.4%** |

### Ovarios.tamano (n=5)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `NORMAL` | `\btama[ñn]o\s+normal\b` | 0 | 0.0% |
| `AUMENTADO` | `\baumentad[oa]\b` | 0 | 0.0% |
| `DISMINUIDO` | `\bdisminuid[oa]\b` | 0 | 0.0% |
| _(sin match)_ | — | 5 | 100.0% |
| **TOTAL matched** | | **0** | **0.0%** |

### Ovarios.forma (n=5)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `OVALADO` | `\bovalad[oa]\b` | 1 | 20.0% |
| `REDONDEADO` | `\bredondead[oa]\b` | 0 | 0.0% |
| _(sin match)_ | — | 4 | 80.0% |
| **TOTAL matched** | | **1** | **20.0%** |

### Testículos.tamano (n=27)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `NORMAL` | `\btama[ñn]o\s+normal\b` | 1 | 3.7% |
| `AUMENTADO` | `\baumentad[oa]\b` | 1 | 3.7% |
| `DISMINUIDO` | `\bdisminuid[oa]\b` | 1 | 3.7% |
| `CONSERVADO` | `\bconservad[oa]\b` | 9 | 33.3% |
| _(sin match)_ | — | 15 | 55.6% |
| **TOTAL matched** | | **12** | **44.4%** |

### Testículos.forma (n=27)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `OVALADO` | `\bovalad[oa]\b` | 5 | 18.5% |
| `CONSERVADA` | `\bforma\s+conservad[oa]\b` | 0 | 0.0% |
| `NORMAL` | `\bforma\s+normal\b` | 0 | 0.0% |
| _(sin match)_ | — | 22 | 81.5% |
| **TOTAL matched** | | **5** | **18.5%** |

### Testículos.ecogenicidad (n=27)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `HIPOECOICA` | `\bhipoecoic[oa]\b` | 0 | 0.0% |
| `HIPERECOICA` | `\bhiperecoic[oa]\b` | 5 | 18.5% |
| `NORMAL` | `\becogenicidad\s+normal\b` | 0 | 0.0% |
| `CONSERVADA` | `\becogenicidad\s+conservad[oa]\b` | 1 | 3.7% |
| _(sin match)_ | — | 21 | 77.8% |
| **TOTAL matched** | | **6** | **22.2%** |

### Testículos.homogeneidad (n=27)  

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `HOMOGENEO` | `\bhomog[ée]ne[oa]\b` | 0 | 0.0% |
| `HETEROGENEO` | `\bheterog[ée]ne[oa]\b` | 7 | 25.9% |
| _(sin match)_ | — | 20 | 74.1% |
| **TOTAL matched** | | **7** | **25.9%** |

### Gestación.fetos (n=200)  🔢 numérico

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `UNO` | `\b(al\s+menos\s+)?1\s+feto\b` | 12 | 6.0% |
| `DOS` | `\b(al\s+menos\s+)?2\s+fetos?\b` | 9 | 4.5% |
| `TRES` | `\b(al\s+menos\s+)?3\s+fetos?\b` | 14 | 7.0% |
| `CUATRO` | `\b(al\s+menos\s+)?4\s+fetos?\b` | 15 | 7.5% |
| `CINCO` | `\b(al\s+menos\s+)?5\s+fetos?\b` | 20 | 10.0% |
| `SEIS` | `\b(al\s+menos\s+)?6\s+fetos?\b` | 17 | 8.5% |
| `SIETE` | `\b(al\s+menos\s+)?7\s+fetos?\b` | 9 | 4.5% |
| `OCHO` | `\b(al\s+menos\s+)?8\s+fetos?\b` | 9 | 4.5% |
| `NUEVE_O_MAS` | `\b(al\s+menos\s+)?(9|10|11|12|\d{2,})\s+fetos?\b` | 2 | 1.0% |
| _(sin match)_ | — | 93 | 46.5% |
| **TOTAL matched** | | **107** | **53.5%** |

### Cavidad abdominal.liquido_libre (n=0) 🔘 binario 

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `PRESENTE` | `\bl[ií]quido\s+libre\b` | 0 | 0.0% |
| `AUSENTE` | `\bno\s+se\s+observ[ao]\s+l[ií]quido\s+libre\b` | 0 | 0.0% |
| `ABUNDANTE` | `\babundante\s+l[ií]quido\s+libre\b` | 0 | 0.0% |
| `MODERADO` | `\bmoderad[oa]\s+l[ií]quido\s+libre\b` | 0 | 0.0% |
| `ESCASO` | `\bescaso\s+l[ií]quido\s+libre\b` | 0 | 0.0% |
| **TOTAL matched** | | **0** | **0.0%** |

### Cavidad abdominal.masas (n=0) 🔘 binario 

| valor_canonico | patron_extraccion | n | % |
|---|---|---:|---:|
| `PRESENTE` | `\bmasa(s)?\b` | 0 | 0.0% |
| `AUSENTE` | `\bsin\s+masa(s)?\b` | 0 | 0.0% |
| **TOTAL matched** | | **0** | **0.0%** |

---

## B. Cardinalidad final propuesta para `dim_valor_atributo`

Esquema objetivo:

```sql
CREATE TABLE dim_valor_atributo (
    id              INTEGER PRIMARY KEY,
    atributo_id     INTEGER NOT NULL REFERENCES dim_atributo(id),
    valor           VARCHAR(64) NOT NULL,
    sinonimos       TEXT,                       -- lista textual de variantes
    patron_extraccion TEXT,                     -- regex canónica que detecta este valor
    es_binario_true BOOLEAN,                    -- si atributo es binario y este es el valor "TRUE"
    es_default      BOOLEAN DEFAULT FALSE,      -- valor por defecto cuando no hay match
    orden           INTEGER DEFAULT 0,           -- orden de display en UI
    activo          BOOLEAN DEFAULT TRUE,        -- soft-delete
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(atributo_id, valor)
);
```

**Notas de diseño:**
- ❌ Sin `organo_id`: `dim_valor_atributo` es **global**. La dimensión anatómica
  se obtiene vía join `dim_organo_atributo`.
- ✅ `patron_extraccion`: regex que el ETL usa para detectar este valor en cualquier
  descripción del órgano correspondiente. Permite trazabilidad y reproducción.
- ✅ `es_binario_true`: para atributos binarios, marca cuál de los valores es "TRUE"
  (ej: en `Linfonodos.presencia`, `PRESENTE` es TRUE, `AUSENTE` es FALSE).
- ✅ `es_default`: valor fallback cuando no se detecta ninguno (típicamente NORMAL).
- ✅ UNIQUE(atributo_id, valor): un valor canónico aparece UNA vez por atributo.

**Inserción propuesta (en orden de prioridad, deduplicada por atributo):**

| atributo_id | valor | patron_extraccion | es_binario_true | es_default |
|---|---|---|---|---|
| `replecion` | `SEMI_PLETORICA` | `\bsemi\s+plet[oó]ric[ao]\b` | FALSE | FALSE |
| `replecion` | `PLETORICA` | `\bplet[oó]ric[ao]\b` | FALSE | FALSE |
| `replecion` | `SEMI_DEPLETADA` | `\bsemi\s+depletad[oa]\b` | FALSE | FALSE |
| `replecion` | `DEPLETADA` | `\bdepletad[oa]\b` | FALSE | FALSE |
| `replecion` | `DISTENDIDA` | `\bdistendid[oa]\b` | FALSE | FALSE |
| `replecion` | `VACIA` | `\bvac[ií][oa]\b` | FALSE | FALSE |
| `replecion` | `REPLECION_CONSERVADA` | `\breplecci[oó]n\s+conservad[oa]\b` | FALSE | FALSE |
| `replecion` | `RETENCION` | `\bretenci[oó]n\b` | FALSE | FALSE |
| `contenido` | `ANECOICO` | `\banecoic[oa]?\b` | FALSE | FALSE |
| `contenido` | `HIPERECOICO` | `\bhiperecoic[oa]?\b` | FALSE | FALSE |
| `contenido` | `HOMOGENEO` | `\bhomog[ée]ne[oa]\b` | FALSE | FALSE |
| `contenido` | `HETEROGENEO` | `\bheterog[ée]ne[oa]\b` | FALSE | FALSE |
| `contenido` | `SEDIMENTO` | `\bsediment[oa]?\b` | FALSE | FALSE |
| `contenido` | `GRANULAR` | `\bgranular\b` | FALSE | FALSE |
| `contenido` | `PUNTIFORME` | `\bpuntiform` | FALSE | FALSE |
| `homogeneidad_contenido` | `HOMOGENEO` | `\bhomog[ée]ne[oa]\b` | FALSE | FALSE |
| `homogeneidad_contenido` | `HETEROGENEO` | `\bheterog[ée]ne[oa]\b` | FALSE | FALSE |
| `homogeneidad_contenido` | `HETEROGENEO_LEVE` | `\b(leve|levemente|discretamente)\s+heterog[ée]ne[oa]\b` | FALSE | FALSE |
| `homogeneidad_contenido` | `HETEROGENEO_MODERADO` | `\bmoderad[oa]?\s+heterog[ée]ne[oa]\b` | FALSE | FALSE |
| `bordes_internos` | `REGULARES` | `\bbordes?\s+intern[oa]s?\s+regular(es)?\b` | FALSE | FALSE |
| `bordes_internos` | `IRREGULARES` | `\bbordes?\s+intern[oa]s?\s+irregular(es)?\b` | FALSE | FALSE |
| `bordes_internos` | `LISOS` | `\bbordes?\s+intern[oa]s?\s+l[io]s[oa]s?\b` | FALSE | FALSE |
| `bordes_internos` | `CONSERVADOS` | `\bbordes?\s+intern[oa]s?\s+conservad[oa]s?\b` | FALSE | FALSE |
| `grosor_pared` | `CONSERVADO` | `\bgrosor\s+conservad[oa]\b` | FALSE | FALSE |
| `grosor_pared` | `ENGROSADO` | `\bengrosad[oa]\b` | FALSE | FALSE |
| `grosor_pared` | `AUMENTADO` | `\bgrosor\s+aumentad[oa]\b` | FALSE | FALSE |
| `grosor_pared` | `DISMINUIDO` | `\bgrosor\s+disminuid[oa]\b` | FALSE | FALSE |
| `grosor_pared` | `NORMAL` | `\bgrosor\s+normal\b` | FALSE | TRUE |
| `forma` | `OVALADA` | `\b(forma\s+)?ovalad[oa]\b` | FALSE | FALSE |
| `forma` | `REDONDEADA` | `\b(forma\s+)?redondead[oa]\b` | FALSE | FALSE |
| `forma` | `GLOBOSA` | `\b(forma\s+)?globos[oa]\b` | FALSE | FALSE |
| `forma` | `OVOIDE` | `\b(forma\s+)?ovoid(e|al)\b` | FALSE | FALSE |
| `forma` | `IRREGULAR` | `\bforma\s+irregular\b` | FALSE | FALSE |
| `forma` | `CONSERVADA` | `\bforma\s+conservad[oa]\b` | FALSE | FALSE |
| `lobulacion` | `BILOBULADA` | `\bbilobulad[oa]\b` | FALSE | FALSE |
| `lobulacion` | `UNILOBULADA` | `\bunilobulad[oa]\b` | FALSE | FALSE |
| `lobulacion` | `LOBULADA` | `\blobulad[oa]\b` | FALSE | FALSE |
| `lobulacion` | `NO_LOBULADA` | `\bno\s+lobulad[oa]\b` | FALSE | FALSE |
| `tamano` | `NORMAL` | `\btama[ñn]o\s+normal\b` | FALSE | TRUE |
| `tamano` | `AUMENTADO` | `\btama[ñn]o\s+aumentad[oa]\b` | FALSE | FALSE |
| `tamano` | `DISMINUIDO` | `\btama[ñn]o\s+disminuid[oa]\b` | FALSE | FALSE |
| `tamano` | `LEVEMENTE_AUMENTADO` | `\b(leve|levemente)\s+(de\s+)?tama[ñn]o\b` | FALSE | FALSE |
| `tamano` | `MODERADAMENTE_AUMENTADO` | `\b(moderad[oa]|moderadamente)\s+(de\s+)?tama[ñn]o\b` | FALSE | FALSE |
| `tamano` | `SEVERAMENTE_AUMENTADO` | `\b(sever[oa]|severamente)\s+(de\s+)?tama[ñn]o\b` | FALSE | FALSE |
| `ecogenicidad` | `HIPOECOICA` | `\bhipoecoic[oa]\b` | FALSE | FALSE |
| `ecogenicidad` | `HIPERECOICA` | `\bhiperecoic[oa]\b` | FALSE | FALSE |
| `ecogenicidad` | `AUMENTADA` | `\becogenicidad\s+aumentad[oa]\b` | FALSE | FALSE |
| `ecogenicidad` | `DISMINUIDA` | `\becogenicidad\s+disminuid[oa]\b` | FALSE | FALSE |
| `ecogenicidad` | `CONSERVADA` | `\becogenicidad\s+conservad[oa]\b` | FALSE | FALSE |
| `ecogenicidad` | `NORMAL` | `\becogenicidad\s+normal\b` | FALSE | TRUE |
| `homogeneidad` | `HOMOGENEA` | `\bhomog[ée]ne[oa]\b` | FALSE | FALSE |
| `homogeneidad` | `HETEROGENEA` | `\bheterog[ée]ne[oa]\b` | FALSE | FALSE |
| `homogeneidad` | `HOMOGENEA_LEVE` | `\b(leve|levemente)\s+heterog[ée]ne[oa]\b` | FALSE | FALSE |
| `homogeneidad` | `HOMOGENEA_MODERADA` | `\bmoderad[oa]\s+heterog[ée]ne[oa]\b` | FALSE | FALSE |
| `forma` | `OVALADO` | `\b(forma\s+)?ovalad[oa]\b` | FALSE | FALSE |
| `forma` | `RENAL` | `\bren(al|iform)\b` | FALSE | FALSE |
| `forma` | `GLOBOSO` | `\b(forma\s+)?globos[oa]\b` | FALSE | FALSE |
| `forma` | `REDONDEADO` | `\b(forma\s+)?redondead[oa]\b` | FALSE | FALSE |
| `forma` | `NORMAL` | `\bforma\s+y\s+tama[ñn]o\s+normales?\b` | FALSE | TRUE |
| `tamano` | `DENTRO_DE_RANGO` | `\btama[ñn]o\s+dentro\s+de\s+rango\b` | FALSE | FALSE |
| `tamano` | `CONSERVADO` | `\btama[ñn]o\s+conservad[oa]\b` | FALSE | FALSE |
| `bordes` | `LISOS` | `\bbordes\s+l[io]s[oa]s?\b` | FALSE | FALSE |
| `bordes` | `REGULARES` | `\bbordes\s+regular(es)?\b` | FALSE | FALSE |
| `bordes` | `IRREGULARES` | `\bbordes\s+irregular(es)?\b` | FALSE | FALSE |
| `bordes` | `LEVEMENTE_IRREGULARES` | `\bbordes\s+levemente\s+irregular(es)?\b` | FALSE | FALSE |
| `bordes` | `MAL_DEFINIDOS` | `\bbordes\s+mal\s+definidos?\b` | FALSE | FALSE |
| `bordes` | `BIEN_DEFINIDOS` | `\bbordes\s+bien\s+definidos?\b` | FALSE | FALSE |
| `bordes` | `CONSERVADOS` | `\bbordes\s+conservad[oa]s?\b` | FALSE | FALSE |
| `ecogenicidad` | `ADECUADA` | `\becogenicidad\s+adecuada\b` | FALSE | FALSE |
| `ecogenicidad` | `AUMENTADA_DE` | `\baumento\s+de\s+ecogenicidad\b` | FALSE | FALSE |
| `ecogenicidad` | `DISMINUIDA_DE` | `\bdisminuci[oó]n\s+de\s+ecogenicidad\b` | FALSE | FALSE |
| `ecogenicidad` | `CORTICAL_HIPOECOICA` | `\b(corteza|c[oó]rtex|cortical)\s+hipoecoic[oa]\b` | FALSE | FALSE |
| `ecogenicidad` | `CORTICAL_HIPERECOICA` | `\b(corteza|c[oó]rtex|cortical)\s+hiperecoic[oa]\b` | FALSE | FALSE |
| `diferenciacion_corticomedular` | `BIEN_DEFINIDA` | `\bbien\s+definid[oa]\b` | FALSE | FALSE |
| `diferenciacion_corticomedular` | `DEFINIDA` | `\bdiferenciaci[oó]n\s+(definid[oa]|presente)\b` | FALSE | FALSE |
| `diferenciacion_corticomedular` | `MAL_DEFINIDA` | `\b(mal|pobremente)\s+definid[oa]\b` | FALSE | FALSE |
| `diferenciacion_corticomedular` | `PRESERVADA` | `\bdiferenciaci[oó]n\s+(preservad[oa]|conservad[oa])\b` | FALSE | FALSE |
| `diferenciacion_corticomedular` | `AUSENTE` | `\bsin\s+diferenciaci[oó]n\b` | FALSE | FALSE |
| `relacion_corticomedular` | `ADECUADA` | `\brelaci[oó]n\s+(cort[io]co[- ]?medular\s+)?(adecuada|normal|conservad[oa])\b` | FALSE | FALSE |
| `relacion_corticomedular` | `AUMENTADA` | `\brelaci[oó]n\s+(cort[io]co[- ]?medular\s+)?aumentad[oa]\b` | FALSE | FALSE |
| `relacion_corticomedular` | `DISMINUIDA` | `\brelaci[oó]n\s+(cort[io]co[- ]?medular\s+)?disminuid[oa]\b` | FALSE | FALSE |
| `relacion_corticomedular` | `INVERTIDA` | `\brelaci[oó]n\s+(cort[io]co[- ]?medular\s+)?invertid[oa]\b` | FALSE | FALSE |
| `relacion_corticomedular` | `PERDIDA` | `\b(perdid[oa]|ausentad[oa])\s+la\s+relaci[oó]n\s+(cort[io]co[- ]?medular|c[- ]?m` | FALSE | FALSE |
| `relacion_corticomedular` | `SIN_RELACION` | `\bsin\s+relaci[oó]n\s+(cort[io]co[- ]?medular|c[- ]?m)\b` | FALSE | FALSE |
| `compromiso_pelvico` | `SIN_COMPROMISO` | `\bsin\s+compromiso\s+p[ée]lvic[oa]?\b` | FALSE | FALSE |
| `compromiso_pelvico` | `CON_COMPROMISO` | `\bcon\s+compromiso\s+p[ée]lvic[oa]?\b` | TRUE | FALSE |
| `compromiso_pelvico` | `ECTASIA_PELVICA` | `\bectasia\s+p[ée]lvic[oa]?\b` | FALSE | FALSE |
| `compromiso_pelvico` | `DILATACION_PELVICA` | `\b(dilataci[oó]n|pelvis\s+dilatad[oa])\b` | FALSE | FALSE |
| `compromiso_pelvico` | `HIDRONEFROSIS` | `\bhidronefrosis\b` | FALSE | FALSE |
| `margenes` | `REGULARES` | `\bm[áa]rgenes\s+regular(es)?\b` | FALSE | FALSE |
| `margenes` | `IRREGULARES` | `\bm[áa]rgenes\s+irregular(es)?\b` | FALSE | FALSE |
| `margenes` | `CONSERVADOS` | `\bm[áa]rgenes\s+conservad[oa]s?\b` | FALSE | FALSE |
| `arquitectura` | `CONSERVADA` | `\barquitectura\s+conservad[oa]\b` | FALSE | FALSE |
| `arquitectura` | `ALTERADA` | `\barquitectura\s+alterad[oa]\b` | FALSE | FALSE |
| `arquitectura` | `NORMAL` | `\barquitectura\s+normal\b` | FALSE | TRUE |
| `distension` | `SEMI_DISTENDIDO` | `\bsemi\s+distendid[oa]\b` | FALSE | FALSE |
| `distension` | `DISTENDIDO` | `\bdistendid[oa]\b` | FALSE | FALSE |
| `distension` | `PLETORICO` | `\bplet[oó]ric[oa]\b` | FALSE | FALSE |
| `distension` | `COLAPSADO` | `\bcolapsad[oa]\b` | FALSE | FALSE |
| `distension` | `VACIO` | `\bvac[ií]o\b` | FALSE | FALSE |
| `contenido` | `ALIMENTICIO` | `\balimenticio\b` | FALSE | FALSE |
| `contenido` | `MUCOSO` | `\bmucos[oa]\b` | FALSE | FALSE |
| `contenido` | `LIQUIDO` | `\bl[ií]quid[oa]\b` | FALSE | FALSE |
| `contenido` | `GAS` | `\bgas\b` | FALSE | FALSE |
| `contenido` | `SIN_CONTENIDO` | `\bsin\s+contenido\b` | FALSE | FALSE |
| `estratificacion_pared` | `PRESENTE` | `\bpared(es)?\s+estratificad[oa]s?\b` | FALSE | FALSE |
| `estratificacion_pared` | `AUSENTE` | `\bpared(es)?\s+no\s+estratificad[oa]s?\b` | FALSE | FALSE |
| `margenes` | `LISOS` | `\bm[áa]rgenes\s+l[io]s[oa]s?\b` | FALSE | FALSE |
| `margenes` | `REDONDEADOS` | `\bm[áa]rgenes\s+redondead[oa]s?\b` | FALSE | FALSE |
| `margenes` | `MAL_DEFINIDOS` | `\bm[áa]rgenes\s+mal\s+definidos?\b` | FALSE | FALSE |
| `ecogenicidad` | `LEVEMENTE_AUMENTADA` | `\b(leve|levemente)\s+(de\s+)?ecogenicidad\b` | FALSE | FALSE |
| `granulado` | `FINO` | `\bgranulad[oa]?\s+fino\b` | FALSE | FALSE |
| `granulado` | `GRUESO` | `\bgranulad[oa]?\s+grues[oa]\b` | FALSE | FALSE |
| `patron_vascular` | `CONSERVADO` | `\bpatr[óo]n\s+vascular\s+conservad[oa]\b` | FALSE | FALSE |
| `patron_vascular` | `ALTERADO` | `\bpatr[óo]n\s+vascular\s+alterad[oa]\b` | FALSE | FALSE |
| `patron_vascular` | `NORMAL` | `\bpatr[óo]n\s+vascular\s+normal\b` | FALSE | TRUE |
| `patron_vascular` | `VASOS_CONSERVADOS` | `\bvasculatura?\s+conservad[oa]\b` | FALSE | FALSE |
| `distension` | `SEMI_DISTENDIDA` | `\bsemi\s+distendid[oa]\b` | FALSE | FALSE |
| `distension` | `DISTENDIDA` | `\bdistendid[oa]\b` | FALSE | FALSE |
| `distension` | `PLETORICA` | `\bplet[oó]ric[oa]\b` | FALSE | FALSE |
| `distension` | `DEPLETADA` | `\bdepletad[oa]\b` | FALSE | FALSE |
| `contenido` | `BARRO_BILIAR` | `\bbarro\s+biliar\b` | FALSE | FALSE |
| `contenido` | `CALCULOS` | `\bc[áa]lcul[oa]s?\b` | FALSE | FALSE |
| `contenido` | `FECAL` | `\bfec[ao]l\b` | FALSE | FALSE |
| `contenido` | `CON_PREDOMINIO_ALIMENTICIO` | `\bpredominio\s+(de\s+)?alimenticio\b` | FALSE | FALSE |
| `grosor_pared` | `DISCRETAMENTE_AUMENTADO` | `\b(discret[oa]|discretamente)\s+aumentad[oa]\b` | FALSE | FALSE |
| `grosor_pared` | `LEVEMENTE_AUMENTADO` | `\b(leve|levemente)\s+aumentad[oa]\b` | FALSE | FALSE |
| `grosor_pared` | `MODERADAMENTE_AUMENTADO` | `\b(moderad[oa]|moderadamente)\s+aumentad[oa]\b` | FALSE | FALSE |
| `grosor_pared` | `SEVERAMENTE_AUMENTADO` | `\b(sever[oa]|severamente|marcadamente)\s+aumentad[oa]\b` | FALSE | FALSE |
| `contenido` | `CON_PREDOMINIO_FECAL` | `\bpredominio\s+(de\s+)?fec[ao]l\b` | FALSE | FALSE |
| `paredes` | `CONSERVADO` | `\bpared(es)?\s+conservad[oa]\b` | FALSE | FALSE |
| `paredes` | `AUMENTADO` | `\bpared(es)?\s+aumentad[oa]\b` | FALSE | FALSE |
| `paredes` | `DISMINUIDO` | `\bpared(es)?\s+disminuid[oa]\b` | FALSE | FALSE |
| `peristaltismo` | `NORMAL` | `\bperistaltismo\s+normal\b` | FALSE | TRUE |
| `peristaltismo` | `AUMENTADO` | `\bperistaltismo\s+aumentad[oa]\b` | FALSE | FALSE |
| `peristaltismo` | `DISMINUIDO` | `\bperistaltismo\s+disminuid[oa]\b` | FALSE | FALSE |
| `peristaltismo` | `AUSENTE` | `\bperistaltismo\s+ausente\b` | FALSE | FALSE |
| `peristaltismo` | `CONSERVADO` | `\bperistaltismo\s+conservad[oa]\b` | FALSE | FALSE |
| `preservacion` | `CONSERVADO` | `\bconservad[oa]\b` | TRUE | FALSE |
| `preservacion` | `PRESERVADO` | `\bpreservad[oa]\b` | TRUE | FALSE |
| `preservacion` | `ALTERADO` | `\balterad[oa]\b` | FALSE | FALSE |
| `preservacion` | `NORMAL` | `\bnormal\b` | TRUE | TRUE |
| `preservacion` | `NO_EVALUADO` | `\bno\s+evaluad[oa]\b` | FALSE | FALSE |
| `aspecto_peripancreatico` | `NORMAL` | `\bnormal\b` | TRUE | TRUE |
| `aspecto_peripancreatico` | `ALTERADO` | `\balterad[oa]\b` | FALSE | FALSE |
| `presencia` | `PRESENTE` | `\bpresente\b` | TRUE | FALSE |
| `presencia` | `AUSENTE` | `\bausente\b` | FALSE | FALSE |
| `presencia` | `NO_SE_OBSERVAN` | `\bno\s+se\s+observ[ao]n\b` | FALSE | FALSE |
| `compromiso` | `NO_COMPROMETIDO` | `\bno\s+comprometid[oa]s?\b` | FALSE | FALSE |
| `compromiso` | `COMPROMETIDO` | `\bcomprometid[oa]s?\b` | FALSE | FALSE |
| `compromiso` | `CONSERVADO` | `\bconservad[oa]s?\b` | TRUE | FALSE |
| `compromiso` | `REACTIVO` | `\breactiv[oa]s?\b` | FALSE | FALSE |
| `compromiso` | `NO_REACTIVO` | `\bno\s+reactiv[oa]s?\b` | FALSE | FALSE |
| `grosor_pared` | `DELGADO` | `\bdelgad[oa]s?\b` | FALSE | FALSE |
| `homogeneidad` | `HOMOGENEO` | `\bhomog[ée]ne[oa]\b` | FALSE | FALSE |
| `homogeneidad` | `HETEROGENEO` | `\bheterog[ée]ne[oa]\b` | FALSE | FALSE |
| `fetos` | `UNO` | `\b(al\s+menos\s+)?1\s+feto\b` | FALSE | FALSE |
| `fetos` | `DOS` | `\b(al\s+menos\s+)?2\s+fetos?\b` | FALSE | FALSE |
| `fetos` | `TRES` | `\b(al\s+menos\s+)?3\s+fetos?\b` | FALSE | FALSE |
| `fetos` | `CUATRO` | `\b(al\s+menos\s+)?4\s+fetos?\b` | FALSE | FALSE |
| `fetos` | `CINCO` | `\b(al\s+menos\s+)?5\s+fetos?\b` | FALSE | FALSE |
| `fetos` | `SEIS` | `\b(al\s+menos\s+)?6\s+fetos?\b` | FALSE | FALSE |
| `fetos` | `SIETE` | `\b(al\s+menos\s+)?7\s+fetos?\b` | FALSE | FALSE |
| `fetos` | `OCHO` | `\b(al\s+menos\s+)?8\s+fetos?\b` | FALSE | FALSE |
| `fetos` | `NUEVE_O_MAS` | `\b(al\s+menos\s+)?(9|10|11|12|\d{2,})\s+fetos?\b` | FALSE | FALSE |
| `liquido_libre` | `PRESENTE` | `\bl[ií]quido\s+libre\b` | TRUE | FALSE |
| `liquido_libre` | `AUSENTE` | `\bno\s+se\s+observ[ao]\s+l[ií]quido\s+libre\b` | FALSE | FALSE |
| `liquido_libre` | `ABUNDANTE` | `\babundante\s+l[ií]quido\s+libre\b` | FALSE | FALSE |
| `liquido_libre` | `MODERADO` | `\bmoderad[oa]\s+l[ií]quido\s+libre\b` | FALSE | FALSE |
| `liquido_libre` | `ESCASO` | `\bescaso\s+l[ií]quido\s+libre\b` | FALSE | FALSE |
| `masas` | `PRESENTE` | `\bmasa(s)?\b` | TRUE | FALSE |
| `masas` | `AUSENTE` | `\bsin\s+masa(s)?\b` | FALSE | FALSE |

**Total filas en `dim_valor_atributo`:** 172

---

## C. Distribución de cardinalidad por atributo (global, deduplicada)

| atributo | n_valores_canonicos_unicos |
|---|---:|
| arquitectura | 3 |
| aspecto_peripancreatico | 2 |
| bordes | 7 |
| bordes_internos | 4 |
| compromiso | 5 |
| compromiso_pelvico | 5 |
| contenido | 17 |
| diferenciacion_corticomedular | 5 |
| distension | 9 |
| ecogenicidad | 12 |
| estratificacion_pared | 2 |
| fetos | 9 |
| forma | 11 |
| granulado | 2 |
| grosor_pared | 10 |
| homogeneidad | 6 |
| homogeneidad_contenido | 4 |
| liquido_libre | 5 |
| lobulacion | 4 |
| margenes | 6 |
| masas | 2 |
| paredes | 3 |
| patron_vascular | 4 |
| peristaltismo | 5 |
| presencia | 3 |
| preservacion | 5 |
| relacion_corticomedular | 6 |
| replecion | 8 |
| tamano | 8 |

**Total atributos únicos:** 29

---

## D. Cobertura global estimada

- Total hallazgos en corpus: **27866**
- Hallazgos con ≥1 atributo detectado: **26747**
- Cobertura global: **96.0%**
