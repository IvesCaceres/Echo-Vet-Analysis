# Adapted analytical code; default PUBLIC_DEMO. No clinical results included.
from pathlib import Path
import sys
CODE_ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "scripts" / "gold_utils.py").is_file() and (p / "synthetic" / "schema.json").is_file())
sys.path.insert(0, str(CODE_ROOT / "scripts"))
from gold_utils import find_project_root, get_output_root


from pathlib import Path
import sys
import sqlite3
import hashlib
import re
from collections import Counter
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def _find_root(start):
    return find_project_root()
PROJECT_ROOT = _find_root(Path.cwd())
sys.path.insert(0, str(PROJECT_ROOT / 'scripts')) if str(PROJECT_ROOT / 'scripts') not in sys.path else None
from gold_utils import connect_gold_readonly, get_gold_db_path, quote_identifier, validate_gold_identity
DB_PATH = get_gold_db_path(PROJECT_ROOT)
OUTPUT_DIR = get_output_root() / 'data_quality'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
sha_pre = validate_gold_identity(DB_PATH)
db_stat_pre = DB_PATH.stat()
print(f'Proyecto: {PROJECT_ROOT}')
print('ACTIVE GOLD: gold_v2_final.db')
print(f'Gold: {DB_PATH}')
print(f'Tamaño: {db_stat_pre.st_size / 1024 ** 2:.2f} MB')
print(f'SHA-256 inicial: {sha_pre}')
print(f'Timestamp inicial UTC: {datetime.fromtimestamp(db_stat_pre.st_mtime).isoformat()}')
conn = connect_gold_readonly(DB_PATH)
quick_check = conn.execute('PRAGMA quick_check').fetchone()[0]
print(f'PRAGMA quick_check: {quick_check}')
assert quick_check == 'ok', 'quick_check no devuelve ok; auditoría detenida.'


def table_names(connection):
    return [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]

def table_info(table):
    return pd.read_sql_query(f'PRAGMA table_info({quote_identifier(table)})', conn)

def col_map(table):
    return {str(r['name']).lower(): r['name'] for _, r in table_info(table).iterrows()}

def find_col(table, candidates, contains=True):
    mapping = col_map(table)
    for candidate in candidates:
        if candidate.lower() in mapping:
            return mapping[candidate.lower()]
    if contains:
        for actual in mapping.values():
            low = actual.lower()
            if any((c.lower() in low for c in candidates)):
                return actual
    return None

def qcol(column):
    return quote_identifier(column)

def qtable(table):
    return quote_identifier(table)
tables = table_names(conn)
reports = 'gold_reports_v2' if 'gold_reports_v2' in tables else None
events = 'gold_clinical_events_v2' if 'gold_clinical_events_v2' in tables else None
concepts = 'dim_clinical_concept_v2' if 'dim_clinical_concept_v2' in tables else None
print(tables)


groups = {'fact': ['gold_reports_v2', 'gold_clinical_events_v2'], 'provenance': ['gold_event_provenance_v2', 'gold_discarded_event_provenance_v2'], 'dimension': ['dim_clinical_concept_v2', 'clinical_concept_alias_v2', 'clinical_concept_taxonomy_v2'], 'metadata': ['gold_build_runs_v2']}
snapshot = []
for t in tables:
    info = table_info(t)
    pk = info.loc[info.pk.gt(0), 'name'].tolist()
    fk_count = len(pd.read_sql_query(f'PRAGMA foreign_key_list({qtable(t)})', conn))
    snapshot.append({'table': t, 'row_count': conn.execute(f'SELECT COUNT(*) FROM {qtable(t)}').fetchone()[0], 'column_count': len(info), 'primary_key_columns': ', '.join(pk), 'foreign_key_count': fk_count, 'table_group': next((g for g, ts in groups.items() if t in ts), 'other')})
table_summary = pd.DataFrame(snapshot)
display(table_summary)


