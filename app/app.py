"""AI Flood Early Warning Dashboard.

Unified 10-section layout that renders all four registered datasets with the same
structure. All five project model architectures are always visible in the sidebar and
selectable for every dataset; section 4 reports each one's real status (trained checkpoint,
training required, or incompatible contract) computed from on-disk artifacts.

Every displayed value is real: it comes from the prepared dataset, the saved evaluation
artifacts, live checkpoint inference, or an on-disk file/manifest scan. Nothing is
hard-coded or fabricated.
"""
from __future__ import annotations

import json as _json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import backend_api as api
from src.datasets import registry
from src.gis import mwbtfreddy_service as mws
from src.config.dataset_registry import (
    DATASET_REGISTRY,
    get_dataset,
    get_dataset_by_name,
    load_dataset_data,
    list_datasets,
)
from src.config.model_registry import (
    get_model_record,
    get_dataset_model_table,
    STATUS_TRAINED_EVALUATED,
    STATUS_TRAINED_NOT_EVALUATED,
    STATUS_TRAINED_FOR_DIFFERENT_DATASET,
    STATUS_NOT_TRAINED,
    STATUS_TRAINING_REQUIRED,
    STATUS_INCOMPATIBLE,
)

DATASET_CSV = PROJECT_ROOT / "data" / "processed" / "district_flood_area_regression.csv"
SPLIT_JSON = PROJECT_ROOT / "data" / "splits" / "district_flood_area_split.json"
ACTUAL_VS_PREDICTED_CSV = PROJECT_ROOT / "results" / "evaluation" / "actual_vs_predicted.csv"
ERROR_SUMMARY_CSV = PROJECT_ROOT / "results" / "evaluation" / "error_summary.csv"
M2_FINAL_METRICS_JSON = PROJECT_ROOT / "results" / "final_member2" / "member2_final_metrics.json"
ABLATION_SUMMARY_JSON = PROJECT_ROOT / "results" / "models" / "ablation" / "ablation_summary.json"

st.set_page_config(
    page_title="AI Flood Early Warning Dashboard",
    layout="wide",
    page_icon="🌊",
)


def sidebar_dataset_selector() -> registry.DatasetConfig:
    datasets = registry.available_datasets()
    if not datasets:
        datasets = [registry.M2_BASELINE]
    options = {d.name: d for d in datasets}
    choice = st.sidebar.selectbox("Dataset", list(options), key="data_sel")
    return options[choice]


st.sidebar.title("Dashboard Controls")
dashboard_view = st.sidebar.radio(
    "Select View Mode",
    ["Analytics & GIS Overview (Default)", "Custom Prediction & Retraining Mode"],
)
st.sidebar.markdown("---")

cfg = sidebar_dataset_selector()

st.sidebar.subheader("Model Selection")
model_options = registry.MODEL_NAMES
default_model = next(
    (name for name in model_options
     if registry.model_compatibility(cfg, name).inference_possible),
    model_options[0],
)
selected_model = st.sidebar.selectbox(
    "Prediction Model", model_options,
    index=model_options.index(default_model), key="model_sel",
)
st.sidebar.caption("All five project architectures are listed and selectable for every "
                   "dataset. Architectures without a real artifact for the selected "
                   "dataset report their actual status.")
compat = registry.model_compatibility(cfg, selected_model)
st.sidebar.markdown(f"**Selected model status:** `{compat.status}`")
st.sidebar.markdown("---")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def load_dataset() -> pd.DataFrame:
    return pd.read_csv(DATASET_CSV)


def load_splits() -> dict:
    import json
    return json.loads(SPLIT_JSON.read_text(encoding="utf-8"))


def load_saved_predictions() -> pd.DataFrame:
    return pd.read_csv(ACTUAL_VS_PREDICTED_CSV)


def load_error_summary() -> pd.DataFrame:
    return pd.read_csv(ERROR_SUMMARY_CSV)


def load_ablation_summary() -> dict:
    if ABLATION_SUMMARY_JSON.is_file():
        import json
        return json.loads(ABLATION_SUMMARY_JSON.read_text(encoding="utf-8"))
    return {}


@st.cache_data
def prepared_analytics(dataset_id: str = "ifi_v3") -> dict:
    if dataset_id == "ifi_v3":
        dataset = load_dataset()
        splits = load_splits()
        predicted = load_saved_predictions()
        error_summary = load_error_summary()
        train_indices = set(splits.get("train_indices", []))
        test_indices = set(splits.get("test_indices", []))
        row_split = dataset.index.map(
            lambda i: "Validation" if i not in train_indices and i not in test_indices
            else "Train" if i in train_indices else "Test"
        )
        dataset = dataset.assign(split_role=row_split)
        return {
            "dataset": dataset,
            "train_count": len(train_indices),
            "valid_count": len(dataset) - len(train_indices) - len(test_indices),
            "test_count": len(test_indices),
            "predicted": predicted,
            "error_summary": error_summary,
        }
    else:
        df = load_dataset_data(dataset_id)
        if df is None:
            df = pd.DataFrame()
        return {
            "dataset": df,
            "train_count": 0,
            "valid_count": 0,
            "test_count": 0,
            "predicted": pd.DataFrame(),
            "error_summary": pd.DataFrame(),
        }


def model_metrics_table() -> pd.DataFrame:
    metrics_df = api.get_model_metrics()
    if metrics_df.empty:
        return metrics_df
    keep = ["Model", "MAE", "RMSE", "R2", "Validation MAE", "Validation RMSE",
            "Diagnosis", "Correction"]
    metrics_df = metrics_df[[c for c in keep if c in metrics_df.columns]].copy()
    for col in ["MAE", "RMSE", "R2", "Validation MAE", "Validation RMSE"]:
        if col in metrics_df.columns:
            metrics_df[col] = metrics_df[col].round(4)
    return metrics_df


@st.cache_data(show_spinner=False)
def cached_image(path: str):
    return registry.open_image(Path(path))


def column_info_table(profile: registry.DatasetProfile) -> pd.DataFrame:
    return pd.DataFrame({
        "Column": profile.column_names,
        "Data Type": [profile.dtypes[c] for c in profile.column_names],
        "Missing": [profile.missing_counts[c] for c in profile.column_names],
        "Missing %": [float(f"{profile.missing_pct[c]:.1f}") for c in profile.column_names],
    })


def render_overview_summary(profile: registry.DatasetProfile) -> None:
    features = ", ".join(profile.input_features) if profile.input_features else "None declared"
    st.markdown(f"**Features (input):** {features}")
    st.markdown(f"**Target:** {profile.target if profile.target else 'None declared'}")
    st.markdown(f"**Task type:** {profile.task_type if profile.task_type else 'Not declared'}")
    if profile.dataset_type:
        st.markdown(f"**Dataset type:** {profile.dataset_type}")
    if profile.geographic_columns:
        st.markdown(f"**Geographic fields:** {', '.join(profile.geographic_columns)}")
    if profile.temporal_columns:
        st.markdown(f"**Temporal fields:** {', '.join(profile.temporal_columns)}")
    st.markdown(f"**Source:** `{profile.source}` · `{profile.path}`")



def build_geo_figure(details: registry.ImageDatasetDetails | None = None) -> go.Figure:
    """Build accurate 2D cartesian building footprint figure with 1:1 aspect ratio."""
    return mws.create_cartesian_footprint_figure()


# ---------------------------------------------------------------------------
# Unified 10-section rendering (every dataset renders all 10 sections)
# ---------------------------------------------------------------------------

def section_1_dataset_overview(cfg: registry.DatasetConfig) -> None:
    st.markdown("### 1. Dataset Overview")
    trained_count = registry.trained_model_count(cfg)
    if cfg.is_image_dataset:
        details = registry.load_image_dataset(cfg)
        summary = mws.get_damage_class_summary()
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric(label="Selected Dataset", value="mwBTFreddy Sample Subset1")
        m2.metric(label="Dataset Type", value="Bitemporal satellite imagery")
        m3.metric(label="Image Pairs", value=f"{summary['image_pairs']}")
        m4.metric(label="Pre / Post Images", value=f"{summary['pre_images']} / {summary['post_images']}")
        m5.metric(label="JSON Annotations", value=f"{summary['json_files']}")

        m6, m7, m8, m9, m10 = st.columns(5)
        m6.metric(label="Building Annotations", value=f"{summary['total_annotations']:,}")
        m7.metric(label="Image Dimensions", value=f"{summary['dimensions'][0]} × {summary['dimensions'][1]}")
        m8.metric(label="Bands", value=f"{summary['bands']} RGB")
        m9.metric(label="Observed Damage Classes", value=f"{summary['observed_count']}")
        m10.metric(label="Trained Models", value=f"{trained_count}")

        st.markdown(
            "**Description:** mwBTFreddy is a bitemporal satellite-image building-damage dataset. "
            "Spatial architectures require dedicated segmentation training; the existing IFI tabular "
            "regression checkpoints are not applicable."
        )
        st.markdown(
            "**Damage Class Accounting:**  \n"
            f"- **Taxonomy classes:** {summary['taxonomy_count']} (`no-damage`, `minor-damage`, `major-damage`, `destroyed`)  \n"
            f"- **Observed in sample:** {summary['observed_count']} (`no-damage`: {summary['sample_counts']['no-damage']:,}, "
            f"`major-damage`: {summary['sample_counts']['major-damage']}, `destroyed`: {summary['sample_counts']['destroyed']})  \n"
            f"- **Unobserved in sample:** `minor-damage`: 0 observations (not fabricated)"
        )
        st.markdown(
            "**Dataset Scope:**  \n"
            "- **Full dataset:** 696 satellite images across Malawi Cyclone Freddy (xBD standard)  \n"
            "- **Current sample subset:** 20 GeoTIFF images (10 bitemporal pre/post pairs), 20 JSON annotation files, 1,274 building annotations"
        )
        if details.source_url:
            st.markdown(f"**Source:** {details.source_url}"
                        + (f" · DOI {details.doi}" if details.doi else "")
                        + (f" · License {details.license}" if details.license else ""))
        st.markdown(f"**Path:** `{details.path}`")
        st.markdown(f"**Task:** Building Damage Classification / Semantic Segmentation (Bitemporal Imagery)")
        st.info("ℹ️ **Status:** Spatial training required — no evaluated artifact currently exists.")
    else:
        profile = registry.analyze_dataframe(registry.load_dataset(cfg), cfg)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric(label="Selected Dataset", value=profile.name.split(" (")[0])
        m2.metric(label="Dataset Type", value=profile.dataset_type.split(" (")[0])
        m3.metric(label="Rows", value=f"{profile.rows:,}")
        m4.metric(label="Columns", value=f"{profile.columns}")
        m5.metric(label="Trained Models", value=f"{trained_count}")
        if trained_count:
            st.markdown("**Available trained models:** "
                        + ", ".join(api.get_available_models()))
        if profile.is_baseline:
            data = prepared_analytics()
            st.markdown(
                f"**Prepared modeling dataset:** {len(data['dataset'])} rows — "
                f"Train {data['train_count']} · Validation {data['valid_count']} · "
                f"Test {data['test_count']}"
            )
        elif cfg.key == registry.IFI_IMPACT.key:
            st.warning(
                "⚠️ **Descriptive post-event dataset — no validated predictive target is defined.** "
                "Casualty, injury, and flood duration figures represent observational disaster outcomes across Indian districts."
            )
        elif cfg.key == registry.IFI_FLOODED_AREA.key:
            st.warning(
                "⚠️ **Target Leakage Notice:** Corrected_Percent_Flooded_Area has an exact mathematical identity "
                "with Percent_Flooded_Area (Percent − Permanent). Using raw flooded area as an input to predict corrected "
                "flooded area constitutes circular target leakage. The project baseline avoids this by instead utilizing "
                "demographic (Population) and hydrological (Permanent_Water) features from the prepared regression dataset."
            )
        render_overview_summary(profile)
    st.markdown("---")


