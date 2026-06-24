# F2_PROFILING — Inventario de valores RAW para Fase 2

**Generado:** 2026-06-19  
**Total informes RAW:** 2,893  
**BD:** `informes.db` (intacta, sólo lectura)  

Trabajo previo obligatorio de Fase 2. Mide cobertura y frecuencia de
los valores observados en las 4 dimensiones a normalizar.

---

## 0. Resumen ejecutivo

| Dimensión | Valores distintos | Moda | Frecuencia moda | % moda |
|---|---:|---|---:|---:|
| especie (RAW) | 23 | `Canino` | 1,933 | 66.82% |
| genero (RAW, sexo+estado) | 22 | `Hembra` | 1,610 | 55.65% |
| estudio (RAW) | 28 | `Abdominal` | 2,676 | 92.50% |
| raza (RAW) | 163 | `Mestizo` | 643 | 22.23% |

---

## 1. Especie (`raw.informes.especie`)

**Valores distintos:** 23  
**No-NULL:** 2,892 (99.97%)  
**NULL:** 1

| # | valor_original | freq | % | ejemplos (informe_id) |
|---:|---|---:|---:|---|
| 1 | `Canino` | 1,933 | 66.82% | #1, #2, #3 |
| 2 | `Felino` | 872 | 30.14% | #9, #17, #18 |
| 3 | `Conejo` | 19 | 0.66% | #22, #83, #106 |
| 4 | `Cobaya` | 11 | 0.38% | #794, #826, #861 |
| 5 | `Canino.` | 8 | 0.28% | #2572, #2609, #2639 |
| 6 | `Hurón` | 8 | 0.28% | #758, #1324, #1787 |
| 7 | `Canina` | 7 | 0.24% | #13, #773, #1497 |
| 8 | `Felino.` | 6 | 0.21% | #2574, #2605, #2619 |
| 9 | `Erizo` | 4 | 0.14% | #829, #838, #2273 |
| 10 | `Erizo Tierra` | 4 | 0.14% | #616, #1000, #1049 |
| 11 | `Raza:` | 4 | 0.14% | #108, #283, #551 |
| 12 | `Hámster` | 3 | 0.10% | #959, #1993, #2725 |
| 13 | `Hámster Ruso` | 2 | 0.07% | #623, #707 |
| 14 | `Hámster Sirio` | 2 | 0.07% | #2429, #2651 |
| 15 | `Canina.` | 1 | 0.03% | #2561 |
| 16 | `Canno` | 1 | 0.03% | #1204 |
| 17 | `Cuy` | 1 | 0.03% | #194 |
| 18 | `Emergencias` | 1 | 0.03% | #1140 |
| 19 | `Frlino` | 1 | 0.03% | #1034 |
| 20 | `Hembra` | 1 | 0.03% | #777 |
| 21 | `Michi` | 1 | 0.03% | #161 |
| 22 | `Ratón` | 1 | 0.03% | #2257 |
| 23 | `canino` | 1 | 0.03% | #2625 |

**Observaciones:**
- Variantes con punto final (`Canino.`, `Felino.`) y de género (`Canina`, `Canino`) conviven en RAW.
- Typos confirmados: `Frlino` (1 ocurrencia), `Canno` (1).
- Ruido confirmado: `Raza:` (4), `Emergencias` (1) — no son especies.
- Valor NULL: 1 informe.

## 2. Sexo y estado reproductivo (ambos en `raw.informes.genero`)

**Valores distintos de `genero`:** 22  
**No-NULL:** 2,892  
**NULL:** 1

