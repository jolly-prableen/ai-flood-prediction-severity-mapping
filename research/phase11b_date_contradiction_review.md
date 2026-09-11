# Phase 11B Event Date Contradiction Review

## A. Purpose

This investigation diagnoses date-order contradictions without modifying raw or processed data. No dates were corrected, rows dropped, observation frames created, or targets generated.

## B. Data inspected

- `data/processed/ifi_event_clean.csv`
- `data/raw/India_Flood_Inventory_v3.csv`
- `src/preprocessing/clean_ifi.py`
- Phase 3 cleaning log and validation report

## C. Contradiction counts

- Reported contradictions under the prior diagnostic: **290** rows.
- Genuine raw-source contradictions under the documented raw DD-MM-YYYY parse: **17** rows.
- Raw contradictions among the reported 290: **2** rows.
- Additional raw contradictions not included in the prior 290-row diagnostic: **15** rows.

## D. Investigation methodology

The raw source uses strings such as `08-06-1969 00:00`; the Phase 3 cleaner parses these day-first and writes ISO-formatted dates to the processed CSV. The prior 290 count was reproduced by reparsing those processed ISO strings with `dayfirst=True`, which is inappropriate for ISO `YYYY-MM-DD` strings. Diagnostics compared raw DD-MM parsing, processed ISO/year-first parsing, and the raw values joined by unique `UEI`.

## E. Evidence from raw/source data

- All 290 reported rows were joined to raw records by `UEI`; no raw match was missing.
- Proper ISO parsing resolves **288** of the reported rows.
- **2** reported rows remain contradictory in the raw source and are classified `SOURCE_INCONSISTENCY`.
- The raw source contains **17** total end-before-start rows; the raw contradictions are not a cleaning transformation artifact.

## F. Date-parsing analysis

- Raw date strings are day-first `DD-MM-YYYY HH:MM`.
- Processed date strings are ISO `YYYY-MM-DD` after Phase 3 serialization.
- Applying `dayfirst=True` to processed ISO strings creates the reported 290-row diagnostic artifact.
- Applying year-first/ISO parsing to processed strings reduces the contradiction count to the 17 raw-source contradictions.
- Month-first parsing is not supported by the raw format and is not a valid automatic correction rule.

## G. Duration consistency

- Under proper raw DD-first parsing, **6839** rows have noncontradictory complete start/end dates.
- The apparent convention is inclusive duration `(end - start) + 1` days; **6684** rows match it.
- **155** noncontradictory rows with nonmissing durations do not match the inclusive convention.
- Duration is therefore not a reliable automatic repair field. It must not be used to swap or reconstruct dates without record-level evidence.

## H. Classification counts for the reported 290

- `CORRECTABLE_WITH_EVIDENCE`: **288**
- `AMBIGUOUS_REQUIRES_REVIEW`: **0**
- `SOURCE_INCONSISTENCY`: **2**
- `UNRESOLVED`: **0**

## I. Recommended treatment

- The 288 parsing-artifact rows are safe for future interval targeting only after the documented parser distinction is enforced in implementation; no file was changed here.
- The 2 raw-source contradictions in the reported set must be excluded from automatic interval targeting or manually resolved from authoritative source evidence.
- The other 15 raw-source contradictions outside the prior 290 must also be excluded from interval targeting until reviewed.
- Never sort dates, take absolute duration, replace an endpoint using duration, or assume a one-day event automatically.

## J. Implications for district-week / 7-day targeting

Use raw DD-first parsing for raw source inspection and ISO/year-first parsing for the serialized processed dates. Only verified chronological intervals may be tested against the district-week forecast window. Parsing artifacts must be resolved by documented parser behavior; source contradictions remain unknown/excluded. A positive or negative target must not be generated for unresolved intervals.

## K. Remaining unresolved records

- **17** raw-source contradictions require authoritative review if they are to be used for interval targeting.
- **155** otherwise chronological records have duration values inconsistent with the apparent inclusive convention; they require separate duration review but are not automatically date contradictions.

## L. Immutability statement

No raw CSV, processed CSV, final crosswalk, model, target column, or observation frame was modified or created. The row-level CSV is diagnostic output only.
