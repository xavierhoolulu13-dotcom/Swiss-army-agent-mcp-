# 🌋 XKSH808 Ultimate Concierge — Hyper Repo MCP Tool

> **FloatForge808 · Volcano IS · SpiffyCloud OS**  
> Four Hugging Face Space engines. One unified MCP server. Fully monetized. Fully ritualized.

---

## ⚡ No-Click Install

### Mac / Linux — one command, auto-starts forever
```bash
curl -fsSL https://raw.githubusercontent.com/xavierhoolulu13-dotcom/Swiss-army-agent-mcp-/main/install.sh | bash
```

### Windows — one command (PowerShell, no admin)
```powershell
irm https://raw.githubusercontent.com/xavierhoolulu13-dotcom/Swiss-army-agent-mcp-/main/install.ps1 | iex
```

### Docker — one command, runs as a service
```bash
curl -fsSL https://raw.githubusercontent.com/xavierhoolulu13-dotcom/Swiss-army-agent-mcp-/main/docker-compose.yml -o docker-compose.yml && docker compose up -d
```

The installer:
1. Clones the repo to `~/.xksh808/mcp`
2. Creates a virtualenv and installs all dependencies
3. **Auto-patches Claude Desktop** `claude_desktop_config.json` — no manual editing
4. **Registers a system service** (launchd on Mac, systemd on Linux, Scheduled Task on Windows) so the server starts on every login
5. Restarts Claude Desktop detection is automatic — just relaunch Claude

After install, only one thing to fill in: `~/.xksh808/mcp/.env` → add `HF_TOKEN` and `OWNER_TOKEN`.

---

## What This Is

A **Model Context Protocol (MCP) server** that wires together four Hugging Face Spaces into a single branded, tier-gated tool engine — deployable as a local MCP server, an HTTP API, or a Hugging Face Gradio Space.

| Module | HF Space | Tier Required |
|---|---|---|
| 🔤 OCR | `stepfun-ai/GOT-OCR2_0` | Free |
| 🖼️ Image Editor | `briaai/BRIA-RMBG-2.0` · `gokaygokay/Tile-Upscaler` | Paid |
| 🎯 Object Detection | `ZhaohuiZhang/LocateAnything` | Paid |
| 🎬 Video Gen | `Wan-AI/Wan2.2-T2V-14B-Fast` | Pro 🔥 |

---

## Architecture

```
Claude / Any MCP Client
        │
        ▼
 xksh808-mcp (stdio MCP server)
        │
        ├── auth/tiers.py        ← Free / Paid / Pro / Owner token gate
        ├── ritual/xksh808.py    ← FloatForge808 branding block
        └── modules/
              ├── ocr.py         → HF Space: GOT-OCR2_0
              ├── image_editor.py→ HF Space: BRIA-RMBG-2.0 / Tile-Upscaler
              ├── object_detect.py→ HF Space: LocateAnything
              └── video_gen.py   → HF Space: Wan2.2-T2V-14B-Fast
                    │
        webhooks/
              ├── stripe_handler.py  ← Payment events → tier assignment
              └── make_handler.py    ← Make.com automation loop
```

---

## Quickstart

### 1. Install

```bash
pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
# Fill in: HF_TOKEN, OWNER_TOKEN, STRIPE_*, MAKE_WEBHOOK_URL
```

### 3. Run as MCP server (stdio — works with Claude Desktop, Cursor, etc.)

```bash
xksh808-mcp
```

Or add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "xksh808-ultimate": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/Swiss-army-agent-mcp-",
      "env": {
        "HF_TOKEN": "hf_your_token",
        "OWNER_TOKEN": "your_secret_owner_token"
      }
    }
  }
}
```

### 4. Run the Gradio UI (local or HF Space)

```bash
cd gradio_app
pip install -r requirements.txt
python app.py
```

Deploy to Hugging Face:
```bash
# Push gradio_app/ contents to a new HF Space named XKSH808-Ultimate-Concierge
```

---

## Payment Tiers

| Tier | Modules | Watermark | Automation | Price |
|---|---|---|---|---|
| Free | OCR only | ✅ Yes | ❌ | $0 |
| Paid | OCR + Image Edit + Detect | ❌ | ✅ | $X/mo |
| Pro 🔥 | All + Video Gen + Secret Lab | ❌ | ✅ Priority | $XX/mo |
| Owner 👑 | Everything, unlimited | ❌ | ✅ | Free (Xavier) |

Set `OWNER_TOKEN` in your `.env` for free owner access.  
Paid/Pro tokens are provisioned automatically via the Stripe webhook flow.

---

## Make.com Automation Flow

```
Stripe Payment
    │  POST /webhooks/stripe
    ▼
assign_tier(email, tier)
    │  POST /webhooks/make  {event: "crm_update"}
    ▼
Notion CRM updated
    │  Make.com scenario
    ▼
affiliate_payout → analytics_log → Funding Concierge → scale_signals
```

Configure in Make.com:
1. HTTP → `POST /webhooks/stripe` (Stripe trigger)
2. HTTP → `POST /webhooks/make` with `{"event":"crm_update", ...}`
3. Notion → create/update page in CRM DB
4. Loop: analytics → funding concierge → scale

---

## MCP Tools Exposed

| Tool | Description |
|---|---|
| `xksh808_ocr` | Extract text from any image |
| `xksh808_image_edit` | Remove bg / upscale / stylize |
| `xksh808_detect_objects` | Detect products, people, items |
| `xksh808_generate_video` | Text-to-video clip (Demon Mode) |
| `xksh808_ritual_info` | Returns ritual block + tier status |

---

## CTOcrew Ritual Pack

Once deployed, share with CTOcrew:

- **Space link:** `https://huggingface.co/spaces/xksh808/XKSH808-Ultimate-Concierge`
- **QR code:** generate from `https://xksh808.com/onboard`
- **Pitch script:** "One link. Four AI engines. Receipts, products, videos — all branded 808."
- **Client flow:** Free OCR → paid image edits → Pro video ads → affiliate referrals
- **Upsell flow:** Free → Paid → Pro → MarketCity808 bundle
- **Affiliate flow:** Each paid referral → CRM log → payout via Make.com
- **MCP config:** Point Claude Desktop at this server and all tools appear instantly

---

## Revenue Loop

```
User pays → Stripe webhook → tier assigned → Make.com fires
→ Notion CRM updated → affiliate tracked → analytics logged
→ Funding Concierge signaled → scale to more modules
→ More CTOcrew micro-businesses → more 808 cashflow 🌋
```

---

## Env Vars Reference

| Variable | Required | Description |
|---|---|---|
| `HF_TOKEN` | ✅ | Hugging Face API token |
| `OWNER_TOKEN` | ✅ | Xavier's master access token |
| `STRIPE_SECRET_KEY` | For payments | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | For payments | Stripe webhook signing secret |
| `STRIPE_PRICE_PAID` | For payments | Stripe price ID for Paid tier |
| `STRIPE_PRICE_PRO` | For payments | Stripe price ID for Pro tier |
| `MAKE_WEBHOOK_URL` | For automation | Make.com outbound webhook URL |
| `MAKE_INBOUND_SECRET` | Optional | Shared secret for Make.com inbound |
| `NOTION_API_TOKEN` | For CRM | Notion integration token |
| `NOTION_CRM_DB_ID` | For CRM | Notion CRM database ID |
| `TELEGRAM_BOT_TOKEN` | Optional | Telegram bot for ritual triggers |

---

*🌋 XKSH808 · FloatForge808 · Volcano IS · SpiffyCloud OS*
