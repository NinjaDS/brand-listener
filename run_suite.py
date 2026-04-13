#!/usr/bin/env python3
"""
Brand Ops Marketing Suite — single entrypoint.

Usage:
    python run_suite.py --brand "Curlsmith"
    python run_suite.py --all
    python run_suite.py --list
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Load .env before any imports that need env vars
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from marketing_suite.agent_readiness import check_readiness
from marketing_suite.brand_awareness import compute_awareness
from marketing_suite.llm_council import convene_council
from marketing_suite.orchestrator import WorkspaceManager, TaskQueue
from marketing_suite.report_builder import build_report
from scrapers.linkedin_scraper import scrape_linkedin

WATCHLIST_PATH = Path(__file__).parent / "watchlist.json"


def load_watchlist():
    with open(WATCHLIST_PATH) as f:
        return json.load(f)


def run_brand(brand_config: dict, queue: TaskQueue):
    brand_name = brand_config["brand"]
    search_keyword = brand_config.get("linkedin_search_keyword") or brand_name
    country = brand_config.get("country", "UK")

    try:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        use_rich = True
    except ImportError:
        use_rich = False
        console = None

    def log(msg):
        if use_rich:
            console.print(f"[bold cyan]{msg}[/bold cyan]")
        else:
            print(msg)

    log(f"\n▶ Running Brand Ops for: {brand_name}")

    # Workspace
    workspace_mgr = WorkspaceManager(brand_name)
    workspace = workspace_mgr.path()

    # Enqueue
    task_id = queue.enqueue(brand_name, {"keyword": search_keyword})
    log(f"  Task ID: {task_id}")

    # Scrape LinkedIn
    log(f"  Scraping LinkedIn: '{search_keyword}'...")
    try:
        linkedin_posts = scrape_linkedin(search_keyword, max_results=20, country=country)
    except Exception as e:
        log(f"  ⚠ LinkedIn scrape error: {e}")
        linkedin_posts = []
    log(f"  LinkedIn posts: {len(linkedin_posts)}")

    # Reddit (placeholder — existing reddit scrapers not modified)
    reddit_posts = []

    # Brand awareness
    log("  Computing brand awareness...")
    awareness = compute_awareness(linkedin_posts + reddit_posts)

    # LLM Council
    log("  Convening LLM Council...")
    question = f"What is the current brand health of {brand_name} and what should they prioritise?"
    council_result = convene_council(brand_name, awareness, linkedin_posts[:3], question)

    # Build report
    log("  Building report...")
    markdown = build_report(
        brand_config=brand_config,
        linkedin_posts=linkedin_posts,
        reddit_posts=reddit_posts,
        awareness=awareness,
        council_result=council_result,
        workspace=workspace,
    )

    # Find saved report path
    report_files = sorted(workspace.glob("report_*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    report_path = str(report_files[0]) if report_files else str(workspace / "report.md")

    # Complete task
    queue.complete(task_id, result_path=report_path)

    # Summary output
    if use_rich:
        from rich.table import Table
        table = Table(title=f"📊 {brand_name} — Summary", show_header=True)
        table.add_column("Metric", style="bold")
        table.add_column("Value")
        table.add_row("Mention Volume", str(awareness["mention_volume"]))
        table.add_row("Avg Engagement", str(awareness["avg_engagement"]))
        table.add_row("Awareness Score", f"{awareness['awareness_score']}/100")
        table.add_row("Sentiment", f"+{awareness['sentiment_share']['positive']}% / -{awareness['sentiment_share']['negative']}%")
        table.add_row("Top Themes", ", ".join(awareness["top_themes"][:2]))
        table.add_row("Council Verdict", council_result.get("verdict", {}).get("verdict", "N/A") if isinstance(council_result.get("verdict"), dict) else "N/A")
        table.add_row("Report Path", report_path)
        console.print(table)
    else:
        print(f"\n=== {brand_name} Summary ===")
        print(f"Mention Volume:   {awareness['mention_volume']}")
        print(f"Avg Engagement:   {awareness['avg_engagement']}")
        print(f"Awareness Score:  {awareness['awareness_score']}/100")
        print(f"Report saved to:  {report_path}")

    return report_path


def main():
    parser = argparse.ArgumentParser(description="Brand Ops Marketing Suite")
    parser.add_argument("--brand", type=str, help="Brand name to run")
    parser.add_argument("--all", action="store_true", help="Run all brands in watchlist")
    parser.add_argument("--list", action="store_true", help="List brands in watchlist")
    args = parser.parse_args()

    watchlist_data = load_watchlist()
    brands = watchlist_data["watchlist"]

    if args.list:
        print("Brands in watchlist:")
        for b in brands:
            print(f"  - {b['brand']}")
        return

    # Readiness check
    readiness = check_readiness()
    print("\n🔍 Agent Readiness:")
    for name, status in readiness["checks"].items():
        icon = "✅" if status == "pass" else "❌"
        print(f"  {icon} {name}: {status}")
    for w in readiness.get("warnings", []):
        print(f"  ⚠  {w}")

    queue = TaskQueue()
    report_paths = []

    if args.all:
        for brand_config in brands:
            try:
                path = run_brand(brand_config, queue)
                report_paths.append(path)
                time.sleep(3)  # between brands
            except Exception as e:
                print(f"ERROR running {brand_config['brand']}: {e}")

    elif args.brand:
        matched = [b for b in brands if b["brand"].lower() == args.brand.lower()]
        if not matched:
            print(f"Brand '{args.brand}' not found in watchlist. Use --list to see available brands.")
            sys.exit(1)
        path = run_brand(matched[0], queue)
        report_paths.append(path)

    else:
        parser.print_help()
        sys.exit(1)

    print(f"\n✅ Done. Reports generated: {len(report_paths)}")
    for p in report_paths:
        print(f"   → {p}")


if __name__ == "__main__":
    main()
