"""
llm_sentiment.py — LLM-powered sentiment via Groq
Returns structured scores + rich evidence cards
"""
import os, json, re
from groq import Groq
from dotenv import load_dotenv

load_dotenv("keys.env")

_client: Groq | None = None

def _get_client() -> Groq:
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise EnvironmentError("GROQ_API_KEY not set in keys.env")
        _client = Groq(api_key=key)
    return _client

def _extract_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    text = text.replace("\\n", " ").replace("\\t", " ")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        candidate = re.sub(r"[\x00-\x1f\x7f]", " ", match.group())
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    raise ValueError(f"No valid JSON in: {text!r}")

def _clamp(v: float, lo=-1.0, hi=1.0) -> float:
    return max(lo, min(hi, v))


def get_sentiment_and_summary(
    articles: list[dict],
    ticker: str = "AAPL",
    max_articles: int = 5,
) -> tuple[float, list[dict]]:
    """
    Returns:
        avg_score : float in [-1, 1]
        evidence  : list of rich dicts with keys:
                    source, title, score, summary, reasoning, quote, label
    """
    if not articles:
        return 0.0, []

    client = _get_client()
    scores: list[float] = []
    evidence: list[dict] = []

    for article in articles[:max_articles]:
        title       = article.get("title", "").strip()
        description = article.get("description", "").strip()
        source      = article.get("source", {}).get("name", "Unknown")
        url         = article.get("url", "")
        published_display = article.get("publishedAt", "")[:10] if article.get("publishedAt") else ""
        published_iso     = article.get("publishedAt", "")  # full ISO for recency calc in ensemble

        if not title:
            continue

        prompt = (
            f"You are a financial analyst. Evaluate the stock market impact of this news on {ticker}.\n\n"
            f"Source: {source}\nTitle: {title}\nDescription: {description}\n\n"
            "Reply with ONLY a single-line JSON object. No markdown, no newlines inside JSON:\n"
            '{"summary": "one sentence market impact", "score": 0.5, '
            '"reasoning": "one sentence why", "quote": "key phrase", '
            '"impact_horizon": "short-term|medium-term|long-term"}\n\n'
            "score: -1.0 (very bearish) to 1.0 (very bullish)."
        )

        try:
            resp  = _get_client().chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=300,
            )
            raw    = resp.choices[0].message.content.strip()
            result = _extract_json(raw)

            score   = _clamp(float(result.get("score", 0.0)))
            scores.append(score)

            label = ("Bullish" if score > 0.1 else
                     "Bearish" if score < -0.1 else "Neutral")

            evidence.append(dict(
                source    = source,
                title     = title,
                score     = score,
                label     = label,
                summary   = result.get("summary", ""),
                reasoning = result.get("reasoning", ""),
                quote     = result.get("quote", title[:80]),
                horizon   = result.get("impact_horizon", "short-term"),
                url       = url,
                published = published_display,   # human-readable date for UI cards
                published_iso = published_iso,   # full ISO string for recency weighting
            ))

        except Exception as exc:
            scores.append(0.0)
            evidence.append(dict(
                source=source, title=title, score=0.0, label="Neutral",
                summary="Could not analyse this article.",
                reasoning=str(exc), quote=title[:80],
                horizon="unknown", url=url,
                published=published_display, published_iso=published_iso,
            ))

    avg = sum(scores) / len(scores) if scores else 0.0
    return avg, evidence