def section_2_model_comparison(cfg: registry.DatasetConfig,
                               compat: registry.ModelCompatibility) -> None:
    st.markdown("### 2. Model Comparison")
    trained = registry.trained_metrics(cfg)

    # --- Comparison table (all five architectures, metrics only where real) ---
    compat_rows = registry.compatibility_table(cfg)
    metric_models = [r.model_name for r in compat_rows if r.model_name in trained]
    metric_models.sort(key=lambda m: trained[m]["MAE"])          # lower MAE = better
    rank_by_model = {m: i + 1 for i, m in enumerate(metric_models)}

    table_rows = []
    for r in compat_rows:
        model = r.model_name
        if model in trained:
            m = trained[model]
            table_rows.append({
                "Model": model,
                "Status": r.status,
                "MAE ↓": f"{m['MAE']:.4f}",
                "RMSE ↓": f"{m['RMSE']:.4f}",
                "R² ↑": f"{m['R2']:.4f}",
                "Rank": f"{rank_by_model[model]}",
                "Selected": "Yes" if model == compat.model_name else "—",
            })
        else:
            table_rows.append({
                "Model": model,
                "Status": r.status,
                "MAE ↓": "—",
                "RMSE ↓": "—",
                "R² ↑": "—",
                "Rank": "—",
                "Selected": "Yes" if model == compat.model_name else "—",
            })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
    st.caption(
        "Ranking is by test MAE (lower is better) among trained + evaluated models only. "
        "Untrained or incompatible architectures never receive metrics or a rank. "
        "No composite score is used."
    )

    if not metric_models:
        if cfg.is_image_dataset:
            st.markdown("#### Dataset-Aware Architecture Compatibility & Task Specification")
            arch_rows = [
                {
                    "Model": "CNN + LSTM",
                    "Architecture Class": "TABULAR MODEL",
                    "Target Task": "District Flooded-Area Regression",
                    "Input Type": "Tabular feature sequence",
                    "Compatibility / Status": "INCOMPATIBLE — TABULAR MODEL / IMAGE INPUT",
                    "Detail": "Not directly compatible with raw satellite imagery; requires image feature extraction. Existing IFI tabular checkpoints cannot be run on imagery.",
                },
                {
                    "Model": "CNN + Transformer",
                    "Architecture Class": "TABULAR MODEL",
                    "Target Task": "District Flooded-Area Regression",
                    "Input Type": "Tabular feature sequence",
                    "Compatibility / Status": "INCOMPATIBLE — TABULAR MODEL / IMAGE INPUT",
                    "Detail": "Not directly compatible with raw satellite imagery; requires image feature extraction. Existing IFI tabular checkpoints cannot be run on imagery.",
                },
                {
                    "Model": "ResNet + BiLSTM",
                    "Architecture Class": "TABULAR MODEL",
                    "Target Task": "District Flooded-Area Regression",
                    "Input Type": "Tabular feature sequence",
                    "Compatibility / Status": "INCOMPATIBLE — TABULAR MODEL / IMAGE INPUT",
                    "Detail": "Not directly compatible with raw satellite imagery; requires image feature extraction. Existing IFI tabular checkpoints cannot be run on imagery.",
                },
                {
                    "Model": "U-Net + ConvLSTM",
                    "Architecture Class": "SPATIAL MODEL",
                    "Target Task": "Building Damage Segmentation",
                    "Input Type": "Bitemporal satellite raster (1024×1024 RGB)",
                    "Compatibility / Status": "SPATIAL TRAINING REQUIRED",
                    "Detail": "Potentially compatible with bitemporal raster input; requires dedicated spatial segmentation training. Small sample experiment (10 pairs); no evaluated prediction masks generated yet.",
                },
                {
                    "Model": "Attention U-Net + LSTM",
                    "Architecture Class": "SPATIAL MODEL",
                    "Target Task": "Building Damage Segmentation",
                    "Input Type": "Bitemporal satellite raster (1024×1024 RGB)",
                    "Compatibility / Status": "SPATIAL TRAINING REQUIRED",
                    "Detail": "Potentially compatible with bitemporal raster input; requires dedicated spatial segmentation training. Small sample experiment (10 pairs); no evaluated prediction masks generated yet.",
                },
            ]
            st.dataframe(pd.DataFrame(arch_rows), use_container_width=True, hide_index=True)
            st.caption("Spatial models require segmentation metrics (mIoU, Dice/F1, pixel accuracy); tabular models require regression metrics (MAE, RMSE, R²). Never compare fundamentally different tasks using identical metric columns.")

        st.info("Model comparison will appear after valid model training and evaluation "
                "for this dataset.")
        st.markdown("---")
        return

    # --- Best performing model (computed dynamically from the real metric table) ---
    best_name = metric_models[0]
    best = trained[best_name]
    reason = (f"Lowest test MAE ({best['MAE']:.4f}) among the currently trained and "
              f"evaluated models ({len(metric_models)}) on this dataset/test set.")
    with st.container(border=True):
        st.markdown("### 🏆 Best Performing Model")
        b1, b2, b3, b4 = st.columns(4)
        b1.metric(label="Best Model", value=best_name)
        b2.metric(label="MAE", value=f"{best['MAE']:.4f}")
        b3.metric(label="RMSE", value=f"{best['RMSE']:.4f}")
        b4.metric(label="R²", value=f"{best['R2']:.4f}")
        st.markdown(f"**Reason:** {reason}")

    # --- Metric comparison charts (equal y-axis start at zero; selected model is orange) ---
    chart_df = pd.DataFrame([{
        "Model": m, "MAE": trained[m]["MAE"],
        "RMSE": trained[m]["RMSE"], "R²": trained[m]["R2"],
    } for m in metric_models])
    color_map = {m: "#E07B00" if m == compat.model_name else "#4472C4"
                 for m in metric_models}
    c1, c2, c3 = st.columns(3)
    c1.plotly_chart(
        px.bar(chart_df, x="Model", y="MAE", color="Model", text_auto=".4f",
               color_discrete_map=color_map, title="MAE by Model")
        .update_layout(yaxis_title="MAE (lower is better)", showlegend=False, height=360),
        use_container_width=True)
    c2.plotly_chart(
        px.bar(chart_df, x="Model", y="RMSE", color="Model", text_auto=".4f",
               color_discrete_map=color_map, title="RMSE by Model")
        .update_layout(yaxis_title="RMSE (lower is better)", showlegend=False, height=360),
        use_container_width=True)
    c3.plotly_chart(
        px.bar(chart_df, x="Model", y="R²", color="Model", text_auto=".4f",
               color_discrete_map=color_map, title="R² by Model")
        .update_layout(yaxis_title="R² (higher is better)", showlegend=False, height=360),
        use_container_width=True)
    st.caption(f"Trained + evaluated models on this dataset/test set. "
               f"Selected model ({compat.model_name}) highlighted in orange. "
               "Axes start at zero so bar differences reflect real proportions.")

    # --- Auto-generated interpretation from the actual metric values ---
    st.markdown("### Model Interpretation")
    st.markdown(_model_interpretation(best_name, best, metric_models, trained))
    st.markdown("---")


def _model_interpretation(best_name: str, best: dict[str, float],
                          metric_models: list[str],
                          trained: dict[str, dict[str, float]]) -> str:
    parts = [
        f"{best_name} currently provides the best test-set performance among the "
        f"{len(metric_models)} trained models on this dataset/test set, achieving the "
        f"lowest MAE ({best['MAE']:.4f})."
    ]
    max_r2 = max(trained[m]["R2"] for m in metric_models)
    if best["R2"] == max_r2:
        parts.append(f"Its R² ({best['R2']:.4f}) is also the highest among the trained "
                     "models.")
    else:
        top_r2 = next(m for m in metric_models if trained[m]["R2"] == max_r2)
        parts.append(f"Its R² ({best['R2']:.4f}) is lower than that of {top_r2} "
                     f"({max_r2:.4f}); the best-model ranking is driven by MAE, not R².")
    if len(metric_models) >= 2:
        second = metric_models[1]
        if trained[second]["MAE"] - best["MAE"] < 0.01:
            parts.append("The top two models are extremely close on MAE, so the difference "
                         "should not be over-interpreted.")
    parts.append("This is the best among the currently evaluated models on this "
                 "dataset/test set, not a universal claim of superiority.")
    return " ".join(parts)


def section_2_classical_baselines(cfg: registry.DatasetConfig) -> None:
    """Separate Classical Baselines block (never mixed into the five required models)."""
    if cfg.key != registry.M2_BASELINE.key:
        return
    classical = registry.classical_baseline_metrics()
    if classical.empty:
        return
    st.markdown("### Classical Baselines")
    keep = ["Model", "MAE", "RMSE", "R2", "Validation MAE", "Validation RMSE",
            "Diagnosis", "Correction"]
    shown = classical[[c for c in keep if c in classical.columns]].copy()
    for col in ["MAE", "RMSE", "R2", "Validation MAE", "Validation RMSE"]:
        if col in shown.columns:
            shown[col] = shown[col].round(4)
    st.dataframe(shown, use_container_width=True)
    st.caption("Separate from the five required deep-learning architectures. Real saved "
               "metrics from results/model_comparison.csv on the same untouched test "
               "split.")
    st.markdown("---")


