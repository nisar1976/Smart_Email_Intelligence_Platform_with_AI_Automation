"""Webhook event models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class StripeEvent(BaseModel):
    """Stripe webhook event data."""

    event_id: str
    event_type: str
    customer_id: str
    subscription_id: Optional[str] = None
    tier: Optional[str] = None  # "phoenix", "visionary", "infinity"
    received_at: datetime
    processed: bool = False

    class Config:
        from_attributes = True
