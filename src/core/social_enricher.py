"""
Social Enricher — calls scan_socials.py for each unique username and
merges the returned social-link data back into player dicts.
"""

import subprocess
import json
import logging
import time
from typing import Dict, List, Optional
from pathlib import Path

log = logging.getLogger(__name__)


class SocialEnricher:
    """
    Runs `scan_socials.py <username>` as a subprocess and reads the JSON
    output.  Falls back gracefully if the script fails or times out.

    Parameters
    ----------
    scan_socials_path : path to scan_socials.py  (default: ./scan_socials.py)
    timeout           : seconds to wait per username lookup
    delay             : seconds to sleep between calls (rate-limit)
    """

    def __init__(
        self,
        scan_socials_path: str = "scan_socials.py",
        timeout: int = 30,
        delay: float = 1.0,
    ):
        self.script = Path(scan_socials_path)
        self.timeout = timeout
        self.delay = delay
        self._cache: Dict[str, Dict] = {}   # username → social dict

    # ── public API ─────────────────────────────────────────────────────────────

    def enrich_player(self, username: str) -> Dict:
        """
        Return a dict with keys: telegram, instagram, twitter, youtube.
        Result is cached so the same username is only looked up once.
        """
        if username in self._cache:
            return self._cache[username]

        result = self._run_scan(username)
        self._cache[username] = result
        return result

    def enrich_players(self, players: List[Dict]) -> List[Dict]:
        """
        Enrich a list of player dicts in-place and return them.
        Unique usernames are deduped before calling the script.
        """
        enriched = []
        seen: Dict[str, Dict] = {}

        for player in players:
            username = player.get("username", "").strip()
            if not username:
                enriched.append(player)
                continue

            # Only call scan_socials once per unique username
            if username not in seen:
                time.sleep(self.delay)
                seen[username] = self.enrich_player(username)

            player.update({k: v for k, v in seen[username].items() if v})
            enriched.append(player)

        log.info("Enriched %d players (%d unique lookups)", len(players), len(seen))
        return enriched

    # ── internals ──────────────────────────────────────────────────────────────

    def _run_scan(self, username: str) -> Dict:
        """Run scan_socials.py and parse its stdout as JSON."""
        empty = {"telegram": None, "instagram": None, "twitter": None, "youtube": None}

        if not self.script.exists():
            log.warning("scan_socials.py not found at %s — skipping enrichment", self.script)
            return empty

        try:
            proc = subprocess.run(
                ["python3", str(self.script), username],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            if proc.returncode != 0:
                log.debug("scan_socials stderr for %r: %s", username, proc.stderr.strip())
                return empty

            data = json.loads(proc.stdout)
            return {
                "telegram":  data.get("telegram"),
                "instagram": data.get("instagram"),
                "twitter":   data.get("twitter"),
                "youtube":   data.get("youtube"),
            }

        except subprocess.TimeoutExpired:
            log.warning("scan_socials timed out for %r", username)
        except json.JSONDecodeError:
            log.warning("scan_socials returned non-JSON for %r", username)
        except Exception as exc:
            log.error("Unexpected error enriching %r: %s", username, exc)

        return empty
