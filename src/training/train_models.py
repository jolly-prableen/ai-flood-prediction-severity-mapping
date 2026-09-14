"""Small command-line training entry point for a legitimate processed CSV."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import torch
from torch.utils.data import DataLoader, TensorDataset
from src.models.cnn_lstm.model import CNNLSTM
from src.training.trainer import Trainer
from src.utils.seed import set_seed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--target", default="Flood_Binary")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--output", default="results/models/cnn_lstm/best_model.pt")
    args = parser.parse_args()
    set_seed(42)
    frame = pd.read_csv(args.csv)
    if args.target not in frame:
        raise ValueError(f"Target {args.target!r} is absent. Available columns: {list(frame.columns)}")
    numeric = frame.select_dtypes(include="number").drop(columns=[args.target], errors="ignore").fillna(0)
    X = torch.tensor(numeric.to_numpy(), dtype=torch.float32).unsqueeze(1)
    y = torch.tensor(frame[args.target].to_numpy(), dtype=torch.long)
    split = max(1, int(len(y) * 0.8))
    train_loader = DataLoader(TensorDataset(X[:split], y[:split]), args.batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(X[split:], y[split:]), args.batch_size)
    model = CNNLSTM(input_dim=X.shape[-1])
    history = Trainer(model, patience=3).fit(train_loader, val_loader, args.epochs, args.output,
                                               {"model_kwargs": {"input_dim": X.shape[-1]}})
    print(history)


if __name__ == "__main__":
    main()
