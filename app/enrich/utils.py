"""
Utility functions for the enrichment pipeline.
"""

import re
from typing import List, Optional


def clean_username(username: str) -> str:
    """Clean and normalize a username string."""
    if not username:
        return ""
    return username.strip().lower()


def extract_username_from_url(url: str) -> Optional[str]:
    """Extract username from a social media URL."""
    patterns = [
        r'/(?:@|u/|user/|profile/)?([a-z0-9_.-]+)/?$',
        r'/([a-z0-9_.-]+)$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url, re.I)
        if match:
            return match.group(1)
    return None


def is_valid_username(username: str) -> bool:
    """Check if a username is valid (basic validation)."""
    if not username or len(username) < 2:
        return False
    if len(username) > 50:
        return False
    # Allow alphanumeric, dots, underscores, hyphens
    if not re.match(r'^[a-z0-9._-]+$', username, re.I):
        return False
    return True
