# Custom Dataset Inference Contract

## Purpose

Custom prediction uses an already-trained model. It does not retrain or refit preprocessing.

`adapt -> validate -> same saved preprocessing transform -> canonical feature ordering -> existing model`

Custom retraining is a separate workflow:

`explicit retrain -> preprocess using training-only fits -> train -> evaluate -> save model and preprocessing bundle`

## Required canonical features

The current canonical order is defined in [canonical_feature_order.json](canonical_feature_order.json):

1. `rainfall_total_mm_7d`
2. `rainfall_total_mm_26w`
3. `rainfall_max_daily_mm_7d`
4. `district_static_geometry`
5. `elevation_m`
6. `land_cover_fraction`
7. `hydrology_static_or_recent`
8. `population_baseline`

All are currently `REQUIRES_EXTERNAL_DATA` or require source-vintage verification. A model cannot be trained or used until its actual required subset and shapes are fixed.

## Accepted aliases and units

Only aliases explicitly approved by the feature contract may be accepted. For rainfall, the defensible semantic aliases are `rainfall`, `rainfall_mm`, `precipitation`, `precipitation_mm`, and `rain`, but only when metadata confirms they represent rainfall depth. No alias establishes units by itself. Units must be declared and compatible with the contract.

No unverified aliases are approved for geometry, DEM, LULC, hydrology, or population.

## Types and derivation

- Rainfall: numeric daily values or an already documented canonical weekly feature; convert to millimetres only with an explicit unit conversion.
- Geometry: valid district geometry or a verified district key mapped to the trained spatial representation.
- DEM: numeric metres or documented compatible conversion.
- LULC: fixed class schema and numeric fractions/grid values.
- Hydrology: source-defined numeric/time-series representation with cutoff-safe timestamps.
- Population: numeric persons with a verified vintage preceding the prediction cutoff.

Legitimate derivations include rainfall rolling/weekly summaries and district zonal aggregation, but only from cutoff-safe source records and the same boundary/CRS rules used in training. Target or post-event fields are never derivable predictive inputs.

## Validation rules

1. Required canonical fields must be present after alias mapping.
2. Each canonical field must map to at most one input column.
3. Duplicate or ambiguous aliases fail validation.
4. Declared units must be compatible and convertible without guessing.
5. Numeric values must parse strictly; invalid non-null values fail.
6. Dates must be parseable and must support the 26-week history and seven-day horizon.
7. District identifiers must resolve through the versioned boundary/crosswalk.
8. No input timestamp may occur after the prediction cutoff.
9. Shapes, class vocabularies, CRS, and feature order must match the saved model contract.
10. Missingness and coverage must satisfy the trained model's saved policy.

## Failure behavior

- **Missing required feature:** reject the prediction request with the missing canonical names; do not impute or silently substitute.
- **Incompatible units:** reject unless an explicit, documented conversion exists; do not guess.
- **Ambiguous columns:** reject and ask for an explicit mapping; do not choose by fuzzy similarity.
- **Extra columns:** ignore only after logging them and confirming they are not used as hidden features; never allow extra columns to alter feature order.
- **Post-event or target-like columns:** reject or quarantine from the feature adapter, including fatalities, injuries, duration, flooded area, damage, severity, event dates used as predictors, and `uei`.
- **Unknown source vintage:** reject when temporal validity cannot be established.

## Scaling

Use only the serialized preprocessing artifact fitted on the training portion. Custom data must be transformed, never fitted. A custom CSV with a different feature schema cannot be used with an existing model merely because column names appear similar.