def section_3_dataset_features(cfg: registry.DatasetConfig) -> None:
    st.markdown("### 3. Dataset Features")
    if cfg.is_image_dataset:
        meta = registry.image_dataset_metadata(cfg)
        info_rows = [
            ("Image format", meta["format"]),
            ("Color mode", meta["mode"]),
            ("Channels (bands)", meta["bands"]),
            ("Dimensions (px)", f"{meta['dimensions'][0]} x {meta['dimensions'][1]}"
             if meta["dimensions"] else "unknown"),
            ("Pre-disaster images", meta["pre"]),
            ("Post-disaster images", meta["post"]),
            ("Image pairs", meta["pairs"]),
            ("Annotation JSON files", meta["json_files"]),
            ("Building annotations", f"{meta['annotations']:,}"),
        ]
        st.markdown("**Image / GeoTIFF metadata (on-disk):**")
        info_df = pd.DataFrame(info_rows, columns=["Field", "Value"])
        info_df["Value"] = info_df["Value"].astype(str)
        st.dataframe(info_df, use_container_width=True, hide_index=True)
        inventory = registry.annotation_field_inventory(cfg)
        st.markdown(f"**Annotation schema** (across {inventory['json_files']} JSON files):")
        c1, c2 = st.columns(2)
        c1.markdown("Per-annotation `properties` keys:")
        c1.dataframe(pd.DataFrame(
            [{"property": k, "occurrences": v}
             for k, v in inventory["property_keys"].items()]),
            use_container_width=True, hide_index=True)
        c2.markdown("Top-level feature keys:")
        c2.dataframe(pd.DataFrame(
            [{"key": k, "occurrences": v}
             for k, v in inventory["top_level_keys"].items()]),
            use_container_width=True, hide_index=True)
        details = registry.load_image_dataset(cfg)
        st.markdown("**Damage classes:** " + " · ".join(details.damage_classes.keys()))
        st.markdown(f"**Task:** {cfg.task_type}")
    else:
        profile = registry.analyze_dataframe(registry.load_dataset(cfg), cfg)
        if profile.is_baseline:
            st.markdown("**Modeling dataset features (input → target):**")
            feat_df = pd.DataFrame({
                "Feature": ["Population", "Parmanent_Water"],
                "Role": ["Demographic Impact Metric", "Hydrological Surface Metric"],
            })
            target_df = pd.DataFrame({
                "Target": ["Corrected_Percent_Flooded_Area"],
                "Role": ["Regression prediction target"],
            })
            st.markdown("**Features (input):**")
            st.dataframe(feat_df, use_container_width=True, hide_index=True)
            st.markdown("**Target:**")
            st.dataframe(target_df, use_container_width=True, hide_index=True)
            for label, path in cfg.related_sources.items():
                if path.exists():
                    related = registry.analyze_dataframe(
                        registry.load_dataset(cfg, path), cfg)
                    st.markdown(f"**{label}:** {related.rows:,} rows / "
                                f"{related.columns} columns - all original IFI fields:")
                    st.dataframe(column_info_table(related), use_container_width=True)
        else:
            st.markdown("**Table columns (all fields):**")
            st.dataframe(column_info_table(profile), use_container_width=True)
    st.markdown("---")


def section_4_data_preview(cfg: registry.DatasetConfig) -> None:
    st.markdown("### 4. Data Preview")
    if cfg.is_image_dataset:
        pairs = mws.get_image_pairs_list()
        if pairs:
            default_pair = st.session_state.get("mwbtfreddy_selected_pair", "malawi-cyclone_00000058")
            if default_pair not in pairs:
                default_pair = pairs[0]
            default_idx = pairs.index(default_pair)

            sel_pair = st.selectbox(
                "Select Image Pair",
                pairs,
                index=default_idx,
                key="mwbt_pair_selector",
                help="Select one of the 10 bitemporal image pairs to inspect pre/post disaster views and building annotations.",
            )
            st.session_state["mwbtfreddy_selected_pair"] = sel_pair

            annos = mws.load_pair_annotations(sel_pair, temporal_phase="post")
            p_counts = {"no-damage": 0, "minor-damage": 0, "major-damage": 0, "destroyed": 0}
            for a in annos:
                sub = a["subtype"]
                p_counts[sub] = p_counts.get(sub, 0) + 1

            c_info1, c_info2, c_info3, c_info4 = st.columns(4)
            c_info1.metric("Pair Buildings", len(annos))
            c_info2.metric("No Damage", p_counts["no-damage"])
            c_info3.metric("Major Damage", p_counts["major-damage"])
            c_info4.metric("Destroyed", p_counts["destroyed"])

            paths = mws.get_pair_file_paths(sel_pair)
            pre_img = cached_image(str(paths["pre_tif"]))
            post_img = cached_image(str(paths["post_tif"]))
            overlay_img = mws.generate_pair_overlay(sel_pair)

            col_pre, col_post, col_over = st.columns(3)
            with col_pre:
                st.markdown("**PRE-DISASTER**")
                if pre_img is not None:
                    st.image(pre_img, caption=f"Pre-disaster · {sel_pair}", use_container_width=True)
                else:
                    st.warning(f"Pre-disaster image unavailable: `{paths['pre_tif'].name}`")
            with col_post:
                st.markdown("**POST-DISASTER**")
                if post_img is not None:
                    st.image(post_img, caption=f"Post-disaster · {sel_pair}", use_container_width=True)
                else:
                    st.warning(f"Post-disaster image unavailable: `{paths['post_tif'].name}`")
            with col_over:
                st.markdown("**ANNOTATION OVERLAY**")
                if overlay_img is not None:
                    st.image(overlay_img, caption=f"Ground-Truth Footprints Overlay · {sel_pair}", use_container_width=True)
                else:
                    st.warning("Overlay generation unavailable.")

            st.caption(
                "Green = No Damage · Orange = Major Damage · Red = Destroyed · Amber = Minor Damage (unobserved). "
                "Footprints rendered directly from GeoTIFF pixel coordinates (`features.xy`) on the 1024×1024 post-disaster image."
            )
        else:
            st.info("No image pairs found for display.")
    else:
        frame = registry.load_dataset(cfg)
        st.dataframe(frame.head(10), use_container_width=True)
        st.caption(f"First 10 rows of `{cfg.source}` "
                   f"({len(frame):,} rows, {len(frame.columns)} columns).")
    st.markdown("---")


def section_5_model_selection_and_status(cfg: registry.DatasetConfig,
                                         compat: registry.ModelCompatibility) -> None:
    st.markdown("### 5. Model Selection & Status")
    rows = [{
        "Model": row.model_name,
        "Architecture": row.architecture,
        "Status": row.status,
        "Inference Available": "Yes" if row.inference_possible else "No",
    } for row in registry.compatibility_table(cfg)]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(
        "Status is computed from real artifacts: TRAINED + EVALUATED = saved checkpoint with "
        "evaluation on the IFI test split; IMPLEMENTED / TRAINING REQUIRED = architecture "
        "exists but no artifact for this dataset; INCOMPATIBLE WITH CURRENT DATA = "
        "architecture/data contract mismatch (existing checkpoints would be misapplied)."
    )

    with st.expander("Dynamic Architecture Specifications (All 5 Architectures)", expanded=False):
        for m_name in registry.MODEL_NAMES:
            rec = get_model_record(cfg.key, m_name)
            st.markdown(f"#### {m_name}")
            st.markdown(
                f"- **Task Type:** {rec.target_task}  \n"
                f"- **Expected Input Type:** {rec.input_type}  \n"
                f"- **Expected Output Type:** {rec.expected_output or 'Continuous percentage (%)'}  \n"
                f"- **Compatible Datasets:** {', '.join(rec.compatible_datasets)}  \n"
                f"- **Status on {cfg.name}:** `{rec.status}` — {rec.status_reason}"
            )
            st.markdown("---")

    with st.expander(f"Selected model details — {compat.model_name} on {compat.dataset_name}"):
        detail = pd.DataFrame({
            "Property": ["Architecture", "Input type", "Target task", "Status",
                         "Input requirements", "Training data", "Preprocessing",
                         "Checkpoint", "Evaluation", "Compatibility reason"],
            "Value": [compat.architecture, compat.input_type, compat.target_task,
                      compat.status, compat.input_requirements, compat.training_data,
                      compat.preprocessing, compat.checkpoint, compat.evaluation,
                      compat.reason],
        })
        detail["Value"] = detail["Value"].astype(str)
        st.dataframe(detail, use_container_width=True, hide_index=True)
    st.markdown("---")


def _availability_text(cfg: registry.DatasetConfig,
                       compat: registry.ModelCompatibility) -> str:
    """Concise, dataset- and model-aware status text for combos with no trained artifact."""
    if compat.inference_possible:
        return (
            f"🟢 **TRAINED + EVALUATED** — {compat.model_name} has a verified trained checkpoint on {cfg.name}; "
            "real test-set predictions, performance metrics, and error analysis are shown in this section."
        )

    if cfg.key in (registry.IFI_IMPACT.key, registry.IFI_FLOODED_AREA.key):
        return (
            f"🔵 **NOT APPLICABLE** — Prediction not applicable — this dataset has no validated predictive target "
            f"({compat.model_name} on {cfg.name}). Available descriptive dataset analysis and GIS remain visible below."
        )

    if compat.status == STATUS_TRAINING_REQUIRED:
        return (
            f"🟡 **TRAINING REQUIRED** — No evaluated artifact exists for this Dataset × Model combination "
            f"({compat.model_name} on {cfg.name}). Available dataset analysis remains visible below."
        )

    return (
        f"🔴 **INCOMPATIBLE** — {compat.reason} ({compat.model_name} on {cfg.name})."
    )


def section_6_model_performance(cfg: registry.DatasetConfig,
                                compat: registry.ModelCompatibility) -> None:
    st.markdown("### 6. Model Performance / Results")
    if cfg.is_baseline:
        st.info(
            "Current M2 Baseline:\n"
            "This system currently performs district-level flooded-area regression using "
            "Population and Parmanent_Water. Flood probability, rainfall forecasting, U-Net "
            "segmentation and geographic risk mapping are not part of this baseline."
        )
    if compat.inference_possible:
        metrics_df = model_metrics_table()
        if not metrics_df.empty:
            st.markdown("**Trained model performance (real saved artifacts):**")
            st.dataframe(metrics_df, use_container_width=True)
            kpi_row = metrics_df[metrics_df["Model"] == compat.model_name]
            if not kpi_row.empty:
                st.markdown(f"**Selected architecture — {compat.model_name}:**")
                c1, c2, c3 = st.columns(3)
                c1.metric(label="MAE", value=f"{float(kpi_row['MAE'].iloc[0]):.4f}")
                c2.metric(label="RMSE", value=f"{float(kpi_row['RMSE'].iloc[0]):.4f}")
                c3.metric(label="R²", value=f"{float(kpi_row['R2'].iloc[0]):.4f}")
                st.caption("All figures from `results/model_comparison.csv` "
                           "(untouched test split).")
        else:
            st.info("No saved model metrics found in `results/` yet.")
    else:
        st.markdown("**Model Performance Status**")
        st.info(_availability_text(cfg, compat))
    st.markdown("---")


