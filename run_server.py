#!/usr/bin/env python3
"""
Console server for managing gambling platform automation workers.

Usage:
    python run_server.py

Commands:
    help                    - Show help
    status                  - Show worker status
    list                    - List all sites
    start <site>            - Start a worker
    start all               - Start all enabled workers
    stop <site>             - Stop a worker
    stop all                - Stop all workers
    restart <site>           - Restart a worker
    enable <site>            - Enable a site
    disable <site>           - Disable a site
    exit / quit              - Shutdown and exit
"""
import asyncio
import logging
import os
import signal
import sys
import threading
from pathlib import Path
from queue import Queue

import yaml

from app.manager.registry import SiteRegistry
from app.manager.server import AutomationManager
from app.manager.commands import CommandHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)


def load_site_configs(config_path: Path) -> dict:
    """Load site configurations from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return {site['key']: site for site in config.get('sites', {}).values()}
    except Exception as e:
        log.error(f"Failed to load config from {config_path}: {e}")
        return {}


async def run_console_server():
    """Run the console server loop."""
    # Load configuration
    config_path = Path(__file__).parent / 'config' / 'sites.yaml'
    site_configs = load_site_configs(config_path)
    
    if not site_configs:
        log.error("No site configurations loaded. Exiting.")
        return
    
    log.info(f"Loaded {len(site_configs)} site configurations")
    
    # Initialize registry and manager
    registry = SiteRegistry()
    
    # Get Puppeteer service URL from environment
    puppeteer_url = os.environ.get('PUPPETEER_SERVICE_URL', 'http://puppeteer-service:3000')
    log.info(f"Connecting to Puppeteer service at: {puppeteer_url}")
    
    manager = AutomationManager(registry, site_configs, puppeteer_url=puppeteer_url)
    command_handler = CommandHandler(manager)
    
    # Wait for Puppeteer service to be ready
    try:
        log.info("Waiting for Puppeteer service...")
        is_available = await manager.wait_for_puppeteer_service(max_retries=30, delay=1.0)
        if not is_available:
            log.warning("Puppeteer service is not available. Workers may not start.")
        else:
            log.info("Puppeteer service is ready!")
    except Exception as e:
        log.warning(f"Could not connect to Puppeteer service: {e}")
    
    # Setup signal handlers for graceful shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler(sig, frame):
        log.info("\nReceived shutdown signal")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Print welcome message
    print("\n" + "=" * 60)
    print("  Automation Worker Console Server")
    print("=" * 60)
    print(f"  Loaded {len(site_configs)} sites")
    print(f"  Type 'help' for available commands")
    print("=" * 60 + "\n")
    
    # Command queue for thread-safe input
    command_queue = Queue()
    
    def input_thread():
        """Thread for reading user input."""
        try:
            while not shutdown_event.is_set():
                try:
                    command = input("automation> ")
                    command_queue.put(command)
                except (EOFError, KeyboardInterrupt):
                    command_queue.put(None)
                    break
        except Exception:
            pass
    
    # Start input thread
    input_thread_obj = threading.Thread(target=input_thread, daemon=True)
    input_thread_obj.start()
    
    # Main console loop
    try:
        while not shutdown_event.is_set():
            try:
                # Wait for command with timeout
                try:
                    command = command_queue.get(timeout=0.5)
                except:
                    # Timeout - check shutdown
                    if shutdown_event.is_set():
                        break
                    continue
                
                if command is None:
                    # EOF/Ctrl+C
                    break
                
                if command.strip():
                    should_exit, response = await command_handler.handle_command(command)
                    if response:
                        print(response)
                    
                    if should_exit:
                        break
                        
            except Exception as e:
                log.error(f"Error processing command: {e}", exc_info=True)
    
    finally:
        # Graceful shutdown
        print("\nShutting down all workers...")
        await manager.shutdown()
        print("Goodbye!\n")


def main():
    """Main entry point."""
    try:
        asyncio.run(run_console_server())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        log.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
