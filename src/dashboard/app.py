import sys
import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import st_folium

sys.path.append(os.path.abspath("src"))
import backend_api as api

st.set_page_config(
    page_title="AI Flood Early Warning Dashboard",
    layout="wide",
    page_icon="🌊"
)

st.sidebar.title("Dashboard Controls")
dashboard_view = st.sidebar.radio(
    "Select View Mode",
    ["Analytics & GIS Overview (Default)", "Custom Prediction & Retraining Mode"]
)
st.sidebar.markdown("---")

# VIEW 1: DEFAULT ANALYTICS
if dashboard_view == "Analytics & GIS Overview (Default)":
    st.sidebar.subheader("Controls & Filters")
    alert_threshold = st.sidebar.slider("Alert Probability Threshold", 0.0, 1.0, 0.60, 0.05)

    st.title("AI-Powered Flood Early Warning Dashboard")
    st.caption("Real-time risk assessment, spatial warnings, and model performance metrics.")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(label="High Risk Districts", value="14", delta="2 from yesterday", delta_color="inverse")
    with kpi2:
        st.metric(label="Avg Flood Probability", value="42.8%", delta="-1.5%")
    with kpi3:
        st.metric(label="Peak Rainfall (24h)", value="184 mm", delta="32 mm", delta_color="inverse")
    with kpi4:
        st.metric(label="Available Trained Models", value=f"{len(api.get_available_models())} / 3")

    st.markdown("---")

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
                color=color, fill=True, fill_color=color, fill_opacity=0.7
            ).add_to(m)
        st_folium(m, width="100%", height=380)

    with col_chart:
        st.subheader("Probability & Risk Distribution")
        chart_data = pd.DataFrame({
            "District": ["Guwahati", "Silchar", "Tezpur", "Jorhat", "Dhubri"],
            "Probability": [0.88, 0.81, 0.54, 0.38, 0.22]
        }).sort_values("Probability", ascending=True)
        fig_bar = px.bar(chart_data, x="Probability", y="District", orientation="h", color="Probability", color_continuous_scale="Reds")
        fig_bar.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    col_feat, col_metrics = st.columns([1, 1])
    with col_feat:
        st.subheader("Current Baseline Features")
        feat_df = pd.DataFrame({
            "Feature": ["Population", "Parmanent_Water"],
            "Role": ["Demographic Impact Metric", "Hydrological Surface Metric"]
        })
        st.dataframe(feat_df, use_container_width=True)

    with col_metrics:
        st.subheader("Trained Model Performance Metrics")
        metrics_df = api.get_model_metrics()
        if not metrics_df.empty:
            st.dataframe(metrics_df, use_container_width=True)
        else:
            st.info("No saved model metrics found in `results/models/` yet.")

# VIEW 2: EXECUTION ENGINE
else:
    st.title("API-Driven Model Execution Engine")
    sub_mode = st.radio("Select Execution Workflow", ["Inference / Prediction Mode", "Model Retraining Mode"], horizontal=True)
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
            compat = api.check_compatibility(mapped_df, selected_model, selected_task)

            st.subheader("Schema Compatibility Analysis")
            if mapping_applied:
                st.info("Auto-mapped column aliases:")
                st.json(mapping_applied)

            for warn in compat["warnings"]:
                st.warning(warn)

            if compat["is_compatible"]:
                st.success("✅ Dataset features are COMPATIBLE.")
                if st.button("🚀 Run Prediction"):
                    try:
                        res = api.predict_uploaded_dataset(mapped_df, selected_model, selected_task)
                        out_df = mapped_df.copy()
                        out_df["Probability"] = res["probabilities"]
                        out_df["Prediction"] = res["predictions"]
                        st.subheader("Output Prediction Table")
                        st.dataframe(out_df)
                    except Exception as e:
                        st.error(f"Inference Error: {str(e)}")
            else:
                st.error("❌ Dataset INCOMPATIBLE. Prediction blocked.")
                if compat["missing_features"]:
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
