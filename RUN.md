# AI-Based Flood Prediction — How to Run

All commands run from this folder (`flood_ai_project/`) using the virtualenv at `..\.venv`.

## 1. One-time setup (install dependencies)

```powershell
cd "P:\ai tech-a-thon"
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r flood_ai_project\requirements.txt
```

> `torch` installs the CPU-only wheel. No GPU needed.

## 2. What is completed and runnable

**Task:** District-level flooded-area **regression** (target `Corrected_Percent_Flooded_Area`, features `Population`, `Parmanent_Water`).

Trained models (checkpoints in `results/models/`):
- `CNN + LSTM`        -> `results/models/cnn_lstm/best_model.pt`
- `CNN + Transformer` -> `results/models/cnn_transformer/best_model.pt`
- `ResNet + BiLSTM`   -> `results/models/resnet_bilstm/best_model.pt`
- `Linear Regression` and `Random Forest Regressor` baselines (`.pkl`)

Not trained: `U-Net + ConvLSTM`, `Attention U-Net + LSTM` (need spatial/raster segmentation data that is not in this workspace).

## 3. Run the dashboard (recommended)

```powershell
cd "P:\ai tech-a-thon\flood_ai_project"
& "..\.venv\Scripts\python" -m streamlit run app\app.py
```

- Primary app: the restored original Member 3 dashboard ("AI Flood Early Warning Dashboard").
  Unsupported sections (probability KPIs, GIS map, retraining) are labeled Unavailable and
  never show fabricated values; the Execution Engine runs real Member 2 checkpoint inference.

Upload a CSV with `Population` and `Parmanent_Water` columns (see `data/raw/sample_test_input.csv`).

## 4. Run inference from Python

```powershell
$env:PYTHONPATH = "."
& "..\.venv\Scripts\python" -c "from src.inference.predictor import predict_uploaded_dataset; print(predict_uploaded_dataset('ResNet + BiLSTM', {'Population':[1500000], 'Parmanent_Water':[0.8]}))"
```

## 5. Retrain the regression models

```powershell
$env:PYTHONPATH = "."
& "..\.venv\Scripts\python" -m src.training.train_real_regression --csv data/processed/district_flood_area_regression.csv --split data/splits/district_flood_area_split.json --epochs 30 --batch-size 32
```

Outputs go to `results/` (model checkpoints, `model_comparison.csv`, 10-fold CV `cv_regression_results.csv`, training curves in `results/plots/`).

## 6. Data pipeline scripts (Member 1)

From `integration/member1-data` these were merged here; `ROOT` resolves automatically:

```powershell
$env:PYTHONPATH = "."
& "..\.venv\Scripts\python" src\preprocessing\clean_ifi.py
& "..\.venv\Scripts\python" src\leakage\audit_ifi.py
```

Raw IFI data: `data/raw/` (canonical), original Zenodo copies kept in `data/raw/original_IFIv3_zenodo/`.