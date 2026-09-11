# Phase 10 Target Audit

## A. Purpose

This audit inventories the cleaned IFI columns and evaluates their eligibility for future target construction. It does not create `Flood_Binary`, `Severity_Score`, `Severity_Class`, labels, splits, or model inputs. Post-event fields may be target components but are prohibited predictive features.

## B. Files inspected

- `data/processed/ifi_event_clean.csv`: 6,876 rows, 23 columns.
- `data/processed/district_flood_impact_clean.csv`: 732 rows, 5 columns.
- `data/processed/district_flooded_area_clean.csv`: 732 rows, 4 columns.

## C. Complete column inventory

| file | column | dtype | rows | missing_count | missing_pct | unique_count | min | max | mean | median | units | category | post_event_status | prediction_time_status | target_candidate_status | leakage_risk | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ifi_event_clean.csv | unnamed_0 | int64 | 6876 | 0 | 0.0 | 6876 | 563 | 7438 | 4000.5 | 4000.5 | not documented | identifier | UNKNOWN | not a predictive feature | NO | HIGH | Identifier/provenance field; retain for grouping or audit only, never as a model feature. |
| ifi_event_clean.csv | uei | str | 6876 | 0 | 0.0 | 6876 |  |  |  |  | not documented | identifier | UNKNOWN | not a predictive feature | NO | HIGH | Identifier/provenance field; retain for grouping or audit only, never as a model feature. |
| ifi_event_clean.csv | start_date | str | 6876 | 20 | 0.2909 | 3685 | 1967-01-08T00:00:00 | 2023-12-09T00:00:00 |  |  | not documented | temporal information | event reference | start is target-time; end is after event | NO | HIGH | Event chronology only; not a predictive feature. |
| ifi_event_clean.csv | end_date | str | 6876 | 20 | 0.2909 | 3693 | 1967-07-28T00:00:00 | 2023-12-09T00:00:00 |  |  | not documented | temporal information | event reference | start is target-time; end is after event | NO | HIGH | Event chronology only; not a predictive feature. |
| ifi_event_clean.csv | duration_days | float64 | 6876 | 19 | 0.2763 | 62 | 1.0 | 365.0 | 3.6130961061688787 | 1.0 | days (source label) | temporal information | post-event | after event | TARGET_ONLY_CANDIDATE | HIGH | Observed event duration; potentially usable in a future severity/impact target after definition review. |
| ifi_event_clean.csv | main_cause | str | 6876 | 31 | 0.4508 | 580 |  |  |  |  | not documented | event metadata | unknown | unknown; may be retrospective | NO | MEDIUM | Cause coding time and controlled vocabulary are undocumented; not a target candidate by itself. |
| ifi_event_clean.csv | location | float64 | 6876 | 6876 | 100.0 | 1 |  |  |  |  | not documented | location/geography | UNKNOWN | potentially before event, but source timing/forecast-unit availability is unresolved | NO | MEDIUM | Geographic context or event-record location; do not treat observed event membership as a complete forecast frame. Entirely missing in this file. |
| ifi_event_clean.csv | districts | str | 6876 | 60 | 0.8726 | 2609 |  |  |  |  | not documented | location/geography | UNKNOWN | potentially before event, but source timing/forecast-unit availability is unresolved | NO | MEDIUM | Geographic context or event-record location; do not treat observed event membership as a complete forecast frame. |
| ifi_event_clean.csv | state | str | 6876 | 0 | 0.0 | 78 |  |  |  |  | not documented | location/geography | UNKNOWN | potentially before event, but source timing/forecast-unit availability is unresolved | NO | MEDIUM | Geographic context or event-record location; do not treat observed event membership as a complete forecast frame. |
| ifi_event_clean.csv | latitude | float64 | 6876 | 6876 | 100.0 | 1 |  |  |  |  | not documented | location/geography | UNKNOWN | potentially before event, but source timing/forecast-unit availability is unresolved | NO | MEDIUM | Geographic context or event-record location; do not treat observed event membership as a complete forecast frame. Entirely missing in this file. |
| ifi_event_clean.csv | longitude | float64 | 6876 | 6876 | 100.0 | 1 |  |  |  |  | not documented | location/geography | UNKNOWN | potentially before event, but source timing/forecast-unit availability is unresolved | NO | MEDIUM | Geographic context or event-record location; do not treat observed event membership as a complete forecast frame. Entirely missing in this file. |
| ifi_event_clean.csv | severity | float64 | 6876 | 6876 | 100.0 | 1 |  |  |  |  | source unit undocumented | other | during/after event | not available before event | TARGET_ONLY_CANDIDATE_BUT_CURRENTLY_UNUSABLE | HIGH | Direct source field is entirely missing in the cleaned inventory; possible target source only if later populated and defined. Entirely missing in this file. |
| ifi_event_clean.csv | area_affected | float64 | 6876 | 6876 | 100.0 | 1 |  |  |  |  | source unit undocumented | flooded area | during/after event | not available before event | TARGET_ONLY_CANDIDATE_BUT_CURRENTLY_UNUSABLE | HIGH | Direct source field is entirely missing in the cleaned inventory; possible target source only if later populated and defined. Entirely missing in this file. |
| ifi_event_clean.csv | human_fatality | float64 | 6876 | 3106 | 45.1716 | 184 | 1.0 | 5000.0 | 18.751458885941645 | 3.0 | persons/animals; source units require verification | human impact | during/after event | not available before event | TARGET_ONLY_CANDIDATE | HIGH | Post-event consequence field; may contribute to Severity_Score but cannot be a predictive feature. |
| ifi_event_clean.csv | human_injured | float64 | 6876 | 5818 | 84.6131 | 63 | 1.0 | 2000.0 | 10.998109640831759 | 3.0 | persons/animals; source units require verification | human impact | during/after event | not available before event | TARGET_ONLY_CANDIDATE | HIGH | Post-event consequence field; may contribute to Severity_Score but cannot be a predictive feature. |
| ifi_event_clean.csv | human_displaced | str | 6876 | 6754 | 98.2257 | 24 |  |  |  |  | persons/animals; source units require verification | human impact | during/after event | not available before event | TARGET_ONLY_CANDIDATE | HIGH | Post-event consequence field; may contribute to Severity_Score but cannot be a predictive feature. |
| ifi_event_clean.csv | animal_fatality | str | 6876 | 6305 | 91.6958 | 248 |  |  |  |  | persons/animals; source units require verification | environmental impact | during/after event | not available before event | TARGET_ONLY_CANDIDATE | HIGH | Post-event consequence field; may contribute to Severity_Score but cannot be a predictive feature. |
| ifi_event_clean.csv | description_of_casualties_injured | str | 6876 | 3609 | 52.4869 | 2488 |  |  |  |  | not documented | human impact | after/during event | not available before event | TARGET_ONLY_CANDIDATE | HIGH | Free-text post-event evidence; requires a predeclared coding rubric before target construction. |
| ifi_event_clean.csv | extent_of_damage | str | 6876 | 3121 | 45.3898 | 3613 |  |  |  |  | not documented | infrastructure/property impact | after/during event | not available before event | TARGET_ONLY_CANDIDATE | HIGH | Free-text post-event evidence; requires a predeclared coding rubric before target construction. |
| ifi_event_clean.csv | event_source | str | 6876 | 0 | 0.0 | 1 |  |  |  |  | not documented | event metadata | UNKNOWN | collection metadata, not a physical predictor | NO | MEDIUM | Source is constant in the current file and should not be used as a feature or target. |
| ifi_event_clean.csv | event_souce_id | float64 | 6876 | 6876 | 100.0 | 1 |  |  |  |  | not documented | identifier | UNKNOWN | not a predictive feature | NO | HIGH | Identifier/provenance field; retain for grouping or audit only, never as a model feature. Entirely missing in this file. |
| ifi_event_clean.csv | district_lgd_codes | str | 6876 | 304 | 4.4212 | 2483 |  |  |  |  | not documented | identifier | UNKNOWN | not a predictive feature | NO | HIGH | Identifier/provenance field; retain for grouping or audit only, never as a model feature. |
| ifi_event_clean.csv | state_codes | str | 6876 | 258 | 3.7522 | 66 |  |  |  |  | not documented | identifier | UNKNOWN | not a predictive feature | NO | HIGH | Identifier/provenance field; retain for grouping or audit only, never as a model feature. |
| district_flood_impact_clean.csv | dist_name | str | 732 | 0 | 0.0 | 726 |  |  |  |  | not documented | location/geography | UNKNOWN | potentially before event, but source timing/forecast-unit availability is unresolved | NO | MEDIUM | Geographic context or event-record location; do not treat observed event membership as a complete forecast frame. |
| district_flood_impact_clean.csv | human_fatality | int64 | 732 | 0 | 0.0 | 234 | 0 | 1726 | 89.93032786885246 | 50.0 | persons/animals; source units require verification | human impact | during/after event | not available before event | TARGET_ONLY_CANDIDATE | HIGH | Post-event consequence field; may contribute to Severity_Score but cannot be a predictive feature. |
| district_flood_impact_clean.csv | human_injured | int64 | 732 | 0 | 0.0 | 85 | 0 | 671 | 15.454918032786885 | 3.0 | persons/animals; source units require verification | human impact | during/after event | not available before event | TARGET_ONLY_CANDIDATE | HIGH | Post-event consequence field; may contribute to Severity_Score but cannot be a predictive feature. |
| district_flood_impact_clean.csv | population | int64 | 732 | 0 | 0.0 | 732 | 7110 | 13403998 | 1922614.43852459 | 1519773.5 | persons | human impact | baseline if vintage is verified | potentially before event; reference year unknown | POTENTIAL_FEATURE_AFTER_VERIFICATION | MEDIUM | Potential exposure covariate only after source vintage and district alignment are verified; not an impact target. |
| district_flood_impact_clean.csv | mean_flood_duration | float64 | 732 | 11 | 1.5027 | 36 | 1.0 | 35.0 | 10.816920943134535 | 7.0 | days (source label) | flooded area | likely post-event; reference period unknown | reference period unknown | TARGET_ONLY_CANDIDATE | HIGH | District aggregate outcome-like measure with undocumented reference period; do not merge into event features. |
| district_flooded_area_clean.csv | dist_name | str | 732 | 0 | 0.0 | 726 |  |  |  |  | not documented | location/geography | UNKNOWN | potentially before event, but source timing/forecast-unit availability is unresolved | NO | MEDIUM | Geographic context or event-record location; do not treat observed event membership as a complete forecast frame. |
| district_flooded_area_clean.csv | percent_flooded_area | float64 | 732 | 0 | 0.0 | 730 | 0.001739235 | 32.6562 | 3.374125593980874 | 1.6978431415 | percent of district area (source label; exact method requires verification) | flooded area | during/after event or unknown reference period | reference period unknown; not safe before event | TARGET_ONLY_CANDIDATE | HIGH | District aggregate flooded-area measurement; possible regression target and Severity_Score component, not a predictive feature. |
| district_flooded_area_clean.csv | parmanent_water | float64 | 732 | 0 | 0.0 | 673 | 0.0 | 29.67097127 | 0.6640254943852459 | 0.2389145345 | source unit undocumented | environmental impact | baseline if vintage is verified | potentially before event; vintage unknown | POTENTIAL_FEATURE_AFTER_VERIFICATION | MEDIUM | Potential static water feature; spelling and provenance are source-defined and require verification. |
| district_flooded_area_clean.csv | corrected_percent_flooded_area | float64 | 732 | 0 | 0.0 | 730 | 7.34e-05 | 23.62192797 | 2.7134377777404373 | 1.2224718365 | percent of district area (source label; exact method requires verification) | flooded area | during/after event or unknown reference period | reference period unknown; not safe before event | TARGET_ONLY_CANDIDATE | HIGH | District aggregate flooded-area measurement; possible regression target and Severity_Score component, not a predictive feature. |