pk_results = []
for t in tables:
    info = table_info(t)
    pk_info = info[info.pk.gt(0)].sort_values('pk')
    pk_cols = pk_info.name.tolist()
    rows = conn.execute(f'SELECT COUNT(*) FROM {qtable(t)}').fetchone()[0]
    if not pk_cols:
        pk_results.append({'table': t, 'pk': '', 'rows': rows, 'non_null': np.nan, 'unique': np.nan, 'duplicates': np.nan, 'nulls': np.nan, 'status': 'WARNING'})
        continue
    cols = ', '.join((qcol(c) for c in pk_cols))
    non_null = conn.execute(f'SELECT COUNT(*) FROM {qtable(t)} WHERE ' + ' AND '.join((f'{qcol(c)} IS NOT NULL' for c in pk_cols))).fetchone()[0]
    unique = conn.execute(f'SELECT COUNT(*) FROM (SELECT {cols} FROM {qtable(t)} WHERE ' + ' AND '.join((f'{qcol(c)} IS NOT NULL' for c in pk_cols)) + f' GROUP BY {cols})').fetchone()[0]
    duplicates = non_null - unique
    nulls = rows - non_null
    status = 'PASS' if duplicates == 0 and nulls == 0 else 'FAIL' if duplicates > 0 else 'WARNING'
    pk_results.append({'table': t, 'pk': ', '.join(pk_cols), 'rows': rows, 'non_null': non_null, 'unique': unique, 'duplicates': duplicates, 'nulls': nulls, 'status': status})
primary_key_quality = pd.DataFrame(pk_results)
display(primary_key_quality)
fk_results = []
for child in tables:
    fk = pd.read_sql_query(f'PRAGMA foreign_key_list({qtable(child)})', conn)
    if fk.empty:
        continue
    for fk_id, grp in fk.groupby('id', sort=False):
        parent = grp.iloc[0]['table']
        child_cols = grp.sort_values('seq')['from'].tolist()
        parent_cols = grp.sort_values('seq')['to'].tolist()
        child_rows = conn.execute(f'SELECT COUNT(*) FROM {qtable(child)}').fetchone()[0]
        null_cond = ' AND '.join((f'{qcol(c)} IS NOT NULL' for c in child_cols))
        join_cond = ' AND '.join((f'c.{qcol(cc)} = p.{qcol(pc)}' for cc, pc in zip(child_cols, parent_cols)))
        matched = conn.execute(f"SELECT COUNT(*) FROM {qtable(child)} c JOIN {qtable(parent)} p ON {join_cond} WHERE {(null_cond.replace(qcol(child_cols[0]), 'c.' + qcol(child_cols[0])) if len(child_cols) == 1 else ' AND '.join(('c.' + qcol(c) + ' IS NOT NULL' for c in child_cols)))}").fetchone()[0]
        nonnull = conn.execute(f'SELECT COUNT(*) FROM {qtable(child)} WHERE {null_cond}').fetchone()[0]
        orphans = nonnull - matched
        pct = orphans / nonnull * 100 if nonnull else 0
        fk_results.append({'parent_table': parent, 'child_table': child, 'relationship': f'{child_cols} -> {parent_cols}', 'child_rows': child_rows, 'matched_rows': matched, 'orphan_rows': orphans, 'orphan_pct': pct, 'status': 'PASS' if orphans == 0 else 'FAIL'})
foreign_key_quality = pd.DataFrame(fk_results)
display(foreign_key_quality)


