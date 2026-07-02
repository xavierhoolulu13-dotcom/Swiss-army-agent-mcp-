"""
Object Detection Module — LocateAnything
=========================================
HF Space: ZhaohuiZhang/LocateAnything
Detects products, people, items from a text prompt + image.
"""

import os
import json
import tempfile
from pathlib import Path
from gradio_client import Client, handle_file

_DETECT_SPACE = os.getenv("HF_DETECT_SPACE", "ZhaohuiZhang/LocateAnything")


def detect_objects(
    image_bytes: bytes,
    prompt: str = "all objects",
    hf_token: str | None = None,
) -> dict:
    """
    Detect objects in an image matching the text prompt.

    Args:
        image_bytes: Raw image data.
        prompt:      Natural-language description of what to find,
                     e.g. "red sneakers", "people", "barcodes".
        hf_token:    Optional HF token.

    Returns:
        dict with keys:
          - annotated_image (bytes): image with bounding boxes drawn
          - detections (list[dict]): [{label, confidence, bbox}, ...]
    """
    token = hf_token or os.getenv("HF_TOKEN")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(image_bytes)
        tmp = f.name

    try:
        client = Client(_DETECT_SPACE, hf_token=token)
        result = client.predict(
            handle_file(tmp),
            prompt,
            api_name="/predict",
        )
        # result may be (annotated_image_path, json_detections_str)
        if isinstance(result, (list, tuple)):
            img_path = result[0]
            detections_raw = result[1] if len(result) > 1 else "[]"
        else:
            img_path = result
            detections_raw = "[]"

        detections = json.loads(detections_raw) if isinstance(detections_raw, str) else detections_raw

        return {
            "annotated_image": Path(img_path).read_bytes() if img_path else b"",
            "detections": detections,
        }
    finally:
        Path(tmp).unlink(missing_ok=True)
