# Phase 11A Flooded-Area Provenance Investigation

## Field under investigation

`corrected_percent_flooded_area`

## Verified from project data

- Source file: `data/raw/District_FloodedArea.csv`, retained as `data/processed/district_flooded_area_clean.csv`.
- Processed column: `corrected_percent_flooded_area`.
- Rows: 732.
- Missing values: 0.
- Unique values: 730.
- Range: 0.0000734 to 23.62192797.
- Mean: approximately 2.71344.
- Median: approximately 1.22247.
- The neighboring fields are `Dist_Name`, `Percent_Flooded_Area`, and `Parmanent_Water`.
- The table has 726 distinct district names and no year, event identifier, event date, or documented reference-period column.
- The Phase 3 cleaning log confirms that the raw field was retained and that no imputation or derivation was performed by the project cleaner.

## Provenance status

**PROVENANCE UNRESOLVED.**

The current repository establishes only that the field is directly present in the supplied IFI district flooded-area CSV. It does not establish whether the value is:

- directly observed from a flood map;
- corrected from `Percent_Flooded_Area` using `Parmanent_Water`;
- derived from another raster or time series;
- an event-specific measure, annual statistic, climatology, or other aggregate;
- associated with a particular year or period;
- measured against the Census 2011 boundary vintage or another district geography.

The spelling `Parmanent_Water` is preserved from the source and does not itself define the correction method.

## Target suitability

- **As a regression target:** potentially suitable at district level because it is complete and numeric, but not approved until the source documentation, reference period, spatial vintage, units, and correction formula are obtained.
- **For district-week prediction:** currently not established. The table has no week/event/time field, so it cannot be aligned to a seven-day forecast window from project data alone.
- **For Severity_Score:** a strong candidate if it represents the same target period and geography as the chosen severity observation. Use either this corrected measure or the uncorrected `percent_flooded_area` unless provenance proves they represent distinct constructs.
- **As a predictive feature:** not safe when predicting flood occurrence/extent/severity. It is outcome-like and may directly encode the event being predicted; using it would be target leakage.

## Required evidence before use

Obtain the official IFI-Impacts v3 data dictionary, publication supplement, source code, or table-specific metadata that states:

1. the calculation of the corrected field;
2. the meaning and units of `Parmanent_Water`;
3. the correction relationship to `Percent_Flooded_Area`;
4. the spatial boundary and district vintage;
5. the temporal/reference period;
6. whether values are event-specific or aggregate;
7. quality flags and treatment of permanent water/cloud/missing pixels.

Until that evidence is supplied, retain the field as a possible target candidate only, exclude it from all predictive features, and do not include it in generated scores.