report_id_r = find_col(reports, ['report_id', 'study_id', 'id']) if reports else None
report_id_e = find_col(events, ['report_id', 'study_id']) if events else None
report_event_distribution = pd.DataFrame()
report_event_top20 = pd.DataFrame()
report_event_summary = {}
if reports and events and report_id_r and report_id_e:
    report_event_distribution = pd.read_sql_query(f'SELECT r.{qcol(report_id_r)} AS report_id, COUNT(e.{qcol(report_id_e)}) AS n_events_per_report FROM {qtable(reports)} r LEFT JOIN {qtable(events)} e ON r.{qcol(report_id_r)}=e.{qcol(report_id_e)} GROUP BY r.{qcol(report_id_r)}', conn)
    s = report_event_distribution.n_events_per_report
    report_event_summary = {'total_reports': len(s), 'reports_with_events': int((s > 0).sum()), 'reports_without_events': int((s == 0).sum()), 'pct_with_events': float((s > 0).mean() * 100), 'min': int(s.min()), 'max': int(s.max()), 'mean': float(s.mean()), 'median': float(s.median()), 'p25': float(s.quantile(0.25)), 'p75': float(s.quantile(0.75)), 'p90': float(s.quantile(0.9)), 'p95': float(s.quantile(0.95)), 'p99': float(s.quantile(0.99))}
    report_event_top20 = report_event_distribution.sort_values('n_events_per_report', ascending=False).head(20)
    display(pd.DataFrame([report_event_summary]))
    display(report_event_top20)
    report_event_distribution.to_csv(OUTPUT_DIR / 'events_per_report.csv', index=False)
else:
    print('No se pudo identificar una clave report→event real; se documenta como no evaluable.')


missing_rows = []
for t in tables:
    rows = conn.execute(f'SELECT COUNT(*) FROM {qtable(t)}').fetchone()[0]
    for _, r in table_info(t).iterrows():
        c = r['name']
        nonnull = conn.execute(f'SELECT COUNT({qcol(c)}) FROM {qtable(t)}').fetchone()[0]
        distinct = conn.execute(f'SELECT COUNT(DISTINCT {qcol(c)}) FROM {qtable(t)}').fetchone()[0]
        nulls = rows - nonnull
        pct = nulls / rows * 100 if rows else np.nan
        cls = 'NONE' if pct == 0 else 'LOW' if pct <= 5 else 'MODERATE' if pct <= 20 else 'HIGH' if pct <= 50 else 'VERY_HIGH'
        missing_rows.append({'table': t, 'column': c, 'row_count': rows, 'non_null_count': nonnull, 'null_count': nulls, 'null_pct': pct, 'distinct_count': distinct, 'missingness_class': cls})
missingness = pd.DataFrame(missing_rows).sort_values('null_pct', ascending=False, ignore_index=True)
display(missingness.head(30))


def value_profile(table, column, top_n=30):
    if not table or not column:
        return pd.DataFrame()
    d = pd.read_sql_query(f'SELECT {qcol(column)} AS value, COUNT(*) AS count FROM {qtable(table)} GROUP BY {qcol(column)} ORDER BY count DESC', conn)
    d['table'] = table
    d['column'] = column
    return d[['table', 'column', 'value', 'count']]
demographic_specs = {'species': ['species'], 'breed': ['breed'], 'sex': ['sex'], 'age': ['age_text', 'age']}
demographic_quality = []
demographic_values = {}
for label, cands in demographic_specs.items():
    c = find_col(reports, cands) if reports else None
    if c:
        m = missingness[(missingness.table == reports) & (missingness.column == c)].iloc[0]
        vals = value_profile(reports, c)
        demographic_values[label] = vals
        for _, v in vals.head(30).iterrows():
            demographic_quality.append({'variable': label, 'table': reports, 'column': c, 'total': m.row_count, 'non_null': m.non_null_count, 'nulls': m.null_count, 'coverage_pct': m.non_null_count / m.row_count * 100 if m.row_count else np.nan, 'cardinality': m.distinct_count, 'value': v.value, 'value_count': v['count']})
        print(f'### {label} ({c})')
        display(vals.head(30))
    else:
        print(f'{label}: columna no encontrada')
