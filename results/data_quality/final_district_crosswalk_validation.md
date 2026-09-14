# Final District Crosswalk Validation

This is a working integration crosswalk for later analysis, not a claim that Census 2011 boundaries represent every historical IFI district. The source comparison was used as the primary evidence. No raw IFI, processed IFI, LGD, or Census boundary file was modified.

## Counts

- Total unique IFI district tokens represented: **882**
- Final crosswalk rows: **889**; extra rows preserve ambiguous candidates.
- Total rows mapped to a Census boundary: **539**
- `VERIFIED_NAME_STATE`: **502 rows**
- `NORMALIZED_REVIEW`: **10 rows**
- `AMBIGUOUS_REVIEW`: **14 rows / 7 IFI names**
- `HISTORICAL_REVIEW`: **170 rows**
- `UNMATCHED`: **193 rows**
- Historical limitation status: **{'HISTORICAL_REVIEW_REQUIRED': 889}**

## Duplicate assignments and relationships

- Duplicate Census boundary assignments to multiple IFI names: **4 censuscode values**.
- Duplicate LGD district assignments to multiple IFI names: **7 LGD district codes**.
- IFI names with multiple final rows (one-to-many candidate relationships): **7 names**.
- Census boundary names assigned to multiple final rows: **11 names**.
- These repeated relationships are preserved for review and are not merged or deduplicated.

## Missing identifiers

- Missing LGD district codes: **193 rows**.
- Missing Census `censuscode`: **350 rows**.
- Missing Census 2011 boundary district: **350 rows**.

## Unresolved issues

- LGD `District Code` is retained as the official LGD field; it is not equated with Census `censuscode` or `DT_CEN_CD`.
- All rows retain `HISTORICAL_REVIEW_REQUIRED` because IFI spans 1967–2023 while the acquired Census boundary layer is a 2011 reference.
- Multi-value IFI state context can be noisy and does not prove a unique state assignment for every district token.
- Normalized, ambiguous, historical, and unmatched rows require review before they are used as an authoritative aggregation key.
- No rainfall aggregation or feature construction was performed.
