"""Train compatible Member 2 models on the prepared real IFI regression task."""
from __future__ import annotations

import argparse
import json
import pickle
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

from src.evaluation.cross_validation import regression_cv
from src.evaluation.overfitting import diagnose_fit
from src.models.cnn_lstm.model import CNNLSTM
from src.models.cnn_transformer.model import CNNTransformer
from src.models.resnet_bilstm.model import ResNetBiLSTM
from src.models.baselines.models import build_regression_baselines
from src.training.trainer import Trainer
from src.utils.seed import set_seed
from src.visualization.plots import plot_training_history

FEATURES = ["Population", "Parmanent_Water"]
TARGET = "Corrected_Percent_Flooded_Area"
MODEL_FACTORIES = {
    "CNN + LSTM": CNNLSTM,
    "CNN + Transformer": CNNTransformer,
    "ResNet + BiLSTM": ResNetBiLSTM,
}


def regression_scores(actual, prediction) -> dict:
    actual, prediction = np.asarray(actual), np.asarray(prediction)
    return {
        "mae": float(mean_absolute_error(actual, prediction)),
        "rmse": float(mean_squared_error(actual, prediction) ** 0.5),
        "r2": float(r2_score(actual, prediction)) if len(np.unique(actual)) > 1 else None,
    }


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def save_preprocessing(path: Path, scaler: StandardScaler) -> None:
    with path.open("wb") as file:
        pickle.dump(scaler, file)


def predict_model(model, loader, device) -> tuple[np.ndarray, np.ndarray]:
    model.eval()
    actual, prediction = [], []
    with torch.no_grad():
        for inputs, targets in loader:
            output = model(inputs.to(device)).logits.detach().cpu().reshape(-1).numpy()
            prediction.extend(output.tolist())
            actual.extend(targets.numpy().reshape(-1).tolist())
    return np.asarray(actual), np.asarray(prediction)


