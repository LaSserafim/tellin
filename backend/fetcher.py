"""
fetcher.py — Multi-Source Crypto Market Ingestion & TradingView Symbol Validator.
Aggregates live market intelligence across:
  1. TradingView Symbol Search API (validates existence and resolves connected exchange tickers)
  2. DexScreener REST API (real-time DEX liquidity, multi-timeframe changes: 5m, 1h, 6h, 24h, FDV)
  3. Alternative.me Crypto Fear & Greed Index (current score + 30-day sentiment trajectory)
  4. Yahoo Finance (long-term multi-year daily OHLCV series for drawdown and cycle performance)
"""
import json
import time
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
import yfinance as yf
import pandas as pd
import numpy as np

# ── IN-MEMORY CACHE WITH TTL ──────────────────────────────────────────────────
_CACHE: Dict[str, Any] = {}

def get_cache(key: str, ttl: float = 30.0) -> Optional[Any]:
    entry = _CACHE.get(key)
    if entry and (time.time() - entry["ts"] < ttl):
        return entry["val"]
    return None

def set_cache(key: str, val: Any) -> None:
    _CACHE[key] = {"val": val, "ts": time.time()}

# ── SAFE NUMERICAL HELPERS ───────────────────────────────────────────────────
def safe_float(val, default: float = 0.0, decimals: Optional[int] = None) -> float:
    try:
        if val is None:
            return default
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return default
        return round(f, decimals) if decimals is not None else f
    except (ValueError, TypeError):
        return default

def fmt_currency(val: Optional[float], prefix: str = "$") -> str:
    if val is None or np.isnan(val):
        return "N/A"
    abs_v = abs(val)
    if abs_v >= 1e12:
        return f"{prefix}{val / 1e12:.2f}T"
    if abs_v >= 1e9:
        return f"{prefix}{val / 1e9:.2f}B"
    if abs_v >= 1e6:
        return f"{prefix}{val / 1e6:.2f}M"
    if abs_v >= 1e3:
        return f"{prefix}{val / 1e3:.2f}K"
    if abs_v < 0.0001:
        return f"{prefix}{val:.8f}"
    if abs_v < 1.0:
        return f"{prefix}{val:.4f}"
    return f"{prefix}{val:,.2f}"

# ── 1. TRADINGVIEW SYMBOL VALIDATION & RESOLVER ──────────────────────────────
def validate_tradingview_symbol(query: str) -> Dict[str, Any]:
    """
    Queries TradingView symbol search API to check whether a coin/pair exists.
    Returns exchange-qualified ticker (e.g. BINANCE:BTCUSDT) or signals non-existence.
    """
    clean_q = query.strip().upper().replace("/", "").replace("-", "")
    cache_key = f"tv_search_{clean_q}"
    cached = get_cache(cache_key, ttl=300)
    if cached:
        return cached

    # Common crypto suffixes to test
    candidates = [clean_q]
    if not any(clean_q.endswith(sfx) for sfx in ["USDT", "USD", "USDC", "PERP"]):
        candidates.extend([f"{clean_q}USDT", f"{clean_q}USD"])

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://www.tradingview.com",
        "Referer": "https://www.tradingview.com/"
    }

    found_matches = []
    for test_text in candidates:
        encoded_text = urllib.parse.quote(test_text)
        url = f"https://symbol-search.tradingview.com/symbol_search/v3/?text={encoded_text}&hl=1&exchange=&lang=en&search_type=crypto&domain=production"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                symbols = data.get("symbols", [])
                if symbols:
                    for s in symbols:
                        sym = s.get("symbol", "").replace("<em>", "").replace("</em>", "")
                        exch = s.get("exchange", "")
                        desc = s.get("description", "")
                        tv_ticker = f"{exch}:{sym}" if exch else sym
                        found_matches.append({
                            "symbol": sym,
                            "exchange": exch,
                            "full_ticker": tv_ticker,
                            "description": desc,
                            "type": s.get("type", "crypto")
                        })
                    break
        except Exception:
            continue

    if found_matches:
        # Prioritize top liquid exchanges: Binance, Coinbase, Bybit, OKX, Kraken
        preferred_exchanges = ["BINANCE", "COINBASE", "BYBIT", "OKX", "KRAKEN", "BITSTAMP", "UNISWAP", "RAYDIUM"]
        best_match = found_matches[0]
        for pref in preferred_exchanges:
            match = next((m for m in found_matches if m["exchange"].upper() == pref), None)
            if match:
                best_match = match
                break

        res = {
            "exists": True,
            "query": query,
            "best_ticker": best_match["full_ticker"],
            "exchange": best_match["exchange"],
            "symbol": best_match["symbol"],
            "description": best_match["description"],
            "matches_count": len(found_matches),
            "matches": found_matches[:6]
        }
    else:
        res = {
            "exists": False,
            "query": query,
            "best_ticker": None,
            "exchange": None,
            "symbol": clean_q,
            "description": None,
            "matches_count": 0,
            "matches": [],
            "error_message": f"Symbol '{query}' does not exist on TradingView crypto feeds."
        }

    set_cache(cache_key, res)
    return res

