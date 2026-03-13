#!/usr/bin/env python3
"""
main.py — Multi-platform gambling lead scraper runner.

Usage
-----
    python3 main.py --platform stake  [--duration 120] [--no-enrich] [--export leads.csv]
    python3 main.py --platform rollbit [--duration 120] [--no-enrich]

Options
-------
    --platform   Which platform to scrape  (stake | rollbit)  [default: stake]
    --duration   Seconds to run            (default: 120)
    --no-enrich  Skip social enrichment step
    --export     Export results to CSV after saving
    --channel    Stake chat channel        (default: english, stake only)
    --db         SQLite database file path (default: players.db)
"""

import argparse
import logging
import sys
from datetime import datetime

from src.core.database import Database
from src.core.social_enricher import SocialEnricher

# ── logging setup ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraper.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ── platform registry ─────────────────────────────────────────────────────────

PLATFORMS = {
    "stake":   "src.scrapers.stake:StakeScraper",
    "rollbit": "src.scrapers.rollbit:RollbitScraper",
}


def load_scraper(platform: str):
    """Dynamically import and return the scraper class for the given platform."""
    if platform not in PLATFORMS:
        log.error("Unknown platform %r. Choose from: %s", platform, list(PLATFORMS))
        sys.exit(1)

    module_path, class_name = PLATFORMS[platform].split(":")
    import importlib
    module = importlib.import_module(module_path.replace("/", "."))
    return getattr(module, class_name)


# ── CLI args ──────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Gambling platform player scraper")
    p.add_argument("--platform",  type=str, default="stake",
                   choices=list(PLATFORMS.keys()),
                   help="Platform to scrape (default: stake)")
    p.add_argument("--duration",  type=int, default=120,
                   help="Seconds to collect live data (default: 120)")
    p.add_argument("--channel",   type=str, default="english",
                   help="Chat channel — Stake only (default: english)")
    p.add_argument("--no-enrich", action="store_true",
                   help="Skip social link enrichment")
    p.add_argument("--export",    type=str, default=None,
                   help="Export results to this CSV path")
    p.add_argument("--db",        type=str, default="players.db",
                   help="SQLite database file (default: players.db)")
    return p.parse_args()


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    log.info("=" * 60)
    log.info("  Platform : %s", args.platform.upper())
    log.info("  Started  : %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log.info("  Duration : %d seconds", args.duration)
    log.info("  Enrich   : %s", not args.no_enrich)
    log.info("=" * 60)

    # ── 1. load correct scraper ───────────────────────────────────────────────
    ScraperClass = load_scraper(args.platform)

    # Build platform-specific kwargs
    kwargs = {"duration": args.duration}
    if args.platform == "stake":
        kwargs["chat_channel"] = args.channel

    scraper = ScraperClass(**kwargs)

    # ── 2. scrape ─────────────────────────────────────────────────────────────
    players = scraper.run()

    if not players:
        log.warning("No players found. Check network/selectors and try again.")
        return

    log.info("Scraped %d unique players from %s", len(players), args.platform.upper())

    # ── 3. social enrichment ──────────────────────────────────────────────────
    if not args.no_enrich:
        log.info("Enriching players with social links…")
        enricher = SocialEnricher(delay=1.0)
        players  = enricher.enrich_players(players)
        with_socials = sum(1 for p in players
                           if any(p.get(k) for k in
                                  ("telegram", "instagram", "twitter", "youtube")))
        log.info("Enrichment done — %d / %d players have socials",
                 with_socials, len(players))
    else:
        log.info("Social enrichment skipped (--no-enrich)")

    # ── 4. save to database ───────────────────────────────────────────────────
    db = Database(db_path=args.db)
    db.save_players(players)
    log.info("Saved %d players → %s  (total in DB: %d)",
             len(players), args.db, db.count())

    # ── 5. optional CSV export ────────────────────────────────────────────────
    if args.export:
        db.export_csv(args.export, platform=args.platform.capitalize())
        log.info("CSV exported → %s", args.export)

    # ── 6. summary ────────────────────────────────────────────────────────────
    log.info("=" * 60)
    log.info("  Done.  Total in DB : %d", db.count())
    log.info("  Source breakdown:")
    for source in ("live_bet", "chat", "pack_opening"):
        n = sum(1 for p in players if p.get("source") == source)
        if n:
            log.info("    %-20s: %d", source, n)
    log.info("=" * 60)

    db.close()


if __name__ == "__main__":
    main()
