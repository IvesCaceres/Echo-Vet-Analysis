# Adapted analytical code; default PUBLIC_DEMO. No clinical results included.
from pathlib import Path
import sys
CODE_ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "scripts" / "gold_utils.py").is_file() and (p / "synthetic" / "schema.json").is_file())
sys.path.insert(0, str(CODE_ROOT / "scripts"))
from gold_utils import find_project_root, get_output_root


from pathlib import Path
import sys, hashlib, itertools
import pandas as pd, numpy as np, matplotlib.pyplot as plt
from display_helpers import display, Markdown

def root_of(p):
    return find_project_root()
ROOT = root_of(Path.cwd())
sys.path.insert(0, str(ROOT / 'scripts'))
from gold_utils import connect_gold_readonly, get_gold_db_path, validate_gold_identity
DB = get_gold_db_path(ROOT)
OUT = get_output_root() / 'event_consistency_audit'
OUT.mkdir(parents=True, exist_ok=True)
sha_pre = validate_gold_identity(DB)
conn = connect_gold_readonly(DB)
qc = conn.execute('PRAGMA quick_check').fetchone()[0]
print('ACTIVE GOLD: gold_v2_final.db')
print('Gold:', DB, 'SHA PRE:', sha_pre, 'size:', DB.stat().st_size, 'quick_check:', qc)
assert qc == 'ok'


tables = ['gold_reports_v2', 'gold_clinical_events_v2', 'gold_event_provenance_v2', 'gold_discarded_event_provenance_v2', 'dim_clinical_concept_v2']
for t in tables:
    print('\n###', t)
    display(pd.read_sql_query('PRAGMA table_info("' + t + '")', conn))
reports = pd.read_sql_query('select report_id,study_date,species,breed,sex,age_text,study_type,outcome,semantic_version,source_document,source_path from gold_reports_v2', conn)
events = pd.read_sql_query('select * from gold_clinical_events_v2', conn)
prov = pd.read_sql_query('select * from gold_event_provenance_v2', conn)
discarded = pd.read_sql_query('select * from gold_discarded_event_provenance_v2', conn)
concepts = pd.read_sql_query('select concept_id,canonical_name,display_name,concept_type,active,semantic_version from dim_clinical_concept_v2', conn)
print('Rows reports/events/prov/discarded/concepts:', len(reports), len(events), len(prov), len(discarded), len(concepts))
print('Provenance cardinality:', prov.groupby('event_id').size().value_counts().to_dict())
assert len(events) == len(prov) and prov.event_id.nunique() == len(events)


dup_key = ['report_id', 'concept_id', 'assertion_status', 'strength']
dup_groups = events.groupby(dup_key, dropna=False).size().reset_index(name='n_events').query('n_events>1').copy()
dup_groups['audit_group_id'] = ['DUP_%04d' % i for i in range(1, len(dup_groups) + 1)]
ms_groups = events.groupby(['report_id', 'concept_id']).agg(n_events=('event_id', 'size'), n_distinct_status=('assertion_status', 'nunique')).reset_index().query('n_distinct_status>1').copy()
ms_groups['audit_group_id'] = ['MS_%04d' % i for i in range(1, len(ms_groups) + 1)]
print('duplicate groups/events/reports/concepts:', len(dup_groups), dup_groups.n_events.sum(), dup_groups.report_id.nunique(), dup_groups.concept_id.nunique())
print('multi-status groups/events/reports/concepts:', len(ms_groups), ms_groups.n_events.sum(), ms_groups.report_id.nunique(), ms_groups.concept_id.nunique())
assert len(dup_groups) >= 0 and len(ms_groups) >= 0
D = set(zip(dup_groups.report_id, dup_groups.concept_id))
M = set(zip(ms_groups.report_id, ms_groups.concept_id))
U = D | M
overlap_summary = pd.DataFrame([{'grupo': 'duplicate_groups', 'N': len(D), 'pct_union': len(D) / len(U) * 100}, {'grupo': 'multi_status_groups', 'N': len(M), 'pct_union': len(M) / len(U) * 100}, {'grupo': 'intersection', 'N': len(D & M), 'pct_union': len(D & M) / len(U) * 100}, {'grupo': 'duplicate_only', 'N': len(D - M), 'pct_union': len(D - M) / len(U) * 100}, {'grupo': 'multi_status_only', 'N': len(M - D), 'pct_union': len(M - D) / len(U) * 100}])
display(overlap_summary)


