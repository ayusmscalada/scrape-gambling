"""
Public discovery layer for finding candidate profiles.
"""

import logging
import time
from typing import List, Optional
from urllib.parse import quote

from app.enrich.schemas import Candidate

log = logging.getLogger(__name__)


def discover_candidates(usernames: List[str], max_results: int = 20) -> List[Candidate]:
    """
    Search for publicly visible identity bridges.
    
    Checks 4 platforms: Telegram, Instagram, X (Twitter), YouTube.
    
    Args:
        usernames: List of username strings to check (original + variants)
        max_results: Maximum number of candidates to return
        
    Returns:
        List of Candidate objects
    """
    candidates: List[Candidate] = []
    seen_urls = set()
    
    # Remove duplicates and clean usernames
    unique_usernames = []
    seen = set()
    for u in usernames:
        cleaned = u.strip().lower()
        if cleaned and cleaned not in seen and len(cleaned) >= 2:
            seen.add(cleaned)
            unique_usernames.append(cleaned)
    
    log.info(f"Discovering candidates for {len(unique_usernames)} username variants...")
    
    for username in unique_usernames[:10]:  # Limit to avoid too many requests
        if len(candidates) >= max_results:
            break
        
        log.info(f"Checking all platforms for username: {username}")
        
        # Check all 4 platforms: Telegram, Instagram, X, YouTube
        # IMPORTANT: Check ALL platforms, don't stop after first match
        platform_checkers = [
            ('telegram', _check_telegram),
            ('instagram', _check_instagram),
            ('x', _check_x),
            ('youtube', _check_youtube),
        ]
        
        for platform_name, checker in platform_checkers:
            try:
                log.debug(f"Checking {platform_name} for {username}...")
                candidate = checker(username)
                if candidate and candidate.social_url not in seen_urls:
                    seen_urls.add(candidate.social_url)
                    candidates.append(candidate)
                    log.info(f"✓ Found {candidate.platform} match: @{candidate.social_handle} ({candidate.social_url})")
                else:
                    log.debug(f"  No {platform_name} profile found for {username}")
                time.sleep(0.5)  # Rate limiting between platform checks
            except Exception as e:
                log.warning(f"Error checking {platform_name} for {username}: {e}")
                # Continue checking other platforms even if one fails
                continue
    
    log.info(f"Discovered {len(candidates)} candidate profiles")
    return candidates[:max_results]


def _check_x(username: str) -> Optional[Candidate]:
    """Check X (Twitter) for username."""
    try:
        import requests
        url = f"https://x.com/{username}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        # Use GET instead of HEAD as X might block HEAD requests
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        # Check if profile exists (not a 404 or redirect to home)
        if r.status_code == 200:
            # Check if it's not the generic "This page doesn't exist" page
            text_lower = r.text.lower()
            if "this account doesn't exist" not in text_lower and "page doesn't exist" not in text_lower:
                return Candidate(
                    platform="x",
                    social_handle=username,
                    social_url=url,
                )
    except Exception as e:
        log.debug(f"X check error for {username}: {e}")
    return None


def _check_telegram(username: str) -> Optional[Candidate]:
    """Check Telegram for username."""
    try:
        import requests
        url = f"https://t.me/{username}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if r.status_code == 200:
            text_lower = r.text.lower()
            # Check for indicators that profile/channel exists
            if ("tgme_page_title" in r.text or 
                "tgme_page_description" in r.text or
                "tgme_page_extra" in r.text):
                # Make sure it's not an error page
                if "sorry, this page is not available" not in text_lower:
                    return Candidate(
                        platform="telegram",
                        social_handle=username,
                        social_url=url,
                    )
    except Exception as e:
        log.debug(f"Telegram check error for {username}: {e}")
    return None


def _check_instagram(username: str) -> Optional[Candidate]:
    """Check Instagram for username."""
    try:
        import requests
        url = f"https://www.instagram.com/{username}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if r.status_code == 200:
            text_lower = r.text.lower()
            # Check for indicators that profile exists
            # Instagram shows "Page Not Found" or redirects to login for non-existent profiles
            if ("page not found" not in text_lower and 
                "sorry, this page isn't available" not in text_lower and
                "the link you followed may be broken" not in text_lower and
                ("instagram.com/" + username.lower()) in text_lower):
                return Candidate(
                    platform="instagram",
                    social_handle=username,
                    social_url=url,
                )
    except Exception as e:
        log.debug(f"Instagram check error for {username}: {e}")
    return None


def _check_youtube(username: str) -> Optional[Candidate]:
    """Check YouTube for username (channel handle)."""
    try:
        import requests
        # Try both @handle format and /c/ format
        urls_to_try = [
            f"https://www.youtube.com/@{username}",
            f"https://www.youtube.com/c/{username}",
            f"https://www.youtube.com/user/{username}",
        ]
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        for url in urls_to_try:
            try:
                r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
                if r.status_code == 200:
                    text_lower = r.text.lower()
                    # Check for indicators that channel exists
                    if ("channelid" in text_lower or 
                        '"channelId"' in r.text or
                        ("youtube.com/@" + username.lower()) in text_lower or
                        ("youtube.com/c/" + username.lower()) in text_lower):
                        # Make sure it's not an error page
                        if "this channel doesn't exist" not in text_lower:
                            return Candidate(
                                platform="youtube",
                                social_handle=username,
                                social_url=url,
                            )
            except Exception:
                continue
    except Exception as e:
        log.debug(f"YouTube check error for {username}: {e}")
    return None


