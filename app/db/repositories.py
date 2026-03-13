"""
Repository layer for database operations.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.models import RawPlayer, IdentityMatch, QualifiedLead
from app.enrich.schemas import EnrichmentResult, CandidateMatch


class RawPlayerRepository:
    """Repository for raw_players table."""
    
    @staticmethod
    def create(
        db: Session,
        username: str,
        source_site: Optional[str] = None,
        captured_at: Optional[datetime] = None
    ) -> RawPlayer:
        """Create a new raw player record."""
        raw_player = RawPlayer(
            username=username,
            source_site=source_site,
            captured_at=captured_at or datetime.utcnow(),
        )
        db.add(raw_player)
        db.flush()  # Flush to get ID without committing
        return raw_player
    
    @staticmethod
    def get_by_username(
        db: Session,
        username: str,
        source_site: Optional[str] = None
    ) -> Optional[RawPlayer]:
        """Get raw player by username and optional source site."""
        query = db.query(RawPlayer).filter(RawPlayer.username == username)
        if source_site:
            query = query.filter(RawPlayer.source_site == source_site)
        return query.first()


class IdentityMatchRepository:
    """Repository for identity_matches table."""
    
    @staticmethod
    def create_from_candidate(
        db: Session,
        raw_player_id: int,
        candidate: CandidateMatch
    ) -> IdentityMatch:
        """Create identity match from a CandidateMatch."""
        identity_match = IdentityMatch(
            raw_player_id=raw_player_id,
            platform=candidate.platform,
            social_handle=candidate.social_handle,
            social_url=candidate.social_url,
            display_name=candidate.display_name,
            avatar_url=candidate.avatar_url,
            public_contact_type=candidate.public_contact_type,
            public_contact_value=candidate.public_contact_value,
            match_score=candidate.match_score,
            confidence_label=candidate.confidence_label,
            scoring_reasons=candidate.scoring_reasons,
            evidence_json=candidate.evidence_json,
        )
        db.add(identity_match)
        return identity_match
    
    @staticmethod
    def create_batch(
        db: Session,
        raw_player_id: int,
        candidates: List[CandidateMatch]
    ) -> List[IdentityMatch]:
        """Create multiple identity matches from candidate list."""
        matches = []
        for candidate in candidates:
            match = IdentityMatchRepository.create_from_candidate(db, raw_player_id, candidate)
            matches.append(match)
        return matches


class QualifiedLeadRepository:
    """Repository for qualified_leads table."""
    
    @staticmethod
    def create_or_update(
        db: Session,
        raw_player_id: int,
        best_candidate: Optional[CandidateMatch],
        final_classification: str,
        notes: Optional[str] = None
    ) -> Optional[QualifiedLead]:
        """
        Create or update qualified lead.
        Only creates if classification is 'weak lead' or 'usable lead'.
        """
        if final_classification == "no lead":
            # Delete existing lead if it exists
            existing = db.query(QualifiedLead).filter(
                QualifiedLead.raw_player_id == raw_player_id
            ).first()
            if existing:
                db.delete(existing)
            return None
        
        # Check if lead already exists
        existing = db.query(QualifiedLead).filter(
            QualifiedLead.raw_player_id == raw_player_id
        ).first()
        
        if existing:
            # Update existing
            existing.best_contact_type = best_candidate.public_contact_type if best_candidate else None
            existing.best_contact_value = best_candidate.public_contact_value if best_candidate else None
            existing.confidence = best_candidate.match_score if best_candidate else None
            existing.confidence_label = final_classification
            existing.notes = notes
            return existing
        else:
            # Create new
            qualified_lead = QualifiedLead(
                raw_player_id=raw_player_id,
                best_contact_type=best_candidate.public_contact_type if best_candidate else None,
                best_contact_value=best_candidate.public_contact_value if best_candidate else None,
                confidence=best_candidate.match_score if best_candidate else None,
                confidence_label=final_classification,
                notes=notes,
            )
            db.add(qualified_lead)
            return qualified_lead


class EnrichmentRepository:
    """High-level repository for saving complete enrichment results."""
    
    @staticmethod
    def save_result(db: Session, result: EnrichmentResult) -> RawPlayer:
        """
        Save a complete enrichment result to the database.
        
        This creates:
        1. A raw_players record
        2. Zero or more identity_matches records
        3. A qualified_leads record (if applicable)
        
        Returns the created RawPlayer.
        """
        # 1. Create raw player
        raw_player = RawPlayerRepository.create(
            db=db,
            username=result.input_username,
            source_site=result.source_site,
            captured_at=datetime.fromisoformat(result.captured_at.replace('Z', '+00:00')) if result.captured_at else None,
        )
        
        # 2. Create identity matches
        if result.candidates:
            IdentityMatchRepository.create_batch(
                db=db,
                raw_player_id=raw_player.id,
                candidates=result.candidates,
            )
        
        # 3. Create/update qualified lead
        notes = None
        if result.best_match:
            notes = f"Best match: {result.best_match.platform} @{result.best_match.social_handle}"
        
        QualifiedLeadRepository.create_or_update(
            db=db,
            raw_player_id=raw_player.id,
            best_candidate=result.best_match,
            final_classification=result.final_classification,
            notes=notes,
        )
        
        return raw_player
