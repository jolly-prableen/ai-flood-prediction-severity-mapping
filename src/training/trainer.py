from __future__ import annotations
import json
import time
from pathlib import Path
import torch
from torch import nn
from .early_stopping import EarlyStopping
from src.evaluation.metrics import classification_metrics, regression_metrics


class Trainer:
    def __init__(self, model, optimizer=None, criterion=None, device=None, patience=3,
                 scheduler=None, task="classification"):
        if task not in {"classification", "regression"}:
            raise ValueError("task must be 'classification' or 'regression'")
        self.model = model
        self.task = task
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model.to(self.device)
        self.optimizer = optimizer or torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
        self.criterion = criterion or (nn.MSELoss() if task == "regression" else nn.CrossEntropyLoss())
        self.scheduler = scheduler
        self.early_stopping = EarlyStopping(patience)

    def _epoch(self, loader, train: bool):
        self.model.train(train)
        total_loss, labels, predictions, probabilities = 0.0, [], [], []
        for inputs, targets in loader:
            inputs, targets = inputs.to(self.device), targets.to(self.device)
            if train:
                self.optimizer.zero_grad(set_to_none=True)
            output = self.model(inputs)
            if self.task == "regression":
                target_values = targets.float().reshape_as(output.logits)
                loss = self.criterion(output.logits, target_values)
            else:
                loss = self.criterion(output.logits, targets.long())
            if train:
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                self.optimizer.step()
            total_loss += loss.item() * len(targets)
            if self.task == "regression":
                labels.extend(target_values.detach().cpu().reshape(-1).tolist())
                predictions.extend(output.logits.detach().cpu().reshape(-1).tolist())
            elif output.logits.ndim == 2:
                labels.extend(targets.detach().cpu().tolist())
                predictions.extend(output.predicted_class.detach().cpu().tolist())
                probabilities.extend(output.probabilities.detach().cpu().tolist())
        if not labels:
            return total_loss / max(len(loader.dataset), 1), {}
        metrics = regression_metrics(labels, predictions) if self.task == "regression" else classification_metrics(labels, predictions, probabilities)
        return total_loss / max(len(loader.dataset), 1), metrics

    def fit(self, train_loader, val_loader, epochs=10, checkpoint_path=None, metadata=None):
        history = {"task": self.task, "train_loss": [], "val_loss": []}
        if self.task == "regression":
            history.update({"train_mae": [], "val_mae": []})
        else:
            history.update({"train_metric": [], "val_metric": []})
        started = time.perf_counter()
        for _ in range(epochs):
            train_loss, train_metrics = self._epoch(train_loader, True)
            val_loss, val_metrics = self._epoch(val_loader, False)
            history["train_loss"].append(float(train_loss))
            history["val_loss"].append(float(val_loss))
            if self.task == "regression":
                history["train_mae"].append(float(train_metrics["mae"]))
                history["val_mae"].append(float(val_metrics["mae"]))
            else:
                history["train_metric"].append(float(train_metrics["f1"]))
                history["val_metric"].append(float(val_metrics["f1"]))
            if self.scheduler:
                self.scheduler.step(val_loss)
            if self.early_stopping.step(val_loss, self.model):
                break
        self.early_stopping.restore(self.model)
        if checkpoint_path:
            path = Path(checkpoint_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            torch.save({"model_state_dict": self.model.state_dict(), "history": history, "metadata": metadata or {}}, path)
            path.with_name("history.json").write_text(json.dumps(history, indent=2))
        history["training_time"] = time.perf_counter() - started
        return history

    def evaluate(self, loader) -> dict:
        loss, metrics = self._epoch(loader, False)
        return {"test_loss": float(loss), **metrics}
