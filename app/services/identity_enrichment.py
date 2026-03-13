"""
Identity enrichment service for creating identity matches.
"""

import logging
from typing import Optional, Dict
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.models import RawPlayer, IdentityMatch

log = logging.getLogger(__name__)


def calculate_scores(socials: Dict[str, Optional[str]]) -> Dict[str, int]:
    """
    Calculate platform scores based on URLs.
    
    Args:
        socials: Dictionary with keys: telegram_url, instagram_url, x_url, youtube_url
        
    Returns:
        Dictionary with platform scores
    """
    return {
        'telegram_score': 100 if socials.get('telegram_url') else 0,
        'instagram_score': 100 if socials.get('instagram_url') else 0,
        'x_score': 100 if socials.get('x_url') else 0,
        'youtube_score': 100 if socials.get('youtube_url') else 0,
    }


def calculate_total_score(scores: Dict[str, int]) -> int:
    """
    Calculate total score as average of all platform scores.
    
    Args:
        scores: Dictionary with platform scores
        
    Returns:
        Total score (0, 25, 50, 75, or 100)
    """
    platform_scores = [
        scores['telegram_score'],
        scores['instagram_score'],
        scores['x_score'],
        scores['youtube_score'],
    ]
    return int(sum(platform_scores) / len(platform_scores))


def create_identity_match(
    db: Session,
    raw_player_id: UUID,
    socials: Dict[str, Optional[str]]
) -> Optional[IdentityMatch]:
    """
    Create an identity match for a raw player.
    
    Logic:
    1. Compute platform scores (100 if URL found, 0 if not)
    2. Compute total_score = average of platform scores
    3. If total_score == 0 → return None (don't create row)
    4. Insert identity_matches row
    
    Args:
        db: Database session
        raw_player_id: UUID of the raw player
        socials: Dictionary with keys: telegram_url, instagram_url, x_url, youtube_url
        
    Returns:
        IdentityMatch instance if created, None if total_score == 0
    """
    # Verify raw_player exists
    raw_player = db.query(RawPlayer).filter(RawPlayer.id == raw_player_id).first()
    if not raw_player:
        log.warning(f"RawPlayer {raw_player_id} not found")
        return None
    
    # Check if identity_match already exists
    existing = db.query(IdentityMatch).filter(IdentityMatch.raw_player_id == raw_player_id).first()
    if existing:
        log.info(f"IdentityMatch already exists for raw_player_id {raw_player_id}, updating...")
        # Update existing
        existing.telegram_url = socials.get('telegram_url')
        existing.instagram_url = socials.get('instagram_url')
        existing.x_url = socials.get('x_url')
        existing.youtube_url = socials.get('youtube_url')
        
        scores = calculate_scores(socials)
        existing.telegram_score = scores['telegram_score']
        existing.instagram_score = scores['instagram_score']
        existing.x_score = scores['x_score']
        existing.youtube_score = scores['youtube_score']
        existing.total_score = calculate_total_score(scores)
        
        # If total_score becomes 0, delete the record
        if existing.total_score == 0:
            db.delete(existing)
            return None
        
        return existing
    
    # Calculate scores
    scores = calculate_scores(socials)
    total_score = calculate_total_score(scores)
    
    # Rule: If total_score == 0, DO NOT create identity_matches row
    if total_score == 0:
        log.debug(f"Total score is 0 for raw_player_id {raw_player_id}, skipping identity_match creation")
        return None
    
    # Create new identity match
    identity_match = IdentityMatch(
        raw_player_id=raw_player_id,
        telegram_url=socials.get('telegram_url'),
        instagram_url=socials.get('instagram_url'),
        x_url=socials.get('x_url'),
        youtube_url=socials.get('youtube_url'),
        telegram_score=scores['telegram_score'],
        instagram_score=scores['instagram_score'],
        x_score=scores['x_score'],
        youtube_score=scores['youtube_score'],
        total_score=total_score,
    )
    
    db.add(identity_match)
    return identity_match