demographic_df = pd.DataFrame(demographic_quality)
age_col = find_col(reports, ['age_text', 'age']) if reports else None
if age_col:
    age_raw = pd.read_sql_query(f'SELECT {qcol(age_col)} AS value FROM {qtable(reports)}', conn)['value']

    def age_class(x):
        if pd.isna(x) or str(x).strip() == '':
            return 'missing'
        s = str(x).strip()
        return 'parsable' if re.fullmatch('\\\\d+(?:[.,]\\\\d+)?(?:\\\\s*(?:d|m|y|days?|months?|years?|años?|meses?))?', s, flags=re.I) else 'ambiguous' if re.search('\\\\d', s) else 'unparsable'
    age_parseability = age_raw.map(age_class).value_counts().rename_axis('classification').reset_index(name='count')
    display(age_parseability)


date_cols = []
if reports:
    date_cols = [c for c in table_info(reports).name if any((k in c.lower() for k in ['date', 'fecha'])) and (not any((k in c.lower() for k in ['precision', 'quality', 'source'])))]
temporal_rows = []
temporal_years = []
for c in date_cols:
    raw = pd.read_sql_query(f'SELECT {qcol(c)} AS value FROM {qtable(reports)}', conn)['value']
    parsed = pd.to_datetime(raw, errors='coerce')
    missing = raw.isna() | raw.astype(str).str.strip().eq('')
    valid = parsed.notna() & ~missing
    years = parsed[valid].dt.year
    for y, n in years.value_counts().sort_index().items():
        temporal_years.append({'column': c, 'year': int(y), 'count': int(n)})
    temporal_rows.append({'table': reports, 'column': c, 'total': len(raw), 'valid_dates': int(valid.sum()), 'nulls': int(missing.sum()), 'unparseable': int((~valid & ~missing).sum()), 'min': parsed.min(), 'max': parsed.max(), 'future_dates': int((parsed > pd.Timestamp.now()).sum()), 'out_of_expected_range': int(((parsed.dt.year < 2022) | (parsed.dt.year > 2026)).fillna(False).sum())})
temporal_quality = pd.DataFrame(temporal_rows)
temporal_year_df = pd.DataFrame(temporal_years)
display(temporal_quality)
display(temporal_year_df)
study_type_col = find_col(reports, ['study_type']) if reports else None
outcome_table = events if events and find_col(events, ['outcome']) else reports
outcome_col = find_col(outcome_table, ['outcome']) if outcome_table else None
study_type_values = value_profile(reports, study_type_col) if study_type_col else pd.DataFrame()
outcome_values = value_profile(outcome_table, outcome_col) if outcome_col else pd.DataFrame()
print('study_type')
display(study_type_values)
print('outcome')
display(outcome_values)


event_quality_rows = []
event_domains = {}
for label, cands in {'status': ['status'], 'strength': ['strength'], 'concept': ['concept', 'concept_id'], 'concept_id': ['concept_id']}.items():
    c = find_col(events, cands) if events else None
    if c:
        vals = value_profile(events, c)
        event_domains[label] = vals
        m = missingness[(missingness.table == events) & (missingness.column == c)].iloc[0]
        event_quality_rows.append({'variable': label, 'table': events, 'column': c, 'total': m.row_count, 'non_null': m.non_null_count, 'nulls': m.null_count, 'coverage_pct': m.non_null_count / m.row_count * 100 if m.row_count else np.nan, 'cardinality': m.distinct_count})
        print(f'### {label} ({c})')
        display(vals)
clinical_event_quality = pd.DataFrame(event_quality_rows)
status_col = find_col(events, ['status'])
strength_col = find_col(events, ['strength'])
status_strength = pd.DataFrame()
if status_col and strength_col:
    status_strength = pd.read_sql_query(f'SELECT {qcol(status_col)} AS status, {qcol(strength_col)} AS strength, COUNT(*) AS n FROM {qtable(events)} GROUP BY 1,2 ORDER BY n DESC', conn)
    display(status_strength)


