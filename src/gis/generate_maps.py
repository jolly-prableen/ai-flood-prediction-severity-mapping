"""GIS scaffold for actual flooded-area regression predictions."""
from __future__ import annotations

from pathlib import Path

import folium
import geopandas as gpd
import pandas as pd


def generate_interactive_prediction_map(geojson_path, predictions_csv_path, output_html_path):
    """Render actual regression predictions only when a validated join key exists.

    The prediction CSV must contain ``district_lgd_code`` and
    ``predicted_corrected_percent_flooded_area``. No probability conversion or
    segmentation interpretation is performed.
    """
    geojson = Path(geojson_path)
    predictions = Path(predictions_csv_path)
    if not geojson.exists() or not predictions.exists():
        raise FileNotFoundError("Validated geometry and prediction files are required")
    geometry = gpd.read_file(geojson)
    values = pd.read_csv(predictions)
    required = {"district_lgd_code", "predicted_corrected_percent_flooded_area"}
    missing = required - set(values.columns)
    if missing:
        raise ValueError(f"INCOMPATIBLE: missing GIS columns {sorted(missing)}")
    if "district_lgd_code" not in geometry.columns:
        raise ValueError("INCOMPATIBLE: geometry has no validated district_lgd_code join key")
    merged = geometry.merge(values, on="district_lgd_code", how="left", validate="one_to_one")
    if merged.empty:
        raise ValueError("INCOMPATIBLE: geographic join produced no rows")
    center = merged.geometry.union_all().centroid
    map_view = folium.Map(location=[center.y, center.x], zoom_start=6, tiles="cartodbpositron")
    folium.GeoJson(
        merged,
        style_function=lambda feature: {
            "fillColor": "#3182bd" if feature["properties"].get("predicted_corrected_percent_flooded_area") is not None else "#bdbdbd",
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.6,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["district_lgd_code", "predicted_corrected_percent_flooded_area"],
            aliases=["District LGD code:", "Predicted corrected flooded area:"],
        ),
    ).add_to(map_view)
    output = Path(output_html_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    map_view.save(output)
