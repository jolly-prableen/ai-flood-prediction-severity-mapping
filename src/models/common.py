"""Shared model output and prediction helpers."""
from __future__ import annotations

from typing import Any
import torch
from torch import nn


def logits_from_output(output: Any) -> torch.Tensor:
    return output.logits if isinstance(output, ModelOutput) else output


class ModelOutput:
    def __init__(self, logits: torch.Tensor):
        self.logits = logits

    @property
    def probabilities(self) -> torch.Tensor:
        class_dimension = 1 if self.logits.ndim > 2 else -1
        if class_dimension == 1 and self.logits.shape[1] == 1:
            return torch.sigmoid(self.logits)
        if class_dimension == 1:
            return torch.softmax(self.logits, dim=1)
        if self.logits.shape[-1] == 1:
            return torch.sigmoid(self.logits)
        return torch.softmax(self.logits, dim=-1)

    @property
    def predicted_class(self) -> torch.Tensor:
        if self.logits.ndim > 2:
            if self.logits.shape[1] == 1:
                return (torch.sigmoid(self.logits) >= 0.5).long()
            return self.logits.argmax(dim=1)
        if self.logits.shape[-1] == 1:
            return (torch.sigmoid(self.logits) >= 0.5).long().view(-1)
        return self.logits.argmax(dim=-1)

    def __getitem__(self, key: str) -> torch.Tensor:
        return {"logits": self.logits, "probabilities": self.probabilities,
                "predicted_class": self.predicted_class}[key]


class PredictionMixin:
    def predict(self, x: torch.Tensor) -> torch.Tensor:
        self.eval()
        with torch.no_grad():
            return self(x).predicted_class

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        self.eval()
        with torch.no_grad():
            return self(x).probabilities

    def get_predictions(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        self.eval()
        with torch.no_grad():
            output = self(x)
        return {"logits": output.logits, "probabilities": output.probabilities,
                "predicted_class": output.predicted_class}


class TabularCNN(nn.Module):
    def __init__(self, input_dim: int, embedding_dim: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(1, 16, 3, padding=1), nn.ReLU(),
            nn.Conv1d(16, embedding_dim, 3, padding=1), nn.ReLU(),
            nn.Dropout(dropout), nn.AdaptiveAvgPool1d(1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x.unsqueeze(1)).squeeze(-1)


class Residual1D(nn.Module):
    def __init__(self, channels: int, dropout: float):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv1d(channels, channels, 3, padding=1), nn.BatchNorm1d(channels),
            nn.ReLU(), nn.Dropout(dropout),
            nn.Conv1d(channels, channels, 3, padding=1), nn.BatchNorm1d(channels),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.relu(x + self.block(x))
