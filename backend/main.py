"""
main.py — FastAPI Backend Server for TELLIN Crypto Quantitative Terminal.
Exposes REST endpoints for:
  - TradingView symbol validation & exchange ticker resolution
  - Real-time multi-source crypto statistics & DEX metrics
  - Alternative.me Fear & Greed Index trajectory
  - Scraped live crypto & geopolitical news feeds
  - DeepSeek V3 AI speculative hypothesis & final verdict
  - 4-Tier crypto drawdown regimes & historical person movements ledger
  - Deep institutional macro research memorandum & market psychology dossier
"""
import os
import sys
import json
import math
import pathlib
import time
from typing import Dict, Any, Optional
import numpy as np

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel

# Add current backend folder to path
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from dotenv import load_dotenv
env_file = pathlib.Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv()

import fetcher
import news_scraper
import drawdown_engine
import ai_analyst
import whale_engine
# ── CLEAN JSON RESPONSE (IEEE 754 FLOAT SANITIZER) ───────────────────────────
def sanitize_nan(obj):
    if isinstance(obj, (float, np.floating)):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, (int, np.integer)):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return [sanitize_nan(v) for v in obj.tolist()]
    elif isinstance(obj, dict):
        return {k: sanitize_nan(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_nan(v) for v in obj]
    return obj

class CleanJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            sanitize_nan(content),
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":")
        ).encode("utf-8")

