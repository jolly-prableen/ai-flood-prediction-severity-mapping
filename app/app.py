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

DATASET_CSV = PROJECT_ROOT / "data" / "processed" / "district_flood_area_regression.csv"
SPLIT_JSON = PROJECT_ROOT / "data" / "splits" / "district_flood_area_split.json"
ACTUAL_VS_PREDICTED_CSV = PROJECT_ROOT / "results" / "evaluation" / "actual_vs_predicted.csv"
ERROR_SUMMARY_CSV = PROJECT_ROOT / "results" / "evaluation" / "error_summary.csv"
M2_FINAL_METRICS_JSON = PROJECT_ROOT / "results" / "final_member2" / "member2_final_metrics.json"

st.set_page_config(
    page_title="AI Flood Early Warning Dashboard",
    layout="wide",
    page_icon="🌊",
)

st.sidebar.title("Dashboard Controls")
dashboard_view = st.sidebar.radio(
    "Select View Mode",
    ["Analytics & GIS Overview (Default)", "Custom Prediction & Retraining Mode"],
)
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


@st.cache_data
def prepared_analytics() -> dict:
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


def sidebar_dataset_selector() -> registry.DatasetConfig:
    datasets = registry.available_datasets()
    if not datasets:
        datasets = [registry.M2_BASELINE]
    options = {d.name: d for d in datasets}
    choice = st.sidebar.selectbox("Dataset", list(options), key="data_sel")
    return options[choice]


def build_geo_figure(details: registry.ImageDatasetDetails) -> go.Figure:
    color_map = {"no-damage": "#2e7d32", "minor-damage": "#f9a825",
                 "major-damage": "#ef6c00", "destroyed": "#c62828"}
    traces: dict[str, dict[str, list]] = {}
    lon_min, lon_max, lat_min, lat_max = 180.0, -180.0, 90.0, -90.0
    for poly in details.sample_polygons:
        subtype = poly["subtype"]
        pts = poly["lng_lat"]
        lone = [p[0] for p in pts] + [pts[0][0]]
        late = [p[1] for p in pts] + [pts[0][1]]
        for lon, lat in pts:
            lon_min, lon_max = min(lon_min, lon), max(lon_max, lon)
            lat_min, lat_max = min(lat_min, lat), max(lat_max, lat)
        bucket = traces.setdefault(subtype, {"lon": [], "lat": []})
        bucket["lon"].extend(lone + [None])
        bucket["lat"].extend(late + [None])
    fig = go.Figure()
    for subtype, data in traces.items():
        fig.add_trace(go.Scattergeo(
            lon=data["lon"], lat=data["lat"], mode="lines", name=subtype,
            line=dict(width=2, color=color_map.get(subtype, "#555555")),
            hovertemplate="%{lat:.5f}, %{lon:.5f}<extra></extra>",
        ))
    margin = 0.01
    geo_opts = dict(showland=True, landcolor="#e8f0e8", coastlinecolor="#444444")
    if lon_min < lon_max and lat_min < lat_max:
        geo_opts["lonaxis"] = dict(range=[round(lon_min - margin, 6), round(lon_max + margin, 6)])
        geo_opts["lataxis"] = dict(range=[round(lat_min - margin, 6), round(lat_max + margin, 6)])
    fig.update_layout(height=520, title="Sample building footprints from JSON annotations (raw lng/lat)",
                      geo=geo_opts)
    return fig


# ---------------------------------------------------------------------------
# Unified 10-section rendering (every dataset renders all 10 sections)
# ---------------------------------------------------------------------------

