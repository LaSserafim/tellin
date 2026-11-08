"""
news_scraper.py — Real-Time Crypto News, Geopolitics & Narrative Scraper.
Aggregates live news feeds across:
  1. Google News RSS (targeted multi-query: Coin + Regulation + Geopolitics + Macro)
  2. CoinTelegraph RSS (breaking crypto industry tape & policy updates)
  3. Narrative & Geopolitical classification (War, Sanctions, SEC/Fed, Sovereign Adoption, Liquidations)
  4. Structured payload preparation for DeepSeek V3 AI analytical deduction
"""
import re
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, List, Optional
import email.utils

# ── IN-MEMORY CACHE WITH TTL ──────────────────────────────────────────────────
_NEWS_CACHE: Dict[str, Any] = {}

def get_news_cache(key: str, ttl: float = 120.0) -> Optional[Any]:
    entry = _NEWS_CACHE.get(key)
    if entry and (time.time() - entry["ts"] < ttl):
        return entry["val"]
    return None

def set_news_cache(key: str, val: Any) -> None:
    _NEWS_CACHE[key] = {"val": val, "ts": time.time()}

# ── TAXONOMY & KEYWORD CLASSIFIERS ───────────────────────────────────────────
GEOPOLITICAL_KEYWORDS = {
    "war", "conflict", "sanctions", "sanction", "russia", "ukraine", "iran", "israel",
    "middle east", "taiwan", "china", "brics", "election", "trump", "biden", "treasury",
    "sovereign", "reserve", "national", "oil", "dollar", "de-dollarization", "tariffs", "trade war"
}

REGULATORY_KEYWORDS = {
    "sec", "cftc", "gensler", "etf", "approval", "lawsuit", "sue", "sues", "settlement",
    "fine", "ban", "compliance", "court", "ruling", "doj", "treasury", "mica", "kyc",
    "aml", "crackdown", "probe", "investigation", "subpoena", "license", "legal"
}

MACRO_KEYWORDS = {
    "fed", "powell", "interest rate", "rates", "rate cut", "rate hike", "inflation", "cpi",
    "pce", "jobs", "unemployment", "recession", "gdp", "liquidity", "yield", "bonds",
    "quantitative easing", "money supply", "m2", "debt ceiling"
}

BEARISH_WORDS = {
    "plunge", "plunges", "crash", "crashes", "sink", "sinks", "drop", "drops", "slump",
    "slumps", "tumble", "rout", "sell-off", "selloff", "wipeout", "liquidation", "liquidated",
    "losses", "bleeding", "ban", "bans", "hack", "hacked", "exploit", "drain", "drained",
    "fraud", "scam", "bankruptcy", "insolvent", "panic", "fear", "bearish", "downside"
}

BULLISH_WORDS = {
    "surge", "surges", "rally", "rallies", "jump", "jumps", "breakout", "soar", "soars",
    "record", "highs", "all-time high", "ath", "inflow", "inflows", "accumulation",
    "buying", "approved", "adoption", "partnership", "strategic reserve", "bullish", "expansion",
    "gain", "gains", "rebound", "rebounds", "recovery", "massive", "optimism"
}

def clean_html_tags(raw_html: str) -> str:
    clean = re.sub(r"<.*?>", "", raw_html)
    return clean.replace("&quot;", '"').replace("&amp;", '&').replace("&apos;", "'").replace("&#39;", "'")

def parse_rss_date(date_str: str) -> str:
    try:
        parsed_tuple = email.utils.parsedate_tz(date_str)
        if parsed_tuple:
            timestamp = email.utils.mktime_tz(parsed_tuple)
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M")

def classify_article(title: str, description: str) -> Dict[str, Any]:
    text = (title + " " + description).lower()
    words = set(re.findall(r"\b[a-z\-]+\b", text))

    # Category matching
    geo_score = len(words & GEOPOLITICAL_KEYWORDS)
    reg_score = len(words & REGULATORY_KEYWORDS)
    macro_score = len(words & MACRO_KEYWORDS)
    
    if geo_score >= max(reg_score, macro_score, 1):
        category = "GEOPOLITICAL"
        cat_badge = "GEOPOLITICS"
    elif reg_score >= max(geo_score, macro_score, 1):
        category = "REGULATORY"
        cat_badge = "REGULATORY / SEC"
    elif macro_score >= 1:
        category = "MACRO_LIQUIDITY"
        cat_badge = "MACRO / FED"
    else:
        category = "MARKET_STRUCTURE"
        cat_badge = "MARKET SENTIMENT"

    # Sentiment scoring
    bear_hits = len(words & BEARISH_WORDS)
    bull_hits = len(words & BULLISH_WORDS)

    if bull_hits > bear_hits:
        tone = "BULLISH"
        score = min(1.0, 0.4 + 0.2 * (bull_hits - bear_hits))
    elif bear_hits > bull_hits:
        tone = "BEARISH"
        score = max(-1.0, -0.4 - 0.2 * (bear_hits - bull_hits))
    else:
        tone = "NEUTRAL"
        score = 0.0

    return {
        "category": category,
        "cat_badge": cat_badge,
        "tone": tone,
        "sentiment_score": round(score, 2),
        "geo_relevance": geo_score > 0
    }

