#!/usr/bin/env python3
"""
Python API server for receiving user data from node_workers.

Usage:
    python run_server.py

This service:
- Connects to PostgreSQL
- Runs HTTP API server to receive user data from node_workers
- Saves data to PostgreSQL raw_players table
- Runs background enrichment job to process unchecked raw_players
- Runs continuously until stopped (Ctrl+C)
"""

import logging
import os
import signal
import sys
import atexit

from app.api.server import create_app
from app.jobs.enrichment_job import EnrichmentJobService
from scan_socials import wait_for_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

# Global reference to enrichment job service
enrichment_job = None


def main():
    """Main entry point."""
    global enrichment_job
    
    # Wait for PostgreSQL to be ready
    log.info("Waiting for PostgreSQL to be ready...")
    try:
        wait_for_db(max_retries=30, delay=1.0)
        log.info("PostgreSQL is ready!")
    except Exception as e:
        log.error(f"Failed to connect to PostgreSQL: {e}")
        log.error("Please ensure PostgreSQL is running and accessible")
        sys.exit(1)
    
    # Initialize Flask API server with WebSocket support first (needed for enrichment job)
    api_port = int(os.environ.get('API_PORT', '5000'))
    flask_app, socketio = create_app()
    
    # Initialize enrichment job service (pass socketio for WebSocket events)
    enrichment_interval = int(os.environ.get('ENRICHMENT_INTERVAL_SECONDS', '60'))
    enrichment_batch_size = int(os.environ.get('ENRICHMENT_BATCH_SIZE', '10'))
    enrichment_max_results = int(os.environ.get('ENRICHMENT_MAX_RESULTS', '20'))
    
    enrichment_job = EnrichmentJobService(
        interval_seconds=enrichment_interval,
        batch_size=enrichment_batch_size,
        max_results=enrichment_max_results,
        socketio=socketio
    )
    
    # Start enrichment job service
    try:
        enrichment_job.start()
        log.info("Enrichment job service started")
    except Exception as e:
        log.error(f"Failed to start enrichment job service: {e}")
        log.error("Continuing without enrichment job...")
        enrichment_job = None
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        log.info("\nReceived shutdown signal, stopping server...")
        
        # Stop enrichment job service
        if enrichment_job:
            log.info("Stopping enrichment job service...")
            enrichment_job.stop()
        
        log.info("Server stopped. Goodbye!")
        sys.exit(0)
    
    # Register cleanup function
    def cleanup():
        if enrichment_job:
            enrichment_job.stop()
    
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start Flask API server with WebSocket support
    log.info("=" * 60)
    log.info("  Python API Server with WebSocket + Enrichment Job")
    log.info("=" * 60)
    log.info(f"  API Port: {api_port}")
    log.info(f"  HTTP Endpoint: http://0.0.0.0:{api_port}/api/raw-players")
    log.info(f"  WebSocket: ws://0.0.0.0:{api_port}")
    log.info(f"  Enrichment Interval: {enrichment_interval}s")
    log.info(f"  Enrichment Batch Size: {enrichment_batch_size}")
    log.info("=" * 60)
    log.info("Starting API server...")
    
    try:
        socketio.run(flask_app, host='0.0.0.0', port=api_port, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        log.error(f"Failed to start API server: {e}")
        if enrichment_job:
            enrichment_job.stop()
        sys.exit(1)


if __name__ == '__main__':
    main()
