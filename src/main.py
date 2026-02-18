import sys

from config import CHANNEL_IDS
from youtube_client import fetch_videos_with_transcripts
from summarizer import summarize_video, generate_overall_digest
from email_sender import send_digest_email


def main():
    if not CHANNEL_IDS:
        print("No channels configured. Add channel IDs to src/config.py")
        sys.exit(1)

    print(f"Checking {len(CHANNEL_IDS)} channel(s) for new videos...")

    # 1. Fetch new videos with transcripts
    videos = fetch_videos_with_transcripts(CHANNEL_IDS)

    if not videos:
        print("No new videos with transcripts found. Skipping digest.")
        return

    # 2. Summarize each video
    print(f"\nSummarizing {len(videos)} video(s) with Claude...")
    analyzed = []
    for video in videos:
        print(f"  Analyzing: {video['title']}")
        analyzed.append(summarize_video(video))

    # 3. Generate overall digest
    print("\nGenerating overall market digest...")
    digest = generate_overall_digest(analyzed)

    # 4. Send email
    print("\nSending digest email...")
    send_digest_email(digest, analyzed)

    print("\nDone!")


if __name__ == "__main__":
    main()
