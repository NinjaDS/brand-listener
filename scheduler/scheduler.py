#!/usr/bin/env python3
"""
scheduler.py — Automated brand listening scheduler with adaptive trend detection.
Part of brand-listener: https://github.com/NinjaDS/brand-listener

Inspired by karpathy/autoresearch: instead of static, one-shot reports,
the scheduler learns from previous runs — detecting trend shifts,
adapting search terms, and alerting on sentiment changes automatically.

No GPU required. Runs on Mac/Linux via AWS Bedrock.

Setup:
    1. Edit watchlist.json with your brands, schedule, and delivery settings
    2. Run once: python3 scheduler.py --run-now
    3. Schedule weekly: python3 scheduler.py --daemon   (keeps running, fires on schedule)
    4. Or use cron:  0 8 * * 1  python3 /path/to/scheduler.py --run-now

Features:
    - Automated weekly (or custom) report generation
    - Adaptive search: refines query terms based on emerging themes from prior reports
    - Trend detection: compares sentiment week-over-week, alerts on drops
    - Email delivery or local save
    - Full audit trail in reports/history.json
"""

import json
import time
import smtplib
import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import brand_listener

WATCHLIST_FILE = Path("watchlist.json")
OUTPUT_DIR     = Path("reports")


def history_file(brand: str) -> Path:
    safe = brand.lower().replace(" ", "-").replace(".", "").replace("/", "")
    d = OUTPUT_DIR / safe
    d.mkdir(parents=True, exist_ok=True)
    return d / "history.json"


# ── Watchlist config ─────────────────────────────────────────────────────────
def load_watchlist() -> dict:
    if not WATCHLIST_FILE.exists():
        print("⚠️  watchlist.json not found. Copy watchlist.example.json and edit it.")
        raise SystemExit(1)
    return json.loads(WATCHLIST_FILE.read_text())


# ── History & trend tracking ─────────────────────────────────────────────────
def load_history() -> dict:
    return {}


def load_brand_history(brand: str) -> list:
    f = history_file(brand)
    if f.exists():
        return json.loads(f.read_text())
    return []


def save_history(history: dict):
    """Save per-brand history files."""
    for brand, runs in history.items():
        f = history_file(brand)
        f.write_text(json.dumps(runs, indent=2))


def get_prior_run(history: dict, brand: str) -> dict | None:
    runs = history.get(brand, [])
    return runs[-1] if runs else None


def record_run(history: dict, brand: str, result: dict):
    if brand not in history:
        history[brand] = load_brand_history(brand)
    history[brand].append(result)
    history[brand] = history[brand][-12:]


# ── Adaptive query engine ─────────────────────────────────────────────────────
def adaptive_search_terms(brand: str, base_topic: str, prior: dict | None) -> str:
    """
    Karpathy-inspired adaptive loop:
    Instead of a static query, expand it using themes from the previous run.
    This means the tool gets smarter over time — chasing emerging conversations.
    """
    if not prior:
        return base_topic

    prior_themes = prior.get("top_themes", [])
    if not prior_themes:
        return base_topic

    # Take top 2 themes and blend them into the query
    extra = " ".join(prior_themes[:2])
    adapted = f"{base_topic} {extra}"
    print(f"   🧠 Adaptive query: '{base_topic}' → '{adapted}' (based on prior themes)")
    return adapted


# ── Trend analysis ────────────────────────────────────────────────────────────
def detect_trend(prior: dict | None, current_sentiment: dict, config: dict) -> list[str]:
    """
    Compare current run vs prior run.
    Return list of alert strings if anything notable changed.
    """
    alerts = []
    if not prior:
        return alerts

    threshold = config.get("adaptive", {}).get("sentiment_alert_threshold", -0.3)
    prev_score    = prior.get("sentiment_score", 0)
    current_score = current_sentiment.get("sentiment_score", 0)

    delta = current_score - prev_score
    if delta < threshold:
        alerts.append(
            f"⚠️ TREND ALERT: Sentiment dropped {delta:.2f} points "
            f"(from {prev_score:.2f} → {current_score:.2f}) vs last run."
        )

    # Alert if new sentiment is outright negative
    if current_sentiment.get("overall_sentiment") == "negative" and prior.get("overall_sentiment") != "negative":
        alerts.append("🚨 Brand just turned NEGATIVE in public sentiment — immediate attention needed.")

    return alerts


