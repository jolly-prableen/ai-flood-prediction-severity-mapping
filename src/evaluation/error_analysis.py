"""Prediction Error Analysis module for flood prediction regression models.

Research-inspired model-improvement extension adapted from error-analysis
methodology in flood-detection literature (e.g., AlleyFloodNet).
Systematically analyzes test-set prediction errors, residuals, and outlier
districts without modifying baseline checkpoints or fabricating data.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_CSV = PROJECT_ROOT / "data" / "processed" / "district_flood_area_regression.csv"
ACTUAL_VS_PREDICTED_CSV = PROJECT_ROOT / "results" / "evaluation" / "actual_vs_predicted.csv"


def calculate_error_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    """Calculate error metrics for regression predictions.
    
    1. Error: prediction - actual
    2. Absolute Error: abs(prediction - actual)
    3. Squared Error: (prediction - actual)^2
    4. MAE: mean(abs(prediction - actual))
    5. RMSE: sqrt(mean((prediction - actual)^2))
    6. R2: coefficient of determination
    """
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    error = predicted - actual
    absolute_error = np.abs(error)
    squared_error = error ** 2

    mae = float(mean_absolute_error(actual, predicted))
    rmse = float(mean_squared_error(actual, predicted) ** 0.5)
    r2 = float(r2_score(actual, predicted)) if len(np.unique(actual)) > 1 else 0.0
    mean_error = float(np.mean(error))
    max_abs_error = float(np.max(absolute_error))

    return {
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2,
        "Mean_Error": mean_error,
        "Max_Absolute_Error": max_abs_error,
        "Sample_Count": int(len(actual)),
    }


def generate_error_interpretation(
    model_name: str,
    metrics: dict[str, float],
    top_error_row: dict[str, Any],
    threshold: float = 3.0,
    count_above_threshold: int = 0,
) -> str:
    """Generate automatic, non-causal interpretation of error metrics and outliers."""
    mean_err = metrics["Mean_Error"]
    direction = "over-prediction" if mean_err > 0 else "under-prediction" if mean_err < 0 else "zero bias"
    
    parts = [
        f"For **{model_name}**, the model's mean error is **{mean_err:+.4f}%**, indicating **{direction}** on average across the 109 test districts.",
        f"**{count_above_threshold}** test samples exhibit an absolute error greater than **{threshold:.1f}%** flooded area.",
        f"The largest prediction error occurs for **{top_error_row['District']}**, where the actual flooded area is **{top_error_row['Actual Flooded Area (%)']:.2f}%** and the model predicted **{top_error_row['Predicted Flooded Area (%)']:.2f}%** (error: **{top_error_row['Error']:+.2f}%**, absolute error: **{top_error_row['Absolute Error']:.2f}%**).",
        "*(Note: Large residuals highlight challenging cases and localized variance; they do not automatically prove model defect, as ground-truth observations may contain measurement noise or reflect unmodeled localized hydrological dynamics such as drainage, embankments, or sudden precipitation.)*",
    ]
    return " ".join(parts)


def get_model_error_analysis(
    model_name: str,
    project_root: Path | None = None,
    dataset_id: str = "ifi_v3",
    threshold: float = 3.0,
) -> dict[str, Any] | None:
    """Load real test-set predictions for model_name and dataset_id and compute complete error analysis."""
    if project_root is None:
        project_root = PROJECT_ROOT

    # If the user passed dataset_id as a string in project_root position
    if isinstance(project_root, str) and dataset_id == "ifi_v3":
        dataset_id = project_root
        project_root = PROJECT_ROOT

    from src.config.model_registry import get_model_record
    try:
        rec = get_model_record(dataset_id, model_name)
    except KeyError:
        return None

    if not rec.inference_available or rec.predictions_path is None or not rec.predictions_path.is_file():
        return None

    preds_path = rec.predictions_path
    data_path = project_root / "data" / "processed" / "district_flood_area_regression.csv"

    if not preds_path.is_file() or not data_path.is_file():
        return None

    preds_df = pd.read_csv(preds_path)
    sub = preds_df[preds_df["model"] == model_name].copy()
    if sub.empty:
        return None

    dataset = pd.read_csv(data_path)
    merged = sub.merge(dataset.reset_index(drop=True), left_on="source_row", right_index=True)

    actual = merged["actual"].to_numpy(dtype=float)
    predicted = merged["predicted"].to_numpy(dtype=float)
    metrics = calculate_error_metrics(actual, predicted)

    # Re-verify error and absolute error columns
    error = predicted - actual
    abs_error = np.abs(error)
    count_above_threshold = int(np.sum(abs_error > threshold))

    merged["District"] = merged["Dist_Name"]
    merged["Actual Flooded Area (%)"] = actual
    merged["Predicted Flooded Area (%)"] = predicted
    merged["Error"] = error
    merged["Absolute Error"] = abs_error

    # Top 10 samples with largest absolute prediction error
    top10_df = (
        merged[[
            "District",
            "Actual Flooded Area (%)",
            "Predicted Flooded Area (%)",
            "Error",
            "Absolute Error",
        ]]
        .sort_values("Absolute Error", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )

    top_row = top10_df.iloc[0].to_dict()
    interpretation = generate_error_interpretation(
        model_name=model_name,
        metrics=metrics,
        top_error_row=top_row,
        threshold=threshold,
        count_above_threshold=count_above_threshold,
    )

    return {
        "model": model_name,
        "metrics": metrics,
        "full_data": merged,
        "top10_table": top10_df,
        "count_above_threshold": count_above_threshold,
        "threshold": threshold,
        "interpretation": interpretation,
    }
