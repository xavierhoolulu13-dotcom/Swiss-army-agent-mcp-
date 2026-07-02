"""
XKSH808 Ultimate Concierge — Gradio HF Space App
==================================================
FloatForge808 neon UI · Mobile-first · Demon Mode toggle
"""

import os
import sys
import base64
import io

import gradio as gr
from PIL import Image
from dotenv import load_dotenv

# Allow importing from parent when running locally
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

load_dotenv()

from mcp_server.auth.tiers import resolve_tier, can_access_module, needs_watermark, Tier
from mcp_server.ritual.xksh808 import build_ritual_block, apply_watermark, NEON_COLORS
from mcp_server.modules import ocr, image_editor, object_detect, video_gen

HF_TOKEN = os.getenv("HF_TOKEN")

# ── Neon CSS ──────────────────────────────────────────────────────────────────
NEON_CSS = """
:root {
  --primary: #FF00FF;
  --accent:  #00FFFF;
  --bg:      #0a0a0a;
  --card-bg: #111118;
  --text:    #e0e0e0;
  --border:  #FF00FF44;
}
body, .gradio-container {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'Courier New', monospace;
}
.gr-button-primary {
  background: linear-gradient(135deg, var(--primary), var(--accent)) !important;
  color: #000 !important;
  font-weight: bold !important;
  border: none !important;
  border-radius: 8px !important;
  text-transform: uppercase !important;
  letter-spacing: 1px !important;
}
.gr-button-secondary {
  border: 1px solid var(--primary) !important;
  color: var(--primary) !important;
  background: transparent !important;
}
.gr-panel, .gr-box, .gradio-tabs, .tab-nav {
  background: var(--card-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}
.tab-nav button.selected {
  background: var(--primary) !important;
  color: #000 !important;
}
label, .gr-label { color: var(--accent) !important; }
.gr-input, textarea, input { background: #1a1a24 !important; color: var(--text) !important; }
"""

HEADER_HTML = """
<div style="text-align:center; padding:20px 0 10px;">
  <h1 style="font-size:2.2em; background:linear-gradient(135deg,#FF00FF,#00FFFF);
             -webkit-background-clip:text; -webkit-text-fill-color:transparent;
             font-family:'Courier New',monospace; letter-spacing:3px;">
    🌋 XKSH808 ULTIMATE CONCIERGE
  </h1>
  <p style="color:#888; font-family:monospace; font-size:.9em;">
    FloatForge808 · Volcano IS · SpiffyCloud OS
  </p>
</div>
"""

FOOTER_MD = (
    "---\n"
    "🔗 [xksh808.com](https://xksh808.com)  ·  "
    "📓 [Notion Hub](https://notion.so/xksh808)  ·  "
    "📡 [Telegram](https://t.me/xksh808)  ·  "
    "🏙️ [MarketCity808](https://marketcity808.com)"
)


# ── Tier resolution ───────────────────────────────────────────────────────────

def _tier(token: str) -> Tier:
    return resolve_tier(token.strip() if token else None)


def _tier_badge(t: Tier) -> str:
    badges = {
        Tier.FREE: "🔓 Free",
        Tier.PAID: "💳 Paid",
        Tier.PRO: "🔥 PRO — Demon Mode",
        Tier.OWNER: "👑 Owner",
    }
    return badges.get(t, "🔓 Free")


# ── Module handlers ───────────────────────────────────────────────────────────

def run_ocr(image, token):
    t = _tier(token)
    if not can_access_module(t, "ocr"):
        return "🔒 OCR requires Free tier or above — no token needed!", None
    if image is None:
        return "Please upload an image.", None
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    text = ocr.run_ocr(buf.getvalue(), "upload.png", HF_TOKEN)
    text = apply_watermark(text, t)
    ritual = build_ritual_block(t)
    return text, f"**Tier:** {_tier_badge(t)}\n\n{ritual.to_markdown()}"


def run_image_edit(image, operation, scale, style, token):
    t = _tier(token)
    if not can_access_module(t, "image_editor"):
        return None, "🔒 Image Editor requires Paid tier or above."
    if image is None:
        return None, "Please upload an image."
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    if operation == "Remove Background":
        result = image_editor.remove_background(img_bytes, HF_TOKEN)
    elif operation == "Upscale":
        result = image_editor.upscale_image(img_bytes, int(scale), HF_TOKEN)
    else:
        result = image_editor.stylize_image(img_bytes, style.lower(), HF_TOKEN)

    out_img = Image.open(io.BytesIO(result))
    ritual = build_ritual_block(t)
    return out_img, f"**Tier:** {_tier_badge(t)}\n\n{ritual.to_markdown()}"