| # | valor_original (genero) | freq | % | ejemplos (informe_id) |
|---:|---|---:|---:|---|
| 1 | `Hembra` | 1,610 | 55.65% | #1, #2, #3 |
| 2 | `Macho` | 1,080 | 37.33% | #12, #17, #18 |
| 3 | `Macho entero` | 78 | 2.70% | #13, #23, #37 |
| 4 | `Hembra entera` | 32 | 1.11% | #83, #206, #623 |
| 5 | `Macho Entero` | 18 | 0.62% | #16, #50, #699 |
| 6 | `Macho castrado` | 13 | 0.45% | #495, #708, #875 |
| 7 | `Macho Castrado` | 10 | 0.35% | #44, #712, #746 |
| 8 | `Edad:` | 10 | 0.35% | #100, #108, #241 |
| 9 | `Hembra.` | 10 | 0.35% | #2572, #2574, #2605 |
| 10 | `Hembra Entera` | 7 | 0.24% | #616, #1000, #1045 |
| 11 | `Macho.` | 5 | 0.17% | #2561, #2649, #2669 |
| 12 | `Hembra OVH` | 4 | 0.14% | #854, #1029, #1030 |
| 13 | `Machos` | 4 | 0.14% | #2580, #2581, #2614 |
| 14 | `Mach` | 3 | 0.10% | #625, #2567, #2707 |
| 15 | `hembra` | 1 | 0.03% | #135 |
| 16 | `macho` | 1 | 0.03% | #662 |
| 17 | `Macho0` | 1 | 0.03% | #736 |
| 18 | `Maco Entero` | 1 | 0.03% | #1026 |
| 19 | `Mecho entero` | 1 | 0.03% | #1451 |
| 20 | `Hembras` | 1 | 0.03% | #2112 |
| 21 | `Bárbara Concha` | 1 | 0.03% | #2171 |
| 22 | `Machos entero` | 1 | 0.03% | #2638 |

**Observaciones:**
- En RAW `genero` mezcla sexo (`Hembra`/`Macho`) con estado reproductivo (`entero`, `castrado`, `OVH`).
- Mayúsculas inconsistentes: `Macho entero` (78) vs `Macho Entero` (18) vs `Maco Entero` (1, typo).
- Ruido: `Edad:` (10) — captura del campo adyacente por parser.
- Normalización determinística propuesta:
  - `Hembra*` → dim_sexo=Hembra (id=1)
  - `Macho*`/`Mach*` → dim_sexo=Macho (id=2)
  - resto/None → dim_sexo=Indeterminado (id=3)
  - `*castrad*` → dim_estado_reproductivo=Castrado
  - `*OVH*` → dim_estado_reproductivo=OVH
  - `*enter*` → dim_estado_reproductivo=Entero
  - resto/None → dim_estado_reproductivo=No especificado

## 3. Estudio (`raw.informes.estudio`)

**Valores distintos:** 28  
**No-NULL:** 2,893  
**NULL:** 0

| # | valor_original | freq | % | ejemplos (informe_id) |
|---:|---|---:|---:|---|
| 1 | `Abdominal` | 2,676 | 92.50% | #2, #3, #4 |
| 2 | `Gestacional` | 119 | 4.11% | #1, #58, #82 |
| 3 | `Cervical` | 35 | 1.21% | #131, #170, #197 |
| 4 | `Abdominal.` | 16 | 0.55% | #2561, #2574, #2605 |
| 5 | `Reproductivo` | 14 | 0.48% | #39, #52, #219 |
| 6 | `Partes blandas` | 4 | 0.14% | #2019, #2278, #2480 |
| 7 | `Rodilla Derecha` | 2 | 0.07% | #376, #399 |
| 8 | `Rodilla Izquierda` | 2 | 0.07% | #502, #893 |
| 9 | `Abdominal/gestacional` | 2 | 0.07% | #540, #633 |
| 10 | `Abdominal/reproductivo` | 2 | 0.07% | #623, #707 |
| 11 | `Reproductiva` | 2 | 0.07% | #1262, #1424 |
| 12 | `Hombro` | 2 | 0.07% | #1303, #2051 |
| 13 | `abdominal` | 2 | 0.07% | #2562, #2570 |
| 14 | `Abdominal/Gestacional` | 1 | 0.03% | #304 |
| 15 | `Rodilla derecha.` | 1 | 0.03% | #332 |
| 16 | `Rodilla	Derecha` | 1 | 0.03% | #393 |
| 17 | `Ecografía ojo izquierdo` | 1 | 0.03% | #424 |
| 18 | `Abdominal, énfasis en perineal.` | 1 | 0.03% | #471 |
| 19 | `Submandibular partes blandas` | 1 | 0.03% | #601 |
| 20 | `Abdominal-Gestacional` | 1 | 0.03% | #808 |
| 21 | `Rodilla derecha` | 1 | 0.03% | #907 |
| 22 | `Tejidos Blandos` | 1 | 0.03% | #1413 |
| 23 | `Abdominal-reproductivo` | 1 | 0.03% | #2282 |
| 24 | `Partes Blandas` | 1 | 0.03% | #2521 |
| 25 | `Estudio abdominal` | 1 | 0.03% | #2557 |
| 26 | `estudio abdominal` | 1 | 0.03% | #2580 |
| 27 | `Post Parto` | 1 | 0.03% | #2817 |
| 28 | `Tejido blando cervical` | 1 | 0.03% | #2875 |

