"""
lstm_predictor.py — Multi-feature LSTM next-day close predictor

Features fed to LSTM (6 inputs instead of 1):
  1. Close price (normalised)
  2. Volume (normalised)
  3. 10-day ROC  — short-term momentum
  4. RSI-14      — overbought/oversold signal
  5. 20-day SMA ratio (close / SMA20) — mean-reversion signal
  6. 10-day volatility (rolling std of returns)

Data split: 80% train | 10% val | 10% test (chronological, no leakage)
Each feature is scaled independently using its OWN scaler fitted only on train.
Early stopping on validation loss. Best weights restored.
"""
import os, joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

MODELS_DIR  = "models"
SEQ_LEN     = 60      # 60-day look-back (3 months) — shorter = less lag
HIDDEN_SIZE = 128
NUM_LAYERS  = 2
EPOCHS      = 150
BATCH_SIZE  = 32
LR          = 5e-4    # lower LR for stability with multi-feature input
PATIENCE    = 15
TRAIN_RATIO = 0.80
VAL_RATIO   = 0.10
N_FEATURES  = 6


# ── Technical indicator helpers ───────────────────────────────────────────────

def _rsi(close: np.ndarray, period: int = 14) -> np.ndarray:
    delta  = np.diff(close, prepend=close[0])
    gain   = np.where(delta > 0, delta, 0.0)
    loss   = np.where(delta < 0, -delta, 0.0)
    avg_g  = np.zeros_like(close)
    avg_l  = np.zeros_like(close)
    # BUG FIX: gain[0] is the diff of close[0]-close[0]=0 (prepend artifact),
    # so the first real gain/loss window is gain[1:period+1].
    # Guard against arrays shorter than period+1.
    if len(close) > period:
        avg_g[period] = gain[1:period+1].mean()
        avg_l[period] = loss[1:period+1].mean()
        for i in range(period + 1, len(close)):
            avg_g[i] = (avg_g[i-1] * (period - 1) + gain[i]) / period
            avg_l[i] = (avg_l[i-1] * (period - 1) + loss[i]) / period
    rs  = np.where(avg_l == 0, 100.0, avg_g / (avg_l + 1e-10))
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi[:period] = 50.0   # fill warm-up with neutral
    return rsi


def _build_features(df: pd.DataFrame) -> np.ndarray:
    """
    Return array of shape (N, N_FEATURES):
      [close, volume, roc10, rsi14, sma20_ratio, vol10]
    """
    close  = df["Close"].values.astype(np.float64)
    volume = df["Volume"].values.astype(np.float64)

    # 10-day Rate of Change
    roc10 = np.zeros_like(close)
    roc10[10:] = (close[10:] - close[:-10]) / (close[:-10] + 1e-10) * 100

    # RSI-14
    rsi14 = _rsi(close, 14)

    # SMA-20 ratio  (how far price is from 20-day mean)
    sma20 = pd.Series(close).rolling(20, min_periods=1).mean().values
    sma_ratio = (close - sma20) / (sma20 + 1e-10) * 100

    # 10-day rolling volatility of daily returns
    returns = np.diff(np.log(close + 1e-10), prepend=0)
    vol10   = pd.Series(returns).rolling(10, min_periods=1).std().fillna(0).values * 100

    return np.column_stack([close, volume, roc10, rsi14, sma_ratio, vol10])


# ── Model ─────────────────────────────────────────────────────────────────────

class LSTMModel(nn.Module):
    def __init__(self, input_size=N_FEATURES, hidden_size=HIDDEN_SIZE,
                 num_layers=NUM_LAYERS, dropout=0.3):
        super().__init__()
        self.lstm    = nn.LSTM(input_size, hidden_size, num_layers,
                               batch_first=True,
                               dropout=dropout if num_layers > 1 else 0.0)
        self.dropout = nn.Dropout(dropout)
        self.fc      = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(self.dropout(out[:, -1, :]))


# ── Paths ─────────────────────────────────────────────────────────────────────

def _paths(ticker):
    base = os.path.join(MODELS_DIR, ticker)
    return (f"{base}_lstm.pth", f"{base}_scalers.pkl", f"{base}_splits.pkl")


# ── Sequence builder ──────────────────────────────────────────────────────────

def _build_sequences(scaled: np.ndarray, seq_len=SEQ_LEN):
    X, y = [], []
    for i in range(seq_len, len(scaled)):
        X.append(scaled[i - seq_len:i])          # (seq_len, N_FEATURES)
        y.append(scaled[i, 0:1])                  # predict close only (feature 0)
    return (torch.from_numpy(np.array(X)).float(),
            torch.from_numpy(np.array(y)).float())


# ── Training ──────────────────────────────────────────────────────────────────

