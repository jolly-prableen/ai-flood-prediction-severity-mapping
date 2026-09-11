# Phase 11D Final Target Component Decision

## Status

Investigation only. No target columns, Severity_Score, or Severity_Class were generated.

## Component decisions

| Component | Source/evidence | Quality and semantics | Decision | Reason |
|---|---|---|---|---|
| `corrected_percent_flooded_area` | District_FloodedArea.csv, 732/732 present | District aggregate; reference period and correction method undocumented | **DEFERRED** | Complete numeric candidate, but provenance and district-week compatibility are unresolved |
| `percent_flooded_area` | District_FloodedArea.csv, 732/732 present | District aggregate; likely related to corrected field; reference period undocumented | **DEFERRED** | Do not include with corrected field until redundancy and calculation relationship are documented |
| `duration_days` | India_Flood_Inventory_v3.csv, 6,857/6,876 present | Event-level days; 19 missing; 17 raw date contradictions; 155 noncontradictory rows inconsistent with apparent inclusive duration convention | **DEFERRED** | Requires date/interval review and event-to-district-week aggregation policy |
| Event `human_fatality` | India_Flood_Inventory_v3.csv | Event-level; 45.17% missing; count units appear to be persons but source semantics require verification | **DEFERRED** | Potential impact component, but reporting missingness and target-level alignment are unresolved |
| District `human_fatality` | District_FloodImpact.csv | District aggregate; complete; reference period and aggregation method undocumented | **DEFERRED** | Cannot be combined with event-level impacts or aligned to weeks without provenance |
| Event `human_injured` | India_Flood_Inventory_v3.csv | Event-level; 84.61% missing | **EXCLUDED** | Excessive missingness for primary score; may be reconsidered only in a separately justified sensitivity analysis |
| District `human_injured` | District_FloodImpact.csv | District aggregate; complete; reference period undocumented | **DEFERRED** | Semantically possible but temporal/aggregation provenance is unresolved |
| `human_displaced` | India_Flood_Inventory_v3.csv | 98.23% missing; string representation; units/encoding undocumented | **EXCLUDED** | Too incomplete and semantically unresolved for the primary score |
| `animal_fatality` | India_Flood_Inventory_v3.csv | 91.70% missing; string representation; units unresolved | **EXCLUDED** | Too incomplete and semantically unresolved for the primary score |
| `description_of_casualties_injured` | India_Flood_Inventory_v3.csv | 52.49% missing free text | **EXCLUDED** | Requires a validated coding rubric before any numeric use |
| `extent_of_damage` | India_Flood_Inventory_v3.csv | 45.39% missing free text; coding scale undocumented | **EXCLUDED** | No defensible numeric transformation is currently documented |
| `mean_flood_duration` | District_FloodImpact.csv | 11/732 missing; district aggregate; reference period unknown | **DEFERRED** | Could duplicate duration information and cannot be aligned to event weeks yet |
| `severity` | India_Flood_Inventory_v3.csv | 100% missing | **EXCLUDED** | Currently unusable and semantically undefined |
| `area_affected` | India_Flood_Inventory_v3.csv | 100% missing; units undefined | **EXCLUDED** | Currently unusable and semantically undefined |

## Approved candidates

**APPROVED_CANDIDATE: none.**

No component has sufficient provenance, temporal alignment, and semantic evidence to be frozen as an approved Severity_Score input.

## Redundancy decision

`corrected_percent_flooded_area` and `percent_flooded_area` should be treated as potentially redundant until official documentation proves otherwise. Do not include both in a score by default. Select one only after the correction formula, source period, spatial unit, and intended interpretation are verified.

## Target leakage

All candidate impact components are known during or after the flood or have an undocumented aggregate reference period. They may be used for target construction after approval, but must never be predictive features for the same outcome. Identifiers and event dates are also excluded from predictive features.

## Required next evidence

- Official IFI flooded-area metadata/publication supplement/source code.
- Reference periods and spatial vintage for both district aggregate tables.
- Resolution of 17 raw date contradictions and 155 duration inconsistencies.
- Approved district-week/event aggregation rule.
- Independent GFM coverage-qualified observation frame for any Flood_Binary target.
- Approved score component registry and training-period-only normalization method.