# ── 2. DEXSCREENER DATA INGESTION ─────────────────────────────────────────────
def fetch_dexscreener_data(coin_query: str) -> Optional[Dict[str, Any]]:
    """
    Fetches real-time price, liquidity, volume, FDV, and 5m/1h/6h/24h performance from DexScreener.
    Works for both major coins (BTC, ETH, SOL) and decentralized tokens.
    """
    clean_q = coin_query.strip().upper()
    cache_key = f"dex_{clean_q}"
    cached = get_cache(cache_key, ttl=15)
    if cached:
        return cached

    url = f"https://api.dexscreener.com/latest/dex/search?q={urllib.parse.quote(clean_q)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pairs = data.get("pairs", [])
            if not pairs:
                return None

            # Sort pairs by highest USD liquidity
            valid_pairs = sorted(
                pairs,
                key=lambda p: safe_float(p.get("liquidity", {}).get("usd", 0.0)),
                reverse=True
            )
            top_pair = valid_pairs[0]

            base_token = top_pair.get("baseToken", {})
            quote_token = top_pair.get("quoteToken", {})
            price_change = top_pair.get("priceChange", {})
            volume = top_pair.get("volume", {})
            liquidity = top_pair.get("liquidity", {})
            txns = top_pair.get("txns", {})

            res = {
                "pair_address": top_pair.get("pairAddress"),
                "dex_id": top_pair.get("dexId", "").upper(),
                "chain_id": top_pair.get("chainId", "").upper(),
                "base_symbol": base_token.get("symbol", clean_q),
                "base_name": base_token.get("name", clean_q),
                "quote_symbol": quote_token.get("symbol", "USD"),
                "price_usd": safe_float(top_pair.get("priceUsd")),
                "price_native": safe_float(top_pair.get("priceNative")),
                "market_cap": safe_float(top_pair.get("marketCap")),
                "fdv": safe_float(top_pair.get("fdv")),
                "liquidity_usd": safe_float(liquidity.get("usd")),
                "volume_24h": safe_float(volume.get("h24")),
                "volume_6h": safe_float(volume.get("h6")),
                "volume_1h": safe_float(volume.get("h1")),
                "change_5m": safe_float(price_change.get("m5")),
                "change_1h": safe_float(price_change.get("h1")),
                "change_6h": safe_float(price_change.get("h6")),
                "change_24h": safe_float(price_change.get("h24")),
                "buys_24h": int(safe_float(txns.get("h24", {}).get("buys", 0))),
                "sells_24h": int(safe_float(txns.get("h24", {}).get("sells", 0))),
                "pair_url": top_pair.get("url", "")
            }
            set_cache(cache_key, res)
            return res
    except Exception as e:
        return None

