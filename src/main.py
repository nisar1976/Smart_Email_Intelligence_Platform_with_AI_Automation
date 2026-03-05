"""Entry point for Email Intelligence Agent."""

import logging
from src.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Start the Email Intelligence Agent."""
    logger.info(f"Starting Email Intelligence Agent (environment: {settings.environment})")
    logger.info(f"Using CRM provider: {settings.crm_provider}")

    # TODO: Initialize CRM client
    # TODO: Start webhook server for Stripe and website behavior events
    # TODO: Initialize background tasks for weekly optimization
    # TODO: Start main agent loop

    logger.info("Agent initialized and running...")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
