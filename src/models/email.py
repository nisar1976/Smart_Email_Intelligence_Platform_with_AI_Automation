"""Email data models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class Email(BaseModel):
    """Email message model."""

    id: Optional[str] = None
    subject: str
    body: str
    recipient_email: EmailStr
    recipient_id: str
    campaign_id: Optional[str] = None
    sequence_step: int  # Position in the 20-email sequence
    segment: str  # e.g., "cold_prospect", "active_user", "churned"
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmailCampaign(BaseModel):
    """Email campaign model."""

    id: Optional[str] = None
    name: str
    description: str
    emails: list[Email]
    target_segment: str
    upsell_type: Optional[str] = None  # "Phoenix", "Visionary", "Infinity"
    created_at: datetime
    sent_at: Optional[datetime] = None
    is_abtest: bool = False

    class Config:
        from_attributes = True


class EmailAnalytics(BaseModel):
    """Email performance metrics."""

    campaign_id: str
    total_sent: int
    total_opened: int
    total_clicked: int
    total_converted: int
    open_rate: float
    click_through_rate: float
    conversion_rate: float
    last_updated: datetime

    class Config:
        from_attributes = True

    def calculate_rates(self) -> None:
        """Calculate performance rates from counts."""
        if self.total_sent > 0:
            self.open_rate = self.total_opened / self.total_sent
            self.click_through_rate = self.total_clicked / self.total_sent
            self.conversion_rate = self.total_converted / self.total_sent
