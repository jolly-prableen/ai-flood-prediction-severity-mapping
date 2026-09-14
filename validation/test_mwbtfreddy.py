"""Validation tests for mwBTFreddy (Malawi Cyclone Freddy) dataset and visualizations.

Verifies:
1. Robust WKT polygon/multipolygon coordinate parsing
2. Correct longitude/latitude ordering and Malawi bounding box
3. Taxonomy (4 classes) vs. observed damage classes (3 classes)
4. Exact Sample Subset1 counts (10 pairs, 20 JSONs, 1,274 annotations)
5. Pre/post GeoTIFF image loading and band properties
6. Annotation overlay generation with building polygons
7. 2D cartesian building footprint figure rendering with 1:1 aspect ratio
8. Interactive Folium Malawi satellite map with auto-zoom and bounds fitting
9. Absolute separation from Indian Census district polygons and IFI models
10. Absence of misleading regression metrics for image models
"""
from __future__ import annotations

import sys
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from src.gis import mwbtfreddy_service as mws
from src.datasets import registry
from src.config.model_registry import (
    get_model_record,
    STATUS_TRAINING_REQUIRED,
    STATUS_INCOMPATIBLE,
    SPATIAL_MODELS,
    TABULAR_MODELS,
)
from src.gis.flood_risk_service import get_descriptive_gis_data


def test_wkt_geometry_parsing():
    """Verify robust WKT parsing of Polygon and MultiPolygon coordinate strings."""
    wkt_poly = "POLYGON ((35.008 -15.835, 35.009 -15.835, 35.009 -15.836, 35.008 -15.836, 35.008 -15.835))"
    pts = mws.parse_wkt_coordinates(wkt_poly)
    assert len(pts) == 5
    assert pts[0] == (35.008, -15.835)
    assert pts[1] == (35.009, -15.835)

    wkt_multi = (
        "MULTIPOLYGON (((35.008 -15.835, 35.009 -15.835, 35.008 -15.835)), "
        "((35.010 -15.836, 35.011 -15.836, 35.010 -15.836)))"
    )
    pts_multi = mws.parse_wkt_coordinates(wkt_multi)
    assert len(pts_multi) == 6


def test_sample_subset_counts():
    """Verify exact Sample Subset1 counts across all 20 JSON files and 20 GeoTIFFs."""
    summary = mws.get_damage_class_summary()
    assert summary["dataset_name"] == "mwBTFreddy Sample Subset1"
    assert summary["image_pairs"] == 10
    assert summary["pre_images"] == 10
    assert summary["post_images"] == 10
    assert summary["json_files"] == 20
    assert summary["total_annotations"] == 1274
    assert summary["unique_buildings"] == 637
    assert summary["dimensions"] == (1024, 1024)
    assert summary["bands"] == 3


def test_damage_class_accounting():
    """Verify taxonomy classes (4) vs. observed classes (3) in Sample Subset1."""
    summary = mws.get_damage_class_summary()
    assert summary["taxonomy_count"] == 4
    assert summary["taxonomy_classes"] == ["no-damage", "minor-damage", "major-damage", "destroyed"]

    assert summary["observed_count"] == 3
    assert set(summary["observed_classes"]) == {"no-damage", "major-damage", "destroyed"}
    assert "minor-damage" in summary["unobserved_classes"]

    counts = summary["sample_counts"]
    assert counts["no-damage"] == 1266
    assert counts["major-damage"] == 1
    assert counts["destroyed"] == 7
    assert counts["minor-damage"] == 0

    post_counts = summary["post_counts"]
    assert post_counts["no-damage"] == 629
    assert post_counts["major-damage"] == 1
    assert post_counts["destroyed"] == 7
    assert sum(post_counts.values()) == 637


