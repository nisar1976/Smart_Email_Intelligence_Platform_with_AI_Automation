"""OpenAI API client wrapper for Email Intelligence Agent."""

import logging
from typing import Optional
from openai import OpenAI
from src.config import settings

logger = logging.getLogger(__name__)


class EmailGenerationClient:
    """Wrapper for OpenAI API with email generation templates."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    def generate_email(
        self,
        recipient_segment: str,
        email_sequence_step: int,
        campaign_context: dict,
        guardrails: Optional[str] = None,
    ) -> str:
        """Generate email content using OpenAI.

        Args:
            recipient_segment: Behavioral segment (e.g., "cold_prospect", "active_user")
            email_sequence_step: Step in the sequence (1-20)
            campaign_context: Context for the email (e.g., upsell type, product name)
            guardrails: Brand voice guardrails to enforce

        Returns:
            Generated email content
        """
        # TODO: Build dynamic prompt from guardrails and sequence templates
        system_prompt = self._build_system_prompt(guardrails)
        user_prompt = self._build_user_prompt(
            recipient_segment, email_sequence_step, campaign_context
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating email: {e}")
            raise

    def optimize_subject_line(
        self,
        subject_line: str,
        segment: str,
        historical_performance: dict,
    ) -> str:
        """Optimize subject line based on historical performance data.

        Args:
            subject_line: Current subject line
            segment: Recipient segment
            historical_performance: Open rate, CTR data from similar campaigns

        Returns:
            Optimized subject line
        """
        # TODO: Implement subject line optimization with A/B test insights
        logger.info(f"Optimizing subject line for segment: {segment}")
        return subject_line

    def _build_system_prompt(self, guardrails: Optional[str]) -> str:
        """Build system prompt with brand voice guardrails."""
        base_prompt = "You are an expert email copywriter for OHM, a premium digital services company."
        if guardrails:
            base_prompt += f"\n\nBrand Voice Guidelines:\n{guardrails}"
        return base_prompt

    def _build_user_prompt(
        self, segment: str, step: int, context: dict
    ) -> str:
        """Build user prompt with sequence context."""
        return (
            f"Write email {step} of the OHM sales sequence for a {segment} audience.\n"
            f"Context: {context}\n"
            f"Email should be compelling, personalized, and follow the OHM brand voice."
        )
