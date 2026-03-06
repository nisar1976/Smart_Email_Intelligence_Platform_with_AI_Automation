"""Entry point for Email Intelligence Agent."""

import logging
from src.config import settings
from src.crm.hubspot_client import HubSpotClient
from src.crm.convertkit_client import ConvertKitClient
from src.integrations.openai_client import EmailGenerationClient
from src.agent.email_generator import EmailGenerator
from src.agent.segmentation import AudienceSegmentor
from src.agent.optimizer import CampaignOptimizer
from src.analytics.tracker import EmailTracker
from src.analytics.reporter import AnalyticsReporter

# Stripe integration is optional
try:
    from src.integrations.stripe_webhook import StripeWebhookHandler
    _stripe_available = True
except ImportError:
    _stripe_available = False

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class EmailIntelligenceAgent:
    """Main orchestrator for Email Intelligence Agent."""

    def __init__(self):
        """Initialize all agent components."""
        logger.info(f"Initializing Email Intelligence Agent (environment: {settings.environment})")

        # Initialize CRM client
        self.crm = self._init_crm()
        logger.info(f"Initialized {settings.crm_provider} CRM client")

        # Initialize OpenAI client
        self.openai_client = EmailGenerationClient()
        logger.info("Initialized OpenAI client")

        # Initialize agent modules
        self.email_generator = EmailGenerator()
        logger.info("Initialized email generator")

        self.segmentor = AudienceSegmentor(self.crm)
        logger.info("Initialized audience segmentor")

        self.optimizer = CampaignOptimizer(self.crm, self.openai_client)
        logger.info("Initialized campaign optimizer")

        # Initialize analytics
        self.tracker = EmailTracker()
        logger.info("Initialized email tracker")

        self.reporter = AnalyticsReporter()
        logger.info("Initialized analytics reporter")

        # Initialize webhook handler (optional)
        if _stripe_available and settings.stripe_webhook_secret:
            self.webhook_handler = StripeWebhookHandler()
            self._register_webhook_handlers()
            logger.info("Initialized Stripe webhook handler")
        else:
            self.webhook_handler = None
            logger.info("Stripe webhook handler disabled (no credentials configured)")

    def _init_crm(self):
        """Initialize CRM client based on configured provider.

        Returns:
            CRM client instance

        Raises:
            ValueError: If CRM provider is not supported
        """
        if settings.crm_provider == "hubspot":
            return HubSpotClient()
        elif settings.crm_provider == "convertkit":
            return ConvertKitClient()
        else:
            raise ValueError(
                f"Unsupported CRM provider: {settings.crm_provider}. "
                f"Supported: hubspot, convertkit"
            )

    def _register_webhook_handlers(self):
        """Register handlers for Stripe webhook events."""
        # These would be implemented to trigger email automation
        logger.info("Registered webhook event handlers")

    async def start_webhook_server(self):
        """Start async webhook server for Stripe events.

        Runs on settings.webhook_port.
        """
        try:
            from fastapi import FastAPI, Request, Response
            import uvicorn

            app = FastAPI(title="OHM Email Agent Webhooks")

            @app.post("/webhooks/stripe")
            async def stripe_webhook(request: Request):
                """Handle Stripe webhook events."""
                if self.webhook_handler is None:
                    return {"status": "disabled", "message": "Stripe webhook handler not configured"}

                payload = await request.body()
                signature = request.headers.get("Stripe-Signature", "")

                try:
                    result = self.webhook_handler.handle_event(payload, signature)
                    return {"status": "success", "result": result}
                except Exception as e:
                    logger.error(f"Webhook processing error: {e}")
                    return Response(
                        content=f"Webhook error: {e}",
                        status_code=400,
                    )

            @app.get("/health")
            async def health():
                """Health check endpoint."""
                return {"status": "healthy"}

            logger.info(f"Starting webhook server on port {settings.webhook_port}")
            await uvicorn.run(app, host="0.0.0.0", port=settings.webhook_port)

        except ImportError:
            logger.warning("FastAPI not installed - webhook server not available")

    def run_segmentation(self):
        """Run audience segmentation."""
        try:
            logger.info("Running audience segmentation...")
            segments = self.segmentor.segment_all()

            for segment_name, contact_ids in segments.items():
                logger.info(f"Segment '{segment_name}': {len(contact_ids)} contacts")

            return segments

        except Exception as e:
            logger.error(f"Error in segmentation: {e}")
            raise

    def generate_campaign_sequence(
        self, segment: str, campaign_type: str, recipient_count: int = 100
    ):
        """Generate a campaign sequence for a segment.

        Args:
            segment: Audience segment
            campaign_type: Campaign type (onboarding, upsell_*, reactivation, cold_outbound)
            recipient_count: Number of recipients

        Returns:
            List of generated Email objects
        """
        try:
            logger.info(
                f"Generating {campaign_type} sequence for segment '{segment}' "
                f"({recipient_count} recipients)"
            )

            # In production, would fetch actual recipient emails from CRM
            recipient_emails = [f"recipient_{i}@example.com" for i in range(recipient_count)]

            emails = self.email_generator.generate_sequence(
                segment=segment,
                campaign_type=campaign_type,
                recipient_emails=recipient_emails,
            )

            logger.info(f"Generated {len(emails)} emails")
            return emails

        except Exception as e:
            logger.error(f"Error generating campaign sequence: {e}")
            raise

    def get_weekly_report(self, analytics_data=None):
        """Generate weekly analytics report.

        Args:
            analytics_data: Optional pre-aggregated analytics data

        Returns:
            WeeklyReport object
        """
        try:
            logger.info("Generating weekly analytics report...")
            report = self.reporter.weekly_report(analytics_data)
            logger.info(
                f"Weekly report: {report.total_emails_sent} emails sent, "
                f"{report.avg_open_rate:.2%} avg open rate"
            )
            return report

        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            raise


def main():
    """Start the Email Intelligence Agent."""
    try:
        # Initialize agent
        agent = EmailIntelligenceAgent()
        logger.info("Email Intelligence Agent ready")

        # Run initial segmentation
        agent.run_segmentation()

        # Start webhook server (if using async)
        logger.info("Agent initialized and ready to handle webhooks")
        logger.info(f"Webhook server running on port {settings.webhook_port}")

        # In production, would run async event loop:
        # import asyncio
        # asyncio.run(agent.start_webhook_server())

    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
