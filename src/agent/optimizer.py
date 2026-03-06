"""A/B testing and weekly subject line optimization."""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from src.models.email import EmailCampaign, EmailAnalytics
from src.models.campaign import ABTestResult
from src.crm.base import CRMClient
from src.integrations.openai_client import EmailGenerationClient

logger = logging.getLogger(__name__)


class CampaignOptimizer:
    """Manages A/B testing and weekly subject line optimization."""

    MIN_SAMPLE_SIZE = 100  # Minimum recipients per variant for statistical significance
    MIN_WAIT_HOURS = 48  # Minimum hours to wait before evaluating A/B test

    def __init__(self, crm_client: CRMClient, openai_client: EmailGenerationClient):
        """Initialize optimizer with CRM and OpenAI clients.

        Args:
            crm_client: CRM client instance
            openai_client: OpenAI client for subject line generation
        """
        self.crm = crm_client
        self.openai_client = openai_client

    def create_ab_test(
        self, campaign: EmailCampaign, variant_b_subject: str
    ) -> Tuple[EmailCampaign, EmailCampaign]:
        """Create an A/B test by splitting campaign recipients 50/50.

        Args:
            campaign: Original email campaign
            variant_b_subject: Alternative subject line for variant B

        Returns:
            Tuple of (variant_a_campaign, variant_b_campaign)

        Raises:
            ValueError: If campaign has fewer than 2*MIN_SAMPLE_SIZE recipients
        """
        try:
            total_recipients = sum(1 for e in campaign.emails)
            if total_recipients < 2 * self.MIN_SAMPLE_SIZE:
                raise ValueError(
                    f"Campaign must have at least {2 * self.MIN_SAMPLE_SIZE} "
                    f"recipients for A/B test, got {total_recipients}"
                )

            # Create test ID
            test_id = str(uuid.uuid4())

            # Split emails 50/50
            midpoint = len(campaign.emails) // 2
            emails_a = campaign.emails[:midpoint]
            emails_b = campaign.emails[midpoint:]

            # Update variant B subject lines
            for email in emails_b:
                if email.sequence_step == 1:  # Only modify first email subject
                    email.subject = variant_b_subject

            # Create variant A campaign
            campaign_a = EmailCampaign(
                id=f"{campaign.id}_variant_a_{test_id}",
                name=f"{campaign.name} - Variant A",
                description=f"A/B test variant A (original) - Test ID: {test_id}",
                emails=emails_a,
                target_segment=campaign.target_segment,
                upsell_type=campaign.upsell_type,
                created_at=datetime.now(),
                is_abtest=True,
            )

            # Create variant B campaign
            campaign_b = EmailCampaign(
                id=f"{campaign.id}_variant_b_{test_id}",
                name=f"{campaign.name} - Variant B",
                description=f"A/B test variant B (alternative) - Test ID: {test_id}",
                emails=emails_b,
                target_segment=campaign.target_segment,
                upsell_type=campaign.upsell_type,
                created_at=datetime.now(),
                is_abtest=True,
            )

            logger.info(
                f"Created A/B test {test_id}: {len(emails_a)} recipients for variant A, "
                f"{len(emails_b)} for variant B"
            )

            return campaign_a, campaign_b

        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            raise

    def evaluate_ab_test(
        self, campaign_a_id: str, campaign_b_id: str, analytics_a: EmailAnalytics,
        analytics_b: EmailAnalytics
    ) -> Optional[ABTestResult]:
        """Evaluate A/B test results and determine winning campaign.

        Requires minimum sample size and wait time before evaluation.

        Args:
            campaign_a_id: ID of variant A campaign
            campaign_b_id: ID of variant B campaign
            analytics_a: Analytics for variant A
            analytics_b: Analytics for variant B

        Returns:
            ABTestResult with winner, or None if evaluation conditions not met

        Raises:
            ValueError: If campaigns have insufficient data
        """
        try:
            # Check minimum sample sizes
            if (analytics_a.total_sent < self.MIN_SAMPLE_SIZE or
                analytics_b.total_sent < self.MIN_SAMPLE_SIZE):
                logger.warning(
                    f"Insufficient sample size for A/B test evaluation. "
                    f"A: {analytics_a.total_sent}, B: {analytics_b.total_sent} "
                    f"(minimum: {self.MIN_SAMPLE_SIZE})"
                )
                return None

            # Compare open rates (primary metric)
            winner_id = None
            is_significant = False

            # Simple statistical test: difference must be >5% to be significant
            rate_difference = abs(analytics_a.open_rate - analytics_b.open_rate)
            if rate_difference > 0.05:
                is_significant = True
                winner_id = (
                    campaign_a_id
                    if analytics_a.open_rate > analytics_b.open_rate
                    else campaign_b_id
                )

            # Create result
            result = ABTestResult(
                test_id=f"test_{uuid.uuid4()}",
                campaign_a_id=campaign_a_id,
                campaign_b_id=campaign_b_id,
                winner_id=winner_id,
                sample_size_a=analytics_a.total_sent,
                sample_size_b=analytics_b.total_sent,
                open_rate_a=analytics_a.open_rate,
                open_rate_b=analytics_b.open_rate,
                evaluated_at=datetime.now(),
                is_statistically_significant=is_significant,
            )

            winner_label = winner_id.split("_")[-1].upper() if winner_id else "TIE"
            logger.info(
                f"A/B test evaluation complete. Winner: {winner_label}. "
                f"Open rates: A={analytics_a.open_rate:.2%}, B={analytics_b.open_rate:.2%}"
            )

            return result

        except Exception as e:
            logger.error(f"Error evaluating A/B test: {e}")
            raise

    def weekly_subject_optimization(
        self, analytics_data: List[Dict]
    ) -> List[str]:
        """Generate optimized subject line suggestions based on weekly performance data.

        Called by weekly scheduler. Pulls top/bottom performers and generates
        improved subject lines using OpenAI.

        Args:
            analytics_data: List of campaign analytics dicts from last 7 days

        Returns:
            List of optimized subject line suggestions for human review
        """
        try:
            if not analytics_data:
                logger.warning("No analytics data available for optimization")
                return []

            # Sort by open rate
            sorted_campaigns = sorted(
                analytics_data,
                key=lambda x: x.get("open_rate", 0),
                reverse=True
            )

            # Get top 3 and bottom 3
            top_performers = sorted_campaigns[:3]
            bottom_performers = sorted_campaigns[-3:]

            # Build optimization context
            performance_summary = "TOP PERFORMERS:\n"
            for campaign in top_performers:
                performance_summary += (
                    f"- Subject: {campaign.get('subject', 'Unknown')}\n"
                    f"  Open Rate: {campaign.get('open_rate', 0):.2%}\n"
                )

            performance_summary += "\nBOTTOM PERFORMERS:\n"
            for campaign in bottom_performers:
                performance_summary += (
                    f"- Subject: {campaign.get('subject', 'Unknown')}\n"
                    f"  Open Rate: {campaign.get('open_rate', 0):.2%}\n"
                )

            # Generate suggestions via OpenAI
            optimization_prompt = (
                f"Based on these email performance metrics:\n\n"
                f"{performance_summary}\n\n"
                f"Generate 5 improved subject lines that combine best practices from "
                f"top performers while maintaining OHM brand voice. "
                f"Subject lines should be compelling, concise, and action-oriented.\n\n"
                f"Return only the 5 subject lines, one per line, no numbering or explanation."
            )

            response = self.openai_client.optimize_subject_line(
                subject_line="Weekly Optimization",
                segment="all",
                historical_performance={
                    "top_performers": top_performers,
                    "bottom_performers": bottom_performers,
                }
            )

            # Parse response into list
            suggestions = []
            if response:
                suggestions = [line.strip() for line in response.split("\n") if line.strip()]

            logger.info(
                f"Generated {len(suggestions)} optimized subject line suggestions"
            )

            return suggestions[:5]  # Return top 5

        except Exception as e:
            logger.error(f"Error in weekly subject optimization: {e}")
            return []

    def get_optimization_recommendations(
        self, analytics_data: List[Dict]
    ) -> Dict:
        """Generate comprehensive optimization recommendations.

        Args:
            analytics_data: List of campaign analytics

        Returns:
            Dict with recommendations for various optimizations
        """
        try:
            if not analytics_data:
                return {}

            recommendations = {
                "timestamp": datetime.now(),
                "total_campaigns": len(analytics_data),
                "avg_open_rate": sum(c.get("open_rate", 0) for c in analytics_data) / len(analytics_data),
                "avg_ctr": sum(c.get("click_through_rate", 0) for c in analytics_data) / len(analytics_data),
                "improvements": [],
            }

            # Identify underperformers
            overall_avg = recommendations["avg_open_rate"]
            underperformers = [
                c for c in analytics_data
                if c.get("open_rate", 0) < overall_avg * 0.8
            ]

            if underperformers:
                recommendations["improvements"].append({
                    "type": "subject_line_improvement",
                    "count": len(underperformers),
                    "reason": "Low open rates compared to average",
                })

            # Check for low CTR
            avg_ctr = recommendations["avg_ctr"]
            low_ctr = [
                c for c in analytics_data
                if c.get("click_through_rate", 0) < avg_ctr * 0.8
            ]

            if low_ctr:
                recommendations["improvements"].append({
                    "type": "cta_optimization",
                    "count": len(low_ctr),
                    "reason": "Low click-through rates",
                })

            logger.info(
                f"Generated optimization recommendations: "
                f"{len(recommendations['improvements'])} areas for improvement"
            )

            return recommendations

        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")
            return {}
