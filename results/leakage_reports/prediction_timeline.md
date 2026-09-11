# Prediction Timeline

The exact operational prediction timestamp and forecast horizon are not specified by the IFI data or current project documentation. The audit therefore uses a conservative pre-event forecasting interpretation and records timing uncertainty explicitly.

## Event reference

- Candidate event reference: `start_date` (6,856 usable values), spanning 1967-01-08 through 2023-12-09.
- `end_date` has 6,856 usable values and represents information available only after the event has ended.
- No prediction horizon, alert lead time, observation cutoff, or district-aggregate reference period is documented.

## PRE-EVENT INFORMATION

Potentially available before a flood, subject to verification: geographic unit, verified baseline population, static permanent-water or other environmental covariates, and a known forecast date. In the current files, population and permanent-water vintage are not documented, and raw geography fields are observed event-record attributes rather than a complete set of forecast units.

## EVENT-TIME INFORMATION

Main cause may be known during an event, but its coding time is undocumented. Start date identifies the event and is target/reference information, not a pre-event predictor. Event source metadata and codes describe collection or geography and should not be treated as measurements without verification.

## POST-EVENT INFORMATION

End date, duration, severity, affected area, fatalities, injuries, displacement, animal fatalities, casualty descriptions, damage extent, flooded-area measures, and flood-impact aggregates are consequences or outcome-like summaries. They are leakage for pre-event predictive features, although some may be valid target components later.

## Decision required

Before feature selection, approve the forecast horizon and the reference period for the district aggregate tables. Without those decisions, no field can be certified SAFE for predictive use.