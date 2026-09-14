# Member 3 model integration

## Current training status

The official IFI-Impacts v3 files are present under `data/raw/`. The real-data preparation and regression experiment have completed.

## Prepared real-data task

- Task: district-level regression.
- Target: `Corrected_Percent_Flooded_Area`.
- Features: `Population`, `Parmanent_Water`, in that order.
- Prepared rows: 720.
- Input shape for tabular sequence models: `(batch, sequence_length=1, features=2)`.
- Dataset: `data/processed/district_flood_area_regression.csv`.
- Schema: `data/processed/district_flood_area_schema.json`.
- Split: `data/splits/district_flood_area_split.json`.
- Audit: `results/data_audit.json`.

The six district names duplicated in both district files (`aurangabad`, `balrampur`, `bilaspur`, `hamirpur`, `pratapgarh`, `raigarh`) were excluded rather than many-to-many joined. No missing target or feature values were filled. The main inventory was not joined to these aggregates because the district files have no LGD key and inventory district values can contain multiple districts.

Rejected as predictors for this first task: `Human_fatality`, `Human_injured`, `Human Displaced`, `Animal Fatality`, `Extent of damage `, `Mean_Flood_Duration`, `Percent_Flooded_Area`, `Severity`, and `Area Affected`; these are post-event outcomes, direct target leakage, entirely missing, or unsuitable text fields. The inventory contains flood events only, so flood occurrence classification is not currently a valid task.

- `U-Net + ConvLSTM`: pending genuine spatial tensors and segmentation masks.
- `CNN + LSTM`: trained regression model; checkpoint `results/models/cnn_lstm/best_model.pt`; test MAE 2.433762, RMSE 3.376278, R2 0.074452; UNDERFITTING.
- `CNN + Transformer`: trained regression model; checkpoint `results/models/cnn_transformer/best_model.pt`; test MAE 2.427292, RMSE 3.454255, R2 0.031206; UNDERFITTING.
- `ResNet + BiLSTM`: trained regression model; checkpoint `results/models/resnet_bilstm/best_model.pt`; test MAE 2.296399, RMSE 3.359883, R2 0.083419; UNDERFITTING.
- `Attention U-Net + LSTM`: pending genuine spatial tensors and segmentation masks.

The final test set was the untouched 109-row partition from `data/splits/district_flood_area_split.json`. Scaling was fitted only on the 503 training rows. No correction was triggered because no model met the overfitting criterion.

## Imports

```python
from src.models.model_registry import MODEL_REGISTRY
from src.inference.predictor import predict_uploaded_dataset, load_model
```

## Tabular/sequential models

`CNN + LSTM`, `CNN + Transformer`, and `ResNet + BiLSTM` expect a float tensor shaped `(batch, sequence_length, features)`. The trained regression schema uses sequence length 1 and features ordered as `Population`, `Parmanent_Water`.

## Spatial models

`U-Net + ConvLSTM` and `Attention U-Net + LSTM` expect `(batch, time, channels, height, width)` and return spatial logits/probabilities shaped `(batch, classes, height, width)`. IFI event/district CSV data does not provide genuine pixel labels in this workspace, so no segmentation IoU/Dice result is reported.

## Checkpoints and outputs

`Trainer.fit(..., checkpoint_path="results/models/<name>/best_model.pt")` saves model weights, history, and metadata. Metrics can be loaded with `load_metrics()` from `results/model_comparison.csv`; prediction tables belong in `results/model_predictions.csv` or `results/predictions/` as selected by the calling workflow. Learning curves belong in `results/plots/`.

For the trained regression models, use `predict_uploaded_dataset`. It loads the checkpoint, feature schema, and fitted preprocessing artifact without fitting during inference:

```python
prediction = predict_uploaded_dataset(
    model_name="ResNet + BiLSTM",
    uploaded_data={"Population": [1500000], "Parmanent_Water": [0.8]},
)
```

The returned dictionary contains `status`, `task`, `model`, `prediction`, `metrics`, and `warnings`. Missing required features return `INCOMPATIBLE`. Severity, area, and segmentation fields are not invented beyond the trained flooded-area regression target.

## Best model

Select the best model from the common-task rows in `results/model_comparison.csv`, using the metric appropriate to that task. Do not compare spatial segmentation rows with tabular classification rows as if they were equivalent.

## Experiment artifacts

The measured comparison is saved in `results/model_comparison.csv`; 10-fold regression CV results are in `results/cv_regression_results.csv`; the run summary is `results/training_summary.json`. Each trained hybrid directory contains `best_model.pt`, `model_config.json`, `feature_schema.json`, `preprocessing.pkl`, `metrics.json`, and `training_history.json`. Baselines are saved as `best_model.pkl` with matching schemas and preprocessing artifacts.

## Next training command

From `flood_ai_project/`:

```powershell
$env:PYTHONPATH='.'
python -m src.training.train_real_regression --csv data/processed/district_flood_area_regression.csv --split data/splits/district_flood_area_split.json --epochs 30 --batch-size 32
```

This command reruns the real regression experiment. It does not train either U-Net model.
