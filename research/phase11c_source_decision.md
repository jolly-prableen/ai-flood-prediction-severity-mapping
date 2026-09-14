# Phase 11C Independent Observation Source Decision

## Scope

This is a research decision only. No source data were downloaded, no observations were created, and no targets or negative labels were generated.

## Candidate comparison

### 1. Global Flood Database

- **Source:** Global satellite-derived flood-event database described in Tellman et al., DOI: https://doi.org/10.1038/s41586-021-03695-w
- **Temporal coverage:** Published database covers 2000–2018.
- **India coverage:** Global product, therefore India is within geographic scope; event-level India completeness is not guaranteed.
- **Spatial resolution:** Approximately 250 m flood mapping products in the publication.
- **Temporal resolution:** Event/flood-map observations tied to satellite acquisitions, not a complete daily district panel.
- **Systematic observations:** Systematic satellite-derived event mapping, but event-selected rather than continuous no-flood surveillance.
- **Negative support:** No. Absence of a mapped event is not a verified no-flood observation because of cloud, revisit, detection, and event-selection limitations.
- **False negatives:** Small/short floods, cloud-obscured scenes, revisit gaps, and events outside 2000–2018.
- **District-week compatibility:** Positive extent can be intersected with districts and weeks; a coverage mask would still be needed for any negative interpretation.
- **Accessibility/reproducibility:** Publication/associated data access is documented, but release and access terms must be checked before acquisition.
- **Classification:** Suitable for positive-event/extent verification in covered periods; unsuitable for negative sampling alone.

### 2. Dartmouth Flood Observatory

- **Source:** University of Colorado Boulder Dartmouth Flood Observatory, https://floodobservatory.colorado.edu/
- **Temporal coverage:** Historical archive coverage is product/release-specific; the current site is undergoing an archive/interface transition and does not establish a complete 1967–2023 district-week series.
- **India coverage:** Global event scope can include India, but completeness is not established.
- **Spatial resolution:** Product-specific event maps/locations; exact resolution must be verified for the selected release.
- **Temporal resolution:** Event observations and satellite-derived products, not a complete district-week panel.
- **Systematic observations:** Event-oriented satellite/reporting archive with systematic components, but not a complete no-event surveillance frame.
- **Negative support:** No. Non-detection can reflect no coverage, clouds, thresholds, or archive omission.
- **False negatives:** High before satellite-era coverage and for small, short, or obscured events.
- **District-week compatibility:** Positive-event corroboration is possible after product-specific acquisition and spatial/temporal review.
- **Accessibility/reproducibility:** Public research site, but current transition means release/version and archive reproducibility require verification.
- **Classification:** Suitable for positive corroboration; unsuitable for negative sampling alone.

### 3. EM-DAT

- **Source:** CRED/UCLouvain, https://www.emdat.be/ ; portal https://public.emdat.be/ ; documentation https://doc.emdat.be/
- **Temporal coverage:** Database records span 1900–present.
- **India coverage:** Country-level global disaster coverage includes India where events meet inclusion criteria.
- **Spatial resolution:** Primarily country-level disaster and loss records, not district polygons or district-week observations.
- **Temporal resolution:** Disaster/event records, not continuous district-week monitoring.
- **Systematic observations:** Systematic major-disaster database; inclusion requires thresholds such as fatalities, affected people, emergency declaration, or international assistance.
- **Negative support:** No. Absence means no qualifying major disaster record, not no flood.
- **False negatives:** Local floods, small floods, unreported events, and events below inclusion thresholds.
- **District-week compatibility:** Poor without external geographic/event disaggregation.
- **Accessibility/reproducibility:** Public portal requires registration/login; non-commercial open access is described by EM-DAT terms.
- **Classification:** Positive major-disaster corroboration only; unsuitable for negative sampling.

### 4. Copernicus Global Flood Monitoring (GFM)

- **Source:** Copernicus Emergency Management Service, https://global-flood.emergency.copernicus.eu/
- **Official access:** The CEMS data-and-services page states that GFM data are distributed through temporal OGC WMS, web-push notifications, product-specific REST APIs, and a download application: https://global-flood.emergency.copernicus.eu/general-information/data-and-services/
- **Temporal coverage:** Sentinel-1-era monitoring is the practical candidate period; exact archive start/end and India acquisition coverage must be verified from GFM metadata. A 2015–2023 restricted period is proposed provisionally because it follows the Sentinel-1 era and overlaps the IFI period, but it is not approved until coverage is audited.
- **India coverage:** Global service scope includes India; district-level coverage must be checked per week and per satellite observation.
- **Spatial resolution:** Product-specific GFM resolution must be taken from the selected release metadata; it must not be guessed from the service name.
- **Temporal resolution:** Satellite-acquisition/event observations, not guaranteed daily observations for every district.
- **Systematic observations:** Strongest candidate among the reviewed sources because it is an operational/systematic global flood-monitoring service with temporal product access.
- **Negative support:** Conditional only. A district-week may be negative only when GFM observation coverage/quality metadata demonstrate sufficient observation opportunity over the relevant window and no qualifying flood is detected. No coverage means UNKNOWN.
- **False negatives:** Satellite revisit gaps, cloud/radar quality masks, water-detection thresholds, small or short floods, geometry mismatch, and incomplete district-week acquisition.
- **District-week compatibility:** Good after spatial intersection, weekly aggregation, and coverage-mask validation. Multiple detections in one week require an any-flood rule plus event metadata.
- **Accessibility/reproducibility:** CEMS exposes APIs, WMS, notifications, and a download application; access terms and product-specific metadata must be recorded. No data were downloaded in Phase 11C.
- **Classification:** Best candidate for both positive verification and conditional negative verification, but only for coverage-qualified district-weeks.

## Decision

**RECOMMENDED SOURCE: Copernicus Global Flood Monitoring (GFM).** It is the only reviewed candidate with an explicitly systematic monitoring service and temporal data-access channels suitable for a coverage-aware district-week frame.

**RECOMMENDED PERIOD: 2015–2023, provisional and coverage-gated.** The period is selected as the practical Sentinel-1-era candidate overlapping the IFI record, but the exact GFM archive start and per-district acquisition coverage must be verified before any labels are made.

This decision does not claim that every district-week from 2015–2023 is observed. It authorizes only a later coverage audit.

## Label-status rule

- **POSITIVE:** a qualifying flood is detected by GFM in the district-week/approved seven-day window, with valid product quality metadata.
- **NEGATIVE:** sufficient GFM observation coverage exists for the district/time window, the quality criteria pass, and no qualifying flood is detected.
- **UNKNOWN:** coverage is insufficient, quality is invalid, the district is not observed, or the source cannot distinguish non-detection from no observation.

UNKNOWN must never become NEGATIVE.

## If GFM coverage fails

If the coverage audit shows that GFM cannot provide sufficient India district-week observation opportunity for a stable restricted period, no defensible negative source is currently available. The fallback is positive-only event verification or a coverage-qualified case-control study with explicit UNKNOWN exclusion; it is not fabrication of negatives.
