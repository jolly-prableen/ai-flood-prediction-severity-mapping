# Historical Boundary Limitations

The acquired layer is a Census 2011 reference boundary set. It must not be treated as a time-invariant representation of Indian districts across the full IFI period, which begins in 1967 and ends in 2023.

## Known risks

- District creation, abolition, renaming, bifurcation, mergers, and state/territory changes can make a 2011 polygon incomparable with an earlier event record.
- The DataMeet documentation warns that some boundaries are pre-delimitation, some names or extents may be incorrect or missing, and some geometries may be shifted.
- IFI district fields contain multi-value names and historical spelling variants; the current comparison produced 332 IFI-only district tokens and 85 boundary-only names.
- Census identifiers are not automatically LGD identifiers and may not provide a stable cross-period key.
- A fixed 2011 geography can support a reproducible contemporary reference map, but it may introduce assignment bias for historical events.

## Required decision

Before historical district-week aggregation, choose one of these explicitly:

1. **Fixed geography:** map all observations to the 2011 boundary vintage, documenting unmatched and changed districts and accepting historical misalignment.
2. **Historical geography:** acquire dated boundary versions and a temporal crosswalk, then assign each event according to its event date.

Neither approach should silently infer historical equivalence from a similar name. Unmatched or ambiguous records must remain `REQUIRES_VERIFICATION`.

## Current status

The project has acquired the 2011 reference layer only. No historical reconstruction or rainfall aggregation has been performed.