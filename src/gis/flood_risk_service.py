"""Flood Risk Visualization Service for district-level regression models.

Research-inspired capability adapted from integrated flood-response platforms
and risk visualization literature (e.g., AlleyFloodNet, Lee & Joo, Electronics 2025).

Derives model-based flood risk categories (LOW, MODERATE, HIGH, VERY HIGH)
from evaluated test predictions and aligns them with verified Census 2011 district
boundaries using existing project artifacts without generating fake data.
"""
from functools import lru_cache
import json
import re
from pathlib import Path
from typing import Any

import folium
import numpy as np
import pandas as pd
import shapefile

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_CSV = PROJECT_ROOT / "data" / "processed" / "district_flood_area_regression.csv"
ACTUAL_VS_PREDICTED_CSV = PROJECT_ROOT / "results" / "evaluation" / "actual_vs_predicted.csv"
SHAPEFILE_PATH = PROJECT_ROOT / "data" / "external" / "boundaries" / "raw" / "2011_Dist.shp"

RISK_COLORS = {
    "LOW": "#2ecc71",        # Emerald green
    "MODERATE": "#f1c40f",   # Amber / yellow
    "HIGH": "#e67e22",       # Orange
    "VERY HIGH": "#e74c3c",  # Crimson red
}

CATEGORY_ORDER = ["LOW", "MODERATE", "HIGH", "VERY HIGH"]


def normalize_name(val: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(val).casefold())


def compute_risk_thresholds(predictions: np.ndarray) -> dict[str, float]:
    """Calculate deterministic quantile thresholds: 25th, 50th (median), 75th percentiles."""
    q25, q50, q75 = np.percentile(predictions, [25, 50, 75])
    return {
        "q25": float(q25),
        "q50": float(q50),
        "q75": float(q75),
        "min": float(predictions.min()),
        "max": float(predictions.max()),
    }


def assign_risk_category(val: float, thresholds: dict[str, float]) -> str:
    """Categorize prediction value into LOW, MODERATE, HIGH, VERY HIGH."""
    if val <= thresholds["q25"]:
        return "LOW"
    elif val <= thresholds["q50"]:
        return "MODERATE"
    elif val <= thresholds["q75"]:
        return "HIGH"
    else:
        return "VERY HIGH"


@lru_cache(maxsize=4)
def load_shapefile_geometries(shp_path: Path = SHAPEFILE_PATH) -> dict[str, dict[str, Any]]:
    """Load Census 2011 boundaries by normalized district name."""
    if not shp_path.is_file():
        return {}
    reader = shapefile.Reader(str(shp_path))
    fields = [f[0] for f in reader.fields if f[0] != "DeletionFlag"]
    shp_dict: dict[str, dict[str, Any]] = {}
    for sr in reader.shapeRecords():
        rec = dict(zip(fields, sr.record))
        norm_key = normalize_name(rec.get("DISTRICT", ""))
        shp_dict[norm_key] = {
            "record": rec,
            "district": str(rec.get("DISTRICT", "")),
            "state": str(rec.get("ST_NM", "")),
            "censuscode": int(rec.get("censuscode", 0)),
            "geometry": sr.shape.__geo_interface__,
        }
    return shp_dict


