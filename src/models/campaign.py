"""Campaign and A/B testing models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ABTestResult(BaseModel):
    """Results from an A/B test comparing two campaign variants."""

    test_id: str
    campaign_a_id: str
    campaign_b_id: str
    winner_id: Optional[str] = None  # Set after evaluation
    sample_size_a: int
    sample_size_b: int
    open_rate_a: float
    open_rate_b: float
    evaluated_at: Optional[datetime] = None
    is_statistically_significant: bool = False

    class Config:
        from_attributes = True
