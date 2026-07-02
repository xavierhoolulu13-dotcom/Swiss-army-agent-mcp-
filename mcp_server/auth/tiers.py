"""
XKSH808 Tier Authentication
============================
Three tiers: Free, Paid, Pro (Demon Mode)
Owner mode: Xavier's master token — always unlimited.
"""

import os
import hashlib
from enum import Enum
from typing import Optional


class Tier(str, Enum):
    FREE = "free"
    PAID = "paid"
    PRO = "pro"          # Demon Mode
    OWNER = "owner"      # Xavier's master access


# Limits per tier (runs per 24h, 0 = unlimited)
TIER_LIMITS: dict[Tier, int] = {
    Tier.FREE: 5,
    Tier.PAID: 100,
    Tier.PRO: 0,
    Tier.OWNER: 0,
}

TIER_WATERMARK: dict[Tier, bool] = {
    Tier.FREE: True,
    Tier.PAID: False,
    Tier.PRO: False,
    Tier.OWNER: False,
}

TIER_MODULES: dict[Tier, list[str]] = {
    Tier.FREE: ["ocr"],
    Tier.PAID: ["ocr", "image_editor", "object_detect"],
    Tier.PRO: ["ocr", "image_editor", "object_detect", "video_gen", "marketcity808", "secret_lab"],
    Tier.OWNER: ["*"],  # all modules
}


def resolve_tier(token: Optional[str]) -> Tier:
    """
    Resolve a bearer token to a Tier.
    Tokens are stored as env vars: TIER_TOKEN_<hash>.
    The OWNER_TOKEN env var always maps to OWNER tier.
    Falls back to FREE if token is missing or unrecognised.
    """
    if not token:
        return Tier.FREE

    owner_token = os.getenv("OWNER_TOKEN", "")
    if owner_token and token == owner_token:
        return Tier.OWNER

    # Check pro / paid tokens from env (format: PRO_TOKEN_<n>, PAID_TOKEN_<n>)
    for tier in (Tier.PRO, Tier.PAID):
        prefix = f"{tier.value.upper()}_TOKEN"
        idx = 0
        while True:
            env_key = f"{prefix}_{idx}" if idx else prefix
            stored = os.getenv(env_key)
            if stored is None:
                break
            if _constant_compare(token, stored):
                return tier
            idx += 1

    return Tier.FREE


def can_access_module(tier: Tier, module: str) -> bool:
    allowed = TIER_MODULES[tier]
    return "*" in allowed or module in allowed


def get_limit(tier: Tier) -> int:
    return TIER_LIMITS[tier]


def needs_watermark(tier: Tier) -> bool:
    return TIER_WATERMARK[tier]


def _constant_compare(a: str, b: str) -> bool:
    """Timing-safe string comparison."""
    return hashlib.sha256(a.encode()).digest() == hashlib.sha256(b.encode()).digest()
