"""
Background job service for enriching raw_players with social media data.
"""

import logging
import time
import threading
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore

from app.db.session import db_session
from app.db.models import RawPlayer, IdentityMatch
from app.services.identity_enrichment import create_identity_match
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
        max_results: int = 20,
        socketio=None
    ):
        """
        Initialize the enrichment job service.
        
        Args:
            interval_seconds: How often to run the enrichment job (default: 60 seconds)
            batch_size: How many raw_players to process per run (default: 10)
            max_results: Maximum candidates to discover per username (default: 20)
            socketio: Optional Flask-SocketIO instance for emitting WebSocket events
        """
        self.interval_seconds = interval_seconds
        self.batch_size = batch_size
        self.max_results = max_results
        self.socketio = socketio
        self.scheduler = None
        self.is_running = False
        
    def _get_unchecked_raw_players(self, db: Session, limit: int) -> List[RawPlayer]:
        """
        Get raw_players that haven't been enriched yet.
        
        A raw_player is considered "unchecked" if it doesn't have an identity_match.
        
        Args:
            db: Database session
            limit: Maximum number of players to return
            
        Returns:
            List of RawPlayer objects
        """
        try:
            # Find raw_players without identity_match
            unchecked = db.query(RawPlayer).outerjoin(
                IdentityMatch, RawPlayer.id == IdentityMatch.raw_player_id
            ).filter(
                IdentityMatch.id.is_(None)
            ).order_by(
                RawPlayer.captured_at.asc()  # Process oldest first
            ).limit(limit).all()
            
            return unchecked
        except Exception as e:
            if "does not exist" in str(e) or "UndefinedTable" in str(e):
                log.warning("Database tables not found. Please run migrations first: alembic upgrade head")
                return []
            raise
    
    def _enrich_raw_player(self, raw_player_id: UUID) -> bool:
        """
        Enrich a single raw_player with social media data.
        
        Args:
            raw_player_id: UUID of RawPlayer to enrich
            
        Returns:
            True if enrichment was successful, False otherwise
        """
        try:
            # Get raw_player and extract data
            with db_session() as session:
                raw_player = session.query(RawPlayer).filter(
                    RawPlayer.id == raw_player_id
                ).first()
                
                if not raw_player:
                    log.warning(f"RawPlayer {raw_player_id} not found in database")
                    return False
                
                # Check if already enriched
                if raw_player.identity_match:
                    return True
                
                # Extract data while session is active
                username = raw_player.username
                site = raw_player.site
            
            # Run enrichment outside of session (this can take time)
            result = enrich_username(
                username=username,
                source_site=site,
                max_results=self.max_results
            )
            
            # Build socials dictionary from enrichment result
            found_platforms = {c.platform.lower(): c for c in result.candidates}
            socials = {
                'telegram_url': found_platforms.get('telegram').social_url if 'telegram' in found_platforms else None,
                'instagram_url': found_platforms.get('instagram').social_url if 'instagram' in found_platforms else None,
                'x_url': found_platforms.get('x').social_url if 'x' in found_platforms else None,
                'youtube_url': found_platforms.get('youtube').social_url if 'youtube' in found_platforms else None,
            }
            
            # Create identity match using the service
            with db_session() as session:
                identity_match = create_identity_match(
                    db=session,
                    raw_player_id=raw_player_id,
                    socials=socials
                )
                
                if identity_match:
                    session.commit()
                    log.info(f"✓ {username} ({site}): total_score={identity_match.total_score}")
                    
                    # Emit WebSocket events
                    if self.socketio:
                        try:
                            self.socketio.emit('identity_match_created', {
                                'id': str(identity_match.id),
                                'raw_player_id': str(identity_match.raw_player_id),
                                'username': username,
                                'site': site,
                                'telegram_url': identity_match.telegram_url,
                                'instagram_url': identity_match.instagram_url,
                                'x_url': identity_match.x_url,
                                'youtube_url': identity_match.youtube_url,
                                'total_score': identity_match.total_score,
                                'created_at': identity_match.created_at.isoformat() if identity_match.created_at else None,
                            })
                            
                            # Emit stats update
                            from sqlalchemy import func
                            stats = {
                                'total_raw_players': session.query(RawPlayer).count(),
                                'total_identity_matches': session.query(IdentityMatch).count(),
                                'by_site': {
                                    site: count for site, count in
                                    session.query(RawPlayer.site, func.count(RawPlayer.id).label('count'))
                                    .group_by(RawPlayer.site).all()
                                    if site
                                }
                            }
                            self.socketio.emit('stats_updated', stats)
                        except Exception as e:
                            log.warning(f"Failed to emit WebSocket events: {e}")
                else:
                    session.commit()
                    log.debug(f"No identity match created for {username} ({site}): total_score=0")
                
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
            # Get unchecked raw_players and extract IDs
            with db_session() as session:
                unchecked = self._get_unchecked_raw_players(session, limit=self.batch_size)
                unchecked_ids = [p.id for p in unchecked]
            
            if not unchecked_ids:
                return
            
            # Process each raw_player
            success_count = error_count = 0
            for raw_player_id in unchecked_ids:
                if not self.is_running:
                    break
                
                if self._enrich_raw_player(raw_player_id):
                    success_count += 1
                else:
                    error_count += 1
                
                time.sleep(2)  # Rate limiting
            
            if success_count > 0 or error_count > 0:
                log.info(f"Batch: {success_count} enriched, {error_count} failed")
            
        except Exception as e:
            log.error(f"Error in enrichment batch processing: {e}", exc_info=True)
    
    def start(self):
        """Start the background job scheduler."""
        if self.is_running:
            log.warning("Enrichment job service is already running")
            return
        
        log.info(f"Enrichment job: {self.interval_seconds}s interval, batch_size={self.batch_size}")
        
        # Configure scheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(1)  # Single thread to avoid database conflicts
        }
        job_defaults = {
            'coalesce': True,
            'max_instances': 1,
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
        
        # Run initial batch in a background thread
        initial_thread = threading.Thread(
            target=self._process_batch,
            daemon=True,
            name="InitialEnrichmentBatch"
        )
        initial_thread.start()
    
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
                    enriched_count = session.query(IdentityMatch).count()
                    
                    return {
                        'is_running': self.is_running,
                        'interval_seconds': self.interval_seconds,
                        'batch_size': self.batch_size,
                        'total_raw_players': total_raw_players,
                        'enriched_count': enriched_count,
                        'unchecked_count': total_raw_players - enriched_count,
                    }
                except Exception as db_error:
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
            return {'is_running': self.is_running, 'error': str(e)}
