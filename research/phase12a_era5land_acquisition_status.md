# Phase 12A ERA5-Land Acquisition Status

## Status

**BLOCKED BEFORE ACQUISITION.** No ERA5-Land request was submitted and no rainfall data were downloaded.

The official `cdsapi` client is now installed in the configured Python environment, but no CDS credentials were found at the standard user locations or environment variables. No rainfall, GFM, final feature, target, split, or model artifact was created in this phase.

## Approved source and variable

- Provider: Copernicus Climate Change Service / ECMWF
- Dataset: `reanalysis-era5-land`
- Official catalogue: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land
- DOI: https://doi.org/10.24381/cds.e2161bac
- Variable: `total_precipitation` (`tp`)
- Expected hourly units: metres of water equivalent (`m`)
- Conversion after raw-file validation: `tp_mm = tp_m * 1000`
- Temporal resolution: hourly
- Distributed grid: 0.1 degree latitude/longitude; returned-file metadata must be checked
- Candidate historical period: 1967-01-01 through 2023-12-31
- Candidate spatial request: explicit India/project boundary bounding box, to be fixed from the approved boundary extent before acquisition

The variable is accumulated precipitation. Daily aggregation must only happen after inspecting the returned file metadata and confirming hourly end-of-period semantics, timestamp uniqueness, missing hours, and 00 UTC boundary handling.

## Reproducible acquisition script

The script is [src/preprocessing/acquire_era5_land.py](../src/preprocessing/acquire_era5_land.py). It only calls the official CDS API, requires an explicit area, preserves the downloaded raw file, and writes a request metadata sidecar with a SHA-256 checksum. It does not aggregate rainfall or create model features.

After the user configures CDS access outside this repository:

```powershell
python -m pip install cdsapi
$env:PYTHONPATH='.'
python -m src.preprocessing.acquire_era5_land `
  --output data/external/era5_land/raw/era5_land_tp_1967_2023.nc `
  --start 1967-01-01 `
  --end 2023-12-31 `
  --area <NORTH> <WEST> <SOUTH> <EAST> `
  --format netcdf
```

`<NORTH> <WEST> <SOUTH> <EAST>` must be replaced with the explicit approved bounding box. No default coordinates are used to prevent an undocumented spatial request.

## Required user setup

1. Create/sign in to a Copernicus CDS account.
2. Accept the ERA5-Land dataset terms.
3. Configure the current official `cdsapi` client using the CDS user guide and keep credentials outside the repository, normally in the user-owned `~/.cdsapirc` or supported environment configuration.
4. Confirm the client authenticates before issuing the large historical request.
5. Review the request size and approve the historical subset before downloading.

Credentials must not be sent through the assistant or committed to the project.

## Validation still pending

After download, validate before Phase 12B:

- file format and returned metadata
- variable name and units
- UTC timestamps and complete requested date coverage
- duplicate timestamps and missing hours
- spatial bounds, grid spacing, and India coverage
- negative or unexpected precipitation values
- accumulated-period semantics and 00 UTC counting
- raw-file checksum and request metadata

Phase 12B, Phase 12C, GFM observation-frame construction, target generation, final dataset creation, final splitting, and final model training remain blocked until this acquisition and validation succeed. The existing Member 2 baseline is separate and must not be changed.

## Baseline integrity note

During the Phase 12A preflight, the active `data/processed/district_flood_area_regression.csv` baseline file was missing. It was restored only after regenerating it in a temporary location with the existing `src/datasets/prepare_ifi.py` script and verifying exact schema, 720 rows, zero missing values, and content-equivalent split indices (`503/108/109`). The restored file SHA-256 is recorded in `results/baseline_integrity_restore.json`. No checkpoint, model artifact, raw file, or baseline training run was modified.
