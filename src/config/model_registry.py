"""Centralized Model Registry.

Tracks all five project architectures across every registered dataset,
specifying exact checkpoint paths, preprocessing artifacts, feature/target
contracts, evaluation metrics, and verified operational statuses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Standard Status Vocabulary (Per Project Specification)
STATUS_TRAINED_EVALUATED = "TRAINED + EVALUATED"
STATUS_TRAINED_NOT_EVALUATED = "TRAINED BUT NOT EVALUATED"
STATUS_TRAINED_FOR_DIFFERENT_DATASET = "TRAINED FOR DIFFERENT DATASET"
STATUS_NOT_TRAINED = "NOT TRAINED"
STATUS_TRAINING_REQUIRED = "IMPLEMENTED / TRAINING REQUIRED"
STATUS_INCOMPATIBLE = "INCOMPATIBLE WITH CURRENT DATA"

ALL_MODELS = [
    "CNN + LSTM",
    "CNN + Transformer",
    "ResNet + BiLSTM",
    "U-Net + ConvLSTM",
    "Attention U-Net + LSTM",
]

TABULAR_MODELS = {"CNN + LSTM", "CNN + Transformer", "ResNet + BiLSTM"}
SPATIAL_MODELS = {"U-Net + ConvLSTM", "Attention U-Net + LSTM"}


@dataclass(frozen=True)
class ModelRecord:
    """Artifact and compatibility record for a specific model × dataset combination."""

    model_name: str
    dataset_id: str
    status: str
    architecture: str
    input_type: str
    target_task: str
    feature_contract: list[str]
    target_name: str | None
    checkpoint_path: Path | None
    preprocessing_path: Path | None
    predictions_path: Path | None
    metrics: dict[str, float] | None
    inference_available: bool
    status_reason: str
    expected_output: str = ""
    compatible_datasets: list[str] = field(default_factory=list)

    @property
    def has_checkpoint(self) -> bool:
        return self.checkpoint_path is not None and self.checkpoint_path.is_file()

    @property
    def has_predictions(self) -> bool:
        return self.predictions_path is not None and self.predictions_path.is_file()


# Saved baseline evaluation metrics for ifi_v3
IFI_BASELINE_METRICS = {
    "ResNet + BiLSTM": {"MAE": 2.2964, "RMSE": 3.3599, "R2": 0.0834},
    "CNN + Transformer": {"MAE": 2.4273, "RMSE": 3.4543, "R2": 0.0312},
    "CNN + LSTM": {"MAE": 2.4338, "RMSE": 3.3763, "R2": 0.0745},
}


def get_model_record(dataset_id: str, model_name: str) -> ModelRecord:
    """Return the authoritative model record for a dataset × model pair."""
    if model_name not in ALL_MODELS:
        raise KeyError(f"Unknown model name: {model_name}")

    # 1. India Flood Inventory v3 (M2 Baseline)
    if dataset_id == "ifi_v3":
        if model_name in TABULAR_MODELS:
            dir_map = {
                "CNN + LSTM": "cnn_lstm",
                "CNN + Transformer": "cnn_transformer",
                "ResNet + BiLSTM": "resnet_bilstm",
            }
            dname = dir_map[model_name]
            ckpt = PROJECT_ROOT / "results" / "models" / dname / "best_model.pt"
            prep = PROJECT_ROOT / "results" / "models" / "preprocessing.pkl"
            preds = PROJECT_ROOT / "results" / "evaluation" / "actual_vs_predicted.csv"
            metrics = IFI_BASELINE_METRICS.get(model_name)
            return ModelRecord(
                model_name=model_name,
                dataset_id=dataset_id,
                status=STATUS_TRAINED_EVALUATED,
                architecture=f"{model_name} tabular regression architecture",
                input_type="tabular feature sequence (batch, time, features)",
                target_task="district flooded-area regression",
                feature_contract=["Population", "Parmanent_Water"],
                target_name="Corrected_Percent_Flooded_Area",
                checkpoint_path=ckpt,
                preprocessing_path=prep,
                predictions_path=preds,
                metrics=metrics,
                inference_available=True,
                status_reason=(
                    f"Saved baseline checkpoint and evaluations exist under results/models/{dname}/ "
                    "evaluated on the 109 untouched test districts."
                ),
                expected_output="Continuous flooded area regression percentage (%)",
                compatible_datasets=["India Flood Inventory v3 (IFI / M2 Baseline)"],
            )
        else:
            return ModelRecord(
                model_name=model_name,
                dataset_id=dataset_id,
                status=STATUS_INCOMPATIBLE,
                architecture=f"{model_name} spatial raster architecture",
                input_type="spatial raster sequence (batch, time, channels, height, width)",
                target_task="spatial prediction / building damage classification",
                feature_contract=[],
                target_name=None,
                checkpoint_path=None,
                preprocessing_path=None,
                predictions_path=None,
                metrics=None,
                inference_available=False,
                status_reason=(
                    f"{model_name} requires 5D spatial raster sequences (imagery); "
                    "incompatible with 1D tabular district features (spatial input data unavailable)."
                ),
                expected_output="Spatial raster prediction / segmentation mask",
                compatible_datasets=["mwBTFreddy Sample Subset1 (requires training)"],
            )

    # 2. District Flood Impact (descriptive)
    elif dataset_id == "ifi_impact":
        return ModelRecord(
            model_name=model_name,
            dataset_id=dataset_id,
            status=STATUS_INCOMPATIBLE,
            architecture=model_name,
            input_type="tabular feature sequence" if model_name in TABULAR_MODELS else "spatial raster",
            target_task="descriptive district aggregates (no predictive target)",
            feature_contract=[],
            target_name=None,
            checkpoint_path=None,
            preprocessing_path=None,
            predictions_path=None,
            metrics=None,
            inference_available=False,
            status_reason=(
                "District Flood Impact holds descriptive post-event impact quantities (fatalities, injuries, "
                "duration) and has no predictive regression target."
            ),
            expected_output="Descriptive statistics only (no prediction target)",
            compatible_datasets=[],
        )

    # 3. District Flooded Area (raw unmerged table)
    elif dataset_id == "ifi_flooded_area":
        return ModelRecord(
            model_name=model_name,
            dataset_id=dataset_id,
            status=STATUS_INCOMPATIBLE,
            architecture=model_name,
            input_type="tabular feature sequence" if model_name in TABULAR_MODELS else "spatial raster",
            target_task="district flooded-area regression (data only)",
            feature_contract=["Parmanent_Water"],
            target_name="Corrected_Percent_Flooded_Area",
            checkpoint_path=None,
            preprocessing_path=None,
            predictions_path=None,
            metrics=None,
            inference_available=False,
            status_reason=(
                "Raw flooded-area table lacking demographic features (Population) and train/test split. "
                "Corrected_Percent_Flooded_Area has an exact mathematical identity relation with "
                "Percent_Flooded_Area (target leakage). Trained models operate on the prepared 720-row baseline."
            ),
            expected_output="Continuous flooded area percentage (%)",
            compatible_datasets=["India Flood Inventory v3 (IFI / M2 Baseline)"],
        )

    # 4. mwBTFreddy Sample Subset1 (imagery)
    elif dataset_id == "mwbtfreddy":
        if model_name in SPATIAL_MODELS:
            return ModelRecord(
                model_name=model_name,
                dataset_id=dataset_id,
                status=STATUS_TRAINING_REQUIRED,
                architecture=f"{model_name} spatial raster architecture",
                input_type="spatial raster sequence (batch, time, channels, height, width)",
                target_task="building damage classification (imagery)",
                feature_contract=[],
                target_name="building_damage_label",
                checkpoint_path=None,
                preprocessing_path=None,
                predictions_path=None,
                metrics=None,
                inference_available=False,
                status_reason=(
                    f"{model_name} is architecturally compatible with image pairs; "
                    "training required on full image dataset."
                ),
                expected_output="Spatial building damage segmentation mask (pixel classes)",
                compatible_datasets=["mwBTFreddy Sample Subset1"],
            )
        else:
            return ModelRecord(
                model_name=model_name,
                dataset_id=dataset_id,
                status=STATUS_INCOMPATIBLE,
                architecture=f"{model_name} tabular architecture",
                input_type="tabular feature sequence",
                target_task="building damage classification (imagery)",
                feature_contract=[],
                target_name="building_damage_label",
                checkpoint_path=None,
                preprocessing_path=None,
                predictions_path=None,
                metrics=None,
                inference_available=False,
                status_reason=(
                    "INCOMPATIBLE — this model currently expects the IFI tabular input contract."
                ),
                expected_output="Tabular regression / classification",
                compatible_datasets=["India Flood Inventory v3 (IFI / M2 Baseline)"],
            )


    raise KeyError(f"Unknown dataset_id: {dataset_id}")


def get_dataset_model_table(dataset_id: str) -> list[ModelRecord]:
    """Return all five model records for the given dataset."""
    return [get_model_record(dataset_id, name) for name in ALL_MODELS]


get_model_artifact_record = get_model_record
