"""
Username normalization and variant generation.
"""

import re
from typing import List, Set


def normalize_username(username: str) -> List[str]:
    """
    Generate a list of normalized username variants for searching.
    
    Rules:
    - Preserve original
    - Lowercase
    - Trim whitespace
    - Remove numeric suffixes/prefixes where reasonable
    - Replace/remove separators (_, ., -)
    - Collapsed alphanumeric version
    - Shortened versions only if obviously useful
    
    Args:
        username: Raw input username
        
    Returns:
        List of unique variants (original preserved, deduplicated)
    """
    if not username:
        return []
    
    variants: Set[str] = set()
    
    # Original (trimmed)
    original = username.strip()
    if original:
        variants.add(original)
    
    # Lowercase
    lower = original.lower()
    if lower:
        variants.add(lower)
    
    # Remove common separators
    no_sep = re.sub(r'[._-]', '', lower)
    if no_sep and no_sep != lower:
        variants.add(no_sep)
    
    # Remove numeric suffix (e.g., "user123" -> "user")
    no_num_suffix = re.sub(r'\d+$', '', lower)
    if no_num_suffix and no_num_suffix != lower and len(no_num_suffix) >= 3:
        variants.add(no_num_suffix)
    
    # Remove numeric prefix (e.g., "123user" -> "user")
    no_num_prefix = re.sub(r'^\d+', '', lower)
    if no_num_prefix and no_num_prefix != lower and len(no_num_prefix) >= 3:
        variants.add(no_num_prefix)
    
    # Collapsed alphanumeric (remove all non-alphanumeric)
    collapsed = re.sub(r'[^a-z0-9]', '', lower)
    if collapsed and collapsed != lower:
        variants.add(collapsed)
    
    # Shortened version if username is long (>12 chars) and has separators
    if len(lower) > 12 and re.search(r'[._-]', lower):
        parts = re.split(r'[._-]', lower)
        if len(parts) >= 2:
            # Take first part if it's meaningful
            first_part = parts[0]
            if len(first_part) >= 4:
                variants.add(first_part)
    
    # Remove empty strings and return sorted list
    variants = {v for v in variants if v and len(v) >= 2}
    return sorted(list(variants), key=lambda x: (len(x), x))


def build_search_queries(username: str, variants: List[str]) -> List[str]:
    """
    Build search query patterns for public discovery.
    
    Args:
        username: Original username
        variants: Generated username variants
        
    Returns:
        List of search query strings
    """
    queries: Set[str] = set()
    
    # Base queries for original and all variants
    all_usernames = [username] + variants
    
    # Platform-specific query patterns
    platforms = ["gambling", "casino", "betting", "Stake", "Roobet", "Rollbit", 
                 "Duelbits", "BcGame", "Metawin", "Razed"]
    
    for uname in all_usernames:
        if not uname:
            continue
        
        # Exact username
        queries.add(f'"{uname}"')
        queries.add(uname)
        
        # Username + platform
        for platform in platforms:
            queries.add(f'"{uname}" {platform}')
            queries.add(f'{uname} {platform}')
    
    return sorted(list(queries))
