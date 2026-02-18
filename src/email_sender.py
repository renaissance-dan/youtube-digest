from __future__ import annotations

import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL


def _render_ticker_badge(ticker):
    colors = {
        "bullish": "#16a34a",
        "bearish": "#dc2626",
        "neutral": "#6b7280",
    }
    color = colors.get(ticker.get("sentiment", "neutral"), "#6b7280")
    symbol = ticker.get("symbol", "???")
    sentiment = ticker.get("sentiment", "neutral").upper()
    return (
        '<span style="display:inline-block;padding:2px 8px;margin:2px;'
        'border-radius:4px;background:{c};color:#fff;font-size:13px;'
        'font-weight:600;">{s} {st}</span>'
    ).format(c=color, s=symbol, st=sentiment)


def _render_video_card(video):
    a = video.get("analysis", {})
    tickers_html = " ".join(_render_ticker_badge(t) for t in a.get("tickers", []))
    insights_html = "".join("<li>{}</li>".format(i) for i in a.get("market_insights", []))
    actions_html = "".join("<li>{}</li>".format(i) for i in a.get("action_items", []))

    channel = video.get("channel", "")
    url = video.get("url", "#")
    title = video.get("title", "Untitled")
    summary = a.get("summary", "No summary available.")

    parts = []
    parts.append('<div style="background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:20px;margin-bottom:16px;">')
    parts.append('  <div style="margin-bottom:4px;font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px;">{}</div>'.format(channel))
    parts.append('  <a href="{}" style="font-size:17px;font-weight:700;color:#111827;text-decoration:none;">{}</a>'.format(url, title))
    parts.append('  <p style="color:#374151;margin:12px 0;font-size:14px;line-height:1.6;">{}</p>'.format(summary))

    if tickers_html:
        parts.append('  <div style="margin:10px 0;">{}</div>'.format(tickers_html))

    if insights_html:
        parts.append('  <div style="margin-top:12px;"><strong style="font-size:13px;color:#111827;">Key Insights</strong>')
        parts.append('  <ul style="margin:4px 0 0;padding-left:20px;color:#374151;font-size:13px;line-height:1.7;">{}</ul></div>'.format(insights_html))

    if actions_html:
        parts.append('  <div style="margin-top:10px;"><strong style="font-size:13px;color:#111827;">Action Items</strong>')
        parts.append('  <ul style="margin:4px 0 0;padding-left:20px;color:#374151;font-size:13px;line-height:1.7;">{}</ul></div>'.format(actions_html))

    parts.append('</div>')
    return "\n".join(parts)


def build_email_html(digest, videos):
    today = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")
    video_count = len(videos)

    # Pre-render list items
    consensus_html = "".join("<li>{}</li>".format(t) for t in digest.get("consensus_themes", []))
    conflicts_html = "".join("<li>{}</li>".format(v) for v in digest.get("conflicting_views", []))
    top_actions_html = "".join("<li>{}</li>".format(a) for a in digest.get("action_items", []))
    risk_html = "".join("<li>{}</li>".format(r) for r in digest.get("risk_alerts", []))

    top_tickers_html = ""
    for t in digest.get("top_tickers", []):
        count = t.get("mention_count", 1)
        summary = t.get("summary", "")
        top_tickers_html += (
            '{badge} <span style="font-size:12px;color:#6b7280;">({count}x) {summary}</span><br>'
            .format(badge=_render_ticker_badge(t), count=count, summary=summary)
        )

    video_cards_html = "".join(_render_video_card(v) for v in videos)
    market_overview = digest.get("market_overview", "No videos found for today.")

    # Build HTML in sections
    html_parts = []

    # DOCTYPE and header
    html_parts.append("""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:640px;margin:0 auto;padding:20px;">

  <div style="text-align:center;padding:24px 0;">
    <h1 style="margin:0;font-size:22px;color:#111827;">Market Digest</h1>
    <p style="margin:4px 0 0;font-size:14px;color:#6b7280;">{today} &middot; {count} video(s) analyzed</p>
  </div>

  <div style="background:linear-gradient(135deg,#1e293b,#334155);border-radius:10px;padding:24px;color:#fff;margin-bottom:20px;">
    <h2 style="margin:0 0 12px;font-size:17px;color:#f1f5f9;">Today's Overview</h2>
    <p style="margin:0 0 16px;font-size:14px;line-height:1.7;color:#e2e8f0;">{overview}</p>""".format(
        today=today, count=video_count, overview=market_overview
    ))

    # Consensus themes
    if consensus_html:
        html_parts.append(
            '    <div style="margin-top:14px;"><strong style="font-size:13px;color:#94a3b8;">CONSENSUS THEMES</strong>'
            '<ul style="margin:6px 0 0;padding-left:20px;color:#e2e8f0;font-size:13px;line-height:1.7;">{}</ul></div>'.format(consensus_html)
        )

    # Conflicting views
    if conflicts_html:
        html_parts.append(
            '    <div style="margin-top:14px;"><strong style="font-size:13px;color:#94a3b8;">CONFLICTING VIEWS</strong>'
            '<ul style="margin:6px 0 0;padding-left:20px;color:#fbbf24;font-size:13px;line-height:1.7;">{}</ul></div>'.format(conflicts_html)
        )

    # Top tickers
    if top_tickers_html:
        html_parts.append('    <div style="margin-top:14px;">{}</div>'.format(top_tickers_html))

    # Close overview div
    html_parts.append('  </div>')

    # Top action items
    if top_actions_html:
        html_parts.append(
            '  <div style="background:#ecfdf5;border:1px solid #a7f3d0;border-radius:8px;padding:18px;margin-bottom:20px;">'
            '    <h3 style="margin:0 0 8px;font-size:15px;color:#065f46;">Top Action Items</h3>'
            '    <ol style="margin:0;padding-left:20px;color:#065f46;font-size:14px;line-height:1.8;">{}</ol>'
            '  </div>'.format(top_actions_html)
        )

    # Risk alerts
    if risk_html:
        html_parts.append(
            '  <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:18px;margin-bottom:20px;">'
            '    <h3 style="margin:0 0 8px;font-size:15px;color:#991b1b;">Risk Alerts</h3>'
            '    <ul style="margin:0;padding-left:20px;color:#991b1b;font-size:14px;line-height:1.8;">{}</ul>'
            '  </div>'.format(risk_html)
        )

    # Video breakdowns
    html_parts.append('  <h2 style="font-size:17px;color:#111827;margin:24px 0 12px;">Video Breakdowns</h2>')
    html_parts.append(video_cards_html)

    # Footer
    html_parts.append("""
  <div style="text-align:center;padding:20px 0;font-size:12px;color:#9ca3af;">
    Generated by YouTube Market Digest
  </div>

</div>
</body>
</html>""")

    return "\n".join(html_parts)


def send_digest_email(digest, videos):
    """Build and send the digest email via Gmail SMTP."""
    today = datetime.now(timezone.utc).strftime("%b %d, %Y")
    html = build_email_html(digest, videos)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Market Digest - {}".format(today)
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())

    print("Digest email sent to {}".format(RECIPIENT_EMAIL))
