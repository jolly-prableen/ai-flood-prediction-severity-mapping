# Prediction Horizon Options

The IFI `start_date` is an observed event reference, not a prediction timestamp. The project has not specified an operational alert lead time, so the options below are design candidates rather than selected labels.

## Same-day

Prediction is made at or immediately before the event start. It can use only information available by that cutoff. Same-day rainfall observations may be partly concurrent with the event and can leak onset information unless the cutoff is defined precisely. Target construction requires a verified district-time frame and event-overlap rule. Compatible with district-day or district-week models, but high leakage ambiguity.

## One-day lead

Prediction is made 24 hours before the event start. Rainfall inputs must stop at the cutoff; forecast rainfall may be needed for future conditions. It is operationally meaningful but requires accurate event start timestamps, which IFI supplies only as dates and has 20 missing starts. Compatible with daily or weekly sequences, but the source resolution limits exact lead-time alignment.

## Three-day lead

Prediction is made 72 hours before event start. Antecedent observed rainfall can be used only through the cutoff; future rainfall requires a forecast product. The longer lead reduces same-event contamination but increases missed-event and timing uncertainty. Compatible with district-week sequences if the event-overlap definition is explicit.

## Seven-day lead

Prediction is made seven days before event start. It fits a weekly observation framework and can use a six-month history represented by 26 weekly steps. It requires a documented event-start tolerance and a rainfall forecast or strictly antecedent rainfall policy. It is a plausible project candidate, not an evidence-based final choice from IFI alone.

## Longer lead

Fourteen or thirty days could support seasonal planning but would require stronger climatological and exposure predictors and would be less directly tied to recorded event onset. The current data do not justify selecting such a horizon.

## Recommendation

**REQUIRES TEAM DECISION.** If the project prioritizes a weekly six-month sequence and an operational warning task, evaluate a seven-day lead first. Do not finalize it until the team approves the lead time, forecast versus observed rainfall policy, event-start tolerance, and negative-observation source. Same-day, one-day, and three-day options remain plausible depending on the operational use case.