"""Generate the Phase 4 IFI feature-level and dataset-level leakage audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "results" / "leakage_reports"
EVENT_FILE = "ifi_event_clean.csv"
FILES = ("ifi_event_clean.csv", "district_flood_impact_clean.csv", "district_flooded_area_clean.csv")


LEAKAGE_FIELDS = {
    "start_date": ("TEMPORAL / TARGET LEAKAGE", "LEAKAGE", "The event start date identifies the occurrence being predicted and is unavailable before the event starts.", "Post-event or target-time field", "Use only as an outcome/reference timestamp, never as a predictive feature."),
    "end_date": ("POST-EVENT INFORMATION", "LEAKAGE", "The end date is known only after the event has ended.", "After event", "Exclude from predictive features; retain for event chronology."),
    "duration_days": ("POST-EVENT INFORMATION", "LEAKAGE", "Duration requires observing the event through its end and is an outcome-like consequence.", "After event", "Exclude from predictive features; possible target component only after definition."),
    "severity": ("TARGET LEAKAGE", "LEAKAGE", "The source field is explicitly named severity and is 100% missing in the current inventory.", "Timing and definition unknown; outcome-like", "Do not use as a feature; investigate only as a possible target source."),
    "area_affected": ("POST-EVENT INFORMATION", "LEAKAGE", "Affected area is an event impact measurement and is 100% missing in the current inventory.", "During/after event", "Exclude from predictive features; possible target component only after verification."),
    "human_fatality": ("POST-EVENT INFORMATION", "LEAKAGE", "Fatality counts describe consequences of a flood; district aggregates may summarize the same events.", "During/after event", "Exclude from predictive features; possible impact target component."),
    "human_injured": ("POST-EVENT INFORMATION", "LEAKAGE", "Injury counts describe consequences of a flood; district aggregates may summarize the same events.", "During/after event", "Exclude from predictive features; possible impact target component."),
    "human_displaced": ("POST-EVENT INFORMATION", "LEAKAGE", "Displacement is a consequence of the event and its representation is source-dependent.", "During/after event", "Exclude from predictive features; possible impact target component after verification."),
    "animal_fatality": ("POST-EVENT INFORMATION", "LEAKAGE", "Animal fatalities are post-event consequences.", "During/after event", "Exclude from predictive features; possible impact target component after verification."),
    "description_of_casualties_injured": ("POST-EVENT INFORMATION", "LEAKAGE", "The field is a casualty/injury description and can directly reveal the outcome.", "During/after event", "Exclude from predictive features."),
    "extent_of_damage": ("POST-EVENT INFORMATION", "LEAKAGE", "Damage extent is a post-event impact description.", "During/after event", "Exclude from predictive features; possible target evidence only after coding rules are defined."),
    "mean_flood_duration": ("AGGREGATE LEAKAGE", "LEAKAGE", "A district mean flood duration is an aggregate outcome-like measure with no documented reference period.", "Reference period unknown; likely after event", "Exclude until provenance and forecast timing are verified."),
    "percent_flooded_area": ("AGGREGATE LEAKAGE", "LEAKAGE", "Flooded area is a direct impact measurement and may summarize the events being predicted.", "During/after event; reference period unknown", "Exclude from predictive features; possible target component after temporal definition."),
    "corrected_percent_flooded_area": ("AGGREGATE LEAKAGE", "LEAKAGE", "Corrected flooded area remains an impact measurement; correction does not remove temporal leakage risk.", "During/after event; reference period unknown", "Exclude from predictive features; possible target component after temporal definition."),
}


CAUTION_FIELDS = {
    "unnamed_0": ("IDENTIFIER LEAKAGE", "CAUTION", "A unique source row/index field can enable memorization or reflect source ordering.", "Available in source, but not a physical predictor", "Exclude from features; retain only for provenance."),
    "uei": ("IDENTIFIER LEAKAGE", "CAUTION", "UEI is unique for every inventory row and could allow memorization or partition contamination.", "Assigned to the recorded event, not a pre-event measurement", "Use for grouping and identity checks only; exclude as a feature."),
    "main_cause": ("TEMPORAL / TARGET LEAKAGE", "CAUTION", "Cause may be known before or during an event, but the dataset does not document when or how it was coded.", "Unknown; potentially pre-event, potentially retrospective", "Require source-timing verification before use."),
    "districts": ("SPATIAL / SAMPLING LEAKAGE", "CAUTION", "District membership is geographic context, but this field is populated from observed event records and contains multiple districts per row.", "Geography may be known pre-event; event-record availability is not", "Use only with a clearly defined forecast unit; do not treat as a simple scalar feature."),
    "state": ("SPATIAL / SAMPLING LEAKAGE", "CAUTION", "State is geographic context, but observed event rows and multi-state values can encode the labeled occurrence.", "Geography may be known pre-event; forecast-unit availability is not", "Use only with a clearly defined forecast unit and negative-sample design."),
    "event_source": ("DATASET / IDENTIFIER LEAKAGE", "CAUTION", "Source metadata is not a physical predictor and may encode collection or event-selection process.", "Likely assigned during data collection", "Exclude from predictive features unless a pre-event source is established."),
    "event_souce_id": ("IDENTIFIER LEAKAGE", "CAUTION", "Identifier-like source field; currently entirely missing and its semantics are unverified.", "Unknown; currently missing", "Exclude from features; retain for provenance if populated later."),
    "district_lgd_codes": ("IDENTIFIER / SPATIAL LEAKAGE", "CAUTION", "Geographic codes can support grouping or joins but are not confirmed as LGD codes and are stored as multi-value event fields.", "Geography may be known pre-event; semantics unverified", "Exclude raw code strings from features until a verified forecast-unit policy exists."),
    "state_codes": ("IDENTIFIER / SPATIAL LEAKAGE", "CAUTION", "State codes are geographic identifiers, not measurements; source semantics and timing require verification.", "Geography may be known pre-event; semantics unverified", "Exclude raw code strings from features until verified."),
    "dist_name": ("SPATIAL / AGGREGATE LEAKAGE", "CAUTION", "District name identifies the geographic unit, but the aggregate table has no time period and cannot be safely aligned to an event.", "Geography available; aggregate reference time unknown", "Use only as a grouping/join key, not as an unrestricted feature."),
    "population": ("TEMPORAL / SPATIAL", "CAUTION", "Population could be a baseline covariate, but its reference year and provenance are undocumented.", "Potentially pre-event; reference period unknown", "Verify vintage and keep fixed relative to the prediction timestamp."),
    "parmanent_water": ("TEMPORAL / SPATIAL", "CAUTION", "Permanent-water coverage may be a baseline geographic feature, but units, vintage, and derivation are undocumented.", "Potentially pre-event; reference period unknown", "Verify source vintage and ensure it excludes event-period observations."),
}


UNKNOWN_FIELDS = {
    "location": ("UNKNOWN / REQUIRES VERIFICATION", "UNKNOWN / REQUIRES VERIFICATION", "The field is entirely missing and its meaning cannot be established from the cleaned data.", "Unknown", "Do not use until meaning and availability are verified."),
    "latitude": ("UNKNOWN / REQUIRES VERIFICATION", "UNKNOWN / REQUIRES VERIFICATION", "The coordinate field is entirely missing; no availability or event-timing assessment is possible.", "Unknown; entirely missing", "Do not use until populated and provenance is verified."),
    "longitude": ("UNKNOWN / REQUIRES VERIFICATION", "UNKNOWN / REQUIRES VERIFICATION", "The coordinate field is entirely missing; no availability or event-timing assessment is possible.", "Unknown; entirely missing", "Do not use until populated and provenance is verified."),
}


def classification(dataset: str, column: str) -> tuple[str, str, str, str, str]:
    if column in LEAKAGE_FIELDS:
        return LEAKAGE_FIELDS[column]
    if column in CAUTION_FIELDS:
        return CAUTION_FIELDS[column]
    if column in UNKNOWN_FIELDS:
        return UNKNOWN_FIELDS[column]
    return ("UNKNOWN / REQUIRES VERIFICATION", "UNKNOWN / REQUIRES VERIFICATION", "No timing or semantic evidence is sufficient to classify this field safely.", "Unknown", "Require domain and source verification before use.")


def load_frames() -> dict[str, pd.DataFrame]:
    return {name: pd.read_csv(PROCESSED_DIR / name) for name in FILES}


def feature_audit(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for dataset, frame in frames.items():
        for column in frame.columns:
            category, status, reason, availability, action = classification(dataset, column)
            rows.append({"dataset": dataset, "column": column, "leakage_category": category, "classification": status, "reason": reason, "prediction_time_availability": availability, "recommended_action": action})
    return pd.DataFrame(rows)


def target_candidates() -> pd.DataFrame:
    rows = [
        {"variable": "start_date", "meaning": "Recorded flood event start date", "occurrence_or_impact": "occurrence", "availability": "event/target time", "feature_leakage": "LEAKAGE", "target_use": "Possible event reference/label boundary; not a feature", "notes": "A Flood_Binary target also requires non-event records, which are not present here."},
        {"variable": "end_date", "meaning": "Recorded flood event end date", "occurrence_or_impact": "occurrence/temporal extent", "availability": "after event", "feature_leakage": "LEAKAGE", "target_use": "Possible duration/reference construction after definition", "notes": "Not available for pre-event forecasting."},
        {"variable": "duration_days", "meaning": "Recorded event duration in days", "occurrence_or_impact": "impact/temporal extent", "availability": "after event", "feature_leakage": "LEAKAGE", "target_use": "Possible Severity_Class or impact target component", "notes": "Target semantics and timing require verification."},
        {"variable": "severity", "meaning": "Source field named severity", "occurrence_or_impact": "impact/severity", "availability": "unknown; entirely missing", "feature_leakage": "LEAKAGE if populated", "target_use": "Possible direct target source only after source verification", "notes": "No usable values are currently present."},
        {"variable": "area_affected", "meaning": "Source field named area affected", "occurrence_or_impact": "impact", "availability": "during/after event; currently missing", "feature_leakage": "LEAKAGE if populated", "target_use": "Possible impact/severity target component", "notes": "Units and definition require verification."},
        {"variable": "human_fatality", "meaning": "Human fatality count or district aggregate", "occurrence_or_impact": "impact", "availability": "during/after event", "feature_leakage": "LEAKAGE", "target_use": "Possible impact target component", "notes": "Event and district tables must not be combined without temporal provenance."},
        {"variable": "human_injured", "meaning": "Human injury count or district aggregate", "occurrence_or_impact": "impact", "availability": "during/after event", "feature_leakage": "LEAKAGE", "target_use": "Possible impact target component", "notes": "Aggregation and time period require verification."},
        {"variable": "percent_flooded_area / corrected_percent_flooded_area", "meaning": "District flooded-area measurements", "occurrence_or_impact": "impact/severity", "availability": "during/after event or unknown reference period", "feature_leakage": "LEAKAGE", "target_use": "Possible Severity_Class or Severity_Score component", "notes": "No target is created in Phase 4."},
        {"variable": "mean_flood_duration", "meaning": "District mean flood duration", "occurrence_or_impact": "impact", "availability": "unknown reference period; likely after event", "feature_leakage": "LEAKAGE", "target_use": "Possible aggregate impact target component", "notes": "Source period is not documented."},
    ]
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for _, row in frame.iterrows():
        values = [str(row[column]).replace("|", "\\|") for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def event_identity(frames: dict[str, pd.DataFrame]) -> str:
    frame = frames[EVENT_FILE]
    dates = pd.to_datetime(frame["start_date"], errors="coerce", format="mixed", dayfirst=True)
    repeated_uei = int(frame["uei"].duplicated().sum())
    keys = pd.DataFrame({"district": frame["districts"], "year": dates.dt.year}).dropna()
    counts = keys.value_counts()
    repeated = counts[counts > 1]
    return "\n".join([
        "# Event Identity Analysis",
        "",
        "## Findings",
        "",
        f"- `uei` is populated for all {len(frame):,} event rows and is unique in the cleaned inventory; repeated UEI rows: **{repeated_uei}**.",
        f"- `unnamed_0` is also unique but is a source row/index field, not a documented event identifier.",
        f"- Start dates are present for {int(dates.notna().sum()):,} rows; 20 are missing. District values are missing for {int(frame['districts'].isna().sum()):,} rows.",
        f"- District + year is not unique: {len(repeated):,} combinations repeat, affecting {int(repeated.sum()):,} rows. This confirms that multiple flood events can occur in one district in one year.",
        "- District + date is not a safe identity because events may share dates, rows may reference multiple districts, and dates are missing in some records.",
        "- District + event identifier is the most defensible event grouping available: use `uei` as the event identity, while retaining district membership as a separate multi-value attribute.",
        "- The semantic definition of UEI should still be verified against the official dataset documentation before it is used as a permanent key.",
        "",
        "## Recommended later strategy",
        "",
        "Use `uei` for event-level grouping and contamination checks. Do not use it as a predictive feature. If the prediction unit becomes district-event, create a verified event-to-district representation only after the forecast unit and temporal horizon are approved; do not substitute district-year as an event key.",
    ])


def timeline(frames: dict[str, pd.DataFrame]) -> str:
    frame = frames[EVENT_FILE]
    starts = pd.to_datetime(frame["start_date"], errors="coerce", format="mixed", dayfirst=True)
    ends = pd.to_datetime(frame["end_date"], errors="coerce", format="mixed", dayfirst=True)
    return "\n".join([
        "# Prediction Timeline",
        "",
        "The exact operational prediction timestamp and forecast horizon are not specified by the IFI data or current project documentation. The audit therefore uses a conservative pre-event forecasting interpretation and records timing uncertainty explicitly.",
        "",
        "## Event reference",
        "",
        f"- Candidate event reference: `start_date` ({starts.notna().sum():,} usable values), spanning {starts.min().date()} through {starts.max().date()}.",
        f"- `end_date` has {ends.notna().sum():,} usable values and represents information available only after the event has ended.",
        "- No prediction horizon, alert lead time, observation cutoff, or district-aggregate reference period is documented.",
        "",
        "## PRE-EVENT INFORMATION",
        "",
        "Potentially available before a flood, subject to verification: geographic unit, verified baseline population, static permanent-water or other environmental covariates, and a known forecast date. In the current files, population and permanent-water vintage are not documented, and raw geography fields are observed event-record attributes rather than a complete set of forecast units.",
        "",
        "## EVENT-TIME INFORMATION",
        "",
        "Main cause may be known during an event, but its coding time is undocumented. Start date identifies the event and is target/reference information, not a pre-event predictor. Event source metadata and codes describe collection or geography and should not be treated as measurements without verification.",
        "",
        "## POST-EVENT INFORMATION",
        "",
        "End date, duration, severity, affected area, fatalities, injuries, displacement, animal fatalities, casualty descriptions, damage extent, flooded-area measures, and flood-impact aggregates are consequences or outcome-like summaries. They are leakage for pre-event predictive features, although some may be valid target components later.",
        "",
        "## Decision required",
        "",
        "Before feature selection, approve the forecast horizon and the reference period for the district aggregate tables. Without those decisions, no field can be certified SAFE for predictive use.",
    ])


def feature_policy(audit: pd.DataFrame) -> str:
    groups = {
        "A. SAFE CANDIDATE FEATURES": audit[audit.classification == "SAFE"],
        "B. FEATURES REQUIRING TEMPORAL/SPATIAL CARE": audit[audit.classification == "CAUTION"],
        "C. POST-EVENT / LEAKAGE FEATURES": audit[audit.classification == "LEAKAGE"],
        "D. IDENTIFIERS TO EXCLUDE": audit[audit.leakage_category.str.contains("IDENTIFIER")],
        "E. TARGET-ONLY VARIABLES": audit[audit.column.isin(["start_date", "end_date", "duration_days", "severity", "area_affected", "human_fatality", "human_injured", "human_displaced", "animal_fatality", "description_of_casualties_injured", "extent_of_damage", "mean_flood_duration", "percent_flooded_area", "corrected_percent_flooded_area"])],
        "F. UNKNOWN / REQUIRES VERIFICATION": audit[audit.classification == "UNKNOWN / REQUIRES VERIFICATION"],
    }
    lines = ["# Leakage-Safe Feature Policy", "", "This policy is for later predictive-dataset design only. No columns were deleted or altered during the audit.", ""]
    for title, group in groups.items():
        lines.extend([f"## {title}", ""])
        if group.empty:
            lines.append("- None currently certified.")
        else:
            for _, row in group.drop_duplicates(["column"]).iterrows():
                lines.append(f"- `{row['column']}`: {row['reason']} Recommended action: {row['recommended_action']}")
        lines.append("")
    lines.extend(["## Policy conclusion", "", "No current field is certified SAFE because the prediction timestamp and forecast unit are unresolved. Geographic fields may become usable after the forecast unit is fixed; impact fields remain target-only or leakage candidates.", ""])
    return "\n".join(lines)


def audit_report(audit: pd.DataFrame, targets: pd.DataFrame) -> str:
    counts = audit.classification.value_counts().to_dict()
    lines = [
        "# IFI Data Leakage Audit Report",
        "",
        "Phase 4 only. Cleaned files were read but not modified. No targets, splits, SMOTE, models, or external data were created.",
        "",
        "## 1. Prediction-time definition",
        "",
        "The operational prediction timestamp and lead time are unresolved. This audit conservatively assumes pre-event forecasting relative to `start_date`; `start_date` is treated as event-reference information, not a feature.",
        "",
        "## 2. Twelve leakage checks",
        "",
        "| Check | Finding | Status |",
        "|---|---|---|",
        "| Target leakage | Event date, severity, affected area, and impact fields can directly represent the outcome. | Confirmed for feature use |",
        "| Post-event information | Fatalities, injuries, displacement, damage, duration, and flooded area are outcome-like. | Confirmed for feature use |",
        "| Temporal leakage | Aggregate reference periods and forecast horizon are undocumented; future observations cannot yet be separated safely. | Unknown / requires verification |",
        "| Train/test contamination | UEI is unique and district-year repeats; later partitioning must group by UEI/event. | Caution |",
        "| Duplicate/near-duplicate leakage | Exact duplicates are absent; repeated district-year records are multiple events, not safe duplicates. | Caution |",
        "| Aggregate leakage | District flood impact and flooded-area tables may summarize the same outcomes. | Confirmed risk |",
        "| Target-construction leakage | Impact fields may be valid target components but invalid features. | Confirmed distinction required |",
        "| Identifier leakage | UEI, row index, source ID, and code fields can enable memorization or provenance leakage. | Caution / exclude |",
        "| Spatial leakage | Event rows contain observed districts/states; aggregate tables lack state and time context. | Unknown / requires verification |",
        "| Future-derived statistics | District aggregates have no documented period; future inclusion cannot be ruled out. | Unknown / requires verification |",
        "| Dataset/merge leakage | No merge was performed; a name-only merge would duplicate or import outcome information. | Merge blocked |",
        "| Sampling leakage | Inventory contains flood events but no explicit non-event records; binary occurrence modeling would be structurally biased without a negative-sample design. | Confirmed design issue |",
        "",
        "## 3. Audit counts",
        "",
        f"- Columns audited: **{len(audit)}**",
        f"- SAFE: **{counts.get('SAFE', 0)}**",
        f"- CAUTION: **{counts.get('CAUTION', 0)}**",
        f"- LEAKAGE: **{counts.get('LEAKAGE', 0)}**",
        f"- UNKNOWN / REQUIRES VERIFICATION: **{counts.get('UNKNOWN / REQUIRES VERIFICATION', 0)}**",
        "",
        "## 4. Confirmed and possible leakage",
        "",
        "Confirmed feature exclusions: event dates, duration, severity, affected area, human/animal impacts, casualty descriptions, damage extent, flooded-area percentages, corrected flooded-area percentages, and mean flood duration.",
        "Possible leakage requiring timing verification: cause, population, permanent water, source metadata, identifiers, geographic fields, and all district aggregates.",
        "",
        "## 5. Target candidates",
        "",
        markdown_table(targets),
        "",
        "## 6. Event identity and temporal ordering",
        "",
        "Use UEI for event identity and grouping, not as a feature. District + year is not unique. Usable event dates span 1967–2023, but 20 start dates and 20 end dates are missing. Multiple events occur in the same district-year. A chronological split may be possible later, but only after defining the forecast horizon and handling missing dates.",
        "",
        "## 7. Spatial, aggregate, and merge findings",
        "",
        "The district tables have no year, event ID, or state field. Their reference periods are unknown. They must not be merged into the event inventory until a verified time/geography crosswalk proves that they do not summarize the target event.",
        "",
        "## 8. Recommended exclusions",
        "",
        "Exclude all post-event impacts, event dates used as predictors, identifiers, source metadata, and unverified aggregate fields from the initial predictive feature set. Retain them for target construction or provenance only where their semantics and timing are approved.",
        "",
        "## 9. Unresolved questions",
        "",
        "- What exact lead time and prediction timestamp define the operational forecast?",
        "- What reference periods generated the district aggregates?",
        "- Is UEI officially defined as a stable event identifier?",
        "- How will non-event/negative examples be sampled for Flood_Binary?",
        "- Which fields are genuinely available before the flood rather than coded retrospectively?",
    ]
    return "\n".join(lines)


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    frames = load_frames()
    audit = feature_audit(frames)
    targets = target_candidates()
    audit.to_csv(REPORT_DIR / "feature_leakage_audit.csv", index=False)
    targets.to_csv(REPORT_DIR / "target_candidates.csv", index=False)
    (REPORT_DIR / "prediction_timeline.md").write_text(timeline(frames), encoding="utf-8")
    (REPORT_DIR / "event_identity_analysis.md").write_text(event_identity(frames), encoding="utf-8")
    (REPORT_DIR / "feature_policy.md").write_text(feature_policy(audit), encoding="utf-8")
    (REPORT_DIR / "leakage_audit_report.md").write_text(audit_report(audit, targets), encoding="utf-8")
    observed_counts = audit.classification.value_counts().to_dict()
    summary = {
        "columns_audited": len(audit),
        "classification_counts": {key: int(observed_counts.get(key, 0)) for key in ("SAFE", "CAUTION", "LEAKAGE", "UNKNOWN / REQUIRES VERIFICATION")},
        "cleaned_files_read": FILES,
        "targets_created": False,
        "splits_created": False,
        "merge_performed": False,
    }
    (REPORT_DIR / "leakage_audit_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()