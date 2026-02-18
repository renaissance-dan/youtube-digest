# YouTube Market Digest — Setup Guide

Follow these steps in order. The whole process takes about 20 minutes.

---

## Step 1: Get a YouTube API Key (free)

This lets the script find new videos from your channels.

**Create a Google Cloud project:**

1. Go to https://console.cloud.google.com
2. Sign in with your Google account
3. At the top of the page, click the project dropdown (it might say "Select a project")
4. Click "New Project" in the popup
5. Name it anything (e.g. "YouTube Digest") and click "Create"
6. Wait a few seconds, then make sure your new project is selected in the dropdown

**Enable the YouTube API:**

7. In the search bar at the top, type "YouTube Data API v3" and click the result
8. Click the blue "Enable" button

**Create the API key:**

9. Now go to https://console.cloud.google.com/apis/credentials
10. Click "+ Create Credentials" at the top → choose "API key"
11. A "Create API key" form will appear. Fill it out like this:
    - **Name:** Type anything you want (e.g. `YouTube Digest API Key`)
    - **Authenticate API calls through a service account:** Leave this **unchecked**
    - **Application restrictions:** Leave set to **None**
    - **API restrictions:** Select **"Restrict key"**, then from the dropdown choose **"YouTube Data API v3"** only (this is a security best practice — it makes sure this key can only be used for YouTube)