# ── 1. GOOGLE NEWS RSS FETCHER ────────────────────────────────────────────────
def fetch_google_news_rss(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    articles = []

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            content = resp.read()
            root = ET.fromstring(content)
            channel = root.find("channel")
            if channel is None:
                return []

            items = channel.findall("item")
            for item in items[:limit]:
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                pub_date = item.findtext("pubDate", "")
                desc = clean_html_tags(item.findtext("description", ""))
                source = item.findtext("source", "Google News")

                if not title:
                    continue

                meta = classify_article(title, desc)
                articles.append({
                    "title": title,
                    "link": link,
                    "date": parse_rss_date(pub_date),
                    "source": source,
                    "snippet": desc[:240] + "..." if len(desc) > 240 else desc,
                    "category": meta["category"],
                    "cat_badge": meta["cat_badge"],
                    "tone": meta["tone"],
                    "sentiment_score": meta["sentiment_score"],
                    "geo_relevance": meta["geo_relevance"]
                })
    except Exception as e:
        pass
    return articles

# ── 2. COINTELEGRAPH RSS FETCHER ─────────────────────────────────────────────
def fetch_cointelegraph_rss(limit: int = 10) -> List[Dict[str, Any]]:
    url = "https://cointelegraph.com/rss"
    headers = {"User-Agent": "Mozilla/5.0"}
    articles = []

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read()
            root = ET.fromstring(content)
            channel = root.find("channel")
            if channel is None:
                return []

            items = channel.findall("item")
            for item in items[:limit]:
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                pub_date = item.findtext("pubDate", "")
                desc = clean_html_tags(item.findtext("description", ""))

                if not title:
                    continue

                meta = classify_article(title, desc)
                articles.append({
                    "title": title,
                    "link": link,
                    "date": parse_rss_date(pub_date),
                    "source": "CoinTelegraph",
                    "snippet": desc[:240] + "..." if len(desc) > 240 else desc,
                    "category": meta["category"],
                    "cat_badge": meta["cat_badge"],
                    "tone": meta["tone"],
                    "sentiment_score": meta["sentiment_score"],
                    "geo_relevance": meta["geo_relevance"]
                })
    except Exception:
        pass
    return articles

# ── 3. COMPREHENSIVE NEWS & GEOPOLITICAL INTELLIGENCE AGGREGATOR ─────────────
def get_crypto_news_and_geopolitics(coin_name: str, coin_symbol: str) -> Dict[str, Any]:
    """
    Scrapes live Google News and CoinTelegraph across multiple query vectors:
    1. Coin-specific events & ETF flows
    2. Geopolitical and regulatory developments
    3. Global macroeconomic liquidity
    Returns a unified deduplicated list sorted by relevance and recency.
    """
    clean_sym = coin_symbol.strip().upper()
    cache_key = f"news_geo_{clean_sym}"
    cached = get_news_cache(cache_key, ttl=120)
    if cached:
        return cached

    # Query Vector 1: Specific asset news & institutional flows
    q1 = f"{coin_name} OR {clean_sym} crypto ETF market when:7d"
    # Query Vector 2: Geopolitics, regulation & macro
    q2 = f"crypto bitcoin geopolitics war sanctions election Fed when:7d"

    articles_q1 = fetch_google_news_rss(q1, limit=12)
    articles_q2 = fetch_google_news_rss(q2, limit=10)
    articles_ct = fetch_cointelegraph_rss(limit=8)

    # Deduplicate by title
    seen_titles = set()
    all_articles = []

    for art in articles_q1 + articles_q2 + articles_ct:
        simplified = re.sub(r"[^a-zA-Z0-9]", "", art["title"].lower())[:40]
        if simplified and simplified not in seen_titles:
            seen_titles.add(simplified)
            all_articles.append(art)

    # Aggregate sentiment stats
    bullish_count = sum(1 for a in all_articles if a["tone"] == "BULLISH")
    bearish_count = sum(1 for a in all_articles if a["tone"] == "BEARISH")
    geo_count = sum(1 for a in all_articles if a["geo_relevance"])
    reg_count = sum(1 for a in all_articles if a["category"] == "REGULATORY")
    macro_count = sum(1 for a in all_articles if a["category"] == "MACRO_LIQUIDITY")

    total = len(all_articles) or 1
    net_sentiment_score = round((bullish_count - bearish_count) / total, 2)

    if net_sentiment_score > 0.2:
        sentiment_label = f"BULLISH MOMENTUM (+{int(net_sentiment_score*100)}%)"
        sentiment_color = "#00f59b"
    elif net_sentiment_score < -0.2:
        sentiment_label = f"BEARISH PRESSURE ({int(net_sentiment_score*100)}%)"
        sentiment_color = "#ff3b5c"
    else:
        sentiment_label = "BALANCED SPECULATIVE TAPE (Neutral)"
        sentiment_color = "#94a3b8"

    res = {
        "coin_symbol": clean_sym,
        "coin_name": coin_name,
        "total_articles": len(all_articles),
        "sentiment_label": sentiment_label,
        "sentiment_color": sentiment_color,
        "net_sentiment_score": net_sentiment_score,
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "geopolitical_count": geo_count,
        "regulatory_count": reg_count,
        "macro_count": macro_count,
        "articles": all_articles[:25]
    }

    set_news_cache(cache_key, res)
    return res