# ── 3. FEAR & GREED SENTIMENT TRAJECTORY ──────────────────────────────────────
def fetch_fear_and_greed(limit: int = 30) -> Dict[str, Any]:
    """
    Ingests Alternative.me Crypto Fear & Greed Index with historical trend.
    """
    cache_key = f"fng_{limit}"
    cached = get_cache(cache_key, ttl=300)
    if cached:
        return cached

    url = f"https://api.alternative.me/fng/?limit={limit}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            data_list = raw.get("data", [])
            if not data_list:
                raise ValueError("Empty FNG data")

            current = data_list[0]
            val = int(safe_float(current.get("value", 50)))
            classification = current.get("value_classification", "Neutral")

            history = []
            for item in data_list:
                history.append({
                    "timestamp": int(item.get("timestamp", 0)),
                    "date": time.strftime("%Y-%m-%d", time.gmtime(int(item.get("timestamp", 0)))),
                    "value": int(safe_float(item.get("value", 50))),
                    "classification": item.get("value_classification", "Neutral")
                })

            # Calculate 7-day and 30-day sentiment momentum
            val_7d_ago = history[min(6, len(history) - 1)]["value"]
            val_30d_ago = history[-1]["value"]

            # Psychology regime diagnosis
            if val <= 20:
                psychology_phase = "CAPITULATION & MAXIMUM DESPAIR (Deep Value Accumulation Zone)"
                color = "#00f59b"  # Contrarian buy in black/green terminal
            elif val <= 40:
                psychology_phase = "FEAR & UNCERTAINTY (Selective DCA Accumulation)"
                color = "#3b82f6"
            elif val <= 55:
                psychology_phase = "NEUTRAL INDECISION (Consolidation Equilibrium)"
                color = "#94a3b8"
            elif val <= 75:
                psychology_phase = "OPTIMISM & GREED (Late Expansion / Partial Profit Lock)"
                color = "#f59e0b"
            else:
                psychology_phase = "EXTREME EUPHORIA & COMPLACENCY (High Leverage Exhaustion Risk)"
                color = "#ff3b5c"

            res = {
                "current_value": val,
                "classification": classification,
                "psychology_phase": psychology_phase,
                "color": color,
                "change_7d": val - val_7d_ago,
                "change_30d": val - val_30d_ago,
                "history": history
            }
            set_cache(cache_key, res)
            return res
    except Exception as e:
        # Fallback default neutral
        return {
            "current_value": 50,
            "classification": "Neutral",
            "psychology_phase": "EQUILIBRIUM (Deterministic Fallback)",
            "color": "#94a3b8",
            "change_7d": 0,
            "change_30d": 0,
            "history": []
        }

# ── 4. HISTORICAL OHLCV & MULTI-TIMEFRAME PERFORMANCE ────────────────────────
def resolve_yfinance_ticker(coin_symbol: str) -> str:
    """Normalizes crypto symbol to yfinance format (e.g. BTC -> BTC-USD)."""
    sym = coin_symbol.strip().upper().replace("/", "").replace("-", "")
    for sfx in ["USDT", "USD", "USDC"]:
        if sym.endswith(sfx) and len(sym) > len(sfx):
            sym = sym[:-len(sfx)]
            break
    return f"{sym}-USD"

