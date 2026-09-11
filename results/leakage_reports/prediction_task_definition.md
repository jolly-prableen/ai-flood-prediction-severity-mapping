# Phase 4.5 Prediction Task Definition

## Evidence boundary

This definition uses the cleaned IFI event inventory and the Phase 4 audit. The inventory contains 6,876 recorded flood-event rows, each with a unique `uei`; it does not contain explicit non-flood observations. The district aggregate tables have no documented year, event identifier, or reference period.

## Most defensible task supported by the current data

The current data support a **conditional event-level impact/severity research task**, not a validated flood-occurrence classifier:

| Item | Provisional definition |
|---|---|
| Prediction unit | One recorded IFI event identified by `uei` |
| Geographic unit | The district or districts recorded in the event's multi-value `districts` field; this is not currently a one-row-per-district representation |
| Temporal unit | Event record, anchored to the recorded `start_date` |
| Prediction timestamp | A hypothetical timestamp immediately before the event starts; the operational lead time is not specified by the project or source |
| Forecast horizon | Not yet defensibly fixed. Event duration and end date are outcome-time information, not a chosen horizon |
| Positive observation | A flood event recorded in IFI with a valid event identity and, where required, a usable start date |
| Negative observation | Not available in the current IFI files. Absence of an IFI record is not evidence that no flood occurred |
| Available information | Only variables independently verified as known before the chosen timestamp; the current IFI files do not establish such a complete feature set |
| Unavailable information | Event start/end, duration, impacts, damage, flooded area, and all other post-event or target-time measurements |

This is a task definition for later design, not a created target. It does not authorize creation of `Flood_Binary`, `Severity_Class`, or `Severity_Score`.

## What the data cannot currently support

The files cannot currently support a defensible occurrence target of the form “flood versus no flood” because the sampling frame contains flood records only. They also cannot establish a valid prediction horizon for the district aggregate tables. A later predictive task requires an independently defined set of at-risk district-time units, including verified non-events and a forecast cutoff.

## Required decision before modeling

The team must approve a lead time and forecast unit, for example district-day or district-week immediately before the forecast window. That choice must be supported by external observations or an authoritative exposure/calendar frame. The project must then distinguish “not observed in IFI” from “verified no flood.”