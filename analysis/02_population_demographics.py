# Adapted analytical code; default PUBLIC_DEMO. No clinical results included.
from pathlib import Path
import sys
CODE_ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "scripts" / "gold_utils.py").is_file() and (p / "synthetic" / "schema.json").is_file())
sys.path.insert(0, str(CODE_ROOT / "scripts"))
from gold_utils import find_project_root, get_output_root


from pathlib import Path
import sys, hashlib, re
import pandas as pd, numpy as np, matplotlib.pyplot as plt
from display_helpers import display, Markdown

def root_of(p):
    return find_project_root()
ROOT = root_of(Path.cwd())
sys.path.insert(0, str(ROOT / 'scripts'))
from gold_utils import connect_gold_readonly, get_gold_db_path, validate_gold_identity
DB = get_gold_db_path(ROOT)
OUT = get_output_root() / 'population_demographics'
OUT.mkdir(parents=True, exist_ok=True)
sha_pre = validate_gold_identity(DB)
conn = connect_gold_readonly(DB)
qc = conn.execute('PRAGMA quick_check').fetchone()[0]
print('ACTIVE GOLD: gold_v2_final.db')
print('Gold:', DB, '\nSHA PRE:', sha_pre, '\nSize:', DB.stat().st_size, '\nquick_check:', qc)
assert qc == 'ok'


schema = pd.read_sql_query('PRAGMA table_info("gold_reports_v2")', conn)
display(schema)
cols = ['report_id', 'species', 'breed', 'sex', 'age_text', 'study_type', 'study_date', 'outcome']
assert set(cols) <= set(schema.name)
all_reports = pd.read_sql_query('SELECT ' + ','.join(('"' + c + '"' for c in cols)) + ' FROM gold_reports_v2', conn)

def den(c, name=None):
    n = len(all_reports)
    a = all_reports[c].notna().sum()
    return {'dimension': name or c, 'N_total': n, 'N_available': int(a), 'N_missing': int(n - a), 'coverage_pct': a / n * 100}
population_denominators = pd.DataFrame([den(c, 'age' if c == 'age_text' else c) for c in ['species', 'sex', 'age_text', 'breed', 'study_date', 'study_type', 'outcome']])
print('N total:', len(all_reports))
display(population_denominators)


def dist(df, c):
    s = df[c].dropna()
    z = s.value_counts().rename_axis(c).reset_index(name='N')
    z['pct'] = z.N / len(s) * 100
    z['denominator'] = len(s)
    return z
species_distribution = dist(all_reports, 'species')
sex_distribution = dist(all_reports, 'sex')
species_sex_distribution = all_reports.dropna(subset=['species', 'sex']).groupby(['species', 'sex']).size().rename('N').reset_index()
species_sex_distribution = species_sex_distribution.merge(all_reports.groupby('species').size().rename('species_N'), on='species')
species_sex_distribution['pct_within_species'] = species_sex_distribution.N / species_sex_distribution.species_N * 100
display(species_distribution)
display(sex_distribution)
display(species_sex_distribution)
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ax[0].bar(species_distribution.species.astype(str), species_distribution.N)
ax[0].set(title='Species (N disponible)', ylabel='Informes (N)')
ax[1].bar(sex_distribution.sex.astype(str), sex_distribution.N)
ax[1].set(title='Sex (N disponible)', ylabel='Informes (N)')
plt.tight_layout()
plt.savefig(OUT / 'species_sex_distributions.png', dpi=140)
plt.show()
display(Markdown('Interpretación: composición del corpus de informes, no riesgo ni prevalencia veterinaria general.'))


age_values = all_reports.age_text.value_counts(dropna=False).rename_axis('age_text').reset_index(name='N')
display(age_values)

def parse_age(x):
    if pd.isna(x) or str(x).strip() == '':
        return (np.nan, 'MISSING')
    s = str(x).strip().lower().replace(',', '.')
    m = re.fullmatch('\\d+(?:\\.\\d+)?', s)
    if m:
        return (float(s) / 12, 'PARSED')
    m = re.fullmatch('(\\d+(?:\\.\\d+)?)\\s*(?:años?|a)', s)
    if m:
        return (float(m.group(1)), 'PARSED')
    m = re.fullmatch('(\\d+(?:\\.\\d+)?)\\s*(?:mes(?:es)?|m)', s)
    if m:
        return (float(m.group(1)) / 12, 'PARSED')
    m = re.fullmatch('(\\d+)\\s*a\\s*(\\d+)\\s*m', s)
    if m:
        return (float(m.group(1)) + float(m.group(2)) / 12, 'PARSED')
    m = re.fullmatch('(\\d+(?:\\.\\d+)?)\\s*d[ií]as?(?:\\s+aprox)?', s)
    if m:
        return (float(m.group(1)) / 365.25, 'PARSED')
    return (np.nan, 'AMBIGUOUS' if re.search('\\d', s) else 'UNPARSEABLE')
