"""
SQLite database layer.

Creates / manages the `players` table and provides helpers for bulk-upserts,
deduplication checks, and CSV export.
"""

import sqlite3
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

log = logging.getLogger(__name__)


# ── schema ────────────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS players (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL,
    platform    TEXT    NOT NULL,
    source      TEXT    NOT NULL,          -- live_bet | chat | pack_opening
    timestamp   TEXT    NOT NULL,
    telegram    TEXT,
    instagram   TEXT,
    twitter     TEXT,
    youtube     TEXT,
    metadata    TEXT    DEFAULT '{}',      -- JSON blob
    created_at  TEXT    DEFAULT (datetime('now')),
    UNIQUE(username, platform, source)     -- avoid exact duplicates
)
"""

UPSERT_SQL = """
INSERT INTO players
    (username, platform, source, timestamp, telegram, instagram, twitter, youtube, metadata)
VALUES
    (:username, :platform, :source, :timestamp,
     :telegram, :instagram, :twitter, :youtube, :metadata)
ON CONFLICT(username, platform, source) DO UPDATE SET
    timestamp = excluded.timestamp,
    telegram  = COALESCE(excluded.telegram,  players.telegram),
    instagram = COALESCE(excluded.instagram, players.instagram),
    twitter   = COALESCE(excluded.twitter,   players.twitter),
    youtube   = COALESCE(excluded.youtube,   players.youtube),
    metadata  = excluded.metadata
"""


# ── Database class ─────────────────────────────────────────────────────────────

class Database:
    """Thread-safe (single-thread) SQLite wrapper."""

    def __init__(self, db_path: str = "players.db"):
        self.db_path = Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None
        self._init()

    # ── lifecycle ──────────────────────────────────────────────────────────────

    def _init(self):
        conn = self._get_conn()
        conn.execute(CREATE_TABLE_SQL)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_platform ON players(platform)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_username ON players(username)")
        conn.commit()
        log.info("Database ready at %s", self.db_path)

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self.db_path),
                detect_types=sqlite3.PARSE_DECLTYPES,
                check_same_thread=False,
            )
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── writes ─────────────────────────────────────────────────────────────────

    def save_player(self, player: Dict):
        """Upsert a single player record."""
        row = {
            "username":  player.get("username", ""),
            "platform":  player.get("platform", ""),
            "source":    player.get("source", ""),
            "timestamp": player.get("timestamp", ""),
            "telegram":  player.get("telegram"),
            "instagram": player.get("instagram"),
            "twitter":   player.get("twitter"),
            "youtube":   player.get("youtube"),
            "metadata":  json.dumps(player.get("metadata", {})),
        }
        conn = self._get_conn()
        conn.execute(UPSERT_SQL, row)
        conn.commit()

    def save_players(self, players: List[Dict]):
        """Bulk upsert — wraps everything in a single transaction."""
        conn = self._get_conn()
        rows = []
        for p in players:
            rows.append({
                "username":  p.get("username", ""),
                "platform":  p.get("platform", ""),
                "source":    p.get("source", ""),
                "timestamp": p.get("timestamp", ""),
                "telegram":  p.get("telegram"),
                "instagram": p.get("instagram"),
                "twitter":   p.get("twitter"),
                "youtube":   p.get("youtube"),
                "metadata":  json.dumps(p.get("metadata", {})),
            })
        conn.executemany(UPSERT_SQL, rows)
        conn.commit()
        log.info("Saved %d players to database", len(rows))

    # ── reads ──────────────────────────────────────────────────────────────────

    def get_all(self, platform: Optional[str] = None) -> List[Dict]:
        conn = self._get_conn()
        if platform:
            rows = conn.execute(
                "SELECT * FROM players WHERE platform = ?", (platform,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM players").fetchall()
        return [dict(r) for r in rows]

    def count(self, platform: Optional[str] = None) -> int:
        conn = self._get_conn()
        if platform:
            return conn.execute(
                "SELECT COUNT(*) FROM players WHERE platform = ?", (platform,)
            ).fetchone()[0]
        return conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]

    def username_exists(self, username: str, platform: str) -> bool:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT 1 FROM players WHERE username=? AND platform=? LIMIT 1",
            (username, platform),
        ).fetchone()
        return row is not None

    # ── export ─────────────────────────────────────────────────────────────────

    def export_csv(self, output_path: str = "leads.csv",
                   platform: Optional[str] = None):
        """Export all (or platform-filtered) rows to a CSV file."""
        rows = self.get_all(platform)
        if not rows:
            log.warning("No rows to export.")
            return
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        log.info("Exported %d rows → %s", len(rows), output_path)
