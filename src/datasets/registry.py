"""Dataset registry and adapter layer for the project dashboard.

Each dataset is described by a :class:`DatasetConfig` (static contract). Tabular
datasets are profiled from their actual CSV files. The mwBTFreddy image dataset
is described from its own ``manifest.json`` paired with a real on-disk scan of
images and JSON annotations, so no counts are hard-coded.

The five fixed project outputs are reported in one of three states:

* ``SUPPORTED``                     - a real trained artifact produces this output.
* ``AVAILABLE DATA / NO TRAINED MODEL`` - source data exists, no trained model yet.
* ``NOT CURRENTLY AVAILABLE``       - neither data nor trained model.

No values are ever fabricated: every number shown comes from a real file scan,
a manifest, or the M2 evaluation artifacts.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Five fixed project output categories.
FLOOD_OUTPUTS = [
    "Flood Probability",
    "Flood Extent",
    "Flood Severity",
    "GIS Visualization",
    "Warning",
]

STATUS_SUPPORTED = "SUPPORTED"
STATUS_AVAILABLE_DATA = "AVAILABLE DATA / NO TRAINED MODEL"
STATUS_NOT_AVAILABLE = "NOT CURRENTLY AVAILABLE"

# ---------------------------------------------------------------------------
# Five project model architectures (fixed catalog)
# ---------------------------------------------------------------------------

MODEL_NAMES = [
    "U-Net + ConvLSTM",
    "CNN + LSTM",
    "CNN + Transformer",
    "ResNet + BiLSTM",
    "Attention U-Net + LSTM",
]

# Kebab-case directory names under results/models used by the trained artifacts.
LOGICAL_MODEL_DIRS = {
    "U-Net + ConvLSTM": "unet_convlstm",
    "CNN + LSTM": "cnn_lstm",
    "CNN + Transformer": "cnn_transformer",
    "ResNet + BiLSTM": "resnet_bilstm",
    "Attention U-Net + LSTM": "attention_unet_lstm",
}

# Architectures that consume spatial raster sequences (image pair datasets).
SPATIAL_MODELS = {"U-Net + ConvLSTM", "Attention U-Net + LSTM"}

# Architectures that consume per-district feature tables (tabular datasets).
DISTRIBUTION_MODELS = {"CNN + LSTM", "CNN + Transformer", "ResNet + BiLSTM"}

# The three architectures with real trained checkpoints on the IFI M2 baseline.
TRAINED_IFI_MODELS = frozenset(DISTRIBUTION_MODELS)

MODEL_STATUS_TRAINED_EVALUATED = "TRAINED + EVALUATED"
MODEL_STATUS_TRAINED = "TRAINED"
MODEL_STATUS_TRAINING_REQUIRED = "IMPLEMENTED / TRAINING REQUIRED"
MODEL_STATUS_INCOMPATIBLE = "INCOMPATIBLE WITH CURRENT DATA"


@dataclass(frozen=True)
class ModelSpec:
    """Static contract for one of the five project model architectures."""

    name: str
    architecture: str
    input_type: str
    supported_tasks: tuple[str, ...]
    implementation: str


MODEL_CATALOG: dict[str, ModelSpec] = {
    "U-Net + ConvLSTM": ModelSpec(
        name="U-Net + ConvLSTM",
        architecture="U-Net encoder/decoder with a ConvLSTM temporal cell",
        input_type="spatial raster sequence (batch, time, channels, height, width)",
        supported_tasks=("spatial segmentation / building damage classification (imagery)",),
        implementation="src/models/unet_convlstm/model.py",
    ),
    "CNN + LSTM": ModelSpec(
        name="CNN + LSTM",
        architecture="CNN feature extraction followed by an LSTM sequence model",
        input_type="tabular feature sequence (batch, time, features)",
        supported_tasks=("district flooded-area regression",),
        implementation="src/models/cnn_lstm/model.py",
    ),
    "CNN + Transformer": ModelSpec(
        name="CNN + Transformer",
        architecture="CNN feature extraction with sinusoidal positional encoding "
                     "and a Transformer encoder",
        input_type="tabular feature sequence (batch, time, features)",
        supported_tasks=("district flooded-area regression",),
        implementation="src/models/cnn_transformer/model.py",
    ),
    "ResNet + BiLSTM": ModelSpec(
        name="ResNet + BiLSTM",
        architecture="1-D ResNet stem/blocks feeding a bidirectional LSTM",
        input_type="tabular feature sequence (batch, time, features)",
        supported_tasks=("district flooded-area regression",),
        implementation="src/models/resnet_bilstm/model.py",
    ),
    "Attention U-Net + LSTM": ModelSpec(
        name="Attention U-Net + LSTM",
        architecture="Attention U-Net decoder over LSTM-temporally-pooled spatial features",
        input_type="spatial raster sequence (batch, time, channels, height, width)",
        supported_tasks=("spatial segmentation / building damage classification (imagery)",),
        implementation="src/models/attention_unet_lstm/model.py",
    ),
}


@dataclass(frozen=True)
class OutputAvailability:
    """Availability of a single fixed project output for a dataset."""

    status: str
    detail: str = ""


def available(status: str, detail: str = "") -> OutputAvailability:
    """Shorthand constructor for an :class:`OutputAvailability` entry."""
    return OutputAvailability(status=status, detail=detail)


@dataclass
class DatasetConfig:
    """Static contract for a known dataset."""

    key: str
    name: str
    source: str
    path: Path
    dataset_type: str = "tabular"
    input_features: list[str] = field(default_factory=list)
    target: str | None = None
    target_type: str | None = None            # "continuous" | "categorical"
    task_type: str | None = None              # "regression" | "classification" | "event_log" | "descriptive" | "building damage classification"
    spatial_fields: list[str] = field(default_factory=list)
    temporal_fields: list[str] = field(default_factory=list)
    output_support: dict[str, OutputAvailability] = field(default_factory=dict)
    model_status: str = "no trained model"
    source_url: str = ""
    description: str = ""
    is_baseline: bool = False
    related_sources: dict[str, Path] = field(default_factory=dict)

    @property
    def relative_path(self) -> str:
        try:
            return self.path.relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            return str(self.path)

    @property
    def exists(self) -> bool:
        return self.path.exists()

    @property
    def is_image_dataset(self) -> bool:
        return self.dataset_type.startswith("image")


# ---------------------------------------------------------------------------
# Known datasets
# ---------------------------------------------------------------------------

# IFI v3 / M2 baseline (prepared modeling dataset, trained models exist).
M2_BASELINE = DatasetConfig(
    key="ifi_v3",
    name="India Flood Inventory v3 (IFI / M2 Baseline)",
    source="data/processed/district_flood_area_regression.csv",
    path=PROJECT_ROOT / "data" / "processed" / "district_flood_area_regression.csv",
    dataset_type="tabular (regression)",
    input_features=["Population", "Parmanent_Water"],
    target="Corrected_Percent_Flooded_Area",
    target_type="continuous",
    task_type="district flooded-area regression",
    spatial_fields=["Dist_Name", "district_key"],
    temporal_fields=[],
    model_status="trained",
    is_baseline=True,
    related_sources={
        "Original IFI inventory (raw)": PROJECT_ROOT / "data" / "raw" / "India_Flood_Inventory_v3.csv",
    },
    output_support={
        "Flood Probability": available(
            STATUS_NOT_AVAILABLE,
            "Trained models output continuous flooded-area regression "
            "(Corrected_Percent_Flooded_Area); no classification or probability output exists.",
        ),
        "Flood Extent": available(
            STATUS_SUPPORTED,
            "Real trained M2 models (CNN + LSTM, CNN + Transformer, ResNet + BiLSTM) predict "
            "Corrected_Percent_Flooded_Area on the prepared dataset.",
        ),
        "Flood Severity": available(
            STATUS_NOT_AVAILABLE,
            "No severity/damage target exists in the prepared modeling dataset.",
        ),
        "GIS Visualization": available(
            STATUS_NOT_AVAILABLE,
            "Modeling dataset has only district names; no coordinates or boundary geometry.",
        ),
        "Warning": available(
            STATUS_NOT_AVAILABLE,
            "No validated risk-threshold warning rule is defined for the regression output.",
        ),
    },
    description=(
        "Current Member 2 baseline: 720 district rows with Population and Parmanent_Water as "
        "input features and Corrected_Percent_Flooded_Area as the regression target. Real "
        "checkpoints exist for CNN + LSTM, CNN + Transformer and ResNet + BiLSTM."
    ),
)

# IFI raw event inventory (descriptive; related source of M2_BASELINE).
IFI_INVENTORY = DatasetConfig(
    key="ifi_inventory",
    name="India Flood Inventory v3 (IFI-Impacts raw)",
    source="data/raw/India_Flood_Inventory_v3.csv",
    path=PROJECT_ROOT / "data" / "raw" / "India_Flood_Inventory_v3.csv",
    dataset_type="tabular (event log)",
    input_features=[],
    target=None,
    target_type=None,
    task_type="historical flood event log",
    spatial_fields=["Districts", "State", "District_LGD_Codes", "State_Codes",
                    "Latitude", "Longitude"],
    temporal_fields=["Start Date", "End Date", "Duration(Days)"],
    model_status="no trained model",
    output_support={
        "Flood Probability": available(
            STATUS_NOT_AVAILABLE,
            "Historical flood event log; no classification target, forecast setup or "
            "probability label exists.",
        ),
        "Flood Extent": available(
            STATUS_NOT_AVAILABLE,
            "Area Affected is fully missing (6876/6876 null); no flooded-area measurement.",
        ),
        "Flood Severity": available(
            STATUS_NOT_AVAILABLE,
            "Severity is fully missing (6876/6876 null); no verified severity/damage target.",
        ),
        "GIS Visualization": available(
            STATUS_NOT_AVAILABLE,
            "Latitude/Longitude are fully missing; no valid coordinates. Administrative name "
            "fields exist but no boundary geometry.",
        ),
        "Warning": available(
            STATUS_NOT_AVAILABLE,
            "Historical descriptive records with no prediction/risk rule.",
        ),
    },
    description=(
        "IFI-Impacts v3 flood event inventory (6876 events, 1967-2020). Each row is a historical "
        "flood event with timing fields, affected districts/states and impact outcomes. Used for "
        "provenance and descriptive analytics, not as a predictive training set."
    ),
)

# IFI district impact aggregates (descriptive tabular).
IFI_IMPACT = DatasetConfig(
    key="ifi_impact",
    name="District Flood Impact (IFI district aggregates)",
    source="data/raw/District_FloodImpact.csv",
    path=PROJECT_ROOT / "data" / "raw" / "District_FloodImpact.csv",
    dataset_type="tabular (descriptive)",
    input_features=[],
    target=None,
    target_type=None,
    task_type="descriptive district aggregates",
    spatial_fields=["Dist_Name"],
    temporal_fields=[],
    model_status="no trained model",
    output_support={
        "Flood Probability": available(
            STATUS_NOT_AVAILABLE,
            "No classification target or probability output.",
        ),
        "Flood Extent": available(
            STATUS_NOT_AVAILABLE,
            "No flooded-area measurement; table holds population, fatality/injury counts and "
            "mean flood duration only.",
        ),
        "Flood Severity": available(
            STATUS_NOT_AVAILABLE,
            "Raw post-event fatality/injury counts exist but require a verified severity "
            "target-creation rubric before use; none is defined.",
        ),
        "GIS Visualization": available(
            STATUS_NOT_AVAILABLE,
            "Only district names; no coordinates or boundary geometry.",
        ),
        "Warning": available(
            STATUS_NOT_AVAILABLE,
            "Descriptive district aggregates with no prediction/risk rule.",
        ),
    },
    description=(
        "IFI district-level impact aggregates (732 districts): Population, Human_fatality, "
        "Human_injured and Mean_Flood_Duration. Descriptive reference data; no prediction target "
        "is defined."
    ),
)

# IFI district flooded-area aggregates (tabular with regression data present).
IFI_FLOODED_AREA = DatasetConfig(
    key="ifi_flooded_area",
    name="District Flooded Area (IFI district aggregates)",
    source="data/raw/District_FloodedArea.csv",
    path=PROJECT_ROOT / "data" / "raw" / "District_FloodedArea.csv",
    dataset_type="tabular (regression data)",
    input_features=["Parmanent_Water"],
    target="Corrected_Percent_Flooded_Area",
    target_type="continuous",
    task_type="district flooded-area regression (data only)",
    spatial_fields=["Dist_Name"],
    temporal_fields=[],
    model_status="no trained model",
    output_support={
        "Flood Probability": available(
            STATUS_NOT_AVAILABLE,
            "Continuous flooded-area target only; no probability output.",
        ),
        "Flood Extent": available(
            STATUS_AVAILABLE_DATA,
            "Corrected_Percent_Flooded_Area target data is present, but the trained M2 models "
            "require the prepared 720-row dataset (Population + Parmanent_Water) and are not "
            "run on this raw 732-row table.",
        ),
        "Flood Severity": available(
            STATUS_NOT_AVAILABLE,
            "No severity/damage target exists.",
        ),
        "GIS Visualization": available(
            STATUS_NOT_AVAILABLE,
            "Only district names; no coordinates or boundary geometry.",
        ),
        "Warning": available(
            STATUS_NOT_AVAILABLE,
            "No validated risk-threshold warning rule.",
        ),
    },
    description=(
        "IFI district flooded-area aggregates (732 districts): Percent_Flooded_Area, "
        "Parmanent_Water and Corrected_Percent_Flooded_Area. Source of the M2 regression target."
    ),
)

# mwBTFreddy Sample Subset1 (satellite image pair + building damage annotations).
MWBTFREDDY = DatasetConfig(
    key="mwbtfreddy",
    name="mwBTFreddy Sample Subset1",
    source="data/raw/custom_flood_datasets/mwBTFreddy",
    path=PROJECT_ROOT / "data" / "raw" / "custom_flood_datasets" / "mwBTFreddy",
    dataset_type="image pair (raster + annotations)",
    input_features=[],
    target=None,
    target_type="categorical (building damage)",
    task_type="building damage classification (imagery)",
    spatial_fields=["lng_lat building polygons"],
    temporal_fields=["pre/post disaster pair"],
    model_status="no trained model",
    output_support={
        "Flood Probability": available(
            STATUS_NOT_AVAILABLE,
            "Building damage classification dataset; no flood probability target or trained model.",
        ),
        "Flood Extent": available(
            STATUS_NOT_AVAILABLE,
            "Annotations are building-level damage labels; no flooded-area extent measurement.",
        ),
        "Flood Severity": available(
            STATUS_AVAILABLE_DATA,
            "Building damage annotations are present (no-damage / major-damage / destroyed). "
            "No model is trained on this dataset.",
        ),
        "GIS Visualization": available(
            STATUS_AVAILABLE_DATA,
            "Building footprints with lng/lat coordinates are present and can be rendered.",
        ),
        "Warning": available(
            STATUS_NOT_AVAILABLE,
            "No validated risk/threshold warning rule is defined.",
        ),
    },
    description=(
        "Sample Subset1 of the mwBTFreddy building damage dataset: 10 pre/post Cyclone Freddy "
        "satellite image pairs (Malawi) with 1274 building damage annotations. This is the small "
        "sample subset, not the full 696-image dataset. Model training/evaluation is not "
        "currently available for this dataset."
    ),
)

DATASETS: list[DatasetConfig] = [
    M2_BASELINE,
    IFI_IMPACT,
    IFI_FLOODED_AREA,
    MWBTFREDDY,
]

# IFI_INVENTORY is a related source of M2_BASELINE, not a separate selector option.
DATASET_BY_KEY: dict[str, DatasetConfig] = {cfg.key: cfg for cfg in DATASETS}


def available_datasets() -> list[DatasetConfig]:
    """Registered datasets whose source actually exists on disk (for the selector)."""
    return [cfg for cfg in DATASETS if cfg.exists]


# ---------------------------------------------------------------------------
# Tabular loading + profiling
# ---------------------------------------------------------------------------

_DATE_WORDS = ("date", "_at", "time", "year", "month", "day", "start", "end", "duration")
_GEO_WORDS = ("lat", "lon", "longitude", "latitude", "district", "state", "code", "geo", "coordinate")
_TARGET_WORDS = ("corrected", "percent", "flooded", "affected", "severity", "damaged",
                 "label", "class", "target", "binary", "probability", "flood")


def load_dataset(config: DatasetConfig, path: str | Path | None = None) -> pd.DataFrame:
    """Load a registered tabular dataset as a DataFrame."""
    target = Path(path) if path else config.path
    return pd.read_csv(target)


def is_datetime_series(series: pd.Series) -> bool:
    if series.dtype.kind in "biufc":
        return False
    sample = series.dropna().head(50)
    if sample.empty:
        return False
    try:
        parsed = pd.to_datetime(sample, errors="coerce")
    except (ValueError, TypeError, OverflowError):
        return False
    return parsed.notna().mean() >= 0.8


def detect_geographic_columns(df: pd.DataFrame) -> list[str]:
    return [str(col) for col in df.columns
            if any(w in str(col).lower().replace(" ", "_") for w in _GEO_WORDS)]


def detect_temporal_columns(df: pd.DataFrame) -> list[str]:
    return [str(col) for col in df.columns
            if any(w in str(col).lower().replace(" ", "_") for w in _DATE_WORDS)
            and is_datetime_series(df[col])]


def detect_possible_targets(df: pd.DataFrame) -> list[str]:
    """Heuristic candidate targets (reporting only; not an invented contract)."""
    return [str(col) for col in df.columns
            if any(w in str(col).lower().replace(" ", "_") for w in _TARGET_WORDS)]


def has_valid_coordinates(df: pd.DataFrame, cols: list[str]) -> bool:
    lat = next((c for c in cols if "lat" in str(c).lower()), None)
    lon = next((c for c in cols if ("lon" in str(c).lower() or "long" in str(c).lower())), None)
    if lat is None or lon is None:
        return False
    return df[lat].notna().any() and df[lon].notna().any()


@dataclass
class DatasetProfile:
    key: str
    name: str
    source: str
    path: str | None
    rows: int
    columns: int
    column_names: list[str]
    dtypes: dict[str, str]
    missing_counts: dict[str, int]
    missing_pct: dict[str, float]
    numeric_columns: list[str]
    categorical_columns: list[str]
    datetime_columns: list[str]
    geographic_columns: list[str]
    temporal_columns: list[str]
    valid_coordinates: bool
    possible_targets: list[str]
    input_features: list[str]
    target: str | None
    target_type: str | None
    task_type: str | None
    output_support: dict[str, OutputAvailability]
    description: str
    numeric_stats: dict[str, dict[str, float]]
    dataset_type: str = ""
    model_status: str = "no trained model"
    is_baseline: bool = False

    def output_status(self, output: str) -> OutputAvailability:
        return self.output_support.get(output, available(STATUS_NOT_AVAILABLE, ""))


def analyze_dataframe(df: pd.DataFrame, config: DatasetConfig | None = None,
                      data_name: str | None = None) -> DatasetProfile:
    """Build a profile from a real DataFrame, using the config contract when known."""
    if config is None:
        config = DatasetConfig(
            key="custom_csv",
            name=data_name or "Custom uploaded CSV",
            source="uploaded CSV",
            path=PROJECT_ROOT / "data" / "raw" / "custom_flood_datasets" / (data_name or "custom.csv"),
        )

    df = df.copy()
    for col in df.columns:
        if df[col].dtype.kind not in "biufc":
            df[col] = df[col].astype(str)

    numeric = [str(c) for c in df.columns if df[c].dtype.kind in "biufc"]
    categorical = [str(c) for c in df.columns
                   if df[c].dtype.kind in "OUSV"
                   or (df[c].dtype.kind in "biufc" and df[c].nunique() <= 20)]
    datetime_cols = [str(c) for c in df.columns
                     if pd.api.types.is_datetime64_any_dtype(df[c])
                     or (df[c].dtype.kind == "O" and is_datetime_series(df[c]))]
    geo_cols = detect_geographic_columns(df)
    temporal_cols = detect_temporal_columns(df)

    missing_counts = {str(c): int(df[c].isna().sum()) for c in df.columns}
    missing_pct = {str(c): float(df[c].isna().mean() * 100) for c in df.columns}
    dtypes = {str(c): str(df[c].dtype) for c in df.columns}
    numeric_stats = {
        str(c): {"mean": float(df[c].mean()), "std": float(df[c].std()),
                 "min": float(df[c].min()), "max": float(df[c].max()),
                 "median": float(df[c].median())}
        for c in df.columns if df[c].dtype.kind in "biufc" and df[c].notna().any()
    }

    possible_targets = config.target and [config.target] or detect_possible_targets(df)

    output_support = dict(config.output_support)
    if not output_support:
        output_support = infer_output_support(df, geo_cols, temporal_cols)

    return DatasetProfile(
        key=config.key,
        name=config.name,
        source=config.source,
        path=config.relative_path,
        rows=len(df),
        columns=len(df.columns),
        column_names=[str(c) for c in df.columns],
        dtypes=dtypes,
        missing_counts=missing_counts,
        missing_pct=missing_pct,
        numeric_columns=numeric,
        categorical_columns=categorical,
        datetime_columns=datetime_cols,
        geographic_columns=geo_cols,
        temporal_columns=temporal_cols,
        valid_coordinates=has_valid_coordinates(df, geo_cols),
        possible_targets=possible_targets,
        input_features=list(config.input_features),
        target=config.target,
        target_type=config.target_type,
        task_type=config.task_type,
        output_support=output_support,
        description=config.description,
        numeric_stats=numeric_stats,
        dataset_type=config.dataset_type,
        model_status=config.model_status,
        is_baseline=config.is_baseline,
    )


def infer_output_support(df: pd.DataFrame, geo_cols: list[str],
                         temporal_cols: list[str]) -> dict[str, OutputAvailability]:
    """Best-effort output availability for an unknown uploaded dataset."""
    binary_like = [c for c in df.columns if df[c].nunique() == 2 and df[c].dtype.kind in "biufc"]
    has_extent = any(any(w in str(c).lower() for w in ("flooded", "flood", "water", "mask"))
                     for c in df.columns)
    has_severity = any(any(w in str(c).lower() for w in ("severity", "damage", "damaged"))
                       for c in df.columns)
    return {
        "Flood Probability": available(
            STATUS_AVAILABLE_DATA if binary_like else STATUS_NOT_AVAILABLE,
            "No binary classification field detected." if not binary_like else
            "Binary classification field detected; no trained model exists for uploads.",
        ),
        "Flood Extent": available(
            STATUS_AVAILABLE_DATA if has_extent else STATUS_NOT_AVAILABLE,
            "No flooded-area/segment field detected." if not has_extent else
            "Flooded-area/segment field detected; no trained model exists for uploads.",
        ),
        "Flood Severity": available(
            STATUS_AVAILABLE_DATA if has_severity else STATUS_NOT_AVAILABLE,
            "No severity/damage field detected." if not has_severity else
            "Severity/damage field detected; no trained model exists for uploads.",
        ),
        "GIS Visualization": available(
            STATUS_AVAILABLE_DATA if has_valid_coordinates(df, geo_cols) else STATUS_NOT_AVAILABLE,
            "No valid coordinates detected." if not has_valid_coordinates(df, geo_cols)
            else "Valid coordinates present; no rendering pipeline for uploads.",
        ),
        "Warning": available(
            STATUS_NOT_AVAILABLE,
            "No validated prediction/risk rule is defined for uploads.",
        ),
    }


# ---------------------------------------------------------------------------
# mwBTFreddy image dataset (manifest + on-disk scan)
# ---------------------------------------------------------------------------


@dataclass
class ImageDatasetDetails:
    name: str
    source_url: str
    doi: str
    license: str
    version: str
    path: str
    description: str
    image_pairs: int
    pre_disaster_images: int
    post_disaster_images: int
    image_files: int
    json_files: int
    image_dimensions: tuple[int, int] | None
    annotation_count: int
    damage_classes: dict[str, int]
    polygon_count: int
    coordinates_available: bool
    sample_polygons: list[dict]
    pairs: list[tuple[str, Path, Path]]
    model_status: str
    output_support: dict[str, OutputAvailability]
    is_full_dataset: bool = False


def parse_polygon_wkt(wkt: str) -> list[tuple[float, float]]:
    """Extract the exterior ring of a ``POLYGON ((lon lat, ...))`` WKT string."""
    if not isinstance(wkt, str) or not wkt.strip().upper().startswith("POLYGON"):
        return []
    match = re.search(r"\(\(([^()]*)\)", wkt)
    if not match:
        return []
    points: list[tuple[float, float]] = []
    for pair in match.group(1).split(","):
        parts = pair.split()
        if len(parts) >= 2:
            try:
                points.append((float(parts[0]), float(parts[1])))
            except ValueError:
                continue
    return points


def _scan_image_dataset(base: Path) -> dict:
    """Real on-disk scan of an image-pair dataset (TIFs + JSON annotations)."""
    tifs = sorted(p for p in base.rglob("*.tif")
                  if "__MACOSX" not in str(p) and p.suffix.lower() == ".tif")
    jsons = sorted(p for p in base.rglob("*.json")
                   if "__MACOSX" not in str(p) and p.name != "manifest.json")
    pre = [p for p in tifs if "_pre_disaster" in p.stem]
    post = [p for p in tifs if "_post_disaster" in p.stem]
    pre_ids = {p.stem.replace("_pre_disaster", "") for p in pre}
    post_ids = {p.stem.replace("_post_disaster", "") for p in post}
    pairs = sorted(pid for pid in pre_ids & post_ids)

    dims: tuple[int, int] | None = None
    first = next(iter(pre or post or tifs), None)
    if first is not None:
        try:
            from PIL import Image
            with Image.open(first) as im:
                dims = im.size
        except Exception:
            dims = None

    total_annotations = 0
    classes: Counter = Counter()
    for f in jsons:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        features = data.get("features", [])
        if isinstance(features, dict):
            features = features.get("lng_lat", [])
        if not isinstance(features, list):
            continue
        for item in features:
            if not isinstance(item, dict):
                continue
            total_annotations += 1
            classes[item.get("properties", {}).get("subtype", "unknown")] += 1

    ordered_classes: dict[str, int] = {}
    for key in ("no-damage", "minor-damage", "major-damage", "destroyed"):
        if classes.get(key):
            ordered_classes[key] = int(classes[key])
    for key, count in sorted(classes.items(), key=lambda kv: (-kv[1], kv[0])):
        ordered_classes.setdefault(key, int(count))

    return {
        "tifs": tifs, "jsons": jsons, "pre": pre, "post": post,
        "pairs": pairs, "dims": dims, "annotation_count": total_annotations,
        "damage_classes": ordered_classes,
    }


def load_image_dataset(config: DatasetConfig) -> ImageDatasetDetails:
    """Describe an image-pair dataset from its manifest.json + a real file scan."""
    base = config.path
    scan = _scan_image_dataset(base)

    manifest: dict = {}
    manifest_path = base / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8")) or {}
        except Exception:
            manifest = {}

    source = manifest.get("source", {}) or {}
    url = str(source.get("url", "") or "")
    doi = str(source.get("doi", "") or "")
    license_ = str(source.get("license", "") or manifest.get("license", "") or "")
    version = str(source.get("record_version", "") or manifest.get("subset", "") or "")
    name = str(manifest.get("dataset_name", "") or config.name)

    sample: list[dict] = []
    for f in scan["jsons"]:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        features = data.get("features", [])
        if isinstance(features, dict):
            features = features.get("lng_lat", [])
        for item in features:
            if not isinstance(item, dict) or len(sample) >= 250:
                break
            subtype = item.get("properties", {}).get("subtype", "unknown")
            points = parse_polygon_wkt(item.get("wkt", ""))
            if points:
                sample.append({"subtype": subtype, "lng_lat": points})
            if len(sample) >= 250:
                break
        if len(sample) >= 250:
            break

    coordinates_available = scan["annotation_count"] > 0 and bool(sample)

    # jitter for chart readability is NOT applied here; coordinates stay raw.

    scan_pairs: list[tuple[str, Path, Path]] = []
    for pid in scan["pairs"]:
        pre_path = next(p for p in scan["pre"]
                        if p.stem.replace("_pre_disaster", "") == pid)
        post_path = next(p for p in scan["post"]
                         if p.stem.replace("_post_disaster", "") == pid)
        scan_pairs.append((pid, pre_path, post_path))

    return ImageDatasetDetails(
        name=name,
        source_url=url,
        doi=doi,
        license=license_,
        version=version,
        path=config.relative_path,
        description=config.description,
        image_pairs=len(scan["pairs"]),
        pre_disaster_images=len(scan["pre"]),
        post_disaster_images=len(scan["post"]),
        image_files=len(scan["tifs"]),
        json_files=len(scan["jsons"]),
        image_dimensions=scan["dims"],
        annotation_count=scan["annotation_count"],
        damage_classes=dict(scan["damage_classes"]),
        polygon_count=scan["annotation_count"],
        coordinates_available=coordinates_available,
        sample_polygons=sample,
        pairs=scan_pairs,
        model_status=config.model_status,
        output_support=dict(config.output_support),
        is_full_dataset="full" in str(manifest.get("subset", "")).lower(),
    )


def open_image(path: Path):
    """Open an image with PIL for dashboard display; returns None on failure."""
    try:
        from PIL import Image
        return Image.open(path)
    except Exception:
        return None


def annotation_field_inventory(config: DatasetConfig) -> dict:
    """Union of real top-level and ``properties`` keys across the annotation JSONs."""
    base = config.path
    jsons = sorted(p for p in base.rglob("*.json")
                   if "__MACOSX" not in str(p) and p.name != "manifest.json")
    top_level: Counter = Counter()
    properties: Counter = Counter()
    for f in jsons:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        features = data.get("features", [])
        if isinstance(features, dict):
            features = features.get("lng_lat", [])
        if not isinstance(features, list):
            continue
        for item in features:
            if not isinstance(item, dict):
                continue
            for key in item.keys():
                top_level[key] += 1
            props = item.get("properties", {})
            if isinstance(props, dict):
                for key in props.keys():
                    properties[key] += 1
    return {
        "json_files": len(jsons),
        "top_level_keys": dict(sorted(top_level.items(), key=lambda kv: (-kv[1], kv[0]))),
        "property_keys": dict(sorted(properties.items(), key=lambda kv: (-kv[1], kv[0]))),
    }


def image_dataset_metadata(config: DatasetConfig) -> dict:
    """Real on-disk image metadata rows (format, mode, dims, counts) for a dataset."""
    details = load_image_dataset(config)
    sample = next(iter(details.pairs), None)
    fmt = mode = None
    if sample is not None:
        path = sample[1] if Path(sample[1]).exists() else None
        if path is None:
            path = sample[2]
        img = open_image(path)
        if img is not None:
            fmt = img.format
            mode = img.mode
            img.close()
    slices = 3 if (mode and mode.upper().startswith("RGB")) else (4 if mode == "RGBA" else 1)
    return {
        "format": fmt,
        "mode": mode,
        "bands": slices,
        "dimensions": details.image_dimensions,
        "pre": details.pre_disaster_images,
        "post": details.post_disaster_images,
        "pairs": details.image_pairs,
        "json_files": details.json_files,
        "annotations": details.annotation_count,
    }


# ---------------------------------------------------------------------------
# Dataset x model compatibility layer
# ---------------------------------------------------------------------------

IFI_REQUIRED_FEATURES = ["Population", "Parmanent_Water"]
IFI_TARGET = "Corrected_Percent_Flooded_Area"
IFI_PREPARED_ROWS = 720


@dataclass
class ModelCompatibility:
    """Status of a single architecture against a single registered dataset."""

    dataset_key: str
    dataset_name: str
    dataset_type: str
    model_name: str
    architecture: str
    input_type: str
    target_task: str
    status: str                              # one of MODEL_STATUS_*
    compatible: bool                         # architecture can consume this dataset
    inference_possible: bool                 # a usable artifact exists for this dataset
    reason: str
    input_requirements: str
    training_data: str
    preprocessing: str
    checkpoint: str
    evaluation: str

    @property
    def trained(self) -> bool:
        return self.status in (MODEL_STATUS_TRAINED, MODEL_STATUS_TRAINED_EVALUATED)


def _model_dir(name: str) -> Path:
    return PROJECT_ROOT / "results" / "models" / LOGICAL_MODEL_DIRS[name]


def _ifi_artifact(rel_path: str) -> Path:
    return PROJECT_ROOT / rel_path


def _baseline_compatibility(cfg: DatasetConfig, model_name: str) -> ModelCompatibility:
    spec = MODEL_CATALOG[model_name]
    if model_name in SPATIAL_MODELS:
        return ModelCompatibility(
            dataset_key=cfg.key, dataset_name=cfg.name, dataset_type=cfg.dataset_type,
            model_name=model_name, architecture=spec.architecture, input_type=spec.input_type,
            target_task=cfg.task_type or "N/A",
            status=MODEL_STATUS_INCOMPATIBLE, compatible=False, inference_possible=False,
            reason=(
                f"{model_name} consumes spatial raster sequences "
                f"({spec.input_type.split(' (')[-1].rstrip(')')}); the IFI prepared dataset is a "
                "tabular regression table (Population + Parmanent_Water). No raster "
                "preprocessing exists for it."
            ),
            input_requirements=spec.input_type,
            training_data="None for this architecture",
            preprocessing="None",
            checkpoint="None",
            evaluation="None",
        )
    model_dir = _model_dir(model_name)
    ckpt = model_dir / "best_model.pt"
    has_ckpt = ckpt.exists()
    return ModelCompatibility(
        dataset_key=cfg.key, dataset_name=cfg.name, dataset_type=cfg.dataset_type,
        model_name=model_name, architecture=spec.architecture, input_type=spec.input_type,
        target_task=cfg.task_type or f"regression on {IFI_TARGET}",
        status=(MODEL_STATUS_TRAINED_EVALUATED if has_ckpt else MODEL_STATUS_TRAINING_REQUIRED),
        compatible=True, inference_possible=has_ckpt,
        reason=(
            "Real trained checkpoint on the prepared 720-row IFI dataset; evaluated on the "
            "held-out test split." if has_ckpt else
            "Architecture implemented for district regression; no trained checkpoint exists."
        ),
        input_requirements=f"{IFI_REQUIRED_FEATURES} -> {IFI_TARGET}",
        training_data=(
            f"Prepared IFI modeling dataset ({IFI_PREPARED_ROWS} rows, "
            f"features {IFI_REQUIRED_FEATURES})"
        ),
        preprocessing=str(_ifi_artifact("results/models/preprocessing.pkl")),
        checkpoint=str(ckpt.relative_to(PROJECT_ROOT)) if has_ckpt else "None",
        evaluation=str(_ifi_artifact("results/evaluation/error_summary.csv")),
    )


def _tabular_dataset_compatibility(cfg: DatasetConfig, model_name: str) -> ModelCompatibility:
    spec = MODEL_CATALOG[model_name]
    if model_name in SPATIAL_MODELS:
        return ModelCompatibility(
            dataset_key=cfg.key, dataset_name=cfg.name, dataset_type=cfg.dataset_type,
            model_name=model_name, architecture=spec.architecture, input_type=spec.input_type,
            target_task=cfg.task_type or "N/A",
            status=MODEL_STATUS_INCOMPATIBLE, compatible=False, inference_possible=False,
            reason=(
                f"{model_name} consumes spatial raster sequences; this dataset is tabular "
                f"({cfg.dataset_type}). No raster preprocessing exists for it."
            ),
            input_requirements=spec.input_type,
            training_data="None for this architecture",
            preprocessing="None",
            checkpoint="None",
            evaluation="None",
        )

    df = load_dataset(cfg)
    missing = [f for f in IFI_REQUIRED_FEATURES if f not in df.columns]
    target_missing = IFI_TARGET not in df.columns
    missing_reason = (
        "the trained-checkpoint feature contract is "
        f"{IFI_REQUIRED_FEATURES}; missing here: {missing or 'none'}"
    )
    if cfg.target is not None and not target_missing:
        missing_reason += f"; target {IFI_TARGET} IS present"
    else:
        missing_reason += f"; target {IFI_TARGET} is missing here"
    return ModelCompatibility(
        dataset_key=cfg.key, dataset_name=cfg.name, dataset_type=cfg.dataset_type,
        model_name=model_name, architecture=spec.architecture, input_type=spec.input_type,
        target_task="district flooded-area regression",
        status=MODEL_STATUS_INCOMPATIBLE, compatible=False, inference_possible=False,
        reason=(
            f"The trained {model_name} checkpoint was fit on the prepared 720-row IFI dataset "
            f"({missing_reason}). Running it on this raw table "
            f"({len(df):,} rows) would be a misapplication of the trained contract."
        ),
        input_requirements=f"{IFI_REQUIRED_FEATURES} -> {IFI_TARGET}",
        training_data="None on this raw table",
        preprocessing="None",
        checkpoint="None",
        evaluation="None",
    )


def _image_dataset_compatibility(cfg: DatasetConfig, model_name: str) -> ModelCompatibility:
    spec = MODEL_CATALOG[model_name]
    spatial = model_name in SPATIAL_MODELS
    return ModelCompatibility(
        dataset_key=cfg.key, dataset_name=cfg.name, dataset_type=cfg.dataset_type,
        model_name=model_name, architecture=spec.architecture, input_type=spec.input_type,
        target_task=cfg.task_type or "building damage classification (imagery)",
        status=MODEL_STATUS_TRAINING_REQUIRED, compatible=True, inference_possible=False,
        reason=(
            f"{model_name} is implemented and architecturally compatible with this image-pair "
            "dataset. No checkpoint or preprocessing has been trained on it yet."
            if spatial else
            f"{model_name} is a tabular-sequence architecture; using it here requires an image "
            "feature-extraction step that is not implemented, and the existing IFI regression "
            "checkpoint must NOT be run on this imagery."
        ),
        input_requirements=spec.input_type,
        training_data=(
            "10 pre/post image pairs with 1274 building damage annotations (Sample Subset1)"
        ),
        preprocessing="None yet",
        checkpoint="None (training required)",
        evaluation="None",
    )


def model_compatibility(cfg: DatasetConfig, model_name: str) -> ModelCompatibility:
    """Compatibility + real-artifact status of ``model_name`` on ``cfg``."""
    if model_name not in MODEL_CATALOG:
        raise KeyError(f"Unknown model name: {model_name}")
    if cfg.key == M2_BASELINE.key:
        return _baseline_compatibility(cfg, model_name)
    if cfg.is_image_dataset:
        return _image_dataset_compatibility(cfg, model_name)
    return _tabular_dataset_compatibility(cfg, model_name)


def compatibility_table(cfg: DatasetConfig) -> list[ModelCompatibility]:
    """One row per architecture for ``cfg`` (fixed five-model order)."""
    return [model_compatibility(cfg, name) for name in MODEL_NAMES]


def trained_model_count(cfg: DatasetConfig) -> int:
    """Number of architectures with a usable real artifact on ``cfg``."""
    return sum(1 for row in compatibility_table(cfg) if row.inference_possible)


# ---------------------------------------------------------------------------
# Model comparison data (authoritative saved metrics only)
# ---------------------------------------------------------------------------

MODEL_COMPARISON_PATH = PROJECT_ROOT / "results" / "model_comparison.csv"
CLASSICAL_BASELINE_MODELS = ("Linear Regression", "Random Forest Regressor")


def model_comparison_csv() -> pd.DataFrame:
    """Authoritative saved comparison rows (results/model_comparison.csv)."""
    if not MODEL_COMPARISON_PATH.is_file():
        return pd.DataFrame()
    return pd.read_csv(MODEL_COMPARISON_PATH)


def trained_metrics(cfg: DatasetConfig) -> dict[str, dict[str, float]]:
    """Real saved test metrics for architectures evaluated on ``cfg``.

    Only the IFI M2 baseline has trained/evaluated checkpoints today, so any other
    dataset returns an empty mapping (no metrics are ever copied across datasets).
    """
    if cfg.key != M2_BASELINE.key:
        return {}
    df = model_comparison_csv()
    if df.empty:
        return {}
    out: dict[str, dict[str, float]] = {}
    for _, row in df[df["Model"].isin(TRAINED_IFI_MODELS)].iterrows():
        out[str(row["Model"])] = {
            "MAE": float(row["MAE"]),
            "RMSE": float(row["RMSE"]),
            "R2": float(row["R2"]),
        }
    return out


def classical_baseline_metrics() -> pd.DataFrame:
    """Authoritative saved metrics for the classical baselines (separate category)."""
    df = model_comparison_csv()
    if df.empty:
        return df
    return df[df["Model"].isin(CLASSICAL_BASELINE_MODELS)].copy()