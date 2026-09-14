"""Investigate IFI date contradictions without modifying any source or processed data."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "India_Flood_Inventory_v3.csv"
PROCESSED = ROOT / "data" / "processed" / "ifi_event_clean.csv"
QUALITY = ROOT / "results" / "data_quality"
RESEARCH = ROOT / "research"


def parse(series: pd.Series, dayfirst: bool) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", format="mixed", dayfirst=dayfirst)


def fmt(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def main() -> None:
    raw = pd.read_csv(RAW, dtype=str)
    clean = pd.read_csv(PROCESSED)
    raw_by_uei = raw.set_index("UEI")

    # Reproduce the 290-row diagnostic that reparsed processed ISO strings day-first.
    processed_dayfirst_start = parse(clean["start_date"], True)
    processed_dayfirst_end = parse(clean["end_date"], True)
    reported_bad = processed_dayfirst_start.notna() & processed_dayfirst_end.notna() & (processed_dayfirst_end < processed_dayfirst_start)

    raw_start = parse(raw["Start Date"], True)
    raw_end = parse(raw["End Date"], True)
    raw_bad = raw_start.notna() & raw_end.notna() & (raw_end < raw_start)
    raw_bad_by_uei = set(raw.loc[raw_bad, "UEI"])

    clean_iso_start = parse(clean["start_date"], False)
    clean_iso_end = parse(clean["end_date"], False)
    raw_start_by_uei = pd.Series(raw_start.to_numpy(), index=raw["UEI"])
    raw_end_by_uei = pd.Series(raw_end.to_numpy(), index=raw["UEI"])
    raw_duration_by_uei = pd.Series(pd.to_numeric(raw["Duration(Days)"], errors="coerce").to_numpy(), index=raw["UEI"])

    rows = []
    for index in clean.index[reported_bad]:
        uei = clean.at[index, "uei"]
        source_start = raw_start_by_uei.get(uei, pd.NaT)
        source_end = raw_end_by_uei.get(uei, pd.NaT)
        proper_start = clean_iso_start[index]
        proper_end = clean_iso_end[index]
        if uei in raw_bad_by_uei:
            classification = "SOURCE_INCONSISTENCY"
            action = "EXCLUDE_FROM_INTERVAL_TARGETING"
            confidence = "HIGH"
            evidence = "The raw DD-MM-YYYY source fields are themselves end-before-start; the contradiction is not introduced by cleaning."
            notes = "Do not swap dates or trust duration without authoritative source correction."
        else:
            classification = "CORRECTABLE_WITH_EVIDENCE"
            action = "SAFE_TO_USE_AFTER_DOCUMENTED_CORRECTION"
            confidence = "HIGH"
            evidence = "The processed CSV stores ISO dates, but the diagnostic used day-first parsing. Re-parsing processed ISO values with ISO/year-first semantics resolves the contradiction, and the raw DD-MM-YYYY fields are chronologically ordered."
            notes = "No dataset correction performed; this is a parsing-rule finding."
        rows.append({
            "uei": uei,
            "district": fmt(clean.at[index, "districts"]),
            "state": fmt(clean.at[index, "state"]),
            "start_date": fmt(clean.at[index, "start_date"]),
            "end_date": fmt(clean.at[index, "end_date"]),
            "duration_days": fmt(clean.at[index, "duration_days"]),
            "raw_start_date": fmt(raw_by_uei.at[uei, "Start Date"]),
            "raw_end_date": fmt(raw_by_uei.at[uei, "End Date"]),
            "raw_duration_days": fmt(raw_by_uei.at[uei, "Duration(Days)"]),
            "classification": classification,
            "evidence": evidence,
            "recommended_action": action,
            "confidence": confidence,
            "notes": notes + f" Proper ISO parse: start={proper_start.date() if pd.notna(proper_start) else ''}, end={proper_end.date() if pd.notna(proper_end) else ''}; raw DD-first parse: start={source_start.date() if pd.notna(source_start) else ''}, end={source_end.date() if pd.notna(source_end) else ''}.",
        })

    contradictions = pd.DataFrame(rows)
    QUALITY.mkdir(parents=True, exist_ok=True)
    contradictions.to_csv(QUALITY / "phase11b_date_contradictions.csv", index=False)

    proper_valid = clean_iso_start.notna() & clean_iso_end.notna() & (clean_iso_end >= clean_iso_start)
    duration = pd.to_numeric(raw["Duration(Days)"], errors="coerce")
    date_diff = (raw_end - raw_start).dt.days
    duration_consistent_inclusive = proper_valid.to_numpy() & duration.notna().to_numpy() & (duration.to_numpy() == (date_diff + 1).to_numpy())
    duration_inconsistent = proper_valid.to_numpy() & duration.notna().to_numpy() & ~duration_consistent_inclusive
    raw_contradiction_count = int(raw_bad.sum())
    reported_count = int(reported_bad.sum())
    correctable = int((contradictions["classification"] == "CORRECTABLE_WITH_EVIDENCE").sum())
    source_inconsistency = int((contradictions["classification"] == "SOURCE_INCONSISTENCY").sum())
    report = [
        "# Phase 11B Event Date Contradiction Review",
        "",
        "## A. Purpose",
        "",
        "This investigation diagnoses date-order contradictions without modifying raw or processed data. No dates were corrected, rows dropped, observation frames created, or targets generated.",
        "",
        "## B. Data inspected",
        "",
        "- `data/processed/ifi_event_clean.csv`",
        "- `data/raw/India_Flood_Inventory_v3.csv`",
        "- `src/preprocessing/clean_ifi.py`",
        "- Phase 3 cleaning log and validation report",
        "",
        "## C. Contradiction counts",
        "",
        f"- Reported contradictions under the prior diagnostic: **{reported_count}** rows.",
        f"- Genuine raw-source contradictions under the documented raw DD-MM-YYYY parse: **{raw_contradiction_count}** rows.",
        f"- Raw contradictions among the reported 290: **{source_inconsistency}** rows.",
        f"- Additional raw contradictions not included in the prior 290-row diagnostic: **{raw_contradiction_count - source_inconsistency}** rows.",
        "",
        "## D. Investigation methodology",
        "",
        "The raw source uses strings such as `08-06-1969 00:00`; the Phase 3 cleaner parses these day-first and writes ISO-formatted dates to the processed CSV. The prior 290 count was reproduced by reparsing those processed ISO strings with `dayfirst=True`, which is inappropriate for ISO `YYYY-MM-DD` strings. Diagnostics compared raw DD-MM parsing, processed ISO/year-first parsing, and the raw values joined by unique `UEI`.",
        "",
        "## E. Evidence from raw/source data",
        "",
        f"- All 290 reported rows were joined to raw records by `UEI`; no raw match was missing.",
        f"- Proper ISO parsing resolves **{correctable}** of the reported rows.",
        f"- **{source_inconsistency}** reported rows remain contradictory in the raw source and are classified `SOURCE_INCONSISTENCY`.",
        f"- The raw source contains **{raw_contradiction_count}** total end-before-start rows; the raw contradictions are not a cleaning transformation artifact.",
        "",
        "## F. Date-parsing analysis",
        "",
        "- Raw date strings are day-first `DD-MM-YYYY HH:MM`.",
        "- Processed date strings are ISO `YYYY-MM-DD` after Phase 3 serialization.",
        "- Applying `dayfirst=True` to processed ISO strings creates the reported 290-row diagnostic artifact.",
        "- Applying year-first/ISO parsing to processed strings reduces the contradiction count to the 17 raw-source contradictions.",
        "- Month-first parsing is not supported by the raw format and is not a valid automatic correction rule.",
        "",
        "## G. Duration consistency",
        "",
        f"- Under proper raw DD-first parsing, **{int(proper_valid.sum())}** rows have noncontradictory complete start/end dates.",
        f"- The apparent convention is inclusive duration `(end - start) + 1` days; **{int(duration_inclusive_consistent := duration_consistent_inclusive.sum())}** rows match it.",
        f"- **{int(duration_inconsistent.sum())}** noncontradictory rows with nonmissing durations do not match the inclusive convention.",
        "- Duration is therefore not a reliable automatic repair field. It must not be used to swap or reconstruct dates without record-level evidence.",
        "",
        "## H. Classification counts for the reported 290",
        "",
        f"- `CORRECTABLE_WITH_EVIDENCE`: **{correctable}**",
        "- `AMBIGUOUS_REQUIRES_REVIEW`: **0**",
        f"- `SOURCE_INCONSISTENCY`: **{source_inconsistency}**",
        "- `UNRESOLVED`: **0**",
        "",
        "## I. Recommended treatment",
        "",
        "- The 288 parsing-artifact rows are safe for future interval targeting only after the documented parser distinction is enforced in implementation; no file was changed here.",
        "- The 2 raw-source contradictions in the reported set must be excluded from automatic interval targeting or manually resolved from authoritative source evidence.",
        f"- The other {raw_contradiction_count - source_inconsistency} raw-source contradictions outside the prior 290 must also be excluded from interval targeting until reviewed.",
        "- Never sort dates, take absolute duration, replace an endpoint using duration, or assume a one-day event automatically.",
        "",
        "## J. Implications for district-week / 7-day targeting",
        "",
        "Use raw DD-first parsing for raw source inspection and ISO/year-first parsing for the serialized processed dates. Only verified chronological intervals may be tested against the district-week forecast window. Parsing artifacts must be resolved by documented parser behavior; source contradictions remain unknown/excluded. A positive or negative target must not be generated for unresolved intervals.",
        "",
        "## K. Remaining unresolved records",
        "",
        f"- **{raw_contradiction_count}** raw-source contradictions require authoritative review if they are to be used for interval targeting.",
        f"- **{int(duration_inconsistent.sum())}** otherwise chronological records have duration values inconsistent with the apparent inclusive convention; they require separate duration review but are not automatically date contradictions.",
        "",
        "## L. Immutability statement",
        "",
        "No raw CSV, processed CSV, final crosswalk, model, target column, or observation frame was modified or created. The row-level CSV is diagnostic output only.",
    ]
    (RESEARCH / "phase11b_date_contradiction_review.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"reported_290": reported_count, "correctable": correctable, "source_inconsistency": source_inconsistency, "unresolved": 0, "raw_total": raw_contradiction_count, "duration_inconsistencies": int(duration_inconsistent.sum()), "safe_after_documented_parser": correctable, "exclude_interval_targeting": raw_contradiction_count}, indent=2))


if __name__ == "__main__":
    main()