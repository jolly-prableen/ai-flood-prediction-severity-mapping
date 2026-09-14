"""Dashboard validation suite (streamlit.testing.v1.AppTest).

Covers every registered dataset x all five selectable models: verifies the unified
10-section layout renders, the model selector always lists all five architectures, each
combination shows its true status, and real IFI numbers are preserved. Also verifies the
protected baseline artifact hash and that View 2 still boots.

Run directly:  python validation/test_dashboard.py
Or via pytest: pytest validation/test_dashboard.py -q
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit.testing.v1 import AppTest

from src.datasets import registry

APP_PATH = PROJECT_ROOT / "app" / "app.py"

HEADINGS = [
    "### 1. Dataset Overview",
    "### 2. Model Comparison",
    "### 3. Dataset Features",
    "### 4. Data Preview",
    "### 5. Model Selection & Status",
    "### 6. Model Performance / Results",
    "### 7. Prediction Visualization",
    "### 8. Actual vs Predicted / Ground Truth",
    "### 9. Error Analysis",
    "### 10. Dataset-specific Visualizations",
    "### 11. Flood / Disaster Analysis",
]

STATUS_TRAINED = "TRAINED + EVALUATED"
STATUS_INCOMPATIBLE = "INCOMPATIBLE WITH CURRENT DATA"
STATUS_TRAINING_REQUIRED = "IMPLEMENTED / TRAINING REQUIRED"


def boot(at: AppTest | None = None) -> AppTest:
    at = at or AppTest.from_file(str(APP_PATH), default_timeout=180)
    at.run()
    failures = [e.message for e in at.exception]
    assert not failures, f"app raised exceptions: {failures}"
    return at


def get_sb(at: AppTest, key: str):
    for sb in at.sidebar.selectbox:
        if sb.key == key:
            return sb
    raise AssertionError(f"sidebar selectbox with key={key!r} not found")


def set_dataset(at: AppTest, cfg: registry.DatasetConfig) -> None:
    get_sb(at, "data_sel").select(cfg.name)
    at.run()


def set_model(at: AppTest, model_name: str) -> None:
    get_sb(at, "model_sel").select(model_name)
    at.run()


def assert_headings(at: AppTest) -> None:
    values = {md.value for md in at.markdown}
    missing = [h for h in HEADINGS if h not in values]
    assert not missing, f"missing section headings: {missing}"


def status_table(at: AppTest):
    for df in at.dataframe:
        cols = list(df.value.columns)
        if set(cols) >= {"Model", "Architecture", "Status", "Inference Available"}:
            return df.value
    raise AssertionError("section-4 model status table not found")


def metrics_frame(at: AppTest):
    """Section-6 trained-model metrics table (prefers the one holding evaluated DL models)."""
    first = None
    for df in at.dataframe:
        if "MAE" in df.value.columns and "RMSE" in df.value.columns:
            if first is None:
                first = df.value
            models = list(df.value["Model"])
            if len(set(models) & set(registry.TRAINED_IFI_MODELS)) >= 2:
                return df.value
    return first


def iter_dataframes(at: AppTest):
    yield from at.dataframe
    for exp in at.expander:
        yield from exp.dataframe


def assert_no_real_metrics(at: AppTest) -> None:
    for df in iter_dataframes(at):
        payload = list(df.value.columns) if hasattr(df.value, "columns") else []
        assert "MAE" not in payload, f"unexpected metrics dataframe with MAE: {payload}"
        assert "RMSE" not in payload, f"unexpected metrics dataframe with RMSE: {payload}"


def check_all_models_visible(at: AppTest) -> None:
    sb = get_sb(at, "model_sel")
    assert list(sb.options) == registry.MODEL_NAMES, (
        f"model selector must list all five models in fixed order; got {list(sb.options)}"
    )


def real_expected_metrics() -> dict[str, dict[str, float]]:
    from src import backend_api as api
    df = api.get_model_metrics()
    out = {}
    for _, row in df.iterrows():
        out[row["Model"]] = {
            "MAE": round(float(row["MAE"]), 4),
            "RMSE": round(float(row["RMSE"]), 4),
            "R2": round(float(row["R2"]), 4),
        }
    return out


def test_all_datasets_render_all_sections() -> None:
    for cfg in registry.available_datasets():
        at = boot()
        set_dataset(at, cfg)
        at.run()
        assert at.sidebar.selectbox, "no sidebar widgets"
        check_all_models_visible(at)
        assert_headings(at)
        failures = [e.message for e in at.exception]
        assert not failures, f"{cfg.key}: app raised: {failures}"
        # Overview shows the real parameter metrics for this dataset.
        labels = [m.label for m in at.metric]
        if cfg.is_image_dataset:
            assert "Image Pairs" in labels and "Trained Models" in labels, (
                f"{cfg.key}: image overview metrics missing: {labels}")
        else:
            assert "Rows" in labels and "Trained Models" in labels, (
                f"{cfg.key}: tabular overview metrics missing: {labels}")


def test_status_of_every_model_on_every_dataset() -> None:
    expected = {
        "ifi_v3": {
            "U-Net + ConvLSTM": STATUS_INCOMPATIBLE,
            "CNN + LSTM": STATUS_TRAINED,
            "CNN + Transformer": STATUS_TRAINED,
            "ResNet + BiLSTM": STATUS_TRAINED,
            "Attention U-Net + LSTM": STATUS_INCOMPATIBLE,
        },
        "ifi_impact": {m: STATUS_INCOMPATIBLE for m in registry.MODEL_NAMES},
        "ifi_flooded_area": {m: STATUS_INCOMPATIBLE for m in registry.MODEL_NAMES},
        "mwbtfreddy": {
            "CNN + LSTM": STATUS_INCOMPATIBLE,
            "CNN + Transformer": STATUS_INCOMPATIBLE,
            "ResNet + BiLSTM": STATUS_INCOMPATIBLE,
            "U-Net + ConvLSTM": STATUS_TRAINING_REQUIRED,
            "Attention U-Net + LSTM": STATUS_TRAINING_REQUIRED,
        },
    }
    for cfg in registry.available_datasets():
        for model_name in registry.MODEL_NAMES:
            at = boot()
            set_dataset(at, cfg)
            set_model(at, model_name)
            at.run()
            failures = [e.message for e in at.exception]
            assert not failures, (
                f"{cfg.key} x {model_name}: app raised: {failures}")
            table = status_table(at)
            row = table[table["Model"] == model_name].iloc[0]
            assert row["Status"] == expected[cfg.key][model_name], (
                f"{cfg.key} x {model_name}: status {row['Status']!r} != "
                f"{expected[cfg.key][model_name]!r}")


def test_ifi_trained_numbers_preserved() -> None:
    expected = real_expected_metrics()
    for model_name in registry.TRAINED_IFI_MODELS:
        at = boot()
        set_dataset(at, registry.M2_BASELINE)
        set_model(at, model_name)
        at.run()
        failures = [e.message for e in at.exception]
        assert not failures, f"{model_name}: app raised: {failures}"
        mf = metrics_frame(at)
        assert mf is not None, f"{model_name}: no metrics dataframe rendered"
        assert set(mf["Model"]).issuperset(registry.TRAINED_IFI_MODELS)
        for trained in registry.TRAINED_IFI_MODELS:
            row = mf[mf["Model"] == trained].iloc[0]
            exp = expected[trained]
            assert float(row["MAE"]) == exp["MAE"], (f"{trained}: MAE {row['MAE']} "
                                                     f"!= {exp['MAE']}")
            assert float(row["RMSE"]) == exp["RMSE"], f"{trained}: RMSE changed"
            assert float(row["R2"]) == exp["R2"], f"{trained}: R2 changed"
        # KPI metrics for the selected model.
        kpi = {m.label: m.value for m in at.metric if m.label in ("MAE", "RMSE", "R²")}
        exp = expected[model_name]
        assert kpi.get("MAE") == f"{exp['MAE']:.4f}", f"KPI MAE = {kpi.get('MAE')}"
        assert kpi.get("RMSE") == f"{exp['RMSE']:.4f}", f"KPI RMSE = {kpi.get('RMSE')}"
        # Real 109-row test prediction table.
        pred_ok = False
        for df in at.dataframe:
            cols = list(df.value.columns)
            if ("Predicted Corrected_%_Flooded_Area" in cols
                    and "Actual Corrected_%_Flooded_Area" in cols):
                assert len(df.value) == 109, (
                    f"{model_name}: prediction table has {len(df.value)} rows, expected 109")
                pred_ok = True
        assert pred_ok, f"{model_name}: real test-set prediction table missing"


def test_ifi_untrained_model_shows_status_no_metrics() -> None:
    for model_name in ("U-Net + ConvLSTM", "Attention U-Net + LSTM"):
        at = boot()
        set_dataset(at, registry.M2_BASELINE)
        set_model(at, model_name)
        at.run()
        failures = [e.message for e in at.exception]
        assert not failures, f"{model_name}: app raised: {failures}"
        table = status_table(at)
        row = table[table["Model"] == model_name].iloc[0]
        assert row["Status"] == STATUS_INCOMPATIBLE
        # The untrained architecture must never receive metrics or a rank, even on IFI.
        cmpt = comparison_table(at)
        crow = cmpt[cmpt["Model"] == model_name].iloc[0]
        assert crow["Rank"] == "—" and crow["MAE ↓"] == "—" and crow["RMSE ↓"] == "—"
        # Section 6 shows a dataset/model-aware status panel instead of dead output.
        markedown = "\n".join(md.value for md in at.markdown)
        assert "Model Performance Status" in markedown
        assert model_name in "\n".join(i.value for i in at.info)


def test_mwbt_and_district_models_no_fake_metrics() -> None:
    for cfg in registry.available_datasets():
        if cfg.key == registry.M2_BASELINE.key:
            continue
        at = boot()
        set_dataset(at, cfg)
        at.run()
        failures = [e.message for e in at.exception]
        assert not failures, f"{cfg.key}: app raised: {failures}"
        assert_no_real_metrics(at)


def comparison_table(at: AppTest):
    """Section-2 model comparison dataframe (always five rows, every dataset)."""
    for df in at.dataframe:
        cols = list(df.value.columns)
        if set(cols) >= {"Model", "Status", "Rank", "Selected"}:
            return df.value
    raise AssertionError("section-2 model comparison table not found")


def test_model_comparison_ifi_real_metrics() -> None:
    expected = real_expected_metrics()
    at = boot()
    set_dataset(at, registry.M2_BASELINE)
    at.run()
    failures = [e.message for e in at.exception]
    assert not failures, f"ifi_v3 comparison: app raised: {failures}"
    tbl = comparison_table(at)
    assert len(tbl) == 5, f"all five models must be listed; got {len(tbl)}"
    ranked = [m for m in tbl["Model"] if tbl[tbl["Model"] == m].iloc[0]["Rank"] != "—"]
    assert set(ranked) == set(registry.TRAINED_IFI_MODELS), f"ranked = {ranked}"
    for model in registry.TRAINED_IFI_MODELS:
        row = tbl[tbl["Model"] == model].iloc[0]
        exp = expected[model]
        assert row["MAE ↓"] == f"{exp['MAE']:.4f}", f"{model}: MAE {row['MAE ↓']}"
        assert row["RMSE ↓"] == f"{exp['RMSE']:.4f}", f"{model}: RMSE changed"
        assert row["R² ↑"] == f"{exp['R2']:.4f}", f"{model}: R2 changed"
    for model in ("U-Net + ConvLSTM", "Attention U-Net + LSTM"):
        row = tbl[tbl["Model"] == model].iloc[0]
        assert row["Rank"] == "—" and row["MAE ↓"] == "—"
    best = [m for m in at.metric if m.label == "Best Model"]
    assert best, "best-model card missing"
    expected_best = min(registry.TRAINED_IFI_MODELS, key=lambda m: expected[m]["MAE"])
    assert best[0].value == expected_best, (
        f"best model = {best[0].value}, expected {expected_best}")
    sel = get_sb(at, "model_sel").value
    assert tbl[tbl["Model"] == sel].iloc[0]["Selected"] == "Yes"


def test_model_comparison_status_only_for_other_datasets() -> None:
    for cfg in registry.available_datasets():
        if cfg.key == registry.M2_BASELINE.key:
            continue
        at = boot()
        set_dataset(at, cfg)
        at.run()
        failures = [e.message for e in at.exception]
        assert not failures, f"{cfg.key}: app raised: {failures}"
        assert_no_real_metrics(at)
        tbl = comparison_table(at)
        assert len(tbl) == 5, f"{cfg.key}: expected 5 rows, got {len(tbl)}"
        statuses = set(tbl["Status"])
        if cfg.is_image_dataset:
            expected_status = {STATUS_TRAINING_REQUIRED, STATUS_INCOMPATIBLE}
        else:
            expected_status = {STATUS_INCOMPATIBLE}
        assert statuses == expected_status, f"{cfg.key}: statuses={statuses}"
        assert (tbl["Rank"] == "—").all(), f"{cfg.key}: untrained models got a rank"
        assert (tbl["MAE ↓"] == "—").all(), f"{cfg.key}: untrained models got metrics"
        info_text = "\n".join(i.value for i in at.info)
        assert "Model comparison will appear after valid model training and evaluation" \
            in info_text, f"{cfg.key}: placeholder message missing"


def test_view2_still_boots() -> None:
    at = boot()
    at.radio[0].set_value("Custom Prediction & Retraining Mode")
    at.run()
    failures = [e.message for e in at.exception]
    assert not failures, f"view 2 raised: {failures}"
    titles = [t.value for t in at.title]
    assert any("API-Driven Model Execution Engine" in t for t in titles), (
        f"view 2 title missing; titles={titles}")


def test_protected_baseline_hash_unchanged() -> None:
    integrity = PROJECT_ROOT / "results" / "baseline_integrity_restore.json"
    assert integrity.is_file(), "protected hash baseline file missing"
    import json
    recorded = json.loads(integrity.read_text(encoding="utf-8"))
    dataset_path = PROJECT_ROOT / recorded["dataset"]
    assert dataset_path.is_file(), f"protected dataset missing: {dataset_path}"
    digest = hashlib.sha256(dataset_path.read_bytes()).hexdigest().upper()
    assert digest == recorded["sha256"].upper(), (
        f"protected {recorded['dataset']} hash changed!\n"
        f"  recorded: {recorded['sha256']}\n  actual:   {digest}")
    for protected in registry.TRAINED_IFI_MODELS:
        ckpt = PROJECT_ROOT / "results" / "models" / \
            registry.LOGICAL_MODEL_DIRS[protected] / "best_model.pt"
        assert ckpt.is_file() and ckpt.stat().st_size > 0, (
            f"protected checkpoint missing or empty: {ckpt}")


ALL_TESTS = [
    test_all_datasets_render_all_sections,
    test_status_of_every_model_on_every_dataset,
    test_ifi_trained_numbers_preserved,
    test_ifi_untrained_model_shows_status_no_metrics,
    test_mwbt_and_district_models_no_fake_metrics,
    test_model_comparison_ifi_real_metrics,
    test_model_comparison_status_only_for_other_datasets,
    test_view2_still_boots,
    test_protected_baseline_hash_unchanged,
]


def main() -> int:
    failures = 0
    for fn in ALL_TESTS:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL  {fn.__name__}: {exc}")
    print("-" * 60)
    print(f"{len(ALL_TESTS) - failures}/{len(ALL_TESTS)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())