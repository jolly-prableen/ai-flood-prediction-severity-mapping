# Severity_Score Methodology v1

## Status

Methodology only. No score, component columns, normalization parameters, or labels are generated here.

## Confirmed evidence and constraints

The audit found these actual impact-like fields:

| Component | Source | Availability | Missingness/quality | Post-event? | Methodology decision |
|---|---|---|---|---|---|
| `corrected_percent_flooded_area` | `district_flooded_area_clean.csv` | 732/732 present | 0% missing; 730 unique; mean 2.7134; median 1.2225; range 0.0000734–23.6219 | During/after or reference period unknown | Strong candidate; require provenance/reference-period approval |
| `percent_flooded_area` | `district_flooded_area_clean.csv` | 732/732 present | 0% missing; 730 unique; mean 3.3741; median 1.6978; range 0.001739–32.6562 | During/after or reference period unknown | Candidate; likely redundant with corrected measure; do not include both without documented rationale |
| `duration_days` | `ifi_event_clean.csv` | 6,857/6,876 present | 19 missing; min 1, max 365; source units days | After event | Candidate after event-level target definition; cannot be a feature |
| `human_fatality` | Event inventory and district aggregate | 3,770/6,876 event values; district table complete | Event missing 45.17%; district aggregate has 0 missing; units/reference period require verification | During/after | Candidate only with explicit level/reference-period choice; do not combine event and aggregate values automatically |
| `human_injured` | Event inventory and district aggregate | 1,058/6,876 event values; district table complete | Event missing 84.61%; district aggregate has 0 missing | During/after | Candidate only after aggregation/provenance review |
| `human_displaced` | `ifi_event_clean.csv` | 122/6,876 nonmissing | 98.23% missing; string representation | During/after | Do not include in the primary score unless coding and missingness are resolved |
| `animal_fatality` | `ifi_event_clean.csv` | 571/6,876 nonmissing | 91.70% missing; string representation | During/after | Optional sensitivity component only after coding review; not primary |
| `description_of_casualties_injured` | `ifi_event_clean.csv` | 3,267/6,876 nonmissing | 52.49% missing; free text | After/during | Do not score directly; requires a separately validated coding rubric |
| `extent_of_damage` | `ifi_event_clean.csv` | 3,755/6,876 nonmissing | 45.39% missing; free text | After/during | Do not score directly without a documented coding rubric and validation |
| `mean_flood_duration` | `district_flood_impact_clean.csv` | 721/732 present | 1.50% missing; district aggregate; reference period unknown | Likely after event | Candidate only if its reference period matches the target observation |
| `severity` | `ifi_event_clean.csv` | 0/6,876 present | 100% missing | Unknown, outcome-like | Exclude until populated and defined |
| `area_affected` | `ifi_event_clean.csv` | 0/6,876 present | 100% missing; unit unknown | During/after | Exclude until populated and defined |

## Recommended score construction approach

Do not assign arbitrary weights or manually choose a 0–100 formula. The defensible first implementation is a **predeclared normalized composite** with a transparent component registry:

1. Select one target level: district-event or district-week. Do not mix levels.
2. Select components only after confirming common reference period and units.
3. Define missingness separately from zero; missing impact is not zero impact.
4. Transform each approved numeric component using a documented monotonic transform, such as `log1p` for nonnegative counts, only after review.
5. Normalize each component using parameters fitted on the target-construction training period only; do not fit using future/validation/test observations.
6. Combine components using equal weights only as a declared provisional composite, not as a claim that impacts are equally important.
7. Publish component coverage, weights, direction, and sensitivity results alongside the score.

If equal weighting is not scientifically acceptable, use an approved data-driven method such as a prespecified latent-factor/PCA analysis fitted only on the target-construction training period. The method must be chosen before examining downstream model performance, and the resulting loadings must be reported. Do not use supervised weights derived from predictors or labels without a separate methodological approval.

## Recommended primary component set

Subject to provenance approval, the first score candidate should use:

- one flooded-area measure, preferably `corrected_percent_flooded_area`;
- `duration_days` or a verified compatible duration aggregate, not both unless nonredundancy is shown;
- human fatalities and injuries only if the target level and reference period are aligned.

Do not include both flooded-area measures by default because they may represent corrected and uncorrected versions of the same construct. Do not include high-missingness displacement/animal fields in the primary score. Free-text damage/casualty fields require independent coding and should remain excluded initially.

## Target versus feature rule

All approved score components are post-event or outcome-like and are target-only. They must never become predictive features for the same flood outcome. `population` and `parmanent_water` are possible baseline predictors after vintage verification, not severity components.

## Open questions

- What exactly does `corrected_percent_flooded_area` correct, and for what reference period?
- Are district flooded-area values event-specific, annual, or another aggregate?
- Can event-level and district-level impacts be reconciled to one target unit?
- How should missing impacts be handled without interpreting reporting absence as zero?
- What score direction and interpretation are required by the project?
- Which component registry and weighting method will the team approve?