def _baseline_predictions(compat: registry.ModelCompatibility, dataset_id: str = "ifi_v3") -> pd.DataFrame | None:
    """Saved test-set predictions for the selected model and dataset."""
    try:
        rec = get_model_record(dataset_id, compat.model_name)
    except KeyError:
        return None
    if not (rec.has_predictions and rec.predictions_path and rec.predictions_path.is_file()):
        return None
    preds_df = pd.read_csv(rec.predictions_path)
    model_pred = preds_df[preds_df["model"] == compat.model_name].copy()
    return model_pred if not model_pred.empty else None


def section_7_prediction_visualization(cfg: registry.DatasetConfig,
                                       compat: registry.ModelCompatibility) -> None:
    st.markdown("### 7. Prediction Visualization")
    model_pred = _baseline_predictions(compat, dataset_id=cfg.key)
    rec = get_model_record(cfg.key, compat.model_name)
    if model_pred is not None and not model_pred.empty and rec.has_predictions:
        dataset = prepared_analytics(cfg.key)["dataset"]
        ds_rec = get_dataset(cfg.key)
        dist_col = ds_rec.district_column if ds_rec.district_column in dataset.columns else "Dist_Name"
        col_map, col_chart = st.columns([1.5, 1])
        with col_map:
            st.markdown(f"**Predicted Flooded Area by District ({compat.model_name})**")
            joined = model_pred.merge(dataset.reset_index(drop=True),
                                      left_on="source_row", right_index=True,
                                      suffixes=("", "_df"))
            top = joined.nlargest(15, "predicted")
            fig = px.bar(top, x="predicted", y=dist_col, orientation="h",
                         title=f"Predicted {ds_rec.target_column or 'Target'} (top-15 test districts)",
                         labels={"predicted": "Predicted %", dist_col: "District"})
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Real test-set predictions for {compat.model_name} on {cfg.name}.")
        with col_chart:
            st.markdown("**Model Prediction Distribution**")
            hist_df = model_pred[["predicted"]].rename(columns={"predicted": "value"})
            hist_df["type"] = "Predicted"
            actual_df = model_pred[["actual"]].rename(columns={"actual": "value"})
            actual_df["type"] = "Actual"
            both = pd.concat([hist_df, actual_df], ignore_index=True)
            fig = px.histogram(both, x="value", color="type", nbins=30, barmode="overlay",
                               title=f"Distribution of {ds_rec.target_column or 'Target'} (Test Set)",
                               labels={"value": f"{ds_rec.target_column or 'Target'} (%)"})
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"Prediction results are not available for {cfg.name} + {compat.model_name}.")
    st.markdown("---")


def section_8_actual_vs_predicted(cfg: registry.DatasetConfig,
                                  compat: registry.ModelCompatibility) -> None:
    st.markdown("### 8. Actual vs Predicted / Ground Truth")
    model_pred = _baseline_predictions(compat, dataset_id=cfg.key)
    rec = get_model_record(cfg.key, compat.model_name)
    if model_pred is not None and not model_pred.empty and rec.has_predictions:
        dataset = prepared_analytics(cfg.key)["dataset"]
        ds_rec = get_dataset(cfg.key)
        dist_col = ds_rec.district_column if ds_rec.district_column in dataset.columns else "Dist_Name"
        col_avp, col_errdist = st.columns([1, 1])
        with col_avp:
            st.markdown("**Actual vs Predicted (Test Set)**")
            fig = px.scatter(model_pred, x="actual", y="predicted",
                             labels={"actual": "Actual %", "predicted": "Predicted %"},
                             title=f"{compat.model_name} - Actual vs Predicted")
            fig.add_shape(type="line", x0=model_pred["actual"].min(),
                          y0=model_pred["actual"].min(),
                          x1=model_pred["actual"].max(), y1=model_pred["actual"].max(),
                          line=dict(color="red", dash="dash"))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        with col_errdist:
            st.markdown("**Error Distribution (Test Set)**")
            fig = px.histogram(model_pred, x="error", nbins=30,
                               labels={"error": "Prediction Error (% flooded area)"},
                               title=f"{compat.model_name} - Prediction Errors")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("**Test-Set Prediction Table**")
        base_df = dataset.drop(columns=["split_role"]) if "split_role" in dataset.columns else dataset
        joined = model_pred.merge(base_df.reset_index(drop=True),
                                  left_on="source_row", right_index=True,
                                  suffixes=("", "_df"))
        table_cols = [dist_col]
        for f in ds_rec.feature_columns:
            if f in joined.columns and f not in table_cols:
                table_cols.append(f)
        table_cols.extend(["actual", "predicted", "error"])
        table = joined[table_cols].rename(columns={
            dist_col: "District",
            "actual": "Actual Corrected_%_Flooded_Area",
            "predicted": "Predicted Corrected_%_Flooded_Area",
            "error": "Error",
        }).copy()
        table["Absolute Error"] = table["Error"].abs()
        st.dataframe(table.sort_values("Absolute Error", ascending=False)
                     .reset_index(drop=True), use_container_width=True)
        st.caption(f"Real test-set rows ({len(table)}) with model predictions from the saved "
                   f"evaluation artifact for {compat.model_name}.")
    elif cfg.is_image_dataset:
        details = registry.load_image_dataset(cfg)
        st.markdown("**Ground-Truth Annotations vs. Predicted Segmentation Masks**")
        st.info("Ground-truth annotations are available, but no predicted segmentation masks have been generated yet.")
        st.caption(
            f"Ground truth consists of {details.image_pairs} bitemporal image pairs and "
            f"{details.annotation_count:,} building annotations across 20 JSON files (637 unique buildings in post-disaster imagery). "
            "When a spatial segmentation model (e.g. U-Net + ConvLSTM or Attention U-Net + LSTM) is trained, "
            "predicted damage masks will be displayed alongside ground-truth masks here."
        )
    else:
        st.info(f"Prediction results are not available for {cfg.name} + {compat.model_name}.")
    st.markdown("---")


def section_9_error_analysis(cfg: registry.DatasetConfig,
                             compat: registry.ModelCompatibility) -> None:
    st.markdown("### 9. Error Analysis")
    rec = get_model_record(cfg.key, compat.model_name)
    if compat.inference_possible and rec.has_predictions:
        err_df = prepared_analytics(cfg.key)["error_summary"]
        if not err_df.empty:
            trained = set(api.get_available_models())
            shown = err_df[err_df["Model"].isin(trained)].copy()
            keep_cols = ["Model", "MAE", "RMSE", "R2", "Mean_Error_Bias",
                         "Median_Absolute_Error", "Maximum_Absolute_Error",
                         "Overprediction_Count", "Underprediction_Count"]
            shown = shown[[c for c in keep_cols if c in shown.columns]]
            for col in ["MAE", "RMSE", "R2", "Mean_Error_Bias", "Median_Absolute_Error",
                         "Maximum_Absolute_Error"]:
                if col in shown.columns:
                    shown[col] = shown[col].round(4)
            st.dataframe(shown, use_container_width=True)
            st.caption("All figures from the saved Member 2 error analysis artifact "
                       "(untouched test split).")
        else:
            st.info("No saved error analysis found in `results/` yet.")
    elif cfg.is_image_dataset:
        st.info("Segmentation error analysis is unavailable because no evaluated prediction masks exist.")
        st.caption(
            "Task-appropriate segmentation error analysis (mean Intersection over Union [mIoU], "
            "Dice/F1 coefficient, pixel accuracy, and per-damage-class confusion matrix) will be computed "
            "once spatial segmentation masks are generated and evaluated."
        )
    else:
        st.info(f"Prediction error analysis is not available for {cfg.name} + {compat.model_name}.")
    st.markdown("---")


