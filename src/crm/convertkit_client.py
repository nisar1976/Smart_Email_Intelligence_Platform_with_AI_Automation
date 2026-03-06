"""ConvertKit CRM integration."""

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


class ConvertKitClient(CRMClient):
    """ConvertKit implementation of CRM client."""

    API_BASE = "https://api.convertkit.com/v3"
    MAX_RETRIES = 1
    RETRY_DELAY = 1  # seconds
    BATCH_SIZE = 1000  # ConvertKit API batch size for subscribers

    def __init__(self):
        """Initialize ConvertKit client with API key."""
        if not settings.convertkit_api_key:
            raise CRMError("CONVERTKIT_API_KEY not configured")
        self.api_key = settings.convertkit_api_key

    def get_contacts(self, segment: str = "all", limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve subscribers from ConvertKit, optionally filtered by segment/tag.

        Args:
            segment: Filter segment name or "all"
            limit: Maximum contacts to retrieve

        Returns:
            List of contact dictionaries
        """
        try:
            all_contacts = []

            # ConvertKit uses tags for segmentation
            tag_id = None
            if segment != "all":
                tag_id = self._get_tag_id(segment)

            # Retrieve subscribers in batches
            page = 1
            while len(all_contacts) < limit:
                params = {
                    "api_key": self.api_key,
                    "limit": min(self.BATCH_SIZE, limit - len(all_contacts)),
                    "page": page,
                }

                url = f"{self.API_BASE}/subscribers"
                if tag_id:
                    url = f"{self.API_BASE}/tags/{tag_id}/subscribers"

                response = self._make_request("GET", url, params=params)
                subscribers = response.get("subscribers", [])

                if not subscribers:
                    break

                all_contacts.extend(
                    [self._normalize_subscriber(s) for s in subscribers]
                )

                page += 1

            logger.info(
                f"Retrieved {len(all_contacts)} subscribers for segment '{segment}'"
            )
            return all_contacts[:limit]

        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            raise CRMError(f"Failed to get contacts: {e}")

    def create_campaign(
        self, campaign_name: str, emails: List[Dict[str, str]]
    ) -> str:
        """Create a new broadcast campaign in ConvertKit.

        Args:
            campaign_name: Campaign name
            emails: List of email dicts (should include subject, body, recipient_email)

        Returns:
            Campaign ID
        """
        try:
            # ConvertKit Broadcasts API
            payload = {
                "broadcast": {
                    "name": campaign_name,
                    "subject": emails[0].get("subject", "") if emails else "",
                    "body": emails[0].get("body", "") if emails else "",
                    "publish_now": False,  # Draft until explicitly sent
                }
            }

            url = f"{self.API_BASE}/broadcasts"
            params = {"api_key": self.api_key}

            response = self._make_request("POST", url, json=payload, params=params)
            campaign_id = response.get("broadcast", {}).get("id")

            if not campaign_id:
                raise CRMError("Failed to create broadcast - no ID returned")

            logger.info(f"Created broadcast '{campaign_name}' with ID {campaign_id}")
            return str(campaign_id)

        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            raise CRMError(f"Failed to create campaign: {e}")

    def send_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Send a broadcast campaign to all subscribers.

        Args:
            campaign_id: ID of broadcast to send

        Returns:
            Deployment confirmation
        """
        try:
            # Mark broadcast as published (which sends it)
            url = f"{self.API_BASE}/broadcasts/{campaign_id}/publish"
            params = {"api_key": self.api_key}

            response = self._make_request("POST", url, params=params)
            broadcast = response.get("broadcast", {})

            logger.info(f"Sent broadcast {campaign_id}")
            return {
                "campaign_id": campaign_id,
                "status": "sent",
                "recipients": broadcast.get("total_sent", 0),
                "sent_at": broadcast.get("published_at"),
            }

        except Exception as e:
            logger.error(f"Error sending campaign: {e}")
            raise CRMError(f"Failed to send campaign: {e}")

    def get_analytics(self, campaign_id: str) -> Dict[str, Any]:
        """Retrieve broadcast analytics from ConvertKit.

        Args:
            campaign_id: Broadcast ID

        Returns:
            Analytics dict with open rate, CTR, etc.
        """
        try:
            url = f"{self.API_BASE}/broadcasts/{campaign_id}"
            params = {"api_key": self.api_key}

            response = self._make_request("GET", url, params=params)
            broadcast = response.get("broadcast", {})

            total_sent = broadcast.get("total_sent", 0)
            total_open = broadcast.get("total_open", 0)
            total_click = broadcast.get("total_click", 0)

            analytics = {
                "campaign_id": campaign_id,
                "total_sent": total_sent,
                "total_opened": total_open,
                "total_clicked": total_click,
                "open_rate": total_open / total_sent if total_sent > 0 else 0,
                "click_rate": total_click / total_sent if total_sent > 0 else 0,
            }

            logger.info(f"Retrieved analytics for broadcast {campaign_id}")
            return analytics

        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            raise CRMError(f"Failed to get analytics: {e}")

    def segment_contacts(self, criteria: Dict[str, Any]) -> List[str]:
        """Segment contacts based on behavioral criteria (tags in ConvertKit).

        Args:
            criteria: Segmentation criteria dict

        Returns:
            List of subscriber IDs matching the segment
        """
        try:
            subscriber_ids = []

            # Build tag filter based on criteria
            tag_id = self._get_tag_id(criteria.get("tag", ""))

            if not tag_id:
                logger.warning("No tag specified for segmentation")
                return []

            url = f"{self.API_BASE}/tags/{tag_id}/subscribers"
            params = {
                "api_key": self.api_key,
                "limit": self.BATCH_SIZE,
            }

            page = 1
            while True:
                params["page"] = page
                response = self._make_request("GET", url, params=params)
                subscribers = response.get("subscribers", [])

                subscriber_ids.extend([s["id"] for s in subscribers])

                if len(subscribers) < self.BATCH_SIZE:
                    break

                page += 1

            logger.info(f"Segmented {len(subscriber_ids)} contacts")
            return [str(sid) for sid in subscriber_ids]

        except Exception as e:
            logger.error(f"Error segmenting contacts: {e}")
            raise CRMError(f"Failed to segment contacts: {e}")

    def update_contact(self, contact_id: str, data: Dict[str, Any]) -> bool:
        """Update subscriber properties in ConvertKit.

        Args:
            contact_id: Subscriber ID
            data: Fields to update

        Returns:
            Success status
        """
        try:
            url = f"{self.API_BASE}/subscribers/{contact_id}"
            params = {"api_key": self.api_key}

            # ConvertKit subscriber update payload
            payload = {
                "subscriber": {
                    "email_address": data.get("email"),
                    "first_name": data.get("firstname"),
                    "fields": self._build_custom_fields(data),
                }
            }

            self._make_request("PUT", url, json=payload, params=params)
            logger.info(f"Updated subscriber {contact_id}")
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
        """Make HTTP request to ConvertKit API with retry logic.

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

    def _normalize_subscriber(self, subscriber_data: Dict) -> Dict[str, Any]:
        """Normalize ConvertKit subscriber to standard format.

        Args:
            subscriber_data: Raw ConvertKit subscriber

        Returns:
            Normalized contact dict
        """
        return {
            "id": subscriber_data.get("id"),
            "email": subscriber_data.get("email_address"),
            "firstname": subscriber_data.get("first_name"),
            "lastname": subscriber_data.get("last_name"),
            "lifecycle_stage": self._get_lifecycle_stage(subscriber_data),
            "hs_lead_status": None,  # ConvertKit doesn't have this concept
            "last_activity_date": subscriber_data.get("updated_at"),
            "subscription_tier": self._extract_subscription_tier(subscriber_data),
            "subscription_created_date": subscriber_data.get("created_at"),
            "subscription_cancelled_date": None,
            "clicked_upsell_cta": False,  # Would be tracked via analytics
        }

    def _get_tag_id(self, tag_name: str) -> Optional[int]:
        """Get ConvertKit tag ID by name.

        Args:
            tag_name: Tag name

        Returns:
            Tag ID or None
        """
        try:
            url = f"{self.API_BASE}/tags"
            params = {"api_key": self.api_key}

            response = self._make_request("GET", url, params=params)
            tags = response.get("tags", [])

            for tag in tags:
                if tag.get("name", "").lower() == tag_name.lower():
                    return tag.get("id")

            logger.warning(f"Tag '{tag_name}' not found")
            return None

        except Exception as e:
            logger.error(f"Error getting tag ID: {e}")
            return None

    def _get_lifecycle_stage(self, subscriber: Dict) -> str:
        """Extract lifecycle stage from ConvertKit subscriber.

        Args:
            subscriber: ConvertKit subscriber data

        Returns:
            Lifecycle stage
        """
        # ConvertKit doesn't have explicit lifecycle stages
        # Use created_at to infer
        return "subscriber"

    def _extract_subscription_tier(self, subscriber: Dict) -> str:
        """Extract subscription tier from ConvertKit subscriber.

        Args:
            subscriber: ConvertKit subscriber data

        Returns:
            Tier name (phoenix, visionary, infinity) or "none"
        """
        # This would extract from ConvertKit custom fields/tags
        # Placeholder implementation
        return "none"

    def _build_custom_fields(self, data: Dict[str, Any]) -> Dict:
        """Build ConvertKit custom fields dict from standard data.

        Args:
            data: Standard data dict

        Returns:
            Custom fields dict for ConvertKit
        """
        return {}
