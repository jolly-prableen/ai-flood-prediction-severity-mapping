from __future__ import annotations
import torch
from torch import nn
from ..common import ModelOutput, PredictionMixin


class ConvLSTMCell(nn.Module):
    def __init__(self, input_channels: int, hidden_channels: int):
        super().__init__()
        self.hidden_channels = hidden_channels
        self.gates = nn.Conv2d(input_channels + hidden_channels, hidden_channels * 4, 3, padding=1)

    def forward(self, x: torch.Tensor, state: tuple[torch.Tensor, torch.Tensor] | None = None):
        if state is None:
            shape = (x.shape[0], self.hidden_channels, x.shape[2], x.shape[3])
            state = (x.new_zeros(shape), x.new_zeros(shape))
        hidden, cell = state
        input_gate, forget_gate, output_gate, candidate = self.gates(torch.cat((x, hidden), 1)).chunk(4, 1)
        input_gate, forget_gate, output_gate = (torch.sigmoid(input_gate), torch.sigmoid(forget_gate), torch.sigmoid(output_gate))
        cell = forget_gate * cell + input_gate * torch.tanh(candidate)
        return output_gate * torch.tanh(cell), cell


class UNetConvLSTM(PredictionMixin, nn.Module):
    """Lightweight spatial sequence model for (batch, time, channels, height, width)."""
    def __init__(self, input_channels: int, num_classes: int = 1, base_channels: int = 8,
                 dropout: float = 0.1):
        super().__init__()
        self.enc1 = nn.Sequential(nn.Conv2d(input_channels, base_channels, 3, padding=1), nn.ReLU(), nn.Dropout2d(dropout))
        self.down = nn.MaxPool2d(2)
        self.enc2 = nn.Sequential(nn.Conv2d(base_channels, base_channels * 2, 3, padding=1), nn.ReLU())
        self.temporal = ConvLSTMCell(base_channels * 2, base_channels * 2)
        self.up = nn.ConvTranspose2d(base_channels * 2, base_channels, 2, stride=2)
        self.dec = nn.Sequential(nn.Conv2d(base_channels * 2, base_channels, 3, padding=1), nn.ReLU())
        self.head = nn.Conv2d(base_channels, num_classes, 1)

    def forward(self, x: torch.Tensor) -> ModelOutput:
        if x.ndim != 5:
            raise ValueError("UNetConvLSTM expects (batch, time, channels, height, width)")
        skip = None
        state = None
        for frame in x.unbind(1):
            skip = self.enc1(frame)
            state = self.temporal(self.enc2(self.down(skip)), state)
        hidden = self.up(state[0])
        if hidden.shape[-2:] != skip.shape[-2:]:
            hidden = nn.functional.interpolate(hidden, size=skip.shape[-2:], mode="bilinear", align_corners=False)
        return ModelOutput(self.head(self.dec(torch.cat((hidden, skip), 1))))
