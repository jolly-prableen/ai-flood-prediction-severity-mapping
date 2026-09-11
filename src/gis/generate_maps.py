import os
import folium
import geopandas as gpd
import pandas as pd


def generate_interactive_alert_map(geojson_path, predictions_csv_path, output_html_path):
    """
    Combines GeoJSON geometry with flood probability predictions to output an interactive Folium map.
    """
    if not os.path.exists(geojson_path) or not os.path.exists(predictions_csv_path):
        print("Missing GeoJSON or predictions file. Script ready for integration.")
        return

    gdf = gpd.read_file(geojson_path)
    preds = pd.read_csv(predictions_csv_path)

    # Merge spatial data with model outputs
    merged = gdf.merge(preds, on="district_lgd_code", how="left")

    # Center map on spatial bounds
    centroid = merged.geometry.unary_union.centroid
    m = folium.Map(location=[centroid.y, centroid.x], zoom_start=7, tiles="cartodbpositron")

    def get_color(prob):
        if pd.isna(prob):
            return "gray"
        elif prob >= 0.7:
            return "red"      # High Alert
        elif prob >= 0.4:
            return "orange"   # Medium Alert
        else:
            return "green"    # Low Risk

    folium.GeoJson(
        merged,
        style_function=lambda feature: {
            'fillColor': get_color(feature['properties'].get('flood_probability')),
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.6
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['district', 'flood_probability'],
            aliases=['District:', 'Flood Prob:'],
            localize=True
        )
    ).add_to(m)

    os.makedirs(os.path.dirname(output_html_path), exist_ok=True)
    m.save(output_html_path)
    print(f"Interactive alert map saved to {output_html_path}")


if __name__ == "__main__":
    print("GIS map generation module ready.")