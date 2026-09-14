# Rainfall Feature Definitions

These are future feature definitions only. No rainfall files have been downloaded and no features have been calculated.

## Common cutoff rule

For a district-week prediction unit, let `C` be the final timestamp available at the approved prediction cutoff. The seven-day forecast window begins after `C` and extends seven calendar days. Observed rainfall after `C` must not enter predictive features. If the team later approves forecast rainfall, forecast values must be kept separate from observed antecedent values and documented by issuance time.

The exact weekly convention, timezone, and date-only event tolerance remain `REQUIRES TEAM DECISION`.

## `rainfall_total_mm_7d`

- **Window:** `[C - 6 days, C]`, seven daily observations including the cutoff day.
- **Endpoint rule:** both endpoints inclusive.
- **Aggregation:** sum daily rainfall depth.
- **Spatial aggregation:** area-weight grid cells intersecting the verified district polygon; preserve boundary vintage, CRS, edge-cell rule, and grid mask.
- **Units:** millimetres, only after selected IMD release metadata confirms the source unit.
- **Missing handling:** do not replace missing cells or days with zero. Require complete coverage or emit a documented coverage mask.
- **Leakage rule:** exclude all rainfall after `C`.

## `rainfall_total_mm_26w`

- **Window:** 26 consecutive completed district-week steps ending at the current week/cutoff; approximately six months.
- **Endpoint rule:** each weekly step is inclusive within its approved week and ends no later than `C`.
- **Aggregation:** sum daily rainfall within each week, retaining the ordered 26-step sequence.
- **Spatial aggregation:** same area-weighted district or native-grid method as the seven-day feature.
- **Units:** millimetres per weekly step or cumulative millimetres, clearly distinguished in implementation.
- **Missing handling:** preserve missingness and coverage; do not silently treat absent rainfall as dry weather.
- **Leakage rule:** no values after `C` and no future-derived rolling statistics.

## `rainfall_max_daily_mm_7d`

- **Window:** `[C - 6 days, C]`, inclusive.
- **Aggregation:** maximum valid daily rainfall across the seven-day antecedent window.
- **Spatial aggregation:** calculate the district daily rainfall series first, then take the temporal maximum; native-grid models retain grid-wise representation instead.
- **Units:** millimetres per day.
- **Missing handling:** insufficient valid coverage is a missing/invalid state, not zero.
- **Leakage rule:** exclude all rainfall after `C`.

## Pending metadata

The selected IMD release must confirm the variable name, coordinate names, time encoding, units, missing-value representation, file format, spatial bounds, and complete coverage through the usable IFI period before implementation.