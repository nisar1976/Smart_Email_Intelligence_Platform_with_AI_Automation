"""Abstract base class for CRM integrations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class CRMClient(ABC):
    """Base class for CRM integrations (HubSpot, ConvertKit, etc.)."""

    @abstractmethod
    def get_contacts(self, segment: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve contacts matching a behavioral segment.

        Args:
            segment: Behavioral segment filter (e.g., "churned", "active_purchase")
            limit: Maximum number of contacts to retrieve

        Returns:
            List of contact dictionaries with email, id, and segment metadata
        """
        pass

    @abstractmethod
    def create_campaign(self, campaign_name: str, emails: List[Dict[str, str]]) -> str:
        """Create a new email campaign.

        Args:
            campaign_name: Name for the campaign
            emails: List of email dicts with subject, body, recipient_id

        Returns:
            Campaign ID
        """
        pass

    @abstractmethod
    def send_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Send a campaign to all recipients.

        Args:
            campaign_id: ID of the campaign to send

        Returns:
            Deployment confirmation with recipient count
        """
        pass

    @abstractmethod
    def get_analytics(
        self, campaign_id: str
    ) -> Dict[str, Any]:
        """Retrieve campaign analytics (opens, clicks, conversions).

        Args:
            campaign_id: ID of the campaign

        Returns:
            Analytics dict with metrics and timestamps
        """
        pass

    @abstractmethod
    def segment_contacts(self, criteria: Dict[str, Any]) -> List[str]:
        """Segment contacts based on behavioral criteria.

        Args:
            criteria: Segmentation criteria (purchase history, engagement, etc.)

        Returns:
            List of contact IDs matching the segment
        """
        pass

    @abstractmethod
    def update_contact(self, contact_id: str, data: Dict[str, Any]) -> bool:
        """Update contact data (e.g., lifecycle stage).

        Args:
            contact_id: ID of the contact
            data: Fields to update

        Returns:
            Success status
        """
        pass
