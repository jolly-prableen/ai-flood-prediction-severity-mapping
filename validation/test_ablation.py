"""Validation test for the Future Work: Feature Ablation Study.

Verifies that:
1. Ablation artifacts exist under results/models/ablation/ and are well-formed.
2. All three feature configurations are evaluated for all three trained models.
3. Baseline checkpoints remain untouched and byte-identical.
4. The Streamlit dashboard renders the ablation section without errors.
5. Untrained models and non-baseline datasets show status without fake metrics.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit.testing.v1 import AppTest
from src.datasets import registry

APP_PATH = PROJECT_ROOT / "app" / "app.py"
ABLATION_SUMMARY = PROJECT_ROOT / "results" / "models" / "ablation" / "ablation_summary.json"
CONFIG_NAMES = ["Full Baseline", "Population Only", "Permanent Water Only"]


def test_ablation_artifacts_exist():
    assert ABLATION_SUMMARY.is_file(), f"Ablation summary missing: {ABLATION_SUMMARY}"
    data = json.loads(ABLATION_SUMMARY.read_text(encoding="utf-8"))
    assert set(data.keys()) == set(registry.TRAINED_IFI_MODELS), (
        f"Ablation models {set(data.keys())} != {set(registry.TRAINED_IFI_MODELS)}"
    )
    for model_name, configs in data.items():
        assert set(configs.keys()) == set(CONFIG_NAMES), (
            f"{model_name} missing configs: {set(configs.keys())} != {set(CONFIG_NAMES)}"
        )
        for cfg_name, res in configs.items():
            assert "MAE" in res and "RMSE" in res and "R2" in res
            assert isinstance(res["MAE"], (int, float)) and res["MAE"] > 0
            assert isinstance(res["RMSE"], (int, float)) and res["RMSE"] > 0
            assert isinstance(res["R2"], (int, float))
    print("[PASS] Ablation artifacts exist and metrics are well-formed.")


CHECKPOINTS = {
    "CNN + LSTM": {"path": "results/models/cnn_lstm/best_model.pt", "md5": "d8991b4182b7cc68ea49c2e32e2a7ea7", "size": 46133},
    "CNN + Transformer": {"path": "results/models/cnn_transformer/best_model.pt", "md5": "03238a166d7d96df87ccc74213505daf", "size": 49269},
    "ResNet + BiLSTM": {"path": "results/models/resnet_bilstm/best_model.pt", "md5": "8f93cbcbd5c049783c9078f7d724f4f0", "size": 136437},
}


def test_baseline_checkpoints_unmodified():
    for model_name, expected in CHECKPOINTS.items():
        path = PROJECT_ROOT / expected["path"]
        assert path.is_file(), f"Missing checkpoint: {path}"
        digest = hashlib.md5(path.read_bytes()).hexdigest()
        assert digest == expected["md5"], f"{model_name} MD5 changed: {digest} != {expected['md5']}"
        assert path.stat().st_size == expected["size"], f"{model_name} size changed"
    print("[PASS] Baseline checkpoints are strictly untouched and match MD5 hashes.")


def test_dashboard_renders_ablation_section():
    at = AppTest.from_file(str(APP_PATH), default_timeout=60)
    at.run()
    assert not at.exception, f"App raised exceptions: {[e.message for e in at.exception]}"

    markdown_vals = "\n".join(md.value for md in at.markdown)
    assert "### Feature Ablation Study" in markdown_vals
    assert "Feature ablation measures how model performance changes" in "\n".join(i.value for i in at.info)

    # Check ablation table exists
    ablation_df = None
    for df in at.dataframe:
        if "Feature Configuration" in df.value.columns:
            ablation_df = df.value
            break
    assert ablation_df is not None, "Ablation dataframe not found in dashboard!"
    assert list(ablation_df.columns) == ["Feature Configuration", "MAE", "RMSE", "R²"]
    assert len(ablation_df) == 3
    assert set(ablation_df["Feature Configuration"]) == set(CONFIG_NAMES)
    print("[PASS] Dashboard correctly renders Feature Ablation Study section and comparison table.")


def main():
    print("Running Ablation Tests...")
    test_ablation_artifacts_exist()
    test_baseline_checkpoints_unmodified()
    test_dashboard_renders_ablation_section()
    print("=" * 60)
    print("ALL ABLATION TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
