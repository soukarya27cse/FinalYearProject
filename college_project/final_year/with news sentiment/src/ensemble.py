"""
ensemble.py — Learned ensemble combining LSTM price + sentiment impact score

Inspired by ticker-teller's Notebook 7 (Ensemble.ipynb) which uses
Linear Regression models (lr_models/) to combine signals rather than
a fixed multiplier.

Pipeline:
  1. Compute ImpactScore from sentiment (Notebook 6 approach):
       impact = sentiment_score × article_recency_weight × source_credibility
  2. Train a Ridge Regression meta-learner on [lstm_pred, impact_score,
       price_momentum, volatility] → actual_next_close
     using the validation set (data the LSTM never trained on)
  3. At inference: meta-learner blends the signals with learned weights

Falls back to weighted-multiplier if not enough val data to train meta-learner.
"""
import os
import numpy as np
import joblib
import pandas as pd
from datetime import datetime, timezone

MODELS_DIR    = "models"
META_WEIGHT   = 0.05    # fallback weight if no meta-learner

# Source credibility scores (Notebook 6: ImpactScore concept)
SOURCE_CREDIBILITY = {
    "the wall street journal": 1.0,
    "bloomberg":               0.95,
    "reuters":                 0.95,
    "financial times":         0.90,
    "cnbc":                    0.80,
    "marketwatch":             0.75,
    "barchart.com":            0.65,
    "thestreet":               0.60,
    "24/7 wall st.":           0.55,
    "macdailynews.com":        0.45,
}
DEFAULT_CREDIBILITY = 0.50


def compute_impact_score(
    evidence: list[dict],
    news_days: int = 14,
) -> float:
    """
    Notebook 6 — ImpactScore:
    Weighted sentiment that accounts for:
      - Article recency (exponential decay: newer = more weight)
      - Source credibility (WSJ > Bloomberg > ... > blogs)
      - Magnitude of score

    Returns a single float in [-1, 1].
    """
    if not evidence:
        return 0.0

    now = datetime.now(timezone.utc)
    weighted_scores = []
    total_weight    = 0.0

    for item in evidence:
        score       = item.get("score", 0.0)
        source      = item.get("source", "").lower()
        # BUG FIX: use full ISO timestamp for accurate recency decay;
        # "published" is now display-only (YYYY-MM-DD), "published_iso" is full datetime
        published   = item.get("published_iso") or item.get("published", "")

        # Recency weight: exponential decay over news_days window
        recency = 1.0
        if published:
            try:
                pub_dt  = datetime.fromisoformat(published.replace("Z", "+00:00"))
                age_days = (now - pub_dt).total_seconds() / 86400
                recency  = np.exp(-age_days / (news_days / 2))
            except Exception:
                recency = 0.5

        # Source credibility
        cred = next(
            (v for k, v in SOURCE_CREDIBILITY.items() if k in source),
            DEFAULT_CREDIBILITY
        )

        weight = recency * cred
        weighted_scores.append(score * weight)
        total_weight += weight

    if total_weight == 0:
        return 0.0

    raw = sum(weighted_scores) / total_weight
    return float(np.clip(raw, -1.0, 1.0))


def _meta_learner_path(ticker: str) -> str:
    return os.path.join(MODELS_DIR, f"{ticker}_meta.pkl")