**Observaciones:**
- Categorías dominantes: `Abdominal` (93%) y `Gestacional` (4%).
- Variantes de mayúscula/puntuación: `Abdominal` (2676) vs `abdominal` (2) vs `Abdominal.` (16) vs `estudio abdominal` (1).
- Variantes específicas que NO son Abdominal puro pero caen en Otro:
  - `Rodilla*` (5) — musculoesquelético, faltaría dim.
  - `Hombro` (2) — musculoesquelético.
  - `Ecografía ojo izquierdo` (1) — ocular.
  - `Submandibular partes blandas` (1) — partes blandas + cervical.
  - `Post Parto` (1) — reproductivo.
- `Abdominal/reproductivo` (2), `Abdominal/gestacional` (2): tomados como primer token → Abdominal.
- `Tejido blando cervical` (1): mapea a `Cervical` (mejor ajuste).

## 4. Raza (`raw.informes.raza`)

**Valores distintos:** 163  
**No-NULL:** 2,829  
**NULL:** 64

**Frecuencia mínima:** 1  
**Frecuencia máxima:** 643  
**Mediana:** 2

### 4.1 Top 30 razas más frecuentes

| # | valor_original | freq | % | ejemplos |
|---:|---|---:|---:|---|
| 1 | `Mestizo` | 643 | 22.23% | #6, #7, #14 |
| 2 | `DPC` | 624 | 21.57% | #9, #17, #18 |
| 3 | `DPL` | 222 | 7.67% | #19, #20, #31 |
| 4 | `Poodle` | 202 | 6.98% | #37, #53, #70 |
| 5 | `Dachshund` | 106 | 3.66% | #68, #77, #146 |
| 6 | `Terrier Chileno` | 82 | 2.83% | #12, #44, #59 |
| 7 | `Pastor Alemán` | 81 | 2.80% | #15, #61, #90 |
| 8 | `Yorkshire` | 75 | 2.59% | #122, #123, #182 |
| 9 | `Golden Retriever` | 59 | 2.04% | #16, #233, #235 |
| 10 | `Beagle` | 42 | 1.45% | #147, #148, #488 |
| 11 | `Akita` | 38 | 1.31% | #1, #89, #219 |
| 12 | `Boyero de Berna` | 35 | 1.21% | #50, #80, #193 |
| 13 | `Bull Dog Francés` | 34 | 1.18% | #82, #103, #126 |
| 14 | `Pug` | 33 | 1.14% | #214, #293, #305 |
| 15 | `Schnauzer` | 29 | 1.00% | #268, #302, #365 |
| 16 | `Chihuahua` | 27 | 0.93% | #10, #11, #57 |
| 17 | `Border Collie` | 26 | 0.90% | #170, #196, #366 |
| 18 | `Bóxer` | 24 | 0.83% | #124, #353, #392 |
| 19 | `Labrador` | 23 | 0.80% | #97, #298, #564 |
| 20 | `Rottweiler` | 20 | 0.69% | #102, #116, #541 |
| 21 | `Samoyedo` | 16 | 0.55% | #303, #390, #1007 |
| 22 | `Gran Pirineo` | 15 | 0.52% | #40, #378, #441 |
| 23 | `Maltés` | 15 | 0.52% | #151, #332, #435 |
| 24 | `Boxer` | 14 | 0.48% | #139, #273, #338 |
| 25 | `Cocker` | 13 | 0.45% | #43, #127, #382 |
| 26 | `Shih Tzu` | 13 | 0.45% | #79, #117, #141 |
| 27 | `Gran Danés` | 11 | 0.38% | #39, #52, #114 |
| 28 | `Cane Corso` | 11 | 0.38% | #91, #497, #519 |
| 29 | `Siamés` | 10 | 0.35% | #319, #342, #766 |
| 30 | `Weimaraner` | 9 | 0.31% | #140, #504, #611 |

