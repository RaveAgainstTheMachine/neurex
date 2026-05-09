import json
from pathlib import Path

import structlog
from fastapi import APIRouter
from pydantic import BaseModel
from pywebpush import WebPushException, webpush

log = structlog.get_logger()
router = APIRouter()

SUBS_FILE = Path.home() / ".neurex" / "push_subscriptions.json"
VAPID_PRIVATE = "private_key.pem"
VAPID_CLAIMS = {"sub": "mailto:admin@neurex.local"}

class Subscription(BaseModel):
    endpoint: str
    keys: dict

@router.post("/register")
async def register_push(sub: Subscription):
    """Store a device's push subscription."""
    SUBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    subs = []
    if SUBS_FILE.exists():
        subs = json.loads(SUBS_FILE.read_text())
    
    # Avoid duplicates
    if not any(s["endpoint"] == sub.endpoint for s in subs):
        subs.append(sub.dict())
        SUBS_FILE.write_text(json.dumps(subs))
        log.info("push.registered", endpoint=sub.endpoint)
    
    return {"status": "registered"}

def send_notification(title: str, body: str):
    """Send a push notification to all registered devices."""
    if not SUBS_FILE.exists():
        return
        
    subs = json.loads(SUBS_FILE.read_text())
    payload = {"title": title, "body": body}
    
    private_key_path = Path("private_key.pem")
    if not private_key_path.exists():
        log.error("push.failed", error="VAPID private key missing")
        return

    for sub in subs:
        try:
            webpush(
                subscription_info=sub,
                data=json.dumps(payload),
                vapid_private_key=str(private_key_path),
                vapid_claims=VAPID_CLAIMS
            )
            log.info("push.sent", endpoint=sub["endpoint"])
        except WebPushException as ex:
            log.error("push.failed", endpoint=sub["endpoint"], error=str(ex))
            # If the subscription is expired/invalid, we should remove it
            if "410" in str(ex) or "404" in str(ex):
                 subs = [s for s in subs if s["endpoint"] != sub["endpoint"]]
                 SUBS_FILE.write_text(json.dumps(subs))
