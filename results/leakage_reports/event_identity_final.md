# Final Event Identity Decision

## Verified findings

- `uei` is present for all 6,876 cleaned event rows.
- `uei` has 6,876 unique non-null values and zero repeated values in the current inventory.
- There are 6,856 usable `start_date` values and 20 missing start dates.
- District plus year is not unique: 812 district-year combinations repeat and affect 2,707 rows.
- Therefore, multiple flood events can occur in the same district in the same year.

## Decision

Use `uei` as the preferred event identifier for:

- event grouping
- exact duplicate checks
- future contamination checks
- event-level aggregation

Do not use `uei` as a model feature. It is an identifier assigned to a recorded event and can enable memorization or source-order artifacts.

Do not use district plus year as an event identifier. District and state fields are multi-value event attributes, and district plus date is also not guaranteed unique or complete.

## Stability limitation

Current-file uniqueness is verified, but official semantics and cross-version stability of `uei` still require confirmation from the IFI documentation. Any future source revision must rerun uniqueness and missingness checks before using it for grouping.