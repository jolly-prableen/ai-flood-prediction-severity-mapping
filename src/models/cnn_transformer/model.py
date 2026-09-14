from __future__ import annotations
import math
import torch
from torch import nn
from ..common import ModelOutput, PredictionMixin, TabularCNN


class CNNTransformer(PredictionMixin, nn.Module):
    """CNN feature extraction, positional encoding, and Transformer encoder."""
    def __init__(self, input_dim: int, embedding_dim: int = 32, num_heads: int = 4,
                 num_layers: int = 1, dropout: float = 0.2, num_classes: int = 2,
                 task: str = "classification"):
        super().__init__()
        if embedding_dim % num_heads:
            raise ValueError("embedding_dim must be divisible by num_heads")
        if task not in {"classification", "regression"}:
            raise ValueError("task must be 'classification' or 'regression'")
        self.task = task
        self.embedding_dim = embedding_dim
        self.extractor = TabularCNN(input_dim, embedding_dim, dropout)
        self.dropout = nn.Dropout(dropout)
        layer = nn.TransformerEncoderLayer(embedding_dim, num_heads, embedding_dim * 2,
                                           dropout, batch_first=True, norm_first=True)
        self.encoder = nn.TransformerEncoder(layer, num_layers)
        output_dim = 1 if task == "regression" else num_classes
        self.head = nn.Linear(embedding_dim, output_dim)

    def forward(self, x: torch.Tensor) -> ModelOutput:
        if x.ndim != 3:
            raise ValueError("CNNTransformer expects (batch, time, features)")
        features = torch.stack([self.extractor(step) for step in x.unbind(1)], dim=1)
        positions = torch.arange(x.shape[1], device=x.device).float()
        positions = torch.sin(positions[:, None] / math.sqrt(self.embedding_dim))
        positions = positions.expand(-1, self.embedding_dim)
        encoded = self.encoder(self.dropout(features + positions[None, :, :]))
        return ModelOutput(self.head(encoded.mean(dim=1)))
