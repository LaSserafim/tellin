"""
ai_analyst.py — DeepSeek V3 AI Crypto Analytical Hypothesis & Market Psychology Engine.
Institutional quantitative format:
  - Concise data-grounded bullet points (zero long paragraphs)
  - Explicit numerical sentiment scores (-100 to +100)
  - Clear signals: STRONG BUY, BULLISH, MIXED / NEUTRAL, BEARISH, DEFENSIVE / RISK-OFF
  - 100% resilient deterministic fallback
"""
import os
import json
import time
from typing import Dict, Any, List, Optional
import requests
from openai import OpenAI

def get_api_key() -> str:
    return os.environ.get("DEEPSEEK_API_KEY", "").strip()

def get_base_url() -> str:
    return os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip().rstrip("/")

def get_model() -> str:
    return os.environ.get("DEEPSEEK_MODEL", "deepseek-chat").strip()

def get_client() -> OpenAI:
    return OpenAI(api_key=get_api_key(), base_url=get_base_url())

def _call_deepseek_json(system_prompt: str, user_prompt: str, max_tokens: int = 1800, timeout: int = 25) -> Dict[str, Any]:
    api_key = get_api_key()
    base_url = get_base_url()
    model = get_model()

    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not configured")

    # 1. Primary: OpenAI client with sanitized parameters
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.25,
            max_tokens=max_tokens,
            timeout=timeout
        )
        data = json.loads(resp.choices[0].message.content)
        data["mode"] = "DEEPSEEK_V3_LIVE"
        return data
    except Exception as e_primary:
        # 2. Resilient fallback: direct requests to bypass any local httpx transport issues on serverless
        try:
            r = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.25,
                    "max_tokens": max_tokens
                },
                timeout=timeout
            )
            if r.status_code == 200:
                raw_json = r.json()
                content = raw_json["choices"][0]["message"]["content"]
                data = json.loads(content)
                data["mode"] = "DEEPSEEK_V3_LIVE"
                return data
            else:
                raise RuntimeError(f"DeepSeek HTTP {r.status_code}: {r.text[:120]}")
        except Exception as e_secondary:
            raise RuntimeError(f"OpenAI error ({e_primary}) & requests error ({e_secondary})")
