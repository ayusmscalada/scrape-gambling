"""
SQLAlchemy database models.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.db.base import Base


class RawPlayer(Base):
    """Represents a captured username from a gambling platform."""
    
    __tablename__ = "raw_players"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), nullable=False, index=True)
    source_site = Column(String(100), nullable=True, index=True)
    captured_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    identity_matches = relationship("IdentityMatch", back_populates="raw_player", cascade="all, delete-orphan")
    qualified_lead = relationship("QualifiedLead", back_populates="raw_player", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_username_source", "username", "source_site"),
        UniqueConstraint("username", "source_site", name="uq_raw_players_username_source"),
    )


class IdentityMatch(Base):
    """Represents a discovered social media profile match for a raw player."""
    
    __tablename__ = "identity_matches"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_player_id = Column(Integer, ForeignKey("raw_players.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)  # telegram, instagram, x, youtube
    social_handle = Column(String(255), nullable=False)
    social_url = Column(String(512), nullable=False)
    display_name = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    public_contact_type = Column(String(50), nullable=True)  # telegram, email, website, discord
    public_contact_value = Column(String(255), nullable=True)
    match_score = Column(Integer, nullable=False, default=0)
    confidence_label = Column(String(50), nullable=False)  # exact match, likely match, weak match, no reliable match
    scoring_reasons = Column(JSONB, nullable=True)
    evidence_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    raw_player = relationship("RawPlayer", back_populates="identity_matches")
    
    __table_args__ = (
        Index("idx_raw_player_platform", "raw_player_id", "platform"),
        Index("idx_match_score", "match_score"),
    )


class QualifiedLead(Base):
    """Represents a qualified lead derived from a raw player's enrichment result."""
    
    __tablename__ = "qualified_leads"
    
    id = Column(Integer, primary_key=True, index=True)
    raw_player_id = Column(Integer, ForeignKey("raw_players.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    best_contact_type = Column(String(50), nullable=True)  # telegram, email, website, discord
    best_contact_value = Column(String(255), nullable=True)
    confidence = Column(Integer, nullable=True)  # Match score from best candidate
    confidence_label = Column(String(50), nullable=False)  # no lead, weak lead, usable lead
    notes = Column(String(1000), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    raw_player = relationship("RawPlayer", back_populates="qualified_lead")
    
    __table_args__ = (
        Index("idx_confidence_label", "confidence_label"),
    )
