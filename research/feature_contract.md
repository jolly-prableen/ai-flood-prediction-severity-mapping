# Member 1 Feature Contract (Final Specification)

**Project**: AI-Based Flood Prediction and Flood Severity Mapping for Disaster Management  
**Role**: Member 1 — Data + Research Lead $\to$ Member 2 — Modeling Lead  
**Branch**: `member1-data`  
**Date**: 2026-09-12  

---

## 1. Executive Status & Categorization

| Category | Deliverable / Features | Status | Notes |
|---|---|---|---|
| **M2 Baseline Features** | `Population`, `Parmanent_Water` | **`APPROVED`** | Frozen for current hackathon baseline modeling. |
| **M2 Baseline Target** | `Corrected_Percent_Flooded_Area` | **`TARGET ONLY`** | Strictly prohibited as an input feature. |
| **Static Spatial Features** | `district_area_sq_km`, `centroid_lat`, `centroid_lon` | **`COMPLETED`** | Extracted from Census 2011 official shapefile for 502 districts. |
| **Rainfall Reanalysis** | `rainfall_total_mm_7d`, `rainfall_total_mm_26w`, `rainfall_max_daily_mm_7d` | **`FUTURE ENHANCEMENT`** | Minimal test NetCDF validated; bulk 2014–2023 download deferred. |
| **Auxiliary Spatial** | `elevation_m`, `land_cover_fraction` | **`FUTURE ENHANCEMENT`** | Deferred until spatial raster pipeline is integrated. |
| **SMOTE Augmentation** | Synthetic minority sampling | **`BLOCKED`** | Blocked for regression; blocked for classification until satellite negatives exist. |

---

## 2. CURRENT APPROVED M2 BASELINE FEATURE CONTRACT

The current Member 2 modeling baseline is frozen and preserved exactly as configured in `src/backend_api.py`:

```python
BASELINE_REQUIRED_FEATURES = ["Population", "Parmanent_Water"]
TARGET_COL = "Corrected_Percent_Flooded_Area"
```

### Exact Feature Specifications

| Order | Feature Name | Accepted Aliases | Data Type | Physical Meaning | Source / Provenance | Min Value | Max Value | Imputation / Missing Handling |
|---|---|---|---|---|---|---|---|---|
| **1** | **`Population`** | `population`, `pop`, `population_baseline` | `float32` / `int64` | Baseline district population (demographic exposure metric) | IFI `District_FloodImpact.csv` / Census 2011 static features | 7,110 | 13,403,998 | Impute with training median ($500,000.0$). Never use event casualties. |
| **2** | **`Parmanent_Water`** | `parmanent_water`, `permanent_water`, `water_body` | `float32` | Baseline percentage of district covered by permanent water bodies | IFI `District_FloodedArea.csv` | 0.00% | 29.67% | Impute with training median ($1.20\%$). |

### Invariants for M2 Baseline
1. **Exact Feature Order**: `[Population, Parmanent_Water]`.
2. **Dimension**: Exactly 2 input features per observation row.
3. **Target Isolation**: `Corrected_Percent_Flooded_Area` is strictly the prediction outcome target and must **NEVER** enter the input feature vector.
4. **Zero External Dependencies**: The M2 baseline runs locally without requiring ERA5-Land downloads or satellite raster processing.

---

## 3. FUTURE ENHANCEMENT FEATURES (Deferred Beyond Hackathon Baseline)

These features are architected and implemented in the observation-frame infrastructure (`src/feature_engineering/`) for future advanced sequence/spatial models:

| Feature Name | Intended Role | Source | Status | Blocker / Deferral Reason |
|---|---|---|---|---|
| `rainfall_total_mm_7d` | 7-day antecedent rainfall depth ($mm$) | ECMWF ERA5-Land | `FUTURE ENHANCEMENT` | Requires 2014–2023 ERA5-Land bulk download completion. |
| `rainfall_total_mm_26w` | 26-week antecedent saturation ($mm$) | ECMWF ERA5-Land | `FUTURE ENHANCEMENT` | Requires 2014-H2 antecedent reanalysis download completion. |
| `rainfall_max_daily_mm_7d` | Peak single-day storm intensity ($mm/day$) | ECMWF ERA5-Land | `FUTURE ENHANCEMENT` | Requires ERA5-Land bulk hourly download completion. |
| `district_area_sq_km` | Official polygon planar area ($km^2$) | Census 2011 GIS | `COMPLETED` | Extracted and available in `district_static_features.csv`. |
| `centroid_lat`, `centroid_lon` | Geometric centroid coordinates | Census 2011 GIS | `COMPLETED` | Extracted and available in `district_static_features.csv`. |
| `elevation_m` | Mean district elevation | SRTM DEM | `FUTURE ENHANCEMENT` | Raster processing deferred to spatial phase. |
| `land_cover_fraction` | Zonal vegetation/urban fractions | Copernicus LULC | `FUTURE ENHANCEMENT` | Raster processing deferred to spatial phase. |

*Explicit Notice: ERA5-Land rainfall and GFM independent observation integration are deferred future enhancements and are NOT part of the current M2 baseline.*

---

## 4. FORBIDDEN COLUMNS & LEAKAGE EXCLUSIONS

The following columns are strictly prohibited from entering any feature matrix:

1. **Target Variables**:
   - `Corrected_Percent_Flooded_Area` (Current M2 Target)
   - `Percent_Flooded_Area` (Uncorrected counterpart; leaking target)
   - `flood_binary` (Provisional classification target)
   - `severity_score`, `severity_class` (Provisional severity targets)
2. **Post-Event Casualties and Outcomes**:
   - `human_fatality`, `human_injured`, `human_displaced`, `animal_fatality`
   - `extent_of_damage`, `description_of_casualties_injured`, `area_affected`
   - `duration_days`, `mean_flood_duration`
3. **Event Identifiers & Timing Boundaries**:
   - `uei` (Unique Event Identifier — fatal event identity leakage)
   - `start_date`, `end_date`, `forecast_start`, `forecast_end`
   - `unnamed_0`, `event_souce_id`, `event_source`, `location`
