#!/usr/bin/env python3
"""
main.py — Single entrypoint for Brand Listener
https://github.com/NinjaDS/brand-listener

Usage:
    # Run a single brand manually
    python3 main.py --brand "Adidas" --competitors "Nike,Puma" --topic "sportswear"

    # Run all brands from watchlist.json immediately
    python3 main.py --schedule --run-now

    # Run as daemon (fires on schedule defined in watchlist.json)
    python3 main.py --schedule --daemon

    # Run one brand from watchlist
    python3 main.py --schedule --brand "Adidas"
"""

import sys
import argparse
from pathlib import Path

# Make sure subpackages are importable
sys.path.insert(0, str(Path(__file__).parent))

from core.brand_listener import run as _run_single


def main():
    parser = argparse.ArgumentParser(
        description="Brand Listener — AI-powered social listening + LLM brand audit"
    )
    parser.add_argument("--brand",        default="",       help="Brand name to monitor")
    parser.add_argument("--competitors",  default="",       help="Comma-separated competitor names")
    parser.add_argument("--topic",        default="",       help="Topic/industry context")
    parser.add_argument("--country",      default="",       help="Country focus (e.g. Italy, UK)")
    parser.add_argument("--subsidiaries", default="",       help="Comma-separated subsidiary brand names")
    parser.add_argument("--region",       default="global",
                        choices=["global", "european", "italian", "us", "uk", "apac"],
                        help="Audience region context for LLM audit")
    parser.add_argument("--schedule",     action="store_true", help="Use scheduler mode")
    parser.add_argument("--run-now",      action="store_true", help="Run all watchlist brands now")
    parser.add_argument("--daemon",       action="store_true", help="Run as daemon on schedule")
    args = parser.parse_args()

    if args.schedule or args.run_now or args.daemon:
        # Scheduler mode
        from scheduler.scheduler import run_all_now, daemon_mode, run_brand, load_watchlist, load_history, save_history
        if args.daemon:
            daemon_mode()
        elif args.brand:
            config  = load_watchlist()
            history = load_history()
            entries = [e for e in config.get("watchlist", [])
                       if e["brand"].lower() == args.brand.lower()]
            if not entries:
                print(f"Brand '{args.brand}' not found in watchlist.json")
                sys.exit(1)
            run_brand(entries[0], config, history)
            save_history(history)
        else:
            run_all_now()
    elif args.brand:
        # Single brand CLI mode
        comps = [c.strip() for c in args.competitors.split(",") if c.strip()]
        subs  = [s.strip() for s in args.subsidiaries.split(",") if s.strip()]
        topic = args.topic or args.brand
        _run_single(args.brand, comps, topic,
                    country=args.country, subsidiaries=subs, region=args.region)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