def fetch_crypto_history(coin_symbol: str, years: int = 5) -> Dict[str, Any]:
    """
    Fetches multi-year daily history from yfinance and calculates multi-timeframe returns,
    ATH, current drawdown from ATH, and performance periods.
    """
    yf_symbol = resolve_yfinance_ticker(coin_symbol)
    cache_key = f"hist_{yf_symbol}_{years}"
    cached = get_cache(cache_key, ttl=60)
    if cached:
        return cached

    period_str = f"{years}y" if years <= 10 else "max"
    ticker = yf.Ticker(yf_symbol)
    df = ticker.history(period=period_str, interval="1d")

    if df.empty or len(df) < 5:
        # Try max fallback
        df = ticker.history(period="max", interval="1d")

    if df.empty or len(df) < 5:
        raise ValueError(f"Unable to load historical price series for {coin_symbol} ({yf_symbol})")

    # Clean columns
    df = df.dropna(subset=["Close"])
    closes = df["Close"].values
    highs = df["High"].values
    lows = df["Low"].values
    dates = [d.strftime("%Y-%m-%d") for d in df.index]

    current_price = safe_float(closes[-1])
    ath_price = safe_float(np.max(highs))
    ath_idx = int(np.argmax(highs))
    ath_date = dates[ath_idx]
    drawdown_from_ath_pct = round(((current_price - ath_price) / ath_price) * 100.0, 2) if ath_price > 0 else 0.0

    # Calculate returns for specific performance windows
    def calc_window_return(lookback_days: int) -> Optional[float]:
        if len(closes) > lookback_days:
            start_p = closes[-1 - lookback_days]
            if start_p > 0:
                return round(((current_price - start_p) / start_p) * 100.0, 2)
        return None

    # Calculate YTD return
    current_year = df.index[-1].year
    ytd_mask = df.index.year == current_year
    if np.sum(ytd_mask) > 1:
        ytd_open = df.loc[ytd_mask, "Open"].iloc[0]
        ytd_return = round(((current_price - ytd_open) / ytd_open) * 100.0, 2) if ytd_open > 0 else None
    else:
        ytd_return = None

    performance = {
        "ret_24h": calc_window_return(1),
        "ret_7d": calc_window_return(7),
        "ret_30d": calc_window_return(30),
        "ret_90d": calc_window_return(90),
        "ret_180d": calc_window_return(180),
        "ret_1y": calc_window_return(365),
        "ret_3y": calc_window_return(365 * 3),
        "ret_ytd": ytd_return,
        "ret_cycle": round(((current_price - np.min(lows)) / np.min(lows)) * 100.0, 2) if np.min(lows) > 0 else None
    }

    candles = []
    step = max(1, len(df) // 500)
    sampled_indices = sorted(set(range(0, len(df), step)) | {len(df) - 1})
    for i in sampled_indices:
        candles.append({
            "time": dates[i],
            "open": round(float(df["Open"].iloc[i]), 4),
            "high": round(float(df["High"].iloc[i]), 4),
            "low": round(float(df["Low"].iloc[i]), 4),
            "close": round(float(df["Close"].iloc[i]), 4),
            "volume": round(float(df["Volume"].iloc[i]), 2)
        })

    res = {
        "symbol": coin_symbol.upper(),
        "yf_symbol": yf_symbol,
        "current_price": current_price,
        "ath_price": ath_price,
        "ath_date": ath_date,
        "drawdown_from_ath_pct": drawdown_from_ath_pct,
        "all_time_low": safe_float(np.min(lows)),
        "performance": performance,
        "candles": candles,
        "total_bars": len(df)
    }
    set_cache(cache_key, res)
    return res

# ── 5. SCREENER UNIVERSE AGGREGATOR ───────────────────────────────────────────
POPULAR_CRYPTO_UNIVERSE = [
    {"symbol": "BTC", "name": "Bitcoin", "category": "Layer 1 / Store of Value"},
    {"symbol": "ETH", "name": "Ethereum", "category": "Layer 1 / Smart Contracts"},
    {"symbol": "SOL", "name": "Solana", "category": "High-Throughput L1"},
    {"symbol": "BNB", "name": "BNB", "category": "Exchange / Ecosystem"},
    {"symbol": "XRP", "name": "XRP", "category": "Cross-Border Settlement"},
    {"symbol": "DOGE", "name": "Dogecoin", "category": "Meme / Culture"},
    {"symbol": "ADA", "name": "Cardano", "category": "PoS Layer 1"},
    {"symbol": "AVAX", "name": "Avalanche", "category": "Subnet / Layer 1"},
    {"symbol": "SUI", "name": "Sui", "category": "Move VM Layer 1"},
    {"symbol": "NEAR", "name": "Near Protocol", "category": "Sharded L1 / AI"},
    {"symbol": "LINK", "name": "Chainlink", "category": "Oracle / Cross-Chain"},
    {"symbol": "PEPE", "name": "Pepe", "category": "Meme Liquidity"}
]

COINGECKO_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "ADA": "cardano",
    "AVAX": "avalanche-2",
    "SUI": "sui",
    "NEAR": "near",
    "LINK": "chainlink",
    "PEPE": "pepe"
}

