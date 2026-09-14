# Rainfall Source Research

## Preferred product

**Recommended product:** IMD high-resolution gridded daily rainfall over India, commonly referred to as IMD daily gridded rainfall.

**Official institution:** India Meteorological Department (IMD), Ministry of Earth Sciences, Government of India. The product is associated with the IMD Pune climate-data program and the IMD gridded-rainfall research release described by Pai and collaborators.

## Verified or well-established product characteristics

| Item | Finding |
|---|---|
| Spatial resolution | 0.25° latitude × 0.25° longitude daily grid for the high-resolution product |
| Temporal resolution | Daily rainfall accumulation |
| Spatial coverage | Indian land region/grid domain; exact mask and bounding coordinates must be recorded from the downloaded release |
| Units | Rainfall depth, normally millimetres per day; confirm the release metadata before processing |
| Temporal coverage | Long historical coverage beginning in 1901 is associated with the IMD gridded product. The exact latest year depends on the release and must be recorded at acquisition time. |
| Format | Release-dependent gridded binary/ASCII/NetCDF-style distribution; do not assume a file format before downloading the selected release |
| District aggregation | Yes, by area-weighted overlay of grid cells with the chosen district-boundary vintage; retain the aggregation method and boundary version |
| Project period | The historical span covers the IFI period in principle, but the selected release must be checked for complete coverage through 2023 and for consistent versioning |

## Access and licensing status

The official access point is the **IMD Data Service Portal Version 5.7**: https://dsp.imdpune.gov.in/

Official pages inspected:

- IMD Pune: https://www.imdpune.gov.in/
- Data Service Portal: https://dsp.imdpune.gov.in/
- Registration: https://dsp.imdpune.gov.in/home_registration_form.php
- Categories and charges: https://dsp.imdpune.gov.in/home_categories.php
- Free data access: https://dsp.imdpune.gov.in/home_freedataaccess.php
- Data formats/cost estimate: https://dsp.imdpune.gov.in/home_sampledata_costestimate.php
- Gridded climatology page: https://dsp.imdpune.gov.in/home_gridded_climatology.php

The portal exposes registration, data categories, data requests, payment/cost information, and a gridded-climatology section. Its free-data page exposes all-India monthly and seasonal rainfall, not the required daily 0.25° gridded rainfall archive.

**Current daily 0.25° archive endpoint: REQUIRES MANUAL VERIFICATION.** No direct downloadable file for the required product was exposed through the normal page content.

The registration page states that users need an account, email verification, and one-time identity and/or undertaking documents, followed by an online data request and payment where applicable. The categories page states that research/educational access receives a 50% concession, while the portal may restrict supply to about 1,000,000 records. Exact charges and eligibility depend on the applicant category.

The exact current download URL, release version, file format, variable name, missing-value code, spatial mask, file size, and redistribution terms remain **not verified for a specific daily 0.25° release**.

Do not scrape an unofficial mirror or silently substitute another rainfall product. At acquisition time, record the official IMD landing page, release/version, request or download date, metadata, checksum, units, missing-value code, and permitted use.

## Recommended use later

Use daily IMD rainfall as the base source. For a district-week framework, compute rainfall summaries from daily values using only dates available before the forecast cutoff, such as antecedent totals and wet-day counts. For spatial deep-learning models, retain the native grid or a documented district rasterization rather than reducing the source prematurely.

## Limitations

- A grid-cell value is an areal estimate, not a gauge observation at every location.
- District boundaries and rainfall grid cells are different spatial supports; edge handling and area weighting matter.
- Boundary changes across the 1967–2023 IFI period create historical comparability issues.
- Missing-value codes, gauge-density changes, interpolation methodology, and release updates must be checked in the selected metadata.
- Rainfall observed after a forecast cutoff is leakage; a forecast task may require forecast rainfall rather than observed rainfall.

## Decision status

**Preferred source:** IMD daily 0.25° gridded rainfall.

**Download status:** Not downloaded.

**Acquisition status:** BLOCKED pending manual verification of the current official IMD portal/download workflow.

**Required manual action:** register/log in to the IMD Data Service Portal, open the data request/catalog workflow, request the daily gridded rainfall product at approximately 0.25° over India covering the usable IFI period, and obtain the release metadata before any download. Do not bypass authentication or substitute the portal's free monthly/seasonal rainfall series.

**Team verification required:** exact product title/version, direct file or delivery method, temporal endpoint, format, variable/coordinate names, units, missing-value convention, spatial mask/bounds, file size, and license/redistribution terms.

No rainfall files, checksums, or `metadata.json` were created because no official downloadable release was verified.