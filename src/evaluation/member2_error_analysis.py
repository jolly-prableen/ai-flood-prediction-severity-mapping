"""Read-only error analysis for the existing Member 2 regression baseline."""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.inference.predictor import predict_uploaded_dataset

FEATURES = ["Population", "Parmanent_Water"]
TARGET = "Corrected_Percent_Flooded_Area"
NEURAL_MODELS = ["CNN + LSTM", "CNN + Transformer", "ResNet + BiLSTM"]
BASELINE_ARTIFACTS = {
    "Linear Regression": "linear_regression/best_model.pkl",
    "Random Forest Regressor": "random_forest_regressor/best_model.pkl",
}
CHECKPOINTS = {
    "CNN + LSTM": "cnn_lstm/best_model.pt",
    "CNN + Transformer": "cnn_transformer/best_model.pt",
    "ResNet + BiLSTM": "resnet_bilstm/best_model.pt",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def metric_values(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    error = predicted - actual
    absolute_error = np.abs(error)
    return {
        "MAE": float(mean_absolute_error(actual, predicted)),
        "MSE": float(mean_squared_error(actual, predicted)),
        "RMSE": float(mean_squared_error(actual, predicted) ** 0.5),
        "R2": float(r2_score(actual, predicted)) if len(np.unique(actual)) > 1 else None,
        "Mean_Error_Bias": float(error.mean()),
        "Median_Absolute_Error": float(np.median(absolute_error)),
        "Maximum_Absolute_Error": float(absolute_error.max()),
    }


def load_test_data(project_root: Path) -> tuple[pd.DataFrame, np.ndarray]:
    frame = pd.read_csv(project_root / "data/processed/district_flood_area_regression.csv")
    split = json.loads((project_root / "data/splits/district_flood_area_split.json").read_text(encoding="utf-8"))
    test_indices = np.asarray(split["test_indices"], dtype=int)
    test = frame.iloc[test_indices].reset_index(drop=False).rename(columns={"index": "source_row"})
    return test, test_indices


def load_predictions(project_root: Path, test: pd.DataFrame) -> dict[str, np.ndarray]:
    predictions: dict[str, np.ndarray] = {}
    inputs = test[FEATURES]
    for model_name in NEURAL_MODELS:
        result = predict_uploaded_dataset(
            model_name,
            inputs,
            checkpoint_path=project_root / "results/models" / CHECKPOINTS[model_name],
            task="regression",
            device="cpu",
        )
        predictions[model_name] = np.asarray(result["prediction"], dtype=float)
    raw_features = inputs.to_numpy(dtype=np.float32)
    for model_name, relative_path in BASELINE_ARTIFACTS.items():
        with (project_root / "results/models" / relative_path).open("rb") as stream:
            model = pickle.load(stream)
        predictions[model_name] = np.asarray(model.predict(raw_features), dtype=float)
    return predictions


def permutation_sensitivity(model_name: str, test: pd.DataFrame,
                             actual: np.ndarray, baseline_prediction: np.ndarray,
                             project_root: Path, repeats: int = 10) -> list[dict]:
    """Measure test MAE increase after shuffling one feature, without fitting."""
    rng = np.random.default_rng(42)
    original = test[FEATURES].copy()
    baseline_mae = mean_absolute_error(actual, baseline_prediction)
    rows = []
    for feature in FEATURES:
        deltas = []
        for _ in range(repeats):
            shuffled = original.copy()
            shuffled[feature] = rng.permutation(shuffled[feature].to_numpy())
            if model_name in NEURAL_MODELS:
                prediction = np.asarray(predict_uploaded_dataset(
                    model_name, shuffled,
                    checkpoint_path=project_root / "results/models" / CHECKPOINTS[model_name],
                    task="regression", device="cpu",
                )["prediction"], dtype=float)
            else:
                with (project_root / "results/models" / BASELINE_ARTIFACTS[model_name]).open("rb") as stream:
                    model = pickle.load(stream)
                prediction = np.asarray(model.predict(shuffled.to_numpy(dtype=np.float32)), dtype=float)
            deltas.append(float(mean_absolute_error(actual, prediction) - baseline_mae))
        rows.append({"Model": model_name, "Feature": feature,
                     "Permutation_MAE_Increase": float(np.mean(deltas)),
                     "Permutation_MAE_Increase_STD": float(np.std(deltas)),
                     "Repeats": repeats})
    return rows


def save_plots(model_name: str, actual: np.ndarray, predicted: np.ndarray, output_dir: Path) -> None:
    safe_name = model_name.lower().replace(" + ", "_").replace(" ", "_")
    residual = predicted - actual
    absolute_error = np.abs(residual)
    figure, axis = plt.subplots(figsize=(6, 5))
    axis.scatter(actual, predicted, alpha=0.75)
    lower, upper = min(actual.min(), predicted.min()), max(actual.max(), predicted.max())
    axis.plot([lower, upper], [lower, upper], "k--")
    axis.set(xlabel="Actual Corrected_Percent_Flooded_Area", ylabel="Predicted", title=f"{model_name}: predicted vs actual")
    figure.tight_layout(); figure.savefig(output_dir / f"{safe_name}_predicted_vs_actual.png", dpi=150); plt.close(figure)

    figure, axis = plt.subplots(figsize=(6, 5))
    axis.scatter(predicted, residual, alpha=0.75)
    axis.axhline(0, color="black", linestyle="--")
    axis.set(xlabel="Predicted", ylabel="Residual (predicted - actual)", title=f"{model_name}: residuals")
    figure.tight_layout(); figure.savefig(output_dir / f"{safe_name}_residuals.png", dpi=150); plt.close(figure)

    figure, axis = plt.subplots(figsize=(6, 4))
    axis.hist(absolute_error, bins=15, edgecolor="black")
    axis.set(xlabel="Absolute error", ylabel="Count", title=f"{model_name}: absolute-error distribution")
    figure.tight_layout(); figure.savefig(output_dir / f"{safe_name}_absolute_error.png", dpi=150); plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--repeats", type=int, default=10)
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    output_dir = project_root / "results/evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)

    test, test_indices = load_test_data(project_root)
    actual = test[TARGET].to_numpy(dtype=float)
    predictions = load_predictions(project_root, test)
    prediction_rows, summary_rows, sensitivity_rows = [], [], []
    for model_name, predicted in predictions.items():
        residual = predicted - actual
        absolute_error = np.abs(residual)
        scores = metric_values(actual, predicted)
        for row_index, (source_row, truth, estimate, error) in enumerate(zip(
                test["source_row"], actual, predicted, residual)):
            prediction_rows.append({"test_position": row_index, "source_row": int(source_row),
                                    "actual": float(truth), "predicted": float(estimate),
                                    "error": float(error), "absolute_error": float(abs(error)),
                                    "model": model_name})
        summary_rows.append({"Model": model_name, **scores,
                             "Error_Actual_Correlation": float(np.corrcoef(actual, absolute_error)[0, 1])
                             if np.std(actual) and np.std(absolute_error) else None,
                             "Overprediction_Count": int((residual > 0).sum()),
                             "Underprediction_Count": int((residual < 0).sum()),
                             "Exact_Match_Count": int((residual == 0).sum())})
        sensitivity_rows.extend(permutation_sensitivity(model_name, test, actual, predicted, project_root, args.repeats))
        save_plots(model_name, actual, predicted, output_dir)

    predictions_frame = pd.DataFrame(prediction_rows)
    summary_frame = pd.DataFrame(summary_rows).sort_values("MAE")
    sensitivity_frame = pd.DataFrame(sensitivity_rows)
    predictions_frame.to_csv(output_dir / "actual_vs_predicted.csv", index=False)
    summary_frame.to_csv(output_dir / "error_summary.csv", index=False)
    sensitivity_frame.to_csv(output_dir / "permutation_sensitivity.csv", index=False)

    largest = predictions_frame.sort_values("absolute_error", ascending=False).head(10)
    actual_bins = pd.qcut(actual, q=3, duplicates="drop")
    bin_rows = []
    for model_name, group in predictions_frame.groupby("model"):
        grouped = group.assign(actual_bin=actual_bins).groupby("actual_bin", observed=True)["absolute_error"].agg(["count", "mean", "median"]).reset_index()
        for row in grouped.to_dict("records"):
            bin_rows.append({"Model": model_name, "Actual_Bin": str(row["actual_bin"]),
                             "Count": int(row["count"]), "Mean_Absolute_Error": float(row["mean"]),
                             "Median_Absolute_Error": float(row["median"])})
    bin_frame = pd.DataFrame(bin_rows)
    bin_frame.to_csv(output_dir / "error_by_actual_range.csv", index=False)

    best = summary_frame.iloc[0]["Model"]
    worst = summary_frame.iloc[-1]["Model"]
    report = {
        "task": "Member 2 baseline district flooded-area regression",
        "test_rows": int(len(test)),
        "test_indices": test_indices.tolist(),
        "features": FEATURES,
        "target": TARGET,
        "models_evaluated": list(predictions),
        "best_model_by_mae": best,
        "worst_model_by_mae": worst,
        "metrics": summary_frame.to_dict("records"),
        "largest_errors": largest.to_dict("records"),
        "error_pattern_analysis": {
            "definition": "error = predicted - actual; positive bias means overprediction",
            "actual_value_error_analysis": bin_frame.to_dict("records"),
            "interpretation": "Correlation and actual-range tables are descriptive only; this two-feature test set does not establish causation.",
        },
        "feature_sensitivity": sensitivity_frame.to_dict("records"),
        "limitations": [
            "Only two predictors are available, so sensitivity is permutation MAE increase, not SHAP.",
            "Permutation sensitivity is measured on the untouched test rows without fitting.",
            "This analysis does not establish causal feature importance.",
            "No model was retrained and no checkpoint was written.",
        ],
        "checkpoint_sha256": {name: sha256(project_root / "results/models" / relative) for name, relative in CHECKPOINTS.items()},
    }
    (output_dir / "member2_error_analysis.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(summary_frame.to_string(index=False))
    print(f"best_model={best}; worst_model={worst}; test_rows={len(test)}")


if __name__ == "__main__":
    main()
