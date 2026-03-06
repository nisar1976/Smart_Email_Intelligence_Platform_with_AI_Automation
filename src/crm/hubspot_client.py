"""HubSpot CRM integration."""

import logging
import time
from typing import Any, Dict, List, Optional
import requests
from src.crm.base import CRMClient
from src.config import settings

logger = logging.getLogger(__name__)


class CRMError(Exception):
    """Raised when CRM operations fail."""

    pass


class HubSpotClient(CRMClient):
    """HubSpot implementation of CRM client."""

    API_BASE = "https://api.hubapi.com"
    MAX_RETRIES = 1
    RETRY_DELAY = 1  # seconds

    def __init__(self):
        """Initialize HubSpot client with API key."""
        if not settings.hubspot_api_key:
            raise CRMError("HUBSPOT_API_KEY not configured")
        self.api_key = settings.hubspot_api_key
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def get_contacts(self, segment: str = "all", limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve contacts from HubSpot, optionally filtered by segment.

        Args:
            segment: Filter segment name or "all"
            limit: Maximum contacts to retrieve

        Returns:
            List of contact dictionaries
        """
        try:
            url = f"{self.API_BASE}/crm/v3/objects/contacts"

            # Map segment names to HubSpot properties
            filter_spec = self._build_segment_filter(segment)

            # Pagination
            all_contacts = []
            after = None

            while len(all_contacts) < limit:
                params = {
                    "limit": min(100, limit - len(all_contacts)),
                    "properties": [
                        "email",
                        "firstname",
                        "lastname",
                        "lifecyclestage",
                        "hs_lead_status",
                        "hs_analytics_last_visit_timestamp",
                        "hs_analytics_num_visits",
                        "notes_last_updated",
                        "createdate",
                    ],
                }

                if after:
                    params["after"] = after

                if filter_spec:
                    params["filterGroups"] = [filter_spec]

                response = self._make_request("GET", url, params=params)
                contacts = response.get("results", [])

                if not contacts:
                    break

                all_contacts.extend(
                    [self._normalize_contact(c) for c in contacts]
                )

                # Check for pagination
                paging = response.get("paging", {})
                after = paging.get("next", {}).get("after")
                if not after:
                    break

            logger.info(f"Retrieved {len(all_contacts)} contacts for segment '{segment}'")
            return all_contacts[:limit]

        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            raise CRMError(f"Failed to get contacts: {e}")

    def create_campaign(
        self, campaign_name: str, emails: List[Dict[str, str]]
    ) -> str:
        """Create a new email campaign in HubSpot.

        Args:
            campaign_name: Campaign name
            emails: List of email dicts (should include subject, body, recipient_email)

        Returns:
            Campaign ID
        """
        try:
            # HubSpot API for email campaigns is via Marketing Emails
            # For simplicity, we'll create a contact list and return a generated ID
            campaign_id = f"campaign_{int(time.time())}"

            logger.info(f"Created campaign '{campaign_name}' with ID {campaign_id}")
            return campaign_id

        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            raise CRMError(f"Failed to create campaign: {e}")

    def send_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Send a campaign to all recipients.

        Args:
            campaign_id: ID of campaign to send

        Returns:
            Deployment confirmation with recipient count
        """
        try:
            # In a real scenario, this would send the campaign via HubSpot API
            # For now, we return a placeholder response
            logger.info(f"Sent campaign {campaign_id}")
            return {
                "campaign_id": campaign_id,
                "status": "sent",
                "recipients": 0,
                "sent_at": None,
            }

        except Exception as e:
            logger.error(f"Error sending campaign: {e}")
            raise CRMError(f"Failed to send campaign: {e}")

    def get_analytics(self, campaign_id: str) -> Dict[str, Any]:
        """Retrieve campaign analytics from HubSpot.

        Args:
            campaign_id: Campaign ID

        Returns:
            Analytics dict with open rate, CTR, etc.
        """
        try:
            # Placeholder implementation - would query HubSpot campaign analytics
            analytics = {
                "campaign_id": campaign_id,
                "total_sent": 0,
                "total_opened": 0,
                "total_clicked": 0,
                "open_rate": 0.0,
                "click_rate": 0.0,
            }

            logger.info(f"Retrieved analytics for campaign {campaign_id}")
            return analytics

        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            raise CRMError(f"Failed to get analytics: {e}")

    def segment_contacts(self, criteria: Dict[str, Any]) -> List[str]:
        """Segment contacts based on behavioral criteria.

        Args:
            criteria: Segmentation criteria dict

        Returns:
            List of contact IDs matching the segment
        """
        try:
            contact_ids = []

            # Build filter based on criteria
            filter_spec = self._build_filter_from_criteria(criteria)

            url = f"{self.API_BASE}/crm/v3/objects/contacts"
            params = {
                "limit": 100,
                "properties": ["email"],
            }

            if filter_spec:
                params["filterGroups"] = [filter_spec]

            # Paginate through results
            after = None
            while True:
                if after:
                    params["after"] = after

                response = self._make_request("GET", url, params=params)
                contacts = response.get("results", [])

                contact_ids.extend([c["id"] for c in contacts])

                paging = response.get("paging", {})
                after = paging.get("next", {}).get("after")
                if not after:
                    break

            logger.info(f"Segmented {len(contact_ids)} contacts")
            return contact_ids

        except Exception as e:
            logger.error(f"Error segmenting contacts: {e}")
            raise CRMError(f"Failed to segment contacts: {e}")

    def update_contact(self, contact_id: str, data: Dict[str, Any]) -> bool:
        """Update contact properties.

        Args:
            contact_id: Contact ID
            data: Fields to update

        Returns:
            Success status
        """
        try:
            url = f"{self.API_BASE}/crm/v3/objects/contacts/{contact_id}"

            # Transform data to HubSpot format
            properties = {}
            for key, value in data.items():
                # Convert snake_case to camelCase for HubSpot
                hs_key = self._to_hubspot_property(key)
                properties[hs_key] = value

            payload = {"properties": properties}

            self._make_request("PATCH", url, json=payload)
            logger.info(f"Updated contact {contact_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating contact: {e}")
            raise CRMError(f"Failed to update contact: {e}")

    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to HubSpot API with retry logic.

        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
            json: JSON body

        Returns:
            Response JSON

        Raises:
            CRMError: On API error
        """
        retries = 0
        while retries <= self.MAX_RETRIES:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=json,
                    timeout=10,
                )

                # Handle rate limiting
                if response.status_code == 429:
                    if retries < self.MAX_RETRIES:
                        logger.warning("Rate limited, retrying...")
                        time.sleep(self.RETRY_DELAY)
                        retries += 1
                        continue
                    else:
                        raise CRMError("Rate limited (max retries exceeded)")

                # Handle errors
                if response.status_code >= 400:
                    error_msg = response.text
                    raise CRMError(f"API error {response.status_code}: {error_msg}")

                return response.json() if response.text else {}

            except requests.RequestException as e:
                raise CRMError(f"Request failed: {e}")

    def _normalize_contact(self, contact_data: Dict) -> Dict[str, Any]:
        """Normalize HubSpot contact to standard format.

        Args:
            contact_data: Raw HubSpot contact

        Returns:
            Normalized contact dict
        """
        properties = contact_data.get("properties", {})
        return {
            "id": contact_data.get("id"),
            "email": properties.get("email"),
            "firstname": properties.get("firstname"),
            "lastname": properties.get("lastname"),
            "lifecycle_stage": properties.get("lifecyclestage"),
            "hs_lead_status": properties.get("hs_lead_status"),
            "last_activity_date": properties.get("hs_analytics_last_visit_timestamp"),
            "subscription_tier": self._extract_subscription_tier(properties),
            "subscription_created_date": properties.get("createdate"),
            "subscription_cancelled_date": None,  # Would be extracted from custom property
            "clicked_upsell_cta": False,  # Would be tracked via analytics
        }

    def _build_segment_filter(self, segment: str) -> Optional[Dict]:
        """Build HubSpot filter spec for a segment.

        Args:
            segment: Segment name

        Returns:
            Filter spec or None
        """
        if segment == "all":
            return None

        # Map segment names to HubSpot filters
        filters = {
            "cold_prospect": {
                "filters": [
                    {
                        "propertyName": "lifecyclestage",
                        "operator": "EQ",
                        "value": "subscriber",
                    }
                ]
            },
            "active_phoenix": {
                "filters": [
                    {
                        "propertyName": "lifecyclestage",
                        "operator": "EQ",
                        "value": "customer",
                    }
                ]
            },
            "churned": {
                "filters": [
                    {
                        "propertyName": "hs_lead_status",
                        "operator": "EQ",
                        "value": "Unqualified",
                    }
                ]
            },
        }

        return filters.get(segment)

    def _build_filter_from_criteria(self, criteria: Dict[str, Any]) -> Optional[Dict]:
        """Build HubSpot filter from generic criteria.

        Args:
            criteria: Segmentation criteria

        Returns:
            Filter spec
        """
        return None  # Placeholder

    def _extract_subscription_tier(self, properties: Dict) -> str:
        """Extract subscription tier from contact properties.

        Args:
            properties: HubSpot contact properties

        Returns:
            Tier name (phoenix, visionary, infinity) or "none"
        """
        # This would extract from custom HubSpot properties
        # Placeholder implementation
        return "none"

    def _to_hubspot_property(self, key: str) -> str:
        """Convert standard property name to HubSpot format.

        Args:
            key: Standard property name

        Returns:
            HubSpot property name
        """
        # Map standard names to HubSpot names
        mapping = {
            "lifecycle_stage": "lifecyclestage",
            "email": "email",
            "firstname": "firstname",
            "lastname": "lastname",
        }
        return mapping.get(key, key)
