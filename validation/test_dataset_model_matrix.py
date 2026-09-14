"""Comprehensive test suite for Dataset x Model compatibility matrix and dynamic switching.

Validates:
1. Every dataset x model combination in the centralized registries.
2. Correct dataset is loaded and statistics reflect real data without hardcoding.
3. Correct model status is assigned according to the standard vocabulary.
4. No wrong checkpoints or predictions are loaded (strict isolation).
5. Unavailable combinations display informative unavailability notices (no fallback, no fake numbers).
6. Mode A Prediction Risk Map renders when predictions exist.
7. Mode B Dataset GIS Overview / Descriptive District Map renders when descriptive geography is available.
8. Dynamic switching sequence:
   Dataset A + Model A -> Dataset A + Model B -> Dataset B + Model B -> Dataset B + Model C -> Dataset A + Model C
   and verifies that results update dynamically without stale data.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit.testing.v1 import AppTest
from src.datasets import registry
from src.config.dataset_registry import (
    DATASET_REGISTRY,
    get_dataset,
    load_dataset_data,
    list_datasets,
)
from src.config.model_registry import (
    ALL_MODELS,
    get_model_record,
    get_dataset_model_table,
    STATUS_TRAINED_EVALUATED,
    STATUS_INCOMPATIBLE,
    STATUS_TRAINING_REQUIRED,
)
from src.gis.flood_risk_service import (
    get_model_flood_risk_data,
    get_descriptive_gis_data,
)
from src.evaluation.error_analysis import get_model_error_analysis

APP_PATH = PROJECT_ROOT / "app" / "app.py"


def test_registry_completeness():
    """Verify that all 4 registered datasets and all 5 models exist in the registry."""
    assert len(DATASET_REGISTRY) == 4
    expected_datasets = {"ifi_v3", "ifi_impact", "ifi_flooded_area", "mwbtfreddy"}
    assert set(DATASET_REGISTRY.keys()) == expected_datasets

    for ds_id in expected_datasets:
        table = get_dataset_model_table(ds_id)
        assert len(table) == 5
        models_in_table = [m.model_name for m in table]
        assert models_in_table == ALL_MODELS


def test_model_status_matrix_correctness():
    """Verify that every combination receives the exact scientifically correct status."""
    expected = {
        "ifi_v3": {
            "CNN + LSTM": STATUS_TRAINED_EVALUATED,
            "CNN + Transformer": STATUS_TRAINED_EVALUATED,
            "ResNet + BiLSTM": STATUS_TRAINED_EVALUATED,
            "U-Net + ConvLSTM": STATUS_INCOMPATIBLE,
            "Attention U-Net + LSTM": STATUS_INCOMPATIBLE,
        },
        "ifi_impact": {m: STATUS_INCOMPATIBLE for m in ALL_MODELS},
        "ifi_flooded_area": {m: STATUS_INCOMPATIBLE for m in ALL_MODELS},
        "mwbtfreddy": {
            "CNN + LSTM": STATUS_INCOMPATIBLE,
            "CNN + Transformer": STATUS_INCOMPATIBLE,
            "ResNet + BiLSTM": STATUS_INCOMPATIBLE,
            "U-Net + ConvLSTM": STATUS_TRAINING_REQUIRED,
            "Attention U-Net + LSTM": STATUS_TRAINING_REQUIRED,
        },
    }

    for ds_id, model_dict in expected.items():
        for model_name, exp_status in model_dict.items():
            rec = get_model_record(ds_id, model_name)
            assert rec.status == exp_status, f"{ds_id} x {model_name}: expected {exp_status}, got {rec.status}"


def test_prediction_artifact_isolation():
    """Ensure no predictions or checkpoints are leaked to incompatible or untrained models."""
    for ds_id in ["ifi_impact", "ifi_flooded_area", "mwbtfreddy"]:
        for model_name in ALL_MODELS:
            rec = get_model_record(ds_id, model_name)
            assert rec.has_predictions is False
            assert rec.checkpoint_path is None
            assert rec.metrics is None

            risk_data = get_model_flood_risk_data(model_name, PROJECT_ROOT, dataset_id=ds_id)
            assert risk_data is None, f"Leak: risk data returned for {ds_id} x {model_name}"

            err_data = get_model_error_analysis(model_name, PROJECT_ROOT, dataset_id=ds_id)
            assert err_data is None, f"Leak: error analysis returned for {ds_id} x {model_name}"

    for model_name in ["U-Net + ConvLSTM", "Attention U-Net + LSTM"]:
        rec = get_model_record("ifi_v3", model_name)
        assert rec.has_predictions is False
        assert rec.metrics is None
        assert get_model_flood_risk_data(model_name, PROJECT_ROOT, dataset_id="ifi_v3") is None
        assert get_model_error_analysis(model_name, PROJECT_ROOT, dataset_id="ifi_v3") is None


def test_descriptive_gis_for_non_predictive_datasets():
    """Mode B GIS overview works for datasets where district geography exists."""
    impact_gis = get_descriptive_gis_data("ifi_impact")
    assert impact_gis is not None
    assert impact_gis["mapped_count"] == 595
    assert "Human_fatality" in impact_gis["available_variables"]
    assert "Population" in impact_gis["available_variables"]
    assert len(impact_gis["geojson"]["features"]) == 595

    flooded_gis = get_descriptive_gis_data("ifi_flooded_area")
    assert flooded_gis is not None
    assert flooded_gis["mapped_count"] == 595
    assert "Percent_Flooded_Area" in flooded_gis["available_variables"]

    # Image dataset (Malawi) has no Indian district shapefile GIS
    assert get_descriptive_gis_data("mwbtfreddy") is None


def test_dynamic_switching_order_apptest():
    """Verify switching order in Streamlit:

    Dataset A + Model A (ifi_v3 + CNN + LSTM)
    -> Dataset A + Model B (ifi_v3 + CNN + Transformer)
    -> Dataset B + Model B (ifi_impact + CNN + Transformer)
    -> Dataset B + Model C (ifi_impact + ResNet + BiLSTM)
    -> Dataset A + Model C (ifi_v3 + ResNet + BiLSTM)
    """
    at = AppTest.from_file(str(APP_PATH), default_timeout=120)
    at.run()
    assert not at.exception, f"Boot raised: {[e.message for e in at.exception]}"

    def select_dataset(name: str):
        for sb in at.sidebar.selectbox:
            if sb.key == "data_sel":
                sb.select(name)
                break
        at.run()
        assert not at.exception, f"Select dataset {name} raised: {[e.message for e in at.exception]}"

    def select_model(name: str):
        for sb in at.sidebar.selectbox:
            if sb.key == "model_sel":
                sb.select(name)
                break
        at.run()
        assert not at.exception, f"Select model {name} raised: {[e.message for e in at.exception]}"

    # Step 1: ifi_v3 + CNN + LSTM
    select_dataset(registry.M2_BASELINE.name)
    select_model("CNN + LSTM")
    markdown_1 = "\n".join(md.value for md in at.markdown)
    assert "**Selected model status:** `TRAINED + EVALUATED`" in markdown_1
    assert "Error Summary Metrics — CNN + LSTM" in markdown_1

    # Step 2: ifi_v3 + CNN + Transformer
    select_model("CNN + Transformer")
    markdown_2 = "\n".join(md.value for md in at.markdown)
    assert "**Selected model status:** `TRAINED + EVALUATED`" in markdown_2
    assert "Error Summary Metrics — CNN + Transformer" in markdown_2
    assert "Error Summary Metrics — CNN + LSTM" not in markdown_2

    # Step 3: ifi_impact + CNN + Transformer
    select_dataset(registry.IFI_IMPACT.name)
    markdown_3 = "\n".join(md.value for md in at.markdown)
    info_3 = "\n".join(inf.value for inf in at.info)
    assert "**Selected model status:** `INCOMPATIBLE WITH CURRENT DATA`" in markdown_3
    assert f"Prediction results are not available for {registry.IFI_IMPACT.name} + CNN + Transformer" in info_3
    assert "Dataset GIS Overview (Descriptive District Map)" in info_3

    # Step 4: ifi_impact + ResNet + BiLSTM
    select_model("ResNet + BiLSTM")
    markdown_4 = "\n".join(md.value for md in at.markdown)
    info_4 = "\n".join(inf.value for inf in at.info)
    assert "**Selected model status:** `INCOMPATIBLE WITH CURRENT DATA`" in markdown_4
    assert f"Prediction results are not available for {registry.IFI_IMPACT.name} + ResNet + BiLSTM" in info_4

    # Step 5: ifi_v3 + ResNet + BiLSTM
    select_dataset(registry.M2_BASELINE.name)
    markdown_5 = "\n".join(md.value for md in at.markdown)
    assert "**Selected model status:** `TRAINED + EVALUATED`" in markdown_5
    assert "Error Summary Metrics — ResNet + BiLSTM" in markdown_5
    assert "District Risk Map (ResNet + BiLSTM)" in markdown_5


def test_all_20_combinations_matrix_explicit():
    """Verify all 4 datasets x 5 models = 20 combinations.

    Validates:
    - Dataset registry exists and source file is on disk
    - Model registry exists and contract is defined
    - Compatibility status is explicit (one of the standard statuses)
    - Artifact lookup is deterministic
    - Wrong artifact cannot be loaded (strict isolation)
    - Dataset overview loads real data without error
    - Model status works with descriptive reason
    - Appropriate visualization state is returned
    - Cross-dataset isolation: (ds_A, model_X) != (ds_B, model_X)
    - Cross-model isolation: (ds_A, model_X) != (ds_A, model_Y)
    - No exception occurs across all 20 pairs
    """
    from src.gis import mwbtfreddy_service as mws

    all_datasets = ["ifi_v3", "ifi_impact", "ifi_flooded_area", "mwbtfreddy"]
    assert len(all_datasets) == 4
    assert len(ALL_MODELS) == 5

    valid_statuses = {
        STATUS_TRAINED_EVALUATED,
        STATUS_INCOMPATIBLE,
        STATUS_TRAINING_REQUIRED,
    }

    combo_count = 0

    for ds_id in all_datasets:
        # Verify dataset registry
        ds_rec = get_dataset(ds_id)
        assert ds_rec.exists, f"Dataset source path missing on disk: {ds_rec.source_path}"
        assert ds_rec.dataset_id == ds_id

        # Dataset overview data verification
        if ds_rec.is_image_dataset:
            img_details = registry.load_image_dataset(registry.MWBTFREDDY)
            assert img_details.image_pairs == 10
            assert img_details.annotation_count == 1274
        else:
            df = load_dataset_data(ds_id)
            assert df is not None and not df.empty
            assert len(df) > 0

        for model_name in ALL_MODELS:
            combo_count += 1

            # 1. Model record exists
            rec = get_model_record(ds_id, model_name)
            assert rec is not None
            assert rec.dataset_id == ds_id
            assert rec.model_name == model_name

            # 2. Compatibility is explicit
            assert rec.status in valid_statuses, f"Invalid status: {rec.status} for {ds_id} x {model_name}"
            assert len(rec.status_reason) > 0

            # 3. Artifact lookup is deterministic
            rec_again = get_model_record(ds_id, model_name)
            assert rec == rec_again, f"Non-deterministic record for {ds_id} x {model_name}"

            # 4. Wrong artifact cannot be loaded / strict artifact isolation
            if rec.status == STATUS_TRAINED_EVALUATED:
                assert rec.has_checkpoint is True
                assert rec.has_predictions is True
                assert rec.metrics is not None
                assert "MAE" in rec.metrics
                # Ensure risk data and error data exist only for trained ifi_v3 models
                risk_data = get_model_flood_risk_data(model_name, PROJECT_ROOT, dataset_id=ds_id)
                assert risk_data is not None
                assert risk_data["model_name"] == model_name
                err_data = get_model_error_analysis(model_name, PROJECT_ROOT, dataset_id=ds_id)
                assert err_data is not None
                assert err_data["model"] == model_name
            else:
                assert rec.has_predictions is False
                assert rec.checkpoint_path is None
                assert rec.metrics is None
                assert get_model_flood_risk_data(model_name, PROJECT_ROOT, dataset_id=ds_id) is None
                assert get_model_error_analysis(model_name, PROJECT_ROOT, dataset_id=ds_id) is None

            # 5. Appropriate visualization state
            if ds_id == "ifi_v3" and rec.status == STATUS_TRAINED_EVALUATED:
                rd = get_model_flood_risk_data(model_name, PROJECT_ROOT, dataset_id=ds_id)
                assert rd["mapped_count"] > 0
                assert len(rd["geojson"]["features"]) > 0
            elif ds_id in ("ifi_impact", "ifi_flooded_area"):
                desc_gis = get_descriptive_gis_data(ds_id)
                assert desc_gis is not None
                assert desc_gis["mapped_count"] > 0
            elif ds_id == "mwbtfreddy":
                fmap = mws.create_folium_malawi_map()
                assert fmap is not None

    assert combo_count == 20, f"Expected exactly 20 combinations, evaluated {combo_count}"

    # Isolation: dataset A + model X != dataset B + model X
    for model_name in ALL_MODELS:
        rec_ifi = get_model_record("ifi_v3", model_name)
        rec_impact = get_model_record("ifi_impact", model_name)
        rec_flooded = get_model_record("ifi_flooded_area", model_name)
        rec_mwbt = get_model_record("mwbtfreddy", model_name)

        assert rec_ifi != rec_impact
        assert rec_ifi != rec_flooded
        assert rec_ifi != rec_mwbt
        assert rec_impact.dataset_id != rec_flooded.dataset_id

    # Isolation: dataset A + model X != dataset A + model Y
    for ds_id in all_datasets:
        for i, m1 in enumerate(ALL_MODELS):
            for j, m2 in enumerate(ALL_MODELS):
                if i != j:
                    r1 = get_model_record(ds_id, m1)
                    r2 = get_model_record(ds_id, m2)
                    assert r1.model_name != r2.model_name
                    assert r1 != r2