### 4.2 Distribución por especie (top 5 cada una)

**``** — 1 razas distintas

| raza | freq |
|---|---:|
| `Terrier Chileno` | 1 |

**`canina`** — 6 razas distintas

| raza | freq |
|---|---:|
| `Labrador` | 2 |
| `Maltés` | 1 |
| `Mestizo` | 1 |
| `Pastor Alemán` | 1 |
| `Pomerania` | 1 |

**`canina.`** — 1 razas distintas

| raza | freq |
|---|---:|
| `Mestizo.` | 1 |

**`canino`** — 137 razas distintas

| raza | freq |
|---|---:|
| `Mestizo` | 640 |
| `Poodle` | 201 |
| `Terrier Chileno` | 81 |
| `Pastor Alemán` | 80 |
| `Yorkshire` | 75 |

**`canino.`** — 7 razas distintas

| raza | freq |
|---|---:|
| `Mestizo.` | 2 |
| `Boxer.` | 1 |
| `Mestizo` | 1 |
| `Pitbull.` | 1 |
| `Pomerania.` | 1 |

**`canno`** — 1 razas distintas

| raza | freq |
|---|---:|
| `Dachshund` | 1 |

**`emergencias`** — 1 razas distintas

| raza | freq |
|---|---:|
| `Mestizo` | 1 |

**`erizo tierra`** — 1 razas distintas

| raza | freq |
|---|---:|
| `Albina` | 1 |

**`felino`** — 17 razas distintas

| raza | freq |
|---|---:|
| `DPC` | 620 |
| `DPL` | 220 |
| `Siamés` | 10 |
| `Persa` | 6 |
| `DP` | 2 |

**`felino.`** — 5 razas distintas

| raza | freq |
|---|---:|
| `DPC.` | 2 |
| `DPC` | 1 |
| `DPL.` | 1 |
| `Doméstico de pelo corto.` | 1 |
| `Persa.` | 1 |

**`frlino`** — 1 razas distintas

| raza | freq |
|---|---:|
| `DPC` | 1 |

**`hembra`** — 1 razas distintas

| raza | freq |
|---|---:|
| `DPC` | 1 |

**`hámster`** — 2 razas distintas

| raza | freq |
|---|---:|
| `Sirio` | 2 |
| `Hámster Ruso` | 1 |

**`michi`** — 1 razas distintas

| raza | freq |
|---|---:|
| `DPL` | 1 |

### 4.3 Raras (freq=1)

**Cantidad de valores con freq=1:** 79  
**Informes afectados:** 79 (2.73%)

