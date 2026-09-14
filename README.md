# AI Flood Prediction & Severity Mapping

Complete working project consolidating the work of three team members:

- **Member 1 — Data + Research**: IFI datasets, district crosswalks, LGD boundary matching,
  leakage audits, feature/preprocessing/target contracts, and documented methodology under
  `data/` and `research/`.
- **Member 2 — AI Models + Evaluation**: trained CNN + LSTM, CNN + Transformer, and
  ResNet + BiLSTM regression checkpoints (`results/models/`), evaluation metrics
  (`results/evaluation/`, `results/model_comparison.csv`), dataset splits, and inference code.
- **Member 3 — Dashboard + Integration**: Streamlit dashboard (`app/app.py`), backend API
  (`src/backend_api.py`), dataset registry and selector (`src/datasets/registry.py`),
  GIS scaffolding (`src/gis/`, `maps/`), and the API-driven execution engine.

## Quick start

```bash
python -m pip install -r requirements.txt
streamlit run app/app.py
```

The dashboard's Dataset selector exposes all registered datasets (IFI v3 / M2 Baseline,
District Flood Impact, District Flooded Area, and the mwBTFreddy sample subset), and the
Model selector lists all five architectures with their real training status.

See `RUN.md` and `M3_DASHBOARD_RECOVERY_PLAN.md` for operational details.

## Project layout

```
app/          Streamlit dashboard (View 1 analytics / View 2 execution engine)
configs/      Configuration files
src/          Source code: datasets, preprocessing, training, models, inference,
              evaluation, leakage, gis, visualization, utils, experiments
data/         Raw, processed, derived, external and split datasets
research/     Member 1 methodology, contracts, audits and handoff documents
results/      Trained models, evaluation, metrics, predictions, plots, reports
maps/         GIS map outputs
validation/   Automated dashboard validation suite (AppTest)
```

## Local-only large artifacts

The following files exceed GitHub's 100 MB per-file limit and are **kept locally only**
(gitignored). They are not deleted, only excluded from the repository:

- `data/raw/custom_flood_datasets/mwBTFreddy_v1.0_full.zip` (161 MB) — full mwBTFreddy
  archive. The dashboard uses the sample subset under
  `data/raw/custom_flood_datasets/mwBTFreddy/`, which **is** committed.
- `results/archive/legacy_remote_checkpoints/` — legacy prototype checkpoint pickles
  preserved locally for reference; the current M2 checkpoints are in `results/models/`.

## Tests

```bash
python validation/test_dashboard.py      # streamlit AppTest suite (9 checks)
python app/test_model_comparison.py      # standalone model-comparison smoke test
```