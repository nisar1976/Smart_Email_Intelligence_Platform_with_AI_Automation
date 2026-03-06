"""Analytics reporting and aggregation."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from src.models.email import EmailAnalytics
from src.models.analytics import WeeklyReport
from src.analytics.tracker import EmailTracker

logger = logging.getLogger(__name__)


class AnalyticsReporter:
    """Aggregates metrics and generates performance reports."""

    def __init__(self):
        """Initialize reporter with tracker."""
        self.tracker = EmailTracker()

    def get_campaign_summary(self, campaign_id: str) -> EmailAnalytics:
        """Get aggregated metrics for a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            EmailAnalytics object with aggregated metrics
        """
        try:
            # This would query the database for all emails in the campaign
            # and aggregate their statistics

            # Placeholder implementation
            analytics = EmailAnalytics(
                campaign_id=campaign_id,
                total_sent=0,
                total_opened=0,
                total_clicked=0,
                total_converted=0,
                open_rate=0.0,
                click_through_rate=0.0,
                conversion_rate=0.0,
                last_updated=datetime.now(),
            )

            analytics.calculate_rates()

            logger.info(f"Generated summary for campaign {campaign_id}")
            return analytics

        except Exception as e:
            logger.error(f"Error getting campaign summary: {e}")
            raise

    def weekly_report(
        self, analytics_data: Optional[List[Dict]] = None
    ) -> WeeklyReport:
        """Generate weekly analytics report.

        Args:
            analytics_data: Optional pre-aggregated analytics data

        Returns:
            WeeklyReport with summary metrics
        """
        try:
            if not analytics_data:
                analytics_data = []

            now = datetime.now()
            week_ending = now.replace(hour=23, minute=59, second=59, microsecond=0)

            if not analytics_data:
                # Return empty report if no data
                return WeeklyReport(
                    week_ending=week_ending,
                    total_emails_sent=0,
                    avg_open_rate=0.0,
                    avg_ctr=0.0,
                    avg_conversion_rate=0.0,
                    top_campaign_id="",
                    bottom_campaign_id="",
                    subject_line_suggestions=[],
                    underperforming_campaigns=[],
                )

            # Calculate aggregates
            total_sent = sum(c.get("total_sent", 0) for c in analytics_data)
            avg_open_rate = (
                sum(c.get("open_rate", 0) for c in analytics_data) / len(analytics_data)
                if analytics_data
                else 0.0
            )
            avg_ctr = (
                sum(c.get("click_through_rate", 0) for c in analytics_data)
                / len(analytics_data)
                if analytics_data
                else 0.0
            )
            avg_conversion = (
                sum(c.get("conversion_rate", 0) for c in analytics_data)
                / len(analytics_data)
                if analytics_data
                else 0.0
            )

            # Find top and bottom performers
            sorted_by_open = sorted(
                analytics_data,
                key=lambda x: x.get("open_rate", 0),
                reverse=True
            )

            top_campaign = sorted_by_open[0] if sorted_by_open else {}
            bottom_campaign = sorted_by_open[-1] if sorted_by_open else {}

            # Identify underperformers
            underperformers = [
                c.get("campaign_id")
                for c in analytics_data
                if c.get("open_rate", 0) < avg_open_rate * 0.8
            ]

            # Generate subject line suggestions (would call optimizer in production)
            subject_suggestions = self._generate_subject_suggestions(analytics_data)

            report = WeeklyReport(
                week_ending=week_ending,
                total_emails_sent=total_sent,
                avg_open_rate=avg_open_rate,
                avg_ctr=avg_ctr,
                avg_conversion_rate=avg_conversion,
                top_campaign_id=top_campaign.get("campaign_id", ""),
                bottom_campaign_id=bottom_campaign.get("campaign_id", ""),
                subject_line_suggestions=subject_suggestions,
                underperforming_campaigns=underperformers,
            )

            logger.info(
                f"Generated weekly report: {total_sent} emails, "
                f"{avg_open_rate:.2%} avg open rate"
            )

            return report

        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            raise

    def flag_underperformers(
        self, analytics_data: List[Dict], threshold_open_rate: float = 0.15
    ) -> List[str]:
        """Identify campaigns with open rates below threshold.

        Args:
            analytics_data: List of campaign analytics dicts
            threshold_open_rate: Minimum acceptable open rate (default 15%)

        Returns:
            List of underperforming campaign IDs
        """
        try:
            underperformers = [
                c.get("campaign_id")
                for c in analytics_data
                if c.get("open_rate", 0) < threshold_open_rate
            ]

            logger.info(
                f"Flagged {len(underperformers)} campaigns with open rate < {threshold_open_rate:.1%}"
            )

            return underperformers

        except Exception as e:
            logger.error(f"Error flagging underperformers: {e}")
            return []

    def get_segment_performance(
        self, analytics_data: List[Dict], segment: str
    ) -> Dict:
        """Get performance metrics for a specific audience segment.

        Args:
            analytics_data: List of campaign analytics dicts
            segment: Segment name to filter by

        Returns:
            Performance summary dict
        """
        try:
            segment_campaigns = [
                c for c in analytics_data
                if c.get("segment") == segment
            ]

            if not segment_campaigns:
                return {
                    "segment": segment,
                    "campaign_count": 0,
                    "avg_open_rate": 0.0,
                    "avg_ctr": 0.0,
                    "avg_conversion_rate": 0.0,
                }

            avg_open = (
                sum(c.get("open_rate", 0) for c in segment_campaigns)
                / len(segment_campaigns)
            )
            avg_ctr = (
                sum(c.get("click_through_rate", 0) for c in segment_campaigns)
                / len(segment_campaigns)
            )
            avg_conversion = (
                sum(c.get("conversion_rate", 0) for c in segment_campaigns)
                / len(segment_campaigns)
            )

            return {
                "segment": segment,
                "campaign_count": len(segment_campaigns),
                "avg_open_rate": avg_open,
                "avg_ctr": avg_ctr,
                "avg_conversion_rate": avg_conversion,
            }

        except Exception as e:
            logger.error(f"Error getting segment performance: {e}")
            return {}

    def _generate_subject_suggestions(self, analytics_data: List[Dict]) -> List[str]:
        """Generate subject line optimization suggestions.

        Args:
            analytics_data: List of campaign analytics dicts

        Returns:
            List of suggested subject lines
        """
        # Placeholder - would call CampaignOptimizer in production
        return [
            "Subject line suggestion 1",
            "Subject line suggestion 2",
            "Subject line suggestion 3",
        ]

    def get_conversion_funnel(
        self, analytics_data: List[Dict]
    ) -> Dict:
        """Get conversion funnel metrics across all campaigns.

        Args:
            analytics_data: List of campaign analytics dicts

        Returns:
            Funnel dict with open -> click -> conversion rates
        """
        try:
            total_sent = sum(c.get("total_sent", 0) for c in analytics_data)
            total_opened = sum(c.get("total_opened", 0) for c in analytics_data)
            total_clicked = sum(c.get("total_clicked", 0) for c in analytics_data)
            total_converted = sum(c.get("total_converted", 0) for c in analytics_data)

            funnel = {
                "total_sent": total_sent,
                "total_opened": total_opened,
                "total_clicked": total_clicked,
                "total_converted": total_converted,
                "open_rate": total_opened / total_sent if total_sent > 0 else 0,
                "click_rate": total_clicked / total_opened if total_opened > 0 else 0,
                "conversion_rate": total_converted / total_clicked if total_clicked > 0 else 0,
            }

            logger.info(
                f"Conversion funnel: {funnel['open_rate']:.2%} open, "
                f"{funnel['click_rate']:.2%} click, "
                f"{funnel['conversion_rate']:.2%} conversion"
            )

            return funnel

        except Exception as e:
            logger.error(f"Error calculating conversion funnel: {e}")
            return {}
