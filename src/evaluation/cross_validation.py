from __future__ import annotations
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from src.evaluation.metrics import classification_metrics
from src.evaluation.metrics import regression_metrics


def stratified_cv(X, y, n_splits=10, seed=42, model_factory=None):
    """Fold-safe CV. Any preprocessing in model_factory is fitted within each fold."""
    X, y = np.asarray(X), np.asarray(y)
    splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    rows = []
    for fold, (train_idx, valid_idx) in enumerate(splitter.split(X, y), 1):
        model = model_factory() if model_factory else make_pipeline(StandardScaler(), LogisticRegression(max_iter=300))
        started = time.perf_counter()
        model.fit(X[train_idx], y[train_idx])
        pred = model.predict(X[valid_idx])
        proba = model.predict_proba(X[valid_idx]) if hasattr(model, "predict_proba") else None
        metrics = classification_metrics(y[valid_idx], pred, proba)
        rows.append({"fold": fold, "training_time": time.perf_counter() - started, **{k: v for k, v in metrics.items() if k != "confusion_matrix"}})
    return pd.DataFrame(rows)


def regression_cv(X, y, n_splits=10, seed=42, model_factory=None):
    """Regression CV with a scaler fitted independently inside every fold."""
    X, y = np.asarray(X), np.asarray(y)
    splitter = __import__("sklearn.model_selection", fromlist=["KFold"]).KFold(
        n_splits=n_splits, shuffle=True, random_state=seed
    )
    rows = []
    for fold, (train_idx, valid_idx) in enumerate(splitter.split(X), 1):
        scaler = StandardScaler().fit(X[train_idx])
        train_x, valid_x = scaler.transform(X[train_idx]), scaler.transform(X[valid_idx])
        model = model_factory() if model_factory else __import__("sklearn.linear_model", fromlist=["LinearRegression"]).LinearRegression()
        started = time.perf_counter()
        model.fit(train_x, y[train_idx])
        prediction = model.predict(valid_x)
        rows.append({"fold": fold, "training_time": time.perf_counter() - started,
                     **regression_metrics(y[valid_idx], prediction)})
    return pd.DataFrame(rows)
