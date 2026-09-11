# Phase 11A Negative-Source Comparison

## Scope and classification

This is an investigation only. No observation frame or labels were created. A source that records flood events is not automatically a source of reliable non-events.

## Candidate 1: EM-DAT International Disaster Database

- **Source/provider:** Centre for Research on the Epidemiology of Disasters (CRED), UCLouvain.
- **URL:** https://www.emdat.be/ ; data portal https://public.emdat.be/ ; documentation https://doc.emdat.be/
- **External facts:** EM-DAT states that it contains disaster records from 1900 to the present and focuses on major disasters. Its inclusion criteria include at least 10 fatalities, 100 affected people, a state-of-emergency declaration, or a request for international assistance. The public portal requires account access.
- **Temporal coverage:** 1900-present at the database level; country/event coverage is not equivalent to complete district-week coverage.
- **Spatial coverage/resolution:** global, primarily country-level disaster/impact records; not a district-week observation grid.
- **Explicit flood events:** yes, for events meeting its inclusion criteria.
- **Can establish non-events:** no. Absence means no qualifying major disaster record, not verified no flood.
- **False negatives:** high for local, small, or unreported floods and events below inclusion thresholds.
- **Licensing/access:** open access for non-commercial use is described by EM-DAT, with portal registration/login and terms.
- **India/1967-2023 compatibility:** India and the period are likely represented at major-disaster scale, but district-level completeness is not established.
- **Classification:** suitable for positive-event corroboration at major-disaster scale; unsuitable for negative sampling.
- **Practical use:** secondary validation or sensitivity analysis, not the sole denominator.

## Candidate 2: Dartmouth Flood Observatory (DFO) Flood Observatory

- **Source/provider:** University of Colorado Boulder, Dartmouth Flood Observatory.
- **URL:** https://floodobservatory.colorado.edu/
- **External facts:** The current site describes space-based measurement, mapping, and modeling of surface water and has a redesigned interface with archive transition work ongoing. Its products are flood-event and satellite-observation oriented.
- **Temporal coverage:** historical archive coverage and current transition status require release-specific verification before acquisition; the accessible current pages do not establish a complete 1967-2023 district-week series.
- **Spatial coverage/resolution:** global event/observational products; exact product-specific spatial resolution varies and must be verified for the selected archive.
- **Explicit flood events:** yes, where the archive records an event.
- **Can establish non-events:** no. Non-detection is affected by satellite coverage, cloud, mapping thresholds, reporting, and archive inclusion.
- **False negatives:** high before satellite-era coverage and for small/short/cloud-obscured events.
- **Licensing/access:** product-specific access and attribution terms require verification.
- **India/1967-2023 compatibility:** potentially useful for positive verification during covered satellite periods; not complete across the full IFI period.
- **Classification:** suitable for positive-event verification in covered periods; unsuitable for negative sampling alone.
- **Practical use:** independent positive corroboration and spatial extent review, not a complete negative frame.

## Candidate 3: Global Flood Database

- **Source/provider:** published global satellite-derived flood-event dataset; publication DOI: https://doi.org/10.1038/s41586-021-03695-w
- **External facts:** The associated publication describes a global database of flood events derived from satellite observations, with event coverage for 2000–2018 and approximately 250 m mapping products. The dataset represents observed flood extent for detected events, not all district-time conditions.
- **Temporal coverage:** 2000–2018 in the published database.
- **Spatial coverage/resolution:** global; approximately 250 m event flood maps in the publication.
- **Explicit flood events:** yes, detected satellite flood events and mapped extents.
- **Can establish non-events:** no. Unmapped areas/times are not verified dry or flood-free; cloud, revisit, sensor, and detection thresholds create non-detection risk.
- **False negatives:** substantial for small events, cloud-obscured scenes, revisit gaps, and periods outside 2000–2018.
- **Licensing/access:** publication/data access terms must be checked for the selected release; no acquisition was performed.
- **India/1967-2023 compatibility:** partial only, limited to 2000–2018 and detected satellite events.
- **Classification:** suitable for positive flood-extent verification in its coverage; unsuitable for negative sampling alone.
- **Practical use:** independent positive/extent corroboration and a sensitivity-period source.

## Candidate 4: Official Indian disaster/flood reporting

- **Potential providers:** NDMA, Ministry of Home Affairs, state disaster-management authorities, CWC/official water resources records, and official historical disaster reports.
- **URLs:** NDMA portal and agency-specific portals must be identified for the exact historical product; no single complete district-week 1967–2023 source was verified in this investigation.
- **Explicit flood events:** some official records do identify flood events or impacts.
- **Can establish non-events:** not established. Reports normally document incidents and impacts, not a complete surveillance denominator of all district-weeks without flooding.
- **False negatives:** reporting, archival, administrative-boundary, and threshold bias.
- **India/1967-2023 compatibility:** potentially strong for selected periods/regions; complete national district-week coverage is unverified.
- **Classification:** potentially suitable for positive corroboration when a specific complete product is verified; unsuitable for negative sampling until completeness is demonstrated.

## Overall conclusion

No reviewed candidate provides reliable negative observations for every Indian district-week across 1967–2023. The safest approach is a hybrid, coverage-bounded design:

1. Use IFI plus one or more independent event sources for positive-event corroboration where temporal/geographic coverage overlaps.
2. Define negatives only inside an independently documented district-week observation frame with explicit surveillance/exposure coverage.
3. Restrict any binary evaluation period to the intersection where the independent frame can justify both detected events and observed non-events.
4. Keep uncovered years/regions as unknown, not negative.

The project is not authorized to generate `Flood_Binary` until such a frame and its coverage/false-negative policy are approved.