CIRCULATING_SUPPLIES = {
    "BTC": 19_800_000,
    "ETH": 120_400_000,
    "SOL": 468_500_000,
    "BNB": 145_900_000,
    "XRP": 56_800_000_000,
    "DOGE": 146_800_000_000,
    "ADA": 35_800_000_000,
    "AVAX": 406_000_000,
    "SUI": 2_850_000_000,
    "NEAR": 1_220_000_000,
    "LINK": 608_000_000,
    "PEPE": 420_690_000_000_000
}

def fetch_coingecko_markets() -> Dict[str, Dict[str, Any]]:
    """
    Ingests verified global institutional cryptocurrency market intelligence from CoinGecko.
    Returns real volume-weighted prices, actual market caps, 24h changes, ATH, and drawdown.
    """
    cache_key = "coingecko_markets_batch"
    cached = get_cache(cache_key, ttl=30)
    if cached:
        return cached

    ids_str = ",".join(COINGECKO_MAP.values())
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={ids_str}&order=market_cap_desc&sparkline=false&price_change_percentage=24h"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    mapping = {}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data:
                sym = item.get("symbol", "").upper()
                price = float(item.get("current_price") or 0.0)
                mcap = float(item.get("market_cap") or 0.0)
                chg = round(float(item.get("price_change_percentage_24h") or 0.0), 2)
                vol = float(item.get("total_volume") or 0.0)
                ath = float(item.get("ath") or 0.0)
                ath_d = (item.get("ath_date") or "")[:10]
                ath_dd = round(float(item.get("ath_change_percentage") or 0.0), 2)

                mapping[sym] = {
                    "symbol": sym,
                    "name": item.get("name"),
                    "price": price,
                    "price_fmt": fmt_currency(price),
                    "market_cap": mcap,
                    "market_cap_fmt": fmt_currency(mcap),
                    "change_24h": chg,
                    "volume_24h": vol,
                    "volume_24h_fmt": fmt_currency(vol),
                    "ath_price": ath,
                    "ath_price_fmt": fmt_currency(ath),
                    "ath_date": ath_d,
                    "drawdown_from_ath_pct": ath_dd,
                    "high_24h": float(item.get("high_24h") or 0.0),
                    "low_24h": float(item.get("low_24h") or 0.0),
                    "source": "CoinGecko Global Institutional Market API"
                }
        if mapping:
            set_cache(cache_key, mapping)
    except Exception:
        pass

    return mapping

