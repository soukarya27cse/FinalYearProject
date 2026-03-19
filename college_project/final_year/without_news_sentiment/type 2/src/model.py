"""
src/model.py — Hybrid CNN → BiLSTM → Multi-Head Attention  (v4)

Architecture overview
─────────────────────
  Input  (batch, seq_len, n_features)
    │
    ▼
  TemporalConvBlock          # 1-D CNN: extracts local patterns
    │   kernel sizes 3 & 5, residual projection
    ▼
  Bidirectional LSTM         # captures long-range dependencies in both directions
    │   stacked, with variational dropout between layers
    ▼
  Multi-Head Self-Attention  # learns which time steps to focus on
    │   + residual + LayerNorm
    ▼
  FC head → scalar prediction

Key changes vs v3
─────────────────
• CombinedLoss — Huber loss + directional penalty.
  Directly penalises wrong-direction predictions so the model is rewarded
  for getting the sign right, not just for staying close to the mean.

• Temporal Attention Pooling — instead of always using the last time step,
  a learnable score function weights all time steps, letting the model attend
  to the most relevant bars anywhere in the window (not just the most recent).

• monte_carlo_forecast — updated signature: accepts raw last close + scaler,
  performs all inverse-transform internally, returns real prices directly
  (no inverse_close() calls needed in app.py).
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler
import streamlit as st


# ── Dataset ────────────────────────────────────────────────────────────────────

class StockDataset(Dataset):
    """Wraps (X, y) numpy arrays as a PyTorch Dataset."""
    def __init__(self, X: np.ndarray, y: np.ndarray):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32).unsqueeze(1)

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int):
        return self.X[idx], self.y[idx]


def make_loaders(
    X_train, y_train,
    X_val,   y_val,
    X_test,  y_test,
    batch_size: int = 32,
) -> tuple[DataLoader, DataLoader, DataLoader]:
    """Wrap split arrays into DataLoaders (shuffle=False — temporal order)."""
    mk = lambda X, y: DataLoader(
        StockDataset(X, y), batch_size=batch_size, shuffle=False
    )
    return mk(X_train, y_train), mk(X_val, y_val), mk(X_test, y_test)


# ── Loss function ──────────────────────────────────────────────────────────────

class CombinedLoss(nn.Module):
    """Huber loss + directional penalty.

    Why this beats plain MSE for log-return prediction
    ───────────────────────────────────────────────────
    MSE penalises magnitude only — it doesn't care if the predicted sign is
    wrong.  On log returns, the sign IS the trading signal, so we add an
    explicit penalty for direction errors.

    Huber loss (delta = 0.01)
        Behaves like L2 for |error| < delta (smooth near zero) and L1 for
        larger errors (less sensitive to outlier days with extreme moves).
        For daily log returns (typically +/-0.01-0.03), delta=0.01 fits well.

    Directional penalty
        relu(-pred * target) = 0 when signs agree, positive when they differ.
        Magnitude scales with how confidently wrong the prediction is.

    Args:
        delta            : Huber loss threshold (default 0.01 suits log returns)
        direction_weight : weight of directional penalty (default 0.4)
    """
    def __init__(self, delta: float = 0.01, direction_weight: float = 0.4):
        super().__init__()
        self.huber            = nn.HuberLoss(delta=delta, reduction='mean')
        self.direction_weight = direction_weight

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        huber_loss  = self.huber(pred, target)
        dir_penalty = torch.mean(F.relu(-(pred * target)))
        return huber_loss + self.direction_weight * dir_penalty


# ── Building blocks ────────────────────────────────────────────────────────────

class TemporalConvBlock(nn.Module):
    """Dual-kernel 1-D CNN with residual projection."""
    def __init__(self, in_channels: int, out_channels: int, dropout: float = 0.2):
        super().__init__()
        mid = out_channels // 2

        self.conv3 = nn.Conv1d(in_channels, mid, kernel_size=3, padding=1)
        self.conv5 = nn.Conv1d(in_channels, mid, kernel_size=5, padding=2)
        self.bn3   = nn.BatchNorm1d(mid)
        self.bn5   = nn.BatchNorm1d(mid)

        self.fuse  = nn.Conv1d(out_channels, out_channels, kernel_size=1)
        self.bn_f  = nn.BatchNorm1d(out_channels)

        self.residual = (
            nn.Conv1d(in_channels, out_channels, kernel_size=1)
            if in_channels != out_channels else nn.Identity()
        )
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        shortcut = self.residual(x)
        c3  = F.gelu(self.bn3(self.conv3(x)))
        c5  = F.gelu(self.bn5(self.conv5(x)))
        out = F.gelu(self.bn_f(self.fuse(torch.cat([c3, c5], dim=1))))
        return self.drop(out) + shortcut


class MultiHeadAttentionBlock(nn.Module):
    """Scaled dot-product multi-head self-attention + residual + LayerNorm."""
    def __init__(self, d_model: int, num_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        assert d_model % num_heads == 0
        self.attn = nn.MultiheadAttention(
            d_model, num_heads, dropout=dropout, batch_first=True
        )
        self.norm = nn.LayerNorm(d_model)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        attn_out, _ = self.attn(x, x, x)
        return self.norm(x + self.drop(attn_out))


# ── Hybrid model ───────────────────────────────────────────────────────────────

class HybridModel(nn.Module):
    """CNN -> Bidirectional LSTM -> Multi-Head Attention -> FC regressor."""
    def __init__(
        self,
        input_size:   int,
        hidden_size:  int   = 128,
        num_layers:   int   = 2,
        cnn_channels: int   = 64,
        num_heads:    int   = 4,
        dropout:      float = 0.2,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers  = num_layers

        self.cnn = TemporalConvBlock(
            in_channels=input_size, out_channels=cnn_channels, dropout=dropout
        )
        self.lstm = nn.LSTM(
            input_size=cnn_channels,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        bilstm_out     = hidden_size * 2
        self.attn      = MultiHeadAttentionBlock(
            d_model=bilstm_out, num_heads=num_heads, dropout=dropout
        )
        self.time_pool = nn.Linear(bilstm_out, 1)
        self.head      = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(bilstm_out, bilstm_out // 2),
            nn.GELU(),
            nn.Dropout(dropout / 2),
            nn.Linear(bilstm_out // 2, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        cnn_out     = self.cnn(x.permute(0, 2, 1)).permute(0, 2, 1)
        lstm_out, _ = self.lstm(cnn_out)
        attn_out    = self.attn(lstm_out)
        scores      = torch.softmax(self.time_pool(attn_out), dim=1)
        pooled      = (attn_out * scores).sum(dim=1)
        return self.head(pooled)


# ── Training loop ──────────────────────────────────────────────────────────────

def train_model(
    train_loader: DataLoader,
    val_loader:   DataLoader,
    input_size:   int,
    epochs:       int,
    patience:     int,
    device:       torch.device,
    hidden_size:  int   = 128,
    dropout:      float = 0.2,
    cnn_channels: int   = 64,
    num_heads:    int   = 4,
) -> tuple[HybridModel, dict]:
    """Train with CombinedLoss, AdamW, cosine warm-restart LR, early stopping."""
    model = HybridModel(
        input_size=input_size,
        hidden_size=hidden_size,
        dropout=dropout,
        cnn_channels=cnn_channels,
        num_heads=num_heads,
    ).to(device)

    criterion = CombinedLoss(delta=0.01, direction_weight=0.4)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
        optimizer, T_0=10, T_mult=2, eta_min=1e-6,
    )

    best_val_loss    = float("inf")
    patience_counter = 0
    best_state       = None
    loss_history     = {"train": [], "val": []}

    bar    = st.progress(0)
    status = st.empty()

    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for X_b, y_b in train_loader:
            X_b, y_b = X_b.to(device), y_b.to(device)
            optimizer.zero_grad()
            loss = criterion(model(X_b), y_b)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss += loss.item()
        train_loss /= len(train_loader)

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for X_b, y_b in val_loader:
                val_loss += criterion(model(X_b.to(device)), y_b.to(device)).item()
        val_loss /= len(val_loader)

        scheduler.step(epoch + val_loss / 10)
        loss_history["train"].append(train_loss)
        loss_history["val"].append(val_loss)

        bar.progress((epoch + 1) / epochs)
        status.markdown(
            f'<span style="font-family:\'DM Mono\',monospace;font-size:0.75rem;color:#94a3b8">'
            f'EPOCH {epoch+1}/{epochs} &nbsp;|&nbsp;'
            f'<span style="color:#38bdf8">TRAIN {train_loss:.5f}</span> &nbsp;|&nbsp;'
            f'<span style="color:#818cf8">VAL {val_loss:.5f}</span></span>',
            unsafe_allow_html=True,
        )

        if val_loss < best_val_loss:
            best_val_loss    = val_loss
            patience_counter = 0
            best_state       = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            patience_counter += 1
            if patience_counter >= patience:
                status.markdown(
                    f'<span style="font-family:\'DM Mono\',monospace;font-size:0.75rem;color:#fbbf24">'
                    f'EARLY STOPPING — epoch {epoch+1} | best val {best_val_loss:.5f}</span>',
                    unsafe_allow_html=True,
                )
                break

    if best_state:
        model.load_state_dict(best_state)
    return model, loss_history


# ── Inference helpers ──────────────────────────────────────────────────────────

def predict_test_set(
    model:       HybridModel,
    test_loader: DataLoader,
    device:      torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    """Return predicted and actual log returns over the test set."""
    model.eval()
    preds, actuals = [], []
    with torch.no_grad():
        for X_b, y_b in test_loader:
            preds.extend(model(X_b.to(device)).cpu().numpy().flatten())
            actuals.extend(y_b.numpy().flatten())
    return np.array(preds), np.array(actuals)


def monte_carlo_forecast(
    model:          HybridModel,
    scaled_data:    np.ndarray,
    raw_close_last: float,
    scaler:         MinMaxScaler,
    n_features:     int,
    seq_length:     int,
    forecast_days:  int,
    device:         torch.device,
    n_samples:      int = 100,
    close_idx:      int = 3,
) -> list[dict]:
    """Recursive MC-Dropout forecast; returns real prices directly."""
    close_min = float(scaler.data_min_[close_idx])
    close_max = float(scaler.data_max_[close_idx])

    last_seq      = scaled_data[-seq_length:].reshape(1, seq_length, -1)
    cur_input     = torch.from_numpy(last_seq.copy()).float().to(device)
    current_price = raw_close_last
    results       = []

    for _ in range(forecast_days):
        samples = []
        model.train()
        for _ in range(n_samples):
            with torch.no_grad():
                samples.append(model(cur_input).cpu().item())

        mean_return = float(np.mean(samples))
        std_return  = float(np.std(samples))
        next_price  = current_price * np.exp(mean_return)
        price_std   = current_price * std_return

        results.append({"mean": next_price, "std": price_std})

        scaled_close = np.clip(
            (next_price - close_min) / max(close_max - close_min, 1e-9), 0.0, 1.0
        )
        nxt                = np.roll(last_seq[0].copy(), -1, axis=0)
        nxt[-1, close_idx] = scaled_close
        last_seq           = nxt.reshape(1, seq_length, -1)
        cur_input          = torch.from_numpy(last_seq.copy()).float().to(device)
        current_price      = next_price

    return results


def model_summary(model: HybridModel) -> str:
    """Concise parameter count string for the Streamlit UI."""
    total     = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return (
        f"Total params: {total:,}  |  "
        f"Trainable: {trainable:,}  |  "
        f"Non-trainable: {total - trainable:,}"
    )