concept_usage = pd.DataFrame()
concept_id_e = find_col(events, ['concept_id']) if events else None
concept_id_d = find_col(concepts, ['concept_id', 'id']) if concepts else None
if concepts and concept_id_d and events and concept_id_e:
    name_col = find_col(concepts, ['concept_name', 'name', 'label'], contains=False)
    select_name = f', d.{qcol(name_col)} AS concept_name' if name_col else ''
    concept_usage = pd.read_sql_query(f'SELECT d.{qcol(concept_id_d)} AS concept_id{select_name}, COUNT(e.{qcol(concept_id_e)}) AS event_count, COUNT(DISTINCT e.{qcol(report_id_e)}) AS report_count FROM {qtable(concepts)} d LEFT JOIN {qtable(events)} e ON d.{qcol(concept_id_d)}=e.{qcol(concept_id_e)} GROUP BY d.{qcol(concept_id_d)}' + (f', d.{qcol(name_col)}' if name_col else '') + ' ORDER BY event_count DESC', conn)
    concept_usage['used'] = concept_usage.event_count.gt(0)
    display(concept_usage)
    print('Conceptos sin uso:', int((~concept_usage.used).sum()), '| N=1:', int((concept_usage.event_count == 1).sum()), '| N<=3:', int((concept_usage.event_count <= 3).sum()))
else:
    print('No se pudo establecer concept_id entre dimensión y eventos.')


report_col = report_id_e
concept_col = concept_id_e or find_col(events, ['concept', 'canonical_concept']) if events else None
duplicate_key_cols = [c for c in [report_col, concept_col, status_col, strength_col] if c]
potential_duplicates = pd.DataFrame()
potential_contradictions = pd.DataFrame()
if events and duplicate_key_cols:
    dup_sql = f"SELECT {', '.join((qcol(c) for c in duplicate_key_cols))}, COUNT(*) AS n_events FROM {qtable(events)} GROUP BY {', '.join((qcol(c) for c in duplicate_key_cols))} HAVING COUNT(*)>1 ORDER BY n_events DESC"
    potential_duplicates = pd.read_sql_query(dup_sql, conn)
    potential_duplicates['classification'] = 'potential_duplicate'
    display(potential_duplicates.head(50))
if events and report_col and concept_col and status_col:
    potential_contradictions = pd.read_sql_query(f'SELECT {qcol(report_col)} AS report_id, {qcol(concept_col)} AS concept_id, COUNT(*) AS n_events, COUNT(DISTINCT {qcol(status_col)}) AS n_distinct_status, GROUP_CONCAT(DISTINCT {qcol(status_col)}) AS statuses FROM {qtable(events)} GROUP BY {qcol(report_col)}, {qcol(concept_col)} HAVING COUNT(DISTINCT {qcol(status_col)})>1 ORDER BY n_events DESC', conn)
    display(potential_contradictions.head(50))


provenance_quality = []
for child, parent in [('gold_event_provenance_v2', 'gold_clinical_events_v2'), ('gold_discarded_event_provenance_v2', 'gold_clinical_events_v2')]:
    if child not in tables:
        continue
    child_key = find_col(child, ['event_id', 'kept_event_id'])
    parent_key = find_col(parent, ['event_id', 'id'])
    if child_key and parent_key:
        cr = conn.execute(f'SELECT COUNT(*) FROM {qtable(child)}').fetchone()[0]
        matched = conn.execute(f'SELECT COUNT(*) FROM {qtable(child)} c JOIN {qtable(parent)} p ON c.{qcol(child_key)}=p.{qcol(parent_key)}').fetchone()[0]
        orphan = cr - matched
        multi = conn.execute(f'SELECT COUNT(*) FROM (SELECT {qcol(child_key)} FROM {qtable(child)} GROUP BY {qcol(child_key)} HAVING COUNT(*)>1)').fetchone()[0]
        provenance_quality.append({'child_table': child, 'parent_table': parent, 'child_rows': cr, 'matched_rows': matched, 'orphan_rows': orphan, 'orphan_pct': orphan / cr * 100 if cr else 0, 'parent_keys_with_multiple_child_rows': multi, 'status': 'PASS' if orphan == 0 else 'WARNING'})