# ── Email delivery ────────────────────────────────────────────────────────────
def send_email(config: dict, brand: str, report_path: str, trend_alerts: list[str]):
    dist = config.get("distribution", {})
    email_to = dist.get("email", "")
    if not email_to:
        return

    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        print("   ⚠️  SMTP credentials not set (SMTP_USER / SMTP_PASS env vars). Skipping email.")
        return

    subject = f"[Brand Listener] Weekly Report — {brand} — {datetime.now().strftime('%d %b %Y')}"
    if trend_alerts:
        subject = "🚨 " + subject

    body = Path(report_path).read_text()
    if trend_alerts:
        body = "\n".join(trend_alerts) + "\n\n---\n\n" + body

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = smtp_user
    msg["To"]      = email_to
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.sendmail(smtp_user, email_to, msg.as_string())
        print(f"   📧 Report emailed to {email_to}")
    except Exception as e:
        print(f"   ⚠️  Email failed: {e}")


# ── Single brand run ──────────────────────────────────────────────────────────
def run_brand(entry: dict, config: dict, history: dict):
    brand       = entry["brand"]
    competitors = entry.get("competitors", [])
    topic       = entry.get("topic", brand)
    region      = entry.get("region", "global")
    country     = entry.get("country", "")
    subsidiaries = entry.get("subsidiaries", [])

    print(f"\n{'='*60}")
    print(f"  🎧 Running: {brand}")
    print(f"{'='*60}")

    prior = get_prior_run(history, brand)

    # Adaptive query
    adaptive_topic = adaptive_search_terms(brand, topic, prior)

    # Run the full brand listener pipeline
    report_path, sentiment, audit = brand_listener.run_full(
        brand=brand,
        competitors=competitors,
        topic=adaptive_topic,
        country=country,
        subsidiaries=subsidiaries,
        region=region,
    )

    # Trend detection
    trend_alerts = detect_trend(prior, sentiment, config)
    if trend_alerts:
        print("\n".join(f"   {a}" for a in trend_alerts))

    # Record run in history
    record_run(history, brand, {
        "date":              datetime.now().strftime("%Y-%m-%d"),
        "report":            report_path,
        "sentiment_score":   sentiment.get("sentiment_score", 0),
        "overall_sentiment": sentiment.get("overall_sentiment", "unknown"),
        "top_themes":        sentiment.get("top_themes", []),
        "trend_alerts":      trend_alerts,
    })

    # Email delivery
    send_email(config, brand, report_path, trend_alerts)

    return report_path


# ── Main scheduler loop ───────────────────────────────────────────────────────
def run_all_now():
    config   = load_watchlist()
    history  = load_history()
    brands   = config.get("watchlist", [])

    print(f"\n🕐 Brand Listener Scheduler — {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"   Brands to run: {len(brands)}")

    for entry in brands:
        try:
            run_brand(entry, config, history)
        except Exception as e:
            print(f"   ❌ Failed for {entry.get('brand', '?')}: {e}")

    save_history(history)
    print(f"\n✅ All brands complete. History saved.")


def daemon_mode():
    """Run continuously, firing on schedule."""
    config = load_watchlist()
    sched  = config.get("schedule", {})
    freq   = sched.get("frequency", "weekly")
    day    = sched.get("day", "monday").lower()
    hour   = int(sched.get("hour", 8))

    day_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
               "friday": 4, "saturday": 5, "sunday": 6}
    target_day = day_map.get(day, 0)

    print(f"🤖 Daemon mode — checking every hour, fires {freq} on {day.title()} at {hour:02d}:00")

    while True:
        now = datetime.now()
        if freq == "weekly":
            if now.weekday() == target_day and now.hour == hour and now.minute < 5:
                run_all_now()
                time.sleep(3600)  # avoid double-firing
        elif freq == "daily":
            if now.hour == hour and now.minute < 5:
                run_all_now()
                time.sleep(3600)
        time.sleep(300)  # check every 5 minutes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Brand Listener Scheduler")
    parser.add_argument("--run-now", action="store_true", help="Run all brands immediately")
    parser.add_argument("--daemon",  action="store_true", help="Run as daemon on schedule")
    parser.add_argument("--brand",   default="",          help="Run a single brand only")
    args = parser.parse_args()

    if args.run_now or args.brand:
        if args.brand:
            config  = load_watchlist()
            history = load_history()
            entries = [e for e in config.get("watchlist", []) if e["brand"].lower() == args.brand.lower()]
            if not entries:
                print(f"Brand '{args.brand}' not found in watchlist.json")
            else:
                run_brand(entries[0], config, history)
                save_history(history)
        else:
            run_all_now()
    elif args.daemon:
        daemon_mode()
    else:
        parser.print_help()