base = events.merge(concepts[['concept_id', 'canonical_name', 'display_name']], on='concept_id', how='left').merge(reports, on='report_id', how='left', suffixes=('', '_report')).merge(prov, on='event_id', how='left', suffixes=('', '_prov'))
audit = []
for _, g in dup_groups.iterrows():
    q = (events.report_id == g.report_id) & (events.concept_id == g.concept_id) & (events.assertion_status == g.assertion_status)
    q = q & (events.strength.isna() if pd.isna(g.strength) else events.strength.eq(g.strength))
    audit += [{'audit_group_id': g.audit_group_id, 'audit_type': 'DUPLICATE', 'event_id': e} for e in events.loc[q, 'event_id']]
for _, g in ms_groups.iterrows():
    audit += [{'audit_group_id': g.audit_group_id, 'audit_type': 'MULTI_STATUS', 'event_id': e} for e in events.loc[(events.report_id == g.report_id) & (events.concept_id == g.concept_id), 'event_id']]
audit_index = pd.DataFrame(audit)
expanded = audit_index.merge(base, on='event_id', how='left')
duplicate_events_expanded = expanded[expanded.audit_type == 'DUPLICATE'].copy()
multistatus_events_expanded = expanded[expanded.audit_type == 'MULTI_STATUS'].copy()
print('expanded duplicate/multi events:', len(duplicate_events_expanded), len(multistatus_events_expanded))
display(expanded.head(8))


def rel(g):
    spans = list(zip(g.source_span_start, g.source_span_end))
    texts = g.source_text.fillna('').astype(str)
    hashes = g.source_hash.fillna('').astype(str)
    clauses = g.source_clause.fillna('').astype(str)
    same_span = len(set(spans)) == 1
    same_text = texts.nunique() == 1 and texts.iloc[0] != ''
    same_hash = hashes.nunique() == 1 and hashes.iloc[0] != ''
    nonoverlap = True
    for a, b in itertools.combinations(spans, 2):
        if all((pd.notna(x) for x in a + b)) and max(a[0], b[0]) < min(a[1], b[1]):
            nonoverlap = False
    if same_span and (same_text or same_hash):
        return 'SAME_SOURCE_STRONG'
    if same_text and same_hash and nonoverlap:
        return 'SAME_SOURCE_STRONG'
    if nonoverlap and (texts.nunique() > 1 or clauses.nunique() > 1 or hashes.nunique() > 1):
        return 'DISTINCT_MENTIONS'
    if clauses.nunique() == 1:
        return 'SAME_SECTION_UNKNOWN'
    return 'UNKNOWN_RELATION'

def evidence(tab):
    rows = []
    for gid, g in tab.groupby('audit_group_id'):
        rows.append({'audit_group_id': gid, 'report_id': g.report_id.iloc[0], 'concept_id': g.concept_id.iloc[0], 'concept_name': g.canonical_name.iloc[0], 'n_events': len(g), 'status_combination': '|'.join(sorted(g.assertion_status.unique())), 'mention_relation': rel(g), 'same_section': g.source_clause.nunique() == 1, 'same_span': g[['source_span_start', 'source_span_end']].drop_duplicates().shape[0] == 1, 'source_text_nunique': g.source_text.nunique(), 'source_hash_nunique': g.source_hash.nunique()})
    return pd.DataFrame(rows)
duplicate_group_evidence = evidence(duplicate_events_expanded)
multistatus_group_evidence = evidence(multistatus_events_expanded)
for tab in [duplicate_group_evidence, multistatus_group_evidence]:
    for reason, col in [('SAME_MENTION_OVERLAP', 'discarded_overlap'), ('TRUE_DUPLICATE', 'discarded_true_duplicate'), ('ALIAS_DUPLICATION', 'discarded_alias_duplication')]:
        z = discarded[discarded.discard_reason == reason].groupby(['report_id', 'canonical_concept']).size()
        tab[col] = [z.get((r, c), 0) for r, c in zip(tab.report_id, tab.concept_name)]
print('discarded reasons:', discarded.discard_reason.value_counts().to_dict())


def dclass(r):
    if r.mention_relation == 'SAME_SOURCE_STRONG':
        return 'LIKELY_TRUE_DUPLICATE'
    if r.mention_relation == 'DISTINCT_MENTIONS':
        return 'DISTINCT_MENTIONS_SAME_CONCEPT'
    if r.mention_relation == 'SAME_SECTION_UNKNOWN':
        return 'POSSIBLE_DUPLICATE'
    return 'UNRESOLVED'
