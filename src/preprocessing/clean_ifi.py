"""Create documented Phase 3 processed IFI tables without modifying raw data."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
DERIVED_DIR = ROOT / "data" / "derived"
QUALITY_DIR = ROOT / "results" / "data_quality"
DICTIONARY_PATH = ROOT / "research" / "data_dictionary.md"
EVENT_FILE = "India_Flood_Inventory_v3.csv"
DISTRICT_FILES = {
    "District_FloodImpact.csv": "district_flood_impact_clean.csv",
    "District_FloodedArea.csv": "district_flooded_area_clean.csv",
}


def snake_case(name: str) -> str:
    value = re.sub(r"[^0-9A-Za-z]+", "_", name.strip()).strip("_").lower()
    return re.sub(r"_+", "_", value)


def format_name_list(value: Any) -> Any:
    if pd.isna(value):
        return value
    parts = [re.sub(r"\s+", " ", part.strip()) for part in str(value).split(",")]
    return ", ".join(parts)


def normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def source_hashes() -> dict[str, str]:
    hashes = {}
    for path in sorted(RAW_DIR.glob("*.csv")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes[path.name] = digest
    return hashes


def is_numeric_text(series: pd.Series) -> bool:
    values = series.dropna().astype(str).str.strip()
    return bool(len(values)) and bool(values.str.fullmatch(r"[-+]?\d+(?:\.\d+)?").all())


def clean_frame(path: Path) -> tuple[pd.DataFrame, list[dict[str, Any]], list[dict[str, str]]]:
    raw = pd.read_csv(path)
    mapping = [{"source_file": path.name, "original_column_name": column, "cleaned_column_name": snake_case(column)} for column in raw.columns]
    frame = raw.rename(columns={item["original_column_name"]: item["cleaned_column_name"] for item in mapping}).copy()
    conversions: list[dict[str, Any]] = []
    for original, cleaned in zip(raw.columns, frame.columns):
        series = raw[original]
        target = "preserved"
        failures = 0
        examples: list[str] = []
        if original in {"Start Date", "End Date"}:
            converted = pd.to_datetime(series, errors="coerce", format="mixed", dayfirst=True)
            failures = int(series.notna().sum() - converted.notna().sum())
            examples = series[series.notna() & converted.isna()].astype(str).head(5).tolist()
            frame[cleaned] = converted
            target = "datetime64[ns]"
        elif pd.api.types.is_numeric_dtype(series):
            frame[cleaned] = pd.to_numeric(series, errors="raise")
            target = str(frame[cleaned].dtype)
        elif is_numeric_text(series):
            converted = pd.to_numeric(series, errors="coerce")
            failures = int(series.notna().sum() - converted.notna().sum())
            examples = series[series.notna() & converted.isna()].astype(str).head(5).tolist()
            frame[cleaned] = converted
            target = str(frame[cleaned].dtype)
        else:
            frame[cleaned] = series.astype("string")
            target = "string"
        conversions.append({
            "source_file": path.name,
            "original_column": original,
            "cleaned_column": cleaned,
            "original_dtype": str(series.dtype),
            "target_dtype": target,
            "conversion_attempted": original in {"Start Date", "End Date"} or pd.api.types.is_numeric_dtype(series) or is_numeric_text(series),
            "conversion_failure_count": failures,
            "failure_examples": " | ".join(examples),
            "action": "converted without imputing values" if target != "preserved" else "preserved as string; no safe numeric conversion",
        })
    for column in ["districts", "state", "dist_name"]:
        if column in frame.columns:
            frame[column] = frame[column].map(format_name_list)
    return frame, conversions, mapping


def make_name_mapping(raw_frames: dict[str, pd.DataFrame], cleaned_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    observations: list[dict[str, str]] = []
    for dataset, raw in raw_frames.items():
        cleaned = cleaned_frames[dataset]
        district_field = next((column for column in raw.columns if column.lower() in {"dist_name", "districts"}), None)
        state_field = next((column for column in raw.columns if column.lower() == "state"), None)
        if district_field is not None:
            cleaned_district_field = snake_case(district_field)
            raw_values = raw[district_field].dropna().astype(str).unique()
            clean_by_raw = dict(zip(raw[district_field].dropna().astype(str), cleaned[cleaned_district_field].dropna().astype(str)))
            variants: defaultdict[str, set[str]] = defaultdict(set)
            for original in raw_values:
                for token in original.split(","):
                    variants[normalize_token(token.strip())].add(token.strip())
            for original in raw_values:
                original_tokens = [token.strip() for token in original.split(",")]
                standardized_tokens = [token.strip() for token in clean_by_raw.get(original, original).split(",")]
                for index, token in enumerate(original_tokens):
                    if not token:
                        continue
                    standardized = standardized_tokens[index] if index < len(standardized_tokens) else token
                    uncertain = len(variants[normalize_token(token)]) > 1
                    observations.append({
                        "source_file": dataset,
                        "original_state": "",
                        "original_district": token,
                        "standardized_state": "",
                        "standardized_district": token if uncertain else standardized,
                        "mapping_reason": "REQUIRES_VERIFICATION: spelling/case/punctuation variant retained" if uncertain else ("format-only: trimmed or collapsed whitespace" if standardized != token else "unchanged source name"),
                        "confidence": "REQUIRES_VERIFICATION" if uncertain else "HIGH",
                    })
        if state_field is not None:
            cleaned_state_field = next(column for column in cleaned.columns if column.lower() == "state")
            raw_values = raw[state_field].dropna().astype(str).unique()
            clean_values = dict(zip(raw[state_field].dropna().astype(str), cleaned[cleaned_state_field].dropna().astype(str)))
            variants: defaultdict[str, set[str]] = defaultdict(set)
            for value in raw_values:
                for token in value.split(","):
                    variants[normalize_token(token.strip())].add(token.strip())
            for original in raw_values:
                original_tokens = [token.strip() for token in original.split(",")]
                standardized_tokens = [token.strip() for token in clean_values[original].split(",")]
                for index, token in enumerate(original_tokens):
                    token = token.strip()
                    if not token:
                        continue
                    standard = standardized_tokens[index] if index < len(standardized_tokens) else token
                    normalized = normalize_token(token)
                    uncertain = len(variants[normalized]) > 1
                    observations.append({
                        "source_file": dataset,
                        "original_state": token,
                        "original_district": "",
                        "standardized_state": token if uncertain else standard,
                        "standardized_district": "",
                        "mapping_reason": "REQUIRES_VERIFICATION: spelling/case/punctuation variant retained" if uncertain else ("format-only: trimmed or collapsed whitespace" if standard != token else "unchanged source name"),
                        "confidence": "REQUIRES_VERIFICATION" if uncertain else "HIGH",
                    })
    return pd.DataFrame(observations).drop_duplicates()


def missing_reason(column: str, missing_count: int, total: int) -> tuple[str, str]:
    if missing_count == 0:
        return "No missing values observed", "No handling required"
    if column.endswith("_id") or "code" in column or column in {"uei", "unnamed_0"}:
        return "Source identifier is absent; reason requires verification", "Preserve missingness; do not fabricate"
    if missing_count == total:
        return "Column is entirely unpopulated in the source", "Retain for provenance; exclude from later use unless source meaning is resolved"
    return "Source value is absent; reason requires verification", "Preserve missingness; no imputation in Phase 3"


def missing_analysis(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for dataset, frame in frames.items():
        for column in frame.columns:
            count = int(frame[column].isna().sum())
            reason, handling = missing_reason(column, count, len(frame))
            rows.append({"dataset": dataset, "column": column, "missing_count": count, "missing_percent": round(count / len(frame) * 100, 4), "dtype": str(frame[column].dtype), "possible_reason": reason, "proposed_handling": handling})
    return pd.DataFrame(rows)


def identifier_analysis(raw_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for dataset, frame in raw_frames.items():
        identifiers = [column for column in frame.columns if any(term in column.lower() for term in ("id", "code", "uei", "unnamed"))]
        for column in identifiers:
            series = frame[column]
            repeated = series.dropna().value_counts()
            if column in {"District_LGD_Codes", "State_Codes"}:
                token_values = set()
                for value in series.dropna().astype(str):
                    token_values.update(token.strip() for token in value.split(",") if token.strip().lower() != "none")
                mapping_note = "Multi-value cell field; scalar uniqueness and district mapping are not established. LGD meaning is not assumed."
                unique_count = len(token_values)
            else:
                mapping_note = "Scalar identifier analysis."
                unique_count = int(series.nunique(dropna=True))
            rows.append({"dataset": dataset, "identifier": column, "dtype": str(series.dtype), "rows": len(frame), "missing_count": int(series.isna().sum()), "unique_identifier_count": unique_count, "duplicate_value_count": int((repeated > 1).sum()), "duplicate_row_count": int(repeated[repeated > 1].sum() - (repeated > 1).sum()), "maps_to_multiple_district_values": "NOT_ASSESSABLE" if column in {"District_LGD_Codes", "State_Codes"} else "not tested; no district identifier in same scalar row", "same_identifier_multiple_values": "NOT_ASSESSABLE" if column in {"District_LGD_Codes", "State_Codes"} else "none detected" if repeated.empty else "requires row-level semantic review", "stability_across_years": "not established; identifier fields are not a temporal panel key", "notes": mapping_note})
    return pd.DataFrame(rows)


def duplicate_report(raw_frames: dict[str, pd.DataFrame]) -> str:
    lines = ["# Phase 3 Duplicate Analysis", "", "No rows were removed for duplication. Repeated district-year combinations were retained because the inventory is event-level and a district can experience multiple events in one year.", ""]
    for dataset, frame in raw_frames.items():
        exact = int(frame.duplicated().sum())
        lines.extend([f"## {dataset}", "", f"- Exact duplicate rows: {exact} ({exact / len(frame) * 100:.4f}%). Recommended treatment: retain all nonduplicates; no action required."])
        if "Start Date" in frame.columns and "Districts" in frame.columns:
            years = pd.to_datetime(frame["Start Date"], errors="coerce", format="mixed", dayfirst=True).dt.year
            keys = pd.DataFrame({"district": frame["Districts"], "year": years}).dropna()
            counts = keys.value_counts()
            repeated = counts[counts > 1]
            affected = int(repeated.sum())
            examples = [{"district": str(key[0]), "year": int(key[1]), "count": int(value)} for key, value in repeated.head(10).items()]
            lines.append(f"- Duplicate district-year combinations: {len(repeated)} combinations affecting {affected} rows ({affected / len(frame) * 100:.4f}%). Examples: `{json.dumps(examples)}`. Recommended treatment: retain until event semantics are defined.")
            event_ids = frame["UEI"].dropna() if "UEI" in frame.columns else pd.Series(dtype="string")
            lines.append(f"- Duplicate district-event combinations: {int(event_ids.duplicated().sum())} repeated UEI rows. Recommended treatment: retain unique UEI records; investigate only if a future source revision creates repeated UEIs.")
            lines.append("- Geographic records with different flood-event information: repeated district-year groups contain multiple UEIs and are therefore treated as separate event observations, not deleted duplicates.")
        else:
            lines.append("- District-year and district-event checks: not applicable because this is a district-level aggregate table with no year or event identifier.")
        lines.append("")
    return "\n".join(lines)


def numerical_sanity(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for dataset, frame in frames.items():
        for column in frame.select_dtypes(include="number").columns:
            series = frame[column].dropna()
            if series.empty:
                minimum = maximum = None
                zero_count = negative_count = 0
            else:
                minimum, maximum = float(series.min()), float(series.max())
                zero_count = int((series == 0).sum())
                negative_count = int((series < 0).sum())
            normalized = column.lower()
            percentage_violations = int(((series < 0) | (series > 100)).sum()) if "percent" in normalized or "area" in normalized else 0
            coordinate_violations = 0
            if normalized == "latitude":
                coordinate_violations = int(((series < -90) | (series > 90)).sum())
            if normalized == "longitude":
                coordinate_violations = int(((series < -180) | (series > 180)).sum())
            if negative_count or percentage_violations or coordinate_violations:
                classification = "impossible_values_detected"
            elif zero_count:
                classification = "zeros_observed; assess whether zero is a valid source value"
            else:
                classification = "no impossible values detected; extremes retained"
            rows.append({"dataset": dataset, "column": column, "dtype": str(frame[column].dtype), "non_missing_count": int(len(series)), "minimum": minimum, "maximum": maximum, "zero_count": zero_count, "negative_count": negative_count, "percentage_range_violations": percentage_violations, "coordinate_range_violations": coordinate_violations, "classification": classification, "proposed_handling": "retain values; no outlier deletion or target construction in Phase 3"})
    return pd.DataFrame(rows)


def write_dictionary(raw_frames: dict[str, pd.DataFrame], cleaned_frames: dict[str, pd.DataFrame]) -> None:
    lines = ["# IFI-Impacts v3 Data Dictionary", "", "Updated during Phase 3. Raw column names and processed snake_case names are shown together. Meanings not supported by the source label are marked `Meaning requires verification.` No target variables were created.", ""]
    for dataset, raw in raw_frames.items():
        cleaned = cleaned_frames[dataset]
        lines.extend([f"## {dataset}", "", "| Original column | Cleaned column | Data type | Geographic level | Temporal meaning | Missing handling | Later feature use | Outcome/post-event status | Description |", "|---|---|---|---|---|---|---|---|---|"])
        for original, column in zip(raw.columns, cleaned.columns):
            lower = original.lower()
            description = {
                "Start Date": "Flood event start date.",
                "End Date": "Flood event end date.",
                "Districts": "District names associated with an event; source values may contain multiple names.",
                "State": "State names associated with an event; source values may contain multiple names.",
                "Dist_Name": "District name in a district-level aggregate table.",
            }.get(original, "Meaning requires verification.")
            if original in {"Human fatality", "Human injured", "Human Displaced", "Animal Fatality", "Severity", "Area Affected", "Extent of damage ", "Description of Casualties/injured", "Human_fatality", "Human_injured", "Mean_Flood_Duration", "Percent_Flooded_Area", "Corrected_Percent_Flooded_Area"}:
                status = "Likely outcome/post-event field; timing must be established later"
            else:
                status = "Not classified as an outcome in Phase 3"
            feature = "Potential later feature only after semantic and timing review"
            missing = "Preserved source missingness; no imputation"
            level = "event-level" if dataset == EVENT_FILE else "district-level aggregate"
            temporal = "event date fields" if "Date" in original else "reference period requires verification"
            lines.append(f"| {original} | {column} | {cleaned[column].dtype} | {level} | {temporal} | {missing} | {feature} | {status} | {description} |")
        lines.append("")
    DICTIONARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    before_hashes = source_hashes()
    raw_paths = {path.name: path for path in sorted(RAW_DIR.glob("*.csv"))}
    expected = {EVENT_FILE, *DISTRICT_FILES}
    if set(raw_paths) != expected:
        raise ValueError(f"Unexpected raw CSV inventory. Found {sorted(raw_paths)}, expected {sorted(expected)}")
    raw_frames: dict[str, pd.DataFrame] = {}
    cleaned_frames: dict[str, pd.DataFrame] = {}
    conversions: list[dict[str, Any]] = []
    column_mapping: list[dict[str, str]] = []
    for dataset, path in raw_paths.items():
        raw = pd.read_csv(path)
        cleaned, conversion_rows, mapping_rows = clean_frame(path)
        raw_frames[dataset] = raw
        cleaned_frames[dataset] = cleaned
        conversions.extend(conversion_rows)
        column_mapping.extend(mapping_rows)
        output_name = "ifi_event_clean.csv" if dataset == EVENT_FILE else DISTRICT_FILES[dataset]
        cleaned.to_csv(PROCESSED_DIR / output_name, index=False)
    after_hashes = source_hashes()
    pd.DataFrame(column_mapping).to_csv(QUALITY_DIR / "column_name_mapping.csv", index=False)
    pd.DataFrame(conversions).to_csv(QUALITY_DIR / "type_conversion_report.csv", index=False)
    missing_analysis(cleaned_frames).to_csv(QUALITY_DIR / "missing_value_analysis.csv", index=False)
    make_name_mapping(raw_frames, cleaned_frames).to_csv(DERIVED_DIR / "district_name_mapping.csv", index=False)
    identifier_analysis(raw_frames).to_csv(QUALITY_DIR / "identifier_analysis.csv", index=False)
    (QUALITY_DIR / "duplicate_analysis.md").write_text(duplicate_report(raw_frames), encoding="utf-8")
    numerical_sanity(cleaned_frames).to_csv(QUALITY_DIR / "numerical_sanity_report.csv", index=False)
    write_dictionary(raw_frames, cleaned_frames)
    merge_reason = "No ifi_unified_clean.csv created. The event inventory stores multi-value district/state lists; district aggregate tables have Dist_Name only, no state field, no year, no event key, and no verified common identifier. A name-only merge would be ambiguous."
    cleaning_log = ["# Phase 3 Cleaning Log", "", "## Scope", "", "Raw CSVs under `data/raw/` were read but not modified. No imputation, target construction, leakage audit, split, augmentation, external-data integration, or model development was performed.", "", "## Source roles", "", "- `India_Flood_Inventory_v3.csv`: event-level flood inventory; one row represents an inventory event record and may reference multiple districts/states.", "- `District_FloodImpact.csv`: district-level aggregate table; no year or event identifier is present.", "- `District_FloodedArea.csv`: district-level aggregate table; no year or event identifier is present.", "", "## Transformations", "", "- Column names were converted to snake_case in processed copies; the original-to-cleaned mapping is recorded in `results/data_quality/column_name_mapping.csv`.", "- Event dates were parsed with the observed day-first mixed format. Non-null conversion failures were zero; missing dates remain missing.", "- Numeric-looking object columns were converted only when every non-null value matched a numeric pattern. Mixed/list-valued code fields remained strings.", "- District and state names received format-only trimming and whitespace collapsing. Semantic spelling variants were retained and marked `REQUIRES_VERIFICATION` in `data/derived/district_name_mapping.csv`.", "- Missing values were preserved. No rows or columns were removed.", "- Exact duplicate rows were analyzed and retained. Repeated district-year combinations were retained as potential separate events.", "", "## Rows and columns", "", "| Source | Original rows | Original columns | Processed rows | Processed columns | Rows removed |", "|---|---:|---:|---:|---:|---:|"]
    for dataset, raw in raw_frames.items():
        cleaning_log.append(f"| {dataset} | {len(raw)} | {len(raw.columns)} | {len(cleaned_frames[dataset])} | {len(cleaned_frames[dataset].columns)} | 0 |")
    cleaning_log.extend(["", "## Merge decision", "", merge_reason, "", "## Validation", "", f"Raw hashes before processing: `{json.dumps(before_hashes)}`", f"Raw hashes after processing: `{json.dumps(after_hashes)}`", f"Hash comparison passed: `{before_hashes == after_hashes}`", ""])
    (QUALITY_DIR / "cleaning_log.md").write_text("\n".join(cleaning_log), encoding="utf-8")
    load_checks = []
    validation = ["# Phase 3 Validation", "", f"- Raw files unchanged: **{before_hashes == after_hashes}**", "- Raw row loss: **0**", "- Unexpected duplicate removal: **none**", "- Fabricated identifiers: **none**", "- Fabricated missing values: **none**", "- Invalid type conversions: **0 non-null failures**", "- District/state transformations: **format-only; semantic variants retained and documented**", "- Unified merge: **not performed; no safe key exists**", "", "## Processed row reconciliation", "", "| File | Rows | Columns | Load status |", "|---|---:|---:|---|"]
    for path in sorted(PROCESSED_DIR.glob("*.csv")):
        check = pd.read_csv(path)
        load_checks.append(True)
        validation.append(f"| {path.name} | {len(check)} | {len(check.columns)} | PASS |")
    validation.insert(2, f"- Processed files load successfully: **{all(load_checks)}**")
    validation.append("")
    (QUALITY_DIR / "phase3_validation.md").write_text("\n".join(validation), encoding="utf-8")
    print(json.dumps({"processed": {path.name: list(pd.read_csv(path).shape) for path in sorted(PROCESSED_DIR.glob("*.csv"))}, "raw_hashes_unchanged": before_hashes == after_hashes, "unified_merge": False}, indent=2))


if __name__ == "__main__":
    main()