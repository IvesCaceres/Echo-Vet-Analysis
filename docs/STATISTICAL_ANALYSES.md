# Statistical analysis inventory and notebook selection

This inventory reuses the existing project audit and a targeted read-only inspection of analysis code. No clinical database was queried and no existing statistical values were exported. Presence of an analysis in code does not establish its validity, successful execution, or permission to publish its output.

## Reviewed analytical notebooks

| Notebook | Can use private Gold? | Public real-result suitability |
|---|---|---|
| 00_gold_v2_inventory | Designed to use the configured snapshot; real execution not tested in this phase | Code/methods can be public; hashes, schema internals and sampled values are not public scientific results |
| 01_data_quality | Yes by design, pending authorized execution | Completeness summaries are candidates; per-report counts, duplicate evidence and samples must remain private |
| 02_population_demographics | Yes by design, pending authorized execution | Best first source for reviewed counts/distributions; small breed/age/year combinations and precision need review |
| 03_event_consistency_audit | Yes by design, pending authorized execution | Aggregate consistency metrics may be useful; event text, report IDs, evidence and manual-review tables are private |
| 10_reviewed_aggregate_results | No database connector | Public viewer for SYNTHETIC_DEMO or exact-file reviewed REAL_AGGREGATED packages only |

The first four are workbenches, not approved-result notebooks. Their real-mode outputs must never be saved into a public file. The auxiliary viewer defaults to invented examples and can explicitly read the seven-file hash-approved editorial bundle. It has no saved outputs or clinical connector.

## Original analyses worth reviewing for real aggregate publication

| Analysis family | Source evidence | Statistical value | Private dependencies / release conditions |
|---|---|---|---|
| Report-level observed frequencies | clinical_prevalence.py; rebuild_clinical_prevalence.py | Counts, percentages, Wilson intervals and event-versus-report denominators | Gold plus canonical report/concept resolution CSV; distinguish repeated events from distinct reports; mixed exports include private rows |
| Assertion-specific frequencies | assertion_specific_prevalence.py | Present/possible/historical/negative states, overlap and unresolved coverage | Resolution CSV and rule version required; do not pool uncertainty states silently |
| Assertion and co-occurrence profiles | clinical_assertion_analysis.py | Concept frequencies by subgroup and report-level co-occurrence | Gold, resolutions and denominator definitions; rare concept pairs can disclose cases |
| Denominator and metadata freeze | denominator_demographic_freeze.py; statistical_analysis_specification.py | Inclusion/eligibility, missingness and analytical feasibility | Verify frozen metadata and cohort selection privately; not a guarantee of unique animals |
| Primary comparisons | run_primary_inferential_statistics.py | Code calls chi-square, Fisher exact, confidence intervals, odds-ratio intervals, Logit and multiple-testing adjustment | Test choice, small cells, independence, effect sizes and test-family definition require statistical review |
| Multivariable models | run_multivariable_models.py; multivariable_method_lock.py | Code contains Logit/GLM Binomial fits and model specifications | Event counts, sparse categories, convergence, separation, missing data and repeated reports require private diagnostics |
| Targeted sensitivity analyses | run_targeted_sensitivity_analyses.py; targeted_sensitivity_method_lock.py | Robustness to specified analysis choices | Compare the same sample/denominators and trace frozen rules; results may reveal suppressed subgroup information |
| Final synthesis and graphics | build_final_analytical_synthesis.py; original 11b notebook | Combines descriptive, inferential and robustness outputs | Reads multiple existing CSV/manifest inputs; not safe to copy wholesale. Review each table, figure and claim together |

The original file names use “prevalence.” Public interpretation should normally be **observed frequency among eligible reports in this corpus**, unless a defensible population sampling framework and unit of analysis are established. The code is not modified in the original project.

## Priority selection

1. Confirm sample flow, inclusion and eligible report denominators privately.
2. Review coarse demographic distributions and aggregate data-quality summaries.
3. Review common concept frequencies with defined assertion states and denominators.
4. Review group comparisons only after disclosure-safe contingency tables and methodological checks.
5. Review adjusted models and sensitivity results separately; do not publish private diagnostics or fitted values.

The published editorial bundle includes owner-approved descriptive results for 3,364 Gold records and 14,245 event rows. Unique animals, eligible clinical cohorts, period, clinical conclusions, confidence intervals, significance and model coefficients remain unverified or excluded. No inferential or diagnostic release is approved.

## Availability guide for an external reader

| Material | Availability | What an external reader can do |
|---|---|---|
| `analysis/00_gold_v2_inventory.py` through `analysis/03_event_consistency_audit.py` | Public Python workbench exports | Inspect the included calculations; execute with synthetic configuration through the documented notebook route |
| Four corresponding workbench notebooks under `notebooks/` | Public; no saved outputs | Run invented fixtures by default; never save real private outputs into Git |
| `notebooks/10_reviewed_aggregate_results.ipynb` | Public aggregate-only viewer | Inspect invented examples or the fixed reviewed public CSV bundle without a clinical connection |
| `scripts/`, `synthetic/schema.json`, `tests/` | Public | Generate compatible invented examples and inspect configuration/release checks |
| `published/editorial/` | Public approved artifacts | Read descriptive results and verify the seven hashes; editorial reuse terms remain pending |
| Real Gold snapshot, reports, individual derivatives, canonical resolution tables and frozen clinical rule/query versions | Private and not distributed | Required, with authorization and original procedures, for a real-corpus recalculation; not needed for the public demo |

Names in the ?Original analyses worth reviewing? table, including `clinical_prevalence.py`, `rebuild_clinical_prevalence.py`, `assertion_specific_prevalence.py`, `denominator_demographic_freeze.py`, `run_primary_inferential_statistics.py`, `run_multivariable_models.py` and the original `11b` notebook, are **references to the private source project, not downloadable paths in this repository**. They are an inventory of potential future work, not public installation dependencies or verified scientific outputs. Do not try to reconstruct or download private inputs from those names.

For the current descriptive selection, consult the table-level map in METHODS.md. Its prior private procedures and frozen mappings are distinct from the public exploratory workbenches. No new clinical computation is needed to inspect the approved public bundle.