duplicate_group_evidence['classification'] = duplicate_group_evidence.apply(dclass, axis=1)
duplicate_classification = duplicate_group_evidence.groupby('classification').agg(groups=('audit_group_id', 'count'), events=('n_events', 'sum'), reports=('report_id', 'nunique')).reset_index()
duplicate_classification['pct'] = duplicate_classification.groups / len(dup_groups) * 100
display(duplicate_classification)
display(Markdown('La clasificación no elimina eventos. La evidencia insuficiente queda UNRESOLVED.'))


status_combination_summary = multistatus_group_evidence.groupby('status_combination').agg(group_count=('audit_group_id', 'count'), report_count=('report_id', 'nunique'), concept_count=('concept_id', 'nunique'), event_count=('n_events', 'sum')).reset_index()
status_combination_summary['pct_of_multistatus_groups'] = status_combination_summary.group_count / len(ms_groups) * 100
status_combination_summary = status_combination_summary.sort_values('group_count', ascending=False)
display(status_combination_summary)

def mclass(r):
    s = set(r.status_combination.split('|'))
    if len(s) >= 3 or 'absent' in s:
        return 'HIGH_PRIORITY_REVIEW'
    if s == {'suspected', 'differential'} or r.mention_relation == 'DISTINCT_MENTIONS':
        return 'LIKELY_COMPATIBLE'
    if r.mention_relation == 'SAME_SOURCE_STRONG':
        return 'POTENTIAL_CONFLICT'
    return 'UNRESOLVED'
multistatus_group_evidence['classification'] = multistatus_group_evidence.apply(mclass, axis=1)
multistatus_classification = multistatus_group_evidence.groupby('classification').agg(groups=('audit_group_id', 'count'), events=('n_events', 'sum'), reports=('report_id', 'nunique')).reset_index()
multistatus_classification['pct'] = multistatus_classification.groups / len(ms_groups) * 100
display(multistatus_classification)
high_priority_cases = multistatus_group_evidence[multistatus_group_evidence.classification == 'HIGH_PRIORITY_REVIEW'].copy()
for combo in ['absent|confirmed', 'absent|suspected', 'absent|differential', 'confirmed|suspected', 'confirmed|differential', 'differential|suspected']:
    print(combo)
    display(multistatus_group_evidence[multistatus_group_evidence.status_combination == combo][['audit_group_id', 'report_id', 'concept_id', 'concept_name', 'mention_relation', 'n_events']].head(20))


three_status = multistatus_group_evidence[multistatus_group_evidence.status_combination.str.count('\\|') >= 2].copy()
print('3+ statuses:', len(three_status))
display(three_status)
concept_issue_summary = events.merge(concepts[['concept_id', 'canonical_name']], on='concept_id').groupby(['concept_id', 'canonical_name']).agg(total_events=('event_id', 'count')).reset_index()
for n, t in [('duplicate_group_count', duplicate_group_evidence), ('multi_status_group_count', multistatus_group_evidence), ('high_concern_group_count', high_priority_cases)]:
    concept_issue_summary = concept_issue_summary.merge(t.groupby(['concept_id', 'concept_name']).size().rename(n), left_on=['concept_id', 'canonical_name'], right_index=True, how='left')
concept_issue_summary = concept_issue_summary.fillna(0).sort_values(['multi_status_group_count', 'duplicate_group_count'], ascending=False)
report_issue_summary = pd.DataFrame({'report_id': sorted(set(dup_groups.report_id) | set(ms_groups.report_id))})
for n, t in [('duplicate_group_count', duplicate_group_evidence), ('multi_status_group_count', multistatus_group_evidence), ('high_concern_group_count', high_priority_cases)]:
    report_issue_summary = report_issue_summary.merge(t.groupby('report_id').size().rename(n), on='report_id', how='left')
report_issue_summary = report_issue_summary.fillna(0).sort_values(['multi_status_group_count', 'duplicate_group_count'], ascending=False)
display(concept_issue_summary.head(20))
display(report_issue_summary.head(20))
for t in [duplicate_group_evidence, multistatus_group_evidence]:
    t['year'] = pd.to_datetime(t.report_id.map(reports.set_index('report_id').study_date), errors='coerce').dt.year
year_issue = pd.concat([duplicate_group_evidence.assign(issue='duplicate'), multistatus_group_evidence.assign(issue='multi_status')]).groupby(['year', 'issue']).size().unstack(fill_value=0).reset_index()
display(year_issue)


def samp(t, n):
    return t.sample(min(n, len(t)), random_state=20260817)