provenance_quality = pd.DataFrame(provenance_quality)
display(provenance_quality)
discarded_summary = pd.DataFrame()
if 'gold_discarded_event_provenance_v2' in tables:
    dt = 'gold_discarded_event_provenance_v2'
    candidates = [c for c in table_info(dt).name if any((k in c.lower() for k in ['reason', 'status', 'concept', 'report', 'event', 'date']))]
    rows = []
    for c in candidates:
        vals = value_profile(dt, c)
        rows.append(vals.assign(profile_column=c))
    discarded_summary = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    display(discarded_summary)
for t in ['clinical_concept_alias_v2', 'clinical_concept_taxonomy_v2']:
    if t in tables:
        print(t)
        display(pd.read_sql_query(f'SELECT * FROM {qtable(t)}', conn))


empty_tokens = ['', ' ', 'NA', 'N/A', 'NULL', 'None', 'unknown', 'Unknown', '-']
empty_rows = []
for t in [x for x in [reports, events] if x]:
    for c in table_info(t).query("type.str.upper().str.contains('CHAR|TEXT', na=False)").name:
        placeholders = ', '.join(('?' for _ in empty_tokens))
        counts = conn.execute(f'SELECT COUNT(*) FROM {qtable(t)} WHERE {qcol(c)} IN ({placeholders})', empty_tokens).fetchone()[0]
        if counts:
            empty_rows.append({'table': t, 'column': c, 'empty_token_frequency': counts})
empty_values = pd.DataFrame(empty_rows)
display(empty_values)
cardinality_rows = []
for t in [x for x in [reports, events] if x]:
    for c in table_info(t).name:
        if c.lower() in ['species', 'breed', 'sex', 'study_type', 'outcome', 'status', 'strength', 'concept', 'concept_id'] or any((k in c.lower() for k in ['study_type', 'outcome'])):
            vals = value_profile(t, c)
            total = vals['count'].sum() if not vals.empty else 0
            top = vals.iloc[0] if not vals.empty else None
            cardinality_rows.append({'table': t, 'column': c, 'n_unique': len(vals), 'top_value': top.value if top is not None else None, 'top_value_count': int(top['count']) if top is not None else 0, 'top_value_pct': float(top['count'] / total * 100) if top is not None and total else np.nan})
cardinality = pd.DataFrame(cardinality_rows)
display(cardinality)
annual_quality = pd.DataFrame()
date_col = find_col(reports, ['study_date', 'date']) if reports else None
if reports and date_col and report_id_r:
    annual_quality = pd.read_sql_query(f"SELECT CAST(strftime('%Y',{qcol(date_col)}) AS INTEGER) AS year, COUNT(*) AS reports FROM {qtable(reports)} WHERE {qcol(date_col)} IS NOT NULL GROUP BY 1 ORDER BY 1", conn)
    for label, cands in [('demographics', ['species']), ('age', ['age_text', 'age']), ('sex', ['sex']), ('breed', ['breed'])]:
        c = find_col(reports, cands)
        if c:
            annual_quality[f'reports_with_{label}'] = pd.read_sql_query(f"SELECT CAST(strftime('%Y',{qcol(date_col)}) AS INTEGER) AS year, COUNT({qcol(c)}) AS n FROM {qtable(reports)} WHERE {qcol(date_col)} IS NOT NULL GROUP BY 1 ORDER BY 1", conn)['n'].values
    annual_quality['events'] = annual_quality.year.map(report_event_distribution.assign(year=0).set_index('year').n_events_per_report.sum() if False else {})
    display(annual_quality)


readiness = []

