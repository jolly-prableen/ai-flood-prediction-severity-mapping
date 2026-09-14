"""Feature Ablation Study experiment on the untouched IFI baseline test split.

Inspired by the STURM-Flood paper (Notarangelo et al., 2025; DOI: 10.1080/20964471.2025.2458714),
which highlights systematic feature ablation studies on prediction accuracy as key future work.

Evaluates three feature configurations:
  A. Full Baseline: Population + Parmanent_Water
  B. Population Only: Population
  C. Permanent Water Only: Parmanent_Water

Uses the same untouched test split (109 rows) for all three configurations and preserves
existing baseline models and metrics unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

import sys
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.overfitting import diagnose_fit
from src.models.cnn_lstm.model import CNNLSTM
from src.models.cnn_transformer.model import CNNTransformer
from src.models.resnet_bilstm.model import ResNetBiLSTM
from src.training.trainer import Trainer
from src.utils.seed import set_seed
DATASET_CSV = PROJECT_ROOT / "data" / "processed" / "district_flood_area_regression.csv"
SPLIT_JSON = PROJECT_ROOT / "data" / "splits" / "district_flood_area_split.json"
BASELINE_MODELS_DIR = PROJECT_ROOT / "results" / "models"
ABLATION_OUTPUT_DIR = PROJECT_ROOT / "results" / "models" / "ablation"
SUMMARY_JSON_PATH = ABLATION_OUTPUT_DIR / "ablation_summary.json"

TARGET = "Corrected_Percent_Flooded_Area"

CONFIGURATIONS = {
    "Full Baseline": ["Population", "Parmanent_Water"],
    "Population Only": ["Population"],
    "Permanent Water Only": ["Parmanent_Water"],
}

CONFIG_SLUGS = {
    "Full Baseline": "full_baseline",
    "Population Only": "population_only",
    "Permanent Water Only": "water_only",
}

MODEL_FACTORIES = {
    "CNN + LSTM": CNNLSTM,
    "CNN + Transformer": CNNTransformer,
    "ResNet + BiLSTM": ResNetBiLSTM,
}

MODEL_SLUGS = {
    "CNN + LSTM": "cnn_lstm",
    "CNN + Transformer": "cnn_transformer",
    "ResNet + BiLSTM": "resnet_bilstm",
}


def compute_baseline_hashes() -> dict[str, str]:
    """Compute sha256 hashes of existing baseline checkpoints to guarantee immutability."""
    hashes = {}
    for name, slug in MODEL_SLUGS.items():
        ckpt = BASELINE_MODELS_DIR / slug / "best_model.pt"
        if ckpt.is_file():
            hashes[name] = hashlib.sha256(ckpt.read_bytes()).hexdigest()
    return hashes


def regression_scores(actual: np.ndarray, prediction: np.ndarray) -> dict[str, float]:
    actual, prediction = np.asarray(actual), np.asarray(prediction)
    return {
        "MAE": float(mean_absolute_error(actual, prediction)),
        "RMSE": float(mean_squared_error(actual, prediction) ** 0.5),
        "R2": float(r2_score(actual, prediction)) if len(np.unique(actual)) > 1 else None,
    }


def predict_model(model: torch.nn.Module, loader: DataLoader, device: torch.device) -> tuple[np.ndarray, np.ndarray]:
    model.eval()
    actual, prediction = [], []
    with torch.no_grad():
        for inputs, targets in loader:
            output = model(inputs.to(device)).logits.detach().cpu().reshape(-1).numpy()
            prediction.extend(output.tolist())
            actual.extend(targets.numpy().reshape(-1).tolist())
    return np.asarray(actual), np.asarray(prediction)


def evaluate_existing_baseline(model_name: str, test_loader: DataLoader, device: torch.device) -> dict[str, Any]:
    """Evaluate existing untouched baseline checkpoint on test loader."""
    slug = MODEL_SLUGS[model_name]
    ckpt_path = BASELINE_MODELS_DIR / slug / "best_model.pt"
    if not ckpt_path.is_file():
        raise FileNotFoundError(f"Baseline checkpoint missing: {ckpt_path}")
    checkpoint = torch.load(ckpt_path, map_location=device, weights_only=False)
    kwargs = checkpoint.get("metadata", {}).get("model_kwargs", {"input_dim": 2, "task": "regression"})
    model = MODEL_FACTORIES[model_name](**kwargs)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    actual, pred = predict_model(model, test_loader, device)
    scores = regression_scores(actual, pred)
    return {
        "Model": model_name,
        "Feature Configuration": "Full Baseline",
        "Features": CONFIGURATIONS["Full Baseline"],
        "MAE": scores["MAE"],
        "RMSE": scores["RMSE"],
        "R2": scores["R2"],
        "Type": "Existing Baseline Checkpoint",
    }


def train_ablation_model(model_name: str, config_name: str, features: list[str],
                        frame: pd.DataFrame, train_idx: np.ndarray, val_idx: np.ndarray,
                        test_idx: np.ndarray, epochs: int = 30, batch_size: int = 32,
                        device: str = "cpu") -> dict[str, Any]:
    """Train a reduced-feature ablation model deterministically and save separately."""
    set_seed(42)
    slug = MODEL_SLUGS[model_name]
    cfg_slug = CONFIG_SLUGS[config_name]
    out_dir = ABLATION_OUTPUT_DIR / slug / cfg_slug
    out_dir.mkdir(parents=True, exist_ok=True)

    X_raw = frame[features].to_numpy(dtype=np.float32)
    y = frame[TARGET].to_numpy(dtype=np.float32)

    scaler = StandardScaler().fit(X_raw[train_idx])
    X = scaler.transform(X_raw).astype(np.float32).reshape(len(frame), 1, len(features))

    train_loader = DataLoader(TensorDataset(torch.from_numpy(X[train_idx]), torch.from_numpy(y[train_idx])),
                              batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(torch.from_numpy(X[val_idx]), torch.from_numpy(y[val_idx])),
                            batch_size=batch_size)
    test_loader = DataLoader(TensorDataset(torch.from_numpy(X[test_idx]), torch.from_numpy(y[test_idx])),
                             batch_size=batch_size)

    factory = MODEL_FACTORIES[model_name]
    model_kwargs = {"input_dim": len(features), "task": "regression"}
    model = factory(**model_kwargs)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    trainer = Trainer(model, task="regression", patience=8, device=device,
                      optimizer=optimizer,
                      scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(
                          optimizer, mode="min", patience=3, factor=0.5
                      ))
    ckpt_path = out_dir / "best_model.pt"
    started = time.perf_counter()
    history = trainer.fit(train_loader, val_loader, epochs=epochs, checkpoint_path=ckpt_path,
                          metadata={"model_kwargs": model_kwargs, "task": "regression",
                                    "ablation_config": config_name, "features": features})
    training_time = time.perf_counter() - started
    diagnosis = diagnose_fit(history)
    correction = "none"

    if diagnosis["diagnosis"] == "OVERFITTING":
        correction = "retrained with dropout=0.35 and weight_decay=0.0005"
        model_kwargs["dropout"] = 0.35
        model = factory(**model_kwargs)
        trainer = Trainer(model, task="regression", patience=8, device=device,
                          optimizer=torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=5e-4))
        history = trainer.fit(train_loader, val_loader, epochs=epochs, checkpoint_path=ckpt_path,
                              metadata={"model_kwargs": model_kwargs, "task": "regression",
                                        "ablation_config": config_name, "features": features,
                                        "correction": correction})
        diagnosis = diagnose_fit(history)

    actual, prediction = predict_model(model, test_loader, trainer.device)
    test_scores = regression_scores(actual, prediction)
    val_actual, val_prediction = predict_model(model, val_loader, trainer.device)
    val_scores = regression_scores(val_actual, val_prediction)

    (out_dir / "model_config.json").write_text(json.dumps({
        "model": model_name, "task": "regression", "model_kwargs": model_kwargs,
        "ablation_config": config_name, "features": features,
    }, indent=2), encoding="utf-8")
    (out_dir / "feature_schema.json").write_text(json.dumps({
        "features": features, "target": TARGET, "input_shape": ["batch", 1, len(features)],
        "ablation_config": config_name,
    }, indent=2), encoding="utf-8")
    with (out_dir / "preprocessing.pkl").open("wb") as f:
        pickle.dump(scaler, f)

    record = {
        "Model": model_name,
        "Feature Configuration": config_name,
        "Features": features,
        "MAE": test_scores["MAE"],
        "RMSE": test_scores["RMSE"],
        "R2": test_scores["R2"],
        "Validation MAE": val_scores["MAE"],
        "Validation RMSE": val_scores["RMSE"],
        "Training Time": training_time,
        "Best Epoch": int(np.argmin(history["val_loss"]) + 1),
        "Diagnosis": diagnosis["diagnosis"],
        "Correction": correction,
        "Type": "Ablation Retrained Model",
    }
    (out_dir / "metrics.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    (out_dir / "training_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    return record


def run_ablation_study(epochs: int = 30, batch_size: int = 32, device: str = "cpu") -> dict[str, Any]:
    """Execute ablation study across all 3 trained models and 3 feature configurations."""
    hashes_before = compute_baseline_hashes()
    frame = pd.read_csv(DATASET_CSV)
    split = json.loads(SPLIT_JSON.read_text(encoding="utf-8"))
    train_idx = np.asarray(split["train_indices"], dtype=int)
    val_idx = np.asarray(split["validation_indices"], dtype=int)
    test_idx = np.asarray(split["test_indices"], dtype=int)

    summary: dict[str, dict[str, Any]] = {}

    for model_name in MODEL_FACTORIES:
        summary[model_name] = {}
        # 1. Full Baseline
        slug = MODEL_SLUGS[model_name]
        with (BASELINE_MODELS_DIR / slug / "preprocessing.pkl").open("rb") as f:
            base_scaler = pickle.load(f)
        X_full_raw = frame[CONFIGURATIONS["Full Baseline"]].to_numpy(dtype=np.float32)
        X_full = base_scaler.transform(X_full_raw).astype(np.float32).reshape(len(frame), 1, 2)
        y_raw = frame[TARGET].to_numpy(dtype=np.float32)
        test_loader = DataLoader(TensorDataset(torch.from_numpy(X_full[test_idx]), torch.from_numpy(y_raw[test_idx])),
                                 batch_size=batch_size)
        base_record = evaluate_existing_baseline(model_name, test_loader, torch.device(device))
        summary[model_name]["Full Baseline"] = base_record

        # 2. Population Only
        pop_record = train_ablation_model(
            model_name, "Population Only", CONFIGURATIONS["Population Only"],
            frame, train_idx, val_idx, test_idx, epochs=epochs, batch_size=batch_size, device=device
        )
        summary[model_name]["Population Only"] = pop_record

        # 3. Permanent Water Only
        water_record = train_ablation_model(
            model_name, "Permanent Water Only", CONFIGURATIONS["Permanent Water Only"],
            frame, train_idx, val_idx, test_idx, epochs=epochs, batch_size=batch_size, device=device
        )
        summary[model_name]["Permanent Water Only"] = water_record

    ABLATION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Verify baseline model hashes are strictly unchanged
    hashes_after = compute_baseline_hashes()
    for name in hashes_before:
        assert hashes_before[name] == hashes_after[name], (
            f"FATAL: Baseline model checkpoint {name} was modified during ablation run!"
        )

    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    print("Starting Feature Ablation Study...")
    summary = run_ablation_study(epochs=args.epochs, batch_size=args.batch_size, device=args.device)
    print("\nAblation Study Completed Successfully!\n")
    for model_name, configs in summary.items():
        print(f"=== {model_name} ===")
        for cfg_name, res in configs.items():
            print(f"  {cfg_name:22s} | MAE: {res['MAE']:.4f} | RMSE: {res['RMSE']:.4f} | R²: {res['R2']:.4f} ({res['Type']})")
        print()


if __name__ == "__main__":
    main()
