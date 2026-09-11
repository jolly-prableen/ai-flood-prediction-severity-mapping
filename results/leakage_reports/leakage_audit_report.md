# IFI Data Leakage Audit Report

Phase 4 only. Cleaned files were read but not modified. No targets, splits, SMOTE, models, or external data were created.

## 1. Prediction-time definition

The operational prediction timestamp and lead time are unresolved. This audit conservatively assumes pre-event forecasting relative to `start_date`; `start_date` is treated as event-reference information, not a feature.

## 2. Twelve leakage checks

| Check | Finding | Status |
|---|---|---|
| Target leakage | Event date, severity, affected area, and impact fields can directly represent the outcome. | Confirmed for feature use |
| Post-event information | Fatalities, injuries, displacement, damage, duration, and flooded area are outcome-like. | Confirmed for feature use |
| Temporal leakage | Aggregate reference periods and forecast horizon are undocumented; future observations cannot yet be separated safely. | Unknown / requires verification |
| Train/test contamination | UEI is unique and district-year repeats; later partitioning must group by UEI/event. | Caution |
| Duplicate/near-duplicate leakage | Exact duplicates are absent; repeated district-year records are multiple events, not safe duplicates. | Caution |
| Aggregate leakage | District flood impact and flooded-area tables may summarize the same outcomes. | Confirmed risk |
| Target-construction leakage | Impact fields may be valid target components but invalid features. | Confirmed distinction required |
| Identifier leakage | UEI, row index, source ID, and code fields can enable memorization or provenance leakage. | Caution / exclude |
| Spatial leakage | Event rows contain observed districts/states; aggregate tables lack state and time context. | Unknown / requires verification |
| Future-derived statistics | District aggregates have no documented period; future inclusion cannot be ruled out. | Unknown / requires verification |
| Dataset/merge leakage | No merge was performed; a name-only merge would duplicate or import outcome information. | Merge blocked |
| Sampling leakage | Inventory contains flood events but no explicit non-event records; binary occurrence modeling would be structurally biased without a negative-sample design. | Confirmed design issue |

## 3. Audit counts

- Columns audited: **32**
- SAFE: **0**
- CAUTION: **13**
- LEAKAGE: **16**
- UNKNOWN / REQUIRES VERIFICATION: **3**

## 4. Confirmed and possible leakage

Confirmed feature exclusions: event dates, duration, severity, affected area, human/animal impacts, casualty descriptions, damage extent, flooded-area percentages, corrected flooded-area percentages, and mean flood duration.
Possible leakage requiring timing verification: cause, population, permanent water, source metadata, identifiers, geographic fields, and all district aggregates.

## 5. Target candidates

| variable | meaning | occurrence_or_impact | availability | feature_leakage | target_use | notes |
| --- | --- | --- | --- | --- | --- | --- |
| start_date | Recorded flood event start date | occurrence | event/target time | LEAKAGE | Possible event reference/label boundary; not a feature | A Flood_Binary target also requires non-event records, which are not present here. |
| end_date | Recorded flood event end date | occurrence/temporal extent | after event | LEAKAGE | Possible duration/reference construction after definition | Not available for pre-event forecasting. |
| duration_days | Recorded event duration in days | impact/temporal extent | after event | LEAKAGE | Possible Severity_Class or impact target component | Target semantics and timing require verification. |
| severity | Source field named severity | impact/severity | unknown; entirely missing | LEAKAGE if populated | Possible direct target source only after source verification | No usable values are currently present. |
| area_affected | Source field named area affected | impact | during/after event; currently missing | LEAKAGE if populated | Possible impact/severity target component | Units and definition require verification. |
| human_fatality | Human fatality count or district aggregate | impact | during/after event | LEAKAGE | Possible impact target component | Event and district tables must not be combined without temporal provenance. |
| human_injured | Human injury count or district aggregate | impact | during/after event | LEAKAGE | Possible impact target component | Aggregation and time period require verification. |
| percent_flooded_area / corrected_percent_flooded_area | District flooded-area measurements | impact/severity | during/after event or unknown reference period | LEAKAGE | Possible Severity_Class or Severity_Score component | No target is created in Phase 4. |
| mean_flood_duration | District mean flood duration | impact | unknown reference period; likely after event | LEAKAGE | Possible aggregate impact target component | Source period is not documented. |

## 6. Event identity and temporal ordering

Use UEI for event identity and grouping, not as a feature. District + year is not unique. Usable event dates span 1967–2023, but 20 start dates and 20 end dates are missing. Multiple events occur in the same district-year. A chronological split may be possible later, but only after defining the forecast horizon and handling missing dates.

## 7. Spatial, aggregate, and merge findings

The district tables have no year, event ID, or state field. Their reference periods are unknown. They must not be merged into the event inventory until a verified time/geography crosswalk proves that they do not summarize the target event.

## 8. Recommended exclusions

Exclude all post-event impacts, event dates used as predictors, identifiers, source metadata, and unverified aggregate fields from the initial predictive feature set. Retain them for target construction or provenance only where their semantics and timing are approved.

## 9. Unresolved questions

- What exact lead time and prediction timestamp define the operational forecast?
- What reference periods generated the district aggregates?
- Is UEI officially defined as a stable event identifier?
- How will non-event/negative examples be sampled for Flood_Binary?
- Which fields are genuinely available before the flood rather than coded retrospectively?