def add_readiness(name, table, coverage, issues, cardinality, notes):
    flag = 'READY' if coverage >= 95 and issues == 0 else 'NOT_READY' if coverage < 50 or (issues > 0 and coverage < 80) else 'USABLE_WITH_CAUTION'
    rec = 'READY' if flag == 'READY' else 'NOT_READY' if flag == 'NOT_READY' else 'USABLE_WITH_CAUTION'
    readiness.append({'variable_or_domain': name, 'table': table, 'coverage_pct': coverage, 'consistency_issue_count': issues, 'consistency_issue_pct': issues / (len(report_event_distribution) or 1) * 100, 'cardinality': cardinality, 'quality_flag': flag, 'recommended_use': rec, 'notes': notes})
for label in ['species', 'breed', 'sex', 'age']:
    c = find_col(reports, demographic_specs[label]) if reports else None
    if c:
        m = missingness[(missingness.table == reports) & (missingness.column == c)].iloc[0]
        add_readiness(label, reports, m.non_null_count / m.row_count * 100, 0, int(m.distinct_count), f'Cobertura calculada sobre informes; revisar variantes superficiales.')
if date_col and (not temporal_quality.empty):
    tq = temporal_quality.iloc[0]
    add_readiness('study_date', reports, tq.valid_dates / tq.total * 100, int(tq.unparseable + tq.out_of_expected_range), int(tq.valid_dates), 'Rango esperado descriptivo 2022–2026; fuera de rango no implica error.')
if status_col:
    m = missingness[(missingness.table == events) & (missingness.column == status_col)].iloc[0]
    add_readiness('status', events, m.non_null_count / m.row_count * 100, 0, int(m.distinct_count), 'Dominio descriptivo; no se interpretan estados clínicamente.')
if concept_usage.empty:
    add_readiness('clinical_concepts', concepts, 0, 1, 0, 'No se pudo verificar uso de conceptos.')
else:
    add_readiness('clinical_concepts', concepts, float(concept_usage.used.mean() * 100), 0, len(concept_usage), 'Uso medido a nivel evento; report_count separado.')
analytical_readiness_matrix = pd.DataFrame(readiness)
display(analytical_readiness_matrix)


exports = {'table_summary': table_summary, 'primary_key_quality': primary_key_quality, 'foreign_key_quality': foreign_key_quality, 'missingness': missingness, 'demographic_quality': demographic_df, 'temporal_quality': temporal_quality, 'clinical_event_quality': clinical_event_quality, 'concept_usage': concept_usage, 'potential_duplicates': potential_duplicates, 'potential_contradictions': potential_contradictions, 'provenance_quality': provenance_quality, 'discarded_events_summary': discarded_summary, 'analytical_readiness_matrix': analytical_readiness_matrix}
for name, df in exports.items():
    if isinstance(df, pd.DataFrame) and (not df.empty):
        df.to_csv(OUTPUT_DIR / f'{name}.csv', index=False)
print(f'CSV exportados en {OUTPUT_DIR}')
plot_paths = []
if 'species' in demographic_values:
    demographic_values['species']['value'] = demographic_values['species']['value'].map(str)
if not report_event_distribution.empty:
    plt.figure(figsize=(8, 4))
    plt.hist(report_event_distribution.n_events_per_report, bins=30)
    plt.title('Distribución de eventos por informe')
    plt.xlabel('Número de eventos por informe')
    plt.ylabel('Número de informes')
    plt.tight_layout()
    p = OUTPUT_DIR / 'events_per_report.png'
    plt.savefig(p, dpi=130)
    plot_paths.append(p)
    plt.show()
if not missingness.empty:
    topmiss = missingness.head(15).sort_values('null_pct')
    plt.figure(figsize=(8, 5))
    plt.barh(topmiss.table + '·' + topmiss.column, topmiss.null_pct)
    plt.title('Missingness — principales columnas')
    plt.xlabel('NULL (%)')
    plt.tight_layout()
    p = OUTPUT_DIR / 'missingness_top.png'
    plt.savefig(p, dpi=130)
    plot_paths.append(p)
    plt.show()
