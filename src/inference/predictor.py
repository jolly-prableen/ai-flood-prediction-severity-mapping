from __future__ import annotations
import json
from pathlib import Path
import pickle
import time
import torch
import numpy as np
from src.models.model_registry import MODEL_REGISTRY
from src.inference.dataset_adapter import to_model_array

ROOT = Path(__file__).resolve().parents[2]


def _model_directory(model_name: str, checkpoint_path=None) -> Path:
    if checkpoint_path:
        return Path(checkpoint_path).parent
    directory_name = model_name.lower().replace(" + ", "_").replace(" ", "_")
    return ROOT / "results" / "models" / directory_name


def load_model(model_name: str, checkpoint_path=None, model_kwargs=None, device=None):
    if model_name not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model: {model_name}")
    path = Path(checkpoint_path) if checkpoint_path else _model_directory(model_name) / "best_model.pt"
    if not path.exists():
        raise FileNotFoundError(f"No checkpoint found at {path}. Train the model first.")
    checkpoint = torch.load(path, map_location=device or "cpu", weights_only=False)
    model = MODEL_REGISTRY[model_name](**(model_kwargs or checkpoint.get("metadata", {}).get("model_kwargs", {})))
    model.load_state_dict(checkpoint["model_state_dict"])
    return model.eval()


def predict_with_model(model_name, input_data, checkpoint_path=None, model_kwargs=None, device="cpu"):
    model = load_model(model_name, checkpoint_path, model_kwargs, device)
    tensor = input_data if isinstance(input_data, torch.Tensor) else torch.as_tensor(input_data, dtype=torch.float32)
    with torch.no_grad():
        output = model(tensor.to(device))
    result = {"model": model_name, "probability": output.probabilities.cpu().tolist(),
              "predicted_class": output.predicted_class.cpu().tolist()}
    return result


def predict_uploaded_dataset(model_name: str, uploaded_data, checkpoint_path=None,
                             task="regression", device="cpu") -> dict:
    """Predict without fitting or modifying preprocessing artifacts."""
    if task != "regression":
        raise ValueError("predict_uploaded_dataset currently supports task='regression' only")
    directory = _model_directory(model_name, checkpoint_path)
    schema_path = directory / "feature_schema.json"
    preprocessing_path = directory / "preprocessing.pkl"
    if not schema_path.exists() or not preprocessing_path.exists():
        raise FileNotFoundError("Trained feature schema and preprocessing artifact are required")
    features = to_model_array(uploaded_data)
    with preprocessing_path.open("rb") as file:
        scaler = pickle.load(file)
    transformed = scaler.transform(features).astype(np.float32).reshape(len(features), 1, features.shape[1])
    started = time.perf_counter()
    model = load_model(model_name, checkpoint_path, {"input_dim": features.shape[1], "task": task}, device)
    with torch.no_grad():
        prediction = model(torch.from_numpy(transformed).to(device)).logits.cpu().reshape(-1).tolist()
    metrics_path = directory / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    return {"status": "success", "task": task, "model": model_name, "prediction": prediction,
            "metrics": metrics, "warnings": [], "inference_time": time.perf_counter() - started}


def retrain_model(csv="data/processed/district_flood_area_regression.csv",
                  split="data/splits/district_flood_area_split.json", epochs=30,
                  batch_size=32, device=None):
    """Explicit retraining entry point; prediction APIs never call this."""
    from src.training.train_real_regression import main as train_main
    arguments = ["--csv", str(csv), "--split", str(split), "--epochs", str(epochs),
                 "--batch-size", str(batch_size)]
    if device:
        arguments.extend(["--device", str(device)])
    return train_main(arguments)


def load_metrics(path=ROOT / "results" / "model_comparison.csv"):
    import pandas as pd
    return pd.read_csv(path) if Path(path).exists() else None


def load_comparison_results(path=ROOT / "results" / "model_comparison.csv"):
    return load_metrics(path)