parts = []
for label, t in [('LIKELY_TRUE_DUPLICATE', duplicate_group_evidence[duplicate_group_evidence.classification == 'LIKELY_TRUE_DUPLICATE']), ('DISTINCT_MENTIONS_SAME_CONCEPT', duplicate_group_evidence[duplicate_group_evidence.classification == 'DISTINCT_MENTIONS_SAME_CONCEPT']), ('confirmed+absent', multistatus_group_evidence[multistatus_group_evidence.status_combination == 'absent|confirmed']), ('suspected+absent', multistatus_group_evidence[multistatus_group_evidence.status_combination == 'absent|suspected']), ('differential+absent', multistatus_group_evidence[multistatus_group_evidence.status_combination == 'absent|differential']), ('confirmed+suspected', multistatus_group_evidence[multistatus_group_evidence.status_combination == 'confirmed|suspected']), ('confirmed+differential', multistatus_group_evidence[multistatus_group_evidence.status_combination == 'confirmed|differential']), ('suspected+differential', multistatus_group_evidence[multistatus_group_evidence.status_combination == 'differential|suspected']), ('>=3 statuses', three_status)]:
    z = samp(t, 10).copy()
    z['review_stratum'] = label
    parts.append(z)
manual_review_sample = pd.concat(parts, ignore_index=True).drop_duplicates('audit_group_id')
display(manual_review_sample[['audit_group_id', 'review_stratum', 'report_id', 'concept_id', 'concept_name', 'status_combination', 'mention_relation', 'n_events']])


pair = events.groupby(['report_id', 'concept_id']).agg(event_count=('event_id', 'size'), status_count=('assertion_status', 'nunique'), statuses=('assertion_status', lambda x: '|'.join(sorted(set(x))))).reset_index()
pairs = len(pair)
multi_pairs = (pair.status_count > 1).sum()
pair['status_set'] = pair.statuses.str.split('|')
pair['has_positive'] = pair.status_set.map(lambda s: bool(set(s) & {'confirmed', 'suspected', 'differential'}))
pair['only_absent'] = pair.status_set.map(lambda s: set(s) == {'absent'})
pair['status_unique'] = pair.status_count.eq(1)
pair_summary = pd.DataFrame([{'category': 'unique_report_concept_pairs', 'N': pairs}, {'category': 'pairs_with_single_status', 'N': int(pair.status_unique.sum())}, {'category': 'pairs_with_multiple_statuses', 'N': int((~pair.status_unique).sum())}, {'category': 'pairs_with_any_positive_status', 'N': int(pair.has_positive.sum())}, {'category': 'pairs_only_absent', 'N': int(pair.only_absent.sum())}])
display(pair_summary)
pair_summary.to_csv(OUT / 'report_concept_pair_summary.csv', index=False)
prevalence_rule_simulation = pd.DataFrame([{'rule': 'A_one_report_concept_max', 'unique_pairs': pairs, 'multi_status_pairs': multi_pairs, 'affected_pairs': multi_pairs, 'affected_pct': multi_pairs / pairs * 100, 'note': 'requiere resolver eventos dentro del par'}, {'rule': 'B_hypothetical_confirmed_priority', 'unique_pairs': pairs, 'multi_status_pairs': multi_pairs, 'affected_pairs': multi_pairs, 'affected_pct': multi_pairs / pairs * 100, 'note': 'simulación, no regla definitiva'}, {'rule': 'C_separate_assertion_status', 'unique_pairs': pairs, 'multi_status_pairs': multi_pairs, 'affected_pairs': 0, 'affected_pct': 0, 'note': 'preserva estados, exige denominadores separados'}, {'rule': 'D_combined_status_categories', 'unique_pairs': pairs, 'multi_status_pairs': multi_pairs, 'affected_pairs': multi_pairs, 'affected_pct': multi_pairs / pairs * 100, 'note': 'transparente, menos comparable'}])
display(prevalence_rule_simulation)
display(Markdown('Absent no equivale a normal; event_count no equivale a case_count. La unidad futura probable es report_id + concept_id, pendiente de resolución.'))


