"""
HTTP client for Puppeteer browser service.
Python communicates with Node.js Puppeteer service via REST API.
"""
import asyncio
import logging
import httpx
from typing import Dict, Optional, Any

log = logging.getLogger(__name__)


class PuppeteerClient:
    """Client for communicating with Puppeteer service API."""
    
    def __init__(self, base_url: str = "http://puppeteer-service:3000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def wait_for_service(self, max_retries: int = 30, delay: float = 1.0) -> bool:
        """
        Wait for Puppeteer service to become available.
        
        Args:
            max_retries: Maximum number of retry attempts
            delay: Delay between retries in seconds
            
        Returns:
            True if service becomes available, False otherwise
        """
        log.info("Waiting for Puppeteer service to be ready...")
        for i in range(max_retries):
            try:
                if await self.health_check():
                    log.info("Puppeteer service is ready!")
                    return True
            except Exception:
                pass
            
            if i < max_retries - 1:
                log.debug(f"Puppeteer service not ready yet (attempt {i+1}/{max_retries})")
                await asyncio.sleep(delay)
        
        log.error(f"Puppeteer service failed to become ready after {max_retries} attempts")
        return False
    
    async def health_check(self) -> bool:
        """Check if Puppeteer service is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            log.error(f"Puppeteer service health check failed: {e}")
            return False
    
    async def start_worker(self, site_key: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start a browser worker for a site.
        
        Args:
            site_key: Site identifier
            config: Worker configuration (headless, url, profile_dir, etc.)
            
        Returns:
            Response dictionary with success status
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/start/{site_key}",
                json=config
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                body = e.response.json()
                api_error = body.get("error", body)
            except Exception:
                api_error = e.response.text or str(e)
            log.error(f"Failed to start worker {site_key}: {api_error}")
            return {"success": False, "error": str(api_error)}
        except httpx.HTTPError as e:
            log.error(f"Failed to start worker {site_key}: {e}")
            return {"success": False, "error": str(e)}
    
    async def stop_worker(self, site_key: str) -> Dict[str, Any]:
        """
        Stop a browser worker for a site.
        
        Args:
            site_key: Site identifier
            
        Returns:
            Response dictionary with success status
        """
        try:
            response = await self.client.post(f"{self.base_url}/stop/{site_key}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            log.error(f"Failed to stop worker {site_key}: {e}")
            return {"success": False, "error": str(e)}
    
    async def restart_worker(self, site_key: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Restart a browser worker for a site.
        
        Args:
            site_key: Site identifier
            config: Worker configuration
            
        Returns:
            Response dictionary with success status
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/restart/{site_key}",
                json=config
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            log.error(f"Failed to restart worker {site_key}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_status(self, site_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Get worker status.
        
        Args:
            site_key: Optional site identifier. If None, returns all workers.
            
        Returns:
            Status dictionary
        """
        try:
            if site_key:
                response = await self.client.get(f"{self.base_url}/status/{site_key}")
            else:
                response = await self.client.get(f"{self.base_url}/status")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            log.error(f"Failed to get status: {e}")
            return {"success": False, "error": str(e)}
    
    async def stop_all(self) -> Dict[str, Any]:
        """
        Stop all running workers.
        
        Returns:
            Response dictionary with results
        """
        try:
            response = await self.client.post(f"{self.base_url}/stop-all")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            log.error(f"Failed to stop all workers: {e}")
            return {"success": False, "error": str(e)}
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
