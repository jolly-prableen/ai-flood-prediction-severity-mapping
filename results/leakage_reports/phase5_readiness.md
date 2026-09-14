# Phase 5 Readiness

1. **Is the prediction task clearly defined?** **NO.** A provisional event-level, pre-start impact task is documented, but the operational forecast unit and lead time are not approved, and the current data do not support occurrence classification.

2. **Is the prediction horizon defined?** **NO.** `start_date` and `end_date` exist for most event rows, but the project has not specified a lead time or cutoff. District aggregate reference periods are unknown.

3. **Is there a defensible negative-sample strategy?** **NO, not from IFI alone.** The safest future approach is an external, documented district-time observation frame with verified event and non-event status. IFI absence cannot be used as a negative label.

4. **Can `Flood_Binary` be constructed without unsupported assumptions?** **NO.** Creating it now would require manufactured negatives or an unsupported completeness assumption.

5. **Can a chronological train/validation/test split now be performed?** **NO.** Dates span 1967-01-08 to 2023-12-09, but the forecast horizon, negative frame, forecast unit, and missing-date policy are unresolved. No split was created.

6. **What information is still missing?**

- Approved forecast unit and lead time.
- An authoritative or systematically documented negative/non-event observation frame.
- Flood-definition and coverage documentation for that frame.
- Reference periods for both district aggregate tables.
- Verified geographic crosswalk and boundary vintage.
- Confirmation of `uei` semantics and cross-version stability.
- A policy for 20 missing start dates and 20 missing end dates.
- A rule for event overlap and multiple events within a district-time unit.

## Decision

The project is **not ready for Phase 5**. Phase 5 should begin only after the forecast horizon and negative-sample source are approved and documented. No targets, negative labels, or splits were created in Phase 4.5.

## PHASE 4.6 FINAL DECISION

1. **Recommended prediction unit:** District-week is the recommended design candidate, with one observation per district-week and a 26-week historical context for the six-month sequence requirement. This is not yet an instantiated observation table.
2. **Recommended forecast horizon:** **REQUIRES TEAM DECISION.** A seven-day lead is the most compatible candidate for the weekly framework, but the team must approve it along with event-start tolerance and observed-versus-forecast rainfall policy.
3. **Required external datasets:** Official IMD daily gridded rainfall; a documented district geometry and LGD/Census crosswalk; an independent district-time event/non-event frame; and any DEM, LULC, or hydrology products selected as model inputs.
4. **Positive observation definition:** A district-time unit with a verified IFI event overlap, linked through `uei`, using an approved event-overlap rule and valid temporal/geographic reconciliation.
5. **Defensible negative observation definition:** A district-time unit independently verified as non-flood by a documented observation frame with known coverage. An absent IFI record is not sufficient.
6. **Can `Flood_Binary` now be constructed?** **NO.** No independent negative frame or approved event-overlap policy exists yet.
7. **Can Phase 5 chronological splitting now begin?** **NO.** The horizon, observation frame, missing-date policy, boundary vintage, and forecast unit still require approval.
8. **Still requiring explicit team approval:** district-week versus another temporal unit; forecast lead time; rainfall observation/forecast cutoff; authoritative negative-source dataset; flood definition and overlap rule; fixed versus historical district boundaries; aggregate-table inclusion; and treatment of the 20 missing start dates.

**Phase 4.6 conclusion:** The research framework is documented, but Phase 5 remains blocked. No labels, observations, datasets, or splits were created.

## Phase 5 Working Design Update

The project now adopts the following working design for the M1-M2 interface:

- Prediction unit: district-level.
- Temporal unit: district-week.
- Historical context: 26 weeks.
- Prediction horizon: 7 days.
- Positive event assignment: verified IFI `uei` overlap with the seven-day forecast window.
- Negative assignment: only from an independently verified district-week observation frame.

This finalizes the feature-interface design, not target creation. `Flood_Binary` remains blocked until the independent negative frame, cutoff convention, event-overlap rule, and rainfall availability policy are approved. No target, observation frame, split, or dataset was created.