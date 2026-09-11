# Leakage-Safe Feature Policy

This policy is for later predictive-dataset design only. No columns were deleted or altered during the audit.

## A. SAFE CANDIDATE FEATURES

- None currently certified.

## B. FEATURES REQUIRING TEMPORAL/SPATIAL CARE

- `unnamed_0`: A unique source row/index field can enable memorization or reflect source ordering. Recommended action: Exclude from features; retain only for provenance.
- `uei`: UEI is unique for every inventory row and could allow memorization or partition contamination. Recommended action: Use for grouping and identity checks only; exclude as a feature.
- `main_cause`: Cause may be known before or during an event, but the dataset does not document when or how it was coded. Recommended action: Require source-timing verification before use.
- `districts`: District membership is geographic context, but this field is populated from observed event records and contains multiple districts per row. Recommended action: Use only with a clearly defined forecast unit; do not treat as a simple scalar feature.
- `state`: State is geographic context, but observed event rows and multi-state values can encode the labeled occurrence. Recommended action: Use only with a clearly defined forecast unit and negative-sample design.
- `event_source`: Source metadata is not a physical predictor and may encode collection or event-selection process. Recommended action: Exclude from predictive features unless a pre-event source is established.
- `event_souce_id`: Identifier-like source field; currently entirely missing and its semantics are unverified. Recommended action: Exclude from features; retain for provenance if populated later.
- `district_lgd_codes`: Geographic codes can support grouping or joins but are not confirmed as LGD codes and are stored as multi-value event fields. Recommended action: Exclude raw code strings from features until a verified forecast-unit policy exists.
- `state_codes`: State codes are geographic identifiers, not measurements; source semantics and timing require verification. Recommended action: Exclude raw code strings from features until verified.
- `dist_name`: District name identifies the geographic unit, but the aggregate table has no time period and cannot be safely aligned to an event. Recommended action: Use only as a grouping/join key, not as an unrestricted feature.
- `population`: Population could be a baseline covariate, but its reference year and provenance are undocumented. Recommended action: Verify vintage and keep fixed relative to the prediction timestamp.
- `parmanent_water`: Permanent-water coverage may be a baseline geographic feature, but units, vintage, and derivation are undocumented. Recommended action: Verify source vintage and ensure it excludes event-period observations.

## C. POST-EVENT / LEAKAGE FEATURES

- `start_date`: The event start date identifies the occurrence being predicted and is unavailable before the event starts. Recommended action: Use only as an outcome/reference timestamp, never as a predictive feature.
- `end_date`: The end date is known only after the event has ended. Recommended action: Exclude from predictive features; retain for event chronology.
- `duration_days`: Duration requires observing the event through its end and is an outcome-like consequence. Recommended action: Exclude from predictive features; possible target component only after definition.
- `severity`: The source field is explicitly named severity and is 100% missing in the current inventory. Recommended action: Do not use as a feature; investigate only as a possible target source.
- `area_affected`: Affected area is an event impact measurement and is 100% missing in the current inventory. Recommended action: Exclude from predictive features; possible target component only after verification.
- `human_fatality`: Fatality counts describe consequences of a flood; district aggregates may summarize the same events. Recommended action: Exclude from predictive features; possible impact target component.
- `human_injured`: Injury counts describe consequences of a flood; district aggregates may summarize the same events. Recommended action: Exclude from predictive features; possible impact target component.
- `human_displaced`: Displacement is a consequence of the event and its representation is source-dependent. Recommended action: Exclude from predictive features; possible impact target component after verification.
- `animal_fatality`: Animal fatalities are post-event consequences. Recommended action: Exclude from predictive features; possible impact target component after verification.
- `description_of_casualties_injured`: The field is a casualty/injury description and can directly reveal the outcome. Recommended action: Exclude from predictive features.
- `extent_of_damage`: Damage extent is a post-event impact description. Recommended action: Exclude from predictive features; possible target evidence only after coding rules are defined.
- `mean_flood_duration`: A district mean flood duration is an aggregate outcome-like measure with no documented reference period. Recommended action: Exclude until provenance and forecast timing are verified.
- `percent_flooded_area`: Flooded area is a direct impact measurement and may summarize the events being predicted. Recommended action: Exclude from predictive features; possible target component after temporal definition.
- `corrected_percent_flooded_area`: Corrected flooded area remains an impact measurement; correction does not remove temporal leakage risk. Recommended action: Exclude from predictive features; possible target component after temporal definition.

