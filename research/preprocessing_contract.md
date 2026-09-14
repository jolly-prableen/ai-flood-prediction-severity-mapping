# Member 1 Preprocessing Contract (Final Specification)

**Project**: AI-Based Flood Prediction and Flood Severity Mapping for Disaster Management  
**Role**: Member 1 — Data + Research Lead $\to$ Member 2 — Modeling Lead  
**Branch**: `member1-data`  
**Date**: 2026-09-12  

---

## 1. Executive Status & Categorization

| Pipeline Component | Scope | Status | Notes |
|---|---|---|---|
| **M2 Baseline Adaptation** | Column alias mapping to `[Population, Parmanent_Water]` | **`APPROVED`** | Verified in `src/backend_api.py` and `scripts/run_model_demo.py`. |
| **M2 Missingness Handling** | Imputation using conservative training medians | **`APPROVED`** | Prevents inference failures on unobserved fields without zero-filling. |
| **M2 Model Preprocessor** | Training-only feature scaling | **`COMPLETED`** | Checkpoint saved in `results/checkpoints/preprocessor.json`. |
| **Rainfall Accumulation (Hourly $\to$ Daily)** | 24-hour UTC accumulation semantics ($m \to mm$) | **`FUTURE ENHANCEMENT`** | Tested on 2023-07-15 NetCDF; bulk production pipeline ready in `process_rainfall.py`. |
| **Cutoff-Safe Antecedent Window** | $[C-6\text{d}, C]$ 7d and $[C-181\text{d}, C]$ 26w derivation | **`FUTURE ENHANCEMENT`** | Fully implemented in `rainfall_features.py`; deferred until bulk download. |

---

## 2. CURRENT APPROVED M2 BASELINE PREPROCESSING

The baseline preprocessing pipeline accepts raw district tabular input and maps it to Member 2's feature contract:

### Step-by-Step Execution Sequence

```
Raw Input Table
  └── Step 1: Column Name Normalization & Alias Mapping
  └── Step 2: Extraction of Required Features [Population, Parmanent_Water]
  └── Step 3: Strict Numeric Casting (float32)
  └── Step 4: Missing Value Imputation (Training Medians)
  └── Step 5: Canonical Ordering [Population, Parmanent_Water]
  └── Model Input (X_input shape: [N, 2])
```

### 1. Column Alias Mapping
Case-insensitive and whitespace-stripped alias resolution:
```python
FEATURE_ALIASES = {
    "population": "Population",
    "pop": "Population",
    "population_baseline": "Population",
    "permanent_water": "Parmanent_Water",
    "parmanent_water": "Parmanent_Water",
    "water_body": "Parmanent_Water"
}
```

### 2. Missing Value Imputation Rules
- `Population`: If null or unparseable, impute with training median ($500,000.0$).
- `Parmanent_Water`: If null or unparseable, impute with training median ($1.20\%$).
- **Integrity Rule**: Never use casualty counts (`human_fatality`, `human_injured`) as population.

### 3. Scaling & Normalization Protocol
- **Training-Only Fit**: All scaler parameters (means, standard deviations, min/max bounds) must be fitted exclusively on the training split (`data/splits/train.csv`).
- **Inference Invariant**: Validation, test, and live demonstration data must strictly invoke `transform`, never `fit` or `fit_transform`.
- **Checkpoint Location**: `results/checkpoints/preprocessor.json` (`"fitted_on": "train_split_only"`).

---

## 3. FUTURE ENHANCEMENT PREPROCESSING (Deferred Pipeline)

For future sequence and spatial architectures (CNN+Transformer, U-Net+ConvLSTM):

1. **ERA5-Land Hourly Accumulation**:
   - Hourly precipitation is accumulated in metres over the 1-hour validity window.
   - Conversion to rainfall depth: $\text{rainfall\_mm} = \text{tp\_m} \times 1000.0$.
   - A complete UTC calendar day consists of exactly 24 hourly validity steps (`01:00` to `24:00` UTC).
   - If any hourly step is missing, the daily aggregate is flagged `NaN` (never zero-filled).
2. **Cutoff-Safe Window Extraction**:
   - For any weekly prediction cutoff $C$ (Sunday 23:59 UTC):
     - `rainfall_total_mm_7d`: Sum of daily rainfall in $[C-6\text{ days}, C]$ (7 inclusive days).
     - `rainfall_max_daily_mm_7d`: Maximum single-day rainfall in $[C-6\text{ days}, C]$.
     - `rainfall_total_mm_26w`: Sum of daily rainfall in $[C-181\text{ days}, C]$ (182 inclusive days).
   - Zero observations $> C$ are permitted into feature calculations.

*Explicit Notice: ERA5-Land rainfall and GFM independent observation integration are deferred future enhancements and are NOT part of the current M2 baseline.*
