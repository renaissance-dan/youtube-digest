import json
import re

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

VIDEO_SUMMARY_PROMPT = """\
You are a senior financial analyst writing a briefing for a portfolio manager who CANNOT watch this video. \
Your job is to extract every specific, concrete claim so they have the same information as someone who watched it.

Video: "{title}" by {channel}

Transcript:
{transcript}

RULES:
1. SPECIFICITY IS EVERYTHING. Never write vague summaries. Extract exact numbers, prices, levels, dates, \
percentages, and named catalysts. "BTC is showing weakness" is useless. "BTC rejected at $52,400 resistance \
and is forming lower highs on the daily, with support at $48,800" is useful.
2. SPONSORED CONTENT: If this video is entirely a paid promotion or sponsored advertisement (e.g., "I was \
compensated to discuss...", paid stock promo), set "is_sponsored" to true and skip the rest. For videos with \
sponsored segments mixed in, IGNORE those segments — only extract from genuine analysis.
3. CAPTURE THE CREATOR'S ACTUAL THESIS. What is their specific directional call? What conditions would \
change their mind? What timeframe are they operating on?
4. PRESERVE DISAGREEMENT AND NUANCE. If the creator says "bulls need X to happen or else Y", capture both sides.
5. INCLUDE SPECIFIC LEVELS. Support, resistance, moving averages, RSI readings, volume observations — \
anything with a number attached.

Respond in JSON:
{{
  "is_sponsored": false,
  "summary": "3-5 sentence summary that captures the creator's specific thesis, key price levels mentioned, \
and their directional bias. Include numbers.",
  "key_claims": [
    "Specific factual claim or prediction from the video with numbers/levels attached",
    "Another concrete claim — e.g., 'SPY needs to hold $445 support or risks a move to $430'",
    "Include the creator's reasoning, not just conclusions"
  ],
  "tickers": [
    {{
      "symbol": "BTC",
      "sentiment": "bearish",
      "price_levels": "Rejected at $52,400 resistance, support at $48,800, next target $46,500",
      "thesis": "Forming lower highs on daily, buyers failing to follow through on bounces"
    }}
  ],
  "trade_ideas": [
    "Specific trade setup or actionable idea mentioned — include entry, target, stop if given"
  ],
  "risks_and_warnings": [
    "Specific risk the creator flagged — e.g., 'CPI data Thursday could invalidate this setup'"
  ]
}}

IMPORTANT:
- "key_claims" is the most important field. These should be specific enough that someone reading them \
gets 80% of the value of watching the video. Aim for 4-8 claims per video.
- For "tickers", always fill in "price_levels" with exact numbers when mentioned. If no specific levels \
are given, write "No specific levels mentioned".
- "trade_ideas" should only include explicit trade setups the creator suggested. If they didn't suggest \
any specific trades, return an empty list.
- "risks_and_warnings" should capture macro risks, upcoming catalysts, or scenarios that could invalidate the thesis.
- Sentiment must be: bullish, bearish, or neutral.
- If the video is entirely sponsored, set "is_sponsored" to true and leave all other fields empty/minimal.
Return ONLY valid JSON, no markdown fences."""

DIGEST_PROMPT = """\
You are a senior financial analyst writing a morning briefing for a portfolio manager. \
Below are detailed summaries from multiple YouTube finance channels. Synthesize them into a \
concise, actionable digest.

Video Summaries:
{summaries_json}

Create a cohesive daily market digest in JSON. Be SPECIFIC — include exact prices, levels, and percentages \
from the underlying video analyses. Do not generalize away the details.

{{
  "market_overview": "4-6 sentence overview of today's key market themes. Reference specific price levels, \
sectors, and catalysts. This should read like a Bloomberg terminal morning note.",
  "consensus_themes": [
    "Theme multiple channels agree on — be specific about what they agree on and WHY"
  ],
  "conflicting_views": [
    "Where channels specifically disagree — name the channels and their opposing positions"
  ],
  "top_tickers": [
    {{
      "symbol": "AAPL",
      "sentiment": "bullish",
      "mention_count": 3,
      "summary": "Specific synthesis of what was said across channels, including price levels"
    }}
  ],
  "key_levels_to_watch": [
    "SPY: Support at $445, resistance at $458 (TheChartGuys)",
    "BTC: Must hold $48,800 or risk move to $46,500 (TheChartGuys)"
  ],
  "action_items": [
    "Specific, prioritized action — ranked by how many channels support it and urgency"
  ],
  "risk_alerts": [
    "Specific risk with date/catalyst if applicable — e.g., 'CPI data Thursday 8:30 AM ET could spike volatility'"
  ],
  "upcoming_catalysts": [
    "Earnings report, economic data release, Fed meeting, etc. with dates"
  ]
}}

Rules:
- "key_levels_to_watch" is critical — pull every specific support/resistance/target mentioned across all videos.
- "upcoming_catalysts" should list any dated events mentioned (earnings, Fed, economic data, etc.).
- Do not water down specific claims into vague generalities.
- Attribute conflicting views to their source channels.
Return ONLY valid JSON, no markdown fences."""


def _clean_json_response(text: str) -> str:
    """Strip markdown code fences and whitespace from Claude's JSON response."""
    cleaned = text.strip()
    # Remove ```json ... ``` or ``` ... ``` wrappers
    match = re.match(r"^```(?:json)?\s*\n?(.*?)\n?\s*```$", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()
    return cleaned


def summarize_video(video: dict) -> dict:
    """Summarize a single video transcript using Claude."""
    # Truncate very long transcripts to stay within context limits
    transcript = video["transcript"][:50000]

    prompt = VIDEO_SUMMARY_PROMPT.format(
        title=video["title"],
        channel=video["channel"],
        transcript=transcript,
    )

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text
    cleaned = _clean_json_response(raw_text)

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"  Warning: Could not parse JSON for '{video['title']}', using raw text")
        result = {
            "summary": cleaned[:500],
            "key_claims": [],
            "tickers": [],
            "trade_ideas": [],
            "risks_and_warnings": [],
        }

    return {
        **video,
        "analysis": result,
    }


def generate_overall_digest(analyzed_videos: list[dict]) -> dict:
    """Generate an overall market digest synthesizing all video summaries."""
    summaries = []
    for v in analyzed_videos:
        summaries.append({
            "channel": v["channel"],
            "title": v["title"],
            "analysis": v["analysis"],
        })

    prompt = DIGEST_PROMPT.format(summaries_json=json.dumps(summaries, indent=2))

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text
    cleaned = _clean_json_response(raw_text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print("  Warning: Could not parse digest JSON, using raw text")
        return {
            "market_overview": cleaned[:500],
            "consensus_themes": [],
            "conflicting_views": [],
            "top_tickers": [],
            "key_levels_to_watch": [],
            "action_items": [],
            "risk_alerts": [],
            "upcoming_catalysts": [],
        }