def fetch_binance_ticker(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetches real-time millisecond spot price & 24h change from Binance order books."""
    sym = symbol.strip().upper()
    cache_key = f"binance_ticker_{sym}"
    cached = get_cache(cache_key, ttl=15)
    if cached:
        return cached

    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}USDT"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            d = json.loads(resp.read().decode("utf-8"))
            price = float(d.get("lastPrice", 0.0))
            chg = round(float(d.get("priceChangePercent", 0.0)), 2)
            vol = float(d.get("quoteVolume", 0.0))
            supp = CIRCULATING_SUPPLIES.get(sym, 1.0)
            mcap = price * supp if supp > 1.0 else 0.0
            res = {
                "symbol": sym,
                "price": price,
                "price_fmt": fmt_currency(price),
                "change_24h": chg,
                "volume_24h": vol,
                "volume_24h_fmt": fmt_currency(vol),
                "market_cap": mcap,
                "market_cap_fmt": fmt_currency(mcap),
                "source": "Binance Live Orderbook Feed"
            }
            set_cache(cache_key, res)
            return res
    except Exception:
        return None

def fetch_coin_market_data(clean_sym: str) -> Dict[str, Any]:
    """
    Multi-tiered global market resolver:
    1. CoinGecko Global Market API (authentic prices, actual market caps, real 24h volumes, verified ATH)
    2. Binance 24hr Ticker API (live tick-by-tick spot prices & volume)
    3. yfinance historical series & FastInfo
    4. DexScreener on-chain token liquidity
    """
    # 1. Primary: CoinGecko batch markets
    cg_map = fetch_coingecko_markets()
    if clean_sym in cg_map:
        return cg_map[clean_sym]

    # 2. Secondary: Binance spot order books
    bn = fetch_binance_ticker(clean_sym)
    if bn and bn.get("price", 0) > 0:
        return bn

    # 3. Tertiary: yfinance
    try:
        hist = fetch_crypto_history(clean_sym, years=1)
        p = hist["current_price"]
        chg = hist["performance"].get("ret_24h") or 0.0
        supp = CIRCULATING_SUPPLIES.get(clean_sym, 1.0)
        mcap = p * supp if supp > 1.0 else 0.0
        return {
            "symbol": clean_sym,
            "price": p,
            "price_fmt": fmt_currency(p),
            "change_24h": round(chg, 2),
            "market_cap": mcap,
            "market_cap_fmt": fmt_currency(mcap),
            "ath_price": hist["ath_price"],
            "ath_price_fmt": fmt_currency(hist["ath_price"]),
            "ath_date": hist["ath_date"],
            "drawdown_from_ath_pct": hist["drawdown_from_ath_pct"],
            "source": "Yahoo Finance Historical Stream"
        }
    except Exception:
        pass

    # 4. Quaternary: DexScreener
    dex = fetch_dexscreener_data(clean_sym)
    if dex and dex.get("price_usd"):
        p = dex["price_usd"]
        m = dex.get("market_cap") or dex.get("fdv", 0.0)
        return {
            "symbol": clean_sym,
            "price": p,
            "price_fmt": fmt_currency(p),
            "change_24h": round(dex.get("change_24h", 0.0), 2),
            "market_cap": m,
            "market_cap_fmt": fmt_currency(m),
            "source": "DexScreener On-Chain Liquidity"
        }

    return {
        "symbol": clean_sym,
        "price": 0.0,
        "price_fmt": "$0.00",
        "change_24h": 0.0,
        "market_cap": 0.0,
        "market_cap_fmt": "$0.00",
        "source": "Unavailable"
    }

def fetch_screener_overview() -> List[Dict[str, Any]]:
    """
    Compiles live screener table for top crypto assets with verified global prices,
    authentic market capitalizations, real 24h percentage changes, and volumes.
    """
    cache_key = "screener_overview_verified"
    cached = get_cache(cache_key, ttl=30)
    if cached:
        return cached

    cg_map = fetch_coingecko_markets()
    rows = []
    for coin in POPULAR_CRYPTO_UNIVERSE:
        sym = coin["symbol"]
        if sym in cg_map:
            d = cg_map[sym]
            price = d["price"]
            price_fmt = d["price_fmt"]
            chg_24 = d["change_24h"]
            mcap = d["market_cap"]
            mcap_fmt = d["market_cap_fmt"]
            vol_24 = d["volume_24h"]
            vol_24_fmt = d["volume_24h_fmt"]
        else:
            m = fetch_coin_market_data(sym)
            price = m.get("price", 0.0)
            price_fmt = m.get("price_fmt", "$0.00")
            chg_24 = m.get("change_24h", 0.0)
            mcap = m.get("market_cap", 0.0)
            mcap_fmt = m.get("market_cap_fmt", "$0.00")
            vol_24 = m.get("volume_24h", 0.0)
            vol_24_fmt = m.get("volume_24h_fmt", "$0.00")

        rows.append({
            "symbol": sym,
            "name": coin["name"],
            "category": coin["category"],
            "price": price,
            "price_fmt": price_fmt,
            "change_24h": chg_24,
            "market_cap": mcap,
            "market_cap_fmt": mcap_fmt,
            "volume_24h": vol_24,
            "volume_24h_fmt": vol_24_fmt
        })

    set_cache(cache_key, rows)
    return rows
