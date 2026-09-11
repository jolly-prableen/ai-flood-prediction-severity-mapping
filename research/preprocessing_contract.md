# Preprocessing Contract

This is the required order for both training and inference. The same fitted preprocessing artifact must be reused for custom inference.

## Pipeline

`raw input -> column mapping -> type conversion -> unit normalization -> missing-value handling -> feature derivation -> aggregation -> scaling/normalization -> canonical feature ordering -> model input`

## 1. Raw input

Accept only documented source files or a custom CSV mapped to the canonical interface. Preserve source metadata and do not use `uei` as an input feature.

## 2. Column mapping

Map approved source columns or validated aliases to the canonical names in [feature_contract.md](feature_contract.md). Do not fuzzy-match. Ambiguous aliases, duplicate aliases, or unrecognized units are validation errors.

## 3. Type conversion

Parse dates with the documented day-first format only where dates are metadata/reference fields. Convert rainfall, terrain, population, and other approved numeric measurements using strict conversion. Invalid non-null values must fail validation with examples; they must not become missing silently.

## 4. Unit normalization

Convert only from explicitly declared compatible units. Rainfall must be millimetres or have a documented conversion to millimetres. Elevation must be metres or have a documented conversion. Counts and fractions require source metadata. Unknown units block the feature.

## 5. Missing-value handling

Do not convert missing rainfall or environmental values to zero automatically. Preserve missingness and generate coverage/mask indicators only when the model contract includes them. A missing required feature blocks inference; optional missing features follow the trained model's explicit mask/default policy. That policy must be fitted and versioned before use.

## 6. Feature derivation

Derive antecedent rainfall totals, weekly summaries, maxima, static zonal statistics, and the 26-week sequence only from data available by the prediction cutoff. Do not derive features from event outcomes, future rainfall, future district aggregates, or `uei`.

## 7. Aggregation

Use the approved district-boundary version and crosswalk. Rainfall grid-to-district aggregation must document area weighting, edge handling, missing-cell treatment, and CRS. Multiple events in a forecast window remain event metadata; they must not be used to derive predictive features.

## 8. Scaling and normalization

Fit every scaler, encoder, imputation statistic, class vocabulary, and learned normalization parameter on the training portion only. Serialize the fitted preprocessing artifact with the model. Validation, test, and custom inference data must only call `transform`, never `fit` or `fit_transform`.

## 9. Canonical ordering

Reorder the final tensor/feature table exactly according to [canonical_feature_order.json](canonical_feature_order.json). Missing, extra, duplicated, or out-of-order fields must be handled by the validation layer before model invocation.

## 10. Model input

Provide a district-week sequence of 26 historical steps with the model-specific spatial representation. The seven-day horizon is metadata for target/inference alignment, not an input feature. The model must receive the same feature names, units, shapes, masks, and preprocessing version used during training.

## Training versus inference

- **Training:** fit mappings and preprocessing on training data only, transform validation/test with the fitted artifact, then save model plus contract/version.
- **Inference:** adapt -> validate -> apply saved preprocessing transform -> order features -> invoke existing model.
- **Custom retraining:** explicit retrain -> fit preprocessing on the new training portion only -> train -> evaluate -> save a new model/preprocessing bundle.