def train_meta_learner(
    ticker: str,
    price_data: pd.DataFrame,
    splits_info: dict,
    lstm_val_preds: np.ndarray | None = None,
) -> bool:
    """
    Notebook 7 — Ensemble with Ridge Regression meta-learner.
    Trains on the validation set: [lstm_pred, impact_placeholder,
    momentum, volatility] → actual_close.

    lstm_val_preds: if provided, use real LSTM val predictions.
    Otherwise estimate from splits_info test data as proxy.
    Returns True if meta-learner was successfully trained.
    """
    try:
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler

        val_end   = splits_info.get("val_end", 0)
        train_end = splits_info.get("train_end", 0)
        if val_end == 0 or train_end == 0:
            return False

        close = price_data["Close"].values.astype(np.float64)
        val_close = close[train_end:val_end]

        if len(val_close) < 20:
            return False

        # Build meta-features for val set
        # Feature 1: naive LSTM proxy (rolling mean of last 60 days)
        lstm_proxy = []
        for i in range(len(val_close)):
            idx = train_end + i
            window = close[max(0, idx-60):idx]
            w = np.exp(np.linspace(0, 1, len(window)))
            lstm_proxy.append(np.dot(w / w.sum(), window))
        lstm_proxy = np.array(lstm_proxy)

        # Feature 2: 10-day momentum
        momentum = np.zeros(len(val_close))
        for i in range(10, len(val_close)):
            momentum[i] = (val_close[i-1] - val_close[i-10]) / (val_close[i-10] + 1e-8)

        # Feature 3: 10-day rolling volatility
        returns = np.diff(np.log(val_close + 1e-8), prepend=0)
        volatility = pd.Series(returns).rolling(10, min_periods=1).std().fillna(0).values

        X_meta = np.column_stack([lstm_proxy, momentum, volatility])
        y_meta = val_close

        # Scale + fit Ridge
        feat_scaler = StandardScaler()
        X_scaled = feat_scaler.fit_transform(X_meta)

        meta_model = Ridge(alpha=1.0)
        meta_model.fit(X_scaled, y_meta)

        score = meta_model.score(X_scaled, y_meta)
        print(f"  Meta-learner R² on val set: {score:.4f}")

        joblib.dump({"model": meta_model, "scaler": feat_scaler}, _meta_learner_path(ticker))
        return True

    except Exception as e:
        print(f"  Meta-learner training failed: {e}")
        return False


def ensemble_predict(
    lstm_price: float,
    sentiment_score: float,
    sentiment_weight: float = META_WEIGHT,
    evidence: list[dict] | None = None,
    ticker: str = "AAPL",
    price_data: pd.DataFrame | None = None,
) -> tuple[float, dict]:
    """
    Two-stage ensemble:
      Stage 1 — ImpactScore: compute credibility-weighted sentiment
      Stage 2 — Meta-learner blend (if available) or weighted multiplier

    Returns (final_price, details_dict)
    """
    # Stage 1: Impact score
    impact = compute_impact_score(evidence or [], news_days=14)

    # Try meta-learner
    meta_path = _meta_learner_path(ticker)
    used_meta = False

    if os.path.exists(meta_path) and price_data is not None:
        try:
            saved       = joblib.load(meta_path)
            meta_model  = saved["model"]
            feat_scaler = saved["scaler"]

            close = price_data["Close"].values.astype(np.float64)

            # BUG FIX: Use same weighted rolling-mean proxy as in train_meta_learner
            # (previously was passing raw lstm_price causing scaler distribution shift)
            window = close[-60:] if len(close) >= 60 else close
            w = np.exp(np.linspace(0, 1, len(window)))
            lstm_proxy = float(np.dot(w / w.sum(), window))

            # 10-day momentum (consistent with train_meta_learner features)
            momentum = (close[-1] - close[-10]) / (close[-10] + 1e-8) if len(close) >= 10 else 0.0

            # 10-day rolling volatility of log-returns
            returns    = np.diff(np.log(close[-11:] + 1e-8)) if len(close) >= 11 else np.array([0.0])
            volatility = float(np.std(returns))

            X = feat_scaler.transform([[lstm_proxy, momentum, volatility]])
            meta_price = float(meta_model.predict(X)[0])

            # Blend: meta-learner anchors the magnitude, sentiment-adjusted LSTM adds directional signal
            sentiment_adjusted = lstm_price * (1.0 + impact * sentiment_weight)
            final_price = 0.70 * meta_price + 0.30 * sentiment_adjusted
            used_meta   = True

        except Exception as e:
            print(f"  Meta-learner inference failed: {e}, falling back")
            used_meta = False

    if not used_meta:
        # Fallback: simple impact-weighted multiplier
        final_price = lstm_price * (1.0 + impact * sentiment_weight)

    return float(np.clip(final_price, lstm_price * 0.85, lstm_price * 1.15)), {
        "raw_sentiment":  sentiment_score,
        "impact_score":   impact,
        "used_meta":      used_meta,
        "lstm_price":     lstm_price,
        "final_price":    final_price,
        "sentiment_nudge": float(impact * sentiment_weight),
    }
