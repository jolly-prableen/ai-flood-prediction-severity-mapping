"""Audit IFI-Impacts and prepare a leakage-aware district regression dataset.

This module never trains a model and never modifies files under data/raw/.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

EXPECTED = {
    "inventory": "India_Flood_Inventory_v3.csv",
    "impact": "District_FloodImpact.csv",
    "area": "District_FloodedArea.csv",
}
TARGET = "Corrected_Percent_Flooded_Area"
FEATURES = ["Population", "Parmanent_Water"]


def json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def normalize_name(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.casefold()


def column_audit(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    audit: dict[str, dict[str, Any]] = {}
    for column in frame.columns:
        series = frame[column]
        entry: dict[str, Any] = {
            "dtype": str(series.dtype),
            "unique_count": int(series.nunique(dropna=True)),
            "missing_count": int(series.isna().sum()),
            "missing_percent": round(float(series.isna().mean() * 100), 4),
        }
        if pd.api.types.is_numeric_dtype(series):
            clean = series.dropna()
            entry["min"] = json_value(clean.min()) if not clean.empty else None
            entry["max"] = json_value(clean.max()) if not clean.empty else None
            entry["mean"] = json_value(clean.mean()) if not clean.empty else None
            entry["quantiles"] = {
                str(level): json_value(clean.quantile(level)) for level in (0.01, 0.25, 0.5, 0.75, 0.99)
            }
        else:
            entry["top_categories"] = {
                str(key): int(value)
                for key, value in series.dropna().astype(str).value_counts().head(10).items()
            }
        audit[column] = entry
    return audit


def duplicate_key_report(frame: pd.DataFrame, key_column: str) -> dict[str, Any]:
    keys = normalize_name(frame[key_column])
    groups = keys.value_counts(dropna=True)
    duplicates = groups[groups > 1]
    return {
        "key_column": key_column,
        "unique_nonmissing_keys": int(keys.nunique(dropna=True)),
        "duplicate_key_count": int(len(duplicates)),
        "duplicate_rows": int(duplicates.sum()),
        "duplicate_keys": {str(key): int(value) for key, value in duplicates.items()},
    }


def join_report(inventory: pd.DataFrame, impact: pd.DataFrame, area: pd.DataFrame) -> dict[str, Any]:
    inventory_names = normalize_name(inventory["Districts"]).dropna()
    area_names = normalize_name(area["Dist_Name"])
    impact_names = normalize_name(impact["Dist_Name"])
    common_inventory_area = set(inventory_names) & set(area_names)
    common_area_impact = set(area_names) & set(impact_names)
    area_dupes = set(area_names[area_names.duplicated(keep=False)])
    impact_dupes = set(impact_names[impact_names.duplicated(keep=False)])
    ambiguous = sorted(area_dupes & impact_dupes)
    return {
        "inventory_to_district_files": {
            "candidate_key": "normalized Districts to Dist_Name",
            "lgd_join_available": False,
            "reason": "District files contain no District_LGD_Codes; inventory Districts may contain comma-separated multi-district values.",
            "overlapping_normalized_values": len(common_inventory_area),
            "matching_inventory_rows": int(inventory_names.isin(common_inventory_area).sum()),
            "unmatched_nonmissing_inventory_rows": int((~inventory_names.isin(common_inventory_area)).sum()),
            "status": "not used for training dataset",
        },
        "area_to_impact": {
            "candidate_key": "normalized Dist_Name",
            "area_unique_keys": int(area_names.nunique()),
            "impact_unique_keys": int(impact_names.nunique()),
            "overlapping_keys": len(common_area_impact),
            "ambiguous_keys_in_both": ambiguous,
            "ambiguous_key_count": len(ambiguous),
            "relationship": "one-to-one after excluding six duplicate-name keys; otherwise many-to-many for six keys",
            "usable_unambiguous_keys": len(common_area_impact) - len(ambiguous),
            "status": "used only for unambiguous one-to-one keys",
        },
    }


def parse_date_report(inventory: pd.DataFrame) -> dict[str, Any]:
    result = {}
    for column in ("Start Date", "End Date"):
        parsed = pd.to_datetime(inventory[column], format="%d-%m-%Y %H:%M", errors="coerce")
        result[column] = {
            "min": parsed.min().isoformat() if parsed.notna().any() else None,
            "max": parsed.max().isoformat() if parsed.notna().any() else None,
            "missing_or_invalid": int(parsed.isna().sum()),
            "invalid_nonmissing": int((inventory[column].notna() & parsed.isna()).sum()),
        }
    return result


def prepare_area_dataset(impact: pd.DataFrame, area: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    impact = impact.copy()
    area = area.copy()
    impact["district_key"] = normalize_name(impact["Dist_Name"])
    area["district_key"] = normalize_name(area["Dist_Name"])
    duplicate_keys = set(impact.loc[impact["district_key"].duplicated(False), "district_key"]) | set(
        area.loc[area["district_key"].duplicated(False), "district_key"]
    )
    impact = impact[~impact["district_key"].isin(duplicate_keys)]
    area = area[~area["district_key"].isin(duplicate_keys)]
    merged = area.merge(
        impact[["district_key", "Population"]],
        on="district_key",
        how="inner",
        validate="one_to_one",
    )
    prepared = merged[["district_key", "Dist_Name", "Population", "Parmanent_Water", TARGET]].copy()
    prepared = prepared.dropna(subset=FEATURES + [TARGET]).reset_index(drop=True)
    return prepared, sorted(duplicate_keys)


def create_split(frame: pd.DataFrame, seed: int = 42) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    indices = rng.permutation(len(frame))
    train_end = int(len(frame) * 0.70)
    validation_end = train_end + int(len(frame) * 0.15)
    split = {
        "strategy": "deterministic district-level random split; no temporal field exists in district aggregate files",
        "seed": seed,
        "train_indices": indices[:train_end].tolist(),
        "validation_indices": indices[train_end:validation_end].tolist(),
        "test_indices": indices[validation_end:].tolist(),
    }
    return split


def build_report(raw_dir: Path, processed_dir: Path, results_dir: Path) -> dict[str, Any]:
    inventory = pd.read_csv(raw_dir / EXPECTED["inventory"])
    impact = pd.read_csv(raw_dir / EXPECTED["impact"])
    area = pd.read_csv(raw_dir / EXPECTED["area"])
    prepared, excluded_duplicate_keys = prepare_area_dataset(impact, area)
    split = create_split(prepared)
    report = {
        "source": "India Flood Inventory-Impacts v3",
        "source_url": "https://zenodo.org/records/11275211",
        "raw_files": {name: str(raw_dir / filename) for name, filename in EXPECTED.items()},
        "raw_shapes": {
            "inventory": list(inventory.shape),
            "impact": list(impact.shape),
            "area": list(area.shape),
        },
        "column_audit": {
            "inventory": column_audit(inventory),
            "impact": column_audit(impact),
            "area": column_audit(area),
        },
        "date_ranges": parse_date_report(inventory),
        "duplicate_keys": {
            "inventory_districts": duplicate_key_report(inventory, "Districts"),
            "impact_districts": duplicate_key_report(impact, "Dist_Name"),
            "area_districts": duplicate_key_report(area, "Dist_Name"),
        },
        "join_quality": join_report(inventory, impact, area),
        "target_candidates": {
            "flood_occurrence": "not available: inventory contains flood events only and no non-flood records",
            "Severity": "not available: 100 percent missing in main inventory",
            "Area Affected": "not available: 100 percent missing in main inventory",
            TARGET: "available in district flooded-area file; prepared as a district regression target",
        },
        "leakage_policy": {
            "accepted_features": FEATURES,
            "rejected_features": {
                "Percent_Flooded_Area": "alternate/current extent measure and direct target leakage",
                "Human_fatality": "post-event outcome",
                "Human_injured": "post-event outcome",
                "Mean_Flood_Duration": "post-event aggregate outcome",
                "Human Displaced": "post-event outcome and heavily missing",
                "Animal Fatality": "post-event outcome and nonnumeric text values",
                "Extent of damage ": "post-event outcome text",
                "Severity": "entirely missing and outcome field",
                "Area Affected": "entirely missing and outcome field",
                "UEI": "identifier/metadata",
                "Dist_Name": "identifier/metadata, not a numeric predictor",
            },
        },
        "recommended_first_task": {
            "target": TARGET,
            "task_type": "district-level regression",
            "features": FEATURES,
            "input_shape_for_tabular_models": "(batch, sequence_length=1, features=2)",
            "spatial_models": "pending: no raster tensors or genuine pixel-level masks",
            "processed_rows": int(len(prepared)),
            "excluded_ambiguous_duplicate_keys": excluded_duplicate_keys,
        },
        "preprocessing_plan": {
            "raw_unchanged": True,
            "numeric_missing_values": "rows missing Population, Parmanent_Water, or target are excluded; no values are fabricated",
            "categorical_encoding": "none required for the two-feature first task",
            "scaling": "fit StandardScaler on training rows only during training; not fitted during this preparation step",
            "feature_order": FEATURES,
            "class_balancing": "not applicable to regression; SMOTE not applied",
        },
        "split": split,
        "model_compatibility": {
            "CNN + LSTM": "SUPPORTED with district regression adaptation; current class head is classification-only and needs regression-head compatibility before training",
            "CNN + Transformer": "POSSIBLE WITH TRANSFORMATION; requires a regression head and sequence length one",
            "ResNet + BiLSTM": "POSSIBLE WITH TRANSFORMATION; requires a regression head and sequence length one",
            "U-Net + ConvLSTM": "REQUIRES ADDITIONAL DATA: spatial/raster sequences and masks",
            "Attention U-Net + LSTM": "REQUIRES ADDITIONAL DATA: spatial/raster sequences and masks",
        },
        "limitations": [
            "No rainfall, DEM, elevation, LULC, river-distance, satellite, or pixel-mask data is present.",
            "The inventory has no non-flood examples, so occurrence classification is not currently valid.",
            "The district files have no LGD codes; inventory-to-district name matching is not used for the prepared task.",
        ],
    }
    processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(processed_dir / "district_flood_area_regression.csv", index=False)
    (processed_dir / "district_flood_area_schema.json").write_text(json.dumps({
        "task": "district-level regression",
        "target": TARGET,
        "features": FEATURES,
        "input_shape": ["batch", 1, len(FEATURES)],
        "source_files": list(EXPECTED.values()),
        "excluded_ambiguous_duplicate_keys": excluded_duplicate_keys,
    }, indent=2), encoding="utf-8")
    (processed_dir.parent / "splits" / "district_flood_area_split.json").parent.mkdir(parents=True, exist_ok=True)
    (processed_dir.parent / "splits" / "district_flood_area_split.json").write_text(json.dumps(split, indent=2), encoding="utf-8")
    (results_dir / "data_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    args = parser.parse_args()
    report = build_report(args.raw_dir, args.processed_dir, args.results_dir)
    print(json.dumps({
        "prepared_dataset": "data/processed/district_flood_area_regression.csv",
        "rows": report["recommended_first_task"]["processed_rows"],
        "target": report["recommended_first_task"]["target"],
        "features": report["recommended_first_task"]["features"],
        "training_performed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
