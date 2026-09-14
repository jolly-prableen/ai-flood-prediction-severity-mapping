# Phase 11D Flooded-Area Provenance

## Scope

Investigation only. No target, score, feature, or dataset was generated or modified.

## `corrected_percent_flooded_area`

### Verified from project data

- **Source table:** `data/raw/District_FloodedArea.csv`, processed as `data/processed/district_flooded_area_clean.csv`.
- **Original source column:** `Corrected_Percent_Flooded_Area`.
- **Processed column:** `corrected_percent_flooded_area`.
- **Rows/completeness:** 732 rows, 0 missing values, 730 unique values.
- **Observed range:** 0.0000734 to 23.62192797.
- **Observed mean/median:** approximately 2.71344 / 1.22247.
- **Spatial unit:** district-level table keyed by `Dist_Name`; 726 distinct district names.
- **Temporal fields:** no year, date, event identifier, or reference-period column is present.
- **Neighboring fields:** `Percent_Flooded_Area` and `Parmanent_Water`.
- **Cleaner behavior:** Phase 3 only renamed columns and preserved values; it did not calculate this field.

### Provenance status

**PROVENANCE UNRESOLVED.**

The repository does not establish:

- whether the field is directly observed or derived;
- the formula or algorithm producing “corrected”;
- whether correction uses `Parmanent_Water`;
- the meaning, units, and source of `Parmanent_Water`;
- the imagery/raster or other source used;
- the spatial boundary vintage;
- the temporal/reference period;
- whether the values are event-specific, annual, climatological, or another aggregate;
- quality flags, cloud treatment, permanent-water treatment, or pixel inclusion rules.

The field name and neighboring columns are not sufficient evidence to infer the calculation.

### Target suitability

- **Regression target:** DEFERRED. It is complete and numeric, but cannot be aligned to the district-week/seven-day horizon until its reference period and spatial provenance are verified.
- **Severity_Score component:** DEFERRED. It is a strong candidate only if it represents the same target observation period and geography selected for the score.
- **Predictive feature:** NOT SAFE. If it represents the flood outcome or post-event flooded extent, use as a feature would directly leak the target.

## `percent_flooded_area`

### Verified from project data

- **Source table/column:** `data/raw/District_FloodedArea.csv`, `Percent_Flooded_Area`.
- **Processed column:** `percent_flooded_area`.
- **Completeness:** 732/732 present; 730 unique values.
- **Range/summary:** 0.001739235 to 32.6562; mean approximately 3.37413; median approximately 1.69784.
- **Unit:** the name suggests percent of district area, but the exact method and unit are not documented beyond the header.
- **Spatial/temporal level:** district-level; temporal/reference period absent.

### Decision

**DEFERRED.** It is likely the uncorrected counterpart of the corrected field, but that relationship is not documented. Do not include both in a score unless official metadata proves they represent distinct constructs. It is not a predictive feature for the same flood outcome.

## Evidence required before approval

Obtain the official IFI-Impacts v3 publication supplement, data dictionary, source code, or table-specific metadata documenting:

1. calculation and correction formula;
2. source imagery/raster and processing date;
3. meaning and units of `Parmanent_Water`;
4. spatial boundary/vintage;
5. temporal/reference period;
6. event versus aggregate semantics;
7. quality and missing-pixel rules.

Until then, both flooded-area fields remain target candidates only, not approved target components and never predictive features.
