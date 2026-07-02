"""
XKSH808 Ritual Layer
=====================
Signature blocks injected into every response:
  - FloatForge808 neon branding
  - QR onboarding block
  - Notion ritual block
  - Telegram trigger
  - ScanBiz transfer protocol
  - Perplexity link
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import Optional
from mcp_server.auth.tiers import Tier


BRAND = "🌋 XKSH808"
TAGLINE = "FloatForge808 · Volcano IS · SpiffyCloud OS"
NEON_COLORS = {"primary": "#FF00FF", "accent": "#00FFFF", "bg": "#0a0a0a"}


@dataclass
class RitualBlock:
    brand: str
    tagline: str
    tier: str
    demon_mode: bool
    owner_mode: bool
    qr_url: str
    notion_url: str
    telegram_handle: str
    perplexity_url: str
    scanbiz_protocol: str
    marketcity_url: str
    colors: dict

    def to_dict(self) -> dict:
        return asdict(self)

    def to_markdown(self) -> str:
        dm = "🔥 DEMON MODE ACTIVE" if self.demon_mode else ""
        ow = "👑 OWNER MODE" if self.owner_mode else ""
        badge = dm or ow or f"[{self.tier.upper()}]"
        return (
            f"---\n"
            f"**{self.brand}** — {self.tagline}  {badge}\n"
            f"🔗 [QR Onboarding]({self.qr_url})  "
            f"📓 [Notion Hub]({self.notion_url})  "
            f"📡 [Telegram]({self.telegram_handle})  "
            f"🧠 [Perplexity]({self.perplexity_url})  "
            f"💼 [MarketCity808]({self.marketcity_url})\n"
            f"---"
        )


def build_ritual_block(tier: Tier) -> RitualBlock:
    return RitualBlock(
        brand=BRAND,
        tagline=TAGLINE,
        tier=tier.value,
        demon_mode=tier == Tier.PRO,
        owner_mode=tier == Tier.OWNER,
        qr_url=os.getenv("QR_ONBOARDING_URL", "https://xksh808.com/onboard"),
        notion_url=os.getenv("NOTION_HUB_URL", "https://notion.so/xksh808"),
        telegram_handle=os.getenv("TELEGRAM_HANDLE", "https://t.me/xksh808"),
        perplexity_url="https://perplexity.ai/search?q=XKSH808+FloatForge808",
        scanbiz_protocol=os.getenv("SCANBIZ_URL", "https://xksh808.com/scanbiz"),
        marketcity_url=os.getenv("MARKETCITY_URL", "https://marketcity808.com"),
        colors=NEON_COLORS,
    )


def apply_watermark(content: str, tier: Tier) -> str:
    """Append a watermark for free-tier outputs."""
    if tier == Tier.FREE:
        return content + "\n\n[🌋 Powered by XKSH808 — upgrade at xksh808.com]"
    return content
