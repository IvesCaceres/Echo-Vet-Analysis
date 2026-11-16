# Echo-Vet-Analysis

Clinical reports can support useful research, but sharing their underlying records can expose sensitive information. Echo-Vet-Analysis explores how to publish methods and reviewed aggregate knowledge while keeping original veterinary ultrasound reports and individual clinical records private.

This independent open-science project shares Python code, methods, a synthetic demonstration and reviewed descriptive statistics. It is **not a public clinical dataset**. Published results describe the analyzed corpus, not population prevalence, clinical validity or demonstrated impact.

## Why this project

Researchers and veterinary professionals may use the methods to examine data quality, denominators and descriptive reporting. Developers and others working with sensitive datasets may adapt the separation between private analysis, synthetic execution and reviewed public outputs. These are potential uses: adoption, a user community and clinical benefit have not been established.

## What you can reproduce

| Route | Private data needed? | What it demonstrates |
|---|---|---|
| Synthetic demo | No | Execution of included methods on invented fixtures |
| Published aggregate inspection | No | Reading and hash verification of the public editorial bundle |
| Real-corpus recalculation | Yes, authorized access | Recalculation using the private snapshot and the original frozen rules/procedures |

The four workbench notebooks run on synthetic data by default. The fifth is a database-free aggregate viewer. **Synthetic execution does not reproduce the real numerical results.** The public viewer reads existing approved CSVs; it does not recompute them from reports. Public workbench calculations and editorial category/denominator conventions are not interchangeable. See [methods and table provenance](docs/METHODS.md).

## Published descriptive results

The fixed snapshot contains **3,364 Gold report records** and **14,245 extraction-event rows**. Within those records, 2,260 are coded canine (67.2%) and 1,034 feline (30.7%); unresolved and missing species remain in the denominator. Report records are not established unique animals or independent episodes; event rows are not independent diagnoses.

Read the complete [reviewed results and limitations](published/editorial/results.md), [tables and figures](published/README.md), and [current protocol](docs/STUDY_PROTOCOL.md). All seven approved artifacts remain unchanged. Age/time summaries and diagnostic frequencies are excluded.

## Quick start

Target: a roughly five-minute walkthrough **after Python and dependencies are available**; download/install time varies. Python 3.11+ is supported by the pinned direct dependencies; CI uses Python 3.11. An export without Git history is used because the publication validator deliberately rejects `.git`. Keep the virtual environment outside the export.

Prepare an empty working directory, then follow [QUICKSTART](docs/QUICKSTART.md) for environment setup. With approved dependencies available:

**PowerShell**

```powershell
git clone https://github.com/IvesCaceres/Echo-Vet-Analysis.git echo-code
cd echo-code
git archive --format=zip HEAD -o ../echo-public.zip
python -B -m zipfile -e ../echo-public.zip ../echo-public
cd ../echo-public
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:ECHO_MODE = "PUBLIC_DEMO"
$env:ECHO_RESULTS_KIND = "SYNTHETIC_DEMO"
python -B scripts/run_notebook.py notebooks/00_gold_v2_inventory.ipynb
python -B -m unittest discover -s tests -v
python -B scripts/validate_candidate.py
```

**Bash**

```bash
git clone https://github.com/IvesCaceres/Echo-Vet-Analysis.git echo-code
cd echo-code
git archive --format=zip HEAD -o ../echo-public.zip
python -B -m zipfile -e ../echo-public.zip ../echo-public
cd ../echo-public
export PYTHONDONTWRITEBYTECODE=1 ECHO_MODE=PUBLIC_DEMO ECHO_RESULTS_KIND=SYNTHETIC_DEMO
python -B scripts/run_notebook.py notebooks/00_gold_v2_inventory.ipynb
python -B -m unittest discover -s tests -v
python -B scripts/validate_candidate.py
```

Expect notebook JSON with `"status": "PASS"`, tests ending in `OK`, and validator JSON with `"status": "PASS"`. The runner suppresses cell output and does not save notebook outputs. Next inspect [the synthetic generator](scripts/generate_synthetic.py), [public species CSV](published/editorial/tables/species.csv) and [its interpretation](published/editorial/results.md). For visible synthetic summaries, all notebooks, output paths and aggregate inspection, use [QUICKSTART](docs/QUICKSTART.md).

## Privacy and release boundaries

Original reports, RAW/Silver/Gold databases, individual derivatives, clinical text, logs, backups and old Git objects are not distributed. Gold is not assumed anonymous. Private workbench outputs may contain individual information and must stay outside the public checkout.

Aggregate publication requires methodological, disclosure, cross-release and exact-content human review. Small-cell/complement checks and hashes are safeguards, not anonymity guarantees or automatic permission. The preliminary threshold is not a universal policy. See [disclosure policy](docs/DISCLOSURE_POLICY.md), [privacy](docs/PRIVACY.md), [publication pipeline](docs/RESULTS_PIPELINE.md) and [permission provenance](docs/RESULTS_PROVENANCE.md).

## Repository guide

- `notebooks/`: four synthetic/private workbenches and one aggregate-only viewer; no saved outputs.
- `analysis/`: Python exports of the four workbenches.
- `scripts/`: synthetic generation, configuration, runners and publication checks.
- `synthetic/`: compatible schema definitions, no clinical records.
- `published/editorial/`: four reviewed CSVs, two figures and one results document.
- `docs/`: methodology, protocol, governance, execution guide and licensing scope.
- `tests/`: public tests using invented fixtures and failure cases.

[Analysis availability](docs/STATISTICAL_ANALYSES.md) distinguishes public files from private procedures that are not included. The synthetic fixture is deterministic; it is not a statistical model of the real corpus. Direct dependency versions are pinned, but there is no full cross-platform dependency lock. The headless runner is not an operating-system sandbox or a full interactive Jupyter validation.

## License and citation

Original software and its software documentation are [MIT licensed](LICENSE), Copyright (c) 2026 Ives C?ceres. See [CITATION.cff](CITATION.cff) for software citation; use the exact commit you analyzed. No DOI, academic affiliation or peer-reviewed publication is claimed.

**Editorial reuse terms remain pending:** the MIT software license does not automatically license the seven statistical tables, figures and result text. Permission to publish that bundle is documented separately and does not grant access to private inputs. See [licensing scope](docs/LICENSING.md) and [third-party review](docs/THIRD_PARTY_REVIEW.md). Do not infer a new license from this README.
