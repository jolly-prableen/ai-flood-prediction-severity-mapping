from __future__ import annotations
import torch
from torch import nn
from ..common import ModelOutput, PredictionMixin


class AttentionGate(nn.Module):
    def __init__(self, skip_channels: int, gate_channels: int, attention_channels: int):
        super().__init__()
        self.skip = nn.Conv2d(skip_channels, attention_channels, 1)
        self.gate = nn.Conv2d(gate_channels, attention_channels, 1)
        self.score = nn.Conv2d(attention_channels, 1, 1)

    def forward(self, skip: torch.Tensor, gate: torch.Tensor) -> torch.Tensor:
        if gate.shape[-2:] != skip.shape[-2:]:
            gate = nn.functional.interpolate(gate, size=skip.shape[-2:], mode="bilinear", align_corners=False)
        weights = torch.sigmoid(self.score(torch.relu(self.skip(skip) + self.gate(gate))))
        return skip * weights


class AttentionUNetLSTM(PredictionMixin, nn.Module):
    """Attention U-Net decoder over temporally pooled spatial features."""
    def __init__(self, input_channels: int, num_classes: int = 1, base_channels: int = 8,
                 hidden_dim: int = 16, dropout: float = 0.1):
        super().__init__()
        self.enc1 = nn.Sequential(nn.Conv2d(input_channels, base_channels, 3, padding=1), nn.ReLU())
        self.enc2 = nn.Sequential(nn.Conv2d(base_channels, base_channels * 2, 3, padding=1), nn.ReLU())
        self.pool = nn.MaxPool2d(2)
        self.temporal = nn.LSTM(base_channels * 2, hidden_dim, batch_first=True)
        self.bottleneck = nn.Linear(hidden_dim, base_channels * 2)
        self.attention = AttentionGate(base_channels, base_channels * 2, base_channels)
        self.up = nn.ConvTranspose2d(base_channels * 2, base_channels, 2, stride=2)
        self.head = nn.Sequential(nn.Conv2d(base_channels * 2, base_channels, 3, padding=1), nn.ReLU(), nn.Dropout2d(dropout), nn.Conv2d(base_channels, num_classes, 1))

    def forward(self, x: torch.Tensor) -> ModelOutput:
        if x.ndim != 5:
            raise ValueError("AttentionUNetLSTM expects (batch, time, channels, height, width)")
        skips, embeddings = [], []
        for frame in x.unbind(1):
            skip = self.enc1(frame)
            deep = self.enc2(self.pool(skip))
            skips.append(skip)
            embeddings.append(deep.mean(dim=(-2, -1)))
        sequence, _ = self.temporal(torch.stack(embeddings, dim=1))
        deep = self.bottleneck(sequence[:, -1]).unsqueeze(-1).unsqueeze(-1)
        deep = deep.expand(-1, -1, x.shape[-2] // 2, x.shape[-1] // 2)
        attended = self.attention(skips[-1], deep)
        up = self.up(deep)
        if up.shape[-2:] != attended.shape[-2:]:
            up = nn.functional.interpolate(up, size=attended.shape[-2:], mode="bilinear", align_corners=False)
        return ModelOutput(self.head(torch.cat((up, attended), 1)))
