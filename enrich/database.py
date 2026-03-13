"""
Database persistence for enrichment results.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from enrich.models import EnrichmentResult, CandidateMatch

log = logging.getLogger(__name__)


class EnrichmentDB:
    """SQLite database for storing enrichment results."""
    
    def __init__(self, db_path: str = "enrichment.db"):
        self.db_path = Path(db_path)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # raw_players table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                source_site TEXT,
                captured_at TEXT NOT NULL,
                UNIQUE(username, source_site)
            )
        """)
        
        # identity_matches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS identity_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_username TEXT NOT NULL,
                platform TEXT NOT NULL,
                social_handle TEXT NOT NULL,
                social_url TEXT NOT NULL,
                display_name TEXT,
                avatar_url TEXT,
                public_contact_type TEXT,
                public_contact_value TEXT,
                match_score INTEGER NOT NULL,
                confidence_label TEXT NOT NULL,
                scoring_reasons TEXT,
                evidence_json TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(source_username, platform, social_handle)
            )
        """)
        
        # qualified_leads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qualified_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_username TEXT NOT NULL,
                best_contact_type TEXT,
                best_contact_value TEXT,
                confidence INTEGER,
                confidence_label TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(source_username)
            )
        """)
        
        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_username ON identity_matches(source_username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_platform ON identity_matches(platform)")
        
        conn.commit()
        conn.close()
        log.debug(f"Database initialized at {self.db_path}")
    
    def save_result(self, result: EnrichmentResult):
        """Save a complete enrichment result."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # Save raw player
            cursor.execute("""
                INSERT OR REPLACE INTO raw_players (username, source_site, captured_at)
                VALUES (?, ?, ?)
            """, (result.input_username, result.source_site, result.captured_at))
            
            # Save identity matches
            for candidate in result.candidates:
                cursor.execute("""
                    INSERT OR REPLACE INTO identity_matches (
                        source_username, platform, social_handle, social_url,
                        display_name, avatar_url, public_contact_type, public_contact_value,
                        match_score, confidence_label, scoring_reasons, evidence_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.input_username,
                    candidate.platform,
                    candidate.social_handle,
                    candidate.social_url,
                    candidate.display_name,
                    candidate.avatar_url,
                    candidate.public_contact_type,
                    candidate.public_contact_value,
                    candidate.match_score,
                    candidate.confidence_label,
                    json.dumps(candidate.scoring_reasons),
                    json.dumps(candidate.evidence_json),
                ))
            
            # Save qualified lead (if applicable)
            if result.final_classification in ("weak lead", "usable lead") and result.best_match:
                best = result.best_match
                cursor.execute("""
                    INSERT OR REPLACE INTO qualified_leads (
                        source_username, best_contact_type, best_contact_value,
                        confidence, confidence_label, notes
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    result.input_username,
                    best.public_contact_type,
                    best.public_contact_value,
                    best.match_score,
                    result.final_classification,
                    f"Best match: {best.platform} @{best.social_handle}",
                ))
            
            conn.commit()
            log.info(f"Saved enrichment result for {result.input_username}")
        
        except Exception as e:
            conn.rollback()
            log.error(f"Error saving result: {e}")
            raise
        finally:
            conn.close()
