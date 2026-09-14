# Final Member 2 Report

## 1. Member 2 scope

This package covers AI model implementation, training, evaluation, error analysis, controlled hyperparameter testing, checkpoints, and inference for the existing Member 2 baseline. Member 1 data acquisition/research and Member 3 dashboard/GIS work are outside this package.

## 2. Dataset used

The existing prepared dataset is `data/processed/district_flood_area_regression.csv` with 720 rows. The split is stored in `data/splits/district_flood_area_split.json` with 503 training rows, 108 validation rows, and 109 untouched test rows.

## 3. Prediction target

`Corrected_Percent_Flooded_Area`.

## 4. Input features

Only these two features are used:

- `Population`
- `Parmanent_Water`

The model input shape is `[N, 1, 2]`.

This is a limited district flooded-area regression baseline. It is not a complete flood forecasting system.

## 5. Data preprocessing

The existing preprocessing fits `StandardScaler` on the training partition only and applies the saved transform to validation, test, and inference data. Feature ordering is preserved. No rainfall, DEM, satellite, river, land-cover, or synthetic feature was used.

## 6. Leakage prevention

Post-event impact fields, target-derived fields, identifiers, and unsupported environmental fields were excluded from the baseline feature contract. The protected test partition was not used for baseline model selection. The controlled experiment selected configurations using validation MAE only.

## 7. Train/validation/test methodology

The existing fixed split was preserved:

- Train: 503
- Validation: 108
- Test: 109

The controlled experiment did not modify this split.

## 8. 10-fold cross-validation

Existing fold-local regression CV results are stored in `results/cv_regression_results.csv`. The CV artifact contains 10 folds. It is included as evaluation evidence and did not overwrite protected checkpoints.

## 9. Model architectures

### 9.1 CNN + LSTM

Implemented and trained as a regression model with a CNN feature extractor, LSTM temporal block, and continuous-value output head. Protected baseline checkpoint: `results/models/cnn_lstm/best_model.pt`.

### 9.2 CNN + Transformer

Implemented and trained as a regression model with CNN extraction, positional encoding, Transformer encoder, and continuous-value output head. Protected baseline checkpoint: `results/models/cnn_transformer/best_model.pt`.

### 9.3 ResNet + BiLSTM

Implemented and trained as a lightweight custom residual feature extractor followed by bidirectional LSTM and continuous-value output head. Protected baseline checkpoint: `results/models/resnet_bilstm/best_model.pt`.

### 9.4 U-Net + ConvLSTM

Implemented, but **NOT TRAINED — DATA REQUIREMENT BLOCKER**. Valid raster/image sequences with corresponding flood masks were unavailable.

### 9.5 Attention U-Net + LSTM

Implemented, but **NOT TRAINED — DATA REQUIREMENT BLOCKER**. Valid raster/image sequences with corresponding flood masks were unavailable.

## 10. Classical baselines

The existing Linear Regression and Random Forest Regressor were evaluated on the same baseline task and test partition.

## 11. Training methodology

The baseline used lightweight PyTorch models, AdamW optimization, MSE regression loss, saved train-only preprocessing, early stopping, and a validation-driven scheduler. No protected checkpoint was changed during packaging or later analysis.

## 12. Underfitting/overfitting analysis

The original three neural models were diagnosed as UNDERFITTING. A controlled experiment tested a control configuration and a capacity/low-regularization configuration for each architecture. Underfitting remained for all selected configurations. No selected configuration was diagnosed as overfitting.

## 13. Hyperparameter experiment

The controlled experiment is in `results/experiments/underfitting_correction/`.

The selected configurations were:

- CNN + LSTM: hidden dimension 64, dropout 0.1, two layers, learning rate 0.0005, weight decay 0.00001.
- CNN + Transformer: hidden dimension 64 as embedding dimension, dropout 0.1, two layers, learning rate 0.0005, weight decay 0.00001.
- ResNet + BiLSTM: control configuration, hidden dimension 32, dropout 0.2, one layer, learning rate 0.001, weight decay 0.0001.

Selection used validation MAE only.

## 14. Final test evaluation

The selected configurations were evaluated once on the untouched 109-row test set:

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| CNN + LSTM | 2.410747 | 3.375897 | 0.074661 |
| CNN + Transformer | 2.373542 | 3.468193 | 0.023372 |
| ResNet + BiLSTM | 2.291087 | 3.348981 | 0.089357 |

Additional MSE, bias, median absolute error, and maximum absolute error are stored in `final_test_comparison.csv`.

## 15. Error analysis

The existing error analysis used all 109 test rows and is stored under `results/evaluation/`.

High actual flooded-area cases have larger errors across the models. For example, the highest actual value in the test set was approximately 17.34, and it generated the largest errors across several models. Most predictions were overpredictions by count, but ResNet + BiLSTM had a slightly negative mean bias because a large high-value case was underpredicted.

The largest absolute error was approximately 16.526 from Random Forest Regressor. ResNet + BiLSTM had the strongest protected-baseline error profile among the neural models.

## 16. Feature sensitivity

Repeated permutation sensitivity was calculated on the test set. It reports the increase in MAE after shuffling one feature. It is **not SHAP** and **not causal feature importance**. Results are in `results/evaluation/permutation_sensitivity.csv`.

## 17. Model comparison

Protected baseline test results:

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| CNN + LSTM | 2.433762 | 3.376278 | 0.074452 |
| CNN + Transformer | 2.427292 | 3.454255 | 0.031206 |
| ResNet + BiLSTM | 2.296399 | 3.359883 | 0.083419 |
| Linear Regression | 2.567885 | 3.585889 | -0.044038 |
| Random Forest Regressor | 2.416081 | 3.534304 | -0.014216 |

Tuned conclusion:

- CNN + LSTM: small improvement across MAE, RMSE, and R².
- CNN + Transformer: MAE improved, but RMSE and R² degraded. The protected baseline remains preferable for this architecture.
- ResNet + BiLSTM: slight improvement across all three metrics.

## 18. Inference pipeline

The existing inference API is:

```python
from src.inference.predictor import predict_uploaded_dataset

result = predict_uploaded_dataset(
    model_name="ResNet + BiLSTM",
    uploaded_data={"Population": [1500000], "Parmanent_Water": [0.8]},
)
```

It loads the actual `.pt` checkpoint, saved preprocessing artifact, feature schema, and model configuration. It does not fit preprocessing during inference and returns continuous regression predictions.

## 19. U-Net limitation

Both U-Net architectures are implemented but not trained. A legitimate public segmentation dataset may provide images and masks without providing repeated temporal sequences. The reviewed candidates did not satisfy the genuine temporal requirement, so no data was downloaded and no temporal dimension was fabricated.

## 20. Current best model

The current best trained Member 2 model is **ResNet + BiLSTM** from the controlled experiment:

- MAE: `2.291087`
- RMSE: `3.348981`
- R²: `0.089357`

The improvement over the protected baseline is modest, and predictive power remains limited.

## 21. Limitations

The current experiment uses only two district-level predictors. It does not use rainfall, DEM, satellite time series, river data, land cover, or a district-week temporal observation frame. Errors increase for larger flooded-area values. Underfitting remains. See `member2_limitations.md` for the complete limitation list.

## 22. Reproducibility

The original baseline artifacts, evaluation commands, controlled experiment command, model paths, preprocessing paths, and output locations are documented in `member2_reproducibility.md`.

## 23. Future richer dataset dependency

A future approved richer dataset may support rainfall, temporal history, spatial geometry, and additional environmental variables. That would be a separate experiment. It must not replace or overwrite this baseline package or its checkpoints.
