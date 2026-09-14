from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def plot_training_history(history: dict, path="results/plots/training_curves.png") -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(history.get("train_loss", []), label="train")
    axes[0].plot(history.get("val_loss", []), label="validation")
    axes[0].set_title("Loss")
    metric_name = "mae" if history.get("task") == "regression" else "metric"
    axes[1].plot(history.get(f"train_{metric_name}", []), label="train")
    axes[1].plot(history.get(f"val_{metric_name}", []), label="validation")
    axes[1].set_title("MAE" if metric_name == "mae" else "F1")
    for axis in axes:
        axis.legend()
        axis.set_xlabel("Epoch")
    figure.tight_layout()
    figure.savefig(destination, dpi=150)
    plt.close(figure)


def plot_model_comparison(comparison: pd.DataFrame, path="results/plots/model_comparison.png") -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(8, 4))
    comparison.plot.bar(x="model", y="f1", ax=axis, legend=False)
    axis.set_ylabel("F1")
    axis.set_title("Model comparison")
    figure.tight_layout()
    figure.savefig(destination, dpi=150)
    plt.close(figure)


def plot_regression_predictions(actual, predicted, path="results/plots/regression_predictions.png") -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(5, 5))
    axis.scatter(actual, predicted, alpha=0.7)
    lower = min(min(actual), min(predicted))
    upper = max(max(actual), max(predicted))
    axis.plot([lower, upper], [lower, upper], linestyle="--", color="black")
    axis.set_xlabel("Actual")
    axis.set_ylabel("Predicted")
    axis.set_title("Regression predictions")
    figure.tight_layout()
    figure.savefig(destination, dpi=150)
    plt.close(figure)
