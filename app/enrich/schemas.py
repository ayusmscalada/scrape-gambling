"""
Data models for social enrichment pipeline.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class Candidate:
    """A discovered candidate profile/page."""
    platform: str
    social_handle: str
    social_url: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio_text: Optional[str] = None
    external_links: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Evidence:
    """Extracted evidence from a candidate profile."""
    platform: str
    social_handle: str
    social_url: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio_text: Optional[str] = None
    platform_mentions: List[str] = field(default_factory=list)  # e.g., ["Stake", "Rollbit"]
    referral_codes: List[str] = field(default_factory=list)
    wallet_mentions: List[str] = field(default_factory=list)
    creator_links: List[str] = field(default_factory=list)
    public_contact_type: Optional[str] = None  # "telegram", "email", "website", "discord"
    public_contact_value: Optional[str] = None
    language_clues: List[str] = field(default_factory=list)
    region_clues: List[str] = field(default_factory=list)
    external_links: List[str] = field(default_factory=list)
    evidence_json: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoreResult:
    """Confidence scoring result for a candidate."""
    match_score: int
    confidence_label: str  # "exact match", "likely match", "weak match", "no reliable match"
    scoring_reasons: List[str] = field(default_factory=list)
    evidence: Evidence = None


@dataclass
class CandidateMatch:
    """A scored and classified candidate match."""
    source_username: str
    platform: str
    social_handle: str
    social_url: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    match_score: int = 0
    confidence_label: str = "no reliable match"
    scoring_reasons: List[str] = field(default_factory=list)
    public_contact_type: Optional[str] = None
    public_contact_value: Optional[str] = None
    evidence_json: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EnrichmentResult:
    """Complete enrichment result for a username."""
    input_username: str
    source_site: Optional[str] = None
    variants: List[str] = field(default_factory=list)
    candidates: List[CandidateMatch] = field(default_factory=list)
    best_match: Optional[CandidateMatch] = None
    final_classification: str = "no lead"  # "no lead", "weak lead", "usable lead"
    captured_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "input_username": self.input_username,
            "source_site": self.source_site,
            "variants": self.variants,
            "candidates": [c.to_dict() for c in self.candidates],
            "best_match": self.best_match.to_dict() if self.best_match else None,
            "final_classification": self.final_classification,
            "captured_at": self.captured_at,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
