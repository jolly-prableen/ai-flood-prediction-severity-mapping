import sys
import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import st_folium

# Connect to backend API module
sys.path.append(os.path.abspath("src"))
import backend_api as api

st.set_page_config(
    page_title="AI Flood Early Warning Dashboard",
    layout="wide",
    page_icon="??"
)

# ---------------------------------------------------------
# SIDEBAR: MODE SELECTION & CONTROLS
# ---------------------------------------------------------
st.sidebar.title("Dashboard Controls")

dashboard_view = st.sidebar.radio(
    "Select View Mode",
    ["Analytics & GIS Overview (Default)", "Custom Prediction & Retraining Mode"]
)

st.sidebar.markdown("---")

# ---------------------------------------------------------
# VIEW 1: DEFAULT RICH ANALYTICS & GIS OVERVIEW
# ---------------------------------------------------------
if dashboard_view == "Analytics & GIS Overview (Default)":
    st.sidebar.subheader("Controls & Filters")
    selected_state = st.sidebar.selectbox("Select State", ["All States", "Assam", "Bihar", "Kerala"])
    alert_threshold = st.sidebar.slider("Alert Probability Threshold", 0.0, 1.0, 0.60, 0.05)

    st.title("AI-Powered Flood Early Warning Dashboard")
    st.caption("Real-time risk assessment, probability analytics, and spatial warnings.")

    # KPI Metrics Row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(label="High Risk Districts", value="14", delta="2 from yesterday", delta_color="inverse")
    with kpi2:
        st.metric(label="Avg Flood Probability", value="42.8%", delta="-1.5%")
    with kpi3:
        st.metric(label="Peak Rainfall (24h)", value="184 mm", delta="32 mm", delta_color="inverse")
    with kpi4:
        st.metric(label="Active Model Version", value="XGBoost v1.2")

    st.markdown("---")

    # Main Grid: GIS Map & Probability Distribution
    col_map, col_chart = st.columns([1.5, 1])

    with col_map:
        st.subheader("Spatial Risk & Probability Map")
        
        m = folium.Map(location=[26.2006, 92.9376], zoom_start=7, tiles="OpenStreetMap")
        
        districts = [
            {"name": "Guwahati", "lat": 26.1445, "lon": 91.7362, "prob": 0.88},
            {"name": "Silchar", "lat": 24.8333, "lon": 92.7789, "prob": 0.81},
            {"name": "Tezpur", "lat": 26.6333, "lon": 92.8000, "prob": 0.54},
            {"name": "Jorhat", "lat": 26.7500, "lon": 94.2167, "prob": 0.38},
            {"name": "Dhubri", "lat": 26.0167, "lon": 89.9833, "prob": 0.22},
        ]

        for d in districts:
            color = "red" if d["prob"] >= alert_threshold else "orange" if d["prob"] >= 0.4 else "green"
            folium.CircleMarker(
                location=[d["lat"], d["lon"]],
                radius=10,
                popup=f"<b>{d['name']}</b><br>Probability: {d['prob']*100:.1f}%",
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7
            ).add_to(m)

        st_folium(m, width="100%", height=380)

    with col_chart:
        st.subheader("Probability & Risk Distribution")
        chart_data = pd.DataFrame({
            "District": ["Guwahati", "Silchar", "Tezpur", "Jorhat", "Dhubri"],
            "Probability": [0.88, 0.81, 0.54, 0.38, 0.22]
        }).sort_values("Probability", ascending=True)

        fig_bar = px.bar(
            chart_data,
            x="Probability",
            y="District",
            orientation="h",
            color="Probability",
            color_continuous_scale="Reds",
            title="Top At-Risk Districts Probability Score"
        )
        fig_bar.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # Bottom Grid: Feature Importance & Baseline Performance Comparison
    col_feat, col_metrics = st.columns([1, 1])

    with col_feat:
        st.subheader("Model Explanations & Feature Importance")
        feat_df = pd.DataFrame({
            "Feature": ["3-Day Cumulative Rainfall", "Soil Moisture Index", "River Discharge Rate", "Elevation Slope", "Vegetation Cover (NDVI)"],
            "Importance": [0.42, 0.25, 0.18, 0.11, 0.06]
        }).sort_values("Importance", ascending=True)

        fig_feat = px.bar(
            feat_df,
            x="Importance",
            y="Feature",
            orientation="h",
            color="Importance",
            color_continuous_scale="Viridis",
            title="Top Contributing Features to Flood Alert"
        )
        fig_feat.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_feat, use_container_width=True)

    with col_metrics:
        st.subheader("Baseline Performance Metrics Comparison")
        metrics_df = pd.DataFrame({
            "Model": ["LogisticRegression", "RandomForest", "XGBoost"],
            "Accuracy": [0.8100, 0.8800, 0.9100],
            "Precision": [0.7800, 0.8500, 0.8800],
            "Recall": [0.8400, 0.8900, 0.9300],
            "ROC-AUC": [0.8500, 0.9200, 0.9500]
        })
        st.dataframe(metrics_df.style.highlight_max(axis=0, color="#FFFF99"), use_container_width=True)

