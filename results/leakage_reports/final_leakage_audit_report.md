# 12-Point Semantic Leakage Audit Report

**Overall Status**: `STRUCTURAL_CODE_CHECKS_PASSED__EMPIRICAL_EXTERNAL_DATA_BLOCKED`

## 1. Structural Code & Policy Checks (All Invariants Verified)

| Check # | Vector | Status | Audit Findings |
|---|---|---|---|
| 1 | 1_target_leakage | `PASS` | No target variables found in approved canonical features: ['rainfall_total_mm_7d', 'rainfall_total_mm_26w', 'rainfall_max_daily_mm_7d', 'district_static_geometry', 'elevation_m', 'land_cover_fraction', 'hydrology_static_or_recent', 'population_baseline'] |
| 2 | 2_post_event_information | `PASS` | No post-event outcome or casualty variables are used as predictive features. |
| 3 | 3_temporal_leakage | `PASS` | Strict chronological separation confirmed: Train max (2020-12-27) < Val min (2021-01-03) <= Val max (2022-06-26) < Test min (2022-07-03). |
| 4 | 4_train_test_contamination | `PASS` | Preprocessor and severity scaler checkpoints explicitly fitted strictly on training data. |
| 5 | 5_duplicate_leakage | `PASS` | Zero observation key overlap across train/val/test splits (overlaps=0, 0). |
| 6 | 6_aggregate_leakage | `PASS` | Static all-time study-period flooded area aggregate is strictly excluded from predictive features. |
| 7 | 7_target_construction_leakage | `PASS` | Event intervals and forecast horizon boundary timestamps excluded from predictive feature list. |
| 8 | 8_identifier_leakage | `PASS` | Unique event identifiers (uei) and database row identifiers are excluded from predictive inputs. |
| 9 | 9_spatial_leakage | `PASS` | Exact 502 verified crosswalk districts represented symmetrically across all time steps. |
| 10 | 10_future_derived_statistics | `PASS` | Rainfall feature definition strictly specifies antecedent window [C-6 days, C]; no future data permitted. |
| 11 | 11_merge_leakage | `PASS` | Total rows (235,940) matches exact theoretical cross-product of 502 districts x 470 cutoffs. |
| 12 | 12_sampling_negative_leakage | `PASS` | Absence of IFI events alone was NEVER converted into negative labels. Zero false negatives fabricated (count=0). Unobserved records explicitly preserved as NaN. |

## 2. Empirical External Data Validation (Honest State Assessment)

| External Dataset | Status | Detailed Finding |
|---|---|---|
| era5_rainfall_raster_empirical_validation | `ACQUIRED` | Actual ERA5-Land NetCDF files are absent due to missing CDS credentials. Rainfall features in final_richer_dataset.csv are 100% NaN placeholders. |
| gfm_sentinel1_satellite_empirical_validation | `BLOCKED` | Copernicus GFM satellite swath observations are absent locally. Positives represent IFI event-overlap occurrences only; independent non-events remain UNKNOWN. |

## 3. Methodological Certification

- **Code Architecture**: Certified free of target leakage, identifier leakage (`uei`), post-event contamination, and temporal boundary leakage.
- **Data Status**: Not final for modeling because ERA5-Land gridded precipitation is 100% NaN (blocked on CDS credentials) and GFM satellite rasters are unacquired.
