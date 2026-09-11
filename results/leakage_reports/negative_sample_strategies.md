# Negative-Sample Strategy Evaluation

The IFI inventory is an event-only database. It contains recorded flood events, not a complete panel of district-time observations. Therefore, no negative labels are created in Phase 4.5.

## Strategy A: District-years with no recorded flood event

**Generation:** Enumerate districts and years represented by an external district frame, then label a district-year negative when no IFI event overlaps it.

**Required assumptions:** IFI coverage is complete for that district-year; district names/codes are reconciled; event dates and district memberships are complete; the external frame covers the same geography.

**Advantages:** Simple temporal unit and compatible with the available event dates.

**Disadvantages and bias:** The IFI record is not documented as exhaustive by district-year. Missing reporting, missing district values, boundary changes, and name mismatches create false negatives. It also discards within-year timing.

**Recommendation:** Not appropriate without an independent completeness or hazard/exposure frame. “No IFI record” must not be labeled no flood.

## Strategy B: District-time periods without a recorded event

**Generation:** Define district-day or district-week exposure units and label periods without an overlapping IFI event.

**Required assumptions:** Complete event detection at that temporal resolution, verified district boundary history, a defined event-overlap rule, and an external frame enumerating all at-risk district-time units.

**Advantages:** Best alignment with a lead-time forecast and avoids treating an entire year as homogeneous.

**Disadvantages and bias:** Requires the most external data and precise event windows. Unrecorded or partially recorded floods remain false-negative risks.

**Recommendation:** Scientifically preferable if an authoritative event/exposure source can establish coverage; not implementable from current IFI alone.

## Strategy C: Matched non-event observations within districts and no-event years

**Generation:** Match event observations to district-time units in periods with no recorded event, controlling for district, season, and possibly weather context.

**Required assumptions:** The matched controls are verified non-events or come from a complete surveillance frame; matching variables are available before prediction; repeated events do not contaminate controls.

**Advantages:** Controls geographic and seasonal confounding and can support case-control design.

**Disadvantages and bias:** Matching cannot repair incomplete outcome ascertainment. It may create artificial class balance and false negatives if controls are only unreported floods.

**Recommendation:** Potentially useful after an external negative frame exists; not safe now.

## Strategy D: External verified event/non-event frame

**Generation:** Obtain a source that enumerates district-time units and independently records flood occurrence or no-occurrence, then reconcile it to IFI using date, state, district, and documented boundary/code crosswalks.

**Required assumptions:** The source has documented coverage, a compatible flood definition, stable temporal resolution, and sufficient geographic identifiers.

**Advantages:** Directly addresses the missing denominator and supports a transparent negative-label rule.

**Disadvantages and bias:** Sources may disagree with IFI, have different detection thresholds, or require substantial boundary and event reconciliation.

**Recommendation:** Safest strategy for this project. The precise source is a project decision; it should be an official or systematically documented national flood-event/exposure record with explicit coverage, not a convenience sample of absent IFI rows.

## Recommendation

Do not manufacture negatives from IFI absence. Before `Flood_Binary` is created, acquire or designate an authoritative district-time observation frame and document its completeness, flood definition, temporal resolution, geographic identifiers, and false-negative limitations.