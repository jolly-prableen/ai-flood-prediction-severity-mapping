from __future__ import annotations
import torch
from torch import nn
from ..common import ModelOutput, PredictionMixin, Residual1D


class ResNetBiLSTM(PredictionMixin, nn.Module):
    """Lightweight custom 1-D ResNet followed by a bidirectional LSTM."""
    def __init__(self, input_dim: int, hidden_dim: int = 32, num_layers: int = 1,
                 dropout: float = 0.2, num_classes: int = 2, channels: int = 32,
                 task: str = "classification"):
        super().__init__()
        if task not in {"classification", "regression"}:
            raise ValueError("task must be 'classification' or 'regression'")
        self.task = task
        self.stem = nn.Sequential(nn.Conv1d(1, channels, 3, padding=1), nn.BatchNorm1d(channels), nn.ReLU())
        self.blocks = nn.Sequential(Residual1D(channels, dropout), Residual1D(channels, dropout))
        self.lstm = nn.LSTM(channels, hidden_dim, num_layers, batch_first=True,
                            bidirectional=True, dropout=dropout if num_layers > 1 else 0)
        output_dim = 1 if task == "regression" else num_classes
        self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(hidden_dim * 2, output_dim))

    def forward(self, x: torch.Tensor) -> ModelOutput:
        if x.ndim != 3:
            raise ValueError("ResNetBiLSTM expects (batch, time, features)")
        batch, steps, features = x.shape
        encoded = self.blocks(self.stem(x.reshape(batch * steps, 1, features)))
        encoded = encoded.mean(dim=-1).reshape(batch, steps, -1)
        sequence, _ = self.lstm(encoded)
        return ModelOutput(self.head(sequence[:, -1]))
