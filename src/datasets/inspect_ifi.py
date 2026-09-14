"""Inspect locally supplied IFI-Impacts CSV files without changing them."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

EXPECTED_FILES = (
    "India_Flood_Inventory_v3.csv",
    "District_FloodImpact.csv",
    "District_FloodedArea.csv",
)


def inspect_csv(path: Path) -> dict:
    frame = pd.read_csv(path)
    return {
        "file": path.name,
        "records": int(len(frame)),
        "columns": list(frame.columns),
        "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
        "missing_values": {column: int(value) for column, value in frame.isna().sum().items()},
        "duplicate_records": int(frame.duplicated().sum()),
        "unique_values": {
            column: int(frame[column].nunique(dropna=True)) for column in frame.columns
        },
    }


def inspect_directory(input_dir: Path) -> dict:
    files = sorted(input_dir.glob("*.csv"))
    return {
        "source": "India Flood Inventory-Impacts (IFI-Impacts)",
        "zenodo": "https://zenodo.org/records/11275211",
        "input_directory": str(input_dir),
        "expected_files": list(EXPECTED_FILES),
        "present_files": [path.name for path in files],
        "missing_expected_files": [name for name in EXPECTED_FILES if not (input_dir / name).exists()],
        "datasets": [inspect_csv(path) for path in files],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path, default=Path("results/dataset_inspection.json"))
    args = parser.parse_args()
    report = inspect_directory(args.input_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
