"""
Console and JSON output formatting.
"""

import json
import logging
from typing import Optional

from enrich.models import EnrichmentResult, CandidateMatch

log = logging.getLogger(__name__)


def render_console_report(result: EnrichmentResult) -> None:
    """
    Print a readable CLI summary.
    
    Shows:
    - input username
    - generated username variants
    - candidate matches found
    - confidence score for each candidate
    - evidence summary for each candidate
    - best candidate
    - final classification
    """
    print("\n" + "=" * 70)
    print("  SOCIAL ENRICHMENT REPORT")
    print("=" * 70)
    
    print(f"\n📝 Input Username: {result.input_username}")
    if result.source_site:
        print(f"   Source Site: {result.source_site}")
    
    print(f"\n🔍 Generated Variants ({len(result.variants)}):")
    for variant in result.variants[:10]:  # Show first 10
        print(f"   • {variant}")
    if len(result.variants) > 10:
        print(f"   ... and {len(result.variants) - 10} more")
    
    if not result.candidates:
        print("\n❌ No reliable public identity or contact match found.")
        print("=" * 70 + "\n")
        return
    
    print(f"\n🎯 Candidates Found: {len(result.candidates)}")
    print("-" * 70)
    
    for i, candidate in enumerate(result.candidates, 1):
        print(f"\n{i}. {candidate.platform.upper()} — @{candidate.social_handle}")
        print(f"   URL: {candidate.social_url}")
        print(f"   Match Score: {candidate.match_score}/100")
        print(f"   Confidence: {candidate.confidence_label}")
        
        if candidate.scoring_reasons:
            print(f"   Scoring Reasons:")
            for reason in candidate.scoring_reasons[:5]:  # Top 5 reasons
                print(f"     • {reason}")
        
        if candidate.public_contact_type:
            print(f"   Public Contact: {candidate.public_contact_type} — {candidate.public_contact_value}")
        
        if candidate.evidence_json.get("platform_mentions"):
            platforms = ", ".join(candidate.evidence_json["platform_mentions"][:3])
            print(f"   Platform Mentions: {platforms}")
    
    if result.best_match:
        print("\n" + "-" * 70)
        print("⭐ BEST MATCH")
        print("-" * 70)
        best = result.best_match
        print(f"   Platform: {best.platform.upper()}")
        print(f"   Handle: @{best.social_handle}")
        print(f"   URL: {best.social_url}")
        print(f"   Score: {best.match_score}/100")
        print(f"   Confidence: {best.confidence_label}")
        if best.public_contact_type:
            print(f"   Contact: {best.public_contact_type} — {best.public_contact_value}")
    
    print("\n" + "-" * 70)
    print(f"📊 FINAL CLASSIFICATION: {result.final_classification.upper()}")
    
    if result.final_classification == "no lead":
        print("\n❌ No reliable public identity or contact match found.")
    elif result.final_classification == "weak lead":
        print("\n⚠️  Likely identity match found, but no strong public contact path.")
    elif result.final_classification == "usable lead":
        print("\n✅ Strong identity match with public contact path available.")
    
    print("=" * 70 + "\n")


def save_json_report(result: EnrichmentResult, path: str) -> None:
    """
    Save structured JSON output to file.
    
    Args:
        result: EnrichmentResult to serialize
        path: Output file path
    """
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        log.info(f"JSON report saved to {path}")
    except Exception as e:
        log.error(f"Error saving JSON report: {e}")
        raise