fig, ax = plt.subplots(1, 2, figsize=(12, 4))
status_combination_summary.head(12).plot.barh(x='status_combination', y='group_count', ax=ax[0], legend=False, title='Multi-status combinations')
multistatus_classification.plot.bar(x='classification', y='groups', ax=ax[1], legend=False, title='Multi-status classification')
ax[1].tick_params(axis='x', rotation=35)
plt.tight_layout()
plt.savefig(OUT / 'combinations_classification.png', dpi=140)
plt.show()
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
duplicate_classification.plot.bar(x='classification', y='groups', ax=ax[0], legend=False, title='Duplicate classification')
concept_issue_summary.head(10).sort_values('duplicate_group_count').plot.barh(x='canonical_name', y='duplicate_group_count', ax=ax[1], legend=False, title='Top concepts duplicate groups')
plt.tight_layout()
plt.savefig(OUT / 'duplicates_concepts.png', dpi=140)
plt.show()
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
year_issue.set_index('year').plot.bar(ax=ax[0], title='Issues by year')
multistatus_group_evidence.mention_relation.value_counts().plot.bar(ax=ax[1], title='Source relation')
plt.tight_layout()
plt.savefig(OUT / 'time_source_relation.png', dpi=140)
plt.show()
for n, t in {'duplicate_groups': dup_groups, 'duplicate_events_expanded': duplicate_events_expanded, 'duplicate_classification': duplicate_classification, 'multistatus_groups': ms_groups, 'multistatus_events_expanded': multistatus_events_expanded, 'status_combination_summary': status_combination_summary, 'multistatus_classification': multistatus_classification, 'high_priority_cases': high_priority_cases, 'concept_issue_summary': concept_issue_summary, 'report_issue_summary': report_issue_summary, 'manual_review_sample': manual_review_sample, 'prevalence_rule_simulation': prevalence_rule_simulation}.items():
    t.to_csv(OUT / (n + '.csv'), index=False)
print('EVENT CONSISTENCY AUDIT SUMMARY')
print('DUP', len(dup_groups), int(dup_groups.n_events.sum()), dup_groups.report_id.nunique())
print('DUP CLASS', duplicate_classification.to_dict('records'))
print('MULTI', len(ms_groups), int(ms_groups.n_events.sum()), ms_groups.report_id.nunique())
print('COMBINATIONS', status_combination_summary.to_dict('records'))
print('HIGH', len(high_priority_cases), 'ABSENT', multistatus_group_evidence.status_combination.str.contains('absent').sum(), '3+', len(three_status))
print('PAIRS', pairs, 'AFFECTED', multi_pairs, multi_pairs / pairs * 100)
print('RECOMMENDATION: MANUAL_REVIEW_REQUIRED')
print('Manual sample:', len(manual_review_sample))


sha_post = hashlib.sha256(DB.read_bytes()).hexdigest().upper()
print('SHA PRE:', sha_pre)
print('SHA POST:', sha_post)
print('quick_check:', conn.execute('PRAGMA quick_check').fetchone()[0])
print('RESULTADO:', 'PASS — Gold no cambió' if sha_pre == sha_post else 'FAIL — Gold cambió')
assert sha_post == sha_pre and conn.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
conn.close()


ctx_cols = ['audit_group_id', 'event_id', 'report_id', 'study_date', 'species', 'breed', 'sex', 'age_text', 'concept_id', 'concept_name', 'assertion_status', 'source_text', 'source_clause', 'source_span_start', 'source_span_end', 'source_type', 'event_origin', 'source_hash', 'rule_id', 'discarded_overlap', 'discarded_true_duplicate', 'discarded_alias_duplication', 'review_stratum']
manual_context = pd.concat([manual_review_sample.merge(duplicate_events_expanded[['audit_group_id', 'event_id', 'report_id', 'concept_id', 'assertion_status', 'source_text', 'source_clause', 'source_span_start', 'source_span_end', 'source_type', 'event_origin', 'source_hash', 'rule_id']], on=['audit_group_id', 'report_id', 'concept_id'], how='left'), manual_review_sample.merge(multistatus_events_expanded[['audit_group_id', 'event_id', 'report_id', 'concept_id', 'assertion_status', 'source_text', 'source_clause', 'source_span_start', 'source_span_end', 'source_type', 'event_origin', 'source_hash', 'rule_id']], on=['audit_group_id', 'report_id', 'concept_id'], how='left')], ignore_index=True)
manual_context = manual_context.merge(reports[['report_id', 'study_date', 'species', 'breed', 'sex', 'age_text']], on='report_id', how='left', suffixes=('', '_report'))
manual_context['concept_name'] = manual_context.get('concept_name', manual_context.get('canonical_name'))
manual_context = manual_context[[c for c in ctx_cols if c in manual_context.columns]]
manual_context.to_csv(OUT / 'manual_review_sample.csv', index=False)
print('Manual review context rows:', len(manual_context))