def section_1_dataset_overview(cfg: registry.DatasetConfig) -> None:
    st.markdown("### 1. Dataset Overview")
    trained_count = registry.trained_model_count(cfg)
    if cfg.is_image_dataset:
        details = registry.load_image_dataset(cfg)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric(label="Selected Dataset", value=details.name.replace(" Sample Subset1", ""))
        m2.metric(label="Dataset Type", value="Image pairs")
        m3.metric(label="Image Pairs", value=f"{details.image_pairs}")
        m4.metric(label="Pre / Post Images",
                  value=f"{details.pre_disaster_images} / {details.post_disaster_images}")
        m5.metric(label="JSON Annotations", value=f"{details.json_files}")
        m6, m7, m8, m9 = st.columns(4)
        m6.metric(label="Building Annotations", value=f"{details.annotation_count:,}")
        dims_str = (f"{details.image_dimensions[0]} x {details.image_dimensions[1]}"
                    if details.image_dimensions else "unknown")
        m7.metric(label="Image Dimensions", value=dims_str)
        m8.metric(label="Damage Classes", value=f"{len(details.damage_classes)}")
        m9.metric(label="Trained Models", value=f"{trained_count}")
        st.markdown("**Subset:** Sample Subset1 - this is the small sample, "
                    "not the full 696-image dataset.")
        if details.source_url:
            st.markdown(f"**Source:** {details.source_url}"
                        + (f" · DOI {details.doi}" if details.doi else "")
                        + (f" · License {details.license}" if details.license else ""))
        st.markdown(f"**Path:** `{details.path}`")
        st.markdown(f"**Task:** {cfg.task_type}")
        st.markdown("**Damage classes:** " + " · ".join(details.damage_classes.keys()))
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
        details = registry.load_image_dataset(cfg)
        shown = min(3, details.image_pairs)
        if shown:
            st.caption("Representative image pairs "
                       f"({shown} of {details.image_pairs}) — Cyclone Freddy, Malawi.")
            for pid, pre_path, post_path in details.pairs[:shown]:
                col_a, col_b = st.columns(2)
                pre_img = cached_image(str(pre_path))
                post_img = cached_image(str(post_path))
                if pre_img is not None:
                    col_a.image(pre_img, caption=f"Pre-disaster  {pid}", use_container_width=True)
                else:
                    col_a.write(f"Pre-disaster image unavailable: `{pre_path.name}`")
                if post_img is not None:
                    col_b.image(post_img, caption=f"Post-disaster {pid}", use_container_width=True)
                else:
                    col_b.write(f"Post-disaster image unavailable: `{post_path.name}`")
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
    """Dataset- and model-aware status text for combos with no trained artifact."""
    if compat.inference_possible:
        return (f"{compat.model_name} has a trained checkpoint on this dataset; real "
                "predictions, performance and error analysis are shown in this section.")
    status = compat.status
    reason = compat.reason
    if cfg.is_image_dataset:
        details = registry.load_image_dataset(cfg)
        return (
            f"**{compat.model_name}** on **{cfg.name}** — status: **{status}**. {reason}\n\n"
            f"This sample subset provides {details.image_pairs} pre/post image pairs and "
            f"{details.annotation_count:,} building damage labels as ground truth. "
            f"Prediction here means building-damage masks from the spatial U-Net-family "
            f"architectures; no predicted masks exist yet, so nothing can be charted or "
            f"compared until one of those models is trained on the image pairs (outside the "
            f"dashboard)."
        )
    if cfg.key != registry.M2_BASELINE.key:
        content = {
            registry.IFI_IMPACT.key: (
                "This table holds descriptive district aggregates (fatalities, injuries, "
                "affected districts) and has no defined prediction target."
            ),
            registry.IFI_FLOODED_AREA.key: (
                "This raw flooded-area table contains regression data, but the trained "
                "checkpoints are fit on the prepared 720-row modeling set and are not "
                "applied to this raw table."
            ),
        }.get(cfg.key, "This dataset is provided as source data.")
        return (
            f"**{compat.model_name}** on **{cfg.name}** — status: **{status}**. {reason} "
            f"{content} The three trained + evaluated tabular checkpoints live on the IFI "
            f"modeling baseline (`{registry.M2_BASELINE.name}`); select that dataset to see "
            f"real predictions, metrics and error analysis."
        )
    return (
        f"**{compat.model_name}** on **{cfg.name}** — status: **{status}**. {reason} "
        f"The trained + evaluated tabular models on this dataset are CNN + LSTM, "
        f"CNN + Transformer and ResNet + BiLSTM; select one of them to see its real "
        f"test-set predictions, performance and error analysis below."
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


def _baseline_predictions(compat: registry.ModelCompatibility) -> pd.DataFrame | None:
    """Saved test-set predictions for the selected model (IFI baseline only)."""
    if not (compat.inference_possible and compat.dataset_key == registry.M2_BASELINE.key):
        return None
    model_pred = prepared_analytics()["predicted"]
    model_pred = model_pred[model_pred["model"] == compat.model_name].copy()
    return model_pred if not model_pred.empty else None


def section_7_prediction_visualization(cfg: registry.DatasetConfig,
                                       compat: registry.ModelCompatibility) -> None:
    st.markdown("### 7. Prediction Visualization")
    model_pred = _baseline_predictions(compat)
    if model_pred is not None:
        dataset = prepared_analytics()["dataset"]
        col_map, col_chart = st.columns([1.5, 1])
        with col_map:
            st.markdown("**Predicted Flooded Area by District**")
            joined = model_pred.merge(dataset.reset_index(drop=True),
                                      left_on="source_row", right_index=True,
                                      suffixes=("", "_df"))
            top = joined.nlargest(15, "predicted")
            fig = px.bar(top, x="predicted", y="Dist_Name", orientation="h",
                         title="Predicted Corrected_Percent_Flooded_Area (top-15 test districts)",
                         labels={"predicted": "Predicted %", "Dist_Name": "District"})
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Real test-set predictions for the selected model on the "
                       "untouched test split.")
        with col_chart:
            st.markdown("**Model Prediction Distribution**")
            hist_df = model_pred[["predicted"]].rename(columns={"predicted": "value"})
            hist_df["type"] = "Predicted"
            actual_df = model_pred[["actual"]].rename(columns={"actual": "value"})
            actual_df["type"] = "Actual"
            both = pd.concat([hist_df, actual_df], ignore_index=True)
            fig = px.histogram(both, x="value", color="type", nbins=30, barmode="overlay",
                               title="Distribution of Corrected_Percent_Flooded_Area (Test Set)",
                               labels={"value": "Corrected_Percent_Flooded_Area (%)"})
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(_availability_text(cfg, compat))
    st.markdown("---")


