"""
Player data model — represents a scraped lead from any gambling platform.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict
from datetime import datetime


@dataclass
class Player:
    """
    Holds all scraped and enriched data for a single gambling player.

    Fields
    ------
    username      : raw username as seen on the platform
    platform      : source platform name  (e.g. "Stake")
    source        : where on the platform  (live_bet | chat | pack_opening)
    timestamp     : when the record was captured (ISO-8601 string)

    Social links (populated by scan_socials.py):
    telegram / instagram / twitter / youtube

    metadata      : any extra platform-specific fields (bet amount, game, etc.)
    """

    username: str
    platform: str
    source: str                          # "live_bet" | "chat" | "pack_opening"
    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    # ── social enrichment ────────────────────────────────────────────────────
    telegram:  Optional[str] = None
    instagram: Optional[str] = None
    twitter:   Optional[str] = None
    youtube:   Optional[str] = None

    # ── extra context ────────────────────────────────────────────────────────
    metadata: Dict = field(default_factory=dict)

    # ── helpers ──────────────────────────────────────────────────────────────
    def to_dict(self) -> Dict:
        return asdict(self)

    def has_socials(self) -> bool:
        return any([self.telegram, self.instagram, self.twitter, self.youtube])

    def __repr__(self) -> str:
        socials = "✓" if self.has_socials() else "✗"
        return (
            f"<Player {self.username!r} @ {self.platform} "
            f"via {self.source} socials={socials}>"
        )
