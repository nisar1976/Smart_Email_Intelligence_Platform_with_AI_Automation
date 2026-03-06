"""Audience segmentation endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Dict, List
from src.config import settings
from src.agent.segmentation import AudienceSegmentor

router = APIRouter()


def _is_crm_configured() -> bool:
    """Check if CRM is properly configured (not using placeholder keys).

    Returns:
        True if CRM is configured with valid API keys, False otherwise
    """
    if settings.crm_provider == "hubspot":
        key = settings.hubspot_api_key
    elif settings.crm_provider == "convertkit":
        key = settings.convertkit_api_key
    else:
        return False

    # Check if key exists and is not a placeholder
    return bool(key) and not key.startswith("your-")


@router.get("/")
async def get_segments():
    """Get all audience segments with contact counts.

    Returns:
        Dict mapping segment names to contact counts
    """
    try:
        # Check if CRM is properly configured
        if not _is_crm_configured():
            # Return empty segments with all names defined
            segment_data = {}
            for segment_name in AudienceSegmentor.SEGMENTS.keys():
                segment_data[segment_name] = {
                    "name": segment_name,
                    "contact_count": 0,
                    "contacts": [],
                    "_crm_status": "not_configured"
                }
            return segment_data

        # Get CRM client based on settings
        if settings.crm_provider == "hubspot":
            from src.crm.hubspot_client import HubSpotClient
            crm = HubSpotClient()
        elif settings.crm_provider == "convertkit":
            from src.crm.convertkit_client import ConvertKitClient
            crm = ConvertKitClient()
        else:
            raise ValueError(f"Unknown CRM provider: {settings.crm_provider}")

        # Initialize segmentor with CRM client
        segmentor = AudienceSegmentor(crm_client=crm)

        # Get segments
        segments = segmentor.segment_all()

        # Format response
        segment_data = {}
        for segment_name, contact_ids in segments.items():
            segment_data[segment_name] = {
                "name": segment_name,
                "contact_count": len(contact_ids),
                "contacts": contact_ids[:10]  # Show first 10 contact IDs
            }

        return segment_data

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch segments: {str(e)}")


@router.get("/{segment_name}")
async def get_segment(segment_name: str):
    """Get details for a specific segment.

    Args:
        segment_name: Name of segment

    Returns:
        Segment details with contact list
    """
    try:
        # Validate segment name exists
        if segment_name not in AudienceSegmentor.SEGMENTS:
            raise ValueError(f"Segment not found: {segment_name}")

        # Check if CRM is properly configured
        if not _is_crm_configured():
            return {
                "name": segment_name,
                "contact_count": 0,
                "contacts": [],
                "_crm_status": "not_configured"
            }

        # Get CRM client
        if settings.crm_provider == "hubspot":
            from src.crm.hubspot_client import HubSpotClient
            crm = HubSpotClient()
        elif settings.crm_provider == "convertkit":
            from src.crm.convertkit_client import ConvertKitClient
            crm = ConvertKitClient()
        else:
            raise ValueError(f"Unknown CRM provider: {settings.crm_provider}")

        # Initialize segmentor with CRM client
        segmentor = AudienceSegmentor(crm_client=crm)

        segments = segmentor.segment_all()

        contact_ids = segments[segment_name]

        return {
            "name": segment_name,
            "contact_count": len(contact_ids),
            "contacts": contact_ids
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch segment: {str(e)}")
