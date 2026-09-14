from __future__ import annotations
from pathlib import Path
import pandas as pd


COMPARISON_COLUMNS = ["model", "task", "accuracy", "precision", "recall", "f1",
                      "roc_auc", "mae", "rmse", "iou", "dice", "training_time", "parameters"]


def parameter_count(model) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def save_model_comparison(rows: list[dict], path="results/model_comparison.csv") -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    for column in COMPARISON_COLUMNS:
        if column not in frame:
            frame[column] = None
    frame = frame[COMPARISON_COLUMNS]
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False)
    return frame


def save_predictions(rows: list[dict], path="results/model_predictions.csv") -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False)
    return frame
