from __future__ import annotations


def diagnose_fit(history: dict, min_epochs: int = 3) -> dict:
    train_loss, val_loss = history.get("train_loss", []), history.get("val_loss", [])
    train_metric, val_metric = history.get("train_metric", []), history.get("val_metric", [])
    if history.get("task") == "regression":
        train_metric = history.get("train_mae", [])
        val_metric = history.get("val_mae", [])
    if len(train_loss) < min_epochs or len(val_loss) < min_epochs:
        return {"diagnosis": "INSUFFICIENT_HISTORY", "reason": "Need more epochs for a curve-based diagnosis."}
    loss_gap = val_loss[-1] - train_loss[-1]
    validation_worsened = val_loss[-1] > min(val_loss[:-1])
    metric_poor = bool(val_metric) and (
        max(val_metric) > 0.6 if history.get("task") == "regression" else max(val_metric) < 0.6
    )
    if loss_gap > 0.1 and validation_worsened:
        diagnosis = "OVERFITTING"
    elif metric_poor and train_metric and (
        max(train_metric) > 0.6 if history.get("task") == "regression" else max(train_metric) < 0.6
    ):
        diagnosis = "UNDERFITTING"
    else:
        diagnosis = "REASONABLE FIT"
    return {"diagnosis": diagnosis, "loss_gap": float(loss_gap), "recommended_correction": {
        "OVERFITTING": "increase dropout/weight decay or stop earlier",
        "UNDERFITTING": "slightly increase capacity or reduce regularization",
        "REASONABLE FIT": "none",
    }.get(diagnosis, "collect more history")}
