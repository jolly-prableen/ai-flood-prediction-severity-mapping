# Member 2 Reproducibility

## Environment

The completed runs used the existing project Python environment with PyTorch, NumPy, pandas, scikit-learn, and Matplotlib available. The exact interpreter can vary by machine; dependency imports were validated during execution.

## Baseline data and split

```text
data/processed/district_flood_area_regression.csv
data/splits/district_flood_area_split.json
```

Contract:

```text
Features: Population, Parmanent_Water
Target: Corrected_Percent_Flooded_Area
Input: [N, 1, 2]
Split: 503 train / 108 validation / 109 test
```

## Protected model artifacts

```text
results/models/cnn_lstm/
results/models/cnn_transformer/
results/models/resnet_bilstm/
```

Each contains the checkpoint, model configuration, feature schema, preprocessing artifact, metrics, and training history.

## Existing inference

The existing inference path is:

```python
from src.inference.predictor import predict_uploaded_dataset

result = predict_uploaded_dataset(
    model_name="ResNet + BiLSTM",
    uploaded_data={"Population": [1500000], "Parmanent_Water": [0.8]},
)
```

The inference path loads the real `.pt` checkpoint, saved `preprocessing.pkl`, schema, and model metadata. It performs no fitting.

## Existing evaluation

The dedicated error-analysis command was:

```powershell
$env:PYTHONPATH='.'
python -m src.evaluation.member2_error_analysis --project-root .
```

Outputs are under `results/evaluation/`.

## Controlled underfitting experiment

The controlled experiment command was:

```powershell
$env:PYTHONPATH='.'
python -m src.experiments.member2_underfitting_correction --project-root . --device cpu
```

All experiment checkpoints were isolated under:

```text
results/experiments/underfitting_correction/checkpoints/
```

The protected `results/models/` checkpoints were not used as output paths.

## Cross-validation

Existing 10-fold regression results are in:

```text
results/cv_regression_results.csv
```

## Final package

This package consolidates existing artifacts only. It does not contain replacement checkpoints and does not retrain models.
