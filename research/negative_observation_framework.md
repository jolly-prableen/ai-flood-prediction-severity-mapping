# Negative Observation Framework

The IFI inventory contains recorded flood events only. None of the following frames may label an absent IFI record as a verified non-flood without an independent observation source.

## District-day

- **Unit:** district × calendar day.
- **Event assignment:** assign a `uei` when a verified event interval covers the day; multiple UEIs on one day remain multiple event references or a documented multi-event indicator.
- **UEI use:** grouping and event overlap checks only, never a feature.
- **Rainfall:** daily rainfall and antecedent windows are naturally aligned; a one-day or seven-day lead can exclude rainfall after the cutoff.
- **Non-events:** require independent flood surveillance or a complete district-day event frame.
- **False-negative risk:** high if IFI reporting is incomplete or event dates are coarse.
- **Cost:** very high: roughly every district and day across the historical period, plus boundary and event reconciliation.
- **Suitability:** best temporal precision, but operationally heavy and not currently supportable from IFI alone.

## District-week

- **Unit:** district × ISO or project-defined week.
- **Event assignment:** link a week to every overlapping `uei`; retain event count/list and define an explicit overlap rule.
- **UEI use:** prevents repeated events from being collapsed into one silently.
- **Rainfall:** aggregate daily rainfall to weekly totals, wet-day counts, maxima, and antecedent windows available before the cutoff.
- **Non-events:** require an independent district-week observation frame or a documented completeness guarantee.
- **False-negative risk:** lower temporal fragmentation than district-day but still high if unreported floods are treated as negatives.
- **Cost:** moderate and compatible with 26-step six-month sequences.
- **Suitability:** strongest candidate for this project once the negative source, boundary vintage, and lead time are approved.

## District-month

- **Unit:** district × calendar month.
- **Event assignment:** link all overlapping `uei` values to the month; multiple events require counts or lists, not a single arbitrary event.
- **UEI use:** event grouping and overlap audit only.
- **Rainfall:** monthly totals and antecedent monthly windows are easy to compute but lose event onset and short extreme-rain information.
- **Non-events:** require independent district-month verification.
- **False-negative risk:** high because short events and unreported events can disappear inside coarse periods.
- **Cost:** low to moderate.
- **Suitability:** useful for seasonal climatology, but weak for event-onset prediction and less natural for a 26-step six-month sequence.

## Recommendation

**District-week** is the recommended design candidate because it balances rainfall availability, computational cost, multiple-event handling, and the requested six-month sequence requirement. It is not approved as a final target frame yet: an independent non-event source and forecast lead time are still required.