# Study protocol and claims register

## Published descriptive results

The approved editorial selection describes a fixed snapshot of **3,364 Gold report records**, with 3,364 distinct report keys, and **14,245 extraction-event rows**. It contains species and sex distributions and nonblank coverage of five fields. Both distributions and each field-coverage calculation use all 3,364 Gold records; categories and rounding are documented in [the exact results](../published/editorial/results.md).

These are snapshot counts, not unique animals, independent episodes, a deduplicated cohort or a clinically eligible study population. No records were corrected or deduplicated for this selection. The period, age/time summaries, diagnostic frequencies and inferential findings are not included or approved here.

| Item | Evidence for the published selection | Remaining limit |
|---|---|---|
| Unit | Gold report record and extraction-event row, separately counted | Unique animals and independent examinations/episodes are not established |
| Sample size | Exactly 3,364 records in the descriptive snapshot | This is not an eligible denominator for every future question |
| Species and sex | Predefined coding with case/whitespace normalization; unresolved/missing/non-specified categories retained | Coding is not clinical validation; no imputation into confirmed categories |
| Coverage | Non-null/nonblank presence of species, sex, breed, study type and outcome | Marginal syntactic presence is not joint completeness, correctness or a validated outcome |
| Selection | Professionally supplied clinical corpus | Population sampling frame, referral patterns and representativeness remain unverified |
| Duplication | Distinct report keys within the snapshot | Content duplicates, repeat animals and follow-up episodes may remain |
| Permission and review | Owner-confirmed aggregate-only permission; seven exact-file approvals and separate publication authorization | Not blanket permission or independent verification of every right; see RESULTS_PROVENANCE.md |

## Future / not-yet-approved analyses

| Question or analysis | Required verification before any new real output |
|---|---|
| Study period and age summaries | Verify dates, coverage, parsing and safe publication granularity privately; do not infer dates from filenames |
| Clinical inclusion/exclusion | Freeze study types, eligibility and analysis-specific N before estimation |
| Diagnostic/concept frequencies | Freeze canonical mappings, assertion states, unresolved coverage and report-versus-event denominators |
| Group comparisons | Review independence, repeated reports, sparse cells, effect sizes and multiplicity |
| Uncertainty intervals | Establish appropriate sampling/dependence assumptions; a Wilson interval alone does not justify generalization |
| Multivariable/sensitivity analyses | Review missingness, clustering, convergence, separation, robustness and disclosure jointly |
| Additional public tables/figures | Review linked margins, complements, known prior disclosures, exact files and residual risk; obtain separate approval |

The private procedures mentioned in earlier inventories are not supplied or executed by this public repository. Their presence in an inventory does not demonstrate validity or successful execution. [STATISTICAL_ANALYSES.md](STATISTICAL_ANALYSES.md) identifies availability.

## Interpretation and traceability

Prefer ?observed frequency among records in this corpus.? Population prevalence, incidence, causal effects, diagnostic accuracy and clinical validation are not established. Keep original snapshot identities, rules, queries, parameters, exclusions, outputs and decisions in authorized private storage. Public documentation must not reveal per-record hashes, paths or identifiers.

Synthetic fixtures demonstrate software execution only. They do not reproduce the real snapshot's statistics or supply evidence about a clinical population.

## Historical status note

Earlier versions of this register described an approximate owner-stated corpus size and said that no result values had been reviewed ?in this phase.? Those statements recorded a pre-editorial planning stage. They do not describe the current seven-file published selection. The original wording remains in Git history; this update changes current documentation, not the historical approval record or any approved artifact. All unapproved future analyses remain pending.
