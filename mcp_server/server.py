"""
XKSH808 Ultimate Concierge — MCP Server
=========================================
Exposes five MCP tools:
  xksh808_ocr            — Extract text from images
  xksh808_image_edit     — Remove bg / upscale / stylize
  xksh808_detect_objects — Object/product detection
  xksh808_generate_video — Text-to-video clip generation
  xksh808_ritual_info    — Returns ritual block + tier info

All tools are gated by bearer-token tier auth.
"""

import base64
import os
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from mcp_server.auth.tiers import Tier, resolve_tier, can_access_module, needs_watermark
from mcp_server.ritual.xksh808 import build_ritual_block, apply_watermark
from mcp_server.modules import ocr, image_editor, object_detect, video_gen

load_dotenv()

app = Server("xksh808-ultimate-concierge")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _decode_image(b64_or_bytes: str) -> bytes:
    """Accept either base64 string or raw bytes string."""
    try:
        return base64.b64decode(b64_or_bytes)
    except Exception:
        return b64_or_bytes.encode() if isinstance(b64_or_bytes, str) else b64_or_bytes


def _get_tier(arguments: dict) -> Tier:
    token = arguments.get("token") or os.getenv("DEFAULT_TOKEN", "")
    return resolve_tier(token)


def _gate(tier: Tier, module: str) -> types.TextContent | None:
    if not can_access_module(tier, module):
        return types.TextContent(
            type="text",
            text=(
                f"🔒 Module '{module}' requires a higher tier. "
                f"Your tier: {tier.value}. Upgrade at https://xksh808.com/upgrade"
            ),
        )
    return None


# ── Tool definitions ──────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="xksh808_ocr",
            description=(
                "Extract text from an image or document using unlimited OCR. "
                "Supports receipts, screenshots, PDFs, business cards."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "image_b64": {
                        "type": "string",
                        "description": "Base64-encoded image data (PNG/JPG/PDF page).",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional filename hint (e.g. 'receipt.png').",
                        "default": "input.png",
                    },
                    "token": {"type": "string", "description": "Bearer token (optional)."},
                },
                "required": ["image_b64"],
            },
        ),
        types.Tool(
            name="xksh808_image_edit",
            description=(
                "Edit an image: remove background, upscale (2x/4x), or stylize/enhance. "
                "Returns base64-encoded result image."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "image_b64": {"type": "string", "description": "Base64-encoded image."},
                    "operation": {
                        "type": "string",
                        "enum": ["remove_background", "upscale", "stylize"],
                        "description": "Which edit operation to perform.",
                    },
                    "scale": {
                        "type": "integer",
                        "enum": [2, 4],
                        "description": "Upscale factor (used only for 'upscale').",
                        "default": 4,
                    },
                    "style": {
                        "type": "string",
                        "enum": ["enhance", "anime", "photo"],
                        "description": "Style for 'stylize' operation.",
                        "default": "enhance",
                    },
                    "token": {"type": "string", "description": "Bearer token (optional)."},
                },
                "required": ["image_b64", "operation"],
            },
        ),
        types.Tool(
            name="xksh808_detect_objects",
            description=(
                "Detect objects, products, or people in an image using LocateAnything. "
                "Returns annotated image + list of detections with bounding boxes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "image_b64": {"type": "string", "description": "Base64-encoded image."},
                    "prompt": {
                        "type": "string",
                        "description": "What to detect, e.g. 'red shoes', 'barcodes', 'people'.",
                        "default": "all objects",
                    },
                    "token": {"type": "string", "description": "Bearer token (optional)."},
                },
                "required": ["image_b64"],
            },
        ),
        types.Tool(
            name="xksh808_generate_video",
            description=(
                "Generate a short video clip from a text prompt using Wan2.2 Fast. "
                "Great for ads, intros, product showcases. Duration capped by tier."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "What to generate, e.g. 'neon 808 city intro loop'.",
                    },
                    "negative_prompt": {
                        "type": "string",
                        "description": "What to avoid.",
                        "default": "blurry, low quality, watermark",
                    },
                    "duration_seconds": {
                        "type": "integer",
                        "description": "Desired clip length in seconds.",
                        "default": 4,
                    },
                    "token": {"type": "string", "description": "Bearer token (optional)."},
                },
                "required": ["prompt"],
            },
        ),
        types.Tool(
            name="xksh808_ritual_info",
            description=(
                "Returns XKSH808 ritual block: tier status, brand links, "
                "QR onboarding URL, Notion hub, Telegram, MarketCity808."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "Bearer token (optional)."},
                },
            },
        ),
    ]


