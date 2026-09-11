# Phase 11A Observation-Frame Research

## Status labels

- **VERIFIED FROM PROJECT DATA:** derived from current cleaned IFI files and project artifacts.
- **VERIFIED FROM EXTERNAL SOURCE:** stated by the cited external source.
- **INFERENCE:** methodological consequence of the evidence.
- **UNRESOLVED:** requires source metadata or team approval.

## Verified project facts

- IFI contains 6,876 event rows and unique `uei` values.
- Usable `start_date` values span 1967-01-08 to 2023-12-09; 20 are missing.
- Usable `end_date` values also have 20 missing values.
- `duration_days` has 19 missing values and ranges from 1 to 365 days.
- There are 812 repeated district-year combinations affecting 2,707 rows.
- 290 rows have `end_date` earlier than `start_date`; these records require temporal review and cannot be used blindly for interval assignment.
- District values can contain multiple names in one event record and 60 event rows lack district values.
- The final crosswalk preserves verified candidates, review classes, historical limitations, and unmatched names; it is not a perfect historical geography.

## Recommended district-week observation rule

### Observation unit

Use one row per `verified_district_id × approved_week`, with an approved calendar convention. The current working design is district-week and a seven-day horizon; ISO week versus local/project week remains **UNRESOLVED**.

### Cutoff and forecast window

Let `C` be the end of the current approved district-week. The forecast window is the next seven calendar days after `C`. Features may use only information available through `C`.

### Event interval and overlap

For a record with a valid start date and a valid, noncontradictory end date:

- Treat the event interval as inclusive of its recorded dates.
- Mark a district-week target window positive when the event interval intersects the seven-day forecast window.
- If a flood continues across multiple forecast windows, it contributes to every affected district-week window; it must not be assigned only to its start week.
- If a record has a valid start but missing end, use the start for occurrence assignment only if the start falls in the forecast window; do not infer an unrecorded end without an approved rule.
- If duration is available and its relationship to dates is validated, duration may support an interval reconstruction, but current date inconsistencies prohibit automatic reconstruction.
- If end precedes start, quarantine the record for review; do not silently swap dates or infer the interval.

### Multiple and overlapping events

- Preserve every overlapping `uei` as audit metadata.
- The binary occurrence outcome is an `any verified event` indicator at the district-week/horizon level, but no label is generated in Phase 11A.
- Do not sum impacts across events unless an explicit target aggregation rule is approved.
- If multiple events overlap the same district-week, retain event count/list, overlap uncertainty, and source provenance for later sensitivity analysis.
- A single `uei` spanning multiple districts must be represented in each verified district association, without using `uei` as a model feature.

### Missing dates

- Missing `start_date`: exclude from automatic target-window assignment and retain in an unresolved queue. Do not create a negative or positive label from it.
- Missing `end_date` with valid start: allow only start-date occurrence assignment under an approved narrow rule; mark interval end unknown.
- Missing duration: do not impute duration for target construction.
- Contradictory dates, including end-before-start: exclude from automatic interval overlap until source review.

### District mapping

Use the final crosswalk only according to its `match_class` and `verification_status`:

- `VERIFIED_NAME_STATE`: usable candidate for current-reference analysis, still carrying historical limitation.
- `NORMALIZED_REVIEW`, `AMBIGUOUS_REVIEW`, `HISTORICAL_REVIEW`: do not silently assign; require an approved review policy or sensitivity branch.
- `UNMATCHED`: no district target assignment.

The fixed Census 2011 geometry must not be represented as the true district boundary for every IFI year. A historical-boundary policy is required before interpreting long-period district statistics.

## Independent observation-frame requirement

The IFI event inventory supplies positive event candidates, not a complete denominator. A defensible binary frame requires an independent district-week source that documents both observation coverage and the meaning of non-event status. Satellite/event archives may corroborate positives during covered periods but do not make uncovered periods negative.

## Seven-day temporal cutoff

The design can be expressed as:

`cutoff C -> features through C only -> forecast window C+1 through C+7 -> target assignment from verified event evidence`

Remaining ambiguities:

- date-only event time and timezone;
- ISO versus project-defined week;
- whether the horizon is next seven dates or seven full 24-hour periods;
- observed versus forecast rainfall availability;
- boundary vintage and crosswalk confidence;
- independent non-event coverage.

## Recommendation

Do not construct the observation frame until the independent source, calendar, overlap policy, missing-date policy, and historical geography policy are approved. The next implementation should first produce an observation-quality audit, not labels, and should preserve unknown/unresolved units separately from positive and negative candidates.