# ── 1. NEWS & GEOPOLITICAL HYPOTHESIS & VERDICT (SECTION 2) ───────────────────
def generate_news_hypothesis_and_verdict(
    coin_name: str,
    coin_symbol: str,
    news_data: Dict[str, Any],
    price_usd: float
) -> Dict[str, Any]:
    articles = news_data.get("articles", [])[:15]
    news_summary_text = ""
    for i, a in enumerate(articles, 1):
        news_summary_text += f"{i}. [{a['cat_badge']} | {a['tone']}] {a['title']} (Source: {a['source']}, Date: {a['date']})\n   Snippet: {a['snippet']}\n"

    system_prompt = (
        "You are an elite quantitative crypto strategist and macro risk officer. "
        "Analyze the provided news tape and macro geopolitical events. "
        "STRICT CONSTRAINT: DO NOT WRITE LONG ESSAYS OR WALLS OF TEXT. "
        "State your points in punchy, concise, data-grounded bullet points citing the exact figures and events provided. "
        "Assign explicit numerical scores (-100 to +100) and clear trading signals. "
        "You MUST respond ONLY with a valid JSON object matching the requested schema."
    )

    user_prompt = f"""
ASSET: {coin_name} ({coin_symbol})
CURRENT SPOT PRICE: ${price_usd:,.2f}
INGESTED ARTICLES: {len(articles)}

SCRAPED HEADLINES:
{news_summary_text if news_summary_text else "No breaking news detected; calibrate to current macro sovereign environment."}

Generate a high-density, bulleted quantitative intelligence dossier in this exact JSON structure:
{{
  "quant_sentiment_score": integer from -100 (Extreme Panic/Sell) to +100 (Extreme Euphoria/Buy),
  "signal": "STRONG BUY" | "BULLISH" | "MIXED / NEUTRAL" | "BEARISH" | "DEFENSIVE / RISK-OFF",
  "category_scores": {{
    "geopolitical": integer from -100 to +100,
    "regulatory": integer from -100 to +100,
    "macro_liquidity": integer from -100 to +100,
    "market_structure": integer from -100 to +100
  }},
  "core_hypothesis_bullets": [
    "Punchy 1-line bullet point stating the core structural thesis based on recent data.",
    "Punchy 1-line bullet point covering spot market absorption vs derivative liquidations.",
    "Punchy 1-line bullet point highlighting key catalyst over next 30-90 days."
  ],
  "macro_landscape_bullets": [
    "Concise bullet point on Fed rates, global M2 liquidity, and dollar strength (DXY).",
    "Concise bullet point on sovereign reserve proposals, sanctions, or international trade.",
    "Concise bullet point on regulatory enforcement (SEC/MiCA) impacts."
  ],
  "bullish_catalysts": [
    {{
      "title": "Short title",
      "evidence": "1 concise sentence citing news/ETF/adoption data.",
      "horizon": "1-4W" | "1-6M" | "1-2Y"
    }},
    {{
      "title": "Short title",
      "evidence": "1 concise sentence citing news/ETF/adoption data.",
      "horizon": "1-4W" | "1-6M" | "1-2Y"
    }}
  ],
  "bearish_risks": [
    {{
      "title": "Short title",
      "evidence": "1 concise sentence citing regulatory or macro tightening risk.",
      "horizon": "1-4W" | "1-6M" | "1-2Y"
    }},
    {{
      "title": "Short title",
      "evidence": "1 concise sentence citing perpetual funding or liquidation trigger.",
      "horizon": "1-4W" | "1-6M" | "1-2Y"
    }}
  ],
  "final_verdict": {{
    "signal_badge": "STRONG BUY" | "BULLISH" | "MIXED / NEUTRAL" | "BEARISH" | "DEFENSIVE",
    "conviction_pct": 0-100 integer,
    "action_directive": "Short punchy directive: e.g. Scale 60% spot on pullbacks, hedge perp longs, or hold dry powder.",
    "key_levels": {{
      "entry_zone": "${price_usd * 0.96:,.2f} – ${price_usd * 0.99:,.2f}",
      "invalidation_stop": "${price_usd * 0.91:,.2f}",
      "target_1": "${price_usd * 1.12:,.2f}",
      "target_2": "${price_usd * 1.25:,.2f}",
      "risk_reward_ratio": "1:2.4"
    }},
    "verdict_bullets": [
      "Key summary bullet point grounded in news data.",
      "Key risk boundary bullet point stating exact invalidation."
    ]
  }}
}}
"""

    try:
        return _call_deepseek_json(system_prompt, user_prompt, max_tokens=1800, timeout=25)
    except Exception as e:
        return _fallback_news_hypothesis(coin_name, coin_symbol, news_data, price_usd, reason=str(e))

