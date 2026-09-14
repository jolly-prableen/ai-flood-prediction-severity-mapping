# Phase 12A ERA5-Land Metadata and Acquisition Plan

## Status

**DATA ACQUIRED: NO.** CDS authentication is not configured in this environment, so no request or download was attempted. No project datasets were modified.

## Official source

- **Provider:** Copernicus Climate Change Service / European Centre for Medium-Range Weather Forecasts (ECMWF).
- **Dataset:** ERA5-Land hourly data from 1950 to present.
- **Official CDS URL:** https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land
- **Dataset DOI:** https://doi.org/10.24381/cds.e2161bac
- **License:** CC-BY licence as shown on the official CDS catalogue entry.
- **Documentation:** https://confluence.ecmwf.int/spaces/CKB/pages/76414402/ERA5+data+documentation

## Dataset facts verified from official CDS/ECMWF pages

- Temporal coverage: January 1950 to present.
- Temporal resolution: hourly.
- Spatial coverage: global.
- Distributed grid: regular latitude-longitude grid at 0.1° × 0.1°; native resolution is approximately 9 km on a reduced Gaussian grid.
- File format: GRIB on the CDS catalogue entry; CDS requests may also provide NetCDF according to ECMWF documentation.
- Required variable: `total_precipitation`, short name `tp`, parameter identifier 228.
- Variable meaning: accumulated liquid and frozen water, including rain and snow, falling to the surface.
- Variable units: metres of water equivalent (`m`) in the hourly dataset; multiply by 1000 to express rainfall/water-equivalent depth in millimetres.
- Relevant period: 1967-01-01 through 2023-12-31 is covered by the dataset’s published historical range.
- Region: request only a bounding box covering India and the project district extent, rather than global data.

## Accumulation conversion rule

`tp` is an accumulated hydrological variable, not an instantaneous rate. Do not blindly sum arbitrary values from different forecast cycles.

The ECMWF documentation states that reanalysis short-forecast accumulations are over the processing period ending at the validity time; for reanalysis hourly data this is the hour ending at the validity time. It also notes that accumulations at step zero are zero and that the 00 UTC value covers the processing period ending at 00 UTC.

For the selected ERA5-Land CDS request, the implementation must:

1. preserve the returned UTC validity timestamps and dataset metadata;
2. confirm whether the returned `tp` values are hourly end-of-period accumulations for the requested dataset/stream;
3. convert metres to millimetres with `tp_mm = tp_m * 1000`;
4. sum the non-overlapping hourly accumulation periods into UTC calendar-day totals;
5. validate that the first/last periods and 00 UTC boundary are counted exactly once;
6. reject or separately diagnose negative/deaccumulation artifacts, duplicate timestamps, missing hours, and mixed forecast-cycle semantics.

The project must not implement a generic deaccumulation algorithm until the actual returned ERA5-Land file metadata has been inspected. The official documentation supports hourly end-period accumulation handling, but the exact request response still needs validation.

## Proposed CDS subset

- Dataset: `reanalysis-era5-land`.
- Variable: `total_precipitation` only.
- Dates: 1967-01-01 through 2023-12-31.
- Times: all hourly validity times required for complete daily totals.
- Area: smallest practical India bounding box, with edge cells retained until district overlay; exact coordinates must be fixed from the final crosswalk/boundary extent before requesting.
- Format: prefer NetCDF if the CDS request supports it and the resulting metadata are clear; otherwise GRIB with `cfgrib`/ecCodes-compatible inspection.

No subset has been requested yet.

## Authentication/access requirement

The CDS requires a user account and accepted dataset terms. This environment has no `~/.cdsapirc`, no `~/.config/cdsapirc`, and no CDS API key environment variable. Credentials must not be requested through the assistant or written into the repository.

Manual setup required:

1. Create or sign in to a Copernicus Climate Data Store account at https://cds.climate.copernicus.eu/.
2. Accept the ERA5-Land dataset terms on the official dataset page.
3. Obtain the account API key from the CDS profile/API-key area.
4. Install the current official `cdsapi` Python client in the user’s environment.
5. Configure the client using the current CDS user-guide instructions, normally via a user-owned `~/.cdsapirc` or supported environment configuration. Keep the key outside the repository.
6. Confirm the API client can authenticate before issuing the large historical request.

After configuration, the request script should use the official dataset identifier and request only `total_precipitation`, the India subset, and the 1967–2023 dates. The historical hourly request is expected to be large and must be estimated/approved before execution.

## Known limitations

- ERA5-Land is a model-based reanalysis estimate, not a direct gauge observation.
- Accuracy and uncertainty vary through time; ECMWF notes larger uncertainty farther back when fewer observations constrain the forcing.
- The 0.1° distributed grid is finer than ERA5 but is not the same as the project’s district geometry.
- District aggregation and rainfall feature calculation are not part of Phase 12A.
- No target, observation frame, district-week feature, split, or model input has been created.
