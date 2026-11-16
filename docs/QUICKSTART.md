# Public execution quick start

## Three distinct tasks

- **Synthetic demo:** execute the included methods with invented data. The generator creates 120 synthetic report rows and 600 synthetic events; these are fixture sizes, not new clinical statistics. It uses deterministic loops, not an unrecorded random seed.
- **Published aggregate inspection:** verify and display existing approved CSVs. This reads no clinical database and does not recalculate the corpus.
- **Real-corpus recalculation:** requires authorized private inputs, frozen procedures/mappings and scientific review. It is not performed by this guide or CI.

## Prepare an isolated environment and export

Python 3.11+; CI uses Python 3.11. `requirements.txt` pins pandas, NumPy and Matplotlib, not every transitive dependency. Installation needs package-registry access; subsequent demonstrations do not need network services or credentials. No optional Jupyter install is required for the headless runner.

From an empty workspace, clone the public repository and export its tracked tree. **Do not overwrite an existing working directory.** The validator and a test intentionally reject `.git`, so they run on an export. This is not a reason to delete Git from your clone. Keep the virtual environment outside the export.

### PowerShell

```powershell
git clone https://github.com/IvesCaceres/Echo-Vet-Analysis.git echo-code
cd echo-code
python -m venv ../echo-env
../echo-env/Scripts/python -m pip install -r requirements.txt
git archive --format=zip HEAD -o ../echo-public.zip
python -B -m zipfile -e ../echo-public.zip ../echo-public
cd ../echo-public
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:ECHO_MODE = "PUBLIC_DEMO"
$env:ECHO_RESULTS_KIND = "SYNTHETIC_DEMO"
../echo-env/Scripts/python -B -m unittest discover -s tests -v
../echo-env/Scripts/python -B scripts/validate_candidate.py
../echo-env/Scripts/python -B scripts/run_notebook.py notebooks/00_gold_v2_inventory.ipynb
```

### Bash

```bash
git clone https://github.com/IvesCaceres/Echo-Vet-Analysis.git echo-code
cd echo-code
python -m venv ../echo-env
../echo-env/bin/python -m pip install -r requirements.txt
git archive --format=zip HEAD -o ../echo-public.zip
python -B -m zipfile -e ../echo-public.zip ../echo-public
cd ../echo-public
export PYTHONDONTWRITEBYTECODE=1 ECHO_MODE=PUBLIC_DEMO ECHO_RESULTS_KIND=SYNTHETIC_DEMO
../echo-env/bin/python -B -m unittest discover -s tests -v
../echo-env/bin/python -B scripts/validate_candidate.py
../echo-env/bin/python -B scripts/run_notebook.py notebooks/00_gold_v2_inventory.ipynb
```

With dependencies already approved/available, use that Python executable instead. Run all commands from the exported repository root, not from `notebooks/`. Never configure private paths for this walkthrough.

## Expected checks and next inspection

Before running the plotting notebooks in a fresh environment, initialize Matplotlib's font cache once using the same environment's Python executable:

```bash
python -B -c "import matplotlib.pyplot; import matplotlib.font_manager as fm; fm.findfont('DejaVu Sans')"
```

This loads installed plotting dependencies, not clinical data. On a clean Linux system font discovery can start a local process; the restricted notebook runner intentionally blocks that operation. CI therefore initializes the cache before entering the runner. Keep `MPLCONFIGDIR`, if explicitly configured, outside the exported source and use the same setting for initialization and execution. Do not weaken the runner's process/network restrictions.

Tests should end with `Ran 35 tests` and `OK`; the validator prints JSON containing `"status": "PASS"` and `"issues": []`. The inventory runner prints `"status": "PASS"`, `"code_cells": 13`, `"mode": "PUBLIC_DEMO"` and `"outputs_saved_in_notebook": false`. No scientific conclusion follows from PASS.

