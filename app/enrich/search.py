"""
Public discovery layer for finding candidate profiles.
"""

import logging
import time
from typing import List, Optional
from urllib.parse import quote

from app.enrich.schemas import Candidate

log = logging.getLogger(__name__)


def discover_candidates(queries: List[str], max_results: int = 20) -> List[Candidate]:
    """
    Search for publicly visible identity bridges.
    
    Checks 4 platforms: Telegram, Instagram, X (Twitter), YouTube.
    
    Args:
        queries: List of search query strings
        max_results: Maximum number of candidates to return
        
    Returns:
        List of Candidate objects
    """
    candidates: List[Candidate] = []
    seen_urls = set()
    
    # Extract unique usernames from queries (remove quotes and platform terms)
    usernames = _extract_usernames_from_queries(queries)
    
    log.info(f"Discovering candidates for {len(usernames)} username variants...")
    
    for username in usernames[:10]:  # Limit to avoid too many requests
        if len(candidates) >= max_results:
            break
        
        # Check only 4 platforms: Telegram, Instagram, X, YouTube
        platform_checkers = [
            _check_telegram,
            _check_instagram,
            _check_x,
            _check_youtube,
        ]
        
        for checker in platform_checkers:
            try:
                candidate = checker(username)
                if candidate and candidate.social_url not in seen_urls:
                    seen_urls.add(candidate.social_url)
                    candidates.append(candidate)
                    log.debug(f"Found candidate: {candidate.platform} @ {candidate.social_handle}")
                    time.sleep(0.5)  # Rate limiting
            except Exception as e:
                log.debug(f"Error checking {checker.__name__} for {username}: {e}")
    
    log.info(f"Discovered {len(candidates)} candidate profiles")
    return candidates[:max_results]


def _extract_usernames_from_queries(queries: List[str]) -> List[str]:
    """Extract unique usernames from query list."""
    usernames = set()
    for q in queries:
        # Remove quotes and platform terms
        cleaned = q.replace('"', '').strip()
        # Remove common platform keywords
        for keyword in ["gambling", "casino", "betting", "Stake", "Roobet", 
                       "Rollbit", "Duelbits", "BcGame", "Metawin", "Razed"]:
            cleaned = cleaned.replace(keyword, '').strip()
        if cleaned and len(cleaned) >= 2:
            usernames.add(cleaned)
    return sorted(list(usernames))


def _check_x(username: str) -> Optional[Candidate]:
    """Check X (Twitter) for username."""
    try:
        import requests
        url = f"https://x.com/{username}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        r = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        if r.status_code == 200:
            return Candidate(
                platform="x",
                social_handle=username,
                social_url=url,
            )
    except Exception:
        pass
    return None


def _check_telegram(username: str) -> Optional[Candidate]:
    """Check Telegram for username."""
    try:
        import requests
        url = f"https://t.me/{username}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        r = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
        if r.status_code == 200 and "tgme_page_title" in r.text:
            return Candidate(
                platform="telegram",
                social_handle=username,
                social_url=url,
            )
    except Exception:
        pass
    return None


def _check_instagram(username: str) -> Optional[Candidate]:
    """Check Instagram for username."""
    try:
        import requests
        url = f"https://www.instagram.com/{username}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        r = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
        if r.status_code == 200 and "Page Not Found" not in r.text[:1000]:
            return Candidate(
                platform="instagram",
                social_handle=username,
                social_url=url,
            )
    except Exception:
        pass
    return None


def _check_youtube(username: str) -> Optional[Candidate]:
    """Check YouTube for username (channel handle)."""
    try:
        import requests
        url = f"https://www.youtube.com/@{username}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        r = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
        if r.status_code == 200 and "channelId" in r.text:
            return Candidate(
                platform="youtube",
                social_handle=username,
                social_url=url,
            )
    except Exception:
        pass
    return None


