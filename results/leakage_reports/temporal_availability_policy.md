# Temporal Availability and Target/Feature Policy

The exact lead time is unresolved. The classifications below use a conservative pre-event prediction interpretation anchored immediately before `start_date`.

## Temporal availability

| Field or group | Availability classification | Policy |
|---|---|---|
| `start_date` | DURING/AROUND EVENT / target reference | Use as event reference or label boundary, never as a pre-event feature. |
| `end_date` | AFTER EVENT | Target/reference information only. |
| `duration_days` | AFTER EVENT | Target-only candidate; exclude as a feature. |
| `severity` | UNKNOWN, currently entirely missing | Do not use until defined; if populated, treat as outcome-like and target-only. |
| `area_affected` | DURING/AFTER EVENT, currently entirely missing | Target-only candidate after units and timing are verified. |
| `human_fatality`, `human_injured` | DURING/AFTER EVENT | Post-event impact; target-only candidates. |
| `human_displaced`, `animal_fatality` | DURING/AFTER EVENT | Post-event impact; target-only candidates after representation is verified. |
| `description_of_casualties_injured`, `extent_of_damage` | AFTER EVENT | Exclude from predictive features; possible target evidence only after coding rules. |
| `main_cause` | UNKNOWN | May be known before or during an event, or coded retrospectively. Require provenance/timing verification. |
| `population` | UNKNOWN | Could be a baseline feature, but reference year is undocumented. Verify vintage before use. |
| `parmanent_water` | UNKNOWN | Could be static baseline geography, but vintage and derivation are undocumented. Verify before use. |
| `districts`, `state`, `dist_name` | BEFORE EVENT geographic context, but event-frame availability is unresolved | Use only after forecast unit and geographic crosswalk are fixed. |
| `district_lgd_codes`, `state_codes` | UNKNOWN identifier timing/semantics | Grouping or joins only; not model features. They are not assumed to be validated LGD fields. |
| `uei`, `unnamed_0`, `event_souce_id` | UNKNOWN/provenance identifiers | Grouping and audit only; never model features. |
| District aggregate impact/flooded-area fields | UNKNOWN reference period, likely DURING/AFTER EVENT | Treat as target-only or leakage until source period and event overlap are established. |
| Rainfall/event information | NOT PRESENT in current files | No availability claim can be made; an external source would need a timestamped forecast/observation policy. |

## Policy buckets

### TARGET-ONLY

`start_date`, `end_date`, `duration_days`, `severity`, `area_affected`, fatality/injury/displacement fields, casualty and damage fields, `mean_flood_duration`, `percent_flooded_area`, and `corrected_percent_flooded_area` may contribute to later outcome definitions only after their semantics and reference periods are approved.

### PREDICTIVE FEATURES

No current field is certified predictive-safe. Population, permanent water, and geographic context are candidates only after their vintage, forecast-unit mapping, and pre-event availability are verified.

### EXCLUDE

All post-event impact fields, event dates as predictors, event/row/source identifiers, raw code strings, and unverified aggregate tables should be excluded from a first predictive feature set.

### UNKNOWN

`main_cause`, `location`, `latitude`, `longitude`, population vintage, permanent-water vintage, district aggregate reference periods, and the availability of event-source metadata require verification.