# Target Contract

No target columns are created in this phase. These are future design contracts only.

## Flood_Binary

- **Definition:** 1 when a verified district-week observation has at least one independently confirmed flood event overlapping the seven-day forecast window; 0 only when the observation frame independently verifies no flood.
- **Source variables:** verified event frame linked to IFI `uei`, event start/end dates, district crosswalk, and independent non-event source.
- **Construction timing:** after the district-week observation frame and event-overlap rule are finalized; before model training.
- **Level:** district-time.
- **Target-only variables:** event dates and event identity metadata used to assign the label.
- **Forbidden features:** `uei`, event dates, duration, impacts, flooded area, damage, and any future data used in label assignment.
- **Precaution:** absence from IFI is never sufficient for zero.

## Severity_Class

- **Definition:** an approved categorical impact/severity class for a positive district-week event, with class thresholds and source semantics defined before construction.
- **Source variables:** candidate IFI outcome fields such as `severity`, `duration_days`, `area_affected`, flooded-area measures, or impact counts, but only after their meanings, units, timing, and aggregation level are verified.
- **Construction timing:** after the positive observation and severity rubric are approved.
- **Level:** district-time or district-event, not currently fixed.
- **Target-only variables:** every outcome field used in class construction.
- **Forbidden features:** every target component and any post-event impact measure.
- **Precaution:** do not combine incompatible event-level and district-aggregate fields without a temporal/geographic crosswalk.

## Severity_Score

- **Definition:** a documented numeric severity/impact score built from approved, predeclared outcome components; the formula, units, weighting, and missingness rule must be approved before use.
- **Source variables:** possible duration, flooded area, fatalities, injuries, displacement, damage, or verified source severity, subject to semantic validation.
- **Construction timing:** after the target rubric and outcome reference period are fixed.
- **Level:** district-time or district-event, pending team decision.
- **Target-only variables:** all outcome components and any post-event aggregates.
- **Forbidden features:** all target components, future-derived statistics, and identifiers.
- **Precaution:** fit no target transformation using validation/test/custom inference observations; define target availability and censoring explicitly.

## General target rules

- A variable may be valid for target construction and invalid as a feature.
- Target assignment must use only the approved forecast window and observation frame.
- `uei` may group events but must never enter the model.
- No target may be created until the independent negative frame, horizon, overlap rule, and missing-date policy are approved.
