"""Validation test suite for Flood Risk Visualization feature.

Verifies:
1. Risk categories are generated correctly from actual predictions.
2. Every category belongs strictly to {LOW, MODERATE, HIGH, VERY HIGH}.
3. Category thresholds are deterministic and monotonic.
4. Predictions are not modified and match evaluation artifacts exactly.
5. District identifiers remain aligned between predictions and geometries.
6. Missing geometry is handled safely and explicitly reported (89 mapped, 20 unmapped).
7. No fake predictions are generated for untrained models.
8. Existing baseline checkpoints remain byte-identical (MD5 & size).
9. Dashboard renders the section and responds to model selector.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit.testing.v1 import AppTest
from src.datasets import registry
from src.gis.flood_risk_service import (
    CATEGORY_ORDER,
    assign_risk_category,
    compute_risk_thresholds,
    create_folium_risk_map,
    get_model_flood_risk_data,
)

APP_PATH = PROJECT_ROOT / "app" / "app.py"
ACTUAL_VS_PREDICTED_CSV = PROJECT_ROOT / "results" / "evaluation" / "actual_vs_predicted.csv"

CHECKPOINTS = {
    "CNN + LSTM": {"path": "results/models/cnn_lstm/best_model.pt", "md5": "d8991b4182b7cc68ea49c2e32e2a7ea7", "size": 46133},
    "CNN + Transformer": {"path": "results/models/cnn_transformer/best_model.pt", "md5": "03238a166d7d96df87ccc74213505daf", "size": 49269},
    "ResNet + BiLSTM": {"path": "results/models/resnet_bilstm/best_model.pt", "md5": "8f93cbcbd5c049783c9078f7d724f4f0", "size": 136437},
}

ALLOWED_CATEGORIES = {"LOW", "MODERATE", "HIGH", "VERY HIGH"}


def test_category_generation_and_validity():
    """Test 1 & 2: Risk categories generated correctly and strictly belong to ALLOWED_CATEGORIES."""
    for model_name in registry.TRAINED_IFI_MODELS:
        data = get_model_flood_risk_data(model_name, PROJECT_ROOT)
        assert data is not None, f"Failed to get risk data for {model_name}"

        # Check total districts
        assert data["total_count"] == 109, f"Expected 109 districts, got {data['total_count']}"
        assert len(data["all_districts"]) == 109

        thresholds = data["thresholds"]
        for d in data["all_districts"]:
            cat = d["risk_category"]
            assert cat in ALLOWED_CATEGORIES, f"Invalid category {cat} for district {d['district_name']}"
            
            # Verify category matches threshold definition
            expected_cat = assign_risk_category(d["predicted_flooded_percent"], thresholds)
            assert cat == expected_cat, f"Category mismatch for {d['district_name']}: {cat} != {expected_cat}"

        # Verify summary counts sum to 109
        cat_counts = data["category_counts"]
        assert sum(cat_counts.values()) == 109, f"Category counts sum to {sum(cat_counts.values())}, expected 109"
        for cat in CATEGORY_ORDER:
            assert cat in cat_counts
            assert cat_counts[cat] > 0, f"Category {cat} has 0 count for {model_name}"

    print("[PASS] Test 1 & 2: Risk categories generated correctly and match ALLOWED_CATEGORIES.")


def test_deterministic_thresholds():
    """Test 3: Thresholds are deterministic and strictly monotonic."""
    sample_preds = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    t1 = compute_risk_thresholds(sample_preds)
    t2 = compute_risk_thresholds(sample_preds)
    assert t1 == t2, "Threshold computation is not deterministic"

    for model_name in registry.TRAINED_IFI_MODELS:
        data = get_model_flood_risk_data(model_name, PROJECT_ROOT)
        assert data is not None
        t = data["thresholds"]
        assert t["min"] <= t["q25"] <= t["q50"] <= t["q75"] <= t["max"], (
            f"Monotonicity violated in thresholds for {model_name}: {t}"
        )
    print("[PASS] Test 3: Thresholds are deterministic and monotonic.")


def test_predictions_unmodified():
    """Test 4: Predictions are not modified and match evaluation artifacts."""
    raw_df = pd.read_csv(ACTUAL_VS_PREDICTED_CSV)
    for model_name in registry.TRAINED_IFI_MODELS:
        sub_raw = raw_df[raw_df["model"] == model_name].sort_values("source_row")
        data = get_model_flood_risk_data(model_name, PROJECT_ROOT)
        assert data is not None

        # Check peak district
        raw_max_idx = sub_raw["predicted"].idxmax()
        raw_peak = sub_raw.loc[raw_max_idx]
        assert abs(data["peak_district"]["predicted"] - raw_peak["predicted"]) < 1e-5
        
        # Check all values match exactly
        merged_df = data["all_districts_df"].sort_values("source_row")
        np.testing.assert_allclose(
            merged_df["predicted"].to_numpy(),
            sub_raw["predicted"].to_numpy(),
            rtol=1e-5,
            err_msg=f"Predictions modified for {model_name}",
        )
        np.testing.assert_allclose(
            merged_df["actual"].to_numpy(),
            sub_raw["actual"].to_numpy(),
            rtol=1e-5,
            err_msg=f"Ground truth modified for {model_name}",
        )
    print("[PASS] Test 4: Predictions and actuals are completely unmodified.")


def test_district_alignment_and_missing_geometry():
    """Test 5 & 6: District identifiers remain aligned, missing geometry handled safely."""
    for model_name in registry.TRAINED_IFI_MODELS:
        data = get_model_flood_risk_data(model_name, PROJECT_ROOT)
        assert data is not None

        # Exactly 89 mapped and 20 unmapped
        assert data["mapped_count"] == 89, f"Expected 89 mapped districts, got {data['mapped_count']}"
        assert data["unmapped_count"] == 20, f"Expected 20 unmapped districts, got {data['unmapped_count']}"
        assert len(data["mapped_districts"]) == 89
        assert len(data["unmapped_districts"]) == 20

        # Mapped districts have valid geometry and census code
        for d in data["mapped_districts"]:
            assert d["has_geometry"] is True
            assert d["censuscode"] is not None
            assert int(d["censuscode"]) > 0
            assert d["district_name"]

        # Unmapped districts handled explicitly without error
        for d in data["unmapped_districts"]:
            assert d["has_geometry"] is False
            assert d["district_id"].startswith("ROW-")
            assert d["district_name"]

        # Folium map builds cleanly
        folium_map = create_folium_risk_map(data)
        assert folium_map is not None
        assert len(data["geojson"]["features"]) == 89

    print("[PASS] Test 5 & 6: District alignment and missing geometry handled safely.")


def test_no_fake_predictions_for_untrained_models():
    """Test 7: No fake predictions are generated for untrained models."""
    untrained_models = [m for m in registry.MODEL_NAMES if m not in registry.TRAINED_IFI_MODELS]
    for model_name in untrained_models:
        data = get_model_flood_risk_data(model_name, PROJECT_ROOT)
        assert data is None, f"Expected None for untrained model {model_name}, got {data}"
    print("[PASS] Test 7: No fake predictions generated for untrained models.")


def test_baseline_checkpoints_unmodified():
    """Test 8: Existing baseline checkpoints remain byte-identical."""
    for model_name, expected in CHECKPOINTS.items():
        path = PROJECT_ROOT / expected["path"]
        assert path.is_file(), f"Missing checkpoint: {path}"
        digest = hashlib.md5(path.read_bytes()).hexdigest()
        assert digest == expected["md5"], f"{model_name} MD5 changed: {digest} != {expected['md5']}"
        assert path.stat().st_size == expected["size"], f"{model_name} size changed"
    print("[PASS] Test 8: Baseline checkpoints are strictly untouched and match MD5 hashes.")


def test_dashboard_renders_flood_risk_visualization():
    """Test 9: Streamlit dashboard renders the Flood Risk Visualization section."""
    at = AppTest.from_file(str(APP_PATH), default_timeout=60)
    at.run()
    assert not at.exception, f"App raised exceptions: {[e.message for e in at.exception]}"

    markdown_vals = "\n".join(md.value for md in at.markdown)
    # Exact title must be present
    assert "### Flood Risk Visualization" in markdown_vals
    # Must NOT say Future Work in section title
    assert "Future Work: Flood Risk Visualization" not in markdown_vals
    # Required methodology note present
    assert "Risk categories are visualization-oriented categories derived from the model's predicted flooded-area percentage" in markdown_vals

    # Metric cards present
    labels = [m.label for m in at.metric]
    assert "Low Risk Districts" in labels
    assert "Moderate Risk Districts" in labels
    assert "High Risk Districts" in labels
    assert "Very High Risk Districts" in labels
    assert "Highest predicted flooded-area district" in labels
    assert "Highest predicted flooded-area percentage" in labels

    # Test switching model to untrained architecture
    for sb in at.sidebar.selectbox:
        if sb.key == "model_sel":
            sb.select("U-Net + ConvLSTM")
            break
    at.run()
    assert not at.exception
    info_vals = "\n".join(inf.value for inf in at.info)
    assert "Risk visualization unavailable: no valid evaluated predictions are available for this model." in info_vals

    print("[PASS] Test 9: Dashboard renders section and updates cleanly on model change.")


if __name__ == "__main__":
    print("Running Flood Risk Visualization validation test suite...")
    test_category_generation_and_validity()
    test_deterministic_thresholds()
    test_predictions_unmodified()
    test_district_alignment_and_missing_geometry()
    test_no_fake_predictions_for_untrained_models()
    test_baseline_checkpoints_unmodified()
    test_dashboard_renders_flood_risk_visualization()
    print("\nAll 9 Flood Risk Visualization tests PASSED successfully!")
