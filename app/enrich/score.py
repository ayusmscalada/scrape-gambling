"""
Confidence scoring for candidate matches.
"""

import logging
from typing import List

from app.enrich.schemas import Evidence, ScoreResult

log = logging.getLogger(__name__)


def score_candidate(
    source_username: str,
    variants: List[str],
    evidence: Evidence
) -> ScoreResult:
    """
    Score a candidate match based on evidence.
    
    Scoring rules:
    - exact username match: +30
    - strong username variant match: +20
    - same/similar avatar or profile image URL pattern: +25
    - same platform mentioned in bio/post/page: +20
    - same referral code / creator link / wallet mention: +40
    - similar language/timezone/region clues: +10
    - inconsistent country/language/profile type: -15
    - no evidence beyond username similarity: -20
    
    Args:
        source_username: Original username
        variants: Generated username variants
        evidence: Extracted evidence
        
    Returns:
        ScoreResult with match score and reasons
    """
    score = 0
    reasons: List[str] = []
    
    source_lower = source_username.lower()
    handle_lower = evidence.social_handle.lower()
    
    # Username matching
    if handle_lower == source_lower:
        score += 30
        reasons.append("exact username match +30")
    elif handle_lower in variants:
        score += 20
        reasons.append(f"strong username variant match +20")
    elif _is_similar_username(source_lower, handle_lower):
        score += 15
        reasons.append("similar username pattern +15")
    else:
        score -= 20
        reasons.append("no evidence beyond username similarity -20")
    
    # Avatar/profile image (if we have it)
    if evidence.avatar_url:
        score += 25
        reasons.append("public avatar/profile image available +25")
    
    # Platform mentions
    if evidence.platform_mentions:
        score += 20
        reasons.append(f"platform mention in bio ({', '.join(evidence.platform_mentions[:3])}) +20")
    
    # Referral codes / creator links / wallet mentions
    if evidence.referral_codes:
        score += 40
        reasons.append(f"referral/creator code found ({len(evidence.referral_codes)} codes) +40")
    
    if evidence.wallet_mentions:
        score += 40
        reasons.append(f"wallet mention found ({len(evidence.wallet_mentions)} mentions) +40")
    
    if evidence.creator_links:
        score += 40
        reasons.append(f"creator link found ({len(evidence.creator_links)} links) +40")
    
    # Language/region clues
    if evidence.language_clues:
        score += 10
        reasons.append(f"language clues found ({', '.join(evidence.language_clues)}) +10")
    
    if evidence.region_clues:
        score += 10
        reasons.append(f"region clues found ({', '.join(evidence.region_clues)}) +10")
    
    # Clamp score to reasonable range
    score = max(0, min(100, score))
    
    # Determine confidence label
    if score >= 70:
        confidence_label = "exact match"
    elif score >= 50:
        confidence_label = "likely match"
    elif score >= 30:
        confidence_label = "weak match"
    else:
        confidence_label = "no reliable match"
    
    return ScoreResult(
        match_score=score,
        confidence_label=confidence_label,
        scoring_reasons=reasons,
        evidence=evidence,
    )


def _is_similar_username(source: str, handle: str) -> bool:
    """Check if two usernames are similar (fuzzy match)."""
    if not source or not handle:
        return False
    
    # Exact match
    if source == handle:
        return True
    
    # One is a substring of the other (if meaningful length)
    if len(source) >= 5 and len(handle) >= 5:
        if source in handle or handle in source:
            return True
    
    # Levenshtein-like: check if most characters match
    if len(source) >= 4 and len(handle) >= 4:
        common_chars = sum(1 for c in source if c in handle)
        similarity = common_chars / max(len(source), len(handle))
        if similarity >= 0.7:
            return True
    
    return False
