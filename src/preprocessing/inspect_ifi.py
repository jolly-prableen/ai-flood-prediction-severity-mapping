"""Inspect every raw IFI CSV and write Phase 2 quality and relationship reports."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
QUALITY_DIR = ROOT / "results" / "data_quality"
DICTIONARY_PATH = ROOT / "research" / "data_dictionary.md"
DETAILED_JSON = QUALITY_DIR / "ifi_detailed_inspection.json"
DETAILED_MARKDOWN = QUALITY_DIR / "ifi_detailed_inspection.md"
DATE_TERMS = ("date", "year", "time")
IDENTIFIER_TERMS = ("id", "code", "uei", "key", "index", "unnamed")

MEANINGS = {
    "Start Date": "Flood event start date, based on the source column label.",
    "End Date": "Flood event end date, based on the source column label.",
    "Duration(Days)": "Flood event duration in days, based on the source column label.",
    "Main Cause": "Recorded main cause of the event; the coding and controlled vocabulary require verification.",
    "Districts": "District names associated with an inventory record; values can contain comma-separated names.",
    "State": "State names associated with an inventory record; values can contain comma-separated names.",
    "Human fatality": "Human fatality count associated with an event, based on the source column label.",
    "Human injured": "Human injury count associated with an event, based on the source column label.",
    "Human Displaced": "Human displacement value associated with an event; representation and units require verification.",
    "Animal Fatality": "Animal fatality value associated with an event; representation and units require verification.",
    "Description of Casualties/injured": "Free-text description of casualties or injuries, based on the source column label.",
    "Extent of damage ": "Free-text or coded extent-of-damage field; representation requires verification.",
    "District_LGD_Codes": "District LGD code field as labeled by the source; values can contain comma-separated codes and require codebook verification.",
    "State_Codes": "State code field as labeled by the source; values can contain comma-separated codes and require codebook verification.",
    "Dist_Name": "District name, based on the source column label.",
    "Human_fatality": "Human fatality aggregate, based on the source column label; aggregation method requires verification.",
    "Human_injured": "Human injury aggregate, based on the source column label; aggregation method requires verification.",
    "Population": "Population value associated with the district table; reference year and source require verification.",
    "Mean_Flood_Duration": "Mean flood duration associated with the district table; aggregation period and units require verification.",
    "Percent_Flooded_Area": "Percentage of district area reported as flooded, based on the source column label; reference period requires verification.",
    "Parmanent_Water": "Permanent-water measure as spelled in the source; units and reference period require verification.",
    "Corrected_Percent_Flooded_Area": "Corrected percentage of district area reported as flooded, based on the source column label; method and reference period require verification.",
}


def as_json(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    if not isinstance(value, (list, dict, tuple)) and pd.isna(value):
        return None
    return value


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def split_values(series: pd.Series) -> set[str]:
    values: set[str] = set()
    for raw in series.dropna().astype(str):
        values.update(part.strip() for part in raw.split(",") if part.strip() and part.strip().lower() != "none")
    return values


def parse_dates(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", format="mixed", dayfirst=True)


def date_details(frame: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in frame.columns:
        if not any(term in column.lower() for term in DATE_TERMS):
            continue
        parsed = parse_dates(frame[column])
        valid = parsed.dropna()
        if valid.empty:
            result[column] = {"valid_count": 0, "invalid_count": int(frame[column].notna().sum())}
            continue
        result[column] = {
            "valid_count": int(valid.size),
            "invalid_count": int(frame[column].notna().sum() - valid.size),
            "minimum": valid.min().date().isoformat(),
            "maximum": valid.max().date().isoformat(),
            "minimum_year": int(valid.dt.year.min()),
            "maximum_year": int(valid.dt.year.max()),
        }
    return result


def column_record(dataset: str, column: str, series: pd.Series) -> dict[str, Any]:
    numeric = pd.api.types.is_numeric_dtype(series)
    record: dict[str, Any] = {
        "dataset": dataset,
        "column": column,
        "dtype": str(series.dtype),
        "missing_count": int(series.isna().sum()),
        "missing_percent": round(float(series.isna().mean() * 100), 4),
        "unique_count": int(series.nunique(dropna=False)),
        "min_value": None,
        "max_value": None,
    }
    if numeric and series.notna().any():
        record["min_value"] = as_json(series.min())
        record["max_value"] = as_json(series.max())
    return record


def suspicious_values(frame: pd.DataFrame) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for column in frame.select_dtypes(include="number").columns:
        series = frame[column]
        normalized = column.casefold()
        if any(term in normalized for term in ("percent", "area")):
            count = int(((series < 0) | (series > 100)).sum())
            if count:
                findings.append({"column": column, "issue": "values outside the 0-100 percentage range", "count": count})
        if any(term in normalized for term in ("fatality", "injured", "population", "duration", "water")):
            count = int((series < 0).sum())
            if count:
                findings.append({"column": column, "issue": "negative value", "count": count})
        if normalized == "latitude":
            count = int(((series < -90) | (series > 90)).sum())
            if count:
                findings.append({"column": column, "issue": "latitude outside [-90, 90]", "count": count})
        if normalized == "longitude":
            count = int(((series < -180) | (series > 180)).sum())
            if count:
                findings.append({"column": column, "issue": "longitude outside [-180, 180]", "count": count})
    for column in frame.columns:
        if any(term in column.lower() for term in DATE_TERMS):
            parsed = parse_dates(frame[column])
            suspicious = parsed.notna() & ((parsed.dt.year < 1900) | (parsed.dt.year > 2026))
            if suspicious.any():
                findings.append({"column": column, "issue": "date year outside 1900-2026", "count": int(suspicious.sum())})
    return findings


def name_variants(frame: pd.DataFrame, columns: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in columns:
        variants: defaultdict[str, set[str]] = defaultdict(set)
        for raw in split_values(frame[column]):
            variants[normalize_name(raw)].add(raw)
        ambiguous = {key: sorted(values) for key, values in variants.items() if len(values) > 1}
        result[column] = {"normalized_names_with_multiple_spellings": len(ambiguous), "examples": dict(list(ambiguous.items())[:20])}
    return result


def duplicate_key_summary(frame: pd.DataFrame, columns: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in columns:
        counts = frame[column].dropna().value_counts()
        repeated = counts[counts > 1]
        result[column] = {
            "non_null_unique": int(frame[column].nunique(dropna=True)),
            "duplicate_value_count": int(repeated.size),
            "duplicate_row_count": int(repeated.sum() - repeated.size),
            "examples": {str(key): int(value) for key, value in repeated.head(20).items()},
        }
    return result


def inspect_frame(dataset: str, frame: pd.DataFrame) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records = [column_record(dataset, column, frame[column]) for column in frame.columns]
    identifier_columns = [column for column in frame.columns if any(term in column.lower() for term in IDENTIFIER_TERMS)]
    categorical_columns = [column for column in frame.columns if pd.api.types.is_object_dtype(frame[column]) or pd.api.types.is_string_dtype(frame[column])]
    numerical_columns = [column for column in frame.columns if pd.api.types.is_numeric_dtype(frame[column])]
    state_columns = [column for column in frame.columns if column.lower() in {"state", "state_codes", "st_nm"}]
    district_columns = [column for column in frame.columns if column.lower() in {"districts", "dist_name", "district", "district_lgd_codes", "dt_cen_cd"}]
    summary = {
        "filename": dataset,
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "exact_column_names": list(frame.columns),
        "dtypes": {column: str(value) for column, value in frame.dtypes.items()},
        "missing_values": {column: int(value) for column, value in frame.isna().sum().items()},
        "missing_percentages": {column: round(float(value), 4) for column, value in (frame.isna().mean() * 100).items()},
        "unique_counts": {column: int(value) for column, value in frame.nunique(dropna=False).items()},
        "numeric_minimums": {column: as_json(frame[column].min()) for column in numerical_columns if frame[column].notna().any()},
        "numeric_maximums": {column: as_json(frame[column].max()) for column in numerical_columns if frame[column].notna().any()},
        "date_coverage": date_details(frame),
        "unique_states": sorted(split_values(frame[state_columns[0]])) if state_columns else [],
        "unique_districts": sorted(split_values(frame[district_columns[0]])) if district_columns else [],
        "identifier_columns": identifier_columns,
        "categorical_columns": categorical_columns,
        "numerical_columns": numerical_columns,
        "duplicate_rows": int(frame.duplicated().sum()),
        "duplicate_identifiers": duplicate_key_summary(frame, identifier_columns),
        "name_variants": name_variants(frame, state_columns + district_columns),
        "suspicious_values": suspicious_values(frame),
    }
    if "Start Date" in frame.columns and "Districts" in frame.columns:
        years = parse_dates(frame["Start Date"]).dt.year
        keys = pd.DataFrame({"districts": frame["Districts"], "year": years}).dropna()
        counts = keys.value_counts()
        repeated = counts[counts > 1]
        summary["duplicate_district_year_combinations"] = {
            "available_rows": int(len(keys)),
            "duplicate_combination_count": int(repeated.size),
            "duplicate_row_count": int(repeated.sum() - repeated.size),
            "examples": [{"districts": str(key[0]), "year": int(key[1]), "count": int(value)} for key, value in repeated.head(20).items()],
        }
    else:
        summary["duplicate_district_year_combinations"] = {"available": False}
    return summary, records


def relationship_report(frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    names = list(frames)
    common_columns = {f"{left} & {right}": sorted(set(frames[left].columns) & set(frames[right].columns)) for index, left in enumerate(names) for right in names[index + 1:]}
    inventory = frames.get("India_Flood_Inventory_v3.csv")
    district_tables = [frames[name] for name in names if "Dist_Name" in frames[name].columns]
    name_comparisons = []
    if inventory is not None and "Districts" in inventory.columns:
        inventory_names = split_values(inventory["Districts"])
        inventory_normalized = {normalize_name(value) for value in inventory_names}
        for table in district_tables:
            table_names = split_values(table["Dist_Name"])
            exact = sorted(set(inventory_names) & table_names)
            normalized = sorted(value for value in table_names if normalize_name(value) in inventory_normalized)
            name_comparisons.append({
                "inventory_field": "Districts",
                "district_table_field": "Dist_Name",
                "table_rows": int(len(table)),
                "inventory_distinct_tokens": len(inventory_names),
                "table_distinct_names": len(table_names),
                "exact_name_matches": len(exact),
                "normalized_name_matches": len(normalized),
                "unmatched_table_names": sorted(set(table_names) - set(normalized))[:50],
                "candidate_key": "normalized district name only; not unique or sufficient without state context",
            })
    return {
        "common_exact_columns": common_columns,
        "candidate_keys": [
            {"fields": ["Districts", "Dist_Name"], "status": "possible after tokenization and name normalization; ambiguous and not a safe merge key alone"},
            {"fields": ["District_LGD_Codes"], "status": "identifier-like in inventory only; no corresponding field in current district tables"},
            {"fields": ["State_Codes"], "status": "identifier-like in inventory only; no corresponding field in current district tables"},
            {"fields": ["State", "Dist_Name"], "status": "state context is needed, but current district tables have no state column"},
        ],
        "name_comparisons": name_comparisons,
        "merge_performed": False,
    }


def write_dictionary(frames: dict[str, pd.DataFrame], records: list[dict[str, Any]]) -> None:
    lines = [
        "# IFI-Impacts v3 Data Dictionary",
        "",
        "This dictionary was regenerated from every CSV currently present in `data/raw/`. Descriptions are limited to meanings supported by the source header or the official IFI record; uncertain semantics are explicitly marked for verification.",
        "",
    ]
    for dataset in frames:
        lines.extend([f"## {dataset}", "", "| Column | Data type | Meaning | Missing | Unique | Notes |", "|---|---|---|---:|---:|---|"])
        for record in [item for item in records if item["dataset"] == dataset]:
            meaning = MEANINGS.get(record["column"], "Meaning requires verification from the dataset documentation or source codebook.")
            notes = "Raw field; preserved unchanged."
            if record["column"].strip() != record["column"]:
                notes += " Source header contains surrounding whitespace."
            lines.append(f"| {record['column']} | {record['dtype']} | {meaning} | {record['missing_percent']}% | {record['unique_count']} | {notes} |")
        lines.append("")
    DICTIONARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# IFI v3 Detailed Inspection",
        "",
        "Generated from every CSV currently present in `data/raw/`. Raw files were read only and were not modified. No merge, cleaning, imputation, split, augmentation, or modeling was performed.",
        "",
        "## Dataset dimensions and coverage",
        "",
    ]
    for name, summary in report["datasets"].items():
        lines.extend([f"### `{name}`", "", f"- Rows: {summary['rows']}", f"- Columns: {summary['columns']}", f"- Duplicate rows: {summary['duplicate_rows']}", f"- Unique states: {len(summary['unique_states'])}", f"- Unique districts: {len(summary['unique_districts'])}", f"- Date/year coverage: `{json.dumps(summary['date_coverage'], default=str)}`", f"- Identifier columns: `{', '.join(summary['identifier_columns']) or 'none detected by name'}`", f"- Categorical columns: `{', '.join(summary['categorical_columns']) or 'none'}`", f"- Numerical columns: `{', '.join(summary['numerical_columns']) or 'none'}`", "", "| Column | dtype | missing | missing % | unique | minimum | maximum |", "|---|---|---:|---:|---:|---|---|"])
        for record in [item for item in report["column_summary"] if item["dataset"] == name]:
            lines.append(f"| {record['column']} | {record['dtype']} | {record['missing_count']} | {record['missing_percent']}% | {record['unique_count']} | {record['min_value'] if record['min_value'] is not None else ''} | {record['max_value'] if record['max_value'] is not None else ''} |")
        lines.append("")
    lines.extend(["## Relationship and key assessment", "", "- Inventory district and state fields contain comma-separated values; they are not one-row-per-district keys.", "- `Districts` and `Dist_Name` are possible name-based candidates only after tokenization and normalization, and require state context because names are not unique globally.", "- `District_LGD_Codes` and `State_Codes` occur in the inventory but have no corresponding fields in the current district tables.", "- No merge was performed.", "", "## Quality and anomaly findings", ""])
    for name, summary in report["datasets"].items():
        if summary["suspicious_values"]:
            lines.append(f"- `{name}` suspicious values: `{json.dumps(summary['suspicious_values'])}`")
        else:
            lines.append(f"- `{name}`: no numeric-range or date-year violations detected by the conservative checks.")
        if summary["duplicate_district_year_combinations"].get("available") is not False:
            lines.append(f"- `{name}` duplicate district-year check: `{json.dumps(summary['duplicate_district_year_combinations'])}`")
        variants = {field: value for field, value in summary["name_variants"].items() if value["normalized_names_with_multiple_spellings"]}
        if variants:
            lines.append(f"- `{name}` name variants after normalization: `{json.dumps(variants)}`")
    lines.extend(["", "## Relationship results", "", f"```json\n{json.dumps(report['relationships'], indent=2)}\n```", ""])
    return "\n".join(lines)


def main() -> None:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    paths = sorted(RAW_DIR.glob("*.csv"))
    if not paths:
        raise FileNotFoundError(f"No CSV files found in {RAW_DIR}")
    frames = {path.name: pd.read_csv(path) for path in paths}
    summaries: dict[str, Any] = {}
    records: list[dict[str, Any]] = []
    for name, frame in frames.items():
        summary, column_records = inspect_frame(name, frame)
        summaries[name] = summary
        records.extend(column_records)
    report = {
        "source": "https://zenodo.org/records/11275211",
        "raw_files_inspected": [path.name for path in paths],
        "datasets": summaries,
        "relationships": relationship_report(frames),
        "column_summary": records,
    }
    DETAILED_JSON.write_text(json.dumps(report, indent=2, default=as_json) + "\n", encoding="utf-8")
    pd.DataFrame(records, columns=["dataset", "column", "dtype", "missing_count", "missing_percent", "unique_count", "min_value", "max_value"]).to_csv(QUALITY_DIR / "ifi_column_summary.csv", index=False)
    DETAILED_MARKDOWN.write_text(markdown_report(report), encoding="utf-8")
    write_dictionary(frames, records)
    print(json.dumps({name: {"rows": value["rows"], "columns": value["columns"], "duplicate_rows": value["duplicate_rows"]} for name, value in summaries.items()}, indent=2))


if __name__ == "__main__":
    main()