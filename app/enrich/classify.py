"""
Lead classification logic.
"""

from typing import Optional

from app.enrich.schemas import ScoreResult, Evidence, CandidateMatch


def classify_candidate(score_result: ScoreResult, evidence: Evidence) -> str:
    """
    Classify a candidate into: exact match, likely match, weak match, no reliable match.
    
    Args:
        score_result: Scoring result
        evidence: Extracted evidence
        
    Returns:
        Classification label
    """
    return score_result.confidence_label


def classify_lead(best_candidate: Optional[CandidateMatch]) -> str:
    """
    Classify the overall lead into: no lead, weak lead, usable lead.
    
    Decision logic:
    - Username only = signal only
    - Public matched profile = identity hypothesis
    - Reachable public contact = usable lead
    
    Args:
        best_candidate: Best candidate match (if any)
        
    Returns:
        "no lead", "weak lead", or "usable lead"
    """
    if not best_candidate:
        return "no lead"
    
    # Check if there's a public contact path
    has_contact = (
        best_candidate.public_contact_type is not None and
        best_candidate.public_contact_value is not None
    )
    
    # Check confidence
    is_strong_match = best_candidate.confidence_label in ("exact match", "likely match")
    is_weak_match = best_candidate.confidence_label == "weak match"
    
    # Usable lead: strong match + public contact
    if is_strong_match and has_contact:
        return "usable lead"
    
    # Weak lead: likely identity match but no strong contact path
    if is_strong_match or (is_weak_match and has_contact):
        return "weak lead"
    
    # No lead: everything else
    return "no lead"
