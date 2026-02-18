from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

from config import YOUTUBE_API_KEY, LOOKBACK_HOURS, MAX_VIDEOS_PER_CHANNEL


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


def _get_full_description(video_id: str) -> Optional[str]:
    """Fetch the full video description via the videos.list API (search only gives truncated)."""
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        response = youtube.videos().list(
            part="snippet",
            id=video_id,
        ).execute()
        items = response.get("items", [])
        if items:
            desc = items[0]["snippet"].get("description", "")
            if len(desc) > 100:  # only useful if there's real content
                return desc
    except Exception as e:
        print(f"  Could not fetch description for {video_id}: {e}")
    return None


def get_transcript(video_id: str) -> Optional[str]:
    """Fetch the transcript for a video. Tries multiple strategies before giving up."""
    # Strategy 1: English captions (manual or auto-generated)
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        return " ".join(entry["text"] for entry in transcript)
    except Exception:
        pass

    # Strategy 2: Any available language (auto-generated captions in any language)
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        # Try auto-generated first, then manual, in any language
        for transcript in transcript_list:
            try:
                fetched = transcript.fetch()
                text = " ".join(entry["text"] for entry in fetched)
                if text:
                    lang = transcript.language_code
                    print(f"  Using {lang} transcript for {video_id}")
                    return text
            except Exception:
                continue
    except Exception:
        pass

    # Strategy 3: Fall back to the full video description
    desc = _get_full_description(video_id)
    if desc:
        print(f"  Using video description as fallback for {video_id}")
        return "[VIDEO DESCRIPTION — no transcript available]\n\n" + desc

    print(f"  No transcript or description available for {video_id}")
    return None


def fetch_videos_with_transcripts(channel_ids: list[str]) -> list[dict]:
    """Fetch new videos and attach transcripts. Skips videos without any text content."""
    videos = get_new_videos(channel_ids)
    print(f"Found {len(videos)} new video(s) across {len(channel_ids)} channel(s)")

    results = []
    for video in videos:
        transcript = get_transcript(video["video_id"])
        if transcript:
            video["transcript"] = transcript
            results.append(video)
            print(f"  + {video['channel']}: {video['title']}")
        else:
            print(f"  - {video['channel']}: {video['title']} (no transcript)")

    print(f"Fetched transcripts for {len(results)} video(s)")
    return results
