"""
OCR Module — Unlimited OCR via Hugging Face Space
===================================================
Wraps the `tesseract-ocr` / `paddle-ocr` HF Space.
Primary space: stepfun-ai/GOT-OCR2_0  (general-purpose OCR)
Fallback:      keras-io/ocr-for-captcha (lightweight)
"""

import os
import base64
import tempfile
from pathlib import Path
from gradio_client import Client, handle_file


_PRIMARY_SPACE = os.getenv("HF_OCR_SPACE", "stepfun-ai/GOT-OCR2_0")
_FALLBACK_SPACE = os.getenv("HF_OCR_FALLBACK", "keras-io/ocr-for-captcha")


def run_ocr(image_bytes: bytes, filename: str = "input.png", hf_token: str | None = None) -> str:
    """
    Extract text from an image.

    Args:
        image_bytes: Raw image data (PNG/JPG/PDF page).
        filename:    Suggested filename for the temp file.
        hf_token:    Optional HF token for private/gated spaces.

    Returns:
        Extracted text as a plain string.
    """
    token = hf_token or os.getenv("HF_TOKEN")

    with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix or ".png", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        client = Client(_PRIMARY_SPACE, hf_token=token)
        # GOT-OCR2_0 API: (image, ocr_type) → plain text
        result = client.predict(
            image=handle_file(tmp_path),
            ocr_type="ocr",
            api_name="/run_GOT",
        )
        return str(result)
    except Exception as primary_err:
        # Fallback
        try:
            client = Client(_FALLBACK_SPACE, hf_token=token)
            result = client.predict(handle_file(tmp_path), api_name="/predict")
            return str(result)
        except Exception as fallback_err:
            raise RuntimeError(
                f"OCR failed. Primary: {primary_err} | Fallback: {fallback_err}"
            ) from fallback_err
    finally:
        Path(tmp_path).unlink(missing_ok=True)
