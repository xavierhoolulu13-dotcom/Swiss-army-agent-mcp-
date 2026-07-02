"""
Image Editor Module — Enhance, upscale, remove bg, stylize
============================================================
HF Spaces used:
  - Background removal: briaai/BRIA-RMBG-2.0
  - Upscale:            gokaygokay/Tile-Upscaler
  - Stylize/enhance:    Uminosachi/realesrgan-stablesr
"""

import os
import tempfile
from pathlib import Path
from gradio_client import Client, handle_file

_BG_REMOVE_SPACE = os.getenv("HF_BGRM_SPACE", "briaai/BRIA-RMBG-2.0")
_UPSCALE_SPACE = os.getenv("HF_UPSCALE_SPACE", "gokaygokay/Tile-Upscaler")
_STYLIZE_SPACE = os.getenv("HF_STYLIZE_SPACE", "Uminosachi/realesrgan-stablesr")


def _write_tmp(image_bytes: bytes, suffix: str = ".png") -> str:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(image_bytes)
        return f.name


def remove_background(image_bytes: bytes, hf_token: str | None = None) -> bytes:
    """
    Remove background from an image.
    Returns PNG bytes with transparent background.
    """
    token = hf_token or os.getenv("HF_TOKEN")
    tmp = _write_tmp(image_bytes)
    try:
        client = Client(_BG_REMOVE_SPACE, hf_token=token)
        result = client.predict(handle_file(tmp), api_name="/image")
        out_path = result if isinstance(result, str) else result[0]
        return Path(out_path).read_bytes()
    finally:
        Path(tmp).unlink(missing_ok=True)


def upscale_image(image_bytes: bytes, scale: int = 4, hf_token: str | None = None) -> bytes:
    """
    Upscale image 2x or 4x using Real-ESRGAN tile upscaler.
    Returns upscaled image bytes.
    """
    token = hf_token or os.getenv("HF_TOKEN")
    tmp = _write_tmp(image_bytes)
    try:
        client = Client(_UPSCALE_SPACE, hf_token=token)
        result = client.predict(
            handle_file(tmp),
            scale,
            api_name="/predict",
        )
        out_path = result if isinstance(result, str) else result[0]
        return Path(out_path).read_bytes()
    finally:
        Path(tmp).unlink(missing_ok=True)


def stylize_image(image_bytes: bytes, style: str = "enhance", hf_token: str | None = None) -> bytes:
    """
    Stylize / enhance image quality.
    style options: 'enhance', 'anime', 'photo'
    """
    token = hf_token or os.getenv("HF_TOKEN")
    tmp = _write_tmp(image_bytes)
    try:
        client = Client(_STYLIZE_SPACE, hf_token=token)
        result = client.predict(handle_file(tmp), style, api_name="/predict")
        out_path = result if isinstance(result, str) else result[0]
        return Path(out_path).read_bytes()
    finally:
        Path(tmp).unlink(missing_ok=True)