def train_hybrid(name, factory, train_loader, val_loader, test_loader, input_dim,
                 output_dir: Path, scaler: StandardScaler, epochs: int,
                 batch_size: int, device: str) -> dict:
    model_kwargs = {"input_dim": input_dim, "task": "regression"}
    model = factory(**model_kwargs)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    trainer = Trainer(model, task="regression", patience=8, device=device,
                      optimizer=optimizer,
                      scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(
                          optimizer, mode="min", patience=3, factor=0.5
                      ))
    model_dir = output_dir / name.lower().replace(" + ", "_").replace(" ", "_")
    model_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = model_dir / "best_model.pt"
    history = trainer.fit(train_loader, val_loader, epochs=epochs, checkpoint_path=checkpoint,
                          metadata={"model_kwargs": model_kwargs, "task": "regression"})
    diagnosis = diagnose_fit(history)
    correction = "none"
    if diagnosis["diagnosis"] == "OVERFITTING":
        correction = "retrained with dropout=0.35 and weight_decay=0.0005"
        model_kwargs["dropout"] = 0.35
        model = factory(**model_kwargs)
        trainer = Trainer(model, task="regression", patience=8, device=device,
                          optimizer=torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=5e-4))
        history = trainer.fit(train_loader, val_loader, epochs=epochs, checkpoint_path=checkpoint,
                              metadata={"model_kwargs": model_kwargs, "task": "regression", "correction": correction})
        diagnosis = diagnose_fit(history)
    actual, prediction = predict_model(model, test_loader, trainer.device)
    test_scores = regression_scores(actual, prediction)
    val_actual, val_prediction = predict_model(model, val_loader, trainer.device)
    val_scores = regression_scores(val_actual, val_prediction)
    write_json(model_dir / "model_config.json", {"model": name, "task": "regression", "model_kwargs": model_kwargs})
    write_json(model_dir / "feature_schema.json", {"features": FEATURES, "target": TARGET, "input_shape": ["batch", 1, input_dim]})
    save_preprocessing(model_dir / "preprocessing.pkl", scaler)
    return {
        "Model": name, "Task": "regression", "MAE": test_scores["mae"], "RMSE": test_scores["rmse"],
        "R2": test_scores["r2"], "Validation MAE": val_scores["mae"], "Validation RMSE": val_scores["rmse"],
        "Training Time": history["training_time"], "Best Epoch": int(np.argmin(history["val_loss"]) + 1),
        "Diagnosis": diagnosis["diagnosis"], "Correction": correction,
    }, history


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", default="data/processed/district_flood_area_regression.csv")
    parser.add_argument("--split", default="data/splits/district_flood_area_split.json")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default=None)
    parser.add_argument("--output-dir", default="results/models")
    parser.add_argument("--skip-cv", action="store_true")
    args = parser.parse_args(argv)
    set_seed(42)
    frame = pd.read_csv(args.csv)
    if frame[FEATURES + [TARGET]].isna().any().any():
        raise ValueError("Prepared dataset contains missing features or target values")
    split = json.loads(Path(args.split).read_text(encoding="utf-8"))
    train_idx, val_idx, test_idx = (np.asarray(split[key], dtype=int) for key in ("train_indices", "validation_indices", "test_indices"))
    X_raw = frame[FEATURES].to_numpy(dtype=np.float32)
    y = frame[TARGET].to_numpy(dtype=np.float32)
    scaler = StandardScaler().fit(X_raw[train_idx])
    X = scaler.transform(X_raw).astype(np.float32).reshape(len(frame), 1, len(FEATURES))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_preprocessing(output_dir / "preprocessing.pkl", scaler)
    write_json(output_dir / "feature_schema.json", {"features": FEATURES, "target": TARGET, "sequence_length": 1})
    train_loader = DataLoader(TensorDataset(torch.from_numpy(X[train_idx]), torch.from_numpy(y[train_idx])), args.batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(torch.from_numpy(X[val_idx]), torch.from_numpy(y[val_idx])), args.batch_size)
    test_loader = DataLoader(TensorDataset(torch.from_numpy(X[test_idx]), torch.from_numpy(y[test_idx])), args.batch_size)
    rows, histories = [], {}
    for name, factory in MODEL_FACTORIES.items():
        row, history = train_hybrid(name, factory, train_loader, val_loader, test_loader, len(FEATURES), output_dir, scaler, args.epochs, args.batch_size, args.device)
        rows.append(row)
        histories[name] = history
        model_dir = output_dir / name.lower().replace(" + ", "_").replace(" ", "_")
        write_json(model_dir / "metrics.json", row)
        write_json(model_dir / "training_history.json", history)
        plot_training_history(history, Path("results/plots") / (model_dir.name + "_training_curves.png"))
    for name, baseline in build_regression_baselines().items():
        started = time.perf_counter()
        baseline.fit(X_raw[train_idx], y[train_idx])
        val_prediction = baseline.predict(X_raw[val_idx])
        test_prediction = baseline.predict(X_raw[test_idx])
        test_scores = regression_scores(y[test_idx], test_prediction)
        validation_scores = regression_scores(y[val_idx], val_prediction)
        row = {"Model": name, "Task": "regression", "MAE": test_scores["mae"],
               "RMSE": test_scores["rmse"], "R2": test_scores["r2"],
               "Validation MAE": validation_scores["mae"],
               "Validation RMSE": validation_scores["rmse"],
               "Training Time": time.perf_counter() - started, "Best Epoch": None,
               "Diagnosis": "not applicable", "Correction": "not applicable"}
        rows.append(row)
        model_dir = output_dir / name.lower().replace(" ", "_")
        model_dir.mkdir(parents=True, exist_ok=True)
        with (model_dir / "best_model.pkl").open("wb") as file:
            pickle.dump(baseline, file)
        save_preprocessing(model_dir / "preprocessing.pkl", scaler)
        write_json(model_dir / "feature_schema.json", {"features": FEATURES, "target": TARGET, "input_shape": ["batch", 1, len(FEATURES)]})
        write_json(model_dir / "metrics.json", row)
        write_json(model_dir / "model_config.json", {"model": name, "task": "regression", "features": FEATURES})
        write_json(model_dir / "training_history.json", {
            "task": "regression", "training_time": row["Training Time"],
            "validation_metrics": {"mae": row["Validation MAE"], "rmse": row["Validation RMSE"]},
        })
    comparison = pd.DataFrame(rows)
    Path("results").mkdir(exist_ok=True)
    comparison.to_csv("results/model_comparison.csv", index=False)
    if not args.skip_cv:
        cv = regression_cv(X_raw, y, n_splits=10, seed=42)
        cv.to_csv("results/cv_regression_results.csv", index=False)
    summary = {"task": "district-level regression", "rows": rows, "spatial_models": {
        "U-Net + ConvLSTM": "PENDING SPATIAL DATA",
        "Attention U-Net + LSTM": "PENDING SPATIAL DATA",
    }}
    write_json(Path("results/training_summary.json"), summary)
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
