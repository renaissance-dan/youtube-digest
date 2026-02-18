from __future__ import annotations

import os
import re
import tempfile
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

from config import YOUTUBE_API_KEY, LOOKBACK_HOURS, MAX_VIDEOS_PER_CHANNEL

# Delay between transcript requests to reduce rate-limiting risk
REQUEST_DELAY_SECONDS = 3


def get_new_videos(channel_ids: list[str]) -> list[dict]:
    """Fetch videos published in the last LOOKBACK_HOURS from the given channels."""
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    published_after = cutoff.isoformat()

    videos = []
    for channel_id in channel_ids:
        try:
            response = youtube.search().list(
                part="snippet",
                channelId=channel_id,
                publishedAfter=published_after,
                order="date",
                type="video",
                maxResults=MAX_VIDEOS_PER_CHANNEL,
            ).execute()

            for item in response.get("items", []):
                videos.append({
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "channel": item["snippet"]["channelTitle"],
                    "published_at": item["snippet"]["publishedAt"],
                    "description": item["snippet"].get("description", ""),
                    "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                })
        except Exception as e:
            print(f"Error fetching videos for channel {channel_id}: {e}")

    return videos


# ---------------------------------------------------------------------------
# Layer 1: youtube-transcript-api (v1.2.4 — innertube-based, most lightweight)
# ---------------------------------------------------------------------------

def _fetch_via_transcript_api(video_id: str) -> Optional[str]:
    """Try youtube-transcript-api: English first, then any available language."""
    ytt = YouTubeTranscriptApi()

    # Try English captions (manual or auto-generated)
    try:
        transcript = ytt.fetch(video_id, languages=["en"])
        snippets = transcript.to_raw_data()
        text = " ".join(s["text"] for s in snippets)
        if text.strip():
            return text
    except Exception:
        pass

    # Try any available language
    try:
        transcript_list = ytt.list(video_id)
        for t in transcript_list:
            try:
                fetched = t.fetch()
                snippets = fetched.to_raw_data()
                text = " ".join(s["text"] for s in snippets)
                if text.strip():
                    print(f"    [transcript-api] Using {t.language_code} transcript")
                    return text
            except Exception:
                continue
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# Layer 2: yt-dlp subtitle extraction (different code path, may bypass blocks)
# ---------------------------------------------------------------------------

def _parse_vtt(vtt_text: str) -> str:
    """Extract plain text from a WebVTT subtitle file."""
    lines = []
    for line in vtt_text.splitlines():
        # Skip VTT headers, timestamps, and blank lines
        line = line.strip()
        if not line:
            continue
        if line.startswith("WEBVTT"):
            continue
        if line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if "-->" in line:
            continue
        if re.match(r"^\d+$", line):
            continue
        # Remove VTT formatting tags like <c> </c> <00:00:01.234>
        clean = re.sub(r"<[^>]+>", "", line)
        if clean.strip():
            lines.append(clean.strip())

    # Deduplicate consecutive identical lines (VTT often repeats)
    deduped = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)

    return " ".join(deduped)


def _fetch_via_ytdlp(video_id: str) -> Optional[str]:
    """Try yt-dlp to extract subtitles without downloading the video."""
    try:
        import yt_dlp
    except ImportError:
        print("    [yt-dlp] Not installed, skipping fallback")
        return None

    url = f"https://www.youtube.com/watch?v={video_id}"

    with tempfile.TemporaryDirectory() as tmpdir:
        output_template = os.path.join(tmpdir, "subs")

        ydl_opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en", "en-US", "en-GB"],
            "subtitlesformat": "vtt",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            print(f"    [yt-dlp] Download failed: {e}")
            return None

        # Look for any .vtt file that was written
        for fname in os.listdir(tmpdir):
            if fname.endswith(".vtt"):
                filepath = os.path.join(tmpdir, fname)
                with open(filepath, "r", encoding="utf-8") as f:
                    vtt_text = f.read()
                text = _parse_vtt(vtt_text)
                if text.strip():
                    print(f"    [yt-dlp] Got subtitles from {fname}")
                    return text

    return None


# ---------------------------------------------------------------------------
# Layer 3: Video description fallback (last resort, free)
# ---------------------------------------------------------------------------

def _get_full_description(video_id: str) -> Optional[str]:
    """Fetch the full video description via the videos.list API."""
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        response = youtube.videos().list(
            part="snippet",
            id=video_id,
        ).execute()
        items = response.get("items", [])
        if items:
            desc = items[0]["snippet"].get("description", "")
            if len(desc) > 100:
                return desc
    except Exception as e:
        print(f"    [description] Could not fetch: {e}")
    return None


# ---------------------------------------------------------------------------
# Main transcript fetcher — tries all layers in order
# ---------------------------------------------------------------------------

def get_transcript(video_id: str) -> Optional[str]:
    """Fetch transcript using a 3-layer fallback strategy."""
    print(f"  Fetching transcript for {video_id}...")

    # Layer 1: youtube-transcript-api
    text = _fetch_via_transcript_api(video_id)
    if text:
        print(f"    [transcript-api] Success")
        return text

    print(f"    [transcript-api] Failed, trying yt-dlp...")

    # Layer 2: yt-dlp subtitle extraction
    text = _fetch_via_ytdlp(video_id)
    if text:
        return text

    print(f"    [yt-dlp] Failed, trying video description...")

    # Layer 3: Video description fallback
    desc = _get_full_description(video_id)
    if desc:
        print(f"    [description] Using as fallback")
        return "[VIDEO DESCRIPTION - no transcript available]\n\n" + desc

    print(f"    No transcript or description available")
    return None


def fetch_videos_with_transcripts(channel_ids: list[str]) -> list[dict]:
    """Fetch new videos and attach transcripts. Skips videos without any text content."""
    videos = get_new_videos(channel_ids)
    print(f"Found {len(videos)} new video(s) across {len(channel_ids)} channel(s)")

    results = []
    for i, video in enumerate(videos):
        # Add delay between requests to avoid rate limiting
        if i > 0:
            time.sleep(REQUEST_DELAY_SECONDS)

        transcript = get_transcript(video["video_id"])
        if transcript:
            video["transcript"] = transcript
            results.append(video)
            print(f"  + {video['channel']}: {video['title']}")
        else:
            print(f"  - {video['channel']}: {video['title']} (no transcript)")

    print(f"Fetched transcripts for {len(results)} video(s)")
    return results
