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
    
    With binary scoring:
    - If any platform found (overall_score > 0): weak lead or usable lead
    - If no platforms found (overall_score = 0): no lead
    - If public contact path exists: usable lead
    - If no public contact path: weak lead
    
    Args:
        best_candidate: Best candidate match (if any)
        
    Returns:
        "no lead", "weak lead", or "usable lead"
    """
    if not best_candidate:
        return "no lead"
    
    # With binary scoring, if we have a candidate, it means at least one platform was found
    # Check if there's a public contact path
    has_contact = (
        best_candidate.public_contact_type is not None and
        best_candidate.public_contact_value is not None
    )
    
    # Usable lead: platform found + public contact
    if has_contact:
        return "usable lead"
    
    # Weak lead: platform found but no strong contact path
    return "weak lead"