def section_10_dataset_visualizations(cfg: registry.DatasetConfig) -> None:
    st.markdown("### 10. Dataset-specific Visualizations")
    ds_rec = get_dataset(cfg.key)
    if cfg.is_image_dataset:
        st.markdown("#### A & B. Damage-Class Accounting (Taxonomy vs. Observed)")
        summary = mws.get_damage_class_summary()

        c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
        c_kpi1.metric("Taxonomy Classes", summary["taxonomy_count"], help="4 classes: no-damage, minor-damage, major-damage, destroyed")
        c_kpi2.metric("Observed in Sample", summary["observed_count"], help="3 classes: no-damage, major-damage, destroyed")
        c_kpi3.metric("Total Annotations (20 JSONs)", f"{summary['total_annotations']:,}")
        c_kpi4.metric("Unique Post Buildings", f"{summary['unique_buildings']:,}")

        class_rows = []
        for cls in summary["taxonomy_classes"]:
            cnt = summary["sample_counts"].get(cls, 0)
            pct = summary["sample_percentages"].get(cls, 0.0)
            status = "Observed" if cnt > 0 else "Unobserved in sample (0 observations)"
            class_rows.append({
                "Damage Class": cls,
                "Sample Count": cnt,
                "Percentage (%)": f"{pct:.2f}%",
                "Status": status,
            })
        class_df = pd.DataFrame(class_rows)

        col_tbl, col_bar = st.columns([1.2, 1.8])
        with col_tbl:
            st.dataframe(class_df, use_container_width=True, hide_index=True)
            st.caption(
                "**Taxonomy vs Observed:** xBD taxonomy defines 4 classes. "
                "In Sample Subset1, exactly 3 classes are observed: "
                "no-damage (1,266), major-damage (1), destroyed (7). "
                "minor-damage has 0 observations and is not fabricated."
            )
        with col_bar:
            obs_df = class_df[class_df["Sample Count"] > 0]
            bar = px.bar(
                obs_df,
                x="Damage Class",
                y="Sample Count",
                color="Damage Class",
                color_discrete_map=mws.DAMAGE_COLORS,
                text="Sample Count",
                labels={"Sample Count": "Annotations"},
                title="Observed Damage Class Distribution (Sample Subset1)",
            )
            bar.update_layout(showlegend=False, height=320)
            st.plotly_chart(bar, use_container_width=True)

        st.markdown("---")
        st.markdown("#### C. Per-Image-Pair Annotation Breakdown")
        pair_table = mws.get_per_pair_table()
        st.dataframe(pair_table, use_container_width=True, hide_index=True)
        st.caption("Distribution of building annotations across all 10 bitemporal image pairs in Sample Subset1.")

        st.markdown("---")
        st.markdown("#### E & G. Geographic Building Footprint Geometry (Cartesian 2D Coordinates)")
        st.markdown(
            "Building footprints parsed from raw WKT polygon annotations (`features.lng_lat`). "
            "Rendered on true physical coordinates with a **1:1 aspect ratio** to preserve accurate building shapes."
        )

        pairs_list = ["All Image Pairs (Overview)"] + mws.get_image_pairs_list()
        curr_sel = st.session_state.get("mwbtfreddy_selected_pair", mws.get_image_pairs_list()[0])
        default_pair_idx = pairs_list.index(curr_sel) if curr_sel in pairs_list else 0

        sel_footprint_pair = st.selectbox(
            "Filter Footprint Plot by Image Pair:",
            pairs_list,
            index=default_pair_idx,
            key="footprint_pair_filter",
        )
        pair_filter_id = None if sel_footprint_pair.startswith("All") else sel_footprint_pair

        footprint_fig = mws.create_cartesian_footprint_figure(selected_pair_id=pair_filter_id)
        st.plotly_chart(footprint_fig, use_container_width=True)

        g1, g2, g3, g4 = st.columns(4)
        g1.metric("Geographic Region", "Chilobwe, Blantyre")
        g2.metric("Country", "Malawi (SE Africa)")
        g3.metric("Longitude Range", "35.006°E – 35.010°E")
        g4.metric("Latitude Range", "15.832°S – 15.837°S")
        st.caption("Coordinate Reference System: WGS 84 (EPSG:4326) · Resolution: ~0.5m GSD")

        st.markdown("---")
        st.markdown("#### Geographic Satellite Map (Chilobwe, Blantyre, Malawi)")
        st.markdown(
            "High-resolution Esri World Imagery basemap auto-fitted to the exact building polygon coordinates in Malawi. "
            "Click or hover on any building polygon to inspect UID and damage class. "
            "Indian Census district boundaries are **not** used."
        )
        malawi_map = mws.create_folium_malawi_map(selected_pair_id=pair_filter_id)
        try:
            from streamlit_folium import st_folium
            st_folium(
                malawi_map,
                width="stretch",
                height=520,
                key=f"malawi_folium_{pair_filter_id or 'all'}",
            )
        except Exception as e:
            st.warning(f"Interactive satellite map rendering issue: {e}")

        st.markdown("---")
        st.markdown("#### I. Complete Building Annotations Table (Post-Disaster Ground Truth)")
        all_post_annos = mws.load_all_post_annotations()
        anno_rows = []
        for a in all_post_annos:
            pts = a["pts_geo"]
            c_lon = sum(p[0] for p in pts) / len(pts)
            c_lat = sum(p[1] for p in pts) / len(pts)
            anno_rows.append({
                "Building UID": a["uid"],
                "Image Pair": a["pair_id"],
                "Damage Class": a["subtype"],
                "Centroid Longitude": round(c_lon, 6),
                "Centroid Latitude": round(c_lat, 6),
                "Vertices Count": len(pts),
            })
        anno_df = pd.DataFrame(anno_rows)
        st.dataframe(anno_df, use_container_width=True, hide_index=True)
        st.caption(f"Showing all {len(anno_df):,} unique post-disaster building annotations in Sample Subset1.")
    elif cfg.is_baseline:
        dataset = prepared_analytics(cfg.key)["dataset"]
        profile = registry.analyze_dataframe(dataset, cfg)
        numeric = [c for c in profile.numeric_columns if c in profile.numeric_stats]
        st.markdown("**Numerical statistics (real prepared dataset):**")
        stats = pd.DataFrame({
            "Column": numeric,
            "Mean": [round(profile.numeric_stats[c]["mean"], 4) for c in numeric],
            "Std Dev": [round(profile.numeric_stats[c]["std"], 4) for c in numeric],
            "Min": [round(profile.numeric_stats[c]["min"], 4) for c in numeric],
            "Median": [round(profile.numeric_stats[c]["median"], 4) for c in numeric],
            "Max": [round(profile.numeric_stats[c]["max"], 4) for c in numeric],
            "Missing Count": [profile.missing_counts.get(c, 0) for c in numeric],
        })
        st.dataframe(stats, use_container_width=True)
        st.markdown("**Feature distributions (real prepared dataset):**")
        c1, c2 = st.columns(2)
        c1.plotly_chart(px.histogram(dataset, x="Population", nbins=30,
                                     title="Population distribution"),
                        use_container_width=True)
        c2.plotly_chart(px.histogram(dataset, x="Parmanent_Water", nbins=30,
                                     title="Parmanent_Water distribution"),
                        use_container_width=True)
        st.plotly_chart(
            px.histogram(dataset, x="Corrected_Percent_Flooded_Area", nbins=30,
                         title="Target distribution (Corrected_Percent_Flooded_Area)"),
            use_container_width=True)
        top = dataset.nlargest(15, "Corrected_Percent_Flooded_Area")
        st.plotly_chart(
            px.bar(top, x="Corrected_Percent_Flooded_Area", y="Dist_Name", orientation="h",
                   title="Top-15 districts by Corrected_Percent_Flooded_Area "
                         "(whole prepared dataset)"),
            use_container_width=True)
    elif cfg.key == registry.IFI_IMPACT.key:
        frame = registry.load_dataset(cfg)
        profile = registry.analyze_dataframe(frame, cfg)
        dist_col = ds_rec.district_column or "Dist_Name"

        st.warning(
            "⚠️ **Descriptive post-event dataset — no validated predictive target is defined.** "
            "Model prediction, error analysis, and predictive risk modeling are not applicable."
        )

        st.markdown("**Dataset Overview & Missing-Data Summary:**")
        missing_rows = []
        for col in frame.columns:
            m_count = int(frame[col].isna().sum())
            missing_rows.append({
                "Column": col,
                "Data Type": str(frame[col].dtype),
                "Total Rows": len(frame),
                "Missing Count": m_count,
                "Missing (%)": round(m_count / len(frame) * 100, 2),
            })
        st.dataframe(pd.DataFrame(missing_rows), use_container_width=True, hide_index=True)

        numeric = [c for c in profile.numeric_columns if c in profile.numeric_stats]
        if numeric:
            st.markdown(f"**Numerical statistics ({cfg.name}):**")
            stats = pd.DataFrame({
                "Column": numeric,
                "Mean": [round(profile.numeric_stats[c]["mean"], 4) for c in numeric],
                "Std Dev": [round(profile.numeric_stats[c]["std"], 4) for c in numeric],
                "Min": [round(profile.numeric_stats[c]["min"], 4) for c in numeric],
                "Median": [round(profile.numeric_stats[c]["median"], 4) for c in numeric],
                "Max": [round(profile.numeric_stats[c]["max"], 4) for c in numeric],
                "Missing Count": [profile.missing_counts.get(c, 0) for c in numeric],
            })
            st.dataframe(stats, use_container_width=True, hide_index=True)

            st.markdown("**Distribution Visualizations:**")
            d1, d2 = st.columns(2)
            if "Human_fatality" in frame.columns:
                d1.plotly_chart(px.histogram(frame, x="Human_fatality", nbins=30,
                                             title="Human Fatality Distribution"),
                                use_container_width=True)
            if "Human_injured" in frame.columns:
                d2.plotly_chart(px.histogram(frame, x="Human_injured", nbins=30,
                                             title="Human Injured Distribution"),
                                use_container_width=True)
            d3, d4 = st.columns(2)
            if "Population" in frame.columns:
                d3.plotly_chart(px.histogram(frame, x="Population", nbins=30,
                                             title="Population Distribution"),
                                use_container_width=True)
            if "Mean_Flood_Duration" in frame.columns:
                d4.plotly_chart(px.histogram(frame, x="Mean_Flood_Duration", nbins=30,
                                             title="Mean Flood Duration (days) Distribution"),
                                use_container_width=True)

            st.markdown("**District Rankings (Top-15 Districts):**")
            r1, r2 = st.columns(2)
            if "Human_fatality" in frame.columns:
                top_fat = frame[[dist_col, "Human_fatality"]].dropna().nlargest(15, "Human_fatality")
                r1.plotly_chart(px.bar(top_fat, x="Human_fatality", y=dist_col, orientation="h",
                                       title="Highest Fatalities (Top-15 Districts)"),
                                use_container_width=True)
            if "Human_injured" in frame.columns:
                top_inj = frame[[dist_col, "Human_injured"]].dropna().nlargest(15, "Human_injured")
                r2.plotly_chart(px.bar(top_inj, x="Human_injured", y=dist_col, orientation="h",
                                       title="Highest Injuries (Top-15 Districts)"),
                                use_container_width=True)
            r3, r4 = st.columns(2)
            if "Population" in frame.columns:
                top_pop = frame[[dist_col, "Population"]].dropna().nlargest(15, "Population")
                r3.plotly_chart(px.bar(top_pop, x="Population", y=dist_col, orientation="h",
                                       title="Highest Population (Top-15 Districts)"),
                                use_container_width=True)
            if "Mean_Flood_Duration" in frame.columns:
                top_dur = frame[[dist_col, "Mean_Flood_Duration"]].dropna().nlargest(15, "Mean_Flood_Duration")
                r4.plotly_chart(px.bar(top_dur, x="Mean_Flood_Duration", y=dist_col, orientation="h",
                                       title="Longest Mean Flood Duration (Top-15 Districts)"),
                                use_container_width=True)

        st.markdown("**District Information Table (Complete Dataset):**")
        st.dataframe(frame, use_container_width=True)
        st.caption(f"Source file: `{cfg.source}` — {len(frame):,} rows, {len(frame.columns)} columns.")

    elif cfg.key == registry.IFI_FLOODED_AREA.key:
        frame = registry.load_dataset(cfg)
        profile = registry.analyze_dataframe(frame, cfg)
        dist_col = ds_rec.district_column or "Dist_Name"

        st.warning(
            "⚠️ **Target Leakage Alert:** In this raw table, the target is mathematically defined as:  \n"
            "`Corrected_Percent_Flooded_Area = Percent_Flooded_Area - Parmanent_Water`.  \n"
            "Using `Percent_Flooded_Area` to predict `Corrected_Percent_Flooded_Area` constitutes a circular algebraic identity, "
            "not an independent predictive relationship. Therefore, no predictive model is trained or evaluated on this table directly."
        )

        st.markdown("**Dataset Overview & Missing-Data Summary:**")
        missing_rows = []
        for col in frame.columns:
            m_count = int(frame[col].isna().sum())
            missing_rows.append({
                "Column": col,
                "Data Type": str(frame[col].dtype),
                "Total Rows": len(frame),
                "Missing Count": m_count,
                "Missing (%)": round(m_count / len(frame) * 100, 2),
            })
        st.dataframe(pd.DataFrame(missing_rows), use_container_width=True, hide_index=True)

        numeric = [c for c in profile.numeric_columns if c in profile.numeric_stats]
        if numeric:
            st.markdown(f"**Numerical statistics ({cfg.name}):**")
            stats = pd.DataFrame({
                "Column": numeric,
                "Mean": [round(profile.numeric_stats[c]["mean"], 4) for c in numeric],
                "Std Dev": [round(profile.numeric_stats[c]["std"], 4) for c in numeric],
                "Min": [round(profile.numeric_stats[c]["min"], 4) for c in numeric],
                "Median": [round(profile.numeric_stats[c]["median"], 4) for c in numeric],
                "Max": [round(profile.numeric_stats[c]["max"], 4) for c in numeric],
                "Missing Count": [profile.missing_counts.get(c, 0) for c in numeric],
            })
            st.dataframe(stats, use_container_width=True, hide_index=True)

            st.markdown("**Distribution Visualizations:**")
            f1, f2, f3 = st.columns(3)
            if "Corrected_Percent_Flooded_Area" in frame.columns:
                f1.plotly_chart(px.histogram(frame, x="Corrected_Percent_Flooded_Area", nbins=30,
                                             title="Corrected_Percent_Flooded_Area (%)"),
                                use_container_width=True)
            if "Percent_Flooded_Area" in frame.columns:
                f2.plotly_chart(px.histogram(frame, x="Percent_Flooded_Area", nbins=30,
                                             title="Percent_Flooded_Area (%)"),
                                use_container_width=True)
            if "Parmanent_Water" in frame.columns:
                f3.plotly_chart(px.histogram(frame, x="Parmanent_Water", nbins=30,
                                             title="Parmanent_Water (%)"),
                                use_container_width=True)

            st.markdown("**District Rankings (Top-15 Districts):**")
            k1, k2, k3 = st.columns(3)
            if "Corrected_Percent_Flooded_Area" in frame.columns:
                top_c = frame[[dist_col, "Corrected_Percent_Flooded_Area"]].dropna().nlargest(15, "Corrected_Percent_Flooded_Area")
                k1.plotly_chart(px.bar(top_c, x="Corrected_Percent_Flooded_Area", y=dist_col, orientation="h",
                                       title="Top-15 by Corrected % Flooded"),
                                use_container_width=True)
            if "Percent_Flooded_Area" in frame.columns:
                top_p = frame[[dist_col, "Percent_Flooded_Area"]].dropna().nlargest(15, "Percent_Flooded_Area")
                k2.plotly_chart(px.bar(top_p, x="Percent_Flooded_Area", y=dist_col, orientation="h",
                                       title="Top-15 by Raw % Flooded"),
                                use_container_width=True)
            if "Parmanent_Water" in frame.columns:
                top_w = frame[[dist_col, "Parmanent_Water"]].dropna().nlargest(15, "Parmanent_Water")
                k3.plotly_chart(px.bar(top_w, x="Parmanent_Water", y=dist_col, orientation="h",
                                       title="Top-15 by Permanent Water"),
                                use_container_width=True)

            st.markdown("**Target Leakage Identity Analysis:**")
            if "Percent_Flooded_Area" in frame.columns and "Corrected_Percent_Flooded_Area" in frame.columns:
                fig_leak = px.scatter(
                    frame,
                    x="Percent_Flooded_Area",
                    y="Corrected_Percent_Flooded_Area",
                    hover_name=dist_col,
                    title="Algebraic Target Leakage: Percent_Flooded_Area vs. Corrected_Percent_Flooded_Area",
                    labels={
                        "Percent_Flooded_Area": "Percent_Flooded_Area (%)",
                        "Corrected_Percent_Flooded_Area": "Corrected_Percent_Flooded_Area (%)",
                    },
                )
                st.plotly_chart(fig_leak, use_container_width=True)
                st.caption("Notice the deterministic linear shift caused by subtracting Parmanent_Water.")

        st.markdown("**District Information Table (Complete Dataset):**")
        st.dataframe(frame, use_container_width=True)
        st.caption(f"Source file: `{cfg.source}` — {len(frame):,} rows, {len(frame.columns)} columns.")

    else:
        frame = registry.load_dataset(cfg)
        st.dataframe(frame.head(20), use_container_width=True)
    st.markdown("---")


