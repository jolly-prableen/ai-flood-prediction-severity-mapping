"""Inspect the official LGD workbook and build a review-only IFI/LGD/Census comparison."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd
import shapefile


ROOT = Path(__file__).resolve().parents[2]
LGD_DIR = ROOT / "data" / "external" / "boundaries" / "lgd"
BOUNDARY_DIR = ROOT / "data" / "external" / "boundaries" / "raw"
IFI_PATH = ROOT / "data" / "processed" / "ifi_event_clean.csv"
QUALITY_DIR = ROOT / "results" / "data_quality"
INSPECTION_PATH = QUALITY_DIR / "lgd_reference_inspection.md"
COMPARISON_PATH = QUALITY_DIR / "ifi_lgd_census_comparison.csv"


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def split_values(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).split(",") if part.strip() and part.strip().casefold() != "none"]


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    workbook = sorted(LGD_DIR.glob("*.xlsx"))
    if len(workbook) != 1:
        raise ValueError(f"Expected exactly one LGD workbook, found {len(workbook)}")
    workbook_path = workbook[0]
    excel = pd.ExcelFile(workbook_path)
    sheets = {sheet: pd.read_excel(workbook_path, sheet_name=sheet, header=1) for sheet in excel.sheet_names}
    if len(sheets) != 1:
        raise ValueError("Expected one official All Districts sheet")
    lgd = next(iter(sheets.values()))
    required = ["State Code", "State Name (In English)", "District Code", "District Name(In English)", "Census 2001 Code", "Census 2011 Code"]
    missing_required = [column for column in required if column not in lgd.columns]
    if missing_required:
        raise ValueError(f"Missing expected LGD fields: {missing_required}")

    state_col = "State Name (In English)"
    district_col = "District Name(In English)"
    lgd["_state_norm"] = lgd[state_col].map(normalize)
    lgd["_district_norm"] = lgd[district_col].map(normalize)
    duplicate_state_district = int(lgd.duplicated(["State Code", state_col, district_col]).sum())
    duplicate_codes = int(lgd["District Code"].duplicated().sum())
    if duplicate_codes or duplicate_state_district:
        raise ValueError("LGD uniqueness checks failed")

    reader = shapefile.Reader(str(BOUNDARY_DIR / "2011_Dist.shp"))
    fields = [field[0] for field in reader.fields if field[0] != "DeletionFlag"]
    boundary = pd.DataFrame(reader.records(), columns=fields)
    boundary["_state_norm"] = boundary["ST_NM"].map(normalize)
    boundary["_district_norm"] = boundary["DISTRICT"].map(normalize)
    boundary_by_pair: defaultdict[tuple[str, str], list[int]] = defaultdict(list)
    for index, row in boundary.iterrows():
        boundary_by_pair[(row["_state_norm"], row["_district_norm"])].append(index)

    ifi = pd.read_csv(IFI_PATH)
    observed_states: defaultdict[str, set[str]] = defaultdict(set)
    for _, row in ifi[["districts", "state"]].iterrows():
        for district in split_values(row["districts"]):
            observed_states[district].update(split_values(row["state"]))
    ifi_names = sorted(observed_states)
    lgd_by_pair = {(row["_state_norm"], row["_district_norm"]): row for _, row in lgd.iterrows()}
    lgd_by_district: defaultdict[str, list[pd.Series]] = defaultdict(list)
    for _, row in lgd.iterrows():
        lgd_by_district[row["_district_norm"]].append(row)

    rows: list[dict[str, object]] = []
    exact_names: set[str] = set()
    normalized_names: set[str] = set()
    unmatched_names: set[str] = set()
    for ifi_name in ifi_names:
        states = sorted(observed_states[ifi_name])
        name_candidates = lgd_by_district.get(normalize(ifi_name), [])
        exact_candidates = [row for row in name_candidates if row[district_col] == ifi_name]
        candidates = exact_candidates or name_candidates
        if exact_candidates:
            match_method = "exact_district_name"
            status = "CANDIDATE_REQUIRES_VERIFICATION"
            exact_names.add(ifi_name)
            reason = "Exact LGD district name; observed IFI state context is retained separately because the IFI field can be multi-value and historical equivalence is unresolved."
        elif candidates:
            match_method = "normalized_district_name"
            status = "NORMALIZED_REQUIRES_VERIFICATION"
            reason = "Transparent normalization only; state and historical identity require manual review."
            normalized_names.add(ifi_name)
        else:
            match_method = "none"
            status = "UNMATCHED_TO_LGD"
            reason = "No exact or normalized LGD district/state candidate."
            unmatched_names.add(ifi_name)
            candidates = [None]
        for candidate in candidates:
            if candidate is None:
                rows.append({"ifi_district_name": ifi_name, "ifi_state_context": "; ".join(states), "lgd_state_code": "", "lgd_state_name": "", "lgd_district_code": "", "lgd_district_name": "", "census_2001_code": "", "census_2011_code": "", "census_boundary_district_name": "", "census_boundary_state": "", "censuscode": "", "match_method": match_method, "verification_status": status, "historical_limitation": "HISTORICAL_REVIEW_REQUIRED", "notes_reason": reason})
                continue
            boundary_candidates = boundary_by_pair.get((normalize(candidate[state_col]), normalize(candidate[district_col])), [])
            if not boundary_candidates:
                boundary_candidates = [index for index, row in boundary.iterrows() if row["_district_norm"] == normalize(candidate[district_col])]
            if not boundary_candidates:
                boundary_candidates = [None]
            for boundary_index in boundary_candidates:
                boundary_row = boundary.iloc[boundary_index] if boundary_index is not None else None
                state_match = bool(states and candidate[state_col] in states)
                state_note = "Observed IFI state context includes LGD state name." if state_match else "Observed IFI state context does not uniquely confirm LGD state name; manual review required."
                rows.append({"ifi_district_name": ifi_name, "ifi_state_context": "; ".join(states), "lgd_state_code": candidate["State Code"], "lgd_state_name": candidate[state_col], "lgd_district_code": candidate["District Code"], "lgd_district_name": candidate[district_col], "census_2001_code": candidate["Census 2001 Code"], "census_2011_code": candidate["Census 2011 Code"], "census_boundary_district_name": boundary_row["DISTRICT"] if boundary_row is not None else "", "census_boundary_state": boundary_row["ST_NM"] if boundary_row is not None else "", "censuscode": boundary_row["censuscode"] if boundary_row is not None else "", "match_method": match_method, "verification_status": status, "historical_limitation": "HISTORICAL_REVIEW_REQUIRED", "notes_reason": reason + " " + state_note + (" LGD/Census candidate by name; codes are not assumed equivalent." if boundary_row is not None else " LGD district has no exact Census boundary pair." )})

    ifi_normalized = {normalize(name) for name in ifi_names}
    lgd_unmatched = lgd[~lgd["_district_norm"].isin(ifi_normalized)]
    for _, candidate in lgd_unmatched.iterrows():
        boundary_candidates = boundary_by_pair.get((candidate["_state_norm"], candidate["_district_norm"]), [])
        for boundary_index in boundary_candidates or [None]:
            boundary_row = boundary.iloc[boundary_index] if boundary_index is not None else None
            rows.append({"ifi_district_name": "", "ifi_state_context": "", "lgd_state_code": candidate["State Code"], "lgd_state_name": candidate[state_col], "lgd_district_code": candidate["District Code"], "lgd_district_name": candidate[district_col], "census_2001_code": candidate["Census 2001 Code"], "census_2011_code": candidate["Census 2011 Code"], "census_boundary_district_name": boundary_row["DISTRICT"] if boundary_row is not None else "", "census_boundary_state": boundary_row["ST_NM"] if boundary_row is not None else "", "censuscode": boundary_row["censuscode"] if boundary_row is not None else "", "match_method": "lgd_only_name", "verification_status": "LGD_UNMATCHED_TO_IFI", "historical_limitation": "HISTORICAL_REVIEW_REQUIRED", "notes_reason": "LGD district normalized name is absent from IFI tokens; not a negative finding about flood coverage."})

    columns = ["ifi_district_name", "ifi_state_context", "lgd_state_code", "lgd_state_name", "lgd_district_code", "lgd_district_name", "census_2001_code", "census_2011_code", "census_boundary_district_name", "census_boundary_state", "censuscode", "match_method", "verification_status", "historical_limitation", "notes_reason"]
    comparison = pd.DataFrame(rows, columns=columns)
    COMPARISON_PATH.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(COMPARISON_PATH, index=False)
    census_name_matches = int(((comparison["lgd_district_name"] != "") & (comparison["census_boundary_district_name"] != "")).sum())
    ambiguous = int(comparison[comparison["ifi_district_name"] != ""].groupby("ifi_district_name").size().gt(1).sum())
    inspection = [
        "# LGD Reference Inspection",
        "",
        f"- Filename: `{workbook_path.name}`",
        f"- SHA-256: `{checksum(workbook_path)}`",
        f"- Sheet names: `{excel.sheet_names}`",
        f"- Active sheet rows: **{len(lgd):,}**",
        f"- Active sheet columns: **{len(lgd.columns) - 2}** (two internal normalization columns were used only in memory)",
        f"- Original columns: `{required + ['S.No.'] if 'S.No.' in lgd.columns else list(lgd.columns)}`",
        "",
        "## Official fields",
        "",
        "- `State Code`: official LGD state code field.",
        "- `State Name (In English)`: official LGD state name.",
        "- `District Code`: official LGD district code. The report title and portal page identify this as the district LGD-code report; it is not assumed equal to any Census code.",
        "- `District Name(In English)`: official LGD district name.",
        "- `Census 2001 Code`: Census reference field supplied by LGD.",
        "- `Census 2011 Code`: Census reference field supplied by LGD.",
        "",
        "## Quality checks",
        "",
        f"- Full duplicate rows: **{int(lgd.duplicated().sum())}**",
        f"- Missing values: **{lgd[required + ['S.No.']].isna().sum().to_dict()}**",
        f"- Duplicate LGD district codes: **{duplicate_codes}**",
        f"- Duplicate state + district combinations: **{duplicate_state_district}**",
        f"- Unique district records: **{len(lgd):,}**",
        f"- Unique states: **{lgd[state_col].nunique():,}**",
        f"- District Code range: **{int(lgd['District Code'].min())}–{int(lgd['District Code'].max())}**",
        "",
        "## Comparison counts",
        "",
        f"- IFI district names: **{len(ifi_names):,}**",
        f"- IFI names with exact LGD district-name candidates: **{len(exact_names):,}**",
        f"- IFI names requiring normalization: **{len(normalized_names):,}**",
        f"- IFI names unmatched to LGD: **{len(unmatched_names):,}**",
        f"- LGD districts unmatched to IFI by normalized district name: **{len(lgd_unmatched):,}**",
        f"- LGD/Census name-pair candidates in comparison: **{census_name_matches:,} rows**",
        f"- Ambiguous IFI mappings with multiple comparison rows: **{ambiguous:,} district names**",
        "- Historical boundary concerns: all comparison rows are marked `HISTORICAL_REVIEW_REQUIRED` because IFI spans 1967–2023 while the Census boundary layer is a 2011 reference.",
        "",
        "## Interpretation limits",
        "",
        "The workbook is an official current LGD district reference, not a historical 1967–2023 boundary crosswalk. Its Census 2001/2011 fields are reference columns; this inspection does not certify that either equals the DataMeet `censuscode`, and it does not create an IFI-code relationship. Exact names are candidates only; normalized names, state context, and historical identity require manual verification.",
        "",
        f"Review comparison: `{COMPARISON_PATH.relative_to(ROOT)}`",
    ]
    INSPECTION_PATH.write_text("\n".join(inspection) + "\n", encoding="utf-8")
    print({"ifi_exact_candidates": len(exact_names), "ifi_normalized": len(normalized_names), "ifi_unmatched": len(unmatched_names), "lgd_unmatched": len(lgd_unmatched), "lgd_census_rows": census_name_matches, "ambiguous_names": ambiguous, "comparison_rows": len(comparison)})


if __name__ == "__main__":
    main()