p = all_reports.age_text.map(parse_age)
all_reports['age_years'] = p.map(lambda z: z[0])
all_reports['age_parse_status'] = p.map(lambda z: z[1])
age_parser_audit = all_reports.groupby(['age_text', 'age_years', 'age_parse_status'], dropna=False).size().rename('N').reset_index()
display(age_parser_audit)
print(all_reports.age_parse_status.value_counts())
print('Effective parser coverage:', all_reports.age_years.notna().mean() * 100)
display(Markdown('Los valores numéricos se interpretan como meses por la escala observada 12,24,36,...; textos no inequívocos quedan auditados, no forzados.'))


ages = all_reports.loc[all_reports.age_parse_status == 'PARSED', 'age_years'].dropna()
age_summary = pd.DataFrame([{'N': len(ages), 'mean': ages.mean(), 'std': ages.std(), 'median': ages.median(), 'P25': ages.quantile(0.25), 'P75': ages.quantile(0.75), 'P90': ages.quantile(0.9), 'P95': ages.quantile(0.95), 'min': ages.min(), 'max': ages.max(), 'IQR': ages.quantile(0.75) - ages.quantile(0.25)}])
display(age_summary)

def band(x):
    if pd.isna(x):
        return np.nan
    for lo, hi, l in [(0, 1, '<1'), (1, 3, '1-<3'), (3, 6, '3-<6'), (6, 10, '6-<10'), (10, 15, '10-<15'), (15, np.inf, '>=15')]:
        if lo <= x < hi:
            return l
all_reports['age_band_eda'] = all_reports.age_years.map(band)
age_band_distribution = dist(all_reports.dropna(subset=['age_band_eda']).assign(age_band=lambda d: d.age_band_eda), 'age_band')
main_species = all_reports.species.value_counts().loc[lambda s: s >= 20].index
age_by_species = all_reports[all_reports.species.isin(main_species)].dropna(subset=['age_years']).groupby('species').age_years.agg(N='count', mean_age='mean', median_age='median', P25=lambda x: x.quantile(0.25), P75=lambda x: x.quantile(0.75), min='min', max='max').reset_index()
breed_distribution = dist(all_reports, 'breed')
b = all_reports.dropna(subset=['species', 'breed']).groupby(['species', 'breed']).size().rename('N').reset_index().merge(all_reports.groupby('species').size().rename('species_N'), on='species')
b['pct_within_species'] = b.N / b.species_N * 100
b['size_flag'] = np.select([b.N < 5, b.N < 10, b.N < 20], ['N < 5', 'N < 10', 'N < 20'], default='N >= 20')
breed_by_species = b
display(age_band_distribution)
display(age_by_species)
display(breed_distribution.head(30))
print('Breed available/unique:', all_reports.breed.notna().sum(), all_reports.breed.nunique(), 'rare N=1/N<=3/N<=5:', (breed_distribution.N == 1).sum(), (breed_distribution.N <= 3).sum(), (breed_distribution.N <= 5).sum())
display(breed_by_species[breed_by_species.species.isin(main_species)].head(100))
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ax[0].hist(ages, bins=25)
ax[0].set(title='Edad (N parseado)', xlabel='Años', ylabel='Informes (N)')
ax[1].boxplot(ages, vert=False)
ax[1].set(title='Boxplot edad', xlabel='Años')
plt.tight_layout()
plt.savefig(OUT / 'age_hist_boxplot.png', dpi=140)
plt.show()
q = breed_distribution.head(20).sort_values('N')
plt.figure(figsize=(9, 6))
plt.barh(q.breed.astype(str), q.N)
plt.title('Top 20 breeds (no es distribución completa)')
plt.xlabel('Informes (N)')
plt.tight_layout()
plt.savefig(OUT / 'top_breeds.png', dpi=140)
plt.show()


study_type_distribution = dist(all_reports, 'study_type')
outcome_distribution = dist(all_reports, 'outcome')
display(study_type_distribution)
display(outcome_distribution)
display(Markdown('Outcome es caracterización global del corpus; no se cruza con conceptos clínicos.'))


