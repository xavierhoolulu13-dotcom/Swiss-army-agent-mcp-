"""
Video Generation Module — Wan2.2 Fast Preview
===============================================
HF Space: Wan-AI/Wan2.2-T2V-14B-Fast (text-to-video, fast preview)
Generates short clips, ads, intros from a text prompt.
"""

import os
import tempfile
from pathlib import Path
from gradio_client import Client

_VIDEO_SPACE = os.getenv("HF_VIDEO_SPACE", "Wan-AI/Wan2.2-T2V-14B-Fast")

# Tier-based duration caps (seconds)
DURATION_CAP = {
    "free": 3,
    "paid": 8,
    "pro": 20,
    "owner": 20,
}


def generate_video(
    prompt: str,
    negative_prompt: str = "blurry, low quality, watermark",
    duration_seconds: int = 4,
    tier: str = "free",
    hf_token: str | None = None,
) -> bytes:
    """
    Generate a short video clip from a text prompt.

    Args:
        prompt:          What to generate, e.g. "neon city 808 intro loop".
        negative_prompt: What to avoid.
        duration_seconds: Length of clip (capped by tier).
        tier:            User tier string to enforce duration cap.
        hf_token:        Optional HF token.

    Returns:
        MP4 video bytes.
    """
    token = hf_token or os.getenv("HF_TOKEN")

    cap = DURATION_CAP.get(tier, DURATION_CAP["free"])
    duration_seconds = min(duration_seconds, cap)

    client = Client(_VIDEO_SPACE, hf_token=token)
    result = client.predict(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_frames=int(duration_seconds * 8),  # 8 fps preview
        api_name="/generate",
    )

    video_path = result if isinstance(result, str) else result[0]
    return Path(video_path).read_bytes()
