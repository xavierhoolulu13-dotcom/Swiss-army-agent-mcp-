"""
HTTP Bridge — exposes MCP tools as REST endpoints
===================================================
Lets Make.com, n8n, Zapier, or any HTTP client call the
same XKSH808 modules without needing an MCP client.

Mount alongside the stripe + make routers.

Routes:
  GET  /health           → uptime check
  POST /run/ocr          → { image_b64, token? } → { text }
  POST /run/image_edit   → { image_b64, operation, ... } → { image_b64 }
  POST /run/detect       → { image_b64, prompt? } → { detections, image_b64 }
  POST /run/video        → { prompt, duration_seconds? } → { video_b64 }
  GET  /ritual           → { ritual_block }
"""

import base64
import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from mcp_server.auth.tiers import resolve_tier, can_access_module, Tier
from mcp_server.ritual.xksh808 import build_ritual_block, apply_watermark
from mcp_server.modules import ocr, image_editor, object_detect, video_gen
from webhooks.stripe_handler import router as stripe_router
from webhooks.make_handler import router as make_router

app = FastAPI(
    title="XKSH808 Ultimate Concierge",
    description="FloatForge808 · Volcano IS · SpiffyCloud OS",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stripe_router)
app.include_router(make_router)

HF_TOKEN = os.getenv("HF_TOKEN")


def _tier(authorization: str | None) -> Tier:
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    return resolve_tier(token or None)


def _gate(tier: Tier, module: str):
    if not can_access_module(tier, module):
        raise HTTPException(
            status_code=403,
            detail=f"Module '{module}' requires a higher tier. Upgrade at https://xksh808.com/upgrade",
        )


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "brand": "🌋 XKSH808 Ultimate Concierge"}


# ── OCR ───────────────────────────────────────────────────────────────────────

class OcrRequest(BaseModel):
    image_b64: str
    filename: str = "input.png"


@app.post("/run/ocr")
def run_ocr(req: OcrRequest, authorization: Optional[str] = Header(None)):
    t = _tier(authorization)
    _gate(t, "ocr")
    img = base64.b64decode(req.image_b64)
    text = ocr.run_ocr(img, req.filename, HF_TOKEN)
    text = apply_watermark(text, t)
    return {"text": text, "tier": t.value, "ritual": build_ritual_block(t).to_dict()}


# ── Image Editor ──────────────────────────────────────────────────────────────

class ImageEditRequest(BaseModel):
    image_b64: str
    operation: str          # remove_background | upscale | stylize
    scale: int = 4
    style: str = "enhance"


@app.post("/run/image_edit")
def run_image_edit(req: ImageEditRequest, authorization: Optional[str] = Header(None)):
    t = _tier(authorization)
    _gate(t, "image_editor")
    img = base64.b64decode(req.image_b64)

    if req.operation == "remove_background":
        result = image_editor.remove_background(img, HF_TOKEN)
    elif req.operation == "upscale":
        result = image_editor.upscale_image(img, req.scale, HF_TOKEN)
    elif req.operation == "stylize":
        result = image_editor.stylize_image(img, req.style, HF_TOKEN)
    else:
        raise HTTPException(400, f"Unknown operation: {req.operation}")

    return {
        "image_b64": base64.b64encode(result).decode(),
        "tier": t.value,
        "ritual": build_ritual_block(t).to_dict(),
    }


# ── Object Detection ──────────────────────────────────────────────────────────

class DetectRequest(BaseModel):
    image_b64: str
    prompt: str = "all objects"


@app.post("/run/detect")
def run_detect(req: DetectRequest, authorization: Optional[str] = Header(None)):
    t = _tier(authorization)
    _gate(t, "object_detect")
    img = base64.b64decode(req.image_b64)
    result = object_detect.detect_objects(img, req.prompt, HF_TOKEN)
    return {
        "detections": result["detections"],
        "annotated_image_b64": base64.b64encode(result["annotated_image"]).decode() if result["annotated_image"] else None,
        "tier": t.value,
        "ritual": build_ritual_block(t).to_dict(),
    }


# ── Video Generation ──────────────────────────────────────────────────────────

class VideoRequest(BaseModel):
    prompt: str
    negative_prompt: str = "blurry, low quality, watermark"
    duration_seconds: int = 4


@app.post("/run/video")
def run_video(req: VideoRequest, authorization: Optional[str] = Header(None)):
    t = _tier(authorization)
    _gate(t, "video_gen")
    mp4 = video_gen.generate_video(req.prompt, req.negative_prompt, req.duration_seconds, t.value, HF_TOKEN)
    return {
        "video_b64": base64.b64encode(mp4).decode(),
        "tier": t.value,
        "ritual": build_ritual_block(t).to_dict(),
    }


# ── Ritual Info ───────────────────────────────────────────────────────────────

@app.get("/ritual")
def ritual_info(authorization: Optional[str] = Header(None)):
    t = _tier(authorization)
    return build_ritual_block(t).to_dict()