def _train(price_data: pd.DataFrame, ticker: str):
    os.makedirs(MODELS_DIR, exist_ok=True)

    features = _build_features(price_data)   # (N, N_FEATURES)
    n        = len(features)

    train_end = int(n * TRAIN_RATIO)
    val_end   = int(n * (TRAIN_RATIO + VAL_RATIO))

    train_raw = features[:train_end]
    val_raw   = features[train_end:val_end]
    test_raw  = features[val_end:]

    # Fit one scaler per feature — ONLY on training data
    scalers = []
    train_scaled = np.zeros_like(train_raw)
    for i in range(N_FEATURES):
        sc = MinMaxScaler(feature_range=(0, 1))
        train_scaled[:, i] = sc.fit_transform(train_raw[:, i:i+1]).flatten()
        scalers.append(sc)

    def _scale(arr):
        out = np.zeros_like(arr, dtype=np.float32)
        for i, sc in enumerate(scalers):
            out[:, i] = sc.transform(arr[:, i:i+1]).flatten()
        return out

    val_ctx  = np.concatenate([train_raw[-SEQ_LEN:], val_raw])
    test_ctx = np.concatenate([train_raw[-SEQ_LEN:], val_raw, test_raw])

    val_scaled_ctx  = _scale(val_ctx.astype(np.float32))
    test_scaled_ctx = _scale(test_ctx.astype(np.float32))

    X_tr, y_tr = _build_sequences(train_scaled.astype(np.float32))
    X_va, y_va = _build_sequences(val_scaled_ctx)
    X_te, y_te = _build_sequences(test_scaled_ctx)

    print(f"  Multi-feature LSTM  Train:{len(X_tr)} Val:{len(X_va)} Test:{len(X_te)}")

    model     = LSTMModel()
    criterion = nn.MSELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
    loader    = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(X_tr, y_tr),
        batch_size=BATCH_SIZE, shuffle=True
    )

    best_val, best_state, no_imp = float("inf"), None, 0
    train_losses, val_losses = [], []

    for epoch in range(EPOCHS):
        model.train()
        ep_loss = 0.0
        for xb, yb in loader:
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            ep_loss += loss.item() * len(xb)
        tl = ep_loss / len(X_tr)
        train_losses.append(tl)

        model.eval()
        with torch.no_grad():
            vl = criterion(model(X_va), y_va).item()
        val_losses.append(vl)
        scheduler.step()

        if vl < best_val - 1e-7:
            best_val   = vl
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            no_imp     = 0
        else:
            no_imp += 1
            if no_imp >= PATIENCE:
                print(f"  Early stop @ epoch {epoch+1}  best_val={best_val:.7f}")
                break

    model.load_state_dict(best_state)
    model.eval()

    # Test evaluation — inverse transform close-only
    close_sc = scalers[0]
    with torch.no_grad():
        test_pred_sc = model(X_te).numpy()
    test_pred   = close_sc.inverse_transform(test_pred_sc).flatten()
    test_actual = features[val_end + SEQ_LEN: val_end + SEQ_LEN + len(test_pred), 0]
    mn          = min(len(test_pred), len(test_actual))
    test_pred, test_actual = test_pred[:mn], test_actual[:mn]

    mae  = float(np.mean(np.abs(test_pred - test_actual)))
    rmse = float(np.sqrt(np.mean((test_pred - test_actual)**2)))
    mape = float(np.mean(np.abs((test_pred - test_actual) / (test_actual + 1e-8))) * 100)
    ss_res = np.sum((test_actual - test_pred) ** 2)
    ss_tot = np.sum((test_actual - test_actual.mean()) ** 2)
    r2   = float(1 - ss_res / (ss_tot + 1e-10))
    print(f"  Test  MAE=${mae:.2f}  RMSE=${rmse:.2f}  MAPE={mape:.2f}%  R²={r2:.4f}")

    model_path, scalers_path, splits_path = _paths(ticker)
    torch.save(model.state_dict(), model_path)
    joblib.dump(scalers, scalers_path)
    joblib.dump(dict(
        train_end=train_end, val_end=val_end, n_total=n,
        train_losses=train_losses, val_losses=val_losses,
        test_pred=test_pred, test_actual=test_actual,
        test_dates=price_data.index[val_end + SEQ_LEN: val_end + SEQ_LEN + mn].tolist(),
        mae=mae, rmse=rmse, mape=mape, r2=r2, best_val_loss=best_val,
    ), splits_path)

    return model, scalers, dict(
        mae=mae, rmse=rmse, mape=mape, r2=r2, best_val_loss=best_val,
        train_end=train_end, val_end=val_end, n_total=n,
        train_size=len(X_tr), val_size=len(X_va), test_size=len(X_te),
        train_losses=train_losses, val_losses=val_losses,
    )


# ── Inference ─────────────────────────────────────────────────────────────────

def predict_next_price(
    price_data: pd.DataFrame,
    ticker: str = "AAPL",
    force_retrain: bool = False,
) -> tuple[float, dict | None]:
    model_path, scalers_path, splits_path = _paths(ticker)
    metrics = None

    needs_train = (force_retrain or
                   not os.path.exists(model_path) or
                   not os.path.exists(scalers_path))

    if needs_train:
        model, scalers, metrics = _train(price_data, ticker)
    else:
        model = LSTMModel()
        model.load_state_dict(torch.load(model_path, weights_only=True))
        scalers = joblib.load(scalers_path)
        if os.path.exists(splits_path):
            s = joblib.load(splits_path)
            metrics = {k: s[k] for k in
                       ["mae","rmse","mape","r2","best_val_loss","train_end",
                        "val_end","n_total","train_losses","val_losses"] if k in s}

    model.eval()

    features = _build_features(price_data)
    if len(features) < SEQ_LEN:
        raise ValueError(f"Need ≥{SEQ_LEN} data points (got {len(features)}).")

    window = features[-SEQ_LEN:].astype(np.float32)
    scaled_window = np.zeros_like(window)
    for i, sc in enumerate(scalers):
        scaled_window[:, i] = sc.transform(window[:, i:i+1]).flatten()

    X = torch.from_numpy(scaled_window.reshape(1, SEQ_LEN, N_FEATURES)).float()
    with torch.no_grad():
        pred_sc = model(X).numpy()

    predicted = float(scalers[0].inverse_transform(pred_sc)[0][0])
    return predicted, metrics
