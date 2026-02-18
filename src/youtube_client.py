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
                    "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                })
        except Exception as e:
            print(f"Error fetching videos for channel {channel_id}: {e}")

    return videos


def get_transcript(video_id: str) -> Optional[str]:
    """Fetch the transcript for a video. Returns None if unavailable."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        return " ".join(entry["text"] for entry in transcript)
    except Exception as e:
        print(f"Transcript unavailable for {video_id}: {e}")
        return None


def fetch_videos_with_transcripts(channel_ids: list[str]) -> list[dict]:
    """Fetch new videos and attach transcripts. Skips videos without transcripts."""
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