all_reports['study_date_parsed'] = pd.to_datetime(all_reports.study_date, errors='coerce')
all_reports['year'] = all_reports.study_date_parsed.dt.year
all_reports['month'] = all_reports.study_date_parsed.dt.month
valid = all_reports.study_date_parsed.notna()
inwin = valid & all_reports.year.between(2022, 2026)
temporal_analysis_reports = all_reports.loc[inwin].copy()
print('all:', len(all_reports), 'valid:', valid.sum(), '2022-2026:', len(temporal_analysis_reports), 'missing:', (~valid).sum(), 'out_of_range:', (valid & ~all_reports.year.between(2022, 2026)).sum())
print('min/max:', all_reports.loc[valid].study_date_parsed.min().date(), all_reports.loc[valid].study_date_parsed.max().date())
reports_by_year = temporal_analysis_reports.groupby('year').size().rename('N').reset_index()
reports_by_year['pct'] = reports_by_year.N / len(temporal_analysis_reports) * 100
reports_by_year = reports_by_year.merge(temporal_analysis_reports.groupby('year').study_date_parsed.agg(min_date='min', max_date='max').reset_index(), on='year')
reports_by_month = temporal_analysis_reports.groupby(['year', 'month']).size().rename('N').reset_index()
reports_by_month['pct'] = reports_by_month.N / len(temporal_analysis_reports) * 100
display(reports_by_year)
display(reports_by_month)
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ax[0].bar(reports_by_year.year.astype(str), reports_by_year.N)
ax[0].set(title='Informes/año (2022-2026)', ylabel='N')
temporal_analysis_reports.assign(period=temporal_analysis_reports.study_date_parsed.dt.to_period('M').astype(str)).groupby('period').size().plot(ax=ax[1])
ax[1].set(title='Informes/mes', ylabel='N')
plt.tight_layout()
plt.savefig(OUT / 'temporal_volume.png', dpi=140)
plt.show()
display(Markdown('Las fechas fuera de 2022-2026 no se eliminan de all_reports. Años parciales y meses ausentes no permiten inferir estacionalidad.'))


def within(df, groups, col):
    z = df.dropna(subset=groups + [col]).groupby(groups + [col]).size().rename('N').reset_index()
    d = df.dropna(subset=groups).groupby(groups).size().rename('group_N').reset_index()
    z = z.merge(d, on=groups)
    z['pct_within_group'] = z.N / z.group_N * 100
    return z
year_species = within(temporal_analysis_reports, ['year'], 'species')
year_sex = within(temporal_analysis_reports, ['year'], 'sex')
display(year_species)
display(year_sex)

def flag(n):
    return 'VERY_SMALL' if n < 5 else 'SMALL' if n < 20 else 'MODERATE' if n < 50 else 'ADEQUATE'
parts = []
for df, g, c, label in [(all_reports, ['species'], 'sex', 'species x sex'), (all_reports, ['species'], 'age_band_eda', 'species x age_band'), (all_reports, ['species'], 'breed', 'species x breed'), (all_reports, ['sex'], 'age_band_eda', 'sex x age_band'), (temporal_analysis_reports, ['year'], 'species', 'year x species')]:
    z = within(df, g, c)
    z['cross'] = label
    z['size_flag'] = z.N.map(flag)
    parts.append(z)
future_analysis_sample_sizes = pd.concat(parts, ignore_index=True)
display(future_analysis_sample_sizes.sort_values(['cross', 'N']))
for c, f in {'species': 'has_species', 'sex': 'has_sex', 'age_years': 'has_age', 'breed': 'has_breed', 'study_date_parsed': 'has_study_date'}.items():
    all_reports[f] = all_reports[c].notna()
demographic_missingness_patterns = all_reports.assign(pattern=all_reports[['has_species', 'has_sex', 'has_age', 'has_breed', 'has_study_date']].apply(lambda r: 'complete' if r.all() else ','.join((k[4:] for k, v in r.items() if not v)), axis=1)).groupby('pattern').size().rename('N').reset_index()
demographic_missingness_patterns['pct_total'] = demographic_missingness_patterns.N / len(all_reports) * 100
display(demographic_missingness_patterns.sort_values('N', ascending=False))
print('Complete species+sex+age:', all_reports[['has_species', 'has_sex', 'has_age']].all(axis=1).sum(), 'complete all four:', all_reports[['has_species', 'has_sex', 'has_age', 'has_breed']].all(axis=1).sum())


analytical_availability = pd.DataFrame([dict(den(c, n), n_categories=all_reports[c].nunique(), notes=note) for n, c, note in [('species', 'species', 'Variantes preservadas'), ('sex', 'sex', 'Dominio real'), ('age', 'age_years', 'Cobertura efectiva parser'), ('breed', 'breed', 'Sin normalización'), ('study_type', 'study_type', 'Dominio real'), ('outcome', 'outcome', 'Composición corpus'), ('study_date', 'study_date_parsed', 'Fecha válida; no study_date_raw')]])
display(analytical_availability)
exports = {'population_denominators': population_denominators, 'species_distribution': species_distribution, 'sex_distribution': sex_distribution, 'species_sex_distribution': species_sex_distribution, 'age_parser_audit': age_parser_audit, 'age_summary': age_summary, 'age_by_species': age_by_species, 'age_band_distribution': age_band_distribution, 'breed_distribution': breed_distribution, 'breed_by_species': breed_by_species, 'study_type_distribution': study_type_distribution, 'outcome_distribution': outcome_distribution, 'reports_by_year': reports_by_year, 'reports_by_month': reports_by_month, 'demographic_missingness_patterns': demographic_missingness_patterns, 'future_analysis_sample_sizes': future_analysis_sample_sizes}
for n, t in exports.items():
    t.to_csv(OUT / (n + '.csv'), index=False)
