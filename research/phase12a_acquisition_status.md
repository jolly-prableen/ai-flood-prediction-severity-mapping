# Phase 12A ERA5-Land Acquisition Status & Validation Report

## Executive Summary

- **Dataset**: ERA5-Land Hourly Total Precipitation (1950–present)
- **Parameter**: `total_precipitation` (`tp`, Parameter ID 228)
- **Source**: Copernicus Climate Change Service (C3S) / ECMWF
- **DOI**: [10.24381/cds.e2161bac](https://doi.org/10.24381/cds.e2161bac)
- **License**: CC-BY-4.0
- **Acquisition Script**: `src/preprocessing/download_era5land.py`
- **Current Status**: **BLOCKED ON CDS CREDENTIALS**. Execution proceeds with downstream reproducible modules without synthetic fabrication.

---

## 1. Authentication Audit

An automated inspection of the runtime environment was conducted:
- `~/.cdsapirc` file: **Absent**
- `CDSAPI_URL` / `CDS_API_URL`: **Not set**
- `CDSAPI_KEY` / `CDS_API_KEY`: **Not set**
- `cdsapi` Python client: **Not installed in global environment**

### Resolution Protocol for Operators
To enable automated live download of ERA5-Land:
1. Register an account at [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/).
2. Accept the terms of use on the dataset page: `reanalysis-era5-land`.
3. Retrieve personal API key from the user profile.
4. Save credentials to `~/.cdsapirc`:
   ```ini
   url: https://cds.climate.copernicus.eu/api
   key: <USER_API_KEY>
   ```
5. Install the official CDS client:
   ```bash
   python3 -m pip install cdsapi
   ```
6. Run the acquisition script:
   ```bash
   python3 src/preprocessing/download_era5land.py --start-year 2015 --end-year 2023
   ```

---

## 2. Request Specification & Semantic Rules

The download script enforces the following immutable parameters:

| Parameter | Specification | Rational / Semantics |
|---|---|---|
| Dataset | `reanalysis-era5-land` | High-resolution land reanalysis (~9 km native, 0.1° regular grid) |
| Variable | `total_precipitation` | Native unit is **metres of water equivalent** ($m$). Must be multiplied by 1000 to yield millimetres ($mm$). |
| Spatial Bounding Box | `[37.5, 68.0, 6.5, 97.5]` (N, W, S, E) | Minimal bounding box containing all Indian territory and districts. |
| Temporal Range | `2015-01-01` to `2023-12-31` | Sentinel-1 / GFM candidate restricted observation period. |
| Timesteps | 24 hourly steps per day (`00:00` to `23:00`) | Necessary for non-overlapping UTC daily accumulation. |
| Format | NetCDF | Structured multi-dimensional arrays with explicit coordinate attributes. |

---

## 3. Validation Criteria

When files are downloaded, `download_era5land.py --validate <path>` and downstream pipeline checks verify:
1. **Spatial Bounds**: Grid spans latitude $6.5^\circ$N to $37.5^\circ$N and longitude $68.0^\circ$E to $97.5^\circ$E.
2. **Temporal Continuity**: 24 hourly timesteps per calendar day without gaps.
3. **Accumulation Semantics**: In ERA5-Land hourly reanalysis, `tp` represents precipitation accumulated over the 1-hour period ending at validity time. Non-overlapping hourly intervals must be summed to obtain 24-hour totals.
4. **Range / Value Sanity**: Values must be non-negative ($\ge 0$). Daily accumulations exceeding meteorological plausibility (> 1500 mm/day) are flagged for QA review.
5. **Missing Value Integrity**: Missing or unobserved cells/hours must remain `NaN` and are never silently filled with 0.