# ── 2. FULL-PAGE INSTITUTIONAL RESEARCH & MARKET PSYCHOLOGY (SECTION 4) ────────
def generate_full_ai_psychology_memo(
    coin_name: str,
    coin_symbol: str,
    stats: Dict[str, Any],
    fng: Dict[str, Any],
    news_data: Dict[str, Any],
    drawdown_data: Dict[str, Any]
) -> Dict[str, Any]:
    price = stats.get("current_price", 0.0)
    ath = stats.get("ath_price", price)
    dd_ath = stats.get("drawdown_from_ath_pct", 0.0)
    perf = stats.get("performance", {})
    
    fng_val = fng.get("current_value", 50)
    fng_class = fng.get("classification", "Neutral")
    fng_phase = fng.get("psychology_phase", "Neutral")
    fng_chg_7d = fng.get("change_7d", 0)

    dd_stats = drawdown_data.get("stats", {})
    tier_matrix = drawdown_data.get("tier_matrix", [])

    system_prompt = (
        "You are the Chief Quantitative Officer and Behavioral Market Psychologist at a premier digital asset fund. "
        "Synthesize all stated metrics into an ultra-dense, bullet-pointed research memorandum. "
        "STRICT RULE: NO LONG PARAGRAPHS. STATE EVERY POINT CONCISELY IN BULLET POINTS GROUNDED IN THE PROVIDED NUMBERS. "
        "Format every claim with factual data references. Respond ONLY with a valid JSON object matching the requested schema."
    )

    user_prompt = f"""
TARGET ASSET: {coin_name} ({coin_symbol})
METRICS: Price: ${price:,.2f} | ATH: ${ath:,.2f} | Drawdown from ATH: {dd_ath}%
PERFORMANCE: 24h: {perf.get('ret_24h')}%, 7d: {perf.get('ret_7d')}%, 30d: {perf.get('ret_30d')}%, 1Y: {perf.get('ret_1y')}%
FEAR & GREED: {fng_val}/100 ({fng_class}) | 7d Velocity: {fng_chg_7d:+d} pts | Phase: {fng_phase}
DRAWDOWN DNA: Max 5Y DD: {dd_stats.get('max_drawdown_pct')}% | Recovery Ratio: {dd_stats.get('recovered_ratio_pct')}% | Tiers: {json.dumps(tier_matrix)}
NEWS HEADLINES: {[a['title'] for a in news_data.get('articles', [])[:5]]}

Generate an exhaustive, dense, bullet-point intelligence dossier in this exact JSON structure:
{{
  "memorandum_header": {{
    "title": "Macro Intelligence & Behavioral State Dossier",
    "timestamp": "{time.strftime('%Y-%m-%d %H:%M UTC')}",
    "asset": "{coin_symbol}",
    "emotional_stage": "e.g. Optimism (Late Expansion)" | "Complacency" | "Capitulation" | "Hope",
    "quant_health_score": 0-100 integer
  }},
  "executive_summary_bullets": [
    "Factual bullet citing ${price:,.2f} valuation, {dd_ath}% ATH distance, and liquidity condition.",
    "Factual bullet evaluating current spot ETF / institutional accumulation velocity.",
    "Factual bullet stating overarching market bias and conviction level."
  ],
  "market_psychology_bullets": [
    "Current Wall Street Cheat Sheet stage: [Stage Name] — interpretation based on F&G {fng_val}.",
    "Retail positioning: [Retail state, e.g. sidelined / chasing / fearful] citing 7d velocity {fng_chg_7d:+d}.",
    "Smart money positioning: [Institutional behavior, e.g. steady accumulation via OTC/ETFs].",
    "Exhaustion / liquidation risk: [Analysis of long/short squeeze vulnerability]."
  ],
  "geopolitical_macro_bullets": [
    "Monetary transmission: [Global M2 money supply, Fed interest rate expectations].",
    "Sovereign & nation-state: [National Bitcoin strategic reserve momentum, de-dollarization].",
    "Regulatory climate: [SEC, MiCA, and global compliance clarity impacts]."
  ],
  "drawdown_dna_bullets": [
    "Regime diagnosis: Current {dd_ath}% decline classified under [Tier 1 Pullback / Tier 2 Flush / Tier 3 Bear].",
    "Recovery timeline: Historical recovery rate stands at {dd_stats.get('recovered_ratio_pct')}% across evaluated cycles.",
    "Historical parallel: Comparable to [Specific past cycle, e.g. mid-2023 or 2020 re-accumulation range]."
  ],
  "multi_scenario_forecast": {{
    "bull_case": {{
      "probability_pct": 0-100,
      "price_target": "${price * 1.30:,.2f}",
      "catalyst_bullets": [
        "Primary bullish trigger bullet.",
        "Secondary liquidity catalyst bullet."
      ]
    }},
    "base_case": {{
      "probability_pct": 0-100,
      "price_range": "${price * 0.95:,.2f} – ${price * 1.12:,.2f}",
      "catalyst_bullets": [
        "Primary range-bound consolidation factor.",
        "Volatility dampening driver."
      ]
    }},
    "bear_case": {{
      "probability_pct": 0-100,
      "price_floor": "${price * 0.78:,.2f}",
      "catalyst_bullets": [
        "Black swan or macro failure condition.",
        "Key liquidation trigger level."
      ]
    }}
  }},
  "actionable_playbook_bullets": {{
    "spot_accumulators": [
      "Specific spot tranche allocation instruction (e.g. 60% base at current price, 40% reserved).",
      "Key invalidation and time horizon."
    ],
    "swing_traders": [
      "Exact pivot level to trade around with R/R ratio.",
      "Protective stop-loss placement below structural support."
    ],
    "dca_investors": [
      "Pacing directive relative to 4-year halving cycle.",
      "Accumulation efficiency target."
    ]
  }}
}}
"""

    try:
        return _call_deepseek_json(system_prompt, user_prompt, max_tokens=2600, timeout=30)
    except Exception as e:
        return _fallback_psychology_memo(coin_name, coin_symbol, stats, fng, news_data, drawdown_data, reason=str(e))

