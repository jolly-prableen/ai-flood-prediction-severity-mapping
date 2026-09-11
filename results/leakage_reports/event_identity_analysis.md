# Event Identity Analysis

## Findings

- `uei` is populated for all 6,876 event rows and is unique in the cleaned inventory; repeated UEI rows: **0**.
- `unnamed_0` is also unique but is a source row/index field, not a documented event identifier.
- Start dates are present for 6,856 rows; 20 are missing. District values are missing for 60 rows.
- District + year is not unique: 812 combinations repeat, affecting 2,707 rows. This confirms that multiple flood events can occur in one district in one year.
- District + date is not a safe identity because events may share dates, rows may reference multiple districts, and dates are missing in some records.
- District + event identifier is the most defensible event grouping available: use `uei` as the event identity, while retaining district membership as a separate multi-value attribute.
- The semantic definition of UEI should still be verified against the official dataset documentation before it is used as a permanent key.

## Recommended later strategy

Use `uei` for event-level grouping and contamination checks. Do not use it as a predictive feature. If the prediction unit becomes district-event, create a verified event-to-district representation only after the forecast unit and temporal horizon are approved; do not substitute district-year as an event key.