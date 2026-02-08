"""
Cognitive Load LSTM Training Pipeline

Trains an LSTM model to predict cognitive load trajectory
from interaction time-series data.
"""

import argparse
import json
from pathlib import Path

import numpy as np


def generate_synthetic_data(n_samples: int = 1000, seq_len: int = 20):
    """Generate synthetic training data for development."""
    X = np.random.rand(n_samples, seq_len, 5).astype(np.float32)  # 5 features
    # Target: next cognitive load (0-100)
    y = (np.mean(X[:, -5:, :], axis=(1, 2)) * 100).astype(np.float32)
    return X, y


def train(epochs: int = 10, batch_size: int = 32, lr: float = 1e-3):
    """Train the LSTM model."""
    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset
    except ImportError:
        print("PyTorch not installed. Run: pip install torch")
        return

    # Generate data
    X, y = generate_synthetic_data()
    dataset = TensorDataset(torch.from_numpy(X), torch.from_numpy(y))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Model
    class CogLoadLSTM(nn.Module):
        def __init__(self, input_dim=5, hidden_dim=64, num_layers=2):
            super().__init__()
            self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
            self.fc = nn.Linear(hidden_dim, 1)

        def forward(self, x):
            out, _ = self.lstm(x)
            return self.fc(out[:, -1, :]).squeeze(-1)

    model = CogLoadLSTM()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    # Training loop
    for epoch in range(epochs):
        total_loss = 0.0
        for X_batch, y_batch in loader:
            optimizer.zero_grad()
            pred = model(X_batch)
            loss = criterion(pred, y_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / len(loader)
        print(f"Epoch {epoch+1}/{epochs} – Loss: {avg_loss:.4f}")

    # Save model
    output_dir = Path("../../ml/experiments")
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_dir / "cognitive_load_lstm.pt")
    print(f"Model saved to {output_dir / 'cognitive_load_lstm.pt'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    args = parser.parse_args()
    train(epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)