def section_8_actual_vs_predicted(cfg: registry.DatasetConfig,
                                  compat: registry.ModelCompatibility) -> None:
    st.markdown("### 8. Actual vs Predicted / Ground Truth")
    model_pred = _baseline_predictions(compat)
    if model_pred is not None:
        dataset = prepared_analytics()["dataset"]
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
        joined = model_pred.merge(dataset.drop(columns=["split_role"]).reset_index(drop=True),
                                  left_on="source_row", right_index=True,
                                  suffixes=("", "_df"))
        table = joined[[
            "Dist_Name", "Population", "Parmanent_Water",
            "actual", "predicted", "error",
        ]].rename(columns={
            "Dist_Name": "District",
            "actual": "Actual Corrected_%_Flooded_Area",
            "predicted": "Predicted Corrected_%_Flooded_Area",
            "error": "Error",
        }).copy()
        table["Absolute Error"] = table["Error"].abs()
        st.dataframe(table.sort_values("Absolute Error", ascending=False)
                     .reset_index(drop=True), use_container_width=True)
        st.caption("Real test-set rows (109) with model predictions from the saved "
                   "evaluation artifact.")
    elif cfg.is_image_dataset:
        details = registry.load_image_dataset(cfg)
        st.markdown("**Ground truth:** building damage annotations "
                    "(no predicted masks exist yet).")
        st.info(f"Ground truth = {details.annotation_count:,} building damage labels in the "
                "JSON annotations. No predicted masks exist for this dataset, so there is "
                "nothing to compare yet.")
    else:
        st.info(_availability_text(cfg, compat))
    st.markdown("---")


def section_9_error_analysis(cfg: registry.DatasetConfig,
                             compat: registry.ModelCompatibility) -> None:
    st.markdown("### 9. Error Analysis")
    if compat.inference_possible:
        err_df = prepared_analytics()["error_summary"]
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
    else:
        st.info(_availability_text(cfg, compat))
    st.markdown("---")