# ── APP INITIALIZATION ────────────────────────────────────────────────────────
app = FastAPI(
    title="TELLIN Crypto Terminal API",
    description="Institutional Crypto Quantitative, Geopolitical & Analytical Intelligence Terminal",
    version="1.0.0",
    default_response_class=CleanJSONResponse
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

# ── Pydantic Request Models ───────────────────────────────────────────────────
class KeyUpdateRequest(BaseModel):
    api_key: str

# ── REST ENDPOINTS ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serves the single-page Neo-Brutalist Black & Green Terminal UI."""
    candidates = [
        BASE_DIR / "frontend" / "index.html",
        pathlib.Path("frontend/index.html"),
        pathlib.Path("index.html"),
        pathlib.Path(__file__).resolve().parent.parent / "frontend" / "index.html",
        pathlib.Path(__file__).resolve().parent / "index.html",
    ]
    for c in candidates:
        if c.exists():
            headers = {
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            }
            return HTMLResponse(c.read_text(encoding="utf-8"), headers=headers)
    return HTMLResponse("<h1>TELLIN Crypto Terminal — Frontend Initializing</h1>", status_code=200)

@app.get("/api/health")
def get_health():
    """System health and active data feed verification."""
    return {
        "status": "ONLINE",
        "terminal": "TELLIN Crypto Quantitative Intelligence Terminal",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "ai_model": ai_analyst.DEEPSEEK_MODEL,
        "ai_configured": bool(ai_analyst.DEEPSEEK_API_KEY)
    }

@app.get("/api/tv-validate")
async def validate_tv_symbol(symbol: str = Query(..., description="Coin symbol or trading pair")):
    """
    Validates whether a symbol exists on TradingView crypto feeds.
    Returns exact exchange ticker (e.g. BINANCE:BTCUSDT) or signals non-existence.
    """
    res = await run_in_threadpool(fetcher.validate_tradingview_symbol, symbol)
    return res

@app.get("/api/screener")
async def get_screener():
    """Returns real-time prices, 24h changes, and market caps for top screener assets."""
    rows = await run_in_threadpool(fetcher.fetch_screener_overview)
    return {"universe": rows, "count": len(rows)}

@app.get("/api/fng")
async def get_fear_and_greed(limit: int = Query(30, ge=1, le=100)):
    """Fetches Alternative.me Crypto Fear & Greed Index and 30-day psychological trajectory."""
    data = await run_in_threadpool(fetcher.fetch_fear_and_greed, limit)
    return data

@app.get("/api/coin/{symbol}")
async def get_coin_overview(symbol: str):
    """
    Aggregates full statistics for a coin:
    - Real-time DEX metrics (price, liquidity, volume, FDV, 5m/1h/6h/24h changes)
    - Historical multi-timeframe performance (24h, 7d, 30d, 90d, 180d, 1Y, YTD, Cycle)
    - ATH price, date, and current drawdown from ATH
    - TradingView symbol resolution
    """
    clean_sym = symbol.strip().upper()

    # 1. Fetch yfinance historical performance & ATH
    try:
        hist_data = await run_in_threadpool(fetcher.fetch_crypto_history, clean_sym, years=5)
    except Exception as e:
        hist_data = None

    # 2. Fetch DexScreener real-time spot & liquidity metrics
    dex_data = await run_in_threadpool(fetcher.fetch_dexscreener_data, clean_sym)

    # 3. Resolve TradingView symbol
    tv_data = await run_in_threadpool(fetcher.validate_tradingview_symbol, clean_sym)

    # Reconcile spot price and 24h change
    if dex_data and dex_data.get("price_usd"):
        spot_price = dex_data["price_usd"]
        chg_24 = dex_data.get("change_24h", 0.0)
        mcap = dex_data.get("market_cap") or dex_data.get("fdv", 0.0)
    elif hist_data:
        spot_price = hist_data["current_price"]
        chg_24 = hist_data["performance"].get("ret_24h") or 0.0
        mcap = 0.0
    else:
        raise HTTPException(status_code=404, detail=f"No market data found for symbol '{clean_sym}'")

    ath_price = hist_data["ath_price"] if hist_data else spot_price
    ath_date = hist_data["ath_date"] if hist_data else "N/A"
    dd_ath = round(((spot_price - ath_price) / ath_price) * 100.0, 2) if ath_price > 0 else 0.0

    return {
        "symbol": clean_sym,
        "name": dex_data.get("base_name", clean_sym) if dex_data else clean_sym,
        "price_usd": spot_price,
        "price_fmt": fetcher.fmt_currency(spot_price),
        "change_24h": chg_24,
        "ath_price": ath_price,
        "ath_date": ath_date,
        "drawdown_from_ath_pct": dd_ath,
        "market_cap": mcap,
        "market_cap_fmt": fetcher.fmt_currency(mcap),
        "performance": hist_data.get("performance", {}) if hist_data else {},
        "dex_metrics": dex_data,
        "tradingview": tv_data,
        "candles_sample": hist_data.get("candles", [])[-60:] if hist_data else []
    }
# ── IN-MEMORY CACHE FOR EXPENSIVE ENDPOINTS ──────────────────────────────────
_ENDPOINT_CACHE: Dict[str, Any] = {}

def get_endpoint_cache(key: str, ttl: float = 600.0) -> Optional[Any]:
    entry = _ENDPOINT_CACHE.get(key)
    if entry and (time.time() - entry["ts"] < ttl):
        return entry["val"]
    return None

def set_endpoint_cache(key: str, val: Any) -> None:
    _ENDPOINT_CACHE[key] = {"val": val, "ts": time.time()}

@app.get("/api/news/{symbol}")
async def get_news_and_geopolitics(symbol: str):
    """
    Scrapes live Google News and CoinTelegraph articles categorized by vector.
    """
    clean_sym = symbol.strip().upper()
    cache_key = f"news_api_{clean_sym}"
    cached = get_endpoint_cache(cache_key, ttl=180.0)
    if cached:
        return cached

    name_map = {"BTC": "Bitcoin", "ETH": "Ethereum", "SOL": "Solana", "BNB": "BNB", "XRP": "XRP", "DOGE": "Dogecoin"}
    coin_name = name_map.get(clean_sym, clean_sym)
    news_data = await run_in_threadpool(news_scraper.get_crypto_news_and_geopolitics, coin_name, clean_sym)
    set_endpoint_cache(cache_key, news_data)
    return news_data

@app.get("/api/hypothesis/{symbol}")
@app.post("/api/hypothesis/{symbol}")
async def get_news_hypothesis(symbol: str):
    """
    Section 2 Engine: DeepSeek V3 AI Hypothesis & Verdict with 10-min cache.
    """
    clean_sym = symbol.strip().upper()
    cache_key = f"hypo_api_{clean_sym}"
    cached = get_endpoint_cache(cache_key, ttl=600.0)
    if cached:
        return cached

    name_map = {"BTC": "Bitcoin", "ETH": "Ethereum", "SOL": "Solana", "BNB": "BNB", "XRP": "XRP", "DOGE": "Dogecoin"}
    coin_name = name_map.get(clean_sym, clean_sym)

    # 1. Fetch news
    news_data = await run_in_threadpool(news_scraper.get_crypto_news_and_geopolitics, coin_name, clean_sym)

    # 2. Fetch spot price
    try:
        hist = await run_in_threadpool(fetcher.fetch_crypto_history, clean_sym, years=1)
        price = hist["current_price"]
    except Exception:
        dex = await run_in_threadpool(fetcher.fetch_dexscreener_data, clean_sym)
        price = dex.get("price_usd", 1.0) if dex else 1.0

    # 3. Generate AI hypothesis
    hypothesis_data = await run_in_threadpool(
        ai_analyst.generate_news_hypothesis_and_verdict,
        coin_name, clean_sym, news_data, price
    )
    res = {
        "symbol": clean_sym,
        "price_usd": price,
        "news_meta": {
            "total_articles": news_data.get("total_articles"),
            "sentiment_label": news_data.get("sentiment_label"),
            "sentiment_color": news_data.get("sentiment_color"),
            "net_score": news_data.get("net_sentiment_score")
        },
        "hypothesis": hypothesis_data
    }
    set_endpoint_cache(cache_key, res)
    return res

@app.get("/api/drawdowns/{symbol}")
async def get_drawdown_regimes(symbol: str):
    """
    Section 3 Engine: 4 Canonical Drawdown Regimes with 10-min cache.
    """
    clean_sym = symbol.strip().upper()
    cache_key = f"dd_api_{clean_sym}"
    cached = get_endpoint_cache(cache_key, ttl=600.0)
    if cached:
        return cached

    try:
        hist = await run_in_threadpool(fetcher.fetch_crypto_history, clean_sym, years=5)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Historical data unavailable for {clean_sym}: {str(e)}")

    dd_result = await run_in_threadpool(
        drawdown_engine.compute_crypto_drawdown_regimes,
        hist["candles"], hist["current_price"]
    )
    dd_result["symbol"] = clean_sym
    dd_result["current_price"] = hist["current_price"]
    dd_result["ath_price"] = hist["ath_price"]
    dd_result["drawdown_from_ath_pct"] = hist["drawdown_from_ath_pct"]
    set_endpoint_cache(cache_key, dd_result)
    return dd_result

@app.get("/api/deep-memo/{symbol}")
@app.post("/api/deep-memo/{symbol}")
async def get_deep_ai_memo(symbol: str):
    """
    Section 4 Engine: Full Deep AI Memo with 15-min cache.
    """
    clean_sym = symbol.strip().upper()
    cache_key = f"memo_api_{clean_sym}"
    cached = get_endpoint_cache(cache_key, ttl=900.0)
    if cached:
        return cached

    name_map = {"BTC": "Bitcoin", "ETH": "Ethereum", "SOL": "Solana", "BNB": "BNB", "XRP": "XRP", "DOGE": "Dogecoin"}
    coin_name = name_map.get(clean_sym, clean_sym)

    hist = await run_in_threadpool(fetcher.fetch_crypto_history, clean_sym, years=5)
    fng = await run_in_threadpool(fetcher.fetch_fear_and_greed, 30)
    news_data = await run_in_threadpool(news_scraper.get_crypto_news_and_geopolitics, coin_name, clean_sym)
    dd_data = await run_in_threadpool(drawdown_engine.compute_crypto_drawdown_regimes, hist["candles"], hist["current_price"])

    memo = await run_in_threadpool(
        ai_analyst.generate_full_ai_psychology_memo,
        coin_name, clean_sym, hist, fng, news_data, dd_data
    )
    res = {
        "symbol": clean_sym,
        "coin_name": coin_name,
        "fng_summary": {
            "value": fng.get("current_value"),
            "classification": fng.get("classification"),
            "psychology_phase": fng.get("psychology_phase")
        },
        "memorandum": memo
    }
    set_endpoint_cache(cache_key, res)
    return res
@app.get("/api/insider-whales/{symbol}")
async def get_insider_whale_intel(symbol: str):
    """
    Section 5 Engine:
    Authentic Corporate Treasuries (CoinGecko), Spot ETF & MSTR Proxies (yfinance),
    On-Chain DEX order flow, Smart Money vs. Retail Divergence, and DeepSeek V3 Institutional Synthesis.
    """
    clean_sym = symbol.strip().upper()
    data = await run_in_threadpool(whale_engine.get_comprehensive_insider_whale_intelligence, clean_sym)
    return data

@app.post("/api/settings/key")
def update_api_key(req: KeyUpdateRequest):
    """Dynamically updates the DeepSeek API key at runtime."""
    new_key = req.api_key.strip()
    if not new_key:
        raise HTTPException(status_code=400, detail="API key cannot be empty")
    ai_analyst.DEEPSEEK_API_KEY = new_key
    return {"status": "SUCCESS", "message": "DeepSeek API key updated successfully", "key_prefix": new_key[:8] + "..."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3001))
    host = os.environ.get("HOST", "0.0.0.0")
    backend_dir = str(pathlib.Path(__file__).parent.resolve())
    print(f"Starting TELLIN Crypto Terminal server on http://127.0.0.1:{port}")
    uvicorn.run("main:app", host=host, port=port, app_dir=backend_dir, reload=True)