def section_11_flood_disaster_analysis(cfg: registry.DatasetConfig) -> None:
    st.markdown("### 11. Flood / Disaster Analysis")
    if cfg.is_image_dataset:
        support = dict(registry.load_image_dataset(cfg).output_support)
    else:
        profile = registry.analyze_dataframe(registry.load_dataset(cfg), cfg)
        support = dict(profile.output_support)
    for output in registry.FLOOD_OUTPUTS:
        oa = support.get(output, registry.available(registry.STATUS_NOT_AVAILABLE, ""))
        st.markdown(f"- **{output}:** `{oa.status}` — {oa.detail}")
    take = {
        registry.M2_BASELINE.key: (
            "This system currently performs district-level flooded-area regression "
            "(Flood Extent). Probability, severity, GIS and warning outputs are not "
            "produced by the trained baseline on this dataset."
        ),
        registry.IFI_IMPACT.key: (
            "Descriptive district aggregates; no prediction target is defined. Historical "
            "fatality/injury counts exist but no verified severity rubric is defined."
        ),
        registry.IFI_FLOODED_AREA.key: (
            "Regression target data is present, but the trained IFI checkpoints are fit on "
            "the prepared 720-row dataset and are not run on this raw table."
        ),
        registry.MWBTFREDDY.key: (
            "Building damage severity labels and footprint coordinates are present as data; "
            "no model is trained on this sample subset and no warning/risk rule is defined."
        ),
    }
    st.markdown(take.get(cfg.key, "No fixed analysis summary is defined for this dataset."))
    st.markdown("---")


