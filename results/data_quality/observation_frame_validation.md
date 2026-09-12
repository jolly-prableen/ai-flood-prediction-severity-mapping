# District-Week Observation Frame & GFM Coverage Validation

## 1. GFM Source Audit

- **Local GFM Rasters Present**: False
- **Audit Status**: UNACQUIRED_INSUFFICIENT_INDEPENDENT_COVERAGE
- **Contract Policy**: NEVER convert unobserved non-event to negative (0). Preserve as UNKNOWN (NaN).

## 2. Frame Summary

- **Temporal Range**: 2015-01-04 to 2023-12-31 (470 weekly cutoffs)
- **Districts**: 502 verified crosswalk districts
- **Total District-Weeks**: 235,940
- **Verified Positive Events (Flood_Binary = 1)**: 14,185
- **Unknown Observation Coverage (Flood_Binary = NaN)**: 221,755
- **Verified Negatives (Flood_Binary = 0)**: 0

## 3. Methodological Compliance

- **No Fake Negatives**: Absence of an IFI event record was NEVER converted to 0.
- **Cutoff Safety**: Prediction cutoff $C$ occurs on Sunday; forecast window is strictly $[C+1, C+7]$.
- **Identifier Isolation**: Event identifiers (`uei`) are recorded in `uei_list` for traceability but excluded from model features.