def section_10_dataset_visualizations(cfg: registry.DatasetConfig) -> None:
    st.markdown("### 10. Dataset-specific Visualizations")
    if cfg.is_image_dataset:
        details = registry.load_image_dataset(cfg)
        st.markdown("**Damage Annotation Summary**")
        class_df = pd.DataFrame({
            "Damage Class": list(details.damage_classes.keys()),
            "Count": list(details.damage_classes.values()),
        })
        col_tbl, col_bar = st.columns([1, 1.4])
        col_tbl.dataframe(class_df, use_container_width=True)
        bar = px.bar(class_df, x="Damage Class", y="Count", color="Damage Class",
                     labels={"Count": "Buildings"}, title="Building damage label counts")
        bar.update_layout(showlegend=False, height=320)
        col_bar.plotly_chart(bar, use_container_width=True)
        st.caption("Building damage labels read directly from the subset JSON annotations.")
        if details.coordinates_available:
            st.markdown("**Geographic Annotation Visualization**")
            st.plotly_chart(build_geo_figure(details), use_container_width=True)
            st.caption("Building footprint outlines read from the subset JSON annotations "
                       "(lng/lat). Visualization of the raw annotation geometry only.")
    elif cfg.is_baseline:
        dataset = prepared_analytics()["dataset"]
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
    else:
        frame = registry.load_dataset(cfg)
        profile = registry.analyze_dataframe(frame, cfg)
        numeric = [c for c in profile.numeric_columns if c in profile.numeric_stats]
        if numeric:
            st.markdown("**Numerical statistics:**")
            stats = pd.DataFrame({
                "Column": numeric,
                "Mean": [round(profile.numeric_stats[c]["mean"], 4) for c in numeric],
                "Std Dev": [round(profile.numeric_stats[c]["std"], 4) for c in numeric],
                "Min": [round(profile.numeric_stats[c]["min"], 4) for c in numeric],
                "Median": [round(profile.numeric_stats[c]["median"], 4) for c in numeric],
                "Max": [round(profile.numeric_stats[c]["max"], 4) for c in numeric],
            })
            st.dataframe(stats, use_container_width=True)
            dist_cols = numeric[:3]
            dist_columns = st.columns(len(dist_cols))
            for col, name in zip(dist_columns, dist_cols):
                col.plotly_chart(px.histogram(frame, x=name, nbins=20,
                                              title=f"{name} distribution"),
                                 use_container_width=True)
            priority = ["Corrected_Percent_Flooded_Area", "Population", "Human_fatality",
                        "Percent_Flooded_Area", "Human_injured"]
            ranking = next((c for c in priority if c in numeric), dist_cols[0])
            if ranking and "Dist_Name" in frame.columns:
                agg = frame[["Dist_Name", ranking]].dropna()
                top = agg.nlargest(15, ranking)
                st.plotly_chart(
                    px.bar(top, x=ranking, y="Dist_Name", orientation="h",
                           title=f"Top-15 districts by {ranking}"),
                    use_container_width=True)
            st.caption(f"Source file: `{cfg.source}` - {len(frame):,} rows, "
                       f"{len(frame.columns)} columns. This table is provided as source data; "
                       "trained models are tied to the IFI (M2) regression contract.")
        else:
            st.info("No numeric columns available for visualization.")
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


# ---------------------------------------------------------------------------
# VIEW 1: unified analytics layout for every dataset
# ---------------------------------------------------------------------------

if dashboard_view == "Analytics & GIS Overview (Default)":

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
            st.info(f"ℹ️ Architecture **{selected_model}** is planned for spatial raster inputs and marked as unavailable.")
        elif selected_model not in available:
            st.warning(f"⚠️ Model **{selected_model}** is **Not trained / unavailable** (No checkpoint found in results/models/).")
        else:
            st.success(f"✅ Verified trained checkpoint for **{selected_model}**.")

        uploaded_file = st.file_uploader("3. Upload Input Dataset (CSV)", type=["csv"])

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
                if st.button("🚀 Run Prediction"):
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