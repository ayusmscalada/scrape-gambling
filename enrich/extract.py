"""
Evidence extraction from candidate profiles.
"""

import re
import logging
from typing import List, Optional

from enrich.models import Candidate, Evidence

log = logging.getLogger(__name__)

# Platform keywords to look for
GAMBLING_PLATFORMS = [
    "stake", "roobet", "rollbit", "duelbits", "bcgame", "metawin", "razed",
    "shguffle", "winna", "gamgom", "thrill", "packdraw",
    "gambling", "casino", "betting", "crypto casino", "crypto gambling"
]

# Contact pattern regexes
TELEGRAM_PATTERN = re.compile(r'(?:telegram|tg)[\s:]*@?([a-z0-9_]{5,32})', re.I)
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
DISCORD_PATTERN = re.compile(r'(?:discord|dc)[\s:]*([a-z0-9_]{2,32}#\d{4})', re.I)
WEBSITE_PATTERN = re.compile(r'https?://(?:www\.)?([a-z0-9.-]+\.[a-z]{2,})', re.I)


def extract_candidate_evidence(
    candidate: Candidate,
    source_username: str,
    variants: List[str]
) -> Evidence:
    """
    Extract evidence from a candidate profile.
    
    Args:
        candidate: The candidate profile to analyze
        source_username: Original username being searched
        variants: Generated username variants
        
    Returns:
        Evidence object with extracted information
    """
    evidence = Evidence(
        platform=candidate.platform,
        social_handle=candidate.social_handle,
        social_url=candidate.social_url,
        display_name=candidate.display_name,
        avatar_url=candidate.avatar_url,
        bio_text=candidate.bio_text,
    )
    
    # Fetch full profile data if not already present
    if not candidate.bio_text and candidate.social_url:
        _fetch_profile_data(candidate)
        evidence.bio_text = candidate.bio_text
        evidence.avatar_url = candidate.avatar_url
        evidence.display_name = candidate.display_name
    
    # Extract platform mentions
    if evidence.bio_text:
        bio_lower = evidence.bio_text.lower()
        for platform in GAMBLING_PLATFORMS:
            if platform in bio_lower:
                evidence.platform_mentions.append(platform.title())
    
    # Extract referral codes / creator codes
    if evidence.bio_text:
        # Look for patterns like "code: ABC123", "ref: XYZ", "creator: ..."
        ref_patterns = [
            r'(?:code|ref|referral|creator)[\s:]+([A-Z0-9]{3,20})',
            r'([A-Z0-9]{3,20})[\s]*(?:code|ref)',
        ]
        for pattern in ref_patterns:
            matches = re.findall(pattern, evidence.bio_text, re.I)
            evidence.referral_codes.extend(matches)
    
    # Extract wallet mentions
    if evidence.bio_text:
        wallet_patterns = [
            r'(?:wallet|address)[\s:]+([a-z0-9]{20,})',
            r'0x[a-f0-9]{40}',  # Ethereum address
            r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}',  # Bitcoin address
        ]
        for pattern in wallet_patterns:
            matches = re.findall(pattern, evidence.bio_text, re.I)
            evidence.wallet_mentions.extend(matches)
    
    # Extract public contact information
    if evidence.bio_text:
        # Telegram
        tg_match = TELEGRAM_PATTERN.search(evidence.bio_text)
        if tg_match:
            evidence.public_contact_type = "telegram"
            evidence.public_contact_value = f"@{tg_match.group(1)}"
        
        # Email
        if not evidence.public_contact_type:
            email_match = EMAIL_PATTERN.search(evidence.bio_text)
            if email_match:
                evidence.public_contact_type = "email"
                evidence.public_contact_value = email_match.group(0)
        
        # Discord
        if not evidence.public_contact_type:
            dc_match = DISCORD_PATTERN.search(evidence.bio_text)
            if dc_match:
                evidence.public_contact_type = "discord"
                evidence.public_contact_value = dc_match.group(1)
        
        # Website
        if not evidence.public_contact_type:
            website_match = WEBSITE_PATTERN.search(evidence.bio_text)
            if website_match:
                evidence.public_contact_type = "website"
                evidence.public_contact_value = website_match.group(0)
    
    # Extract external links
    if candidate.external_links:
        evidence.external_links = candidate.external_links
    
    # Language/region clues (basic heuristics)
    if evidence.bio_text:
        # English indicators
        if re.search(r'\b(?:the|and|or|is|are|was|were)\b', evidence.bio_text, re.I):
            evidence.language_clues.append("English")
        # Spanish indicators
        if re.search(r'\b(?:el|la|los|las|y|o|es|son)\b', evidence.bio_text, re.I):
            evidence.language_clues.append("Spanish")
    
    # Build evidence JSON
    evidence.evidence_json = {
        "bio_text": evidence.bio_text,
        "platform_mentions": evidence.platform_mentions,
        "referral_codes": evidence.referral_codes,
        "wallet_mentions": evidence.wallet_mentions,
        "contact_type": evidence.public_contact_type,
        "contact_value": evidence.public_contact_value,
        "language_clues": evidence.language_clues,
        "region_clues": evidence.region_clues,
        "external_links": evidence.external_links,
    }
    
    return evidence


def _fetch_profile_data(candidate: Candidate):
    """Fetch additional profile data from the candidate URL."""
    try:
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        r = requests.get(candidate.social_url, headers=headers, timeout=10, allow_redirects=True)
        if r.status_code == 200:
            text = r.text.lower()
            
            # Try to extract bio text (platform-specific)
            if candidate.platform == "x":
                # X/Twitter - look for meta description
                desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', r.text)
                if desc_match:
                    candidate.bio_text = desc_match.group(1)
            
            elif candidate.platform == "telegram":
                # Telegram - look for description
                desc_match = re.search(r'<div[^>]*class="tgme_page_description"[^>]*>([^<]+)', r.text)
                if desc_match:
                    candidate.bio_text = desc_match.group(1).strip()
            
            elif candidate.platform == "instagram":
                # Instagram - look for meta description
                desc_match = re.search(r'<meta\s+property="og:description"\s+content="([^"]+)"', r.text)
                if desc_match:
                    candidate.bio_text = desc_match.group(1)
            
            elif candidate.platform == "youtube":
                # YouTube - look for channel description
                desc_match = re.search(r'"channelDescription":"([^"]+)"', r.text)
                if desc_match:
                    candidate.bio_text = desc_match.group(1)
            
            # Extract avatar URL if present
            avatar_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', r.text)
            if avatar_match:
                candidate.avatar_url = avatar_match.group(1)
            
            # Extract display name
            title_match = re.search(r'<title>([^<]+)</title>', r.text)
            if title_match:
                candidate.display_name = title_match.group(1).strip()
    
    except Exception as e:
        log.debug(f"Error fetching profile data for {candidate.social_url}: {e}")
