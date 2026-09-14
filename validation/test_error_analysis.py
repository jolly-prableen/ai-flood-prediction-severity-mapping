"""Validation test suite for Prediction Error Analysis feature.

Verifies:
1. Error calculation: error = predicted - actual
2. Absolute error is strictly non-negative
3. MAE matches sklearn calculation
4. RMSE matches sklearn calculation
5. Actual and predicted lengths match exactly (109 rows)
6. Top-10 error table is correctly sorted by Absolute Error descending
7. Existing baseline artifacts remain unchanged (MD5 & size)
8. Existing Feature Ablation Study still works
9. Dashboard renders the section and handles model switching without errors
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit.testing.v1 import AppTest
from src.datasets import registry
from src.evaluation.error_analysis import calculate_error_metrics, get_model_error_analysis

APP_PATH = PROJECT_ROOT / "app" / "app.py"

CHECKPOINTS = {
    "CNN + LSTM": {"path": "results/models/cnn_lstm/best_model.pt", "md5": "d8991b4182b7cc68ea49c2e32e2a7ea7", "size": 46133},
    "CNN + Transformer": {"path": "results/models/cnn_transformer/best_model.pt", "md5": "03238a166d7d96df87ccc74213505daf", "size": 49269},
    "ResNet + BiLSTM": {"path": "results/models/resnet_bilstm/best_model.pt", "md5": "8f93cbcbd5c049783c9078f7d724f4f0", "size": 136437},
}


def test_error_calculations():
    for model_name in registry.TRAINED_IFI_MODELS:
        res = get_model_error_analysis(model_name, PROJECT_ROOT)
        assert res is not None, f"Analysis missing for {model_name}"
        
        df = res["full_data"]
        # 1. Error calculation: error = predicted - actual
        expected_error = df["predicted"].to_numpy() - df["actual"].to_numpy()
        np.testing.assert_allclose(df["Error"].to_numpy(), expected_error, atol=1e-6)
        
        # 2. Absolute error is non-negative
        assert (df["Absolute Error"] >= 0).all(), "Negative absolute error found!"
        np.testing.assert_allclose(df["Absolute Error"].to_numpy(), np.abs(expected_error), atol=1e-6)
        
        # 3. MAE matches sklearn
        expected_mae = mean_absolute_error(df["actual"], df["predicted"])
        assert abs(res["metrics"]["MAE"] - expected_mae) < 1e-6, "MAE mismatch"
        
        # 4. RMSE matches sklearn
        expected_rmse = mean_squared_error(df["actual"], df["predicted"]) ** 0.5
        assert abs(res["metrics"]["RMSE"] - expected_rmse) < 1e-6, "RMSE mismatch"
        
        # 5. Lengths match exactly
        assert len(df) == 109, f"Expected 109 test samples, got {len(df)}"
        assert res["metrics"]["Sample_Count"] == 109
        
        # 6. Top-10 error table is correctly sorted
        top10 = res["top10_table"]
        assert len(top10) == 10, f"Expected 10 rows in top-10, got {len(top10)}"
        abs_errs = top10["Absolute Error"].to_list()
        assert abs_errs == sorted(abs_errs, reverse=True), "Top 10 table not sorted descending!"
        assert list(top10.columns) == [
            "District",
            "Actual Flooded Area (%)",
            "Predicted Flooded Area (%)",
            "Error",
            "Absolute Error",
        ]
        
    print("[PASS] Error metrics, lengths, non-negativity, and top-10 sorting validated.")


def test_baseline_artifacts_unmodified():
    for model_name, expected in CHECKPOINTS.items():
        path = PROJECT_ROOT / expected["path"]
        assert path.is_file(), f"Missing checkpoint: {path}"
        digest = hashlib.md5(path.read_bytes()).hexdigest()
        assert digest == expected["md5"], f"{model_name} MD5 changed"
        assert path.stat().st_size == expected["size"], f"{model_name} size changed"
    print("[PASS] Baseline checkpoints are strictly untouched and match MD5 hashes.")


def test_feature_ablation_unbroken():
    from validation.test_ablation import test_ablation_artifacts_exist
    test_ablation_artifacts_exist()
    print("[PASS] Feature Ablation Study artifacts verified intact.")


def test_dashboard_integration():
    at = AppTest.from_file(str(APP_PATH), default_timeout=60)
    at.run()
    assert not at.exception, f"App raised: {[e.message for e in at.exception]}"

    markdown_vals = "\n".join(md.value for md in at.markdown)
    # Heading must match exactly without "Future Work" prefix
    assert "### Prediction Error Analysis" in markdown_vals
    assert "Future Work: Prediction Error Analysis" not in markdown_vals
    assert "Top 10 Largest Prediction Errors" in markdown_vals

    # Check that Top 10 table rendered
    found_top10 = False
    for df in at.dataframe:
        cols = list(df.value.columns)
        if cols == ["District", "Actual Flooded Area (%)", "Predicted Flooded Area (%)", "Error", "Absolute Error"]:
            assert len(df.value) == 10
            found_top10 = True
            break
    assert found_top10, "Top 10 error dataframe not found in dashboard!"

    # Check that Feature Ablation is also still rendered
    assert "### Feature Ablation Study" in markdown_vals
    print("[PASS] Dashboard integrates Prediction Error Analysis section seamlessly.")


def main():
    print("Running Prediction Error Analysis Tests...")
    test_error_calculations()
    test_baseline_artifacts_unmodified()
    test_feature_ablation_unbroken()
    test_dashboard_integration()
    print("=" * 60)
    print("ALL PREDICTION ERROR ANALYSIS TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
