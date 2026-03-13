"""
SQLAlchemy database models.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index, UniqueConstraint, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class RawPlayer(Base):
    """Represents a captured username from a gambling platform."""
    
    __tablename__ = "raw_players"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    site = Column(String(255), nullable=False, index=True)
    username = Column(String(255), nullable=False, index=True)
    rank = Column(Integer, nullable=True)
    metric_value = Column(Numeric, nullable=True)
    source_url = Column(String(512), nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    
    # Relationships
    identity_match = relationship("IdentityMatch", back_populates="raw_player", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_site_username", "site", "username"),
    )


class IdentityMatch(Base):
    """Represents social enrichment results for a raw player."""
    
    __tablename__ = "identity_matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    raw_player_id = Column(UUID(as_uuid=True), ForeignKey("raw_players.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Platform URLs
    telegram_url = Column(String(512), nullable=True)
    instagram_url = Column(String(512), nullable=True)
    x_url = Column(String(512), nullable=True)
    youtube_url = Column(String(512), nullable=True)
    
    # Platform scores (binary: 100 if found, 0 if not)
    telegram_score = Column(Integer, nullable=False, default=0)
    instagram_score = Column(Integer, nullable=False, default=0)
    x_score = Column(Integer, nullable=False, default=0)
    youtube_score = Column(Integer, nullable=False, default=0)
    
    # Total score: (telegram_score + instagram_score + x_score + youtube_score) / 4
    total_score = Column(Integer, nullable=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    
    # Relationships
    raw_player = relationship("RawPlayer", back_populates="identity_match")
    
    __table_args__ = (
        Index("idx_total_score", "total_score"),
        UniqueConstraint("raw_player_id", name="unique_identity_match"),
    )
