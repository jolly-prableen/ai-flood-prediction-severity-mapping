"""Build a conservative IFI-to-Census boundary crosswalk without fuzzy mapping."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import pandas as pd
import shapefile


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_DIR = ROOT / "data" / "external" / "boundaries" / "raw"
IFI_PATH = ROOT / "data" / "processed" / "ifi_event_clean.csv"
OUTPUT = ROOT / "data" / "derived" / "district_crosswalk.csv"


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def split_values(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).split(",") if part.strip() and part.strip().casefold() != "none"]


def main() -> None:
    ifi = pd.read_csv(IFI_PATH)
    observations: defaultdict[str, set[str]] = defaultdict(set)
    for _, row in ifi[["districts", "state"]].iterrows():
        states = split_values(row["state"])
        for district in split_values(row["districts"]):
            observations[district].update(states)

    reader = shapefile.Reader(str(BOUNDARY_DIR / "2011_Dist.shp"))
    fields = [field[0] for field in reader.fields if field[0] != "DeletionFlag"]
    boundary_rows = pd.DataFrame(reader.records(), columns=fields)
    boundary_by_normalized: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    for _, row in boundary_rows.iterrows():
        record = {
            "census_boundary_district": str(row["DISTRICT"]).strip(),
            "census_boundary_state": str(row["ST_NM"]).strip(),
            "censuscode": str(row["censuscode"]).strip(),
        }
        boundary_by_normalized[normalize(record["census_boundary_district"])].append(record)

    rows: list[dict[str, object]] = []
    for ifi_district in sorted(observations):
        candidates = boundary_by_normalized.get(normalize(ifi_district), [])
        exact = any(ifi_district == candidate["census_boundary_district"] for candidate in candidates)
        if exact:
            candidates = [candidate for candidate in candidates if ifi_district == candidate["census_boundary_district"]]
            method = "exact_name"
            group = "exact_name_candidate"
            status = "REQUIRES_MANUAL_VERIFICATION"
            reason = "Exact spelling match; state context and historical boundary equivalence are not established."
        elif candidates:
            method = "normalized_name"
            group = "normalized_requires_verification"
            status = "REQUIRES_MANUAL_VERIFICATION"
            reason = "Case/punctuation normalization only; no fuzzy matching; state context and historical equivalence require review."
        else:
            method = "none"
            group = "unmatched"
            status = "UNMATCHED"
            reason = "No exact or transparent normalized Census boundary name match."
            candidates = [{"census_boundary_district": "", "census_boundary_state": "", "censuscode": ""}]
        for candidate in candidates:
            states = "; ".join(sorted(observations[ifi_district]))
            rows.append({
                "ifi_district_name": ifi_district,
                "ifi_state_name": states,
                **candidate,
                "match_group": group,
                "match_method": method,
                "verification_status": status,
                "historical_boundary_status": "HISTORICAL_BOUNDARY_REVIEW_REQUIRED",
                "notes_reason": reason,
            })

    boundary_names = set(boundary_by_normalized)
    for normalized_name, candidates in boundary_by_normalized.items():
        if normalized_name in {normalize(name) for name in observations}:
            continue
        for candidate in candidates:
            rows.append({
                "ifi_district_name": "",
                "ifi_state_name": "",
                **candidate,
                "match_group": "unmatched",
                "match_method": "none",
                "verification_status": "UNMATCHED",
                "historical_boundary_status": "HISTORICAL_BOUNDARY_REVIEW_REQUIRED",
                "notes_reason": "Boundary district has no exact or transparent normalized IFI district token.",
            })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=[
        "ifi_district_name", "ifi_state_name", "census_boundary_district", "census_boundary_state", "censuscode",
        "match_group", "match_method", "verification_status", "historical_boundary_status", "notes_reason",
    ]).to_csv(OUTPUT, index=False)
    result = pd.read_csv(OUTPUT)
    print(result["match_group"].value_counts().to_dict())
    print({"rows": len(result), "manual": int((result.verification_status == "REQUIRES_MANUAL_VERIFICATION").sum()), "unmatched": int((result.verification_status == "UNMATCHED").sum())})


if __name__ == "__main__":
    main()