12. Click the blue **"Create"** button at the bottom
13. Google will show your API key — copy it and save it somewhere safe (you'll need it later)

> If Google asks you to enable billing, you can skip it. The YouTube API free tier is more than enough.

---

## Step 2: Get a Gmail App Password (free)

This lets the script send emails from your Gmail account. It does NOT use your regular Gmail password.

1. Go to https://myaccount.google.com/security
2. Make sure "2-Step Verification" is turned ON (if it's not, turn it on first — Google will walk you through it)
3. Go to https://myaccount.google.com/apppasswords
4. You may need to sign in again
5. In the "App name" field, type "YouTube Digest" and click "Create"
6. Google will show you a 16-character password (like `abcd efgh ijkl mnop`)
7. Copy this password and save it somewhere safe — Google only shows it once

---

## Step 3: Get an Anthropic API Key

This is for the AI that reads and summarizes the videos. Costs ~$7/month.

1. Go to https://console.anthropic.com
2. Create an account or sign in
3. Add a payment method (Settings → Billing) — you'll be charged based on usage
4. Go to https://console.anthropic.com/settings/keys
5. Click "Create Key", name it "YouTube Digest"
6. Copy the key and save it somewhere safe

---

## Step 4: Channel IDs (already done!)

Your 5 channels are already configured in `src/config.py`:

| Channel | Role |
|---|---|
| Bravos Research | Macro view, global trends |
| ZipTrader | Daily market news |
| Humbled Trader | Trade setups, risk management |
| TheChartGuys | Technical levels, support/resistance |
| Ticker Symbol: YOU | Disruptive tech, AI, semiconductors |

> **Want to add or remove a channel later?** Open `src/config.py`, edit the `CHANNEL_IDS` list, commit, and push to GitHub. To find a channel ID, go to https://commentpicker.com/youtube-channel-id.php and paste the channel URL.

---

## Step 5: Test It Locally (optional but recommended)

> This step runs the digest on your computer to make sure everything works before automating it. If you'd rather skip straight to automation, jump to Step 6.

If you want to make sure everything works before setting up the automation:

1. Open Terminal (on Mac: press Cmd+Space, type "Terminal", press Enter)
2. Copy-paste these commands one at a time, pressing Enter after each:

```
cd ~/Claude/youtube-digest
```

```
cp .env.example .env
```

3. Open the `.env` file in a text editor and replace each placeholder with your real values:

```
YOUTUBE_API_KEY=paste_your_youtube_key_here
ANTHROPIC_API_KEY=paste_your_anthropic_key_here
GMAIL_ADDRESS=youremail@gmail.com
GMAIL_APP_PASSWORD=paste_your_16_char_app_password_here
RECIPIENT_EMAIL=youremail@gmail.com
```

4. Save the file, then go back to Terminal and run:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd src && python main.py
```

5. Check your email — you should receive a digest within a minute or two

> If you see an error, read the error message. The most common issues are:
> - "No channels configured" → the channel IDs in `src/config.py` may have been cleared. Re-check the file.
> - "API key not valid" → double-check your YouTube API key
> - "Authentication" errors → double-check your Gmail app password
> - "No new videos found" → your channels may not have posted in the last 24 hours. Try increasing `LOOKBACK_HOURS` in config.py to `72` temporarily

---

## Step 6: Create a GitHub Account (skip if you already have one)

1. Go to https://github.com
2. Click "Sign Up" and follow the steps
3. Verify your email address

---

## Step 7: Create a GitHub Repository

1. Go to https://github.com/new
2. Repository name: `youtube-digest`
3. Set it to **Private** (so your channel list isn't public)
4. Do NOT check any of the boxes (no README, no .gitignore, no license)
5. Click "Create repository"
6. GitHub will show you setup instructions — leave this page open

---

## Step 8: Upload the Code to GitHub

1. Open Terminal
2. Run these commands one at a time (replace `YOUR_GITHUB_USERNAME` with your actual GitHub username):

```
cd ~/Claude/youtube-digest
```

```
git init
```

```
git add -A
```

```
git commit -m "Initial commit"
```

```
git branch -M main
```

```
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/youtube-digest.git
```

```
git push -u origin main
```

> If GitHub asks you to sign in, follow the prompts. You may need to use a "Personal Access Token" instead of your password — GitHub will guide you through this.

---

## Step 9: Add Your Secrets to GitHub

This is how the automated script accesses your API keys without them being visible in the code.

1. Go to your repository on GitHub: `https://github.com/YOUR_USERNAME/youtube-digest`
2. Click **Settings** (tab at the top of the repo)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click the green **"New repository secret"** button
5. Add each of these secrets one at a time (click "Add secret" after each):

| Name | Value |
|------|-------|
| `YOUTUBE_API_KEY` | Your YouTube API key from Step 1 |
| `ANTHROPIC_API_KEY` | Your Anthropic API key from Step 3 |
| `GMAIL_ADDRESS` | Your Gmail address (e.g. you@gmail.com) |
| `GMAIL_APP_PASSWORD` | Your 16-character app password from Step 2 |
| `RECIPIENT_EMAIL` | The email where you want the digest (can be the same Gmail) |

---

## Step 10: Test the Automation

1. Go to your repository on GitHub
2. Click the **Actions** tab at the top
3. On the left, click **"Daily YouTube Market Digest"**
4. Click the **"Run workflow"** dropdown button on the right
5. Click the green **"Run workflow"** button
6. Wait 1-2 minutes, then check your email

If the run fails, click on it to see the error logs.

---

## Step 11: Adjust the Time (if needed)

The digest is set to send at **8 PM Eastern Time**. If you're in a different timezone, edit `.github/workflows/daily-digest.yml`:

| Your Timezone | Change the cron to |
|---|---|
| Eastern (EST/EDT) | `0 1 * * *` (already set) |
| Central (CST/CDT) | `0 2 * * *` |
| Mountain (MST/MDT) | `0 3 * * *` |
| Pacific (PST/PDT) | `0 4 * * *` |

After editing, commit and push the change to GitHub.

---

## You're Done!

Every day at 8 PM, you'll receive an email with:
- An overall market overview synthesizing all your channels
- Consensus themes (what multiple channels agree on)
- Conflicting views (where channels disagree)
- Ticker mentions with bullish/bearish/neutral sentiment
- Prioritized action items
- Risk alerts
- Individual video breakdowns

**Monthly cost:** ~$7 for Claude API usage. Everything else is free.

---

## Troubleshooting

**"No new videos found"**
Your channels may not have posted in the last 24 hours. The digest only sends when there are new videos.

**Email not arriving**
Check your spam folder. Also verify your Gmail app password is correct (it's 16 characters, no spaces).

**GitHub Action failing**
Go to the Actions tab, click the failed run, and read the red error message. Usually it's a missing or incorrect secret.

**Want to add or remove a channel?**
Edit `src/config.py`, update the `CHANNEL_IDS` list, commit, and push to GitHub.
