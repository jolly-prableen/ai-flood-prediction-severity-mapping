# Phase 11A Severity Component Review

## Status

Investigation only. No Severity_Score or component values are generated.

## Component review

| Component | Evidence and quality | Post-event status | Normalization feasibility | Decision |
|---|---|---|---|---|
| `corrected_percent_flooded_area` | District table; 732/732 present; 730 unique; range 0.0000734–23.6219; reference period and correction method unknown | During/after or unknown | Numeric normalization is feasible after provenance approval | **DEFER** pending provenance; strongest complete candidate |
| `percent_flooded_area` | District table; 732/732 present; 730 unique; range 0.001739–32.6562; reference period unknown | During/after or unknown | Numeric normalization feasible after provenance approval | **DEFER**; likely redundant with corrected field |
| `duration_days` | Event table; 6,857/6,876 present; range 1–365 days; 19 missing | Post-event | `log1p` or robust scaling possible after target-level approval | **DEFER**; event-level candidate only after date consistency review |
| `human_fatality` | Event table 45.17% missing; district aggregate complete but reference period unknown; counts have nonnegative values | During/after | Counts can use `log1p`, but missingness/reporting bias is material | **DEFER**; choose one aligned source level, do not combine automatically |
| `human_injured` | Event table 84.61% missing; district aggregate complete but reference period unknown | During/after | Counts can use `log1p`, but high missingness and reporting bias are material | **EXCLUDE FROM PRIMARY SCORE / DEFER SENSITIVITY** |
| `human_displaced` | Event table 98.23% missing; string representation; units/encoding unresolved | During/after | Not reliable without parsing and missingness study | **EXCLUDE** from primary score |
| `animal_fatality` | Event table 91.70% missing; string representation; units unresolved | During/after | Not reliable without parsing and missingness study | **EXCLUDE** from primary score |
| `description_of_casualties_injured` | 52.49% missing; free text | After/during | Requires independently validated coding rubric | **EXCLUDE** until coded and validated |
| `extent_of_damage` | 45.39% missing; free text; no documented coding scale | After/during | Requires validated categorical/text coding | **EXCLUDE** until coded and validated |
| `mean_flood_duration` | District aggregate; 11/732 missing; reference period and event alignment unknown | Likely post-event | Numeric normalization feasible after reference-period approval | **DEFER**; do not combine with event duration automatically |
| `severity` | Event table 100% missing | Outcome-like, timing unknown | Not applicable currently | **EXCLUDE** until populated and defined |
| `area_affected` | Event table 100% missing; units unknown | During/after | Not applicable currently | **EXCLUDE** until populated and defined |
| `population` | District aggregate; complete; reference year/provenance unknown | Potential baseline | Numeric normalization feasible after vintage verification | **NOT A SEVERITY COMPONENT**; possible predictive exposure feature only after verification |
| `parmanent_water` | District aggregate; complete; source units/vintage/correction role unknown | Potential baseline | Numeric normalization feasible after provenance verification | **NOT A SEVERITY COMPONENT**; possible predictive feature only after verification |

## Missingness and zero policy

No component may treat missing as zero without evidence that the source uses zero to encode a true zero. The district aggregate human-impact fields contain explicit zeros, but their source semantics still require verification. Event-level missing impact reports may reflect unknown or unreported impact, not absence of impact.

## Recommended component registry

Before score generation, approve a registry containing one flooded-area measure, a compatible duration measure, and only impact counts whose reference period and reporting quality are acceptable. Start with a provenance-gated analysis of corrected flooded area, duration, and human fatality; evaluate human injury as sensitivity only. Do not include both corrected and uncorrected flooded-area measures by default.

## Leakage and availability

Every approved severity component is known during or after the flood and is therefore target-only. None may enter predictive features for the same prediction task. Normalization parameters, if used for the score, must be fitted on the target-construction training period only.

## Required unresolved evidence

- Official metadata for both district flooded-area fields and `Parmanent_Water`.
- Reference period and spatial vintage for district aggregates.
- Event/district alignment rule.
- Impact reporting and missingness semantics.
- Approved score formula or data-driven weighting method.
