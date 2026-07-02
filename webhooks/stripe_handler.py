"""
Stripe Webhook Handler
=======================
Listens for Stripe checkout events and:
  1. Assigns the correct tier to the customer
  2. Fires the Make.com automation webhook
  3. Logs to Notion CRM (if configured)

Mount this FastAPI router under /webhooks/stripe.
"""

import os
import hmac
import hashlib
import httpx
import json
from fastapi import APIRouter, Request, HTTPException

router = APIRouter(prefix="/webhooks/stripe", tags=["webhooks"])

# Stripe price IDs → tier mapping (set in Stripe Dashboard)
PRICE_TO_TIER: dict[str, str] = {
    os.getenv("STRIPE_PRICE_PAID", "price_paid_placeholder"): "paid",
    os.getenv("STRIPE_PRICE_PRO", "price_pro_placeholder"): "pro",
}


@router.post("/")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # Verify Stripe signature
    if not _verify_stripe_sig(payload, sig, secret):
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    event = json.loads(payload)
    event_type = event.get("type", "")

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_details", {}).get("email", "")
        price_id = _extract_price_id(session)
        tier = PRICE_TO_TIER.get(price_id, "paid")

        # Fire Make.com automation
        await _fire_make_webhook(
            event="payment_completed",
            email=customer_email,
            tier=tier,
            session_id=session.get("id", ""),
        )

    return {"status": "ok"}


async def _fire_make_webhook(event: str, email: str, tier: str, session_id: str):
    url = os.getenv("MAKE_WEBHOOK_URL", "")
    if not url:
        return
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json={
            "event": event,
            "email": email,
            "tier": tier,
            "session_id": session_id,
            "brand": "XKSH808",
        })


def _verify_stripe_sig(payload: bytes, sig_header: str, secret: str) -> bool:
    if not secret:
        return True  # Skip verification in dev
    try:
        parts = {k: v for k, v in (p.split("=", 1) for p in sig_header.split(","))}
        timestamp = parts.get("t", "")
        v1 = parts.get("v1", "")
        signed = f"{timestamp}.{payload.decode()}"
        expected = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, v1)
    except Exception:
        return False


def _extract_price_id(session: dict) -> str:
    try:
        return session["line_items"]["data"][0]["price"]["id"]
    except (KeyError, IndexError, TypeError):
        return ""