def run_detect(image, prompt, token):
    t = _tier(token)
    if not can_access_module(t, "object_detect"):
        return None, "🔒 Object Detection requires Paid tier or above."
    if image is None:
        return None, "Please upload an image."
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    result = object_detect.detect_objects(buf.getvalue(), prompt or "all objects", HF_TOKEN)

    ann_img = None
    if result["annotated_image"]:
        ann_img = Image.open(io.BytesIO(result["annotated_image"]))

    import json
    detections_text = json.dumps(result["detections"], indent=2)
    detections_text = apply_watermark(detections_text, t)
    ritual = build_ritual_block(t)
    return ann_img, f"**Detections:**\n```json\n{detections_text}\n```\n\n{ritual.to_markdown()}"


def run_video(prompt, neg_prompt, duration, token):
    t = _tier(token)
    if not can_access_module(t, "video_gen"):
        return None, "🔒 Video Gen requires Pro (Demon Mode) tier."
    if not prompt:
        return None, "Please enter a prompt."
    mp4 = video_gen.generate_video(prompt, neg_prompt, int(duration), t.value, HF_TOKEN)
    # Save to temp file for Gradio to serve
    import tempfile, pathlib
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp.write(mp4)
    tmp.close()
    ritual = build_ritual_block(t)
    return tmp.name, f"**Tier:** {_tier_badge(t)}\n\n{ritual.to_markdown()}"


# ── Gradio UI ─────────────────────────────────────────────────────────────────

def build_ui():
    with gr.Blocks(css=NEON_CSS, title="🌋 XKSH808 Ultimate Concierge") as demo:
        gr.HTML(HEADER_HTML)

        with gr.Row():
            token_input = gr.Textbox(
                label="🔑 Bearer Token (leave blank for Free tier)",
                placeholder="Paste your XKSH808 token here…",
                type="password",
                scale=4,
            )
            tier_display = gr.Markdown("", scale=1)

        token_input.change(
            fn=lambda t: f"**Tier:** {_tier_badge(_tier(t))}",
            inputs=token_input,
            outputs=tier_display,
        )

        with gr.Tabs():
            # ── OCR Tab ──────────────────────────────────────────────────────
            with gr.Tab("🔤 OCR"):
                with gr.Row():
                    ocr_img = gr.Image(label="Upload Image / Doc", type="pil")
                    with gr.Column():
                        ocr_out = gr.Textbox(label="Extracted Text", lines=12)
                        ocr_ritual = gr.Markdown()
                gr.Button("🔍 Extract Text", variant="primary").click(
                    run_ocr, [ocr_img, token_input], [ocr_out, ocr_ritual]
                )

            # ── Image Editor Tab ─────────────────────────────────────────────
            with gr.Tab("🖼️ Image Editor"):
                with gr.Row():
                    edit_img = gr.Image(label="Upload Image", type="pil")
                    edit_out = gr.Image(label="Result")
                with gr.Row():
                    op_radio = gr.Radio(
                        ["Remove Background", "Upscale", "Stylize"],
                        label="Operation", value="Remove Background"
                    )
                    scale_slider = gr.Slider(2, 4, step=2, value=4, label="Upscale Factor")
                    style_drop = gr.Dropdown(["Enhance", "Anime", "Photo"], value="Enhance", label="Style")
                edit_ritual = gr.Markdown()
                gr.Button("✨ Edit Image", variant="primary").click(
                    run_image_edit,
                    [edit_img, op_radio, scale_slider, style_drop, token_input],
                    [edit_out, edit_ritual],
                )

            # ── Object Detection Tab ─────────────────────────────────────────
            with gr.Tab("🎯 Detect Objects"):
                with gr.Row():
                    det_img = gr.Image(label="Upload Image", type="pil")
                    det_out = gr.Image(label="Annotated Result")
                det_prompt = gr.Textbox(label="What to detect", placeholder="e.g. red shoes, barcodes…")
                det_text = gr.Markdown()
                gr.Button("🎯 Detect", variant="primary").click(
                    run_detect, [det_img, det_prompt, token_input], [det_out, det_text]
                )

            # ── Video Generation Tab ─────────────────────────────────────────
            with gr.Tab("🎬 Video Gen 🔥"):
                vid_prompt = gr.Textbox(label="Prompt", placeholder="neon 808 city intro loop…")
                vid_neg = gr.Textbox(label="Negative Prompt", value="blurry, low quality, watermark")
                vid_dur = gr.Slider(2, 20, value=4, step=1, label="Duration (seconds)")
                with gr.Row():
                    vid_out = gr.Video(label="Generated Clip")
                    vid_ritual = gr.Markdown()
                gr.Button("🎬 Generate Video", variant="primary").click(
                    run_video, [vid_prompt, vid_neg, vid_dur, token_input], [vid_out, vid_ritual]
                )

            # ── Ritual / Info Tab ────────────────────────────────────────────
            with gr.Tab("🌋 Ritual Info"):
                ritual_out = gr.Markdown()
                gr.Button("Show My Ritual Block", variant="secondary").click(
                    fn=lambda t: build_ritual_block(_tier(t)).to_markdown(),
                    inputs=token_input,
                    outputs=ritual_out,
                )
                gr.Markdown(FOOTER_MD)

        gr.Markdown(FOOTER_MD)

    return demo


if __name__ == "__main__":
    ui = build_ui()
    ui.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))
