"""Settings management endpoints."""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

SETTINGS_FILE = Path("settings_store.json")


class SettingsUpdate(BaseModel):
    """Settings update request model."""
    openai_api_key: Optional[str] = None
    gmail_email: Optional[str] = None
    gmail_app_password: Optional[str] = None
    crm_provider: Optional[str] = None
    crm_api_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None


class SettingsResponse(BaseModel):
    """Settings response model (passwords masked)."""
    openai_api_key: str = ""
    gmail_email: str = ""
    gmail_app_password: str = ""
    crm_provider: str = "hubspot"
    crm_api_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""


def _load_settings() -> dict:
    """Load settings from file."""
    if SETTINGS_FILE.exists():
        return json.loads(SETTINGS_FILE.read_text())
    return {}


def _save_settings(settings: dict) -> None:
    """Save settings to file."""
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2))


def _mask_password(password: str) -> str:
    """Mask password for display."""
    if not password:
        return ""
    if len(password) <= 4:
        return "*" * len(password)
    return password[:2] + "*" * (len(password) - 4) + password[-2:]


@router.post("/")
async def update_settings(settings_update: SettingsUpdate):
    """Update settings (OpenAI key, Gmail credentials, etc.).

    Args:
        settings_update: Settings to update

    Returns:
        Updated settings (with passwords masked)
    """
    try:
        # Load current settings
        settings = _load_settings()

        # Update provided settings
        if settings_update.openai_api_key:
            settings["openai_api_key"] = settings_update.openai_api_key
        if settings_update.gmail_email:
            settings["gmail_email"] = settings_update.gmail_email
        if settings_update.gmail_app_password:
            settings["gmail_app_password"] = settings_update.gmail_app_password
        if settings_update.crm_provider:
            settings["crm_provider"] = settings_update.crm_provider
        if settings_update.crm_api_key:
            settings["crm_api_key"] = settings_update.crm_api_key
        if settings_update.stripe_secret_key:
            settings["stripe_secret_key"] = settings_update.stripe_secret_key
        if settings_update.stripe_webhook_secret:
            settings["stripe_webhook_secret"] = settings_update.stripe_webhook_secret

        # Save settings
        _save_settings(settings)

        # Update environment variables
        import os
        if settings_update.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings_update.openai_api_key
        if settings_update.gmail_email:
            os.environ["GMAIL_EMAIL"] = settings_update.gmail_email
        if settings_update.gmail_app_password:
            os.environ["GMAIL_APP_PASSWORD"] = settings_update.gmail_app_password
        if settings_update.stripe_secret_key:
            os.environ["STRIPE_SECRET_KEY"] = settings_update.stripe_secret_key
        if settings_update.stripe_webhook_secret:
            os.environ["STRIPE_WEBHOOK_SECRET"] = settings_update.stripe_webhook_secret

        return {
            "message": "Settings updated successfully",
            "settings": _get_masked_settings()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.get("/")
async def get_settings():
    """Get current settings (with passwords masked).

    Returns:
        Current settings configuration
    """
    try:
        return _get_masked_settings()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch settings: {str(e)}")


def _get_masked_settings() -> dict:
    """Get settings with passwords masked."""
    settings = _load_settings()

    return {
        "openai_api_key": _mask_password(settings.get("openai_api_key", "")),
        "gmail_email": settings.get("gmail_email", ""),
        "gmail_app_password": _mask_password(settings.get("gmail_app_password", "")),
        "crm_provider": settings.get("crm_provider", "hubspot"),
        "crm_api_key": _mask_password(settings.get("crm_api_key", "")),
        "stripe_secret_key": _mask_password(settings.get("stripe_secret_key", "")),
        "stripe_webhook_secret": _mask_password(settings.get("stripe_webhook_secret", "")),
        "configured": bool(settings.get("openai_api_key"))
    }


@router.post("/test")
async def test_settings():
    """Test if settings are valid (test API connections).

    Returns:
        Test results for each configured service
    """
    try:
        settings = _load_settings()
        results = {}

        # Test OpenAI
        if settings.get("openai_api_key"):
            try:
                import openai
                openai.api_key = settings["openai_api_key"]
                # Try a simple request
                client = openai.OpenAI(api_key=settings["openai_api_key"])
                client.models.list()
                results["openai"] = "✓ Valid"
            except Exception as e:
                results["openai"] = f"✗ Invalid: {str(e)}"
        else:
            results["openai"] = "⚠ Not configured"

        # Test Gmail
        if settings.get("gmail_email") and settings.get("gmail_app_password"):
            try:
                import smtplib
                server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=5)
                server.login(settings["gmail_email"], settings["gmail_app_password"])
                server.quit()
                results["gmail"] = "✓ Valid"
            except Exception as e:
                results["gmail"] = f"✗ Invalid: {str(e)}"
        else:
            results["gmail"] = "⚠ Not configured"

        # Test CRM
        results["crm"] = "ℹ Configured"

        # Test Stripe
        if settings.get("stripe_secret_key"):
            results["stripe"] = "✓ Configured"
        else:
            results["stripe"] = "⚠ Not configured"

        return {
            "message": "Settings test completed",
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test settings: {str(e)}")
