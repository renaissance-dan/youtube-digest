import json

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

VIDEO_SUMMARY_PROMPT = """\
You are a financial analyst assistant. Analyze this YouTube video transcript and extract structured insights.

Video: "{title}" by {channel}

Transcript:
{transcript}

Respond in JSON with this exact structure:
{{
  "summary": "2-3 sentence summary of the video's main points",
  "market_insights": ["insight 1", "insight 2", ...],
  "tickers": [
    {{"symbol": "AAPL", "sentiment": "bullish", "context": "brief reason"}}
  ],
  "action_items": ["specific actionable step 1", "step 2", ...]
}}

Focus on actionable, specific insights. For tickers, sentiment must be one of: bullish, bearish, neutral.
If no specific tickers are mentioned, return an empty list for tickers.
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

    try:
        result = json.loads(response.content[0].text)
    except json.JSONDecodeError:
        result = {
            "summary": response.content[0].text[:500],
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

    try:
        return json.loads(response.content[0].text)
    except json.JSONDecodeError:
        return {
            "market_overview": response.content[0].text[:500],
            "consensus_themes": [],
            "conflicting_views": [],
            "top_tickers": [],
            "action_items": [],
            "risk_alerts": [],
        }
