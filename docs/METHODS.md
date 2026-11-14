# Methods and reproducibility boundaries

The reviewed analysis subset inventories a Gold-style relational schema, profiles missingness and relationships, summarizes demographic variables, and examines consistency between events and provenance. It retains the analytical code of four source notebooks with configuration adapted to explicit data and output boundaries.

The compatible schema contains reports, events, concepts, aliases, taxonomy, provenance and build metadata. These are schema definitions only, not records. The synthetic generator invents reports and event combinations, including duplicates and differing assertion statuses, to exercise analysis paths. Dates, example names and descriptions it generates are fictional demonstration values.

## Changes made

1. All source notebook outputs, execution counts, attachments and metadata were excluded.
2. Original narrative Markdown and comments were omitted to avoid carrying scientific findings or case notes into a public demonstration.
3. Code-root lookup replaces discovery of clinical databases in ancestor directories.
4. Output paths are selected by mode outside the checkout; SQL/calculations in the included notebooks otherwise retain their source logic.
5. Private fixed snapshot hashes and canonical-resolution CSV pins were not copied. The database helper now validates explicitly configured snapshots.
6. A headless display fallback supports offline tests without installing Jupyter.

This repository does not include private resolution tables or promotion/repair workflows. Their exclusion is a scope limitation, not a claim that they are scientifically unnecessary. No clinical conclusion has been invented, validated or recomputed from the real corpus in this preparation.

For private reproducibility, preserve the original snapshots, code, query parameters, rule versions, outputs and scientific decisions in approved private storage. Compare results against that private baseline before using adapted code scientifically. A passing synthetic test only establishes execution and software properties for the invented fixtures.

## Reviewed real aggregate publication

This repository includes the exact seven-file editorial aggregate bundle, approved by the owner after the stated review and published under a separate explicit authorization. The original four notebooks remain private-output workbenches; the fifth notebook is a database-free reviewed-results viewer. See DISCLOSURE_POLICY.md and RESULTS_PIPELINE.md. Saved public figures/notebooks require exact-file hash approval; stripping outputs is the default, not permission to publish unreviewed aggregates. Synthetic demonstrations remain labeled SYNTHETIC_DEMO.

## Current exact editorial bundle

The seven files under published/editorial/ now reproduce only the owner-approved aggregate selection, with no new clinical query. The four workbench methods remain distinct from these fixed results. The auxiliary fifth viewer was adapted to read this exact hash-reviewed bundle or invented examples; it has no clinical connector. See published/editorial/results.md for the current final descriptive methods and limits. The generic JSON-package prototype remains separate from the exact CSV editorial bundle.