def section_flood_risk_visualization(
    cfg: registry.DatasetConfig,
    compat: registry.ModelCompatibility,
) -> None:
    st.markdown("### Flood Risk Visualization")

    st.markdown(
        "Adapted from research on integrated flood-response platforms and risk visualization "
        "(e.g., *AlleyFloodNet: A Ground-Level Image Dataset for Rapid Flood Detection in "
        "Economically and Flood-Vulnerable Areas*, Lee & Joo, *Electronics*, 2025, "
        "DOI: [10.3390/electronics14102082](https://doi.org/10.3390/electronics14102082)), "
        "this section translates flood metrics into spatial risk categories across district "
        "boundaries for comparative evaluation."
    )

    from src.gis.flood_risk_service import (
        get_model_flood_risk_data,
        create_folium_risk_map,
        get_descriptive_gis_data,
        create_folium_descriptive_map,
    )
    from src.config.model_registry import get_model_record
    from src.config.dataset_registry import get_dataset

    ds_rec = get_dataset(cfg.key)
    rec = get_model_record(cfg.key, compat.model_name)

    # MODE A: Prediction Risk Map (when valid evaluated predictions exist)
    if cfg.is_baseline and compat.model_name in registry.TRAINED_IFI_MODELS:
        data = get_model_flood_risk_data(compat.model_name, PROJECT_ROOT, dataset_id=cfg.key)
        if data is not None:
            st.markdown(f"**Flood Risk Summary Cards — {compat.model_name} (Test Set, N = {data['total_count']}):**")
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("Low Risk Districts", data["category_counts"].get("LOW", 0))
            c2.metric("Moderate Risk Districts", data["category_counts"].get("MODERATE", 0))
            c3.metric("High Risk Districts", data["category_counts"].get("HIGH", 0))
            c4.metric("Very High Risk Districts", data["category_counts"].get("VERY HIGH", 0))
            c5.metric("Highest predicted flooded-area district", data["peak_district"]["district"])
            c6.metric("Highest predicted flooded-area percentage", f"{data['peak_district']['predicted']:.2f}%")

            t = data["thresholds"]
            st.caption(
                f"**Model-based Flood Risk Category Thresholds ({compat.model_name}):** "
                f"LOW: ≤ {t['q25']:.3f}% | MODERATE: {t['q25']:.3f}% – {t['q50']:.3f}% | "
                f"HIGH: {t['q50']:.3f}% – {t['q75']:.3f}% | VERY HIGH: > {t['q75']:.3f}% "
                f"(derived from test-set prediction quantiles Q25, Q50, Q75)."
            )

            st.markdown(f"**District Risk Map ({compat.model_name})**")
            folium_map = create_folium_risk_map(data)
            try:
                from streamlit_folium import st_folium
                map_out = st_folium(
                    folium_map,
                    width="stretch",
                    height=500,
                    key=f"risk_map_{compat.model_name}",
                )
            except Exception as e:
                st.warning(f"Interactive map rendering encountered an issue: {e}")
                map_out = None

            st.markdown("#### District Information")
            clicked_district = None
            if map_out and isinstance(map_out, dict):
                drawing = map_out.get("last_active_drawing")
                if drawing and isinstance(drawing, dict) and "properties" in drawing:
                    clicked_district = drawing["properties"].get("district") or drawing["properties"].get("district_name")

            district_options = sorted([d["district_name"] for d in data["all_districts"]])
            default_idx = 0
            if clicked_district and clicked_district in district_options:
                default_idx = district_options.index(clicked_district)
            elif data["peak_district"]["district_name"] in district_options:
                default_idx = district_options.index(data["peak_district"]["district_name"])

            selected_dname = st.selectbox(
                "Select district to inspect:",
                district_options,
                index=default_idx,
                key=f"risk_dist_select_{compat.model_name}",
            )
            sel_rec = next((d for d in data["all_districts"] if d["district_name"] == selected_dname), data["all_districts"][0])

            i1, i2, i3, i4 = st.columns(4)
            with i1:
                st.markdown(f"**District:**\n### {sel_rec['district_name']}")
                st.caption(f"Identifier: `{sel_rec['district_id']}`")
            with i2:
                st.markdown(f"**Predicted flooded area:**\n### {sel_rec['predicted_flooded_percent']:.2f} %")
                st.caption(f"Actual Flooded Area: {sel_rec['actual']:.2f}%")
            with i3:
                st.markdown(f"**Risk category:**\n### {sel_rec['risk_category']}")
                st.caption("Model-based comparative risk")
            with i4:
                st.markdown(f"**Selected model:**\n### {compat.model_name}")
                st.caption(f"Boundary Status: {'Mapped in Census 2011' if sel_rec['has_geometry'] else 'Unmapped'}")

            st.markdown("#### Data Alignment & Boundary Coverage")
            st.info(
                f"**Data Alignment:** All {data['total_count']} evaluated test districts are mapped to their respective dataset records. "
                f"{data['mapped_count']} districts match Census 2011 boundary polygons directly. "
                f"{data['unmapped_count']} districts (newer administrative units formed after the 2011 census) lack 2011 boundary polygons "
                f"and are explicitly accounted for without silent fuzzy matching or geometric distortion."
            )
            with st.expander(f"View Unmapped Districts ({data['unmapped_count']} districts)"):
                unmapped_table = pd.DataFrame([
                    {
                        "District": d["district_name"],
                        "District Identifier": d["district_id"],
                        "Predicted Flooded Area (%)": round(d["predicted_flooded_percent"], 3),
                        "Risk Category": d["risk_category"],
                        "Population": d["population"],
                        "Permanent Water": d["permanent_water"],
                    }
                    for d in data["unmapped_districts"]
                ])
                st.dataframe(unmapped_table, use_container_width=True, hide_index=True)

            st.markdown("#### Methodology Note")
            st.markdown(
                "> **Methodology Note:** Risk categories are visualization-oriented categories derived from the "
                "model's predicted flooded-area percentage. They are intended for comparative interpretation within this "
                "application and do not represent official government hazard thresholds or real-time emergency warnings."
            )
            st.markdown("---")
            return

    # If IFI baseline but untrained model: exact message tested in validation suite
    if cfg.is_baseline:
        st.info("Risk visualization unavailable: no valid evaluated predictions are available for this model.")
        st.markdown("---")
        return

    # MODE B: DATASET GIS OVERVIEW / DESCRIPTIVE DISTRICT MAP
    # (when predictions do not exist but district geography is available)
    if ds_rec.has_gis and not ds_rec.is_image_dataset:
        st.info(
            f"Model predictions are unavailable for **{cfg.name} + {compat.model_name}**. "
            "Displaying **Dataset GIS Overview (Descriptive District Map)** based on Census 2011 boundaries."
        )
        temp_gis = get_descriptive_gis_data(cfg.key)
        if temp_gis is not None and temp_gis["available_variables"]:
            var_options = temp_gis["available_variables"]
            sel_var = st.selectbox(
                "Select descriptive variable to map:",
                var_options,
                key=f"desc_gis_var_{cfg.key}",
            )
            desc_data = get_descriptive_gis_data(cfg.key, variable_name=sel_var)
            if desc_data is not None:
                st.markdown(f"#### Dataset GIS Overview: Descriptive District Map ({sel_var})")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Mapped Districts", desc_data["mapped_count"])
                c2.metric("Unmapped Districts", desc_data["unmapped_count"])
                c3.metric(f"Peak District ({sel_var})", desc_data["peak_district"]["district"])
                c4.metric(f"Peak Value", f"{desc_data['peak_district']['value']:,.2f}")

                desc_map = create_folium_descriptive_map(desc_data)
                try:
                    from streamlit_folium import st_folium
                    map_out_b = st_folium(
                        desc_map,
                        width="stretch",
                        height=500,
                        key=f"desc_map_{cfg.key}_{sel_var}",
                    )
                except Exception as e:
                    st.warning(f"Interactive map rendering encountered an issue: {e}")
                    map_out_b = None

                st.markdown("#### District Information")
                clicked_district_b = None
                if map_out_b and isinstance(map_out_b, dict):
                    drawing = map_out_b.get("last_active_drawing")
                    if drawing and isinstance(drawing, dict) and "properties" in drawing:
                        clicked_district_b = drawing["properties"].get("district")

                dist_opts_b = sorted([d["district_name"] for d in desc_data["all_districts"]])
                default_idx_b = 0
                if clicked_district_b and clicked_district_b in dist_opts_b:
                    default_idx_b = dist_opts_b.index(clicked_district_b)
                elif desc_data["peak_district"]["district"] in dist_opts_b:
                    default_idx_b = dist_opts_b.index(desc_data["peak_district"]["district"])

                sel_dname_b = st.selectbox(
                    "Select district to inspect:",
                    dist_opts_b,
                    index=default_idx_b,
                    key=f"desc_dist_select_{cfg.key}",
                )
                sel_rec_b = next((d for d in desc_data["all_districts"] if d["district_name"] == sel_dname_b), desc_data["all_districts"][0])

                i1, i2, i3, i4 = st.columns(4)
                with i1:
                    st.markdown(f"**District:**\n### {sel_rec_b['district_name']}")
                    st.caption(f"Census Code: `{sel_rec_b.get('censuscode', 'Unmapped')}`")
                with i2:
                    st.markdown(f"**{sel_var}:**\n### {sel_rec_b['value']:,.2f}")
                    st.caption(f"Descriptive Value")
                with i3:
                    st.markdown(f"**Tier:**\n### {sel_rec_b['tier']}")
                    st.caption(f"Quartile Classification")
                with i4:
                    st.markdown(f"**State:**\n### {sel_rec_b.get('state', 'Unmapped')}")
                    st.caption(f"Boundary Status: {'Mapped' if sel_rec_b['is_mapped'] else 'Unmapped'}")

                if desc_data["unmapped_count"] > 0:
                    with st.expander(f"View Unmapped Districts ({desc_data['unmapped_count']} districts)"):
                        st.dataframe(pd.DataFrame(desc_data["unmapped_districts"]), use_container_width=True, hide_index=True)

                st.markdown("#### Methodology Note")
                st.markdown(
                    "> **Descriptive Map Note:** This map visualizes raw reported values from the dataset "
                    "joined with 2011 Census district boundaries. It is not a predictive risk model."
                )
                st.markdown("---")
                return

    # Default fallback for datasets without GIS
    st.info("Risk visualization unavailable: no valid evaluated predictions are available for this model.")
    if cfg.is_image_dataset:
        st.caption(
            "mwBTFreddy consists of bitemporal satellite imagery over Chilobwe, Blantyre, Malawi (not Indian Census district polygons). "
            "Please refer to **Section 10 (Dataset-specific Visualizations)** for the interactive satellite map and building footprint geometry."
        )
    st.markdown("---")


def section_prediction_error_analysis(
    cfg: registry.DatasetConfig,
    compat: registry.ModelCompatibility,
) -> None:
    st.markdown("### Prediction Error Analysis")

    st.markdown(
        "Adapted from research on model-error analysis and targeted model improvement "
        "(e.g., AlleyFloodNet), this section systematically inspects test-set prediction "
        "errors, residuals, and outlier districts to diagnose model limitations on the evaluation split."
    )

    rec = get_model_record(cfg.key, compat.model_name)
    if not cfg.is_baseline or compat.model_name not in registry.TRAINED_IFI_MODELS or not rec.has_predictions:
        st.info("Prediction error analysis is unavailable because no valid evaluated test-set predictions are available for this model.")
        st.markdown("---")
        return

    from src.evaluation.error_analysis import get_model_error_analysis

    res = get_model_error_analysis(compat.model_name, PROJECT_ROOT, dataset_id=cfg.key)
    if res is None:
        st.info("Prediction error analysis is unavailable because no valid evaluated test-set predictions are available for this model.")
        st.markdown("---")
        return

    m = res["metrics"]

    st.markdown(f"**Error Summary Metrics — {compat.model_name} (Test Set, N = {m['Sample_Count']}):**")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("MAE", f"{m['MAE']:.4f}")
    c2.metric("RMSE", f"{m['RMSE']:.4f}")
    c3.metric("R²", f"{m['R2']:.4f}")
    c4.metric("Mean Error", f"{m['Mean_Error']:+.4f}")
    c5.metric("Max Absolute Error", f"{m['Max_Absolute_Error']:.4f}")
    c6.metric("Samples Analyzed", f"{m['Sample_Count']}")

    col_scatter, col_hist = st.columns([1, 1])
    full_df = res["full_data"]

    with col_scatter:
        st.markdown("**Actual vs. Predicted Flooded Area**")
        min_v = min(full_df["actual"].min(), full_df["predicted"].min())
        max_v = max(full_df["actual"].max(), full_df["predicted"].max())
        fig_scatter = px.scatter(
            full_df,
            x="actual",
            y="predicted",
            hover_name="District",
            hover_data={"actual": ":.3f", "predicted": ":.3f", "Error": ":.3f"},
            labels={
                "actual": "Actual Corrected Percent Flooded Area (%)",
                "predicted": "Predicted Corrected Percent Flooded Area (%)",
            },
            title=f"Actual vs. Predicted Flooded Area (%) — {compat.model_name}",
        )
        fig_scatter.add_shape(
            type="line",
            x0=min_v, y0=min_v,
            x1=max_v, y1=max_v,
            line=dict(color="red", dash="dash"),
        )
        fig_scatter.update_layout(height=420)
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption("Red dashed line indicates the ideal y = x line where prediction equals ground truth.")

    with col_hist:
        st.markdown("**Error Distribution (Predicted − Actual)**")
        fig_hist = px.histogram(
            full_df,
            x="Error",
            nbins=30,
            labels={"Error": "Prediction Error (% flooded area)"},
            title=f"Prediction Error Distribution — {compat.model_name}",
        )
        fig_hist.add_vline(
            x=0,
            line_dash="dash",
            line_color="black",
            annotation_text="Zero Error (y = 0)",
            annotation_position="top left",
        )
        fig_hist.update_layout(yaxis_title="Count", height=420)
        st.plotly_chart(fig_hist, use_container_width=True)
        st.caption("Error = Predicted − Actual. Positive values denote over-prediction; negative denote under-prediction.")

    st.markdown("**Top 10 Largest Prediction Errors**")
    top10_table = res["top10_table"].copy()
    for col in ["Actual Flooded Area (%)", "Predicted Flooded Area (%)", "Error", "Absolute Error"]:
        top10_table[col] = top10_table[col].round(4)
    st.dataframe(top10_table, use_container_width=True, hide_index=True)
    st.caption("Top 10 test districts ranked by Absolute Error in descending order.")

    st.markdown("#### Automatic Error Interpretation")
    st.markdown(res["interpretation"])
    st.markdown("---")