def get_model_flood_risk_data(
    model_name: str,
    project_root: Path = PROJECT_ROOT,
    dataset_id: str = "ifi_v3",
) -> dict[str, Any] | None:
    """Prepare complete flood risk visualization data for the given model architecture and dataset."""
    from src.config.dataset_registry import get_dataset, load_dataset_data
    from src.config.model_registry import get_model_record

    try:
        record = get_model_record(dataset_id, model_name)
    except KeyError:
        return None

    if not record.has_predictions or not record.predictions_path or not record.predictions_path.is_file():
        return None

    try:
        ds_rec = get_dataset(dataset_id)
    except KeyError:
        return None

    if not ds_rec.has_gis:
        return None

    dataset = load_dataset_data(dataset_id)
    if dataset is None or dataset.empty:
        return None

    shp_path = project_root / "data" / "external" / "boundaries" / "raw" / "2011_Dist.shp"
    preds_df = pd.read_csv(record.predictions_path)
    sub_preds = preds_df[preds_df["model"] == model_name].copy()
    if sub_preds.empty:
        return None

    merged = sub_preds.merge(dataset.reset_index(drop=True), left_on="source_row", right_index=True)
    if merged.empty:
        return None

    pred_vals = merged["predicted"].to_numpy(dtype=float)
    thresholds = compute_risk_thresholds(pred_vals)

    # Assign risk categories
    merged["risk_category"] = [assign_risk_category(p, thresholds) for p in pred_vals]
    merged["color"] = [RISK_COLORS[c] for c in merged["risk_category"]]

    # Category counts
    category_counts = {cat: int((merged["risk_category"] == cat).sum()) for cat in CATEGORY_ORDER}

    # Outlier / peak info
    dist_col = ds_rec.district_column if ds_rec.district_column in merged.columns else "Dist_Name"
    max_idx = int(np.argmax(pred_vals))
    peak_row = merged.iloc[max_idx]
    peak_info = {
        "district": str(peak_row[dist_col]),
        "district_name": str(peak_row[dist_col]),
        "predicted": float(peak_row["predicted"]),
        "predicted_flooded_percent": float(peak_row["predicted"]),
        "risk_category": str(peak_row["risk_category"]),
        "actual": float(peak_row["actual"]),
    }

    # Load boundaries
    boundaries = load_shapefile_geometries(shp_path)

    features = []
    mapped_districts = []
    unmapped_districts = []

    for _, row in merged.iterrows():
        dname = str(row[dist_col])
        norm_key = normalize_name(dname)
        raw_pred = float(row["predicted"])
        raw_actual = float(row["actual"])
        pred_val = round(raw_pred, 3)
        actual_val = round(raw_actual, 3)
        risk_cat = str(row["risk_category"])
        color = RISK_COLORS[risk_cat]

        dist_record = {
            "district": dname,
            "district_name": dname,
            "predicted": raw_pred,
            "predicted_flooded_percent": raw_pred,
            "actual": raw_actual,
            "risk_category": risk_cat,
            "model": model_name,
            "model_name": model_name,
            "population": int(row["Population"]) if "Population" in row and pd.notna(row["Population"]) else 0,
            "permanent_water": float(row["Parmanent_Water"]) if "Parmanent_Water" in row and pd.notna(row["Parmanent_Water"]) else 0.0,
        }

        if norm_key in boundaries:
            b_info = boundaries[norm_key]
            dist_record["censuscode"] = b_info["censuscode"]
            dist_record["district_id"] = str(b_info["censuscode"])
            dist_record["state"] = b_info["state"]
            dist_record["is_mapped"] = True
            dist_record["has_geometry"] = True
            mapped_districts.append(dist_record)

            features.append({
                "type": "Feature",
                "geometry": b_info["geometry"],
                "properties": {
                    "district": dname,
                    "district_name": dname,
                    "district_id": str(b_info["censuscode"]),
                    "censuscode": b_info["censuscode"],
                    "state": b_info["state"],
                    "predicted": pred_val,
                    "actual": actual_val,
                    "risk_category": risk_cat,
                    "model": model_name,
                    "color": color,
                },
            })
        else:
            dist_record["censuscode"] = None
            dist_record["district_id"] = f"ROW-{row['source_row']}"
            dist_record["state"] = "Unmapped"
            dist_record["is_mapped"] = False
            dist_record["has_geometry"] = False
            unmapped_districts.append(dist_record)

    geojson_data = {
        "type": "FeatureCollection",
        "features": features,
    }

    return {
        "model": model_name,
        "model_name": model_name,
        "thresholds": thresholds,
        "category_counts": category_counts,
        "peak_district": peak_info,
        "geojson": geojson_data,
        "mapped_count": len(mapped_districts),
        "unmapped_count": len(unmapped_districts),
        "total_count": len(merged),
        "mapped_districts": mapped_districts,
        "unmapped_districts": unmapped_districts,
        "all_districts": mapped_districts + unmapped_districts,
        "all_districts_df": merged,
    }


