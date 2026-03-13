"""
Background job service for enriching raw_players with social media data.
"""

import logging
import time
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore

from app.db.session import db_session
from app.db.models import RawPlayer, IdentityMatch, QualifiedLead
from app.db.repositories import EnrichmentRepository
from scan_socials import enrich_username

log = logging.getLogger(__name__)


class EnrichmentJobService:
    """
    Background job service that periodically enriches unchecked raw_players.
    """
    
    def __init__(
        self,
        interval_seconds: int = 60,
        batch_size: int = 10,
        max_results: int = 20
    ):
        """
        Initialize the enrichment job service.
        
        Args:
            interval_seconds: How often to run the enrichment job (default: 60 seconds)
            batch_size: How many raw_players to process per run (default: 10)
            max_results: Maximum candidates to discover per username (default: 20)
        """
        self.interval_seconds = interval_seconds
        self.batch_size = batch_size
        self.max_results = max_results
        self.scheduler = None
        self.is_running = False
        
    def _get_unchecked_raw_players(self, db: Session, limit: int) -> List[RawPlayer]:
        """
        Get raw_players that haven't been enriched yet.
        
        A raw_player is considered "unchecked" if:
        - It has no identity_matches, AND
        - It has no qualified_lead
        
        Args:
            db: Database session
            limit: Maximum number of players to return
            
        Returns:
            List of RawPlayer objects
        """
        try:
            # Find raw_players that have no identity_matches and no qualified_lead
            # Using LEFT JOIN and checking for NULL
            unchecked = db.query(RawPlayer).outerjoin(
                IdentityMatch, RawPlayer.id == IdentityMatch.raw_player_id
            ).outerjoin(
                QualifiedLead, RawPlayer.id == QualifiedLead.raw_player_id
            ).filter(
                and_(
                    IdentityMatch.id.is_(None),
                    QualifiedLead.id.is_(None)
                )
            ).order_by(
                RawPlayer.captured_at.asc()  # Process oldest first
            ).limit(limit).all()
            
            return unchecked
        except Exception as e:
            # Handle case where tables don't exist yet
            if "does not exist" in str(e) or "UndefinedTable" in str(e):
                log.warning("Database tables not found. Please run migrations first: alembic upgrade head")
                return []
            raise
    
    def _enrich_raw_player(self, raw_player_id: int) -> bool:
        """
        Enrich a single raw_player with social media data.
        
        Args:
            raw_player_id: ID of RawPlayer to enrich
            
        Returns:
            True if enrichment was successful, False otherwise
        """
        try:
            # Get raw_player in a new session and access attributes while session is active
            with db_session() as session:
                raw_player = session.query(RawPlayer).filter(
                    RawPlayer.id == raw_player_id
                ).first()
                
                if not raw_player:
                    log.warning(f"RawPlayer {raw_player_id} not found in database")
                    return False
                
                # Check if already enriched (race condition check)
                has_matches = session.query(IdentityMatch).filter(
                    IdentityMatch.raw_player_id == raw_player.id
                ).first() is not None
                
                has_lead = session.query(QualifiedLead).filter(
                    QualifiedLead.raw_player_id == raw_player.id
                ).first() is not None
                
                if has_matches or has_lead:
                    log.info(f"RawPlayer {raw_player.id} already enriched, skipping")
                    return True
                
                # Access attributes while session is active
                username = raw_player.username
                source_site = raw_player.source_site
                
                log.info(f"Enriching raw_player {raw_player.id}: {username} (source: {source_site})")
            
            # Run enrichment outside of session (this can take time)
            result = enrich_username(
                username=username,
                source_site=source_site,
                max_results=self.max_results
            )
            
            # Save results to database in a new session
            with db_session() as session:
                # Get the raw_player again in this session
                db_raw_player = session.query(RawPlayer).filter(
                    RawPlayer.id == raw_player_id
                ).first()
                
                if not db_raw_player:
                    log.warning(f"RawPlayer {raw_player_id} not found in database")
                    return False
                
                # Double-check if enriched while we were running (race condition)
                has_matches = session.query(IdentityMatch).filter(
                    IdentityMatch.raw_player_id == db_raw_player.id
                ).first() is not None
                
                has_lead = session.query(QualifiedLead).filter(
                    QualifiedLead.raw_player_id == db_raw_player.id
                ).first() is not None
                
                if has_matches or has_lead:
                    log.info(f"RawPlayer {db_raw_player.id} already enriched (race condition), skipping")
                    return True
                
                # Create identity matches from enrichment result
                if result.candidates:
                    from app.db.repositories import IdentityMatchRepository
                    IdentityMatchRepository.create_batch(
                        db=session,
                        raw_player_id=db_raw_player.id,
                        candidates=result.candidates,
                    )
                    log.info(f"Created {len(result.candidates)} identity matches for {username}")
                
                # Create/update qualified lead
                from app.db.repositories import QualifiedLeadRepository
                notes = None
                if result.best_match:
                    notes = f"Best match: {result.best_match.platform} @{result.best_match.social_handle}"
                
                QualifiedLeadRepository.create_or_update(
                    db=session,
                    raw_player_id=db_raw_player.id,
                    best_candidate=result.best_match,
                    final_classification=result.final_classification,
                    notes=notes,
                )
                
                session.commit()
                log.info(f"Enrichment complete for {username}: {result.final_classification}")
                return True
                
        except Exception as e:
            log.error(f"Error enriching raw_player {raw_player_id}: {e}", exc_info=True)
            return False
    
    def _process_batch(self):
        """
        Process a batch of unchecked raw_players.
        This is called periodically by the scheduler.
        """
        if not self.is_running:
            return
        
        try:
            log.info(f"Starting enrichment batch (batch_size: {self.batch_size})")
            
            # Get unchecked raw_players
            with db_session() as session:
                unchecked = self._get_unchecked_raw_players(session, limit=self.batch_size)
            
            if not unchecked:
                log.debug("No unchecked raw_players found")
                return
            
            log.info(f"Found {len(unchecked)} unchecked raw_players to enrich")
            
            # Process each raw_player
            success_count = 0
            error_count = 0
            
            for raw_player in unchecked:
                if not self.is_running:
                    log.info("Job service stopped, aborting batch processing")
                    break
                
                # Pass only the ID to avoid session issues
                success = self._enrich_raw_player(raw_player.id)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                
                # Small delay between enrichments to avoid rate limiting
                time.sleep(2)
            
            log.info(f"Batch complete: {success_count} succeeded, {error_count} failed")
            
        except Exception as e:
            log.error(f"Error in enrichment batch processing: {e}", exc_info=True)
    
    def start(self):
        """Start the background job scheduler."""
        if self.is_running:
            log.warning("Enrichment job service is already running")
            return
        
        log.info(f"Starting enrichment job service (interval: {self.interval_seconds}s, batch_size: {self.batch_size})")
        
        # Configure scheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(1)  # Single thread to avoid database conflicts
        }
        job_defaults = {
            'coalesce': True,  # Combine multiple pending jobs into one
            'max_instances': 1,  # Only one instance running at a time
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        # Add the enrichment job
        self.scheduler.add_job(
            self._process_batch,
            'interval',
            seconds=self.interval_seconds,
            id='enrichment_job',
            name='Enrich unchecked raw_players',
            replace_existing=True
        )
        
        self.is_running = True
        self.scheduler.start()
        
        # Run initial batch immediately
        log.info("Running initial enrichment batch...")
        self._process_batch()
        
        log.info("Enrichment job service started successfully")
    
    def stop(self):
        """Stop the background job scheduler."""
        if not self.is_running:
            log.warning("Enrichment job service is not running")
            return
        
        log.info("Stopping enrichment job service...")
        self.is_running = False
        
        if self.scheduler:
            self.scheduler.shutdown(wait=True)
            self.scheduler = None
        
        log.info("Enrichment job service stopped")
    
    def trigger_now(self):
        """Manually trigger an enrichment batch (for testing)."""
        if not self.is_running:
            log.warning("Enrichment job service is not running")
            return False
        
        log.info("Manually triggering enrichment batch...")
        self._process_batch()
        return True
    
    def get_stats(self) -> dict:
        """Get statistics about the job service."""
        try:
            with db_session() as session:
                try:
                    total_raw_players = session.query(RawPlayer).count()
                    
                    # Count enriched (have identity_matches or qualified_lead)
                    enriched_count = session.query(RawPlayer).outerjoin(
                        IdentityMatch, RawPlayer.id == IdentityMatch.raw_player_id
                    ).outerjoin(
                        QualifiedLead, RawPlayer.id == QualifiedLead.raw_player_id
                    ).filter(
                        or_(
                            IdentityMatch.id.isnot(None),
                            QualifiedLead.id.isnot(None)
                        )
                    ).count()
                    
                    unchecked_count = total_raw_players - enriched_count
                    
                    return {
                        'is_running': self.is_running,
                        'interval_seconds': self.interval_seconds,
                        'batch_size': self.batch_size,
                        'total_raw_players': total_raw_players,
                        'enriched_count': enriched_count,
                        'unchecked_count': unchecked_count,
                        'next_run': None  # Could add next run time if needed
                    }
                except Exception as db_error:
                    # Handle case where tables don't exist yet
                    if "does not exist" in str(db_error) or "UndefinedTable" in str(db_error):
                        return {
                            'is_running': self.is_running,
                            'interval_seconds': self.interval_seconds,
                            'batch_size': self.batch_size,
                            'error': 'Database tables not found. Please run: alembic upgrade head',
                            'total_raw_players': 0,
                            'enriched_count': 0,
                            'unchecked_count': 0,
                        }
                    raise
        except Exception as e:
            log.error(f"Error getting stats: {e}")
            return {
                'is_running': self.is_running,
                'error': str(e)
            }
