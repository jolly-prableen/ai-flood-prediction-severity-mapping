# IFI to Boundary Matching

## Inputs

- IFI: `data/processed/ifi_event_clean.csv`
- Boundary: `data/external/boundaries/raw/2011_Dist.shp` and its original sidecar files
- Boundary fields: `DISTRICT`, `ST_NM`, `ST_CEN_CD`, `DT_CEN_CD`, `censuscode`
- IFI geographic fields: `districts`, `state`, `district_lgd_codes`, `state_codes`

## Comparison method

The comparison tokenized the IFI comma-separated district values and compared them to boundary names using exact matching and transparent case/punctuation normalization. It did not fuzzy-match, assign codes, or perform a spatial join. A normalized name match is not accepted as a final mapping.

## Results

| Result | Count |
|---|---:|
| Boundary polygon features | 641 |
| Distinct boundary district names | 631 |
| Distinct IFI district tokens | 882 |
| Exact name matches | 537 |
| Normalized matches requiring verification | 22 |
| Boundary-only names | 85 |
| IFI-only tokens | 332 |

The complete row-level comparison is in `results/data_quality/ifi_boundary_comparison.csv`.

## Identifier findings

`censuscode` is unique across the 641 boundary features. `ST_CEN_CD` and `DT_CEN_CD` repeat because they are state/district Census-code fields in the published layer, not necessarily globally unique row keys. No LGD field is present in the boundary DBF, and no documented relationship between these Census codes and IFI `district_lgd_codes` was established.

The IFI code fields are multi-value strings and are not used as a boundary crosswalk in this phase. They must not be relabeled as LGD codes without an official crosswalk.

## Match policy

- Exact name matches are candidates for manual review, not final approval.
- Normalized matches are `REQUIRES_VERIFICATION` and need state context plus historical review.
- Boundary-only and IFI-only names remain unresolved.
- Historical district changes may explain both unmatched groups; no current boundary is assumed to represent all IFI years.
- No IFI or boundary file was modified.