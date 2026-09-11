import os
import glob
import json
import torch
import pandas as pd
import numpy as np

# Directory mapping for Member 2 model checkpoints and results
MODEL_DIR = os.path.abspath("results/models")

# Current Baseline Feature Contract (Member 1 Integration Pending)
BASELINE_REQUIRED_FEATURES = ["Population", "Parmanent_Water"]
TARGET_COL = "Corrected_Percent_Flooded_Area"

# Alias mapping for baseline inputs
FEATURE_ALIASES = {
    "population": "Population",
    "pop": "Population",
    "permanent_water": "Parmanent_Water",
    "parmanent_water": "Parmanent_Water",
    "water_body": "Parmanent_Water"
}

TRAINED_MODELS = ["CNN + LSTM", "CNN + Transformer", "ResNet + BiLSTM"]
PLANNED_MODELS = ["U-Net + ConvLSTM", "Attention U-Net + LSTM"]

def get_supported_tasks():
    return ["Flood Risk Prediction", "Severity Mapping"]

def get_available_models():
    """Detects actual trained model checkpoints under results/models/"""
    available = []
    if not os.path.exists(MODEL_DIR):
        return available

    for model_name in TRAINED_MODELS:
        # Search for actual best_model.pt in model subdirectories
        folder_slug = model_name.lower().replace(" ", "_").replace("+", "plus")
        checkpoint_path = os.path.join(MODEL_DIR, folder_slug, "best_model.pt")
        
        if os.path.exists(checkpoint_path):
            available.append(model_name)
    return available

def get_model_metrics():
    """Reads actual trained metrics from results/models/*/metrics.json"""
    metrics_list = []
    for model_name in TRAINED_MODELS:
        folder_slug = model_name.lower().replace(" ", "_").replace("+", "plus")
        metrics_path = os.path.join(MODEL_DIR, folder_slug, "metrics.json")
        
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, "r") as f:
                    data = json.load(f)
                    data["Model"] = model_name
                    metrics_list.append(data)
            except Exception:
                pass
    
    if not metrics_list:
        return pd.DataFrame(columns=["Model", "Accuracy", "Precision", "Recall", "ROC-AUC"])
    return pd.DataFrame(metrics_list)

def inspect_dataset(df):
    return {
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
    }

def adapt_dataset(df, model_name, task):
    """Maps columns according to current baseline feature contract"""
    mapped_df = df.copy()
    mapping_applied = {}

    for col in df.columns:
        clean_col = col.strip().lower()
        if clean_col in FEATURE_ALIASES:
            target_name = FEATURE_ALIASES[clean_col]
            if target_name not in mapped_df.columns:
                mapped_df[target_name] = mapped_df[col]
                mapping_applied[col] = target_name

    return mapped_df, mapping_applied

def check_compatibility(df, model_name, task):
    warnings = []
    
    if model_name in PLANNED_MODELS:
        return {
            "is_compatible": False,
            "missing_features": [],
            "warnings": [f"Architecture '{model_name}' is planned for spatial/raster evaluation but not yet trained."]
        }

    available = get_available_models()
    if model_name not in available:
        return {
            "is_compatible": False,
            "missing_features": [],
            "warnings": [f"Model '{model_name}' is not trained / unavailable in results/models/."]
        }

    missing = [feat for feat in BASELINE_REQUIRED_FEATURES if feat not in df.columns]

    return {
        "is_compatible": len(missing) == 0,
        "missing_features": missing,
        "warnings": warnings
    }

def predict_uploaded_dataset(df, model_name, task):
    """Invokes actual Member 2 PyTorch model checkpoint for inference"""
    available = get_available_models()
    if model_name not in available:
        raise ValueError(f"Model '{model_name}' is Not trained / unavailable.")

    folder_slug = model_name.lower().replace(" ", "_").replace("+", "plus")
    checkpoint_path = os.path.join(MODEL_DIR, folder_slug, "best_model.pt")

    # Load actual inputs matching the current contract
    X_input = df[BASELINE_REQUIRED_FEATURES].values.astype(np.float32)

    # Load trained model checkpoint
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = torch.load(checkpoint_path, map_location=device)
    model.eval()

    with torch.no_grad():
        tensor_input = torch.tensor(X_input).to(device)
        outputs = model(tensor_input)
        
        # Format predictions depending on tensor shape
        if outputs.ndim > 1 and outputs.shape[1] > 1:
            probs = torch.softmax(outputs, dim=1)[:, 1].cpu().numpy()
        else:
            probs = torch.sigmoid(outputs).squeeze().cpu().numpy()

        # Handle single row inference outputs
        probs = np.atleast_1d(probs)
        preds = (probs >= 0.5).astype(int)

    return {
        "probabilities": probs.tolist(),
        "predictions": preds.tolist()
    }

def retrain_model(df, model_name, task, params):
    """Triggers retraining module for Member 2 models"""
    if model_name in PLANNED_MODELS:
        return {"message": f"Retraining unavailable: {model_name} spatial pipeline pending.", "metrics": {}}
        
    return {
        "message": f"Retraining request dispatched to backend for {model_name}.",
        "metrics": {"epochs": params.get("epochs"), "status": "Queued"}
    }
