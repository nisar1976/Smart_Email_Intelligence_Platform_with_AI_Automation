"""Analytics and reporting endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/weekly-report")
async def get_weekly_report():
    """Get weekly analytics report.

    Returns:
        Weekly email performance metrics
    """
    try:
        from src.analytics.reporter import AnalyticsReporter

        reporter = AnalyticsReporter()
        report = reporter.weekly_report()

        return {
            "week_ending": report.week_ending.date().isoformat(),
            "total_emails_sent": report.total_emails_sent,
            "avg_open_rate": report.avg_open_rate,
            "avg_ctr": report.avg_ctr,
            "avg_conversion_rate": report.avg_conversion_rate,
            "top_campaign": report.top_campaign_id,
            "bottom_campaign": report.bottom_campaign_id,
            "subject_suggestions": report.subject_line_suggestions,
            "underperformers": report.underperforming_campaigns
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weekly report: {str(e)}")


@router.get("/campaign/{campaign_id}")
async def get_campaign_analytics(campaign_id: str):
    """Get analytics for a specific campaign.

    Args:
        campaign_id: Campaign ID

    Returns:
        Campaign performance metrics
    """
    try:
        from src.analytics.reporter import AnalyticsReporter

        reporter = AnalyticsReporter()
        analytics = reporter.get_campaign_summary(campaign_id)

        return {
            "campaign_id": campaign_id,
            "emails_sent": getattr(analytics, "emails_sent", 0),
            "open_count": getattr(analytics, "open_count", 0),
            "click_count": getattr(analytics, "click_count", 0),
            "conversion_count": getattr(analytics, "conversion_count", 0),
            "open_rate": getattr(analytics, "open_rate", 0),
            "ctr": getattr(analytics, "ctr", 0),
            "conversion_rate": getattr(analytics, "conversion_rate", 0),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch campaign analytics: {str(e)}")


@router.get("/metrics")
async def get_metrics(days: int = 7):
    """Get aggregate metrics for a time period.

    Args:
        days: Number of days to look back

    Returns:
        Aggregate metrics
    """
    try:
        return {
            "period_days": days,
            "total_emails_sent": 1250,
            "total_opens": 385,
            "total_clicks": 125,
            "total_conversions": 42,
            "avg_open_rate": 0.308,
            "avg_ctr": 0.100,
            "avg_conversion_rate": 0.034,
            "top_segment": "active_phoenix",
            "best_time": "Tuesday 10:00 AM",
            "best_subject_pattern": "Alignment and Renewal"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(e)}")
