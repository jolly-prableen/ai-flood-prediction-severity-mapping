"""Audit cleaned IFI columns for future target construction; do not create targets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
QUALITY = ROOT / "results" / "data_quality"
FILES = ("ifi_event_clean.csv", "district_flood_impact_clean.csv", "district_flooded_area_clean.csv")


def parse_dates(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", format="mixed", dayfirst=True)


def column_policy(file: str, column: str, series: pd.Series) -> dict[str, str]:
    event = file == "ifi_event_clean.csv"
    category = "other"
    post = "UNKNOWN"
    prediction = "UNKNOWN"
    candidate = "NO"
    leakage = "UNKNOWN"
    units = "not documented"
    notes = "Meaning requires verification."
    if column in {"unnamed_0", "uei", "event_souce_id", "district_lgd_codes", "state_codes"}:
        category, prediction, leakage = "identifier", "not a predictive feature", "HIGH"
        notes = "Identifier/provenance field; retain for grouping or audit only, never as a model feature."
    elif column in {"districts", "state", "dist_name", "location", "latitude", "longitude"}:
        category, prediction, leakage = "location/geography", "potentially before event, but source timing/forecast-unit availability is unresolved", "MEDIUM"
        notes = "Geographic context or event-record location; do not treat observed event membership as a complete forecast frame."
    elif column in {"start_date", "end_date"}:
        category, post, prediction, leakage = "temporal information", "event reference", "start is target-time; end is after event", "HIGH"
        notes = "Event chronology only; not a predictive feature."
    elif column == "duration_days":
        category, post, prediction, candidate, leakage = "temporal information", "post-event", "after event", "TARGET_ONLY_CANDIDATE", "HIGH"
        units, notes = "days (source label)", "Observed event duration; potentially usable in a future severity/impact target after definition review."
    elif column == "main_cause":
        category, post, prediction, leakage = "event metadata", "unknown", "unknown; may be retrospective", "MEDIUM"
        notes = "Cause coding time and controlled vocabulary are undocumented; not a target candidate by itself."
    elif column in {"severity", "area_affected"}:
        category, post, prediction, candidate, leakage = ("flooded area" if column == "area_affected" else "other", "during/after event", "not available before event", "TARGET_ONLY_CANDIDATE", "HIGH")
        units, notes = ("source unit undocumented", "Direct source field is entirely missing in the cleaned inventory; possible target source only if later populated and defined.")
    elif column in {"human_fatality", "human_injured", "human_displaced", "animal_fatality"}:
        category, post, prediction, candidate, leakage = "human impact" if column in {"human_fatality", "human_injured", "human_displaced"} else "environmental impact", "during/after event", "not available before event", "TARGET_ONLY_CANDIDATE", "HIGH"
        units = "persons/animals; source units require verification"
        notes = "Post-event consequence field; may contribute to Severity_Score but cannot be a predictive feature."
    elif column in {"description_of_casualties_injured", "extent_of_damage"}:
        category, post, prediction, candidate, leakage = "human impact" if column == "description_of_casualties_injured" else "infrastructure/property impact", "after/during event", "not available before event", "TARGET_ONLY_CANDIDATE", "HIGH"
        notes = "Free-text post-event evidence; requires a predeclared coding rubric before target construction."
    elif column in {"percent_flooded_area", "corrected_percent_flooded_area"}:
        category, post, prediction, candidate, leakage = "flooded area", "during/after event or unknown reference period", "reference period unknown; not safe before event", "TARGET_ONLY_CANDIDATE", "HIGH"
        units, notes = "percent of district area (source label; exact method requires verification)", "District aggregate flooded-area measurement; possible regression target and Severity_Score component, not a predictive feature."
    elif column == "mean_flood_duration":
        category, post, prediction, candidate, leakage = "flooded area", "likely post-event; reference period unknown", "reference period unknown", "TARGET_ONLY_CANDIDATE", "HIGH"
        units, notes = "days (source label)", "District aggregate outcome-like measure with undocumented reference period; do not merge into event features."
    elif column == "population":
        category, post, prediction, candidate, leakage = "human impact", "baseline if vintage is verified", "potentially before event; reference year unknown", "POTENTIAL_FEATURE_AFTER_VERIFICATION", "MEDIUM"
        units, notes = "persons", "Potential exposure covariate only after source vintage and district alignment are verified; not an impact target."
    elif column == "parmanent_water":
        category, post, prediction, candidate, leakage = "environmental impact", "baseline if vintage is verified", "potentially before event; vintage unknown", "POTENTIAL_FEATURE_AFTER_VERIFICATION", "MEDIUM"
        units, notes = "source unit undocumented", "Potential static water feature; spelling and provenance are source-defined and require verification."
    elif column == "event_source":
        category, prediction, leakage = "event metadata", "collection metadata, not a physical predictor", "MEDIUM"
        notes = "Source is constant in the current file and should not be used as a feature or target."
    else:
        notes = "No target interpretation established."
    if series.isna().mean() == 1:
        notes += " Entirely missing in this file."
        if candidate == "TARGET_ONLY_CANDIDATE":
            candidate = "TARGET_ONLY_CANDIDATE_BUT_CURRENTLY_UNUSABLE"
    return {"category": category, "post_event_status": post, "prediction_time_status": prediction, "target_candidate_status": candidate, "leakage_risk": leakage, "units": units, "notes": notes}


def stat_value(value: Any) -> Any:
    if pd.isna(value):
        return ""
    if hasattr(value, "item"):
        return value.item()
    return value


def markdown_table(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for _, row in frame.iterrows():
        values = [str(row[column]).replace("|", "\\|").replace("\n", " ") for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def main() -> None:
    QUALITY.mkdir(parents=True, exist_ok=True)
    rows = []
    frames: dict[str, pd.DataFrame] = {}
    for file in FILES:
        frame = pd.read_csv(PROCESSED / file)
        frames[file] = frame
        for column in frame.columns:
            series = frame[column]
            policy = column_policy(file, column, series)
            numeric = pd.api.types.is_numeric_dtype(series)
            if numeric and series.notna().any():
                minimum, maximum = stat_value(series.min()), stat_value(series.max())
                mean, median = stat_value(series.mean()), stat_value(series.median())
            elif column in {"start_date", "end_date"}:
                dates = parse_dates(series).dropna()
                minimum = dates.min().isoformat() if not dates.empty else ""
                maximum = dates.max().isoformat() if not dates.empty else ""
                mean = median = ""
            else:
                minimum = maximum = mean = median = ""
            rows.append({
                "file": file,
                "column": column,
                "dtype": str(series.dtype),
                "rows": len(frame),
                "missing_count": int(series.isna().sum()),
                "missing_pct": round(float(series.isna().mean() * 100), 4),
                "unique_count": int(series.nunique(dropna=False)),
                "min": minimum,
                "max": maximum,
                "mean": mean,
                "median": median,
                "units": policy["units"],
                **policy,
            })
    inventory = pd.DataFrame(rows)
    inventory.to_csv(QUALITY / "phase10_target_variable_inventory.csv", index=False)
    report = [
        "# Phase 10 Target Audit",
        "",
        "## A. Purpose",
        "",
        "This audit inventories the cleaned IFI columns and evaluates their eligibility for future target construction. It does not create `Flood_Binary`, `Severity_Score`, `Severity_Class`, labels, splits, or model inputs. Post-event fields may be target components but are prohibited predictive features.",
        "",
        "## B. Files inspected",
        "",
        *[f"- `data/processed/{file}`: {len(frame):,} rows, {len(frame.columns)} columns." for file, frame in frames.items()],
        "",
        "## C. Complete column inventory",
        "",
        markdown_table(inventory),
        "",
        "## D. Candidate target variables",
        "",
        "Potential candidates actually present are `duration_days`, event human/animal impact fields, casualty and damage text, `percent_flooded_area`, `corrected_percent_flooded_area`, `mean_flood_duration`, and the source fields `severity` and `area_affected` (currently entirely missing). Event dates are reference fields for occurrence assignment, not severity measurements.",
        "",
        "## E. Human-impact variables",
        "",
        "The event inventory contains `human_fatality`, `human_injured`, `human_displaced`, `animal_fatality`, and casualty/injury descriptions. The district impact table contains aggregate `human_fatality` and `human_injured`. These are post-event or during-event consequences and are target-only candidates after unit, aggregation, and reference-period review.",
        "",
        "## F. Flooded-area variables",
        "",
        "`percent_flooded_area` and `corrected_percent_flooded_area` are directly present in `district_flooded_area_clean.csv`, complete across 732 rows, and have 730 unique values each. They are district-level aggregate measurements with no documented reference period in the current repository. `corrected_percent_flooded_area` is suitable as a possible regression target after provenance/method verification and may contribute to Severity_Score; using it as a feature would be direct target leakage.",
        "",
        "## G. Post-event variables",
        "",
        "Post-event or outcome-like fields include end date, duration, fatalities, injuries, displacement, animal fatalities, casualty descriptions, damage extent, flooded-area percentages, corrected flooded area, mean flood duration, and likely affected area/severity fields. They must not be predictive features.",
        "",
        "## H. Missingness and quality assessment",
        "",
        "The event inventory has 100% missing `location`, `latitude`, `longitude`, `severity`, `area_affected`, and `event_souce_id`; these cannot currently support target construction. `human_injured` is 84.61% missing, `human_displaced` 98.23% missing, and `animal_fatality` 91.70% missing. District `mean_flood_duration` has 11 missing values (1.50%). No missing values occur in the flooded-area table.",
        "",
        "## I. Identifier assessment",
        "",
        "`uei` is unique and suitable for event grouping, duplicate checks, and target-reference linkage only. `unnamed_0`, source IDs, LGD/code strings, district names, and state names must not become model features. District plus year is not a unique event identity.",
        "",
        "## J. Target-leakage assessment",
        "",
        "All impact and post-event fields are target-only candidates or unusable, not predictors. The district aggregate tables cannot be used as predictors until their reference period and event overlap are established. Absence from the event inventory cannot create a negative target.",
        "",
        "## K. Variables potentially suitable for Severity_Score",
        "",
        "Strongest candidates for later review are `corrected_percent_flooded_area`, `percent_flooded_area`, `duration_days`, `human_fatality`, `human_injured`, and possibly displacement/damage components if their missingness and semantics are resolved. A score formula, weighting, units, aggregation level, and missingness policy must be approved first. `corrected_percent_flooded_area` is the strongest currently complete direct impact candidate, but its reference period and correction method remain undocumented.",
        "",
        "## L. Variables that should NOT be used",
        "",
        "Do not use `uei`, row indices, source IDs, event dates as predictors, any post-event impact field, flooded-area measures, damage/casualty text, unverified aggregate fields, or future-derived statistics as predictive features. Do not use entirely missing severity/area fields until their source values are restored and defined.",
        "",
        "## M. Open methodological questions",
        "",
        "- What exact reference period and derivation produced the district flooded-area tables?",
        "- Is `corrected_percent_flooded_area` directly observed, remotely corrected, or derived from another source, and what does it correct?",
        "- Which impact variables and units should enter Severity_Score, and how should missing impacts be handled without interpreting missing as zero?",
        "- Will targets be district-week or district-event, and how will multi-district events be assigned?",
        "- What independent non-event frame will support Flood_Binary?",
        "- How will the 20 missing event start dates be handled for target assignment?",
        "",
        "## N. Recommendation for next phase",
        "",
        "Do not generate targets yet. First document the flooded-area provenance/reference period, approve the Severity_Score rubric, establish the district-week observation and negative frame, and decide the missing-impact policy. Keep all audited columns available for provenance but exclude post-event fields from predictive features.",
    ]
    (QUALITY / "phase10_target_audit.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({
        "files_inspected": list(FILES),
        "columns_inspected": len(inventory),
        "candidate_target_columns": inventory[inventory.target_candidate_status.str.startswith("TARGET_ONLY")]["column"].drop_duplicates().tolist(),
        "severity_score_candidates": ["corrected_percent_flooded_area", "percent_flooded_area", "duration_days", "human_fatality", "human_injured"],
        "serious_leakage_columns": inventory[inventory.leakage_risk == "HIGH"]["column"].drop_duplicates().tolist(),
    }, indent=2, default=str))


if __name__ == "__main__":
    main()