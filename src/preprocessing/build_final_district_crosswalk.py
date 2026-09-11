"""Build the final working IFI/LGD/Census crosswalk from the reviewed comparison."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "results" / "data_quality" / "ifi_lgd_census_comparison.csv"
OUTPUT = ROOT / "data" / "derived" / "district_crosswalk_final.csv"
VALIDATION = ROOT / "results" / "data_quality" / "final_district_crosswalk_validation.md"


def main() -> None:
    comparison = pd.read_csv(INPUT).fillna("")
    ifi = comparison[comparison["ifi_district_name"] != ""].copy()
    ifi["state_consistent"] = ifi.apply(
        lambda row: bool(row["lgd_state_name"])
        and row["lgd_state_name"] in [value.strip() for value in row["ifi_state_context"].split(";") if value.strip()],
        axis=1,
    )
    ifi["has_boundary"] = ifi["census_boundary_district_name"] != ""
    ifi["ambiguous_name"] = ifi.groupby("ifi_district_name")["ifi_district_name"].transform("size") > 1

    def classify(row: pd.Series) -> tuple[str, str, str, str]:
        if row["match_method"] == "none":
            return "UNMATCHED", "UNMATCHED", "none", "No defensible LGD/Census candidate in the reviewed comparison."
        if row["ambiguous_name"]:
            return "AMBIGUOUS_REVIEW", "REQUIRES_MANUAL_VERIFICATION", "multiple_lgd_candidates", "The IFI district name has multiple plausible LGD candidates; preserve all candidates."
        if row["match_method"] == "normalized_district_name":
            return "NORMALIZED_REVIEW", "REQUIRES_MANUAL_VERIFICATION", "normalized_district_name", "Normalization was required; no silent rename or fuzzy match was applied."
        if row["state_consistent"] and row["has_boundary"]:
            return "VERIFIED_NAME_STATE", "NAME_STATE_CANDIDATE_WITH_HISTORICAL_LIMITATION", "exact_name_state_boundary_candidate", "Exact LGD name, observed state context, and Census boundary candidate agree; code equivalence is not assumed."
        return "HISTORICAL_REVIEW", "REQUIRES_MANUAL_VERIFICATION", "exact_name_without_complete_state_boundary_confirmation", "Identity is plausible by exact LGD name but state or Census-boundary evidence is incomplete or contradictory."

    classified = ifi.apply(classify, axis=1, result_type="expand")
    classified.columns = ["match_class", "verification_status", "mapping_method", "classification_note"]
    ifi = ifi.drop(columns=["verification_status"])
    ifi = pd.concat([ifi, classified], axis=1)
    ifi["historical_boundary_status"] = "HISTORICAL_REVIEW_REQUIRED"
    ifi["mapping_confidence"] = ifi["match_class"].map({
        "VERIFIED_NAME_STATE": "HIGH_FOR_CURRENT_NAME_STATE_LINK; HISTORICAL_LIMITATION",
        "NORMALIZED_REVIEW": "MEDIUM_REQUIRES_MANUAL_VERIFICATION",
        "AMBIGUOUS_REVIEW": "LOW_REQUIRES_MANUAL_VERIFICATION",
        "HISTORICAL_REVIEW": "LOW_REQUIRES_HISTORICAL_REVIEW",
        "UNMATCHED": "NONE",
    })
    ifi["notes"] = ifi.apply(lambda row: f"{row['classification_note']} Existing comparison note: {row['notes_reason']}", axis=1)
    output = ifi.rename(columns={
        "census_boundary_district_name": "census_boundary_district",
        "classification_note": "_classification_note",
    })
    columns = [
        "ifi_district_name", "ifi_state_context", "lgd_state_code", "lgd_state_name", "lgd_district_code", "lgd_district_name",
        "census_2001_code", "census_2011_code", "census_boundary_district", "census_boundary_state", "censuscode",
        "match_class", "verification_status", "historical_boundary_status", "mapping_method", "mapping_confidence", "notes",
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    output[columns].to_csv(OUTPUT, index=False)
    final = pd.read_csv(OUTPUT).fillna("")
    census_duplicates = final[final.censuscode != ""].groupby("censuscode").ifi_district_name.nunique()
    lgd_duplicates = final[final.lgd_district_code != ""].groupby("lgd_district_code").ifi_district_name.nunique()
    repeated_ifis = final.groupby("ifi_district_name").size()
    report = [
        "# Final District Crosswalk Validation",
        "",
        "This is a working integration crosswalk for later analysis, not a claim that Census 2011 boundaries represent every historical IFI district. The source comparison was used as the primary evidence. No raw IFI, processed IFI, LGD, or Census boundary file was modified.",
        "",
        "## Counts",
        "",
        f"- Total unique IFI district tokens represented: **{final['ifi_district_name'].nunique():,}**",
        f"- Final crosswalk rows: **{len(final):,}**; extra rows preserve ambiguous candidates.",
        f"- Total rows mapped to a Census boundary: **{int((final.census_boundary_district != '').sum()):,}**",
        f"- `VERIFIED_NAME_STATE`: **{int((final.match_class == 'VERIFIED_NAME_STATE').sum()):,} rows**",
        f"- `NORMALIZED_REVIEW`: **{int((final.match_class == 'NORMALIZED_REVIEW').sum()):,} rows**",
        f"- `AMBIGUOUS_REVIEW`: **{int((final.match_class == 'AMBIGUOUS_REVIEW').sum()):,} rows / {final.loc[final.match_class == 'AMBIGUOUS_REVIEW', 'ifi_district_name'].nunique():,} IFI names**",
        f"- `HISTORICAL_REVIEW`: **{int((final.match_class == 'HISTORICAL_REVIEW').sum()):,} rows**",
        f"- `UNMATCHED`: **{int((final.match_class == 'UNMATCHED').sum()):,} rows**",
        f"- Historical limitation status: **{final['historical_boundary_status'].value_counts().to_dict()}**",
        "",
        "## Duplicate assignments and relationships",
        "",
        f"- Duplicate Census boundary assignments to multiple IFI names: **{int((census_duplicates > 1).sum())} censuscode values**.",
        f"- Duplicate LGD district assignments to multiple IFI names: **{int((lgd_duplicates > 1).sum())} LGD district codes**.",
        f"- IFI names with multiple final rows (one-to-many candidate relationships): **{int((repeated_ifis > 1).sum())} names**.",
        f"- Census boundary names assigned to multiple final rows: **{int(final[final.census_boundary_district != ''].groupby('census_boundary_district').size().gt(1).sum())} names**.",
        "- These repeated relationships are preserved for review and are not merged or deduplicated.",
        "",
        "## Missing identifiers",
        "",
        f"- Missing LGD district codes: **{int((final.lgd_district_code == '').sum())} rows**.",
        f"- Missing Census `censuscode`: **{int((final.censuscode == '').sum())} rows**.",
        f"- Missing Census 2011 boundary district: **{int((final.census_boundary_district == '').sum())} rows**.",
        "",
        "## Unresolved issues",
        "",
        "- LGD `District Code` is retained as the official LGD field; it is not equated with Census `censuscode` or `DT_CEN_CD`.",
        "- All rows retain `HISTORICAL_REVIEW_REQUIRED` because IFI spans 1967–2023 while the acquired Census boundary layer is a 2011 reference.",
        "- Multi-value IFI state context can be noisy and does not prove a unique state assignment for every district token.",
        "- Normalized, ambiguous, historical, and unmatched rows require review before they are used as an authoritative aggregation key.",
        "- No rainfall aggregation or feature construction was performed.",
    ]
    VALIDATION.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(final.match_class.value_counts().to_dict())


if __name__ == "__main__":
    main()