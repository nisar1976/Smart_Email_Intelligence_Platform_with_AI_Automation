"""Analytics and reporting models."""

from datetime import datetime
from typing import List
from pydantic import BaseModel


class WeeklyReport(BaseModel):
    """Weekly analytics report summary."""

    week_ending: datetime
    total_emails_sent: int
    avg_open_rate: float
    avg_ctr: float
    avg_conversion_rate: float
    top_campaign_id: str
    bottom_campaign_id: str
    subject_line_suggestions: List[str]
    underperforming_campaigns: List[str]

    class Config:
        from_attributes = True
