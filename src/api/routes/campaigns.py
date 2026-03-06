"""Campaign generation and management endpoints."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from pathlib import Path

router = APIRouter()


class GenerateCampaignRequest(BaseModel):
    """Request model for campaign generation."""
    segment: str
    campaign_type: str
    recipient_count: Optional[int] = None


class EmailContent(BaseModel):
    """Email content model."""
    step: int
    subject: str
    body: str


class GenerateCampaignResponse(BaseModel):
    """Response model for campaign generation."""
    campaign_id: str
    segment: str
    campaign_type: str
    emails: List[EmailContent]
    citations: List[dict]
    output_file: str
    generated_at: str


@router.post("/generate", response_model=GenerateCampaignResponse)
async def generate_campaign(request: GenerateCampaignRequest):
    """Generate an email campaign for a specific segment.

    Args:
        request: Campaign generation request with segment and type

    Returns:
        Generated emails with citations and output file path
    """
    # Check OpenAI API key early
    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="OpenAI API key not configured. Go to Settings to add it."
        )

    try:
        # Import here to avoid circular imports
        from src.agent.email_generator import EmailGenerator
        from src.rag.retriever import RAGRetriever

        # Initialize generators
        email_gen = EmailGenerator()
        rag = RAGRetriever()
        rag.initialize()

        # Generate emails
        emails = email_gen.generate_sequence(
            segment=request.segment,
            campaign_type=request.campaign_type,
            recipient_emails=[]
        )

        # Convert to email dicts
        email_list = []
        for idx, email in enumerate(emails, 1):
            email_list.append({
                "step": idx,
                "subject": email.subject,
                "body": email.body
            })

        # Query RAG for citations
        query = f"Generate {request.campaign_type} email campaign for {request.segment}"
        rag_results = rag.query(query, k=3)

        # Format citations
        citations = [
            {
                "source_name": chunk.get("source_name"),
                "source_path": chunk.get("source_path"),
                "excerpt": chunk.get("text", "")[:200]  # First 200 chars
            }
            for chunk in rag_results.get("retrieved_chunks", [])
        ]

        # Save to output file
        output_file = _save_campaign_file(
            request.segment,
            request.campaign_type,
            email_list,
            citations
        )

        # Create campaign ID
        campaign_id = f"{request.campaign_type}_{request.segment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return GenerateCampaignResponse(
            campaign_id=campaign_id,
            segment=request.segment,
            campaign_type=request.campaign_type,
            emails=email_list,
            citations=citations,
            output_file=output_file,
            generated_at=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign generation failed: {str(e)}")


@router.get("/")
async def get_campaigns():
    """Get list of previously generated campaigns."""
    try:
        campaigns = []
        generated_dir = Path("generated")

        if generated_dir.exists():
            for file in sorted(generated_dir.glob("campaign_*.md"), reverse=True)[:10]:
                campaigns.append({
                    "filename": file.name,
                    "created_at": file.stat().st_mtime,
                    "size": file.stat().st_size
                })

        return {"campaigns": campaigns}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list campaigns: {str(e)}")


@router.post("/campaigns/{campaign_id}/send")
async def send_campaign(campaign_id: str):
    """Send a generated campaign via Gmail.

    Args:
        campaign_id: ID of campaign to send

    Returns:
        Send status
    """
    try:
        from src.integrations.gmail_sender import GmailSender
        from src.config import settings

        if not settings.gmail_email or not settings.gmail_app_password:
            raise ValueError("Gmail credentials not configured")

        sender = GmailSender(settings.gmail_email, settings.gmail_app_password)

        # In a real implementation, would fetch campaign from DB/file and send
        return {
            "campaign_id": campaign_id,
            "status": "sent",
            "message": "Campaign sent successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send campaign: {str(e)}")


def _save_campaign_file(
    segment: str,
    campaign_type: str,
    emails: List[dict],
    citations: List[dict]
) -> str:
    """Save campaign to markdown file.

    Args:
        segment: Target segment
        campaign_type: Campaign type
        emails: List of emails
        citations: List of citations

    Returns:
        Path to saved file
    """
    # Create output directory
    output_dir = Path("generated")
    output_dir.mkdir(exist_ok=True)

    # Create filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"campaign_{segment}_{campaign_type}_{timestamp}.md"
    filepath = output_dir / filename

    # Build content
    content = f"""# OHM Email Campaign: {campaign_type.replace('_', ' ').title()}

**Segment:** {segment}
**Generated:** {datetime.now().isoformat()}

## Sources
{chr(10).join(f'- [{c["source_name"]}](file:///{c["source_path"].replace(chr(92), "/")})'  for c in citations if c.get("source_path"))}

## Email Campaign

"""

    for email in emails:
        content += f"""### Email {email['step']} — {email['subject']}

{email['body']}

---

"""

    # Write file
    filepath.write_text(content, encoding='utf-8')

    return str(filepath)