# ── Tool handlers ─────────────────────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
    tier = _get_tier(arguments)
    hf_token = os.getenv("HF_TOKEN")

    # ── OCR ──────────────────────────────────────────────────────────────────
    if name == "xksh808_ocr":
        if blocked := _gate(tier, "ocr"):
            return [blocked]
        image_bytes = _decode_image(arguments["image_b64"])
        filename = arguments.get("filename", "input.png")
        text = ocr.run_ocr(image_bytes, filename, hf_token)
        text = apply_watermark(text, tier)
        ritual = build_ritual_block(tier)
        return [
            types.TextContent(type="text", text=text),
            types.TextContent(type="text", text=ritual.to_markdown()),
        ]

    # ── Image Editor ──────────────────────────────────────────────────────────
    if name == "xksh808_image_edit":
        if blocked := _gate(tier, "image_editor"):
            return [blocked]
        image_bytes = _decode_image(arguments["image_b64"])
        operation = arguments["operation"]
        result_bytes: bytes

        if operation == "remove_background":
            result_bytes = image_editor.remove_background(image_bytes, hf_token)
        elif operation == "upscale":
            scale = int(arguments.get("scale", 4))
            result_bytes = image_editor.upscale_image(image_bytes, scale, hf_token)
        elif operation == "stylize":
            style = arguments.get("style", "enhance")
            result_bytes = image_editor.stylize_image(image_bytes, style, hf_token)
        else:
            return [types.TextContent(type="text", text=f"Unknown operation: {operation}")]

        result_b64 = base64.b64encode(result_bytes).decode()
        ritual = build_ritual_block(tier)
        return [
            types.ImageContent(type="image", data=result_b64, mimeType="image/png"),
            types.TextContent(type="text", text=ritual.to_markdown()),
        ]

    # ── Object Detection ──────────────────────────────────────────────────────
    if name == "xksh808_detect_objects":
        if blocked := _gate(tier, "object_detect"):
            return [blocked]
        image_bytes = _decode_image(arguments["image_b64"])
        prompt = arguments.get("prompt", "all objects")
        result = object_detect.detect_objects(image_bytes, prompt, hf_token)

        out: list[types.ContentBlock] = []
        if result["annotated_image"]:
            ann_b64 = base64.b64encode(result["annotated_image"]).decode()
            out.append(types.ImageContent(type="image", data=ann_b64, mimeType="image/png"))

        import json
        det_text = json.dumps(result["detections"], indent=2)
        det_text = apply_watermark(det_text, tier)
        out.append(types.TextContent(type="text", text=det_text))
        out.append(types.TextContent(type="text", text=build_ritual_block(tier).to_markdown()))
        return out

    # ── Video Generation ──────────────────────────────────────────────────────
    if name == "xksh808_generate_video":
        if blocked := _gate(tier, "video_gen"):
            return [blocked]
        prompt = arguments["prompt"]
        neg = arguments.get("negative_prompt", "blurry, low quality, watermark")
        dur = int(arguments.get("duration_seconds", 4))
        mp4_bytes = video_gen.generate_video(prompt, neg, dur, tier.value, hf_token)
        mp4_b64 = base64.b64encode(mp4_bytes).decode()
        ritual = build_ritual_block(tier)
        return [
            types.BlobResourceContents(
                uri=f"video://xksh808/{prompt[:40].replace(' ', '_')}.mp4",
                mimeType="video/mp4",
                blob=mp4_b64,
            ),
            types.TextContent(type="text", text=ritual.to_markdown()),
        ]

    # ── Ritual Info ───────────────────────────────────────────────────────────
    if name == "xksh808_ritual_info":
        ritual = build_ritual_block(tier)
        return [
            types.TextContent(type="text", text=ritual.to_markdown()),
            types.TextContent(
                type="text",
                text=(
                    f"**Tier:** {tier.value}  \n"
                    f"**Modules available:** {', '.join(can_access_module.__module__ and [] or _tier_modules(tier))}  \n"
                    f"**Demon Mode:** {'ON 🔥' if tier == Tier.PRO else 'OFF'}  \n"
                    f"**Owner Mode:** {'ON 👑' if tier == Tier.OWNER else 'OFF'}"
                ),
            ),
        ]

    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


def _tier_modules(tier: Tier) -> list[str]:
    from mcp_server.auth.tiers import TIER_MODULES
    modules = TIER_MODULES[tier]
    return ["all"] if "*" in modules else modules


# ── Entry point ───────────────────────────────────────────────────────────────

async def _run():
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())


def main():
    import asyncio
    asyncio.run(_run())


if __name__ == "__main__":
    main()