## D. Candidate target variables

Potential candidates actually present are `duration_days`, event human/animal impact fields, casualty and damage text, `percent_flooded_area`, `corrected_percent_flooded_area`, `mean_flood_duration`, and the source fields `severity` and `area_affected` (currently entirely missing). Event dates are reference fields for occurrence assignment, not severity measurements.

## E. Human-impact variables

The event inventory contains `human_fatality`, `human_injured`, `human_displaced`, `animal_fatality`, and casualty/injury descriptions. The district impact table contains aggregate `human_fatality` and `human_injured`. These are post-event or during-event consequences and are target-only candidates after unit, aggregation, and reference-period review.

## F. Flooded-area variables

`percent_flooded_area` and `corrected_percent_flooded_area` are directly present in `district_flooded_area_clean.csv`, complete across 732 rows, and have 730 unique values each. They are district-level aggregate measurements with no documented reference period in the current repository. `corrected_percent_flooded_area` is suitable as a possible regression target after provenance/method verification and may contribute to Severity_Score; using it as a feature would be direct target leakage.

## G. Post-event variables

Post-event or outcome-like fields include end date, duration, fatalities, injuries, displacement, animal fatalities, casualty descriptions, damage extent, flooded-area percentages, corrected flooded area, mean flood duration, and likely affected area/severity fields. They must not be predictive features.

