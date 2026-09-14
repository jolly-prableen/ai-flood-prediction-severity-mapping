# Final Prediction Design

## Status

This is the approved working design for the project. It defines an interface and rules only. No observations, labels, targets, splits, or datasets are created here.

## Design

| Item | Contract |
|---|---|
| Prediction unit | District-level observation |
| Temporal unit | District-week |
| Historical context | 26 consecutive weeks, approximately six months |
| Prediction horizon | 7 days after the prediction cutoff |
| Geographic key | A verified district identifier from the selected boundary/LGD crosswalk; IFI `uei` is not a geographic key |
| Prediction cutoff | End of the current district-week, with the seven-day forecast window beginning after the cutoff |
| Positive observation | A district-week with a verified IFI event interval overlapping the seven-day forecast window, linked through one or more `uei` values |
| Negative observation | A district-week independently verified as non-flood by an approved observation frame; absence from IFI is insufficient |

## Assumptions

- **Working assumption:** the model predicts whether a district experiences a verified flood during the seven days after the cutoff.
- **Working assumption:** the input sequence contains only information available through the cutoff.
- **Unresolved:** whether the weekly cutoff is ISO-week, local-calendar-week, or another project-defined interval.
- **Unresolved:** the authoritative negative/event observation source and its completeness.
- **Unresolved:** the precise flood definition and event-overlap tolerance.
- **Unresolved:** whether rainfall inputs are observed rainfall through the cutoff, forecast rainfall, or both.

## Event-overlap rule

Assign every `uei` whose verified event interval overlaps the seven-day forecast window. Do not collapse multiple events into one arbitrary event. Store event count and event identifiers as audit metadata only; `uei` must never enter model features. Events with missing `start_date` cannot be assigned to a forecast window until resolved by a documented policy.

## Information available at prediction time

Potentially available, subject to source and vintage verification: antecedent rainfall through the cutoff, forecast rainfall if an operational forecast is approved, fixed district geometry, verified static DEM/LULC/hydrology features, and population or other baseline exposure values whose reference date precedes the cutoff.

## Information prohibited as features

Never use event start/end dates, duration, severity, affected area, fatalities, injuries, displacement, animal fatalities, casualty descriptions, damage extent, flooded-area measures, flood-impact aggregates, future rainfall, future-derived rolling statistics, `uei`, row indices, source IDs, or unverified geographic codes as predictive inputs. These may be retained as target/reference/audit fields according to the target contract.

## Negative observations

No negative labels may be generated from missing IFI records alone. The observation frame must independently establish district-week coverage and non-flood status, document its flood definition, and identify its own false-negative limitations.
