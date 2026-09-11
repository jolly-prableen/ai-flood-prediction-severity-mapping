# M1 Open Questions

## Blocking before target creation

- Which authoritative or systematically documented source will establish district-week non-events?
- What exact flood definition and coverage guarantee does that source provide?
- Is the prediction cutoff the end of an ISO week, local calendar week, or another interval?
- Is the seven-day horizon measured from the cutoff to the start of the event, or to any overlap with the forecast window?
- Will rainfall be observed through the cutoff, forecast rainfall, or both?
- What tolerance applies when IFI has date-only event starts and no time-of-day?
- How are events with missing `start_date` handled?
- How are multiple `uei` values in one district-week represented?

## External-data decisions

- Which current IMD release, access route, file format, latest date, missing-value code, and license will be used?
- Which district boundary vintage is the modeling geography: fixed Census 2011 or a historical boundary series?
- Which official LGD reference and version will crosswalk IFI geographic codes?
- Are DEM, LULC, and hydrology required for the first model or optional extensions?
- What spatial representation is needed for the listed U-Net/ConvLSTM and raster models versus district-tabular models?
- What source vintages are valid for population, LULC, DEM, and hydrology relative to each cutoff?

## Feature-contract decisions

- Which `REQUIRES_EXTERNAL_DATA` fields will be mandatory for the first trained model?
- What model-specific tensor shape represents `district_static_geometry`?
- What missingness threshold and mask policy will be saved with the model?
- What exact scaling and encoding artifacts will be serialized?
- Which rainfall aliases and unit conversions will the adapter accept after metadata review?
- How will custom uploads identify the trained boundary/crosswalk version?

## Target decisions

- Will the first target be Flood_Binary, Severity_Class, or Severity_Score?
- If severity is selected, which outcome fields and thresholds define it?
- Are district aggregate tables target sources, predictive sources, or excluded until their reference periods are verified?
- How will positive events be assigned when one event spans multiple districts or forecast windows?

## Current prohibition

Until these questions are resolved, do not create labels, negative observations, splits, SMOTE outputs, or model inputs. IFI outcome and identifier fields remain excluded from predictive features.
