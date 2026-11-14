# Statistical disclosure review policy — proposal

**The threshold remains preliminary. The owner approved seven exact aggregate artifacts for this local candidate; remote publication remains unauthorized. This is not blanket approval of new outputs or all policy choices.** Aggregation is not anonymity. This policy concerns outputs, not release of anonymized individual datasets.

## Mandatory scope of review

Review the complete intended publication: tables, text containing numbers, figures, notebook outputs, metadata, downloadable files, previous releases and known external/public results. Consider linkage to tutors, professionals, patients and visits even when their direct identifiers are absent.

No row-level data, IDs, hashes per case, source paths, original dates, report text, quotes, case lists, predictions or residuals belong in a public result package. Category labels must come from a reviewed vocabulary/protocol, not arbitrary values discovered in free text.

## Counts, totals and suppression

The demo uses min_count=10 solely to exercise checks. It is not a legal rule, validated privacy threshold, or approved production policy. The responsible reviewers must choose the real thresholds and granularity based on risk and context. Zero/full cells also need review; passing the positive-cell threshold is not clearance.

Check both numerator and complement, eligible denominators, missingness categories, margins, subtotals and overlapping tables. Hiding one count but retaining its total, percentage, CI or sibling counts can reveal it by subtraction.

The initial code takes a conservative approach: if any predeclared table in a package has a positive small cell/complement or small denominator, the entire package is withheld, without numeric result tables, totals or percentages. This protects against within-package reconstruction from those outputs. It is not a general solution to linkage or across-release differencing.

Private reviewers may propose broader categories or a smaller publication scope. Any coarsening, alternative complementary suppression, rounding/noise or redesigned table must be documented and rerun/rechecked privately under authorization. Do not publish different variants merely to work around a failed threshold.

## Across-release disclosure

Maintain a private release ledger with cohort/eligibility definitions, variables, filters, periods, denominator logic, proposed and previously published tables/figures, decisions and exact content hashes. Compare intersections, complements and differences across versions, cohorts and outputs. The public approval manifest records only a reference and exact file hashes; it does not implement this ledger or a reconstruction solver.

If prior releases or external publications are unknown, record the uncertainty and withhold approval until the responsible reviewer resolves or explicitly assesses it. No package is automatically safe because another package passed.

## Descriptive and inferential statistics

- Review supporting N and distribution, not only a published average. Min/max and outlier displays can expose single observations.
- Review quantiles, rounding and precision in context. Do not infer safety from aggregate format.
- P-values, intervals, odds ratios and model coefficients may reveal underlying small cells or sparse groups; keep them in the same review family as the counts.
- No individual scatter, residual/influence plots, case tooltips or rare combinations. Review SVG/HTML/image metadata and embedded data, not just the visible plot.
- Statistical validity and privacy are separate decisions. A safe output may be misleading; a correct estimate may be disclosive.

## Approval record

Each real release requires privacy, methodology, cross-release and owner-content decisions tied to the exact package and each figure/notebook hash. Keep reviewer identities, notes and dataset paths private; expose only a non-identifying review reference. Any data/code/filter/format change invalidates the relevant approval and requires reassessment.

REAL_AGGREGATED means computed on real authorized inputs and cleared for that exact public content. REAL_PENDING_REVIEW stays private. SYNTHETIC_DEMO cannot be relabeled as real. No review record alone authorizes GitHub publication.

## Methodological references

These are general output-checking references, not Chilean legal requirements or a policy imported wholesale:

- ONS discusses keeping a record of released tables and secondary suppression so totals do not disclose hidden cells: https://www.ons.gov.uk/methodology/methodologytopicsandstatisticalconcepts/disclosurecontrol/policyonprotectingconfidentialityintablesofbirthanddeathstatistics
- Government Analysis Function discusses disclosure by differencing across linked tables: https://analysisfunction.civilservice.gov.uk/policy-store/statistical-disclosure-control-for-tables-produced-from-surveys/
