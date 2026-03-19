"""
src/model.py — LSTM architecture, StockDataset, and training loop
"""
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import streamlit as st


# ── Dataset ────────────────────────────────────────────────────────────────────

class StockDataset(Dataset):
    """Wraps (X, y) numpy arrays as a PyTorch Dataset."""
    def __init__(self, X: np.ndarray, y: np.ndarray):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32).unsqueeze(1)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


def make_loaders(
    X_train, y_train,
    X_val,   y_val,
    X_test,  y_test,
    batch_size: int = 32,
) -> tuple[DataLoader, DataLoader, DataLoader]:
    """Wrap split arrays into DataLoaders (shuffle=False — temporal order matters)."""
    mk = lambda X, y: DataLoader(StockDataset(X, y), batch_size=batch_size, shuffle=False)
    return mk(X_train, y_train), mk(X_val, y_val), mk(X_test, y_test)


# ── Model ──────────────────────────────────────────────────────────────────────

class LSTMModel(nn.Module):
    """2-layer LSTM with configurable hidden size, layers, and dropout.

    Args:
        input_size  : number of input features per time-step
        hidden_size : LSTM hidden units (default 128 — increased from 64)
        num_layers  : stacked LSTM layers (default 2)
        dropout     : dropout probability applied after the last LSTM step
    """
    def __init__(self, input_size: int, hidden_size: int = 128,
                 num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers  = num_layers
        self.lstm    = nn.LSTM(
            input_size, hidden_size, num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc      = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        return self.fc(self.dropout(out[:, -1, :]))


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
) -> tuple["LSTMModel", dict]:
    """Train with early stopping, ReduceLROnPlateau, and gradient clipping.

    Returns:
        model       : Trained LSTMModel with best-validation weights loaded.
        loss_history: Dict with 'train' and 'val' loss lists for plotting.
    """
    model     = LSTMModel(input_size=input_size, hidden_size=hidden_size, dropout=dropout).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5
    )

    best_val_loss    = float('inf')
    patience_counter = 0
    best_state       = None
    loss_history     = {'train': [], 'val': []}

    bar    = st.progress(0)
    status = st.empty()

    for epoch in range(epochs):
        # ── train ──
        model.train()
        train_loss = 0.0
        for X_b, y_b in train_loader:
            X_b, y_b = X_b.to(device), y_b.to(device)
            loss = criterion(model(X_b), y_b)
            optimizer.zero_grad()
            loss.backward()
            # Gradient clipping — prevents exploding gradients in deep LSTMs
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss += loss.item()
        train_loss /= len(train_loader)

        # ── validate ──
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for X_b, y_b in val_loader:
                val_loss += criterion(model(X_b.to(device)), y_b.to(device)).item()
        val_loss /= len(val_loader)

        scheduler.step(val_loss)
        loss_history['train'].append(train_loss)
        loss_history['val'].append(val_loss)

        # ── progress UI ──
        bar.progress((epoch + 1) / epochs)
        status.markdown(
            f'<span style="font-family:\'DM Mono\',monospace;font-size:0.75rem;color:#94a3b8">'
            f'EPOCH {epoch+1}/{epochs} &nbsp;|&nbsp;'
            f'<span style="color:#38bdf8"> TRAIN {train_loss:.5f}</span> &nbsp;|&nbsp;'
            f'<span style="color:#818cf8"> VAL {val_loss:.5f}</span></span>',
            unsafe_allow_html=True,
        )

        # ── early stopping ──
        if val_loss < best_val_loss:
            best_val_loss, patience_counter, best_state = val_loss, 0, model.state_dict()
        else:
            patience_counter += 1
            if patience_counter >= patience:
                status.markdown(
                    f'<span style="font-family:\'DM Mono\',monospace;font-size:0.75rem;color:#fbbf24">'
                    f'⚡ EARLY STOPPING — epoch {epoch+1}</span>',
                    unsafe_allow_html=True,
                )
                break

    if best_state:
        model.load_state_dict(best_state)
    return model, loss_history


# ── Inference helpers ──────────────────────────────────────────────────────────

def predict_test_set(
    model: LSTMModel,
    test_loader: DataLoader,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    """Run the trained model over the test loader.

    Returns:
        preds  : (N,)  scaled Close predictions
        actuals: (N,)  scaled Close ground-truth values
    """
    model.eval()
    preds, actuals = [], []
    with torch.no_grad():
        for X_b, y_b in test_loader:
            preds.extend(model(X_b.to(device)).cpu().numpy().flatten())
            actuals.extend(y_b.numpy().flatten())
    return np.array(preds), np.array(actuals)


def monte_carlo_forecast(
    model:         LSTMModel,
    scaled_data:   np.ndarray,
    seq_length:    int,
    forecast_days: int,
    device:        torch.device,
    n_samples:     int = 100,
) -> list[dict]:
    """Recursive multi-step forecast with Monte Carlo Dropout uncertainty.

    n_samples increased to 100 (from 50) for tighter, more stable uncertainty bands.

    Returns:
        List of dicts: [{'mean': float, 'std': float}, ...]  (length = forecast_days)
        Values are in *scaled* space — caller must inverse-transform them.
    """
    last_seq  = scaled_data[-seq_length:].reshape(1, seq_length, -1)
    cur_input = torch.from_numpy(last_seq).float().to(device)
    results   = []

    for _ in range(forecast_days):
        samples = []
        model.train()   # enable dropout for MC sampling
        for _ in range(n_samples):
            with torch.no_grad():
                samples.append(model(cur_input).cpu().numpy().flatten()[0])

        mean_p = float(np.mean(samples))
        std_p  = float(np.std(samples))
        results.append({'mean': mean_p, 'std': std_p})

        # Shift window: insert mean prediction at Close position
        nxt        = np.roll(last_seq[0].copy(), -1, axis=0)
        nxt[-1, 3] = mean_p   # index 3 = Close
        last_seq   = nxt.reshape(1, seq_length, -1)
        cur_input  = torch.from_numpy(last_seq).float().to(device)

    return results
