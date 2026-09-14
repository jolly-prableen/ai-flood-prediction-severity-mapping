"""Reproducible ERA5-Land acquisition for Phase 12A.

This script downloads only from the official Copernicus CDS API. It requires
user-configured CDS credentials outside the repository and an explicit area.
It does not process rainfall, create features, or modify project datasets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import date, timedelta
from pathlib import Path

DATASET = "reanalysis-era5-land"
VARIABLE = "total_precipitation"
DEFAULT_START = date(1967, 1, 1)
DEFAULT_END = date(2023, 12, 31)
TIMES = [f"{hour:02d}:00" for hour in range(24)]


def date_range(start: date, end: date) -> list[str]:
    if end < start:
        raise ValueError("end date must not precede start date")
    return [(start + timedelta(days=offset)).isoformat()
            for offset in range((end - start).days + 1)]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--start", type=date.fromisoformat, default=DEFAULT_START)
    parser.add_argument("--end", type=date.fromisoformat, default=DEFAULT_END)
    parser.add_argument("--area", nargs=4, type=float, required=True,
                        metavar=("NORTH", "WEST", "SOUTH", "EAST"),
                        help="Explicit CDS area in north west south east order")
    parser.add_argument("--format", choices=("netcdf", "grib"), default="netcdf")
    args = parser.parse_args()

    if not os.environ.get("CDSAPI_KEY") and not Path.home().joinpath(".cdsapirc").exists():
        raise SystemExit(
            "CDS credentials are required. Configure the official cdsapi client "
            "outside this repository, then rerun this command."
        )
    try:
        import cdsapi
    except ImportError as error:
        raise SystemExit(
            "cdsapi is not installed. Install the official CDS client in the active "
            "environment before rerunning."
        ) from error

    args.output.parent.mkdir(parents=True, exist_ok=True)
    request = {
        "variable": [VARIABLE],
        "year": sorted({value[:4] for value in date_range(args.start, args.end)}),
        "month": sorted({value[5:7] for value in date_range(args.start, args.end)}),
        "day": sorted({value[8:10] for value in date_range(args.start, args.end)}),
        "time": TIMES,
        "date": date_range(args.start, args.end),
        "area": args.area,
        "data_format": "netcdf" if args.format == "netcdf" else "grib",
        "download_format": "unarchived",
    }
    client = cdsapi.Client()
    client.retrieve(DATASET, request, str(args.output))
    metadata = {
        "source": "Copernicus Climate Change Service / ECMWF",
        "dataset": DATASET,
        "dataset_url": "https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land",
        "doi": "https://doi.org/10.24381/cds.e2161bac",
        "variable": VARIABLE,
        "variable_units_expected": "m of water equivalent",
        "conversion_to_mm": "tp_mm = tp_m * 1000",
        "temporal_resolution": "hourly",
        "spatial_resolution": "0.1 degree distributed grid; verify returned file metadata",
        "start": args.start.isoformat(),
        "end": args.end.isoformat(),
        "area_north_west_south_east": args.area,
        "request": request,
        "file": str(args.output),
        "sha256": sha256(args.output),
        "processing_status": "raw acquisition only; daily aggregation and feature derivation not performed",
    }
    args.output.with_suffix(args.output.suffix + ".metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
