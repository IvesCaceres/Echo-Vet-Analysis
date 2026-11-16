# Controlled aggregate publication pipeline

## Published repository

The preceding private read-only analysis produced aggregate artifacts. The owner confirmed aggregate-publication permission from the responsible veterinarian, approved the seven selected files for local incorporation conditional on exact hashes and satisfactory final review, and subsequently authorized their publication. No new clinical query was executed for incorporation.

The result is the REAL_AGGREGATED editorial bundle under published/editorial/: four CSV tables, two PNG figures and one methodology/results document. All seven are byte-identical to the selected private sources. published/editorial-manifest.json preserves their exact hashes, permission basis and prepublication local-approval scope. Its local-only fields are historical review metadata, not the current publication status. The owner separately authorized publication of this exact bundle; additional outputs still require review and authorization.

editorial_release.py admits only this fixed seven-path layout, with strict predefined CSV fields/labels, shared denominators, proportions, partition sums, small-cell/complement checks and cross-table coverage consistency. The candidate validator rejects unregistered CSV/images and changed approved content. This administrative allowlist is not a signature, consent document or anonymity proof.

The four analytical workbenches still use invented data by default and private external paths only by explicit configuration. The auxiliary viewer reads only reviewed public aggregates in REAL_AGGREGATED mode and invented aggregates in SYNTHETIC_DEMO mode. It cannot access Gold. No outputs are saved in the notebooks.

## Private boundary and future releases

Authorized Gold snapshot plus frozen rules -> private diagnostics and aggregates -> disclosure/methodology/cross-release review -> exact owner content approval -> transfer of only approved artifacts -> offline verification -> separate remote-publication decision.

Original reports, all clinical databases and individual derivatives remain private. Private staging, clinical queries and original rule tables are not publication artifacts. Reuse verified private aggregate results before considering recomputation. Do not copy an entire private checkout or import its Git objects.

Age/time families including linked denominators, diagnostic frequencies and individual records are excluded. New descriptive variables, group comparisons, confidence intervals and model outputs need separate schemas and contextual disclosure review before export. No general exporter for those statistics is provided.

The earlier aggregate_release.py JSON-package prototype remains available for design/tests; published/approved-manifest.json is empty and does not govern the current CSV editorial bundle. Its numerical tests produce pending review, never automatic real approval. No clinical connector or promotion CLI is supplied.

## Structure

- analysis/: reviewed analytical Python exports.
- notebooks/: four workbenches and an auxiliary aggregate-only viewer.
- scripts/: explicit private configuration, synthetic fixtures, review controls and validators.
- synthetic/: schema metadata, no clinical records.
- published/editorial/: exact approved aggregate artifacts only.
- docs/: protocol, limitations, privacy and third-party review.
- tests/: invented fixtures and failure-mode checks.

See DISCLOSURE_POLICY.md and published/editorial/results.md. Passing tests does not establish clinical validity or permission for GitHub publication.

## Reusing the separation on another sensitive corpus

The following is an invented, nonclinical example; it is not a description or statistic of the veterinary corpus and creates no new approved artifact.

1. **Conceptual private dataset:** an authorized organization holds 40 fictional maintenance tickets with internal ticket IDs and free-text notes. Both stay private. Define the unit as one ticket, not a person or repair event.
2. **Private extraction:** map each ticket into a reviewed category vocabulary, `ROUTINE` or `FOLLOW_UP`. Record unresolved/missing cases separately if they occur. Freeze definitions and provenance privately before aggregation.
3. **Private aggregation:** the fictional counts are 24 ROUTINE and 16 FOLLOW_UP, with denominator 40. Only category code, count, denominator and rounded percentage enter the proposed aggregate stage. IDs and free text never enter a public package.
4. **Publication control:** validate the predefined schema and partitions; inspect small cells and complements, linked tables and known prior releases. A preliminary numerical threshold alone cannot approve disclosure. A methodology/privacy reviewer and the owner decide on the exact content. For contrast, changing the invented counts to 39 and 1 would fail the small-cell/complement screen and withhold the entire package, including totals and percentages; a hidden cell could otherwise be reconstructed.
5. **Potential public artifact:** only after separate approval, publish a two-row aggregate table, methods/limits and exact hashes. Publish a separate synthetic fixture for executable demonstrations; never relabel it as real evidence.

This example illustrates a reusable boundary, not a general-purpose anonymization algorithm. `aggregate_release.py` is a generic JSON-package prototype with synthetic tests; it does not locate clinical data or automatically approve publication. The fixed seven-file CSV editorial bundle uses a different exact-file allowlist. Adapt schema, units, approval responsibilities and cross-release review to the new context; do not copy the existing approval manifest or assume its thresholds fit another corpus.
