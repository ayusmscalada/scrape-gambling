"""
Rollbit.com scraper — stub for main.py pipeline.

Live scraping is implemented in node_workers/workers/rollbit.js (Puppeteer).
This stub returns an empty list so main.py can run (e.g. for testing enrichment).
"""

from typing import List, Dict, Any


class RollbitScraper:
    """Stub scraper. Real automation runs in node_workers/workers/rollbit.js."""

    def __init__(self, duration: int = 120, **kwargs: Any):
        self.duration = duration

    def run(self) -> List[Dict[str, Any]]:
        """Return empty list; use Puppeteer worker for real scraping."""
        return []
