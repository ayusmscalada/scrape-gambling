#!/usr/bin/env python3
"""
Background job service for enriching raw_players with social media data.

Usage:
    python run_enrichment_job.py [--interval <seconds>] [--batch-size <number>] [--max-results <number>]

Example:
    python run_enrichment_job.py --interval 60 --batch-size 10
"""

import argparse
import logging
import signal
import sys
import time
from pathlib import Path

from app.jobs.enrichment_job import EnrichmentJobService
from app.config import settings
from scan_socials import wait_for_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)


def main():
    """Main entry point for enrichment job service."""
    parser = argparse.ArgumentParser(
        description="Background job service for enriching raw_players",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_enrichment_job.py
  python run_enrichment_job.py --interval 120 --batch-size 5
  python run_enrichment_job.py --interval 60 --batch-size 10 --max-results 20
        """
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Interval between enrichment batches in seconds (default: 60)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of raw_players to process per batch (default: 10)'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=20,
        help='Maximum candidates to discover per username (default: 20)'
    )
    parser.add_argument(
        '--wait-db',
        action='store_true',
        help='Wait for PostgreSQL to be ready before starting'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Wait for database if requested
    if args.wait_db:
        log.info("Waiting for PostgreSQL to be ready...")
        wait_for_db()
    
    # Create and start job service
    job_service = EnrichmentJobService(
        interval_seconds=args.interval,
        batch_size=args.batch_size,
        max_results=args.max_results
    )
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        log.info("\nReceived shutdown signal, stopping job service...")
        job_service.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the service
    try:
        log.info("=" * 60)
        log.info("  Social Enrichment Background Job Service")
        log.info("=" * 60)
        log.info(f"  Interval: {args.interval} seconds")
        log.info(f"  Batch size: {args.batch_size}")
        log.info(f"  Max results per username: {args.max_results}")
        log.info("=" * 60)
        
        job_service.start()
        
        # Keep the process alive
        log.info("Job service is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            # Print stats periodically
            stats = job_service.get_stats()
            if stats.get('unchecked_count', 0) > 0:
                log.info(f"Stats: {stats.get('enriched_count', 0)} enriched, {stats.get('unchecked_count', 0)} unchecked")
    
    except KeyboardInterrupt:
        log.info("Interrupted by user")
        job_service.stop()
        sys.exit(0)
    except Exception as e:
        log.error(f"Error: {e}", exc_info=True)
        job_service.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
