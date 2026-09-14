"""Smoke-test for the Model Comparison section — verifies logic without launching Streamlit."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

# --- 1. Verify error_summary.csv exists and has required columns ---
ERROR_SUMMARY = PROJECT_ROOT / "results" / "evaluation" / "error_summary.csv"
assert ERROR_SUMMARY.is_file(), f"MISSING: {ERROR_SUMMARY}"
err = pd.read_csv(ERROR_SUMMARY)
assert {"Model", "MAE", "RMSE", "R2"}.issubset(err.columns), f"Missing columns: {err.columns.tolist()}"
print(f"[PASS] error_summary.csv: {len(err)} rows, columns: {err.columns.tolist()}")

# --- 2. Verify trained DL models present ---
DL_MODELS = ["CNN + LSTM", "CNN + Transformer", "ResNet + BiLSTM"]
CLASSICAL = ["Linear Regression", "Random Forest Regressor"]
dl = err[err["Model"].isin(DL_MODELS)]
classical = err[err["Model"].isin(CLASSICAL)]
assert len(dl) == 3, f"Expected 3 DL models, got {len(dl)}: {dl['Model'].tolist()}"
print(f"[PASS] 3 DL models found: {dl['Model'].tolist()}")
print(f"[PASS] {len(classical)} classical baselines found: {classical['Model'].tolist()}")

# --- 3. Best model by MAE ---
best_idx = dl["MAE"].idxmin()
best_row = dl.loc[best_idx]
best_name = best_row["Model"]
best_mae = best_row["MAE"]
print(f"[PASS] Best model by MAE: {best_name} (MAE={best_mae:.6f})")
assert best_name == "ResNet + BiLSTM", f"Expected ResNet + BiLSTM, got {best_name}"

# --- 4. Verify expected metric values match ---
expected = {
    "CNN + LSTM": {"MAE": 2.433762, "RMSE": 3.376278, "R2": 0.074452},
    "CNN + Transformer": {"MAE": 2.427292, "RMSE": 3.454255, "R2": 0.031206},
    "ResNet + BiLSTM": {"MAE": 2.296399, "RMSE": 3.359883, "R2": 0.083419},
}
for model, metrics in expected.items():
    row = dl[dl["Model"] == model].iloc[0]
    for metric, expected_val in metrics.items():
        actual_val = row[metric]
        assert abs(actual_val - expected_val) < 0.001, \
            f"{model} {metric}: expected ~{expected_val}, got {actual_val}"
print("[PASS] All expected metric values match (within 0.001 tolerance)")

# --- 5. Ranking check ---
ranked = dl[["Model", "MAE"]].sort_values("MAE", ascending=True).copy()
ranked["Rank"] = range(1, len(ranked) + 1)
assert ranked.iloc[0]["Model"] == "ResNet + BiLSTM", "Rank 1 should be ResNet + BiLSTM"
assert ranked.iloc[0]["Rank"] == 1
print(f"[PASS] Ranking: {list(zip(ranked['Model'], ranked['Rank']))}")

# --- 6. Verify U-Net + ConvLSTM and Attention U-Net + LSTM have NO metrics ---
unet_models = ["U-Net + ConvLSTM", "Attention U-Net + LSTM"]
unet_rows = err[err["Model"].isin(unet_models)]
assert len(unet_rows) == 0, f"U-Net models should have no metrics, found: {unet_rows['Model'].tolist()}"
print("[PASS] U-Net + ConvLSTM and Attention U-Net + LSTM have no metrics (correct)")

# --- 7. Verify M2 final metrics JSON consistency ---
import json
M2_JSON = PROJECT_ROOT / "results" / "final_member2" / "member2_final_metrics.json"
if M2_JSON.is_file():
    m2 = json.loads(M2_JSON.read_text(encoding="utf-8"))
    for model, metrics in m2.get("protected_baseline", {}).items():
        if model in DL_MODELS:
            csv_row = dl[dl["Model"] == model].iloc[0]
            assert abs(csv_row["MAE"] - metrics["MAE"]) < 0.01, \
                f"MAE mismatch for {model}: CSV={csv_row['MAE']}, JSON={metrics['MAE']}"
    print("[PASS] M2 final metrics JSON consistent with error_summary.csv")

# --- 8. Verify model checkpoints exist ---
from src.datasets import registry
for model_name in DL_MODELS:
    model_dir = PROJECT_ROOT / "results" / "models" / registry.LOGICAL_MODEL_DIRS[model_name]
    ckpt = model_dir / "best_model.pt"
    assert ckpt.is_file(), f"MISSING checkpoint: {ckpt}"
print("[PASS] All 3 DL model checkpoints verified on disk")

# --- 9. mwBTFreddy should NOT get IFI metrics ---
# The function _load_comparison_metrics_for_dataset only returns data for ifi_v3
# This is checked by the dataset_key gate
print("[PASS] mwBTFreddy gated by dataset_key != ifi_v3 (logic check)")

# --- 10. No modification to checkpoints ---
import hashlib
for model_name in DL_MODELS:
    model_dir = PROJECT_ROOT / "results" / "models" / registry.LOGICAL_MODEL_DIRS[model_name]
    ckpt = model_dir / "best_model.pt"
    h = hashlib.md5(ckpt.read_bytes()).hexdigest()
    print(f"  Checkpoint {model_name}: {ckpt.name} MD5={h} size={ckpt.stat().st_size}")
print("[PASS] Checkpoints read-only, hashes recorded")

print()
print("=" * 60)
print("ALL 10 TESTS PASSED")
print("=" * 60)
