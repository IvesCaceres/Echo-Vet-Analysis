# Privacy boundaries

Original clinical reports, populated clinical databases, individual records, private case adjudications, logs and inherited Git objects are excluded. Gold is not assumed anonymous.

The seven artifacts under published/editorial/ contain exact hash-reviewed aggregate tables, figures and methodology text. The owner specifically authorized their local incorporation and subsequent publication, and confirmed the responsible veterinarian permits derived aggregate statistics. These authorizations do not cover additional outputs or independently establish all third-party rights.

PUBLIC_DEMO uses invented data only. The auxiliary viewer defaults to SYNTHETIC_DEMO; its explicit REAL_AGGREGATED mode reads only the hash-reviewed aggregate CSVs, never a clinical database. PRIVATE_ANALYSIS can produce individual outputs and must use external private output storage; do not save its outputs here.

The defensive .gitignore blocks clinical data formats and permits only the four exact editorial CSV paths and reviewed figure paths. The validator additionally checks hashes, predefined CSV labels, schemas, denominators and numerical consistency. No arbitrary CSV or image is admitted. This administrative allowlist is not a cryptographic approval system or anonymity proof.

Age/time families and their linked denominators, diagnostic frequencies, rare cross-tabulations, original category values, case lists and individual plots are not included in the editorial release. Species and sex margins and syntactic field-presence coverage are reviewed together. Small-cell/complement checks, including the preliminary threshold 10, cannot eliminate historical linkage risks or guarantee anonymity.

See DISCLOSURE_POLICY.md and published/editorial/results.md for risks and scientific limits. Changes to any approved artifact invalidate its hash and require exact-content review. Never copy a private checkout wholesale, import its Git history, or treat .gitignore as retrospective removal of tracked history.
