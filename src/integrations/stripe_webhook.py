"""Stripe webhook handler for email automation triggers."""

import logging
import hmac
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from src.models.webhook import StripeEvent
from src.config import settings

logger = logging.getLogger(__name__)


class WebhookValidationError(Exception):
    """Raised when webhook signature validation fails."""

    pass


class StripeWebhookHandler:
    """Handles Stripe webhook events and triggers email automation."""

    # Stripe event types
    EVENT_TYPES = {
        "customer.subscription.created": "subscription_created",
        "customer.subscription.updated": "subscription_updated",
        "customer.subscription.deleted": "subscription_deleted",
        "invoice.payment_failed": "payment_failed",
        "invoice.payment_succeeded": "payment_succeeded",
    }

    def __init__(self):
        """Initialize webhook handler."""
        self.secret = settings.stripe_webhook_secret
        self._init_event_db()
        self.event_handlers: Dict[str, list[Callable]] = {
            event_type: [] for event_type in self.EVENT_TYPES.keys()
        }

    def _init_event_db(self) -> None:
        """Initialize SQLite table for deduplication of webhook events."""
        try:
            if settings.database_url.startswith("sqlite:"):
                import sqlite3
                from urllib.parse import urlparse

                db_path = urlparse(settings.database_url).path
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS stripe_events (
                        event_id TEXT PRIMARY KEY,
                        event_type TEXT,
                        customer_id TEXT,
                        subscription_id TEXT,
                        processed BOOLEAN DEFAULT 0,
                        received_at DATETIME,
                        processed_at DATETIME
                    )
                    """
                )

                conn.commit()
                conn.close()
                logger.info("Stripe webhook event database initialized")

        except Exception as e:
            logger.error(f"Error initializing webhook database: {e}")

    def handle_event(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Validate and process a Stripe webhook event.

        Args:
            payload: Raw webhook payload (bytes)
            signature: Stripe signature header

        Returns:
            Processing result dict

        Raises:
            WebhookValidationError: If signature validation fails
        """
        try:
            # Validate signature
            if not self._validate_signature(payload, signature):
                raise WebhookValidationError("Invalid webhook signature")

            # Parse event
            event_data = json.loads(payload)
            event_id = event_data.get("id")
            event_type = event_data.get("type")

            logger.info(f"Processing Stripe webhook: {event_type} (ID: {event_id})")

            # Check for deduplication
            if self._is_event_processed(event_id):
                logger.info(f"Event {event_id} already processed, skipping")
                return {"status": "deduplicated", "event_id": event_id}

            # Extract data
            stripe_event = self._parse_stripe_event(event_data)

            # Route to appropriate handler
            result = self._route_event(stripe_event, event_data)

            # Mark as processed
            self._mark_event_processed(event_id, event_type)

            return result

        except WebhookValidationError as e:
            logger.error(f"Webhook validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise

    def register_event_handler(
        self, event_type: str, handler: Callable
    ) -> None:
        """Register a handler for a specific event type.

        Args:
            event_type: Stripe event type (e.g., customer.subscription.created)
            handler: Callable that processes the event
        """
        if event_type not in self.event_handlers:
            logger.warning(f"Unknown event type: {event_type}")
            return

        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type}")

    def _validate_signature(self, payload: bytes, signature: str) -> bool:
        """Validate Stripe webhook signature.

        Args:
            payload: Raw webhook payload
            signature: Stripe signature header (t=...,v1=...)

        Returns:
            True if signature is valid
        """
        try:
            if not self.secret:
                logger.warning("No Stripe webhook secret configured")
                return False

            # Parse signature header
            parts = signature.split(",")
            timestamp = None
            hash_value = None

            for part in parts:
                if part.startswith("t="):
                    timestamp = int(part[2:])
                elif part.startswith("v1="):
                    hash_value = part[3:]

            if not timestamp or not hash_value:
                logger.error("Invalid signature format")
                return False

            # Check timestamp freshness (within 5 minutes)
            current_time = int(time.time())
            if abs(current_time - timestamp) > 300:
                logger.error("Webhook signature too old")
                return False

            # Compute expected hash
            signed_content = f"{timestamp}.{payload.decode()}"
            expected_hash = hmac.new(
                self.secret.encode(),
                signed_content.encode(),
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(hash_value, expected_hash)

        except Exception as e:
            logger.error(f"Error validating signature: {e}")
            return False

    def _parse_stripe_event(self, event_data: Dict) -> StripeEvent:
        """Parse Stripe event into StripeEvent model.

        Args:
            event_data: Raw Stripe event dict

        Returns:
            StripeEvent model instance
        """
        event_object = event_data.get("data", {}).get("object", {})

        return StripeEvent(
            event_id=event_data.get("id"),
            event_type=event_data.get("type"),
            customer_id=event_object.get("customer"),
            subscription_id=event_object.get("id") if "subscription" in event_data.get("type", "") else None,
            tier=self._extract_tier_from_event(event_object),
            received_at=datetime.fromtimestamp(event_data.get("created", 0)),
            processed=False,
        )

    def _route_event(
        self, stripe_event: StripeEvent, event_data: Dict
    ) -> Dict[str, Any]:
        """Route event to appropriate handler based on type.

        Args:
            stripe_event: Parsed StripeEvent
            event_data: Raw Stripe event dict

        Returns:
            Handler result dict
        """
        event_type = stripe_event.event_type

        if event_type == "customer.subscription.created":
            return self._handle_subscription_created(stripe_event, event_data)
        elif event_type == "customer.subscription.updated":
            return self._handle_subscription_updated(stripe_event, event_data)
        elif event_type == "customer.subscription.deleted":
            return self._handle_subscription_deleted(stripe_event, event_data)
        elif event_type == "invoice.payment_failed":
            return self._handle_payment_failed(stripe_event, event_data)
        elif event_type == "invoice.payment_succeeded":
            return self._handle_payment_succeeded(stripe_event, event_data)
        else:
            logger.warning(f"Unhandled event type: {event_type}")
            return {"status": "unhandled"}

    def _handle_subscription_created(
        self, stripe_event: StripeEvent, event_data: Dict
    ) -> Dict[str, Any]:
        """Handle subscription creation - trigger onboarding sequence.

        Args:
            stripe_event: Parsed event
            event_data: Raw event

        Returns:
            Result dict
        """
        logger.info(
            f"Subscription created: customer={stripe_event.customer_id}, "
            f"tier={stripe_event.tier}"
        )

        # Call registered handlers
        for handler in self.event_handlers.get("customer.subscription.created", []):
            try:
                handler(stripe_event, event_data)
            except Exception as e:
                logger.error(f"Handler error: {e}")

        return {
            "status": "triggered",
            "sequence": "onboarding",
            "customer_id": stripe_event.customer_id,
        }

    def _handle_subscription_updated(
        self, stripe_event: StripeEvent, event_data: Dict
    ) -> Dict[str, Any]:
        """Handle subscription update - trigger upgrade confirmations.

        Args:
            stripe_event: Parsed event
            event_data: Raw event

        Returns:
            Result dict
        """
        event_object = event_data.get("data", {}).get("object", {})
        previous_tier = self._extract_tier_from_event(
            event_data.get("data", {}).get("previous_attributes", {})
        )

        logger.info(
            f"Subscription updated: customer={stripe_event.customer_id}, "
            f"{previous_tier} -> {stripe_event.tier}"
        )

        # Call registered handlers
        for handler in self.event_handlers.get("customer.subscription.updated", []):
            try:
                handler(stripe_event, event_data)
            except Exception as e:
                logger.error(f"Handler error: {e}")

        return {
            "status": "triggered",
            "sequence": "upgrade_confirmation",
            "from_tier": previous_tier,
            "to_tier": stripe_event.tier,
        }

    def _handle_subscription_deleted(
        self, stripe_event: StripeEvent, event_data: Dict
    ) -> Dict[str, Any]:
        """Handle subscription cancellation - mark churned, schedule reactivation.

        Args:
            stripe_event: Parsed event
            event_data: Raw event

        Returns:
            Result dict
        """
        logger.info(f"Subscription deleted: customer={stripe_event.customer_id}")

        # Call registered handlers
        for handler in self.event_handlers.get("customer.subscription.deleted", []):
            try:
                handler(stripe_event, event_data)
            except Exception as e:
                logger.error(f"Handler error: {e}")

        return {
            "status": "triggered",
            "sequence": "reactivation",
            "delay_days": 7,
            "customer_id": stripe_event.customer_id,
        }

    def _handle_payment_failed(
        self, stripe_event: StripeEvent, event_data: Dict
    ) -> Dict[str, Any]:
        """Handle payment failure - trigger payment recovery sequence.

        Args:
            stripe_event: Parsed event
            event_data: Raw event

        Returns:
            Result dict
        """
        logger.info(f"Payment failed: customer={stripe_event.customer_id}")

        # Call registered handlers
        for handler in self.event_handlers.get("invoice.payment_failed", []):
            try:
                handler(stripe_event, event_data)
            except Exception as e:
                logger.error(f"Handler error: {e}")

        return {
            "status": "triggered",
            "sequence": "payment_recovery",
            "emails": 2,  # 2-email sequence: immediate + day 3
        }

    def _handle_payment_succeeded(
        self, stripe_event: StripeEvent, event_data: Dict
    ) -> Dict[str, Any]:
        """Handle successful payment - clear payment failure flag.

        Args:
            stripe_event: Parsed event
            event_data: Raw event

        Returns:
            Result dict
        """
        logger.info(f"Payment succeeded: customer={stripe_event.customer_id}")

        # Call registered handlers
        for handler in self.event_handlers.get("invoice.payment_succeeded", []):
            try:
                handler(stripe_event, event_data)
            except Exception as e:
                logger.error(f"Handler error: {e}")

        return {"status": "processed", "customer_id": stripe_event.customer_id}

    def _extract_tier_from_event(self, event_object: Dict) -> Optional[str]:
        """Extract subscription tier from Stripe event object.

        Args:
            event_object: Stripe subscription object

        Returns:
            Tier name (phoenix, visionary, infinity) or None
        """
        if not event_object:
            return None

        # Stripe metadata or product name would contain tier
        items = event_object.get("items", {}).get("data", [])
        if items:
            product_id = items[0].get("product")
            # Map product IDs to tiers (would be configured)
            tier_map = {
                "prod_phoenix": "phoenix",
                "prod_visionary": "visionary",
                "prod_infinity": "infinity",
            }
            return tier_map.get(product_id)

        return None

    def _is_event_processed(self, event_id: str) -> bool:
        """Check if event has already been processed (deduplication).

        Args:
            event_id: Stripe event ID

        Returns:
            True if already processed
        """
        try:
            if settings.database_url.startswith("sqlite:"):
                import sqlite3
                from urllib.parse import urlparse

                db_path = urlparse(settings.database_url).path
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT processed FROM stripe_events WHERE event_id = ?",
                    (event_id,),
                )
                result = cursor.fetchone()
                conn.close()

                return result is not None and result[0]

            return False

        except Exception as e:
            logger.error(f"Error checking event deduplication: {e}")
            return False

    def _mark_event_processed(
        self, event_id: str, event_type: str, customer_id: str = None, subscription_id: str = None
    ) -> None:
        """Mark event as processed in database.

        Args:
            event_id: Stripe event ID
            event_type: Stripe event type
            customer_id: Customer ID (optional)
            subscription_id: Subscription ID (optional)
        """
        try:
            if settings.database_url.startswith("sqlite:"):
                import sqlite3
                from urllib.parse import urlparse

                db_path = urlparse(settings.database_url).path
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO stripe_events
                    (event_id, event_type, customer_id, subscription_id, processed, received_at, processed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (event_id, event_type, customer_id, subscription_id, 1, datetime.now(), datetime.now()),
                )

                conn.commit()
                conn.close()

        except Exception as e:
            logger.error(f"Error marking event processed: {e}")
