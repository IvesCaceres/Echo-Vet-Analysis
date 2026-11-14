# Descriptive statistics of the Gold corpus

## Scope and methods

This descriptive analysis concerns a fixed private Gold database snapshot, comprising 3,364 Gold report records and 14,245 extraction-event rows. There are 3,364 distinct report keys. Report records, animals, clinical episodes and extraction events are different units: neither unique animals nor independent episodes have been established. Content-level duplication has not been ruled out. No records were corrected or deduplicated for this analysis.

The database was queried read-only during the preceding analysis; this editorial selection reuses its verified aggregate artifacts without querying the clinical database again. Species and sex mappings used predefined labels with case and whitespace normalization. The full corpus of 3,364 records is the denominator for both distributions, including missing and unresolved codes. Percentages are rounded to one decimal place and may not sum exactly to 100%.

## Results

Species coding mapped 2,260 records to canine (67.2%) and 1,034 to feline (30.7%). A further 59 records had unresolved species coding (1.8%); these are not asserted to represent other confirmed species. Species was null or blank in 11 records (0.3%).

Sex coding mapped 1,410 records to male (41.9%) and 1,914 to female (56.9%). The remaining 40 records (1.2%) matched predefined codes indicating non-specified information and are labeled **Not specified** (Spanish: **No especificado**). None was reassigned to male or female. No null or blank sex values were observed; a nonblank code does not necessarily specify sex.

The event total is a count of extraction-event rows, not a number of independent diagnoses, animals or disease-positive reports. No diagnostic frequencies are included.

## Field coverage

The coverage table reports only whether a field is non-null and nonblank: species, 3,353/3,364 (99.7%); sex, 3,364/3,364 (100.0%); breed, 3,203/3,364 (95.2%); study type, 3,364/3,364 (100.0%); and outcome, 3,364/3,364 (100.0%). This is syntactic field presence, not clinical completeness, correctness, informative content or validation of an outcome. In particular, non-specified sex codes count as nonblank. These are separate marginal summaries, not the number of records complete across all fields.

## Limitations and data protection

These are observed frequencies in a selected corpus with an unverified population sampling frame. They must not be interpreted as population prevalence, causal effects, diagnostic accuracy or clinical validation. Repeated animals or episodes, content-level duplicates, selection/referral patterns, missingness and extraction errors may affect interpretation. The unresolved species labels remain explicitly unresolved.

No individual records, names, report text, original documents or clinical databases accompany these results. Age, temporal summaries, their linked denominators, and diagnostic frequencies are outside this release proposal. The species and sex tables are separate margins; no joint subgroups or case-level plots are supplied. The preliminary disclosure screen checked positive cell counts and complements against 10; this is not an anonymity guarantee. Historical exposures or external copies cannot be ruled out. Publication requires separate, exact-content human approval following the documented residual-risk assessment.
