"""Site registry for managing automation workers."""
import logging
from typing import Dict, Optional, List

log = logging.getLogger(__name__)

# Registry of valid site keys (browsers are managed by Puppeteer service)
VALID_SITES = [
    'shuffle',
    'winna',
    'gamdom',
    'thrill',
    'roobet',
    'stake',
    'stake_us',
    'rollbit',
    'bcgame',
    'duelbits',
    'packdraw',
    'metawin',
    'metawin_us',
    'razed',
]


class SiteRegistry:
    """Registry for site keys and metadata."""
    
    def __init__(self):
        self._sites = set(VALID_SITES)
        self._metadata: Dict[str, Dict] = {}
    
    def register_site(
        self,
        site_key: str,
        metadata: Optional[Dict] = None
    ):
        """Register a site key."""
        self._sites.add(site_key)
        if metadata:
            self._metadata[site_key] = metadata
        log.debug(f"Registered site: {site_key}")
    
    def list_sites(self) -> List[str]:
        """List all registered site keys."""
        return sorted(list(self._sites))
    
    def is_valid_site(self, site_key: str) -> bool:
        """Check if a site key is valid."""
        return site_key in self._sites
    
    def get_metadata(self, site_key: str) -> Dict:
        """Get metadata for a site."""
        return self._metadata.get(site_key, {})