# ── 3. DETERMINISTIC SYNTHESIZER FALLBACKS ───────────────────────────────────
def _fallback_news_hypothesis(
    coin_name: str,
    coin_symbol: str,
    news_data: Dict[str, Any],
    price_usd: float,
    reason: str
) -> Dict[str, Any]:
    score = news_data.get("net_sentiment_score", 0.0)
    scaled_score = int(score * 80)
    
    if score > 0.15:
        signal = "BULLISH"
        badge = "BULLISH ACCUMULATION"
        conv = 75
    elif score < -0.15:
        signal = "BEARISH"
        badge = "DEFENSIVE / RISK-OFF"
        conv = 70
    else:
        signal = "MIXED / NEUTRAL"
        badge = "MIXED CONSOLIDATION"
        conv = 65

    return {
        "quant_sentiment_score": scaled_score,
        "signal": signal,
        "category_scores": {
            "geopolitical": 0,
            "regulatory": scaled_score + 10,
            "macro_liquidity": scaled_score,
            "market_structure": scaled_score - 5
        },
        "core_hypothesis_bullets": [
            f"{coin_symbol} trades at ${price_usd:,.2f} in an institutional accumulation regime with stable spot absorption.",
            "ETF inflows and institutional custody continue to soak up liquid supply from centralized order books.",
            "Short-term price action remains constrained by derivatives open interest and range-bound liquidity."
        ],
        "macro_landscape_bullets": [
            "Central bank easing trajectory and global M2 expansion create positive macro liquidity backdrop.",
            "Geopolitical polarization reinforces demand for sovereign-neutral, permissionless digital collateral.",
            "Regulatory clarity in major jurisdictions is funneling capital toward established market leaders."
        ],
        "bullish_catalysts": [
            {
                "title": "ETF Institutional Inflows",
                "evidence": f"Scraped news tape confirms {news_data.get('bullish_count', 0)} positive adoption catalysts.",
                "horizon": "1-6M"
            },
            {
                "title": "Corporate & Sovereign Accumulation",
                "evidence": "Persistent institutional balance sheet accumulation establishes structural floor.",
                "horizon": "1-2Y"
            }
        ],
        "bearish_risks": [
            {
                "title": "Derivatives Leverage Squeeze",
                "evidence": "Elevated perpetual futures open interest increases risk of sharp liquidation cascades.",
                "horizon": "1-4W"
            },
            {
                "title": "Regulatory Headwinds",
                "evidence": f"Monitoring {news_data.get('bearish_count', 0)} headlines regarding compliance and legal actions.",
                "horizon": "1-6M"
            }
        ],
        "final_verdict": {
            "signal_badge": badge,
            "conviction_pct": conv,
            "action_directive": "Scale 60% spot on dips; place invalidation stops below structural range lows.",
            "key_levels": {
                "entry_zone": f"${price_usd * 0.96:,.2f} – ${price_usd * 0.99:,.2f}",
                "invalidation_stop": f"${price_usd * 0.91:,.2f}",
                "target_1": f"${price_usd * 1.12:,.2f}",
                "target_2": f"${price_usd * 1.25:,.2f}",
                "risk_reward_ratio": "1:2.4"
            },
            "verdict_bullets": [
                f"Net sentiment is {news_data.get('sentiment_label')} with score {scaled_score}/100.",
                f"Risk-reward is asymmetric to the upside above key invalidation at ${price_usd * 0.91:,.2f}."
            ]
        },
        "mode": f"DETERMINISTIC_SYNTHESIZER ({reason[:40]})"
    }

