# Member 1 to Member 2 Final Handoff Specification

**Project**: AI-Based Flood Prediction and Flood Severity Mapping for Disaster Management  
**Role**: Member 1 — Data + Research Lead $\to$ Member 2 — Modeling / ML Lead  
**Branch**: `member1-data`  
**Date**: 2026-09-12  
**Handoff Status**: Final Data & Research Certification  

---

## 1. Executive Summary & Baseline Demarcation

Member 1 has finalized the data engineering, geographic harmonization, observation framing, target engineering, chronological partitioning, training-only preprocessing, and 12-point semantic leakage audit.

### Explicit Baseline Notice
> **ERA5-Land rainfall and GFM independent observation integration are deferred future enhancements and are NOT part of the current M2 baseline.**

Member 2's existing baseline modeling setup is frozen, approved, and preserved without modification.

---

## 2. CURRENT APPROVED M2 BASELINE CONTRACT

### A. Approved Features
1. **`Population`** (Demographic exposure metric; float32/int64; source: IFI `District_FloodImpact.csv` / Census 2011)
2. **`Parmanent_Water`** (Hydrological surface baseline percentage; float32; source: IFI `District_FloodedArea.csv`)

- **Exact Feature Order**: `["Population", "Parmanent_Water"]`
- **Accepted Column Aliases**:
  - `Population`: `population`, `pop`, `population_baseline`
  - `Parmanent_Water`: `parmanent_water`, `permanent_water`, `water_body`

### B. Approved Target
- **`Corrected_Percent_Flooded_Area`** (Continuous percentage, range $0.000073\%$ to $23.62\%$)
- **Mathematical Formula**: $|\text{Percent\_Flooded\_Area} - \text{Parmanent\_Water}|$ (verified exact on $732 / 732$ rows).
- **Target Invariant**: Strictly `TARGET ONLY`. Prohibited from entering the input feature vector.

### C. Missing Value Imputation Rules
- Missing `Population`: Impute with training median ($500,000.0$).
- Missing `Parmanent_Water`: Impute with training median ($1.20\%$).
- Preprocessing scaler fitted exclusively on training data: `results/checkpoints/preprocessor.json`.

---

## 3. Dataset Artifacts & File Locations

| Artifact | File Path | Rows | Purpose |
|---|---|---|---|
| **Cleaned IFI Events** | `data/processed/ifi_event_clean.csv` | 6,876 | Cleaned primary event records from IFI-Impacts v3. |
| **Cleaned District Impact** | `data/processed/district_flood_impact_clean.csv` | 732 | Baseline demographic and casualty impact metrics. |
| **Cleaned Flooded Area** | `data/processed/district_flooded_area_clean.csv` | 732 | Baseline permanent water and corrected flooded area target. |
| **Verified District Static Features** | `data/processed/district_static_features.csv` | 502 | Official Census 2011 boundaries, areas, and centroid coordinates. |
| **Final District Crosswalk** | `data/derived/district_crosswalk_final.csv` | 889 | 502 `VERIFIED_NAME_STATE` districts; unverified preserved transparently. |
| **M2 Baseline Checkpoint (Classical)** | `results/checkpoints/baseline_classifier.joblib` | - | Random Forest baseline classifier evaluated on `[Population, Parmanent_Water]`. |
| **M2 Backend PyTorch Checkpoint** | `results/models/cnn_plus_lstm/best_model.pt` | - | PyTorch model checkpoint compatible with `src/backend_api.py`. |
| **M2 Baseline Metrics** | `results/metrics/xgboost_metrics.json` | - | Member 2's benchmark metrics (*100% untouched*). |

---

## 4. Extended Observation Frame & Split Locations (For Future Research)

For future sequence models and spatial evaluation:

| Split File | Path | Rows | Cutoff Range | Positive Overlaps |
|---|---|---|---|---|
| **Training Split** | `data/splits/train.csv` | 157,126 | `2015-01-04` to `2020-12-27` | 11,269 |
| **Validation Split** | `data/splits/val.csv` | 39,156 | `2021-01-03` to `2022-06-26` | 1,421 |
| **Test Split** | `data/splits/test.csv` | 39,658 | `2022-07-03` to `2023-12-31` | 1,495 |

- **Strict Chronological Separation**: $\text{Train} < \text{Val} < \text{Test}$ with zero key overlap.
- **Zero False Negatives**: All unobserved district-weeks remain `NaN` / `UNKNOWN_INSUFFICIENT_COVERAGE`.

---

## 5. Leakage Exclusions & Precautionary Rules

The 12-point semantic leakage audit (`src/leakage/final_leakage_audit.py`) certified zero structural leakage:
1. `Corrected_Percent_Flooded_Area` must NEVER be used as an input feature.
2. `uei` must NEVER enter model features (unique event identifier; causes catastrophic lookup leakage).
3. Casualty variables (`human_fatality`, `human_injured`, `human_displaced`) are strictly outcome metrics.
4. Event interval dates (`start_date`, `end_date`, `forecast_start`, `forecast_end`) are excluded from feature vectors.
5. All transformers and scalers are fitted exclusively on training splits (`"fitted_on": "train_split_only"`).

---

## 6. Known Limitations & Provenance

1. **`Corrected_Percent_Flooded_Area`**: Represents an all-time multi-year study period aggregate rather than dynamic weekly observations. It is preserved specifically as the hackathon baseline target.
2. **Satellite Non-Event Data**: Independent negative observations from Copernicus GFM Sentinel-1 are unacquired; absence from IFI is never treated as a verified negative flood observation.
3. **ERA5-Land Grid Reanalysis**: Gridded precipitation was validated on the 2023-07-15 test NetCDF; full historical reanalysis (2014–2023) is deferred post-hackathon.

---

## 7. How Member 2 Can Run Inference

### Via Python Script:
```python
import joblib
import pandas as pd

# Load baseline model
clf = joblib.load("results/checkpoints/baseline_classifier.joblib")

# Prepare input data adhering to baseline contract
X_input = pd.DataFrame({
    "Population": [1500000.0, 450000.0],
    "Parmanent_Water": [2.5, 0.2]
})

# Run inference
probs = clf.predict_proba(X_input)[:, 1]
preds = clf.predict(X_input)
print("Predicted probabilities:", probs)
print("Predicted alerts:", preds)
```

### Via Backend API (`src/backend_api.py`):
```python
import sys
sys.path.append("src")
import backend_api as api
import pandas as pd

df = pd.DataFrame({"Population": [1500000.0], "Parmanent_Water": [2.5]})
result = api.predict_uploaded_dataset(df, "CNN + LSTM", "Flood Risk Prediction")
print(result)
```
