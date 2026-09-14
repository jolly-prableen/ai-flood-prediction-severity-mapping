from __future__ import annotations
import numpy as np
from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix,
                             f1_score, mean_absolute_error, mean_squared_error,
                             precision_score, r2_score, recall_score, roc_auc_score)


def classification_metrics(y_true, y_pred, probabilities=None, average="binary") -> dict:
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    result = {"accuracy": float(accuracy_score(y_true, y_pred)),
              "precision": float(precision_score(y_true, y_pred, average=average, zero_division=0)),
              "recall": float(recall_score(y_true, y_pred, average=average, zero_division=0)),
              "f1": float(f1_score(y_true, y_pred, average=average, zero_division=0)),
              "confusion_matrix": confusion_matrix(y_true, y_pred).tolist()}
    if probabilities is not None and len(np.unique(y_true)) > 1:
        scores = np.asarray(probabilities)
        scores = scores[:, 1] if scores.ndim == 2 and scores.shape[1] > 1 else scores.reshape(-1)
        result["roc_auc"] = float(roc_auc_score(y_true, scores))
        result["pr_auc"] = float(average_precision_score(y_true, scores))
        result["brier"] = float(np.mean((scores - y_true) ** 2))
    else:
        result.update({"roc_auc": None, "pr_auc": None, "brier": None})
    return result


def regression_metrics(y_true, y_pred) -> dict:
    y_true, y_pred = np.asarray(y_true).reshape(-1), np.asarray(y_pred).reshape(-1)
    return {"mae": float(mean_absolute_error(y_true, y_pred)),
            "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
            "r2": float(r2_score(y_true, y_pred)) if len(np.unique(y_true)) > 1 else None}


def segmentation_metrics(y_true, probabilities, threshold=0.5) -> dict:
    truth = np.asarray(y_true).astype(bool)
    prediction = np.asarray(probabilities) >= threshold
    intersection = np.logical_and(truth, prediction).sum()
    union = np.logical_or(truth, prediction).sum()
    return {"iou": float(intersection / union) if union else None,
            "dice": float(2 * intersection / (truth.sum() + prediction.sum())) if truth.sum() + prediction.sum() else None,
            "precision": float(np.logical_and(truth, prediction).sum() / prediction.sum()) if prediction.sum() else 0.0,
            "recall": float(np.logical_and(truth, prediction).sum() / truth.sum()) if truth.sum() else 0.0}
