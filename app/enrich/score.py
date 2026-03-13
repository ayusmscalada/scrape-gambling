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
    Score a candidate match - binary scoring: 100 if found, 0 if not found.
    
    Simple binary scoring:
    - If profile found on platform: score = 100
    - If profile not found on platform: score = 0
    
    Args:
        source_username: Original username (not used in binary scoring)
        variants: Generated username variants (not used in binary scoring)
        evidence: Extracted evidence
        
    Returns:
        ScoreResult with match score = 100 (always, since if we have evidence, profile was found)
    """
    # Binary scoring: if we have evidence, the profile was found = 100
    score = 100
    reasons = ["Profile found on platform +100"]
    
    return ScoreResult(
        match_score=score,
        confidence_label="found",
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