if not temporal_year_df.empty:
    temporal_year_df.groupby('year', as_index=False)['count'].sum().plot(x='year', y='count', kind='bar', legend=False, title='Registros temporales por año')
    plt.ylabel('Registros')
    plt.tight_layout()
    p = OUTPUT_DIR / 'records_by_year.png'
    plt.savefig(p, dpi=130)
    plot_paths.append(p)
    plt.show()
if 'species' in demographic_values:
    v = demographic_values['species'].head(15).sort_values('count')
    plt.figure(figsize=(8, 4))
    plt.barh([str(x) for x in v.value.tolist()], v['count'])
    plt.title('Species — valores más frecuentes')
    plt.xlabel('Frecuencia')
    plt.tight_layout()
    p = OUTPUT_DIR / 'species_top.png'
    plt.savefig(p, dpi=130)
    plot_paths.append(p)
    plt.show()


sha_post = hashlib.sha256(DB_PATH.read_bytes()).hexdigest().upper()
db_stat_post = DB_PATH.stat()
assert sha_post == sha_pre, 'INCIDENTE: SHA-256 de Gold cambió.'
print('1. Integridad relacional:')
print('   ', 'PASS — sin huérfanos en FKs declaradas.' if foreign_key_quality.empty or foreign_key_quality.orphan_rows.sum() == 0 else f'WARNING/FAIL — {int(foreign_key_quality.orphan_rows.sum())} huérfanos.')
if report_event_summary:
    print(f"2. Cobertura report→event: {report_event_summary['reports_with_events']}/{report_event_summary['total_reports']} informes ({report_event_summary['pct_with_events']:.2f}%).")
for label in ['species', 'breed', 'sex', 'age']:
    if label in demographic_values:
        c = find_col(reports, demographic_specs[label])
        m = missingness[(missingness.table == reports) & (missingness.column == c)].iloc[0]
        print(f'3. {label}: {m.non_null_count}/{m.row_count} no nulos ({m.non_null_count / m.row_count * 100:.2f}%), cardinalidad {m.distinct_count}.')
if not temporal_quality.empty:
    print(f"4. Temporal: {temporal_quality.iloc[0]['min']} a {temporal_quality.iloc[0]['max']}; no parseables={int(temporal_quality.iloc[0]['unparseable'])}; fuera de rango={int(temporal_quality.iloc[0]['out_of_expected_range'])}.")
event_column_count = len(pd.read_sql_query(f'SELECT * FROM {qtable(events)} LIMIT 1', conn).columns) if events else 0
print(f'5. Eventos: {event_column_count} columnas; duplicados potenciales: {len(potential_duplicates)} grupos; contradicciones potenciales: {len(potential_contradictions)} grupos.')
print(f"6. Provenance: {(provenance_quality.to_dict('records') if not provenance_quality.empty else 'no evaluable')}.")
if not concept_usage.empty:
    print(f'7. Conceptos usados: {int(concept_usage.used.sum())}/{len(concept_usage)}; no usados: {int((~concept_usage.used).sum())}.')
print('8. Dimensiones READY:')
display(analytical_readiness_matrix.query("quality_flag=='READY'"))
print('   Dimensiones USABLE_WITH_CAUTION:')
display(analytical_readiness_matrix.query("quality_flag=='USABLE_WITH_CAUTION'"))
print('   Dimensiones NOT_READY:')
display(analytical_readiness_matrix.query("quality_flag=='NOT_READY'"))
print('9. Unidad de análisis: informes/estudios y eventos son niveles distintos; no usar eventos como denominador de prevalencia.')
print(f'10. Gold inmutable: SHA POST={sha_post}; tamaño POST={db_stat_post.st_size}; timestamp POST={datetime.fromtimestamp(db_stat_post.st_mtime).isoformat()}')
conn.close()

