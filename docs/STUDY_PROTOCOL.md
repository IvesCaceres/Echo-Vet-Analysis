# Study protocol and claims register — verification pending

The exact published editorial bundle reports 3,364 Gold report records and 14,245 extraction-event rows. These are snapshot counts, not unique-animal counts or a clinically eligible cohort denominator. Study period, effect estimates, inferential findings and diagnostic conclusions are not approved in this selection.

| Item | Current evidence | Required private verification before a real release |
|---|---|---|
| Unit | Code uses report-level and event-level structures | Define report, examination, animal and event; do not equate them |
| Sample size | Approximate corpus size stated by owner | Exact eligible report counts, exclusions, missingness and analysis-specific N |
| Period | Source code includes temporal analyses | Verify actual dates/coverage privately; do not infer range from filenames or code constants; publish only reviewed granularity |
| Inclusion | Method-lock/specification and eligibility scripts exist | Freeze criteria, study types, species and handling of unavailable variables before estimating |
| Duplicates/repeated observations | Event and report distinction exists | Distinguish duplicate events, duplicate documents, follow-ups and repeated reports per animal. Names alone do not establish identity |
| Variables | Gold concepts, assertion states, demographics and canonical resolution artifacts | Versioned definitions, mapping/rule changes, validation limits and unresolved/ambiguous states |
| Denominators | Denominator-freeze and concept-eligibility code exists | Concept/organ eligibility, reports vs events, subgroup missingness, mutually exclusive vs overlapping categories |
| Uncertainty | Wilson intervals, tests and model calls appear in source | Assumptions, uncertainty interpretation, dependence/clustering and model adequacy |
| Comparisons | Chi-square/Fisher, Logit/GLM and multiple-testing code exists | Prespecified questions, effect sizes, sparse cells, convergence/separation and multiplicity families |
| Selection | Professionally supplied clinical corpus, not a demonstrated population sample | Referral/indication, geographic/service coverage, case mix and time-dependent ascertainment |
| Missing data | Data-quality and demographic readiness analyses exist | Missingness definitions, complete-case vs other strategies and denominators per table |
| Scientific claims | No result values reviewed in this phase | Trace each claim to a private versioned analysis and a reviewed aggregate output |

Prefer wording such as “observed frequency among eligible reports in this corpus.” Population prevalence, incidence, causal effects, clinical validation and generalization beyond the sampled setting need evidence not established here. Repeated reports may violate independence assumptions; a binomial confidence interval or regression call is not proof that those assumptions hold.

Real outcomes must stay associated privately with snapshot identities, canonical resolution versions, query/code versions, parameters, exclusions and scientific decisions. Public metadata should explain the method and limitations without revealing paths, per-record hashes or identifying details.

The code's synthetic demo demonstrates execution only. Its example counts and graphs are never scientific evidence for the real cohort. A future results section should cite only REAL_AGGREGATED releases approved for that exact content.

## Current descriptive snapshot

The approved published editorial bundle establishes 3,364 Gold report records and 14,245 extraction-event rows for this snapshot. These do not establish unique animals, independent episodes, a content-deduplicated cohort or clinical eligibility. The workbench protocol and its unresolved items remain relevant for future scientific analyses. Age, period, diagnostic frequencies and inferential results are not in the approved editorial selection.
