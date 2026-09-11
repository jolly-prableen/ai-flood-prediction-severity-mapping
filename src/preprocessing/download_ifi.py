"""Download the official IFI-Impacts v3 CSV files from Zenodo."""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import urlopen


RECORD_ID = "11275211"
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
FILES = (
    "India_Flood_Inventory_v3.csv",
    "District_FloodImpact.csv",
    "District_FloodedArea.csv",
)


def download_file(filename: str, force: bool = False) -> Path:
    destination = RAW_DIR / filename
    if destination.exists() and not force:
        print(f"exists: {destination}")
        return destination

    url = f"https://zenodo.org/api/records/{RECORD_ID}/files/{filename}/content"
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".download")
    with urlopen(url) as response, temporary.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    temporary.replace(destination)
    print(f"downloaded: {destination}")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace existing files with the official Zenodo copies",
    )
    args = parser.parse_args()
    for filename in FILES:
        download_file(filename, force=args.force)


if __name__ == "__main__":
    main()