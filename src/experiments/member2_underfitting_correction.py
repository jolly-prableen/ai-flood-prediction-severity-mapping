"""Controlled Member 2 underfitting experiment on the existing baseline split."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

from src.evaluation.overfitting import diagnose_fit
from src.models.cnn_lstm.model import CNNLSTM
from src.models.cnn_transformer.model import CNNTransformer
from src.models.resnet_bilstm.model import ResNetBiLSTM
from src.training.trainer import Trainer
from src.utils.seed import set_seed

FEATURES = ["Population", "Parmanent_Water"]
TARGET = "Corrected_Percent_Flooded_Area"
EXPERIMENT_ROOT = Path("results/experiments/underfitting_correction")
MODEL_FACTORIES = {
    "CNN + LSTM": CNNLSTM,
    "CNN + Transformer": CNNTransformer,
    "ResNet + BiLSTM": ResNetBiLSTM,
}
BASELINE_METRICS = {
    "CNN + LSTM": {"MAE": 2.433762, "RMSE": 3.376278, "R2": 0.074452},
    "CNN + Transformer": {"MAE": 2.427292, "RMSE": 3.454255, "R2": 0.031206},
    "ResNet + BiLSTM": {"MAE": 2.296399, "RMSE": 3.359883, "R2": 0.083419},
}
CONFIGS = {
    "control": {
        "hidden_dim": 32, "dropout": 0.2, "num_layers": 1,
        "learning_rate": 1e-3, "weight_decay": 1e-4, "max_epochs": 20,
        "patience": 6,
    },
    "capacity_low_regularization": {
        "hidden_dim": 64, "dropout": 0.1, "num_layers": 2,
        "learning_rate": 5e-4, "weight_decay": 1e-5, "max_epochs": 35,
        "patience": 8,
    },
}


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str), encoding="utf-8")


def checkpoint_hashes(project_root: Path) -> dict[str, str]:
    result = {}
    for name in MODEL_FACTORIES:
        slug = name.lower().replace(" + ", "_").replace(" ", "_")
        path = project_root / "results/models" / slug / "best_model.pt"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        result[name] = digest
    return result


def scores(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    error = predicted - actual
    return {
        "MAE": float(mean_absolute_error(actual, predicted)),
        "MSE": float(mean_squared_error(actual, predicted)),
        "RMSE": float(mean_squared_error(actual, predicted) ** 0.5),
        "R2": float(r2_score(actual, predicted)),
        "Mean_Bias": float(error.mean()),
        "Median_Absolute_Error": float(np.median(np.abs(error))),
        "Maximum_Absolute_Error": float(np.max(np.abs(error))),
    }


def model_kwargs(model_name: str, config: dict) -> dict:
    kwargs = {"input_dim": 2, "task": "regression",
              "num_layers": config["num_layers"], "dropout": config["dropout"]}
    if model_name == "CNN + LSTM":
        kwargs["hidden_dim"] = config["hidden_dim"]
        kwargs["embedding_dim"] = config["hidden_dim"]
    elif model_name == "CNN + Transformer":
        kwargs["embedding_dim"] = config["hidden_dim"]
        kwargs["num_heads"] = 4
    else:
        kwargs["hidden_dim"] = config["hidden_dim"]
    return kwargs


def predict(model, inputs: np.ndarray, targets: np.ndarray, device: torch.device) -> tuple[np.ndarray, np.ndarray]:
    model.eval()
    with torch.no_grad():
        output = model(torch.from_numpy(inputs).to(device)).logits.detach().cpu().reshape(-1).numpy()
    return targets, output


def plot_history(history: dict, path: Path, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(7, 4))
    axis.plot(history["train_loss"], label="train loss")
    axis.plot(history["val_loss"], label="validation loss")
    axis.set(xlabel="Epoch", ylabel="MSE loss", title=title)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    torch.set_num_threads(1)
    project_root = args.project_root.resolve()
    output_root = project_root / EXPERIMENT_ROOT
    histories_dir = output_root / "training_histories"
    plots_dir = output_root / "plots"
    output_root.mkdir(parents=True, exist_ok=True)
    histories_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    before_hashes = checkpoint_hashes(project_root)
    frame = pd.read_csv(project_root / "data/processed/district_flood_area_regression.csv")
    split = json.loads((project_root / "data/splits/district_flood_area_split.json").read_text(encoding="utf-8"))
    train_idx = np.asarray(split["train_indices"], dtype=int)
    val_idx = np.asarray(split["validation_indices"], dtype=int)
    test_idx = np.asarray(split["test_indices"], dtype=int)
    raw_x = frame[FEATURES].to_numpy(dtype=np.float32)
    y = frame[TARGET].to_numpy(dtype=np.float32)
    scaler = StandardScaler().fit(raw_x[train_idx])
    scaled_x = scaler.transform(raw_x).astype(np.float32).reshape(len(frame), 1, 2)
    train_loader = DataLoader(TensorDataset(torch.from_numpy(scaled_x[train_idx]), torch.from_numpy(y[train_idx])), batch_size=32, shuffle=True)
    val_loader = DataLoader(TensorDataset(torch.from_numpy(scaled_x[val_idx]), torch.from_numpy(y[val_idx])), batch_size=32)
    device = torch.device(args.device)

    rows = []
    selected_models = {}
    for model_name, factory in MODEL_FACTORIES.items():
        candidates = []
        for config_name, config in CONFIGS.items():
            set_seed(args.seed)
            kwargs = model_kwargs(model_name, config)
            model = factory(**kwargs)
            optimizer = torch.optim.AdamW(model.parameters(), lr=config["learning_rate"], weight_decay=config["weight_decay"])
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", patience=4, factor=0.5)
            trainer = Trainer(model, optimizer=optimizer, scheduler=scheduler, patience=config["patience"], device=device, task="regression")
            run_dir = output_root / "checkpoints" / model_name.lower().replace(" + ", "_").replace(" ", "_") / config_name
            checkpoint = run_dir / "best_model.pt"
            history = trainer.fit(train_loader, val_loader, epochs=config["max_epochs"], checkpoint_path=checkpoint,
                                  metadata={"model": model_name, "task": "regression", "config_name": config_name, "model_kwargs": kwargs})
            diagnosis = diagnose_fit(history)
            train_actual, train_pred = predict(model, scaled_x[train_idx], y[train_idx], trainer.device)
            val_actual, val_pred = predict(model, scaled_x[val_idx], y[val_idx], trainer.device)
            train_scores = scores(train_actual, train_pred)
            val_scores = scores(val_actual, val_pred)
            best_epoch = int(np.argmin(history["val_mae"]) + 1)
            row = {
                "Model": model_name, "Config": config_name, "Best_Epoch": best_epoch,
                "Final_Train_Loss": float(history["train_loss"][-1]),
                "Final_Validation_Loss": float(history["val_loss"][-1]),
                "Train_Validation_Loss_Gap": float(history["val_loss"][-1] - history["train_loss"][-1]),
                "Train_MAE": train_scores["MAE"], "Validation_MAE": val_scores["MAE"],
                "Train_RMSE": train_scores["RMSE"], "Validation_RMSE": val_scores["RMSE"],
                "Validation_R2": val_scores["R2"], "Diagnosis": diagnosis["diagnosis"],
                "Overfitting": diagnosis["diagnosis"] == "OVERFITTING",
                "Underfitting": diagnosis["diagnosis"] == "UNDERFITTING",
                "Max_Epochs": config["max_epochs"], "Patience": config["patience"],
                "Learning_Rate": config["learning_rate"], "Weight_Decay": config["weight_decay"],
                "Hidden_Dim": config["hidden_dim"], "Dropout": config["dropout"],
                "Num_Layers": config["num_layers"], "Checkpoint": str(checkpoint.relative_to(project_root)),
            }
            rows.append(row)
            write_json(histories_dir / f"{model_name.lower().replace(' + ', '_').replace(' ', '_')}_{config_name}.json", history)
            plot_history(history, plots_dir / f"{model_name.lower().replace(' + ', '_').replace(' ', '_')}_{config_name}_loss.png", f"{model_name} - {config_name}")
            candidates.append(row)
        selected_models[model_name] = min(candidates, key=lambda item: item["Validation_MAE"])

    results_frame = pd.DataFrame(rows)
    results_frame.to_csv(output_root / "experiment_results.csv", index=False)
    best_configs = {name: {key: value for key, value in row.items() if key != "Checkpoint"}
                    for name, row in selected_models.items()}
    write_json(output_root / "best_configs.json", best_configs)

    # The test split is first accessed here, after validation-only selection.
    final_rows = []
    for model_name, selected in selected_models.items():
        checkpoint = project_root / selected["Checkpoint"]
        config_name = selected["Config"]
        config = CONFIGS[config_name]
        kwargs = model_kwargs(model_name, config)
        from src.inference.predictor import load_model
        model = load_model(model_name, checkpoint_path=checkpoint, model_kwargs=kwargs, device="cpu")
        test_actual, test_pred = predict(model, scaled_x[test_idx], y[test_idx], torch.device("cpu"))
        test_scores = scores(test_actual, test_pred)
        baseline = BASELINE_METRICS[model_name]
        final_rows.append({"Model": model_name, "Selected_Config": config_name, **test_scores,
                           "Baseline_MAE": baseline["MAE"], "Baseline_RMSE": baseline["RMSE"], "Baseline_R2": baseline["R2"],
                           "MAE_Change": test_scores["MAE"] - baseline["MAE"],
                           "RMSE_Change": test_scores["RMSE"] - baseline["RMSE"],
                           "R2_Change": test_scores["R2"] - baseline["R2"],
                           "Underfitting_Remains": selected["Underfitting"],
                           "Generalization_Improved": test_scores["MAE"] < baseline["MAE"] and test_scores["RMSE"] < baseline["RMSE"] and test_scores["R2"] > baseline["R2"]})
    final_frame = pd.DataFrame(final_rows)
    final_frame.to_csv(output_root / "final_test_comparison.csv", index=False)

    plot_frame = final_frame.set_index("Model")[["Baseline_MAE", "MAE", "Baseline_RMSE", "RMSE"]]
    axis = plot_frame.plot.bar(figsize=(9, 5), title="Protected baseline vs selected experiment")
    axis.set_ylabel("Metric value")
    figure = axis.get_figure(); figure.tight_layout(); figure.savefig(plots_dir / "baseline_vs_corrected_metrics.png", dpi=150); plt.close(figure)

    after_hashes = checkpoint_hashes(project_root)
    summary = {
        "dataset": "data/processed/district_flood_area_regression.csv",
        "features": FEATURES, "target": TARGET,
        "split_counts": {"train": len(train_idx), "validation": len(val_idx), "test": len(test_idx)},
        "selection_rule": "minimum validation MAE; test split accessed only after selection",
        "configurations": CONFIGS,
        "best_configurations": selected_models,
        "final_test_results": final_frame.to_dict("records"),
        "overall_best_selected_model": final_frame.sort_values("MAE").iloc[0]["Model"],
        "checkpoint_hashes_before": before_hashes,
        "checkpoint_hashes_after": after_hashes,
        "checkpoint_hashes_unchanged": before_hashes == after_hashes,
        "test_accessed_only_after_selection": True,
        "member1_work_performed": False,
        "retraining_of_protected_baseline": False,
    }
    write_json(output_root / "experiment_summary.json", summary)
    print(final_frame.to_string(index=False))
    print(f"checkpoint_hashes_unchanged={before_hashes == after_hashes}")


if __name__ == "__main__":
    main()