The runner suppresses cell stdout/stderr, executes sequential code cells and does not persist notebook outputs. Its message confirms completion, not that it displayed tables. Start by inspecting the generator, the notebook source and `published/editorial/tables/species.csv` alongside the results document.

### All synthetic notebooks

Using your environment's Python executable, run the notebooks in this order:

```bash
python -B scripts/run_notebook.py notebooks/00_gold_v2_inventory.ipynb
python -B scripts/run_notebook.py notebooks/01_data_quality.ipynb
python -B scripts/run_notebook.py notebooks/02_population_demographics.ipynb
python -B scripts/run_notebook.py notebooks/03_event_consistency_audit.ipynb
python -B scripts/run_notebook.py notebooks/10_reviewed_aggregate_results.ipynb
```

Keep `ECHO_MODE=PUBLIC_DEMO` and `ECHO_RESULTS_KIND=SYNTHETIC_DEMO`. Each should return PASS. Notebook outputs stay empty. Workbenches may create synthetic CSVs/figures in an external OS temporary directory; the viewer does not save plots. These generated files are **not approved clinical outputs**.

To see the exact generated path and fixture totals without a notebook, run this in a fresh Python process from the export:

```bash
python -B -c "import sys; sys.path.insert(0, 'scripts'); from gold_utils import get_gold_db_path, get_output_root, connect_gold_readonly; p=get_gold_db_path(); c=connect_gold_readonly(p); print('SYNTHETIC_DEMO'); print('fixture:',p); print('outputs:',get_output_root()); print('synthetic report rows:',c.execute('SELECT COUNT(*) FROM gold_reports_v2').fetchone()[0]); print('synthetic event rows:',c.execute('SELECT COUNT(*) FROM gold_clinical_events_v2').fetchone()[0]); c.close()"
```

Expect 120 and 600. Each new process creates its own `echo_synthetic_*` directory; the path printed by this helper is **not the path from an earlier notebook process**. For interactive exploration in an independently installed Jupyter environment, use only PUBLIC_DEMO and inspect `OUTPUT_DIR` or `OUT` in that same kernel. Interactive Jupyter execution is not covered by the headless-runner test. Do not commit generated files or save private outputs.

## Inspect the approved real aggregates

This only reads public files:

```powershell
$env:ECHO_RESULTS_KIND = "REAL_AGGREGATED"
python -B scripts/run_notebook.py notebooks/10_reviewed_aggregate_results.ipynb
```

```bash
ECHO_RESULTS_KIND=REAL_AGGREGATED python -B scripts/run_notebook.py notebooks/10_reviewed_aggregate_results.ipynb
```

The viewer checks the exact seven hashes before reading tables, but the headless runner hides displays. For an observable hash check and public totals:

```bash
python -B -c "from pathlib import Path; import sys; sys.path.insert(0,'scripts'); from editorial_release import approved_editorial_files,load_editorial_tables; p=Path.cwd(); print('PASS: reviewed files',len(approved_editorial_files(p))); t=load_editorial_tables(p); print('public species denominator',t['species'][0]['denominator_records']); print('public species count sum',sum(int(r['count']) for r in t['species']))"
```

Expect `PASS: reviewed files 7`, denominator 3364 and count sum 3364. Inspect the four CSVs, two PNGs and results text under `published/editorial/` directly. This verifies package identity and some consistency; it does not reproduce the private source query or prove anonymity.

## Boundaries

Do not set PRIVATE_ANALYSIS, supply Gold paths, run private analyses or regenerate approved results for these tasks. Private analysis needs explicit external paths, a snapshot hash and separate authorization. The runner blocks common network/process operations, but is not an OS sandbox. Workbench denominator conventions differ from the approved editorial selection; see METHODS.md.

The historical editorial manifest intentionally retains its local-approval fields. The current README and pipeline explain the separate subsequent publication authorization. Do not edit that historical record to make tests pass. Statistical/editorial reuse licensing remains pending under LICENSING.md.
