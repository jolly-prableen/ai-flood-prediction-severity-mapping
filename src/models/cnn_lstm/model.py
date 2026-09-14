from __future__ import annotations
import torch
from torch import nn
from ..common import ModelOutput, PredictionMixin, TabularCNN


class CNNLSTM(PredictionMixin, nn.Module):
    """CNN feature extraction followed by LSTM for (batch, time, features)."""
    def __init__(self, input_dim: int, hidden_dim: int = 32, num_layers: int = 1,
                 dropout: float = 0.2, num_classes: int = 2, embedding_dim: int = 32,
                 task: str = "classification"):
        super().__init__()
        if task not in {"classification", "regression"}:
            raise ValueError("task must be 'classification' or 'regression'")
        self.task = task
        self.extractor = TabularCNN(input_dim, embedding_dim, dropout)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, num_layers,
                            batch_first=True, dropout=dropout if num_layers > 1 else 0)
        output_dim = 1 if task == "regression" else num_classes
        self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(hidden_dim, output_dim))

    def forward(self, x: torch.Tensor) -> ModelOutput:
        if x.ndim != 3:
            raise ValueError("CNNLSTM expects (batch, time, features)")
        features = torch.stack([self.extractor(step) for step in x.unbind(1)], dim=1)
        sequence, _ = self.lstm(features)
        return ModelOutput(self.head(sequence[:, -1]))
