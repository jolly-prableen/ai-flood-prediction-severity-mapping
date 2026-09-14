"""Strict adapter for the prepared IFI regression feature schema."""
from __future__ import annotations

import numpy as np
import pandas as pd

CANONICAL_FEATURES = ["Population", "Parmanent_Water"]
ALIASES = {
    "population": "Population",
    "permanent_water": "Parmanent_Water",
    "parmanent_water": "Parmanent_Water",
}


def adapt_uploaded_dataset(data) -> pd.DataFrame:
    frame = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    renamed = {}
    for column in frame.columns:
        key = str(column).strip().casefold()
        if key in ALIASES:
            renamed[column] = ALIASES[key]
    frame = frame.rename(columns=renamed)
    missing = [feature for feature in CANONICAL_FEATURES if feature not in frame.columns]
    if missing:
        raise ValueError(f"INCOMPATIBLE: missing required features {missing}")
    selected = frame[CANONICAL_FEATURES].apply(pd.to_numeric, errors="coerce")
    if selected.isna().any().any():
        raise ValueError("INCOMPATIBLE: required features contain missing or non-numeric values")
    return selected


def to_model_array(data) -> np.ndarray:
    return adapt_uploaded_dataset(data).to_numpy(dtype=np.float32)
