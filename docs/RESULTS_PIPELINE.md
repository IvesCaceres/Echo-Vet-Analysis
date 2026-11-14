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
