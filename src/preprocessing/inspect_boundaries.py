"""Inspect the acquired DataMeet Census 2011 district boundaries without editing source data."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import shapefile


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_DIR = ROOT / "data" / "external" / "boundaries" / "raw"
IFI_PATH = ROOT / "data" / "processed" / "ifi_event_clean.csv"
QUALITY_DIR = ROOT / "results" / "data_quality"
REPORT_PATH = QUALITY_DIR / "boundary_quality_report.md"
COMPARISON_PATH = QUALITY_DIR / "ifi_boundary_comparison.csv"


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def tokens(series: pd.Series) -> set[str]:
    values: set[str] = set()
    for value in series.dropna().astype(str):
        values.update(part.strip() for part in value.split(",") if part.strip() and part.casefold() != "none")
    return values


def checksums() -> dict[str, str]:
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(BOUNDARY_DIR.iterdir()) if path.is_file()}


def main() -> None:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    shp_path = BOUNDARY_DIR / "2011_Dist.shp"
    reader = shapefile.Reader(str(shp_path))
    fields = [field for field in reader.fields if field[0] != "DeletionFlag"]
    field_names = [field[0] for field in fields]
    records = reader.records()
    shapes = reader.shapes()
    frame = pd.DataFrame(records, columns=field_names)
    shape_types = Counter(shape.shapeTypeName for shape in shapes)
    multipart_count = sum(1 for shape in shapes if len(shape.parts) > 1)
    empty_count = sum(1 for shape in shapes if not shape.points)
    nonfinite_count = sum(1 for shape in shapes for point in shape.points if any(value != value or abs(value) == float("inf") for value in point))
    bbox = reader.bbox
    prj = (BOUNDARY_DIR / "2011_Dist.prj").read_text(encoding="utf-8").strip()
    identifiers = [field for field in ("ST_CEN_CD", "DT_CEN_CD", "censuscode") if field in frame.columns]
    identifier_rows = []
    for field in identifiers:
        values = frame[field]
        counts = values.value_counts(dropna=False)
        repeated = counts[counts > 1]
        identifier_rows.append({
            "field": field,
            "missing_count": int(values.isna().sum()),
            "unique_count": int(values.nunique(dropna=True)),
            "duplicate_value_count": int((counts > 1).sum()),
            "duplicate_row_count": int(repeated.sum() - len(repeated)),
        })
    ifi = pd.read_csv(IFI_PATH)
    ifi_districts = tokens(ifi["districts"])
    ifi_states = tokens(ifi["state"])
    boundary_districts = set(frame["DISTRICT"].dropna().astype(str).str.strip())
    boundary_states = set(frame["ST_NM"].dropna().astype(str).str.strip())
    boundary_normalized: defaultdict[str, set[str]] = defaultdict(set)
    for name in boundary_districts:
        boundary_normalized[normalize_name(name)].add(name)
    ifi_normalized: defaultdict[str, set[str]] = defaultdict(set)
    for name in ifi_districts:
        ifi_normalized[normalize_name(name)].add(name)
    comparison_rows = []
    for name in sorted(boundary_districts):
        normalized = normalize_name(name)
        exact = name in ifi_districts
        candidates = ifi_normalized.get(normalized, set())
        if exact:
            status = "EXACT_MATCH"
            matched = name
            reason = "Exact district-name token match"
        elif len(candidates) == 1:
            status = "NORMALIZED_MATCH_REQUIRES_VERIFICATION"
            matched = next(iter(candidates))
            reason = "Case/punctuation/whitespace-normalized match; state context and historical identity require verification"
        elif len(candidates) > 1:
            status = "REQUIRES_VERIFICATION"
            matched = " | ".join(sorted(candidates))
            reason = "Multiple IFI names share the normalized form"
        else:
            status = "BOUNDARY_ONLY"
            matched = ""
            reason = "No exact or normalized IFI district token match"
        comparison_rows.append({"boundary_state": frame.loc[frame["DISTRICT"] == name, "ST_NM"].iloc[0], "boundary_district": name, "ifi_district_candidates": matched, "match_status": status, "reason": reason})
    for name in sorted(ifi_districts - boundary_districts):
        normalized_candidates = boundary_normalized.get(normalize_name(name), set())
        comparison_rows.append({"boundary_state": "", "boundary_district": "", "ifi_district_candidates": name, "match_status": "IFI_ONLY" if not normalized_candidates else "NORMALIZED_MATCH_REQUIRES_VERIFICATION", "reason": "IFI district token absent from boundary exact names" if not normalized_candidates else "IFI name has a normalized boundary candidate; state and historical identity require verification"})
    pd.DataFrame(comparison_rows).to_csv(COMPARISON_PATH, index=False)
    report = [
        "# Boundary Quality Report",
        "",
        "Source: DataMeet India Community Maps Project, Census 2011 district boundaries.",
        "Source URL: https://github.com/datameet/maps/tree/master/Districts/Census_2011",
        "Raw files were inspected in place and not modified.",
        "",
        "## Structure",
        "",
        f"- Feature count: **{len(shapes):,}**",
        f"- Geometry types: **{dict(shape_types)}**",
        f"- Bounding box `(xmin, ymin, xmax, ymax)`: **{bbox}**",
        f"- Multipart geometries: **{multipart_count:,}**",
        f"- Empty geometries: **{empty_count:,}**",
        f"- Non-finite coordinate values: **{nonfinite_count:,}**",
        f"- DBF fields: **{field_names}**",
        f"- CRS from `.prj`: `{prj}`",
        "- The CRS is geographic WGS 84 according to the published `.prj`; EPSG:4326 is the usual equivalent representation.",
        "- Full polygon validity/self-intersection validation was not performed by PyShp; a GIS engine is required for that check.",
        "",
        "## Geography and identifiers",
        "",
        f"- Boundary states represented: **{frame['ST_NM'].nunique(dropna=True):,}**",
        f"- Boundary districts represented: **{frame['DISTRICT'].nunique(dropna=True):,}**",
        f"- Missing district names: **{int(frame['DISTRICT'].isna().sum())}**",
        f"- Missing state names: **{int(frame['ST_NM'].isna().sum())}**",
        f"- District-name duplicates: **{int(frame['DISTRICT'].duplicated(keep=False).sum())} rows**",
        f"- State-name duplicates are expected because multiple districts occur in each state.",
        f"- Identifier analysis: `{json.dumps(identifier_rows)}`",
        "- Published identifier fields are Census-coded fields: `ST_CEN_CD`, `DT_CEN_CD`, and `censuscode`.",
        "- No LGD field was found in the published DBF fields. Census codes are not called LGD codes.",
        "",
        "## IFI comparison",
        "",
        f"- IFI distinct district tokens: **{len(ifi_districts):,}**",
        f"- IFI distinct state tokens: **{len(ifi_states):,}**",
        f"- Boundary distinct districts: **{len(boundary_districts):,}**",
        f"- Exact boundary-to-IFI district-name matches: **{sum(row['match_status'] == 'EXACT_MATCH' for row in comparison_rows):,}**",
        f"- Normalized matches requiring verification: **{sum(row['match_status'] == 'NORMALIZED_MATCH_REQUIRES_VERIFICATION' for row in comparison_rows):,}**",
        f"- Boundary-only districts: **{sum(row['match_status'] == 'BOUNDARY_ONLY' for row in comparison_rows):,}**",
        f"- IFI-only district tokens: **{sum(row['match_status'] == 'IFI_ONLY' for row in comparison_rows):,}**",
        "- The comparison is name-based and does not establish an identifier crosswalk or historical equivalence.",
        "- State/district spelling and historical boundary mismatches require manual review; no fuzzy match was silently accepted.",
        "",
        "## Raw checksums",
        "",
        "```json",
        json.dumps(checksums(), indent=2),
        "```",
    ]
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"features": len(shapes), "fields": field_names, "geometry_types": dict(shape_types), "boundary_districts": len(boundary_districts), "ifi_districts": len(ifi_districts)}, indent=2))


if __name__ == "__main__":
    main()