#!/usr/bin/env python3
"""
scan_socials.py — Public social enrichment CLI tool.

Usage:
    python scan_socials.py <username> [--source-site <name>] [--json-out <path>] [--max-results <int>]

Example:
    python scan_socials.py antonyambriz --source-site Stake --json-out result.json
"""

import argparse
import json
import logging
import sys
import time
from typing import Optional, List

from app.enrich.schemas import EnrichmentResult, CandidateMatch
from app.enrich.normalize import normalize_username, build_search_queries
from app.enrich.search import discover_candidates
from app.enrich.extract import extract_candidate_evidence
from app.enrich.score import score_candidate
from app.enrich.classify import classify_candidate, classify_lead
from app.enrich.output import render_console_report, save_json_report, result_to_socials_dict
from app.db.session import db_session
from app.db.repositories import EnrichmentRepository
from app.config import settings

# ── logging setup ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def wait_for_db(max_retries: int = 30, delay: float = 1.0):
    """Wait for PostgreSQL to be ready."""
    from sqlalchemy import create_engine, text
    from app.config import settings
    
    log.info("Waiting for PostgreSQL to be ready...")
    for i in range(max_retries):
        try:
            engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            log.info("PostgreSQL is ready!")
            return True
        except Exception as e:
            if i < max_retries - 1:
                log.debug(f"PostgreSQL not ready yet (attempt {i+1}/{max_retries}): {e}")
                time.sleep(delay)
            else:
                log.error(f"PostgreSQL failed to become ready after {max_retries} attempts")
                raise
    return False


def enrich_username(
    username: str,
    source_site: Optional[str] = None,
    max_results: int = 20
) -> EnrichmentResult:
    """
    Main enrichment workflow.
    
    Args:
        username: Input username
        source_site: Optional source site name
        max_results: Maximum candidates to discover
        
    Returns:
        EnrichmentResult
    """
    log.info(f"Starting enrichment for username: {username}")
    
    # Stage A: Normalization
    log.info("Stage A: Normalizing username and generating variants...")
    variants = normalize_username(username)
    queries = build_search_queries(username, variants)
    log.info(f"Generated {len(variants)} variants, {len(queries)} search queries")
    
    # Stage B: Discovery
    log.info("Stage B: Discovering public candidates...")
    candidates = discover_candidates(queries, max_results=max_results)
    log.info(f"Discovered {len(candidates)} candidate profiles")
    
    # Stage C & D: Extraction and Scoring
    log.info("Stage C & D: Extracting evidence and scoring matches...")
    candidate_matches: List[CandidateMatch] = []
    
    for candidate in candidates:
        try:
            # Extract evidence
            evidence = extract_candidate_evidence(candidate, username, variants)
            
            # Score candidate
            score_result = score_candidate(username, variants, evidence)
            
            # Classify candidate
            confidence_label = classify_candidate(score_result, evidence)
            
            # Build CandidateMatch
            match = CandidateMatch(
                source_username=username,
                platform=candidate.platform,
                social_handle=candidate.social_handle,
                social_url=candidate.social_url,
                display_name=evidence.display_name,
                avatar_url=evidence.avatar_url,
                match_score=score_result.match_score,
                confidence_label=confidence_label,
                scoring_reasons=score_result.scoring_reasons,
                public_contact_type=evidence.public_contact_type,
                public_contact_value=evidence.public_contact_value,
                evidence_json=evidence.evidence_json,
            )
            
            candidate_matches.append(match)
            log.debug(f"Scored {candidate.platform} @{candidate.social_handle}: {score_result.match_score}/100")
        
        except Exception as e:
            log.warning(f"Error processing candidate {candidate.social_url}: {e}")
            continue
    
    # Sort by match score (descending)
    candidate_matches.sort(key=lambda x: x.match_score, reverse=True)
    
    # Stage E: Classification
    log.info("Stage E: Classifying lead...")
    best_match = candidate_matches[0] if candidate_matches else None
    final_classification = classify_lead(best_match)
    
    # Build result
    result = EnrichmentResult(
        input_username=username,
        source_site=source_site,
        variants=variants,
        candidates=candidate_matches,
        best_match=best_match,
        final_classification=final_classification,
    )
    
    log.info(f"Enrichment complete. Classification: {final_classification}")
    return result


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Public social enrichment tool for gambling platform usernames",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scan_socials.py antonyambriz
  python scan_socials.py antonyambriz --source-site Stake --json-out result.json
  python scan_socials.py user123 --max-results 10
        """
    )
    
    parser.add_argument(
        "username",
        help="Username to enrich"
    )
    parser.add_argument(
        "--source-site",
        dest="source_site",
        help="Source site name (e.g., Stake, Rollbit)"
    )
    parser.add_argument(
        "--json-out",
        dest="json_out",
        help="Path to save JSON output"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=20,
        help="Maximum candidates to discover (default: 20)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Skip saving to PostgreSQL database"
    )
    parser.add_argument(
        "--wait-db",
        action="store_true",
        help="Wait for PostgreSQL to be ready (useful in Docker)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_stdout",
        help="Print only a JSON object to stdout (telegram, instagram, twitter, youtube) for use by main.py enricher"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # When --json, logs must go to stderr so stdout is only JSON for SocialEnricher
    if args.json_stdout:
        root = logging.getLogger()
        for h in root.handlers[:]:
            root.removeHandler(h)
        root.addHandler(logging.StreamHandler(sys.stderr))
    
    # Wait for database if requested
    if args.wait_db:
        wait_for_db()
    
    # Run enrichment
    try:
        result = enrich_username(
            username=args.username,
            source_site=args.source_site,
            max_results=args.max_results
        )
        
        # Save to PostgreSQL database
        if not args.no_save:
            try:
                with db_session() as session:
                    raw_player = EnrichmentRepository.save_result(session, result)
                    log.info(f"Saved enrichment result to PostgreSQL (raw_player_id: {raw_player.id})")
            except Exception as e:
                log.error(f"Failed to save to PostgreSQL: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
                # Continue execution even if DB save fails
        
        # Save JSON output
        if args.json_out:
            save_json_report(result, args.json_out)
        
        # Machine-readable JSON to stdout (for main.py SocialEnricher)
        if args.json_stdout:
            print(json.dumps(result_to_socials_dict(result), ensure_ascii=False))
        else:
            # Render console report
            render_console_report(result)
        
        # Exit code based on classification
        if result.final_classification == "no lead":
            sys.exit(1)
        elif result.final_classification == "weak lead":
            sys.exit(2)
        else:  # usable lead
            sys.exit(0)
    
    except KeyboardInterrupt:
        log.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        log.error(f"Error: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()
