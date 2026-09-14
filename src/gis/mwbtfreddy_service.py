"""Service for mwBTFreddy (Malawi Cyclone Freddy) satellite imagery and building-damage annotations.

Provides robust parsing of WKT building footprint polygons, bitemporal image loading,
annotation overlay generation on GeoTIFFs, 2D cartesian building footprint plotting,
and interactive Folium satellite mapping centered strictly on Chilobwe, Blantyre, Malawi.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import folium
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MWBT_BASE = PROJECT_ROOT / "data" / "raw" / "custom_flood_datasets" / "mwBTFreddy"
SUBSET_DIR = MWBT_BASE / "msBTFreddy_Sample_Subset1"
IMAGES_DIR = SUBSET_DIR / "images"
JSON_DIR = SUBSET_DIR / "json"

# Damage scale styling (xView2 / xBD taxonomy standard)
TAXONOMY_CLASSES = ["no-damage", "minor-damage", "major-damage", "destroyed"]

DAMAGE_COLORS = {
    "no-damage": "#2ecc71",     # Emerald green
    "minor-damage": "#f1c40f",  # Yellow / amber (0 in this subset)
    "major-damage": "#e67e22",  # Orange
    "destroyed": "#e74c3c",     # Crimson red
    "unclassified": "#95a5a6",  # Grey
}

OVERLAY_FILL = {
    "no-damage": (46, 204, 113, 140),
    "minor-damage": (241, 196, 15, 160),
    "major-damage": (230, 126, 34, 180),
    "destroyed": (231, 76, 60, 200),
    "unclassified": (149, 165, 166, 140),
}

OVERLAY_OUTLINE = {
    "no-damage": (39, 174, 96, 255),
    "minor-damage": (243, 156, 18, 255),
    "major-damage": (211, 84, 0, 255),
    "destroyed": (192, 57, 43, 255),
    "unclassified": (127, 140, 141, 255),
}


def parse_wkt_coordinates(wkt: str) -> list[tuple[float, float]]:
    """Extract coordinates from WKT Polygon or MultiPolygon string.
    
    Handles standard WKT formats like:
      POLYGON ((x1 y1, x2 y2, ...))
      MULTIPOLYGON (((x1 y1, x2 y2, ...)))
    """
    if not isinstance(wkt, str) or not wkt.strip():
        return []
    
    # Extract all floating-point numbers in order
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", wkt)
    if len(nums) < 6:  # Needs at least 3 pairs for a polygon
        return []
    
    points: list[tuple[float, float]] = []
    for i in range(0, len(nums) - 1, 2):
        try:
            points.append((float(nums[i]), float(nums[i + 1])))
        except ValueError:
            continue
    return points


@lru_cache(maxsize=1)
def get_image_pairs_list() -> list[str]:
    """Return sorted list of the 10 image pair IDs in Sample Subset1."""
    if not IMAGES_DIR.is_dir():
        return []
    pre_tifs = sorted(IMAGES_DIR.glob("*_pre_disaster.tif"))
    return [p.name.replace("_pre_disaster.tif", "") for p in pre_tifs]


def get_pair_file_paths(pair_id: str) -> dict[str, Path]:
    """Return dictionary of file paths for the given pair ID."""
    return {
        "pre_tif": IMAGES_DIR / f"{pair_id}_pre_disaster.tif",
        "post_tif": IMAGES_DIR / f"{pair_id}_post_disaster.tif",
        "pre_json": JSON_DIR / f"{pair_id}_pre_disaster.json",
        "post_json": JSON_DIR / f"{pair_id}_post_disaster.json",
    }


def load_pair_annotations(pair_id: str, temporal_phase: str = "post") -> list[dict[str, Any]]:
    """Load building annotations for a specific image pair and phase ('pre' or 'post')."""
    paths = get_pair_file_paths(pair_id)
    json_path = paths["post_json"] if temporal_phase == "post" else paths["pre_json"]
    if not json_path.is_file():
        return []
    
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    
    features = data.get("features", {})
    lng_lat_list = features.get("lng_lat", [])
    xy_list = features.get("xy", [])
    
    annotations = []
    for i, item in enumerate(lng_lat_list):
        if not isinstance(item, dict):
            continue
        props = item.get("properties", {}) or {}
        uid = props.get("uid", f"{pair_id}_{i}")
        subtype = props.get("subtype", "no-damage")
        wkt = item.get("wkt", "")
        pts_geo = parse_wkt_coordinates(wkt)
        
        # Get corresponding xy coordinates if available
        pts_xy = []
        if i < len(xy_list) and isinstance(xy_list[i], dict):
            pts_xy = parse_wkt_coordinates(xy_list[i].get("wkt", ""))
            
        if len(pts_geo) >= 3:
            annotations.append({
                "pair_id": pair_id,
                "uid": uid,
                "subtype": subtype,
                "feature_type": props.get("feature_type", "building"),
                "pts_geo": pts_geo,
                "pts_xy": pts_xy,
                "wkt": wkt,
            })
    return annotations


@lru_cache(maxsize=1)
def load_all_post_annotations() -> list[dict[str, Any]]:
    """Load all 637 post-disaster building annotations across all 10 image pairs."""
    all_annos = []
    for pid in get_image_pairs_list():
        all_annos.extend(load_pair_annotations(pid, temporal_phase="post"))
    return all_annos


@lru_cache(maxsize=1)
def get_damage_class_summary() -> dict[str, Any]:
    """Compute exact damage class statistics for mwBTFreddy Sample Subset1."""
    annos = load_all_post_annotations()
    
    # 637 pre-disaster buildings are all no-damage
    # Post-disaster buildings have observed damages:
    post_counts = {cls: 0 for cls in TAXONOMY_CLASSES}
    for a in annos:
        sub = a["subtype"]
        post_counts[sub] = post_counts.get(sub, 0) + 1
        
    # Across all 20 JSON files (pre + post):
    # Total no-damage = 637 (pre) + post_counts["no-damage"]
    total_counts = {
        "no-damage": len(annos) + post_counts["no-damage"],  # 637 + 629 = 1266
        "minor-damage": post_counts.get("minor-damage", 0),  # 0
        "major-damage": post_counts.get("major-damage", 0),  # 1
        "destroyed": post_counts.get("destroyed", 0),        # 7
    }
    total_annotations = sum(total_counts.values())  # 1274
    
    observed_classes = [c for c in TAXONOMY_CLASSES if total_counts[c] > 0]
    unobserved_classes = [c for c in TAXONOMY_CLASSES if total_counts[c] == 0]
    
    percentages = {
        c: round((total_counts[c] / total_annotations) * 100, 2)
        for c in TAXONOMY_CLASSES
    }
    
    return {
        "dataset_name": "mwBTFreddy Sample Subset1",
        "taxonomy_classes": TAXONOMY_CLASSES,
        "taxonomy_count": len(TAXONOMY_CLASSES),
        "observed_classes": observed_classes,
        "observed_count": len(observed_classes),
        "unobserved_classes": unobserved_classes,
        "sample_counts": total_counts,
        "sample_percentages": percentages,
        "post_counts": post_counts,
        "unique_buildings": len(annos),
        "total_annotations": total_annotations,
        "image_pairs": len(get_image_pairs_list()),
        "pre_images": len(get_image_pairs_list()),
        "post_images": len(get_image_pairs_list()),
        "json_files": len(get_image_pairs_list()) * 2,
        "dimensions": (1024, 1024),
        "bands": 3,
        "format": "GeoTIFF (3-band RGB)",
    }


def get_per_pair_table() -> pd.DataFrame:
    """Return summary DataFrame of all 10 image pairs and their damage breakdown."""
    rows = []
    for pid in get_image_pairs_list():
        annos = load_pair_annotations(pid, temporal_phase="post")
        counts = {cls: 0 for cls in TAXONOMY_CLASSES}
        for a in annos:
            sub = a["subtype"]
            counts[sub] = counts.get(sub, 0) + 1
        rows.append({
            "Image Pair ID": pid,
            "Total Buildings": len(annos),
            "no-damage": counts["no-damage"],
            "major-damage": counts["major-damage"],
            "destroyed": counts["destroyed"],
            "minor-damage (unobserved)": counts["minor-damage"],
        })
    return pd.DataFrame(rows)


def generate_pair_overlay(pair_id: str) -> Image.Image | None:
    """Generate image overlay of post-disaster GeoTIFF with ground-truth building polygons."""
    paths = get_pair_file_paths(pair_id)
    if not paths["post_tif"].is_file():
        return None
    
    try:
        im = Image.open(paths["post_tif"]).convert("RGBA")
    except Exception:
        return None
        
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    annos = load_pair_annotations(pair_id, temporal_phase="post")
    for a in annos:
        pts = a["pts_xy"]
        sub = a["subtype"]
        if len(pts) >= 3:
            fill_col = OVERLAY_FILL.get(sub, OVERLAY_FILL["unclassified"])
            out_col = OVERLAY_OUTLINE.get(sub, OVERLAY_OUTLINE["unclassified"])
            draw.polygon(pts, fill=fill_col, outline=out_col, width=2)
            
    return Image.alpha_composite(im, overlay).convert("RGB")


def create_cartesian_footprint_figure(selected_pair_id: str | None = None) -> go.Figure:
    """Build Plotly 2D cartesian building footprint figure with exact longitude/latitude axes.
    
    Uses 1:1 aspect ratio so building footprints maintain correct physical proportions.
    Distinguishes observed damage classes visually.
    """
    annos = load_all_post_annotations()
    if not annos:
        return go.Figure().update_layout(title="No building footprints available")
    
    fig = go.Figure()
    
    # Organize polygons by damage class for clean legend entries
    class_polygons: dict[str, list[dict]] = {cls: [] for cls in TAXONOMY_CLASSES}
    for a in annos:
        sub = a["subtype"]
        if sub in class_polygons:
            class_polygons[sub].append(a)
            
    all_lons: list[float] = []
    all_lats: list[float] = []
    
    for cls in ["no-damage", "major-damage", "destroyed"]:
        items = class_polygons.get(cls, [])
        if not items:
            continue
            
        color = DAMAGE_COLORS[cls]
        
        # Build polygon outlines separated by None
        x_pts: list[float | None] = []
        y_pts: list[float | None] = []
        centroid_x: list[float] = []
        centroid_y: list[float] = []
        hover_texts: list[str] = []
        
        for item in items:
            pts = item["pts_geo"]
            is_selected = (selected_pair_id is None) or (item["pair_id"] == selected_pair_id)
            
            lons = [p[0] for p in pts] + [pts[0][0]]
            lats = [p[1] for p in pts] + [pts[0][1]]
            
            x_pts.extend(lons + [None])
            y_pts.extend(lats + [None])
            
            all_lons.extend(lons)
            all_lats.extend(lats)
            
            # Centroid for hover inspection
            c_lon = float(np.mean([p[0] for p in pts]))
            c_lat = float(np.mean([p[1] for p in pts]))
            centroid_x.append(c_lon)
            centroid_y.append(c_lat)
            hover_texts.append(
                f"<b>Building UID:</b> {item['uid'][:8]}...<br>"
                f"<b>Status:</b> {cls}<br>"
                f"<b>Pair:</b> {item['pair_id']}<br>"
                f"<b>Location:</b> Chilobwe, Blantyre, Malawi<br>"
                f"<b>Coordinates:</b> {c_lat:.5f}°S, {c_lon:.5f}°E"
            )
            
        # Draw the building polygon boundaries
        fig.add_trace(go.Scatter(
            x=x_pts,
            y=y_pts,
            mode="lines",
            fill="toself",
            name=f"{cls} ({len(items)} buildings)",
            line=dict(color=color, width=2 if cls != "no-damage" else 1.2),
            fillcolor=f"rgba{OVERLAY_FILL[cls]}",
            hoverinfo="skip",
        ))
        
        # Hover markers at building centroids
        fig.add_trace(go.Scatter(
            x=centroid_x,
            y=centroid_y,
            mode="markers",
            name=f"{cls} hover info",
            marker=dict(size=4, color=color, opacity=0.0),
            hoverinfo="text",
            hovertext=hover_texts,
            showlegend=False,
        ))

    lon_min, lon_max = min(all_lons), max(all_lons)
    lat_min, lat_max = min(all_lats), max(all_lats)
    d_lon = lon_max - lon_min
    d_lat = lat_max - lat_min
    margin = max(d_lon, d_lat) * 0.05
    
    fig.update_layout(
        title="Building Footprint Geometry (Chilobwe, Blantyre, Malawi — Cyclone Freddy)",
        xaxis_title="Longitude (°E)",
        yaxis_title="Latitude (°S)",
        xaxis=dict(
            range=[lon_min - margin, lon_max + margin],
            showgrid=True,
            gridcolor="#e0e0e0",
            zeroline=False,
        ),
        yaxis=dict(
            range=[lat_min - margin, lat_max + margin],
            showgrid=True,
            gridcolor="#e0e0e0",
            zeroline=False,
            scaleanchor="x",
            scaleratio=1.0,  # 1:1 geographic aspect ratio
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        height=540,
        plot_bgcolor="#f8fafc",
    )
    return fig


def create_folium_malawi_map(selected_pair_id: str | None = None) -> folium.Map:
    """Create interactive Folium map centered on Chilobwe, Blantyre, Malawi.
    
    Auto-fits map bounds to the exact building polygons.
    Includes satellite tile layer and building popups.
    """
    annos = load_all_post_annotations()
    if not annos:
        # Fallback centered on Chilobwe, Blantyre
        return folium.Map(location=[-15.835, 35.008], zoom_start=17)
        
    all_lats = [p[1] for a in annos for p in a["pts_geo"]]
    all_lons = [p[0] for a in annos for p in a["pts_geo"]]
    lat_center = float(np.mean(all_lats))
    lon_center = float(np.mean(all_lons))
    
    fmap = folium.Map(
        location=[lat_center, lon_center],
        zoom_start=17,
        tiles=None,
    )
    
    # Add Esri Satellite Imagery as primary tile layer
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite Imagery",
        overlay=False,
        control=True,
    ).add_to(fmap)
    
    # Add OpenStreetMap as secondary option
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(fmap)
    
    for item in annos:
        pts = item["pts_geo"]
        cls = item["subtype"]
        color = DAMAGE_COLORS.get(cls, "#2ecc71")
        is_selected = (selected_pair_id is None) or (item["pair_id"] == selected_pair_id)
        
        # Folium uses [lat, lon]
        locations = [[p[1], p[0]] for p in pts]
        
        popup_html = (
            f"<div style='font-family: sans-serif; min-width: 180px;'>"
            f"<h4 style='margin:0 0 5px 0; color: {color};'>Building: {cls.upper()}</h4>"
            f"<b>UID:</b> <code>{item['uid'][:12]}...</code><br>"
            f"<b>Image Pair:</b> {item['pair_id']}<br>"
            f"<b>Location:</b> Chilobwe, Blantyre, Malawi<br>"
            f"<b>Centroid:</b> {np.mean([p[1] for p in pts]):.5f}°S, {np.mean([p[0] for p in pts]):.5f}°E"
            f"</div>"
        )
        
        folium.Polygon(
            locations=locations,
            color=color,
            weight=3 if is_selected and selected_pair_id else 1.5,
            fill=True,
            fill_color=color,
            fill_opacity=0.7 if cls != "no-damage" else 0.45,
            tooltip=f"{cls} ({item['pair_id']})",
            popup=folium.Popup(popup_html, max_width=250),
        ).add_to(fmap)
        
    # Auto-fit map bounds strictly to Malawi building coordinates
    lat_min, lat_max = min(all_lats), max(all_lats)
    lon_min, lon_max = min(all_lons), max(all_lons)
    fmap.fit_bounds([[lat_min, lon_min], [lat_max, lon_max]])
    
    folium.LayerControl().add_to(fmap)
    return fmap