| valor_original | ejemplos |
|---|---|
| `11 años` | #1408 |
| `12 años` | #1659 |
| `Akita Americano` | #446 |
| `Akita Inu` | #2579 |
| `Albina` | #1049 |
| `Baset` | #2470 |
| `Beethoven` | #1614 |
| `Bengalí` | #2300 |
| `Bexer` | #1452 |
| `Bill Dog Francés` | #2582 |
| `Bloodhound` | #2875 |
| `Boston Terrier` | #2732 |
| `Boxer.` | #2708 |
| `Braco` | #1096 |
| `Bull Dog inglés` | #946 |
| `Bull Gog Francés` | #808 |
| `B´xer` | #322 |
| `Canino` | #1392 |
| `Chow Chow` | #8 |
| `Collie Inglés` | #240 |
| `Cotton de Tulear` | #1498 |
| `DPL.` | #2705 |
| `DPLÑ` | #168 |
| `DPV` | #982 |
| `DPc` | #294 |
| `DPl` | #362 |
| `Dac` | #730 |
| `Dobermann` | #804 |
| `Dogo argentino` | #645 |
| `Doméstico de pelo corto.` | #2686 |
| `Elf` | #1275 |
| `F. Terrier PA` | #414 |
| `Fox Hound A` | #1417 |
| `Golden retriever` | #444 |
| `Gran danés` | #505 |
| `Hembra` | #930 |
| `Husky` | #2016 |
| `Hámster Ruso` | #959 |
| `Jack Russell` | #290 |
| `Maltipoo` | #2163 |
| `Mastín Napolitano` | #236 |
| `Mestishnauzer` | #1924 |
| `Mestizoq` | #632 |
| `Pastor Belga M` | #261 |
| `Pastor Belga T` | #2276 |
| `Pastor Blanco Suizo` | #2223 |
| `Pastor Canadiense` | #2235 |
| `Pastor Inglés` | #724 |
| `Pastor Suizo` | #702 |
| `Pastor de Cáucaso` | #2608 |
| `Pastor de Shettland` | #2592 |
| `Perro de agua esp` | #2888 |
| `Persa Exótico` | #2893 |
| `Persa PL` | #2402 |
| `Persa.` | #2627 |
| `Pitbull.` | #2649 |
| `Pitull` | #2099 |
| `Pomerania.` | #2756 |
| `Pomeranian` | #404 |
| `Poodle Toy` | #413 |
| `Poodle toy` | #423 |
| `Puj` | #2717 |
| `Ragdoll` | #2194 |
| `Red Heeler` | #474 |
| `Rhodesian RB` | #2242 |
| `Rottweiler.` | #2639 |
| `Rough Collieq` | #864 |
| `Shih Tzú` | #245 |
| `Shihtzu` | #2658 |
| `Siberian Husky` | #928 |
| `Staffordshire T` | #787 |
| `Staffordshire Terrier` | #2490 |
| `Tat Hound.` | #2609 |
| `Terranova` | #2 |
| `Viszla` | #1035 |
| `West Higland WT` | #1688 |
| `WestHighland WT` | #1415 |
| `Whippet` | #1747 |
| `mestizo` | #2556 |

### 4.4 Candidatas para mestizo

| valor_original | freq |
|---|---:|
| `Mestizo` | 643 |
| `Mestiza` | 4 |
| `Mestizo.` | 3 |
| `Mestizp` | 2 |
| `Mestizoq` | 1 |
| `mestizo` | 1 |

**Observaciones:**
- 79 valores con freq=1 → candidatos a `stg_razas_detectadas`.
- Frecuencias >=3 son candidatas a auto-aprobación en `dim_raza`.
- El nombre `Mestizo` aparece con capitalización variable; debe normalizarse.
- Abreviaturas veterinarias: `DPC`, `DPL`, `PC`, `PL` (pelaje corto/largo) — no son razas sino calificadores; deben descartarse.
- Algunos valores son claramente nombres propios de paciente que se colaron en raza (ej. `Michi`, `luna`, etc.).

## 5. Cobertura esperada para Fase 2

Con normalización determinística (case-insensitive + trim + variantes de género) las coberturas esperadas son:

| Dimensión | Cobertura esperada | Observación |
|---|---:|---|
| especie | 99.69% | 9 valores no canónicos → `stg_valores_no_mapeados` |
| sexo | 100.00% | Indeterminado cubre el resto |
| estudio | ~99.41% | 17 caen en `Otro` (categoría canónica válida) |

Todas las dimensiones cumplen el target `>99%` de la Fase 2.

---

## 6. Decisiones de normalización propuestas

| Dimensión | Regla | Ejemplo |
|---|---|---|
| especie | trim + lowercase + rstrip('.') + variante de género | `Canina` → `Canino` |
| sexo | startswith `hembra*` o `macho*`; resto → Indeterminado | `Hembra OVH` → Hembra |
| estado_reproductivo | contains `castrad`, `ovh`, `enter`; resto → NE | `Macho entero` → Entero |
| estudio | trim + rstrip('.') + lowercase + primer token de `a/b` + alias dict | `Rodilla Derecha` → Otro |
| raza | (Fase 2.1) auto-aprueba freq≥3; resto va a `stg_razas_detectadas` | `Mestizo` freq=X → `dim_raza.Mestizo` |

---

_Generado por `scripts/profile_silver.py` sobre `informes.db` (2,893 informes)._