def compute_feature_bounds(features: list[dict[str, Any]]) -> list[list[float]] | None:
    """Extract [[min_lat, min_lon], [max_lat, max_lon]] bounding box from GeoJSON features."""
    if not features:
        return None
    min_lat, min_lon = 90.0, 180.0
    max_lat, max_lon = -90.0, -180.0

    def extract_pts(c: Any):
        if isinstance(c, (list, tuple)) and len(c) >= 2 and isinstance(c[0], (int, float)):
            yield c[0], c[1]
        elif isinstance(c, (list, tuple)):
            for sub in c:
                yield from extract_pts(sub)

    for feat in features:
        geom = feat.get("geometry")
        if not geom:
            continue
        coords = geom.get("coordinates", [])
        for lon, lat in extract_pts(coords):
            min_lon = min(min_lon, float(lon))
            max_lon = max(max_lon, float(lon))
            min_lat = min(min_lat, float(lat))
            max_lat = max(max_lat, float(lat))

    if min_lat < max_lat and min_lon < max_lon:
        return [[min_lat, min_lon], [max_lat, max_lon]]
    return None


def create_folium_risk_map(risk_data: dict[str, Any]) -> folium.Map:
    """Build an interactive Folium choropleth map for model-predicted flood risk with auto-zoom."""
    geojson = risk_data["geojson"]
    features = geojson.get("features", [])
    bounds = compute_feature_bounds(features)

    # Initial center (falls back to India centroid if bounds unavailable)
    map_center = [22.8, 79.5]
    if bounds:
        map_center = [(bounds[0][0] + bounds[1][0]) / 2.0, (bounds[0][1] + bounds[1][1]) / 2.0]

    map_view = folium.Map(
        location=map_center,
        zoom_start=5,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    if features:
        folium.GeoJson(
            geojson,
            name="District Risk Polygons",
            style_function=lambda f: {
                "fillColor": f["properties"]["color"],
                "color": "#2c3e50",
                "weight": 1.2,
                "fillOpacity": 0.72,
            },
            highlight_function=lambda f: {
                "weight": 3,
                "color": "#000000",
                "fillOpacity": 0.9,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["district", "risk_category", "predicted", "censuscode"],
                aliases=["District:", "Model Risk Category:", "Predicted Flooded Area (%):", "Census 2011 Code:"],
                style="background-color: white; color: #333; font-family: sans-serif; font-size: 12px; padding: 10px;",
            ),
            popup=folium.GeoJsonPopup(
                fields=["district", "risk_category", "predicted", "actual", "state"],
                aliases=["District:", "Risk Category:", "Predicted Flooded Area (%):", "Actual Flooded Area (%):", "State:"],
            ),
        ).add_to(map_view)

        # Auto-zoom tightly to district boundaries
        if bounds:
            map_view.fit_bounds(bounds)

    return map_view


# Sequential color palettes for descriptive variables
DESCRIPTIVE_PALETTE = [
    "#eff3ff",  # Tier 1 (Lowest)
    "#bdd7e7",  # Tier 2
    "#6baed6",  # Tier 3
    "#2171b5",  # Tier 4 (Highest)
]


@lru_cache(maxsize=16)
def get_descriptive_gis_data(
    dataset_id: str,
    variable_name: str | None = None,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any] | None:
    """Prepare descriptive district GIS data for datasets without predictive models."""
    from src.config.dataset_registry import get_dataset, load_dataset_data

    try:
        ds_rec = get_dataset(dataset_id)
    except KeyError:
        return None

    if ds_rec.is_image_dataset or not ds_rec.has_gis:
        return None

    df = load_dataset_data(dataset_id)
    if df is None or df.empty or ds_rec.district_column not in df.columns:
        return None

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if not numeric_cols:
        return None

    if not variable_name or variable_name not in numeric_cols:
        variable_name = numeric_cols[0]

    clean_df = df.dropna(subset=[ds_rec.district_column, variable_name]).copy()
    vals = clean_df[variable_name].to_numpy(dtype=float)
    if len(vals) == 0:
        return None

    q25, q50, q75 = np.percentile(vals, [25, 50, 75])
    thresholds = {
        "min": float(vals.min()),
        "q25": float(q25),
        "q50": float(q50),
        "q75": float(q75),
        "max": float(vals.max()),
    }

    def assign_tier(val: float) -> tuple[str, str]:
        if val <= thresholds["q25"]:
            return "Tier 1 (Low)", DESCRIPTIVE_PALETTE[0]
        elif val <= thresholds["q50"]:
            return "Tier 2 (Moderate)", DESCRIPTIVE_PALETTE[1]
        elif val <= thresholds["q75"]:
            return "Tier 3 (High)", DESCRIPTIVE_PALETTE[2]
        else:
            return "Tier 4 (Very High)", DESCRIPTIVE_PALETTE[3]

    shp_path = project_root / "data" / "external" / "boundaries" / "raw" / "2011_Dist.shp"
    boundaries = load_shapefile_geometries(shp_path)

    features = []
    mapped_districts = []
    unmapped_districts = []

    for _, row in clean_df.iterrows():
        dname = str(row[ds_rec.district_column])
        norm_key = normalize_name(dname)
        val = float(row[variable_name])
        tier_name, color = assign_tier(val)

        dist_record = {
            "district": dname,
            "district_name": dname,
            "variable_name": variable_name,
            "value": val,
            "tier": tier_name,
            "color": color,
        }

        if norm_key in boundaries:
            b_info = boundaries[norm_key]
            dist_record["censuscode"] = b_info["censuscode"]
            dist_record["state"] = b_info["state"]
            dist_record["is_mapped"] = True
            dist_record["has_geometry"] = True
            mapped_districts.append(dist_record)

            features.append({
                "type": "Feature",
                "geometry": b_info["geometry"],
                "properties": {
                    "district": dname,
                    "censuscode": b_info["censuscode"],
                    "state": b_info["state"],
                    "variable_name": variable_name,
                    "value": round(val, 3),
                    "tier": tier_name,
                    "color": color,
                },
            })
        else:
            dist_record["censuscode"] = None
            dist_record["state"] = "Unmapped"
            dist_record["is_mapped"] = False
            dist_record["has_geometry"] = False
            unmapped_districts.append(dist_record)

    geojson_data = {
        "type": "FeatureCollection",
        "features": features,
    }

    # Summary peak
    max_idx = int(np.argmax(vals))
    peak_row = clean_df.iloc[max_idx]
    peak_info = {
        "district": str(peak_row[ds_rec.district_column]),
        "value": float(peak_row[variable_name]),
        "variable_name": variable_name,
    }

    return {
        "dataset_id": dataset_id,
        "dataset_name": ds_rec.display_name,
        "variable_name": variable_name,
        "available_variables": numeric_cols,
        "thresholds": thresholds,
        "peak_district": peak_info,
        "geojson": geojson_data,
        "mapped_count": len(mapped_districts),
        "unmapped_count": len(unmapped_districts),
        "total_count": len(clean_df),
        "mapped_districts": mapped_districts,
        "unmapped_districts": unmapped_districts,
        "all_districts": mapped_districts + unmapped_districts,
    }


def create_folium_descriptive_map(desc_data: dict[str, Any]) -> folium.Map:
    """Build an interactive Folium choropleth map for descriptive district variables with auto-zoom."""
    geojson = desc_data["geojson"]
    features = geojson.get("features", [])
    bounds = compute_feature_bounds(features)
    var_name = desc_data["variable_name"]

    map_center = [22.8, 79.5]
    if bounds:
        map_center = [(bounds[0][0] + bounds[1][0]) / 2.0, (bounds[0][1] + bounds[1][1]) / 2.0]

    map_view = folium.Map(
        location=map_center,
        zoom_start=5,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    if features:
        folium.GeoJson(
            geojson,
            name="District Overview Polygons",
            style_function=lambda f: {
                "fillColor": f["properties"]["color"],
                "color": "#333333",
                "weight": 1.1,
                "fillOpacity": 0.70,
            },
            highlight_function=lambda f: {
                "weight": 2.5,
                "color": "#000000",
                "fillOpacity": 0.9,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["district", "state", "variable_name", "value", "censuscode"],
                aliases=["District:", "State:", "Variable:", "Value:", "Census Code:"],
                style="background-color: white; color: #333; font-family: sans-serif; font-size: 12px; padding: 8px;",
            ),
            popup=folium.GeoJsonPopup(
                fields=["district", "state", "variable_name", "value", "tier", "censuscode"],
                aliases=["District:", "State:", "Variable:", "Value:", "Tier:", "Census Code:"],
            ),
        ).add_to(map_view)

        if bounds:
            map_view.fit_bounds(bounds)

    return map_view
