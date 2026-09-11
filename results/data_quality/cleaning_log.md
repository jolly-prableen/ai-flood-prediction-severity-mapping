# Phase 3 Cleaning Log

## Scope

Raw CSVs under `data/raw/` were read but not modified. No imputation, target construction, leakage audit, split, augmentation, external-data integration, or model development was performed.

## Source roles

- `India_Flood_Inventory_v3.csv`: event-level flood inventory; one row represents an inventory event record and may reference multiple districts/states.
- `District_FloodImpact.csv`: district-level aggregate table; no year or event identifier is present.
- `District_FloodedArea.csv`: district-level aggregate table; no year or event identifier is present.

## Transformations

- Column names were converted to snake_case in processed copies; the original-to-cleaned mapping is recorded in `results/data_quality/column_name_mapping.csv`.
- Event dates were parsed with the observed day-first mixed format. Non-null conversion failures were zero; missing dates remain missing.
- Numeric-looking object columns were converted only when every non-null value matched a numeric pattern. Mixed/list-valued code fields remained strings.
- District and state names received format-only trimming and whitespace collapsing. Semantic spelling variants were retained and marked `REQUIRES_VERIFICATION` in `data/derived/district_name_mapping.csv`.
- Missing values were preserved. No rows or columns were removed.
- Exact duplicate rows were analyzed and retained. Repeated district-year combinations were retained as potential separate events.

## Rows and columns

| Source | Original rows | Original columns | Processed rows | Processed columns | Rows removed |
|---|---:|---:|---:|---:|---:|
| District_FloodImpact.csv | 732 | 5 | 732 | 5 | 0 |
| District_FloodedArea.csv | 732 | 4 | 732 | 4 | 0 |
| India_Flood_Inventory_v3.csv | 6876 | 23 | 6876 | 23 | 0 |

## Merge decision

No ifi_unified_clean.csv created. The event inventory stores multi-value district/state lists; district aggregate tables have Dist_Name only, no state field, no year, no event key, and no verified common identifier. A name-only merge would be ambiguous.

## Validation

Raw hashes before processing: `{"District_FloodImpact.csv": "0cc7381e8153cdd34e287540e64947e4cd2e5ff46d2461581e7b6c041b3655fb", "District_FloodedArea.csv": "738d5edf8a29c70de520b3b7b8e148eb7eed2ce89bbd9f0ecacd3cbc17b07610", "India_Flood_Inventory_v3.csv": "ef9ab2cd0db7bf917dcc22c7cb094ec599f5013ef1b96ba525d816f26ff1b108"}`
Raw hashes after processing: `{"District_FloodImpact.csv": "0cc7381e8153cdd34e287540e64947e4cd2e5ff46d2461581e7b6c041b3655fb", "District_FloodedArea.csv": "738d5edf8a29c70de520b3b7b8e148eb7eed2ce89bbd9f0ecacd3cbc17b07610", "India_Flood_Inventory_v3.csv": "ef9ab2cd0db7bf917dcc22c7cb094ec599f5013ef1b96ba525d816f26ff1b108"}`
Hash comparison passed: `True`
