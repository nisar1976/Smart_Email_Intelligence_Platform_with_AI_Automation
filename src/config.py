"""Configuration management for Email Intelligence Agent.

Environment variables are loaded from .env file using python-dotenv.
Never commit .env files or hardcode credentials.
"""

import os
from typing import Literal
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_model: str = "gpt-4"

    # CRM Configuration
    crm_provider: Literal["hubspot", "convertkit"] = "hubspot"
    hubspot_api_key: str = Field(default="", env="HUBSPOT_API_KEY")
    convertkit_api_key: str = Field(default="", env="CONVERTKIT_API_KEY")

    # Stripe Configuration (for webhook data)
    stripe_api_key: str = Field(default="", env="STRIPE_API_KEY")
    stripe_webhook_secret: str = Field(default="", env="STRIPE_WEBHOOK_SECRET")

    # Email Configuration
    sender_email: str = Field(default="no-reply@example.com", env="SENDER_EMAIL")
    sender_name: str = Field(default="OHM Team", env="SENDER_NAME")

    # Gmail Configuration (for SMTP sending)
    gmail_email: str = Field(default="", env="GMAIL_EMAIL")
    gmail_app_password: str = Field(default="", env="GMAIL_APP_PASSWORD")

    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"

    # Database (optional)
    database_url: str = Field(default="sqlite:///./email_agent.db", env="DATABASE_URL")

    # Webhook Configuration
    webhook_port: int = Field(default=8000, env="WEBHOOK_PORT")

    model_config = {"env_file": ".env", "case_sensitive": False}

    def validate_crm_config(self) -> None:
        """Validate that required CRM credentials are provided."""
        if self.crm_provider == "hubspot" and not self.hubspot_api_key:
            raise ValueError(
                "HUBSPOT_API_KEY environment variable is required when using HubSpot"
            )
        if self.crm_provider == "convertkit" and not self.convertkit_api_key:
            raise ValueError(
                "CONVERTKIT_API_KEY environment variable is required when using ConvertKit"
            )

    def validate_stripe_config(self) -> None:
        """Validate that Stripe credentials are provided if using webhooks."""
        if self.stripe_api_key and not self.stripe_webhook_secret:
            raise ValueError(
                "STRIPE_WEBHOOK_SECRET must be set if STRIPE_API_KEY is configured"
            )


# Global settings instance (lazy initialization - do not validate CRM at import time)
settings = Settings()
