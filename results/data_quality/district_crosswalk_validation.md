# District Crosswalk Validation

## Inputs

- IFI input: `data/processed/ifi_event_clean.csv`
- Boundary input: original DataMeet Census 2011 Shapefile components under `data/external/boundaries/raw/`
- Output: `data/derived/district_crosswalk.csv`
- Method: exact spelling and transparent case/punctuation normalization only; no fuzzy matching, spatial join, or code substitution.

## Crosswalk counts

The output contains 977 rows because duplicate Census boundary features are preserved rather than collapsed.

| Category | Rows | Meaning |
|---|---:|---|
| Exact-name candidates | 547 | Exact IFI district spelling matched one or more Census boundary records; not historically or state verified |
| Normalized candidates requiring verification | 13 | Case/punctuation-normalized candidate only |
| Unmatched | 417 | IFI-only or boundary-only records with no accepted name match |
| Verified mappings | 0 | No official crosswalk or historical evidence was available to certify a mapping |
| Manual verification required | 560 | All exact and normalized candidates require state/historical review |

The earlier comparison's 537 exact and 22 normalized counts were name-level comparison counts. The final file preserves boundary-feature rows and uses a more conservative candidate representation; therefore row counts are not directly identical to those name-level counts.

## Identifier validation

- Boundary fields: `DISTRICT`, `ST_NM`, `ST_CEN_CD`, `DT_CEN_CD`, `censuscode`.
- `censuscode` is unique across the 641 boundary features.
- `ST_CEN_CD` and `DT_CEN_CD` repeat and are documented as Census-code fields.
- No LGD field is present in the boundary DBF.
- The official LGD portal is `https://lgdirectory.gov.in/` and provides district-code views/downloads, but its data were not downloaded in this phase.
- No relationship between IFI `district_lgd_codes` and Census `censuscode`/`DT_CEN_CD` was established. No Census field is called an LGD code.

## Historical limitation

All 977 output rows are marked `HISTORICAL_BOUNDARY_REVIEW_REQUIRED`. The boundary layer is a Census 2011 reference while IFI events span 1967–2023. District creation, renaming, splitting, merging, and boundary changes can make a same-name match historically invalid.

## Validation conclusions

- No raw IFI or processed IFI file was modified.
- No district was silently renamed or merged.
- No unsupported fuzzy match was accepted.
- Empty mapping fields represent unmatched sides, not fabricated values.
- The crosswalk is suitable as a review queue, not as an approved aggregation key.
- Rainfall aggregation must wait for manual review, an approved boundary-vintage policy, and an official LGD/Census crosswalk decision.