"""Behavioral audience segmentation logic."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from src.crm.base import CRMClient

logger = logging.getLogger(__name__)


class AudienceSegmentor:
    """Classifies contacts into behavioral segments based on CRM + Stripe data."""

    # Segment definitions with criteria
    SEGMENTS = {
        "cold_prospect": {
            "description": "No purchase, no engagement in 30+ days",
            "days_inactive": 30,
        },
        "new_phoenix": {
            "description": "Subscribed Phoenix tier < 7 days ago",
            "days_since_signup": 7,
        },
        "active_phoenix": {
            "description": "Phoenix, engaged in last 14 days, no upsell yet",
            "days_active": 14,
        },
        "upsell_candidate_visionary": {
            "description": "Active Phoenix, 30+ days, clicked upsell CTA",
            "days_since_signup": 30,
        },
        "upsell_candidate_infinity": {
            "description": "Active Visionary, 30+ days, clicked upsell CTA",
            "days_since_signup": 30,
        },
        "churned": {
            "description": "Cancelled subscription or no login in 60+ days",
            "days_inactive": 60,
        },
        "reactivation": {
            "description": "Churned > 90 days, previously active",
            "days_since_churn": 90,
        },
    }

    def __init__(self, crm_client: CRMClient):
        """Initialize segmentor with CRM client.

        Args:
            crm_client: CRM client instance (HubSpot, ConvertKit, etc.)
        """
        self.crm = crm_client

    def segment_all(self) -> Dict[str, List[str]]:
        """Classify all contacts and return mapping of segment -> contact IDs.

        Returns:
            Dict mapping segment name to list of contact IDs
        """
        segments = {segment_name: [] for segment_name in self.SEGMENTS.keys()}

        try:
            # Retrieve all contacts from CRM (in batches)
            contacts = self.crm.get_contacts(segment="all", limit=10000)

            for contact in contacts:
                segment = self.classify_contact(contact)
                if segment:
                    segments[segment].append(contact.get("id"))

            logger.info(
                f"Segmented {sum(len(v) for v in segments.values())} contacts "
                f"across {len(self.SEGMENTS)} segments"
            )
            return segments

        except Exception as e:
            logger.error(f"Error segmenting all contacts: {e}")
            raise

    def classify_contact(self, contact: dict) -> str:
        """Classify a single contact into the best-fit segment.

        Args:
            contact: Contact dict with email, id, lifecycle_stage, last_activity_date, etc.

        Returns:
            Segment name string, or None if unclassified
        """
        try:
            # Extract contact properties
            lifecycle_stage = contact.get("lifecycle_stage", "").lower()
            tier = contact.get("subscription_tier", "").lower()
            last_activity = contact.get("last_activity_date")
            subscription_created = contact.get("subscription_created_date")
            subscription_cancelled = contact.get("subscription_cancelled_date")
            clicked_upsell_cta = contact.get("clicked_upsell_cta", False)

            now = datetime.now()

            # Parse dates if they're strings
            if isinstance(last_activity, str):
                try:
                    last_activity = datetime.fromisoformat(last_activity)
                except ValueError:
                    last_activity = None

            if isinstance(subscription_created, str):
                try:
                    subscription_created = datetime.fromisoformat(subscription_created)
                except ValueError:
                    subscription_created = None

            if isinstance(subscription_cancelled, str):
                try:
                    subscription_cancelled = datetime.fromisoformat(
                        subscription_cancelled
                    )
                except ValueError:
                    subscription_cancelled = None

            # Segment classification logic
            # Priority: most specific to least specific

            # Churned - cancelled subscription
            if subscription_cancelled:
                days_since_churn = (now - subscription_cancelled).days
                if days_since_churn > 90:
                    return "reactivation"
                elif days_since_churn > 0:
                    return "churned"

            # No active subscription = cold prospect
            if not tier or tier == "none":
                if last_activity:
                    days_inactive = (now - last_activity).days
                    if days_inactive > 30:
                        return "cold_prospect"
                return "cold_prospect"

            # New Phoenix member
            if tier == "phoenix" and subscription_created:
                days_since_signup = (now - subscription_created).days
                if days_since_signup < 7:
                    return "new_phoenix"

            # Upsell candidate - Visionary
            if (
                tier == "phoenix"
                and subscription_created
                and clicked_upsell_cta
            ):
                days_since_signup = (now - subscription_created).days
                if days_since_signup >= 30:
                    return "upsell_candidate_visionary"

            # Upsell candidate - Infinity
            if (
                tier == "visionary"
                and subscription_created
                and clicked_upsell_cta
            ):
                days_since_signup = (now - subscription_created).days
                if days_since_signup >= 30:
                    return "upsell_candidate_infinity"

            # Active Phoenix
            if tier == "phoenix" and last_activity:
                days_inactive = (now - last_activity).days
                if days_inactive <= 14:
                    return "active_phoenix"

            # Default fallback
            return "cold_prospect"

        except Exception as e:
            logger.error(f"Error classifying contact {contact.get('id')}: {e}")
            return None
