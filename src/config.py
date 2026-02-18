import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# Gmail
GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", GMAIL_ADDRESS)

# YouTube channels to follow — add your channel IDs here
# Find a channel ID: go to the channel page → View Page Source → search "channelId"
# Or use https://www.youtube.com/@channelname and look at the page source
CHANNEL_IDS = [
    "UCOHxDwCcOzBaLkeTazanwcw",  # Bravos Research — macro view, global trends
    "UC0BGhWsIbV7Dm-lsvhdlMbA",  # ZipTrader — daily market news (ignore stock picks)
    "UCcIvNGMBSQWwo1v3n-ZRBCw",  # Humbled Trader — trade setups, risk management
    "UCnqZ2hx679DqRi6khRUNw2g",  # TheChartGuys — technical levels, support/resistance
    "UC7kCeZ53sli_9XwuQeFxLqw",  # Ticker Symbol: YOU — disruptive tech, AI, semis
]

# How far back to look for new videos (in hours)
LOOKBACK_HOURS = int(os.environ.get("LOOKBACK_HOURS", "24"))

# Max videos to process per channel (to control costs)
MAX_VIDEOS_PER_CHANNEL = int(os.environ.get("MAX_VIDEOS_PER_CHANNEL", "5"))

# Claude model for summarization
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
