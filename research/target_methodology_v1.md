# Target Methodology v1

## Status and scope

This document freezes methodology design only. It creates no target columns, labels, observations, classes, scores, splits, or model artifacts.

## Confirmed facts

- The approved prediction design is district-level, district-week, 26-week history, and a seven-day horizon.
- IFI contains recorded flood events only, with unique `uei` event identifiers.
- IFI absence is not verified non-flood status.
- The event inventory has 20 missing start dates and 20 missing end dates.
- District plus year is not a unique event identity.
- `corrected_percent_flooded_area` is complete in the district flooded-area table, but its provenance/reference period is not documented.
- Event impacts are post-event or outcome-like and may be target components, never same-task predictive features.

## Target set

### Flood_Binary

Use the methodology in [flood_binary_methodology_v1.md](flood_binary_methodology_v1.md): construct a district-week observation frame, assign positives from verified IFI event overlap in the seven-day forecast window, and assign negatives only from an independent documented non-event frame. Do not use IFI absence as zero.

### Severity_Score

Use the methodology in [severity_score_methodology_v1.md](severity_score_methodology_v1.md): choose one target level, approve compatible outcome components, preserve missingness, normalize with training-period-only parameters, and use a predeclared transparent composite or approved data-driven latent-factor method. Do not invent weights.

### Severity_Class

Derive classes only after Severity_Score is frozen and its distribution is known. Recommended method: evaluate quantile classes as the initial reproducible option, with class count selected by minimum class-size and stability criteria; compare against distribution-based or domain thresholds. Do not use arbitrary fixed numeric cutoffs. If quantile classes are used, quantile boundaries must be fitted on the target-construction training period only and frozen for later evaluation/inference.

### Corrected_Percent_Flooded_Area

Treat as a separate candidate regression target at district level only after its provenance, derivation, reference period, and relationship to the boundary vintage are verified. It may be a Severity_Score component after the same approval. It must never be a predictive feature when it represents the outcome.

## Target aggregation design

The eventual observation frame should be district-week. Each IFI `uei` whose verified event interval overlaps the seven-day forecast window is retained as event metadata. Multiple events in the same district-week are not silently collapsed; the implementation must define whether the outcome is any-event occurrence, event count metadata, maximum impact, or an approved aggregate. Events with missing start dates cannot be assigned automatically.

Event-level impacts and district aggregate tables must not be combined unless their geography and reference period are proven compatible. District aggregate tables currently have no year/event identifier and remain target-source candidates only.

## Temporal and leakage rules

- Features stop at the prediction cutoff.
- Event dates, duration, impacts, flooded-area values, damage, casualty information, and any future observations used in target assignment are target/reference data only.
- `uei` is for grouping and audit only.
- No negative label is created from an absent IFI record.
- Target transformations, normalization, class boundaries, and latent-factor parameters must be fitted only on the target-construction training period.

## Methodological decisions still required

1. Approve the independent district-week event/non-event frame.
2. Approve the weekly calendar and date-only event-overlap rule.
3. Approve the handling of missing event dates.
4. Verify flooded-area provenance and reference period.
5. Select district-event versus district-week severity target level.
6. Approve the component registry and weighting/latent-factor method.
7. Approve the class-count and stability rule for Severity_Class.
8. Define how multiple overlapping events contribute to district-week targets.

## Exact inputs required for target-generation phase

- Versioned district-week observation frame with an independent non-event source.
- Final reviewed district crosswalk and approved boundary vintage.
- IFI event dates and `uei` linkage, with missing-date policy applied.
- Provenance metadata for flooded-area tables and impact aggregates.
- Approved Severity_Score component registry, transforms, missingness policy, and fitting period.
- Approved Severity_Class method and training-only class-boundary procedure.
- Explicit target-generation configuration recorded before any labels are materialized.
