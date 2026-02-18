import json

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

VIDEO_SUMMARY_PROMPT = """\
You are a financial analyst assistant. Analyze this YouTube video transcript and extract structured insights.

Video: "{title}" by {channel}

Transcript:
{transcript}

IMPORTANT — Sponsored content filtering:
- Some videos are ENTIRELY paid promotions or sponsored advertisements for a stock or product. \
If the video is primarily a paid promotion, sponsored content, or advertisement, set "is_sponsored" to true. \
Examples: "This video is sponsored by...", "I was compensated to discuss...", paid stock promotions, \
entire videos dedicated to promoting a single stock the creator was paid to cover.
- For videos that contain SOME sponsored segments mixed with real analysis, IGNORE the sponsored \
portions entirely. Only extract insights from the genuine, independent analysis portions.
- Do NOT include tickers, insights, or action items that come from sponsored segments.

Respond in JSON with this exact structure:
{{
  "is_sponsored": false,
  "summary": "2-3 sentence summary of the video's main points",
  "market_insights": ["insight 1", "insight 2", ...],
  "tickers": [
    {{"symbol": "AAPL", "sentiment": "bullish", "context": "brief reason"}}
  ],
  "action_items": ["specific actionable step 1", "step 2", ...]
}}

Focus on actionable, specific insights. For tickers, sentiment must be one of: bullish, bearish, neutral.
If no specific tickers are mentioned, return an empty list for tickers.
If the video is entirely sponsored, set "is_sponsored" to true and leave all other fields minimal.
Return ONLY valid JSON, no markdown fences."""

DIGEST_PROMPT = """\
You are a financial analyst assistant. Below are summaries from multiple YouTube finance channels published today. Synthesize them into an overall market digest.

Video Summaries:
{summaries_json}

Create a cohesive daily market digest in JSON:
{{
  "market_overview": "3-4 sentence overview of today's key market themes",
  "consensus_themes": ["theme that multiple channels agree on", ...],
  "conflicting_views": ["area where channels disagree and why", ...],
  "top_tickers": [
    {{"symbol": "AAPL", "sentiment": "bullish", "mention_count": 3, "summary": "why"}}
  ],
  "action_items": ["top prioritized action item 1", "item 2", ...],
  "risk_alerts": ["any warnings or risks mentioned across channels"]
}}

Prioritize action items by how many channels support them. Flag conflicting views clearly.
Return ONLY valid JSON, no markdown fences."""


def _clean_json_response(text: str) -> str:
    """Strip markdown code fences and whitespace from Claude's JSON response."""
    import re
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
        max_tokens=1024,
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
            "market_insights": [],
            "tickers": [],
            "action_items": [],
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
        max_tokens=1500,
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
            "action_items": [],
            "risk_alerts": [],
        }