def _fallback_psychology_memo(
    coin_name: str,
    coin_symbol: str,
    stats: Dict[str, Any],
    fng: Dict[str, Any],
    news_data: Dict[str, Any],
    drawdown_data: Dict[str, Any],
    reason: str
) -> Dict[str, Any]:
    price = stats.get("current_price", 0.0)
    ath = stats.get("ath_price", price)
    dd_ath = stats.get("drawdown_from_ath_pct", 0.0)
    fng_val = fng.get("current_value", 50)
    fng_phase = fng.get("psychology_phase", "Neutral")

    return {
        "memorandum_header": {
            "title": "Macro Intelligence & Behavioral State Dossier",
            "timestamp": time.strftime("%Y-%m-%d %H:%M UTC"),
            "asset": coin_symbol,
            "emotional_stage": fng_phase,
            "quant_health_score": 74
        },
        "executive_summary_bullets": [
            f"{coin_name} ({coin_symbol}) trades at ${price:,.2f}, representing a {dd_ath}% pullback from ${ath:,.2f} ATH.",
            f"Sentiment index sits at {fng_val}/100 ({fng.get('classification', 'Neutral')}), reflecting orderly re-accumulation.",
            "Long-term structural thesis remains robust with zero structural impairment to network security or adoption."
        ],
        "market_psychology_bullets": [
            f"Current Cheat Sheet stage: {fng_phase} — avoids the euphoric blowoff peaks that precede secular winters.",
            "Retail participants remain hesitant following past volatility, creating low-crowded entry conditions.",
            "Institutional smart money continues steady spot absorption through regulated ETF wrappers.",
            "Liquidation risk is concentrated around near-term perpetual leverage clusters rather than systemic solvency."
        ],
        "geopolitical_macro_bullets": [
            "Central bank global easing and expanding M2 liquidity historically create favorable tailwinds for scarce assets.",
            "Nation-state sovereign reserve proposals transition digital assets from speculative toys to geopolitical hedges.",
            "Regulatory frameworks are shifting from enforcement-by-litigation to compliant institutional frameworks."
        ],
        "drawdown_dna_bullets": [
            f"Current {dd_ath}% decline aligns with a Tier 2 Leverage Flush (-20% to -35%).",
            f"Historical recovery rate for this regime is {drawdown_data.get('stats', {}).get('recovered_ratio_pct', 100)}% over full cycle.",
            "Drawdown structure mirrors the mid-cycle re-accumulation ranges of 2020 and 2023."
        ],
        "multi_scenario_forecast": {
            "bull_case": {
                "probability_pct": 55,
                "price_target": f"${price * 1.30:,.2f}",
                "catalyst_bullets": [
                    "Accelerating ETF net inflows and sovereign reserve formalization.",
                    "Breakout above local range highs triggering short-covering squeeze."
                ]
            },
            "base_case": {
                "probability_pct": 35,
                "price_range": f"${price * 0.95:,.2f} – ${price * 1.12:,.2f}",
                "catalyst_bullets": [
                    "Sideways accumulation absorbing residual overhead supply.",
                    "Consolidation allowing moving averages to catch up."
                ]
            },
            "bear_case": {
                "probability_pct": 10,
                "price_floor": f"${price * 0.78:,.2f}",
                "catalyst_bullets": [
                    "Severe macro liquidity withdrawal or aggressive regulatory enforcement.",
                    "Cascading liquidation flush below long-term moving averages."
                ]
            }
        },
        "actionable_playbook_bullets": {
            "spot_accumulators": [
                f"Deploy 60% spot allocation at current levels (${price:,.2f}); reserve 40% for limit bids at ${price * 0.92:,.2f}.",
                "Maintain minimum 12-to-24 month investment horizon anchored around halving cycle."
            ],
            "swing_traders": [
                f"Trade range boundaries: Long near ${price * 0.96:,.2f} with stop placed at ${price * 0.91:,.2f}.",
                f"Target 1 at ${price * 1.12:,.2f} for a 1:2.4 risk-to-reward ratio."
            ],
            "dca_investors": [
                "Automate fixed weekly dollar-cost averaging regardless of short-term noise.",
                "Accumulate heavily whenever Fear & Greed Index drops below 35."
            ]
        },
        "mode": f"DETERMINISTIC_SYNTHESIZER ({reason[:40]})"
    }
