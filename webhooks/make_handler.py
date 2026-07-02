"""
Make.com Automation Webhook — Inbound receiver
===============================================
Make.com can POST back to this endpoint to trigger
module runs or CRM updates from within a scenario.

Automation flow supported:
  payment → trigger_module → deliver_output
  → crm_update → affiliate_payout → analytics_log
  → funding_concierge → scale_signals
"""

import os
import httpx
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Literal

router = APIRouter(prefix="/webhooks/make", tags=["webhooks"])

MAKE_SECRET = os.getenv("MAKE_INBOUND_SECRET", "")


class MakePayload(BaseModel):
    event: Literal[
        "trigger_module",
        "crm_update",
        "affiliate_payout",
        "analytics_log",
        "funding_signal",
    ]
    module: str | None = None
    email: str | None = None
    tier: str = "free"
    data: dict = {}


@router.post("/")
async def make_inbound(request: Request, payload: MakePayload):
    # Optional shared-secret gate
    if MAKE_SECRET:
        auth = request.headers.get("X-Make-Secret", "")
        if auth != MAKE_SECRET:
            raise HTTPException(status_code=401, detail="Unauthorized")

    if payload.event == "trigger_module":
        return await _handle_trigger(payload)
    if payload.event == "crm_update":
        return await _handle_crm(payload)
    if payload.event == "analytics_log":
        return _handle_analytics(payload)
    if payload.event == "funding_signal":
        return _handle_funding(payload)

    return {"status": "received", "event": payload.event}


async def _handle_trigger(payload: MakePayload) -> dict:
    """Forward module trigger to the MCP server's HTTP bridge (if running)."""
    bridge_url = os.getenv("MCP_HTTP_BRIDGE", "")
    if bridge_url:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{bridge_url}/run", json={
                "module": payload.module,
                "tier": payload.tier,
                "data": payload.data,
            })
            return resp.json()
    return {"status": "bridge_not_configured"}


async def _handle_crm(payload: MakePayload) -> dict:
    """Push update to Notion CRM database."""
    notion_token = os.getenv("NOTION_API_TOKEN", "")
    notion_db = os.getenv("NOTION_CRM_DB_ID", "")
    if not (notion_token and notion_db):
        return {"status": "notion_not_configured"}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.notion.com/v1/pages",
            headers={
                "Authorization": f"Bearer {notion_token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            json={
                "parent": {"database_id": notion_db},
                "properties": {
                    "Email": {"email": payload.email},
                    "Tier": {"select": {"name": payload.tier}},
                    "Event": {"rich_text": [{"text": {"content": payload.event}}]},
                },
            },
        )
    return {"status": "crm_updated", "notion_id": resp.json().get("id")}


def _handle_analytics(payload: MakePayload) -> dict:
    # Stub: log to internal analytics store
    return {"status": "logged", "event": payload.event, "tier": payload.tier}


def _handle_funding(payload: MakePayload) -> dict:
    # Stub: signal Funding Concierge for scale decision
    return {"status": "signal_received", "brand": "XKSH808", "data": payload.data}