## D. IDENTIFIERS TO EXCLUDE

- `unnamed_0`: A unique source row/index field can enable memorization or reflect source ordering. Recommended action: Exclude from features; retain only for provenance.
- `uei`: UEI is unique for every inventory row and could allow memorization or partition contamination. Recommended action: Use for grouping and identity checks only; exclude as a feature.
- `event_source`: Source metadata is not a physical predictor and may encode collection or event-selection process. Recommended action: Exclude from predictive features unless a pre-event source is established.
- `event_souce_id`: Identifier-like source field; currently entirely missing and its semantics are unverified. Recommended action: Exclude from features; retain for provenance if populated later.
- `district_lgd_codes`: Geographic codes can support grouping or joins but are not confirmed as LGD codes and are stored as multi-value event fields. Recommended action: Exclude raw code strings from features until a verified forecast-unit policy exists.
- `state_codes`: State codes are geographic identifiers, not measurements; source semantics and timing require verification. Recommended action: Exclude raw code strings from features until verified.

## E. TARGET-ONLY VARIABLES

- `start_date`: The event start date identifies the occurrence being predicted and is unavailable before the event starts. Recommended action: Use only as an outcome/reference timestamp, never as a predictive feature.
- `end_date`: The end date is known only after the event has ended. Recommended action: Exclude from predictive features; retain for event chronology.
- `duration_days`: Duration requires observing the event through its end and is an outcome-like consequence. Recommended action: Exclude from predictive features; possible target component only after definition.
- `severity`: The source field is explicitly named severity and is 100% missing in the current inventory. Recommended action: Do not use as a feature; investigate only as a possible target source.
- `area_affected`: Affected area is an event impact measurement and is 100% missing in the current inventory. Recommended action: Exclude from predictive features; possible target component only after verification.
- `human_fatality`: Fatality counts describe consequences of a flood; district aggregates may summarize the same events. Recommended action: Exclude from predictive features; possible impact target component.
- `human_injured`: Injury counts describe consequences of a flood; district aggregates may summarize the same events. Recommended action: Exclude from predictive features; possible impact target component.
- `human_displaced`: Displacement is a consequence of the event and its representation is source-dependent. Recommended action: Exclude from predictive features; possible impact target component after verification.
- `animal_fatality`: Animal fatalities are post-event consequences. Recommended action: Exclude from predictive features; possible impact target component after verification.
- `description_of_casualties_injured`: The field is a casualty/injury description and can directly reveal the outcome. Recommended action: Exclude from predictive features.
- `extent_of_damage`: Damage extent is a post-event impact description. Recommended action: Exclude from predictive features; possible target evidence only after coding rules are defined.
- `mean_flood_duration`: A district mean flood duration is an aggregate outcome-like measure with no documented reference period. Recommended action: Exclude until provenance and forecast timing are verified.
- `percent_flooded_area`: Flooded area is a direct impact measurement and may summarize the events being predicted. Recommended action: Exclude from predictive features; possible target component after temporal definition.
- `corrected_percent_flooded_area`: Corrected flooded area remains an impact measurement; correction does not remove temporal leakage risk. Recommended action: Exclude from predictive features; possible target component after temporal definition.

## F. UNKNOWN / REQUIRES VERIFICATION

- `location`: The field is entirely missing and its meaning cannot be established from the cleaned data. Recommended action: Do not use until meaning and availability are verified.
- `latitude`: The coordinate field is entirely missing; no availability or event-timing assessment is possible. Recommended action: Do not use until populated and provenance is verified.
- `longitude`: The coordinate field is entirely missing; no availability or event-timing assessment is possible. Recommended action: Do not use until populated and provenance is verified.

## Policy conclusion

No current field is certified SAFE because the prediction timestamp and forecast unit are unresolved. Geographic fields may become usable after the forecast unit is fixed; impact fields remain target-only or leakage candidates.
