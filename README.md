# TELLIN // Institutional Crypto Quantitative, Geopolitical & Analytical Terminal

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![DeepSeek V3](https://img.shields.io/badge/AI-DeepSeek%20V3-00f59b?style=for-the-badge&logo=openai&logoColor=black)](https://api.deepseek.com)
[![TradingView](https://img.shields.io/badge/Charting-TradingView%20Pro-blue?style=for-the-badge&logo=tradingview&logoColor=white)](https://www.tradingview.com)
[![License](https://img.shields.io/badge/License-MIT-red?style=for-the-badge)](LICENSE)

> **TELLIN** is an institutional-grade cryptocurrency quantitative terminal, geopolitical risk engine, and speculative intelligence platform. It synthesizes real-time exchange liquidity, live news feeds, the 4 Canonical Crypto Drawdown Regimes, historical person movements, and DeepSeek V3 macroeconomic deduction into a unified Neo-Brutalist Black & Green terminal.

---

## 1. Executive Summary & Capabilities

Unlike equities, cryptocurrency markets operate 24/7/365, exhibit extreme fat tails (excess kurtosis $K > 20$), and are predominantly driven by **macroeconomic liquidity, geopolitical tensions, regulatory enforcement, and key figure movements**.

TELLIN organizes institutional research into four distinct computational modules:

| Module | Route / Tab | Analytical Focus | Core Outputs |
|---|---|---|---|
| **01. TradingView & Screener** | `[ 01 // TRADINGVIEW ]` | Interactive technical charting & multi-coin liquidity screener | Live TradingView Pro candlestick widget, floating/dockable chart panel, TradingView existence validator, 12-asset liquidity ranking table |
| **02. News Sentiment & Geopolitics** | `[ 02 // NEWS ]` | Real-time news scraping & AI speculative hypothesis | Multi-query Google News & CoinTelegraph scraper, Geopolitical/Regulatory classification, DeepSeek V3 Core Hypothesis, Bull/Bear arguments with citations, Final Verdict |
| **03. Stats & 4-Tier Drawdown** | `[ 03 // STATS ]` | Multi-timeframe performance, drawdown DNA & person movements | 1h to Cycle returns, 4 Canonical Crypto Drawdown Tiers (-10%, -20%, -35%, -55%+), recovery timelines, rolling underwater curve, 12-event Historical Person Movements Ledger |
| **04. Deep AI Psychology Memo** | `[ 04 // AI MEMO ]` | Full 1-page institutional research memorandum | Fear & Greed Index diagnosis, Wall Street Cheat Sheet emotional cycle stage, retail vs smart money divergence, multi-scenario probabilistic forecast, actionable investor playbook |
| **05. Insider, Whale & Speculation** | `[ 05 // WHALES ]` | Institutional decisions, corporate treasuries & retail speculation | CoinGecko 180+ public corporate treasuries ($68B+ held), BlackRock IBIT & MSTR proxies, DexScreener on-chain buy/sell flow, Smart Money vs. Retail Divergence classifier |

---

## 2. Core Methodologies & Mathematical Foundations

### 2.1 TradingView Symbol Validation & Exchange Resolver
Before injecting any iframe or widget, TELLIN queries TradingView's symbol search endpoint (`symbol-search.tradingview.com/symbol_search/v3/`). 
* If verified: It extracts the most liquid exchange pairing (`BINANCE:BTCUSDT`, `COINBASE:BTCUSD`, etc.) and attaches it seamlessly.
* If unverified: It displays a prominent neo-brutalist error box (`[ ✖ SYMBOL DOES NOT EXIST ON TRADINGVIEW ]`) preventing broken iframes and saving user time.

### 2.2 The 4 Canonical Crypto Drawdown Regimes
Adapted from institutional equity models (FutureAs) and recalibrated for 24/7 crypto volatility:
1. **Tier 1: Pullback (-10% to -20%)**: Normal leverage unwinding, minor profit-taking. Benchmark: 4–6x per year.
2. **Tier 2: Leverage Flush (-20% to -35%)**: Cascading perpetual futures long liquidations, funding rate resets. Benchmark: 2–3x per year.
3. **Tier 3: Bear Market Leg (-35% to -55%)**: Macro monetary tightening, regulatory litigation, institutional outflows. Benchmark: Every 1–2 years.
4. **Tier 4: Capitulation / Crypto Winter (≤ -55% to -85%+)**: Black swan shocks, exchange insolvencies, multi-year structural bottoms. Benchmark: Every 3–4 years (Halving cycle).

### 2.3 Historical Person & Event Movement Ledger
Major historical inflection points mapped with identifiable reasons and prominent figures:
* **Donald Trump** (July 2024: US Strategic National Bitcoin Reserve keynote).
* **German BKA & Mt. Gox Trustee** (July 2024: 50,000 BTC government dump and creditor distribution).
* **Gary Gensler & US SEC** (Jan 2024: Spot Bitcoin ETF approval; June 2023: Binance/Coinbase suits).
* **Changpeng Zhao (CZ) & DOJ** (Nov 2023: $4.3B plea deal resolving regulatory overhang).
* **Sam Bankman-Fried (SBF) & FTX** (Nov 2022: Alameda balance sheet insolvency and $15.5k cycle bottom).
* **Do Kwon & Luna Foundation Guard** (May 2022: $40B UST algorithmic de-peg & 80,000 BTC reserve dump).
* **Jerome Powell & Federal Reserve** (March 2020: Emergency COVID QE; Nov 2021: 500bps rate hiking cycle).
* **China State Council** (May 2021: Total ban on Bitcoin mining and crypto transactions).
* **Elon Musk & Tesla** (Feb 2021: $1.5B BTC treasury buy; May 2021: suspension of BTC payments).
* **Michael Saylor & MicroStrategy** (Aug 2020: Invention of the corporate Bitcoin standard).

---

## 3. UI/UX Design System (Neo-Brutalism Black & Green)

Constructed strictly following the `ui-ux-pro-max` design system:
* **Strict Reset**: `*, *::before, *::after { border-radius: 0 !important; }`.
* **Colors**: Deep Pitch Black (`#000000`), Dark Green Backing (`#003822`), Matrix Accent Green (`#00f59b`), Electric Crimson (`#ff3b5c`), Cyan (`#38bdf8`), Amber (`#fbbf24`).
* **Typography**: `Barlow Condensed` / `Orbitron` (bold condensed display) + `IBM Plex Mono` (tabular numerals).
* **Accessibility**: High contrast passing WCAG AAA, zero emojis as icons (100% SVG icons), visible focus states (`outline: 2px solid #00f59b`), and smooth transitions.

---

## 4. REST API Specification

| Endpoint | Method | Description |
|---|---|---|
| `GET /` | `GET` | Serves the single-page Neo-Brutalist HTML terminal. |
| `GET /api/health` | `GET` | Service status, active models, and data feed integrity. |
| `GET /api/tv-validate?symbol=BTC` | `GET` | Validates whether symbol exists on TradingView and returns best exchange ticker. |
| `GET /api/screener` | `GET` | Real-time prices, 24h changes, and market caps for top screener assets. |
| `GET /api/coin/{symbol}` | `GET` | Aggregated DEX metrics, multi-timeframe performance, ATH, and drawdown from ATH. |
| `GET /api/fng` | `GET` | Alternative.me Fear & Greed Index score + 30-day psychological trajectory. |
| `GET /api/news/{symbol}` | `GET` | Scraped real-time Google News & CoinTelegraph articles categorized by vector. |
| `GET /api/hypothesis/{symbol}` | `GET / POST` | DeepSeek V3 AI Core Hypothesis, Bull/Bear arguments, and Final Verdict. |
| `GET /api/drawdowns/{symbol}` | `GET` | 4-Tier Drawdown analysis, recovery timelines, and Historical Person Movements Ledger. |
| `GET /api/deep-memo/{symbol}` | `GET / POST` | Full 1-page institutional research memorandum synthesizing all sections. |
| `GET /api/insider-whales/{symbol}` | `GET` | Authentic corporate treasuries, Spot ETF & MSTR proxies, on-chain order flow, and Smart Money vs. Retail Divergence. |
| `POST /api/settings/key` | `POST` | Dynamically updates DeepSeek API key at runtime. |

---

## 5. Quick Start & Execution

### Prerequisites
* Python 3.9 or higher
* Internet connection (for live data feeds and TradingView widget)

### 1. Launch Terminal Server
```bash
cd "/Users/macbook/Documents/omp-coding/crypto analysis/tellin"
./run.sh
```
Or run directly via Python:
```bash
python3 backend/main.py
```

### 2. Access Web Interface
Open your browser at:
```
http://127.0.0.1:3001
```

---

## 6. License
MIT License. Developed for quantitative researchers, crypto asset allocators, and digital currency analysts.