print('CSV exportados:', len(exports))


print('POPULATION DEMOGRAPHICS SUMMARY')
print('N total:', len(all_reports), 'N temporal:', len(temporal_analysis_reports))
print('Species:', species_distribution.to_dict('records'))
print('Sex:', sex_distribution.to_dict('records'))
print('Edad:', age_summary.to_dict('records'))
print('Parser:', all_reports.age_parse_status.value_counts().to_dict())
print('Breed top:', breed_distribution.head(10)[['breed', 'N']].to_dict('records'))
print('Study type:', study_type_distribution.to_dict('records'))
print('Outcome:', outcome_distribution.to_dict('records'))
print('Año:', reports_by_year[['year', 'N']].to_dict('records'))
print('Demografía completa species+sex+age+breed:', int(all_reports[['has_species', 'has_sex', 'has_age', 'has_breed']].all(axis=1).sum()))
print('Limitaciones demostradas: fechas faltantes/fuera de ventana, parser no efectivo en algunos textos, razas/estratos pequeños; corpus no equivale a población general; sin conclusiones clínicas.')


sha_post = hashlib.sha256(DB.read_bytes()).hexdigest().upper()
print('SHA PRE:', sha_pre)
print('SHA POST:', sha_post)
print('RESULTADO:', 'PASS — Gold no cambió' if sha_pre == sha_post else 'FAIL — Gold cambió')
assert sha_post == sha_pre
conn.close()


fig, ax = plt.subplots(figsize=(8, 4))
age_band_distribution.plot.bar(x='age_band', y='N', ax=ax, legend=False, title='Age bands EDA (N disponible)')
ax.set_xlabel('Age band EDA')
ax.set_ylabel('Informes (N)')
plt.tight_layout()
plt.savefig(OUT / 'age_bands.png', dpi=140)
plt.show()
fig, ax = plt.subplots(figsize=(9, 5))
age_by_species.set_index('species')['median_age'].sort_values().plot.barh(ax=ax)
ax.set_title('Edad mediana por especie (species N >= 20)')
ax.set_xlabel('Edad mediana (años)')
plt.tight_layout()
plt.savefig(OUT / 'median_age_by_species.png', dpi=140)
plt.show()
fig, ax = plt.subplots(figsize=(9, 4))
study_type_distribution.plot.bar(x='study_type', y='N', ax=ax, legend=False, title='Distribución de study_type')
ax.set_xlabel('Study type')
ax.set_ylabel('Informes (N)')
ax.tick_params(axis='x', rotation=35)
plt.tight_layout()
plt.savefig(OUT / 'study_type_distribution.png', dpi=140)
plt.show()
fig, ax = plt.subplots(figsize=(8, 4))
outcome_distribution.plot.bar(x='outcome', y='N', ax=ax, legend=False, title='Distribución de outcome')
ax.set_xlabel('Outcome')
ax.set_ylabel('Informes (N)')
ax.tick_params(axis='x', rotation=25)
plt.tight_layout()
plt.savefig(OUT / 'outcome_distribution.png', dpi=140)
plt.show()
fig, ax = plt.subplots(figsize=(10, 5))
year_species.pivot(index='year', columns='species', values='pct_within_group').plot.bar(stacked=True, ax=ax, title='Composición de species por año')
ax.set_ylabel('% dentro de año')
ax.set_xlabel('Año')
plt.tight_layout()
plt.savefig(OUT / 'species_composition_by_year.png', dpi=140)
plt.show()
fig, ax = plt.subplots(figsize=(10, 5))
year_sex.pivot(index='year', columns='sex', values='pct_within_group').plot.bar(stacked=True, ax=ax, title='Composición de sex por año')
ax.set_ylabel('% dentro de año')
ax.set_xlabel('Año')
plt.tight_layout()
plt.savefig(OUT / 'sex_composition_by_year.png', dpi=140)
plt.show()
fig, ax = plt.subplots(figsize=(9, 4))
z = demographic_missingness_patterns.head(12).sort_values('N')
ax.barh(z.pattern, z.pct_total)
ax.set_title('Missingness demográfico')
ax.set_xlabel('% del total')
plt.tight_layout()
plt.savefig(OUT / 'demographic_missingness.png', dpi=140)
plt.show()

