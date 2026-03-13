"""
Repository layer for database operations.
"""

from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID

from app.db.models import RawPlayer, IdentityMatch


class RawPlayerRepository:
    """Repository for raw_players table."""
    
    @staticmethod
    def create(
        db: Session,
        site: str,
        username: str,
        rank: Optional[int] = None,
        metric_value: Optional[float] = None,
        source_url: Optional[str] = None,
        captured_at: Optional[datetime] = None
    ) -> RawPlayer:
        """Create a new raw player record."""
        raw_player = RawPlayer(
            site=site,
            username=username,
            rank=rank,
            metric_value=metric_value,
            source_url=source_url,
            captured_at=captured_at or datetime.utcnow(),
        )
        db.add(raw_player)
        db.flush()
        return raw_player
    
    @staticmethod
    def get_by_site_username(
        db: Session,
        site: str,
        username: str
    ) -> Optional[RawPlayer]:
        """Get raw player by site and username."""
        return db.query(RawPlayer).filter(
            RawPlayer.site == site,
            RawPlayer.username == username
        ).first()