def test_coordinate_ranges_and_ordering():
    """Verify coordinate structure, longitude/latitude ordering, and Malawi location bounds."""
    annos = mws.load_all_post_annotations()
    assert len(annos) == 637

    for a in annos:
        pts = a["pts_geo"]
        assert len(pts) >= 3, f"Building {a['uid']} has invalid polygon vertex count"
        for p in pts:
            lon, lat = p[0], p[1]
            # Longitude in Chilobwe, Blantyre, Malawi (~35.006 to 35.011 °E)
            assert 35.00 <= lon <= 35.02, f"Longitude out of Malawi range: {lon}"
            # Latitude in Chilobwe, Blantyre, Malawi (~ -15.838 to -15.831 °S)
            assert -15.85 <= lat <= -15.82, f"Latitude out of Malawi range: {lat}"


def test_pre_and_post_image_loading():
    """Verify that all 10 bitemporal GeoTIFF pairs load with RGB bands."""
    pairs = mws.get_image_pairs_list()
    assert len(pairs) == 10

    for pid in pairs:
        paths = mws.get_pair_file_paths(pid)
        assert paths["pre_tif"].is_file(), f"Missing pre GeoTIFF: {paths['pre_tif']}"
        assert paths["post_tif"].is_file(), f"Missing post GeoTIFF: {paths['post_tif']}"

        with Image.open(paths["pre_tif"]) as pre_img:
            assert pre_img.size == (1024, 1024)
            assert pre_img.mode == "RGB"

        with Image.open(paths["post_tif"]) as post_img:
            assert post_img.size == (1024, 1024)
            assert post_img.mode == "RGB"


def test_annotation_overlay_generation():
    """Verify that annotation overlay generates a valid composite RGB image."""
    overlay = mws.generate_pair_overlay("malawi-cyclone_00000058")
    assert overlay is not None
    assert overlay.size == (1024, 1024)
    assert overlay.mode == "RGB"


def test_cartesian_footprint_figure():
    """Verify 2D cartesian footprint figure has labelled axes and 1:1 aspect ratio."""
    fig = mws.create_cartesian_footprint_figure()
    assert fig is not None
    assert len(fig.data) > 0

    layout = fig.layout
    assert "Longitude" in layout.xaxis.title.text
    assert "Latitude" in layout.yaxis.title.text
    assert layout.yaxis.scaleanchor == "x"
    assert layout.yaxis.scaleratio == 1.0


def test_folium_malawi_map():
    """Verify interactive Folium map is centered on Malawi and auto-fits bounds."""
    fmap = mws.create_folium_malawi_map()
    assert fmap is not None

    # Check location center is around Malawi coordinates
    assert -16.0 <= fmap.location[0] <= -15.0
    assert 34.5 <= fmap.location[1] <= 35.5

    # Check HTML representation includes Esri tile layer and Chilobwe
    html = fmap.get_root().render()
    assert "ArcGIS" in html or "World_Imagery" in html or "esri" in html.lower()
    assert "Chilobwe" in html or "Blantyre" in html or "Malawi" in html


def test_no_indian_census_geometry_for_mwbt():
    """Verify mwBTFreddy never loads or uses Indian Census district GIS data."""
    gis_data = get_descriptive_gis_data("mwbtfreddy")
    assert gis_data is None


def test_model_compatibility_rules():
    """Verify model compatibility rules for tabular vs spatial models on mwBTFreddy."""
    cfg = registry.MWBTFREDDY

    for model_name in registry.MODEL_NAMES:
        compat = registry.model_compatibility(cfg, model_name)
        rec = get_model_record(cfg.key, model_name)

        assert not compat.inference_possible
        assert rec.checkpoint_path is None
        assert rec.predictions_path is None
        assert rec.metrics is None

        if model_name in SPATIAL_MODELS:
            assert compat.status == STATUS_TRAINING_REQUIRED
            assert "u-net" in compat.architecture.lower()
            assert "spatial" in rec.architecture.lower()
            assert "building damage" in compat.target_task.lower()
        else:
            assert compat.status == STATUS_INCOMPATIBLE
            assert model_name in TABULAR_MODELS
            assert "incompatible" in compat.reason.lower()


def test_no_regression_metrics_for_mwbt():
    """Verify that no trained regression metrics are returned for mwBTFreddy."""
    trained = registry.trained_metrics(registry.MWBTFREDDY)
    assert trained == {}