## H. Missingness and quality assessment

The event inventory has 100% missing `location`, `latitude`, `longitude`, `severity`, `area_affected`, and `event_souce_id`; these cannot currently support target construction. `human_injured` is 84.61% missing, `human_displaced` 98.23% missing, and `animal_fatality` 91.70% missing. District `mean_flood_duration` has 11 missing values (1.50%). No missing values occur in the flooded-area table.

## I. Identifier assessment

`uei` is unique and suitable for event grouping, duplicate checks, and target-reference linkage only. `unnamed_0`, source IDs, LGD/code strings, district names, and state names must not become model features. District plus year is not a unique event identity.

## J. Target-leakage assessment

All impact and post-event fields are target-only candidates or unusable, not predictors. The district aggregate tables cannot be used as predictors until their reference period and event overlap are established. Absence from the event inventory cannot create a negative target.

## K. Variables potentially suitable for Severity_Score

Strongest candidates for later review are `corrected_percent_flooded_area`, `percent_flooded_area`, `duration_days`, `human_fatality`, `human_injured`, and possibly displacement/damage components if their missingness and semantics are resolved. A score formula, weighting, units, aggregation level, and missingness policy must be approved first. `corrected_percent_flooded_area` is the strongest currently complete direct impact candidate, but its reference period and correction method remain undocumented.

## L. Variables that should NOT be used

Do not use `uei`, row indices, source IDs, event dates as predictors, any post-event impact field, flooded-area measures, damage/casualty text, unverified aggregate fields, or future-derived statistics as predictive features. Do not use entirely missing severity/area fields until their source values are restored and defined.

## M. Open methodological questions

- What exact reference period and derivation produced the district flooded-area tables?
- Is `corrected_percent_flooded_area` directly observed, remotely corrected, or derived from another source, and what does it correct?
- Which impact variables and units should enter Severity_Score, and how should missing impacts be handled without interpreting missing as zero?
- Will targets be district-week or district-event, and how will multi-district events be assigned?
- What independent non-event frame will support Flood_Binary?
- How will the 20 missing event start dates be handled for target assignment?

## N. Recommendation for next phase

Do not generate targets yet. First document the flooded-area provenance/reference period, approve the Severity_Score rubric, establish the district-week observation and negative frame, and decide the missing-impact policy. Keep all audited columns available for provenance but exclude post-event fields from predictive features.