# ---------------------------------------------------------
# VIEW 2: CUSTOM PREDICTION & MODEL RETRAIN WORKFLOW
# ---------------------------------------------------------
else:
    st.title("API-Driven Model Execution Engine")
    
    sub_mode = st.radio("Select Execution Workflow", ["Inference / Prediction Mode", "Model Retraining Mode"], horizontal=True)
    all_models = ["U-Net + ConvLSTM", "CNN + LSTM", "CNN + Transformer", "ResNet + BiLSTM", "Attention U-Net + LSTM"]

    if sub_mode == "Inference / Prediction Mode":
        st.subheader("Run Model Inference on Custom Dataset")
        
        c1, c2 = st.columns(2)
        with c1:
            selected_model = st.selectbox("1. Select Model Architecture", all_models)
        with c2:
            selected_task = st.selectbox("2. Target Task", api.get_supported_tasks())

        trained_models = api.get_available_models()
        if selected_model not in trained_models:
            st.warning(f"Checkpoint for **{selected_model}** not found in results/checkpoints/.")
            st.info("Pipeline status: Waiting for Member 2 model checkpoints.")
        else:
            st.success(f"Checkpoint verified for **{selected_model}**.")

        uploaded_file = st.file_uploader("3. Upload Input Dataset (CSV)", type=["csv"])

        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            
            with st.expander("Inspect Uploaded Dataset"):
                st.json(api.inspect_dataset(df))
                st.dataframe(df.head())

            mapped_df, mapping_applied = api.adapt_dataset(df, selected_model, selected_task)
            compat = api.check_compatibility(mapped_df, selected_model, selected_task)

            st.subheader("Column Mapping & Compatibility Analysis")
            if mapping_applied:
                st.info("Auto-mapped column aliases:")
                st.json(mapping_applied)

            for warn in compat["warnings"]:
                st.warning(warn)

            if compat["is_compatible"]:
                st.success("Dataset features are COMPATIBLE.")
                if st.button("Run Prediction"):
                    res = api.predict_uploaded_dataset(df, selected_model, selected_task)
                    out_df = mapped_df.copy()
                    out_df["Probability"] = res["probabilities"]
                    out_df["Prediction"] = res["predictions"]
                    if "severities" in res:
                        out_df["Severity"] = res["severities"]

                    st.subheader("Output Prediction Table")
                    st.dataframe(out_df)
                    fig = px.histogram(out_df, x="Probability", color="Prediction", title="Risk Probability Distribution")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Dataset INCOMPATIBLE. Prediction blocked.")
                st.write("**Missing Required Features:**")
                st.json(compat["missing_features"])

    else:
        st.subheader("Model Retraining Pipeline")
        retrain_model_name = st.selectbox("Select Model to Train", all_models)
        retrain_task = st.selectbox("Select Task", api.get_supported_tasks())
        train_file = st.file_uploader("Upload Training Data (CSV)", type=["csv"], key="train_up")

        epochs = st.number_input("Epochs", min_value=1, max_value=100, value=10)
        learning_rate = st.selectbox("Learning Rate", [0.001, 0.0001, 0.01])

        if train_file is not None and st.button("Execute Retraining"):
            train_df = pd.read_csv(train_file)
            res = api.retrain_model(train_df, retrain_model_name, retrain_task, {"epochs": epochs, "lr": learning_rate})
            st.success(res["message"])
            st.json(res["metrics"])
