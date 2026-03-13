"""Console server for managing automation workers."""
import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime

from app.manager.registry import SiteRegistry
from app.manager.puppeteer_client import PuppeteerClient

log = logging.getLogger(__name__)


class AutomationManager:
    """Manages multiple automation workers via Puppeteer service."""
    
    def __init__(self, registry: SiteRegistry, site_configs: Dict, puppeteer_url: str = "http://puppeteer-service:3000"):
        self.registry = registry
        self.site_configs = site_configs
        self.puppeteer_client = PuppeteerClient(puppeteer_url)
        self.workers: Dict[str, Dict] = {}  # Track worker state
        self._shutdown_event = asyncio.Event()
    
    async def _check_puppeteer_service(self) -> bool:
        """Check if Puppeteer service is available."""
        return await self.puppeteer_client.health_check()
    
    async def wait_for_puppeteer_service(self, max_retries: int = 30, delay: float = 1.0) -> bool:
        """Wait for Puppeteer service to become available."""
        return await self.puppeteer_client.wait_for_service(max_retries, delay)
    
    def list_workers(self) -> List[str]:
        """List all site keys."""
        return self.registry.list_sites()
    
    async def list_running_workers(self) -> List[str]:
        """List site keys of currently running workers."""
        try:
            status = await self.puppeteer_client.get_status()
            if status.get('success'):
                workers = status.get('workers', {})
                return [key for key, info in workers.items() if info.get('state') == 'running']
            return []
        except Exception as e:
            log.error(f"Failed to get running workers: {e}")
            return []
    
    async def start_worker(self, site_key: str) -> bool:
        """
        Start a worker for a site via Puppeteer service.
        
        Args:
            site_key: Site identifier
            
        Returns:
            True if started successfully, False otherwise
        """
        if not self.registry.is_valid_site(site_key):
            log.error(f"Invalid site key: {site_key}")
            return False
        
        # Check if Puppeteer service is available (with retry)
        try:
            if not await self._check_puppeteer_service():
                log.error("Puppeteer service is not available. Is the service running?")
                log.error(f"Service URL: {self.puppeteer_client.base_url}")
                return False
        except Exception as e:
            log.error(f"Failed to connect to Puppeteer service: {e}")
            log.error(f"Service URL: {self.puppeteer_client.base_url}")
            log.error("Make sure the puppeteer-service container is running: docker compose ps")
            return False
        
        # Get site config
        config = self.site_configs.get(site_key, {})
        if not config.get('enabled', True):
            log.warning(f"Site {site_key} is disabled in config")
            return False
        
        # Prepare config for Puppeteer service
        puppeteer_config = {
            'headless': config.get('headless', False),
            'url': config.get('url'),
            'profile_dir': config.get('profile_dir', f'./profiles/{site_key}'),
            'viewport_width': config.get('viewport_width', 1440),
            'viewport_height': config.get('viewport_height', 900),
            'timeout_seconds': config.get('timeout_seconds', 30),
        }
        
        # Call Puppeteer service
        result = await self.puppeteer_client.start_worker(site_key, puppeteer_config)
        
        if result.get('success'):
            self.workers[site_key] = {
                'state': 'running',
                'started_at': datetime.now(),
            }
            log.info(f"Started worker for {site_key}")
            return True
        else:
            error = result.get('error', 'Unknown error')
            log.error(f"Failed to start worker for {site_key}: {error}")
            return False
    
    async def stop_worker(self, site_key: str) -> bool:
        """
        Stop a worker for a site via Puppeteer service.
        
        Args:
            site_key: Site identifier
            
        Returns:
            True if stopped successfully, False otherwise
        """
        # Call Puppeteer service
        result = await self.puppeteer_client.stop_worker(site_key)
        
        if result.get('success'):
            if site_key in self.workers:
                self.workers[site_key]['state'] = 'stopped'
            log.info(f"Stopped worker for {site_key}")
            return True
        else:
            error = result.get('error', 'Unknown error')
            log.error(f"Failed to stop worker for {site_key}: {error}")
            return False
    
    async def restart_worker(self, site_key: str) -> bool:
        """
        Restart a worker for a site via Puppeteer service.
        
        Args:
            site_key: Site identifier
            
        Returns:
            True if restarted successfully, False otherwise
        """
        log.info(f"Restarting worker for {site_key}")
        
        # Get site config
        config = self.site_configs.get(site_key, {})
        puppeteer_config = {
            'headless': config.get('headless', False),
            'url': config.get('url'),
            'profile_dir': config.get('profile_dir', f'./profiles/{site_key}'),
            'viewport_width': config.get('viewport_width', 1440),
            'viewport_height': config.get('viewport_height', 900),
            'timeout_seconds': config.get('timeout_seconds', 30),
        }
        
        # Call Puppeteer service
        result = await self.puppeteer_client.restart_worker(site_key, puppeteer_config)
        
        if result.get('success'):
            self.workers[site_key] = {
                'state': 'running',
                'started_at': datetime.now(),
            }
            log.info(f"Restarted worker for {site_key}")
            return True
        else:
            error = result.get('error', 'Unknown error')
            log.error(f"Failed to restart worker for {site_key}: {error}")
            return False
    
    async def start_all(self) -> Dict[str, bool]:
        """
        Start all enabled workers.
        
        Returns:
            Dictionary mapping site_key to success status
        """
        results = {}
        enabled_sites = [
            key for key, config in self.site_configs.items()
            if config.get('enabled', True) and self.registry.is_valid_site(key)
        ]
        
        log.info(f"Starting {len(enabled_sites)} enabled workers...")
        
        for site_key in enabled_sites:
            results[site_key] = await self.start_worker(site_key)
            await asyncio.sleep(0.5)  # Stagger starts
        
        return results
    
    async def stop_all(self) -> Dict[str, bool]:
        """
        Stop all running workers via Puppeteer service.
        
        Returns:
            Dictionary mapping site_key to success status
        """
        log.info("Stopping all running workers...")
        
        # Call Puppeteer service
        result = await self.puppeteer_client.stop_all()
        
        if result.get('success'):
            results = result.get('results', {})
            # Update local worker state
            for site_key in results.keys():
                if site_key in self.workers:
                    self.workers[site_key]['state'] = 'stopped'
            return {key: info.get('success', False) for key, info in results.items()}
        else:
            log.error("Failed to stop all workers")
            return {}
    
    async def get_status(self) -> Dict[str, Dict]:
        """
        Get status of all workers from Puppeteer service.
        
        Returns:
            Dictionary mapping site_key to health status
        """
        try:
            # Get status from Puppeteer service
            response = await self.puppeteer_client.get_status()
            
            if response.get('success'):
                puppeteer_workers = response.get('workers', {})
                status = {}
                
                # Merge Puppeteer status with config info
                for site_key, config in self.site_configs.items():
                    puppeteer_info = puppeteer_workers.get(site_key, {})
                    state = puppeteer_info.get('state', 'idle')
                    
                    status[site_key] = {
                        'site_key': site_key,
                        'state': state,
                        'is_running': state == 'running',
                        'enabled': config.get('enabled', True),
                        'headless': puppeteer_info.get('headless', config.get('headless', False)),
                        'profile_dir': puppeteer_info.get('profile_dir', config.get('profile_dir', f'./profiles/{site_key}')),
                        'target_url': puppeteer_info.get('target_url', config.get('url', '')),
                    }
                
                return status
            else:
                log.error("Failed to get status from Puppeteer service")
                # Return basic status from configs
                return {
                    site_key: {
                        'site_key': site_key,
                        'state': 'unknown',
                        'is_running': False,
                        'enabled': config.get('enabled', True),
                        'headless': config.get('headless', False),
                        'profile_dir': config.get('profile_dir', f'./profiles/{site_key}'),
                        'target_url': config.get('url', ''),
                    }
                    for site_key, config in self.site_configs.items()
                }
        except Exception as e:
            log.error(f"Error getting status: {e}")
            # Return basic status from configs
            return {
                site_key: {
                    'site_key': site_key,
                    'state': 'error',
                    'is_running': False,
                    'enabled': config.get('enabled', True),
                    'headless': config.get('headless', False),
                    'profile_dir': config.get('profile_dir', f'./profiles/{site_key}'),
                    'target_url': config.get('url', ''),
                }
                for site_key, config in self.site_configs.items()
            }
    
    async def shutdown(self):
        """Gracefully shutdown all workers."""
        log.info("Shutting down all workers...")
        self._shutdown_event.set()
        await self.stop_all()
        await self.puppeteer_client.close()
        log.info("Shutdown complete")
