"""Thin dashboard adapter over the real Member 2 inference pipeline."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.inference.dataset_adapter import adapt_uploaded_dataset
from src.inference.predictor import predict_uploaded_dataset as member2_predict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = PROJECT_ROOT / "results" / "models"
BASELINE_REQUIRED_FEATURES = ["Population", "Parmanent_Water"]
TARGET_COL = "Corrected_Percent_Flooded_Area"
TRAINED_MODELS = {
    "CNN + LSTM": MODEL_ROOT / "cnn_lstm" / "best_model.pt",
    "CNN + Transformer": MODEL_ROOT / "cnn_transformer" / "best_model.pt",
    "ResNet + BiLSTM": MODEL_ROOT / "resnet_bilstm" / "best_model.pt",
}
PLANNED_MODELS = {
    "U-Net + ConvLSTM": "Not trained - spatial/raster sequence data required",
    "Attention U-Net + LSTM": "Not trained - spatial/raster sequence data required",
}


def get_supported_tasks() -> list[str]:
    return ["District flooded-area regression"]


def get_available_models() -> list[str]:
    return [name for name, path in TRAINED_MODELS.items() if path.is_file()]


def get_model_status() -> dict[str, str]:
    status = {name: "trained" if name in get_available_models() else "unavailable"
              for name in TRAINED_MODELS}
    status.update({name: "unavailable" for name in PLANNED_MODELS})
    return status


def get_model_metrics() -> pd.DataFrame:
    path = PROJECT_ROOT / "results" / "model_comparison.csv"
    if not path.is_file():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    return frame[frame["Model"].isin(TRAINED_MODELS)].copy()


def inspect_dataset(frame: pd.DataFrame) -> dict:
    return {
        "num_rows": len(frame),
        "num_columns": len(frame.columns),
        "columns": list(frame.columns),
        "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
    }


def adapt_dataset(frame: pd.DataFrame, model_name: str | None = None,
                   task: str | None = None) -> tuple[pd.DataFrame, dict[str, str]]:
    original_columns = list(frame.columns)
    adapted = adapt_uploaded_dataset(frame)
    mapping = {
        source: target for source, target in zip(original_columns, adapted.columns)
        if source != target and source.strip().casefold() in {
            "population", "permanent_water", "parmanent_water"
        }
    }
    return adapted, mapping


def check_compatibility(frame: pd.DataFrame, model_name: str,
                        task: str | None = None) -> dict:
    if model_name in PLANNED_MODELS:
        return {"is_compatible": False, "missing_features": [],
                "warnings": [PLANNED_MODELS[model_name]]}
    if model_name not in TRAINED_MODELS:
        return {"is_compatible": False, "missing_features": [],
                "warnings": [f"Unknown model: {model_name}"]}
    if model_name not in get_available_models():
        return {"is_compatible": False, "missing_features": [],
                "warnings": [f"No trained checkpoint found for {model_name}"]}
    try:
        adapt_uploaded_dataset(frame)
    except ValueError as error:
        message = str(error)
        missing = [feature for feature in BASELINE_REQUIRED_FEATURES if feature not in frame.columns]
        return {"is_compatible": False, "missing_features": missing,
                "warnings": [message]}
    return {"is_compatible": True, "missing_features": [], "warnings": []}


def predict_uploaded_dataset(frame: pd.DataFrame, model_name: str,
                             task: str | None = None) -> dict:
    if model_name in PLANNED_MODELS:
        return {"status": "unavailable", "task": "regression", "model": model_name,
                "prediction": [], "metrics": {}, "warnings": [PLANNED_MODELS[model_name]]}
    if model_name not in TRAINED_MODELS:
        raise ValueError(f"Unknown or unavailable model: {model_name}")
    compatible = check_compatibility(frame, model_name, task)
    if not compatible["is_compatible"]:
        return {"status": "INCOMPATIBLE", "task": "regression", "model": model_name,
                "prediction": [], "metrics": {}, "warnings": compatible["warnings"]}
    return member2_predict(model_name, frame, checkpoint_path=TRAINED_MODELS[model_name],
                           task="regression")


def retrain_model(*args, **kwargs) -> dict:
    return {"status": "unavailable", "message": "Retraining is disabled in the dashboard.",
            "metrics": {}, "warnings": ["Use the explicit Member 2 training command outside the dashboard."]}
