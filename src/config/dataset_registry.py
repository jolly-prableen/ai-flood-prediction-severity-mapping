"""Centralized Dataset Registry.

Defines all known datasets, their schemas, feature and target contracts,
GIS capabilities, and evaluation/prediction artifact paths.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class DatasetRecord:
    """Explicit metadata and contracts for a registered dataset."""

    dataset_id: str
    display_name: str
    source_path: Path
    dataset_type: str
    feature_columns: list[str]
    target_column: str | None
    target_type: str | None
    district_column: str | None
    has_gis: bool
    latitude_column: str | None = None
    longitude_column: str | None = None
    prediction_artifact: Path | None = None
    evaluation_artifact: Path | None = None
    ablation_artifact: Path | None = None
    description: str = ""
    is_baseline: bool = False
    related_sources: dict[str, Path] = field(default_factory=dict)

    @property
    def exists(self) -> bool:
        return self.source_path.exists()

    @property
    def is_image_dataset(self) -> bool:
        return self.dataset_type.startswith("image")

    @property
    def relative_source(self) -> str:
        try:
            return self.source_path.relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            return str(self.source_path)


# 1. India Flood Inventory v3 (IFI / M2 Baseline)
DATASET_IFI_V3 = DatasetRecord(
    dataset_id="ifi_v3",
    display_name="India Flood Inventory v3 (IFI / M2 Baseline)",
    source_path=PROJECT_ROOT / "data" / "processed" / "district_flood_area_regression.csv",
    dataset_type="tabular (regression)",
    feature_columns=["Population", "Parmanent_Water"],
    target_column="Corrected_Percent_Flooded_Area",
    target_type="continuous",
    district_column="Dist_Name",
    has_gis=True,
    prediction_artifact=PROJECT_ROOT / "results" / "evaluation" / "actual_vs_predicted.csv",
    evaluation_artifact=PROJECT_ROOT / "results" / "evaluation" / "error_summary.csv",
    ablation_artifact=PROJECT_ROOT / "results" / "models" / "ablation" / "ablation_summary.json",
    description=(
        "Member 2 baseline regression dataset: 720 district rows with Population and "
        "Parmanent_Water predicting Corrected_Percent_Flooded_Area."
    ),
    is_baseline=True,
    related_sources={
        "Original IFI inventory (raw)": PROJECT_ROOT / "data" / "raw" / "India_Flood_Inventory_v3.csv",
    },
)

# 2. District Flood Impact (IFI district aggregates)
DATASET_IFI_IMPACT = DatasetRecord(
    dataset_id="ifi_impact",
    display_name="District Flood Impact (IFI district aggregates)",
    source_path=PROJECT_ROOT / "data" / "raw" / "District_FloodImpact.csv",
    dataset_type="tabular (descriptive)",
    feature_columns=[],
    target_column=None,
    target_type=None,
    district_column="Dist_Name",
    has_gis=True,
    prediction_artifact=None,
    evaluation_artifact=None,
    ablation_artifact=None,
    description=(
        "Descriptive district-level impact aggregates (732 districts): Population, Human_fatality, "
        "Human_injured, and Mean_Flood_Duration. No prediction target is defined."
    ),
    is_baseline=False,
)

# 3. District Flooded Area (IFI district aggregates)
DATASET_IFI_FLOODED_AREA = DatasetRecord(
    dataset_id="ifi_flooded_area",
    display_name="District Flooded Area (IFI district aggregates)",
    source_path=PROJECT_ROOT / "data" / "raw" / "District_FloodedArea.csv",
    dataset_type="tabular (regression data)",
    feature_columns=["Parmanent_Water"],
    target_column="Corrected_Percent_Flooded_Area",
    target_type="continuous",
    district_column="Dist_Name",
    has_gis=True,
    prediction_artifact=None,
    evaluation_artifact=None,
    ablation_artifact=None,
    description=(
        "Raw district flooded-area aggregates (732 districts): Percent_Flooded_Area, Parmanent_Water, "
        "and Corrected_Percent_Flooded_Area. Reference source of the M2 baseline target."
    ),
    is_baseline=False,
)

# 4. mwBTFreddy Sample Subset1
DATASET_MWBTFREDDY = DatasetRecord(
    dataset_id="mwbtfreddy",
    display_name="mwBTFreddy Sample Subset1",
    source_path=PROJECT_ROOT / "data" / "raw" / "custom_flood_datasets" / "mwBTFreddy",
    dataset_type="image pair (raster + annotations)",
    feature_columns=[],
    target_column=None,
    target_type="categorical (building damage)",
    district_column=None,
    has_gis=True,
    prediction_artifact=None,
    evaluation_artifact=None,
    ablation_artifact=None,
    description=(
        "Sample Subset1 of Cyclone Freddy satellite image pairs (10 pairs, 1274 building annotations). "
        "Target task is building damage classification on satellite imagery."
    ),
    is_baseline=False,
)

DATASET_REGISTRY: dict[str, DatasetRecord] = {
    "ifi_v3": DATASET_IFI_V3,
    "ifi_impact": DATASET_IFI_IMPACT,
    "ifi_flooded_area": DATASET_IFI_FLOODED_AREA,
    "mwbtfreddy": DATASET_MWBTFREDDY,
}

DATASET_BY_DISPLAY_NAME: dict[str, DatasetRecord] = {
    rec.display_name: rec for rec in DATASET_REGISTRY.values()
}


def get_dataset(key_or_name: str) -> DatasetRecord:
    """Retrieve dataset by ID or display name."""
    if key_or_name in DATASET_REGISTRY:
        return DATASET_REGISTRY[key_or_name]
    if key_or_name in DATASET_BY_DISPLAY_NAME:
        return DATASET_BY_DISPLAY_NAME[key_or_name]
    raise KeyError(f"Unknown dataset key or display name: {key_or_name}")


def list_datasets() -> list[DatasetRecord]:
    """Return all registered datasets whose source exists on disk."""
    return [rec for rec in DATASET_REGISTRY.values() if rec.exists]


def load_dataset_data(dataset_id: str) -> pd.DataFrame | None:
    """Load the tabular DataFrame for a dataset if it exists."""
    rec = get_dataset(dataset_id)
    if rec.is_image_dataset or not rec.exists:
        return None
    return pd.read_csv(rec.source_path)


get_dataset_by_name = get_dataset
