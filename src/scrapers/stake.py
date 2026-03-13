"""
Stake.com scraper — stub for main.py pipeline.

Live scraping is implemented in node_workers/workers/stake.js (Puppeteer).
This stub returns an empty list so main.py can run (e.g. for testing enrichment).
"""

from typing import List, Dict, Any


class StakeScraper:
    """Stub scraper. Real automation runs in node_workers/workers/stake.js."""

    def __init__(self, duration: int = 120, chat_channel: str = "english", **kwargs: Any):
        self.duration = duration
        self.chat_channel = chat_channel

    def run(self) -> List[Dict[str, Any]]:
        """Return empty list; use Puppeteer worker for real scraping."""
        return []