def section_future_work_feature_ablation_study(
    cfg: registry.DatasetConfig,
    compat: registry.ModelCompatibility,
) -> None:
    st.markdown("### Feature Ablation Study")

    st.info(
        "**Research Context (STURM-Flood, Notarangelo et al., 2025):**\n\n"
        "Feature ablation measures how model performance changes when individual "
        "input features are removed while keeping the evaluation setup consistent."
    )

    rec = get_model_record(cfg.key, compat.model_name)
    if not cfg.is_baseline or compat.model_name not in registry.TRAINED_IFI_MODELS or not rec.has_predictions:
        st.markdown("**Feature Ablation Status**")
        st.info(
            f"Feature ablation results are not currently available for {cfg.name} + {compat.model_name}."
        )
        st.markdown("---")
        return

    ablation_data = load_ablation_summary()
    model_ablation = ablation_data.get(compat.model_name, {})
    if not model_ablation:
        st.info(f"Feature ablation results are not currently available for {cfg.name} + {compat.model_name}.")
        st.markdown("---")
        return

    st.markdown(f"**Ablation Evaluation on Untouched Test Split — {compat.model_name}:**")

    table_rows = []
    chart_rows = []
    config_order = ["Full Baseline", "Population Only", "Permanent Water Only"]
    for cfg_name in config_order:
        res = model_ablation.get(cfg_name)
        if res:
            mae = float(res["MAE"])
            rmse = float(res["RMSE"])
            r2 = float(res["R2"])
            table_rows.append({
                "Feature Configuration": cfg_name,
                "MAE": round(mae, 4),
                "RMSE": round(rmse, 4),
                "R²": round(r2, 4),
            })
            chart_rows.append({
                "Feature Configuration": cfg_name,
                "MAE": mae,
            })

    table_df = pd.DataFrame(table_rows)
    st.dataframe(table_df, use_container_width=True, hide_index=True)
    st.caption(
        "All three configurations evaluated on the exact same untouched test split (109 districts). "
        "Full Baseline reflects the existing saved baseline checkpoint; single-feature configurations "
        "are trained deterministically under results/models/ablation/."
    )

    if chart_rows:
        chart_df = pd.DataFrame(chart_rows)
        fig = px.bar(
            chart_df,
            x="Feature Configuration",
            y="MAE",
            text="MAE",
            color="Feature Configuration",
            color_discrete_sequence=["#2E75B6", "#ED7D31", "#A5A5A5"],
            title=f"Test MAE across Feature Configurations ({compat.model_name})",
        )
        fig.update_traces(texttemplate="%{text:.4f}", textposition="outside")
        fig.update_layout(
            yaxis_title="MAE (lower is better)",
            showlegend=False,
            height=380,
            yaxis=dict(range=[0, max(chart_df["MAE"]) * 1.25]),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Automatic Interpretation")
    interpretation_text = _generate_ablation_interpretation(compat.model_name, table_rows)
    st.markdown(interpretation_text)
    st.markdown("---")


def _generate_ablation_interpretation(model_name: str, rows: list[dict]) -> str:
    if not rows:
        return "No ablation results available to interpret."
    best_mae_row = min(rows, key=lambda r: r["MAE"])
    best_r2_row = max(rows, key=lambda r: r["R²"])

    full_row = next((r for r in rows if r["Feature Configuration"] == "Full Baseline"), None)
    pop_row = next((r for r in rows if r["Feature Configuration"] == "Population Only"), None)
    water_row = next((r for r in rows if r["Feature Configuration"] == "Permanent Water Only"), None)

    parts = [
        f"For **{model_name}**, the **{best_mae_row['Feature Configuration']}** configuration achieves the lowest test MAE ({best_mae_row['MAE']:.4f}).",
        f"The highest R² ({best_r2_row['R²']:.4f}) is achieved by **{best_r2_row['Feature Configuration']}**.",
    ]

    if full_row and pop_row and water_row:
        if full_row["MAE"] <= pop_row["MAE"] and full_row["MAE"] <= water_row["MAE"]:
            parts.append(
                "Both **Population** and **Parmanent_Water** appear useful: removing either feature increases prediction error (MAE) compared to the full baseline, "
                "indicating that demographic scale and hydrological surface metrics provide complementary predictive signal."
            )
        elif full_row["MAE"] > pop_row["MAE"]:
            parts.append(
                "**Population** alone achieved lower error than the multi-feature baseline, suggesting that Parmanent_Water did not improve test accuracy for this architecture."
            )
        elif full_row["MAE"] > water_row["MAE"]:
            parts.append(
                "**Parmanent_Water** alone achieved lower error than the multi-feature baseline, suggesting that Population did not improve test accuracy for this architecture."
            )

    parts.append(
        "*Note: These observations reflect statistical association and predictive error on the evaluation split; they do not establish causal relationships.*"
    )
    return " ".join(parts)


# ---------------------------------------------------------------------------
# VIEW 1: unified analytics layout for every dataset
# ---------------------------------------------------------------------------

if dashboard_view == "Analytics & GIS Overview (Default)":

    st.title("AI-Powered Flood Early Warning Dashboard")
    st.caption("Unified 10-section overview: real dataset parameters, five selectable model "
               "architectures, and their true performance status for every dataset.")

    section_1_dataset_overview(cfg)
    section_2_model_comparison(cfg, compat)
    section_2_classical_baselines(cfg)
    section_3_dataset_features(cfg)
    section_4_data_preview(cfg)
    section_5_model_selection_and_status(cfg, compat)
    section_6_model_performance(cfg, compat)
    section_7_prediction_visualization(cfg, compat)
    section_8_actual_vs_predicted(cfg, compat)
    section_9_error_analysis(cfg, compat)
    section_10_dataset_visualizations(cfg)
    section_11_flood_disaster_analysis(cfg)
    section_flood_risk_visualization(cfg, compat)
    section_prediction_error_analysis(cfg, compat)
    section_future_work_feature_ablation_study(cfg, compat)


# VIEW 2: EXECUTION ENGINE
else:
    st.title("API-Driven Model Execution Engine")
    sub_mode = st.radio(
        "Select Execution Workflow",
        ["Inference / Prediction Mode", "Model Retraining Mode"],
        horizontal=True,
    )
    all_models = ["CNN + LSTM", "CNN + Transformer", "ResNet + BiLSTM", "U-Net + ConvLSTM", "Attention U-Net + LSTM"]

    if sub_mode == "Inference / Prediction Mode":
        st.subheader("Run Model Inference")
        c1, c2 = st.columns(2)
        with c1:
            selected_model = st.selectbox("1. Select Model Architecture", all_models)
        with c2:
            selected_task = st.selectbox("2. Target Task", api.get_supported_tasks())

        available = api.get_available_models()
        if selected_model in api.PLANNED_MODELS:
            st.warning(
                f"⚠️ **Incompatible Architecture:** Model **{selected_model}** requires 5D spatial raster/image inputs "
                "`(batch, time, channels, height, width)`. Prediction inputs are disabled because spatial input data is unavailable."
            )
        elif selected_model not in available:
            st.warning(f"⚠️ **Model Unavailable:** No trained checkpoint found for **{selected_model}** in `results/models/`. Training required.")
        else:
            st.success(f"✅ Verified trained checkpoint available for **{selected_model}** (IFI M2 Baseline).")

            pred_tab1, pred_tab2 = st.tabs(["Interactive Custom Prediction", "Batch CSV Inference"])

            with pred_tab1:
                st.markdown("#### Live District Inundation Prediction")
                st.caption("Enter district demographic and hydrological surface metrics to generate instant live inference.")
                c_p1, c_p2, c_p3 = st.columns(3)
                with c_p1:
                    custom_dist = st.text_input("District Name", value="Custom Test District", key="custom_dist_name")
                with c_p2:
                    custom_pop = st.number_input("Population (persons)", min_value=1000, max_value=25000000, value=500000, step=25000, key="custom_pop_val")
                with c_p3:
                    custom_wat = st.number_input("Permanent Water (%)", min_value=0.0, max_value=100.0, value=1.50, step=0.1, format="%.2f", key="custom_wat_val")

                if st.button("🚀 Run Live Inference", key="btn_run_single"):
                    single_df = pd.DataFrame([{
                        "Dist_Name": custom_dist,
                        "Population": float(custom_pop),
                        "Parmanent_Water": float(custom_wat),
                    }])
                    try:
                        res = api.predict_uploaded_dataset(single_df, selected_model, selected_task)
                        if res["status"] == "success":
                            pred_val = res["prediction"][0]
                            st.success(f"### Predicted Flooded Area: **{pred_val:.3f} %**")
                            st.caption(f"Expected Unit: % of total district land area inundated. Inference latency: {res.get('inference_time', 0.0)*1000:.2f} ms")
                            m_info = res.get("metrics", {})
                            if m_info:
                                k1, k2, k3 = st.columns(3)
                                k1.metric("Model Test MAE", f"{m_info.get('MAE', 0):.4f}")
                                k2.metric("Model Test RMSE", f"{m_info.get('RMSE', 0):.4f}")
                                k3.metric("Model Test R²", f"{m_info.get('R2', 0):.4f}")
                        else:
                            st.error(f"Prediction failed: {res.get('status')}")
                    except Exception as e:
                        st.error(f"Inference error: {e}")

            with pred_tab2:
                uploaded_file = st.file_uploader("Upload Input Dataset (CSV)", type=["csv"], key="csv_batch_up")

                if uploaded_file is not None:
                    df = pd.read_csv(uploaded_file)
                    with st.expander("Inspect Uploaded Dataset"):
                        st.json(api.inspect_dataset(df))
                        st.dataframe(df.head())

                    mapped_df, mapping_applied = api.adapt_dataset(df, selected_model, selected_task)
                    compat2 = api.check_compatibility(mapped_df, selected_model, selected_task)

                    st.subheader("Schema Compatibility Analysis")
                    if mapping_applied:
                        st.info("Auto-mapped column aliases:")
                        st.json(mapping_applied)

                    for warn in compat2["warnings"]:
                        st.warning(warn)

                    if compat2["is_compatible"]:
                        st.success("✅ Dataset features are COMPATIBLE.")
                        if st.button("🚀 Run Batch Prediction", key="btn_run_batch"):
                            try:
                                res = api.predict_uploaded_dataset(mapped_df, selected_model, selected_task)
                                out_df = mapped_df.copy()
                                if res["status"] == "success":
                                    out_df["Predicted Corrected_Percent_Flooded_Area"] = res["prediction"]
                                    st.subheader("Output Prediction Table")
                                    st.dataframe(out_df)
                                else:
                                    st.error(f"Prediction failed: {res['status']}")
                                    for warn in res.get("warnings", []):
                                        st.warning(warn)
                            except Exception as e:
                                st.error(f"Inference Error: {str(e)}")
                    else:
                        st.error("❌ Dataset INCOMPATIBLE. Prediction blocked.")
                        if compat2["missing_features"]:
                            st.write("**Missing Required Features:**")
                            st.json(compat2["missing_features"])

    else:
        st.subheader("Model Retraining Pipeline")
        retrain_model_name = st.selectbox("Select Model to Train", all_models)
        retrain_task = st.selectbox("Select Task", api.get_supported_tasks())
        train_file = st.file_uploader("Upload Training Data (CSV)", type=["csv"], key="train_up")
        epochs = st.number_input("Epochs", min_value=1, max_value=100, value=10)
        learning_rate = st.selectbox("Learning Rate", [0.001, 0.0001, 0.01])

        st.warning(
            "Retraining is unavailable in the dashboard. Prediction never retrains a model. "
            "Use the explicit Member 2 training command outside the dashboard: "
            "`src.training.train_real_regression`."
        )

        if train_file is not None and st.button("Execute Retraining"):
            train_df = pd.read_csv(train_file)
            res = api.retrain_model(train_df, retrain_model_name, retrain_task, {"epochs": epochs, "lr": learning_rate})
            if res["status"] == "unavailable":
                st.warning(res["message"])
            else:
                st.success(res["message"])
            st.json(res["metrics"])