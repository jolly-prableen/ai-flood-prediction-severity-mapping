# Phase 11C Restricted Historical Period

## Recommended period

**2015-01-01 through 2023-12-31, provisional and coverage-gated.**

This is a candidate period for later investigation using Copernicus Global Flood Monitoring (GFM), not a generated observation frame. The start is chosen to represent the practical Sentinel-1-era monitoring window and the end aligns with the usable IFI period. Exact GFM archive availability and India/district acquisition coverage must be verified before use.

## Why not 1967–2023

The reviewed independent sources do not provide complete, systematic district-week flood/non-flood observations across the full IFI period:

- EM-DAT is a major-disaster inventory with country-level thresholds.
- Dartmouth Flood Observatory is event-oriented and has historical/satellite coverage limitations.
- Global Flood Database covers 2000–2018 and detected satellite events, not continuous negatives.
- GFM is the strongest systematic candidate, but satellite acquisition and product-quality coverage are not guaranteed for every district-week.

## Required coverage audit before any labels

For every candidate district-week and seven-day horizon, obtain GFM metadata sufficient to determine:

1. whether the district intersects valid GFM observation data;
2. whether the relevant dates have sufficient satellite observation opportunity;
3. whether quality/cloud/radar masks permit a flood/non-flood interpretation;
4. whether the spatial footprint covers enough of the district;
5. whether the product resolution and detection threshold are adequate for the approved flood definition.

The coverage audit must produce three states:

- `POSITIVE`: qualifying GFM flood detected;
- `NEGATIVE`: sufficient valid coverage and no qualifying flood detected;
- `UNKNOWN`: insufficient/invalid coverage or ambiguous non-detection.

Only the first two states may later be eligible for binary target construction. `UNKNOWN` is excluded from negatives and must remain explicitly represented in audit metadata.

## Compatibility with IFI

IFI events inside 2015–2023 can be used as candidate positive records, but they must be reconciled to GFM detections by district, date/window, and the approved final crosswalk. IFI-only events are not automatically GFM positives, and GFM-only detections require an event-linkage review before they are merged conceptually.

The final district crosswalk carries historical limitations, so the selected boundary vintage and unmatched/ambiguous policy must be fixed before any district-week coverage audit.

## Decision status

The period is **RECOMMENDED FOR COVERAGE AUDIT**, not approved for labels. No source data, observations, or target values were downloaded or created in Phase 11C.
