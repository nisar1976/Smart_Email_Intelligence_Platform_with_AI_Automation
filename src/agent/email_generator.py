"""Email sequence generation with OpenAI and brand guardrails."""

import logging
import os
import yaml
from typing import List, Optional
from src.models.email import Email, EmailCampaign
from src.integrations.openai_client import EmailGenerationClient
from src.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)


class GuardrailViolationError(Exception):
    """Raised when generated email violates brand voice guardrails."""

    pass


class EmailGenerator:
    """Orchestrates email generation using OpenAI + prompt library + guardrails."""

    def __init__(self):
        """Initialize generator with OpenAI client and prompt templates."""
        self.openai_client = EmailGenerationClient()
        self.guardrails = self._load_guardrails()
        self.email_sequences = self._load_email_sequences()

    def _load_guardrails(self) -> dict:
        """Load brand voice guardrails from YAML.

        Returns:
            Dict with guardrails configuration
        """
        try:
            prompts_dir = os.path.join(
                os.path.dirname(__file__), "..", "prompts"
            )
            guardrails_path = os.path.join(prompts_dir, "guardrails.yaml")

            with open(guardrails_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading guardrails: {e}")
            raise

    def _load_email_sequences(self) -> dict:
        """Load email sequence templates from YAML.

        Returns:
            Dict with sequence definitions
        """
        try:
            prompts_dir = os.path.join(
                os.path.dirname(__file__), "..", "prompts"
            )
            sequences_path = os.path.join(prompts_dir, "email_sequences.yaml")

            with open(sequences_path, "r") as f:
                data = yaml.safe_load(f)
                return data.get("sequences", {})
        except Exception as e:
            logger.error(f"Error loading email sequences: {e}")
            raise

    def generate_sequence(
        self, segment: str, campaign_type: str, recipient_emails: List[str]
    ) -> List[Email]:
        """Generate a full email sequence for a given audience segment.

        Args:
            segment: Behavioral segment (e.g., "cold_prospect", "active_user")
            campaign_type: Campaign type (onboarding, upsell_*, reactivation, cold_outbound)
            recipient_emails: List of recipient email addresses

        Returns:
            List of Email objects ready to send

        Raises:
            GuardrailViolationError: If any generated email violates guardrails
            KeyError: If campaign_type not found in sequences
        """
        if campaign_type not in self.email_sequences:
            raise KeyError(f"Campaign type '{campaign_type}' not found in sequences")

        sequence_config = self.email_sequences[campaign_type]
        generated_emails = []

        try:
            for step in range(1, sequence_config["total_emails"] + 1):
                email_template = next(
                    (e for e in sequence_config["emails"] if e["step"] == step),
                    None,
                )
                if not email_template:
                    logger.warning(
                        f"No template found for step {step} in {campaign_type}"
                    )
                    continue

                # Generate one email per recipient
                for idx, recipient_email in enumerate(recipient_emails):
                    try:
                        email = self.generate_single_email(
                            segment=segment,
                            step=step,
                            campaign_type=campaign_type,
                            recipient_email=recipient_email,
                            recipient_id=f"recipient_{idx}",
                            email_template=email_template,
                        )
                        generated_emails.append(email)
                    except GuardrailViolationError as e:
                        logger.error(
                            f"Guardrail violation for {recipient_email}, step {step}: {e}"
                        )
                        raise

            logger.info(
                f"Generated {len(generated_emails)} emails for segment '{segment}' "
                f"campaign '{campaign_type}'"
            )
            return generated_emails

        except Exception as e:
            logger.error(f"Error generating sequence: {e}")
            raise

    def generate_single_email(
        self,
        segment: str,
        step: int,
        campaign_type: str,
        recipient_email: str,
        recipient_id: str,
        email_template: dict,
    ) -> Email:
        """Generate a single email for a specific recipient.

        Args:
            segment: Behavioral segment
            step: Step in the sequence
            campaign_type: Campaign type
            recipient_email: Recipient email address
            recipient_id: Recipient ID
            email_template: Email template dict from sequences YAML

        Returns:
            Email object

        Raises:
            GuardrailViolationError: If generated content violates guardrails
        """
        try:
            # Build context for OpenAI
            context = {
                "segment": segment,
                "step": step,
                "total_steps": len(
                    [e for e in self.email_sequences[campaign_type]["emails"]]
                ),
                "campaign_type": campaign_type,
                "tone": email_template.get("tone", "professional"),
                "purpose": email_template.get("purpose", ""),
                "key_messages": email_template.get("key_messages", []),
                "cta": email_template.get("cta", ""),
                "length": email_template.get("length", "medium"),
                "guardrails": self._format_guardrails_for_prompt(),
            }

            # Generate email body
            email_body = self.openai_client.generate_email(
                recipient_segment=segment,
                email_sequence_step=step,
                campaign_context=context,
                guardrails=context["guardrails"],
            )

            # Generate subject line
            subject_line = self._generate_subject_line(
                segment=segment,
                step=step,
                campaign_type=campaign_type,
                email_template=email_template,
            )

            # Validate against guardrails
            if not self.validate_against_guardrails(email_body):
                raise GuardrailViolationError(
                    f"Email body violates brand voice guardrails for {segment}, step {step}"
                )

            # Create Email object
            email = Email(
                subject=subject_line,
                body=email_body,
                recipient_email=recipient_email,
                recipient_id=recipient_id,
                sequence_step=step,
                segment=segment,
                sent_at=None,
            )

            return email

        except Exception as e:
            logger.error(f"Error generating single email: {e}")
            raise

    def validate_against_guardrails(self, email_content: str) -> bool:
        """Validate email content against OHM brand voice guardrails.

        Uses a second OpenAI call to check compliance with guardrails.

        Args:
            email_content: Full email body to validate

        Returns:
            True if content passes validation, False otherwise
        """
        try:
            # Build validation prompt
            hard_prohibitions = self.guardrails.get("hard_prohibitions", [])
            guardrails_text = "\n".join(hard_prohibitions)

            validation_prompt = (
                f"Review this email content for brand compliance. "
                f"Reject if it violates ANY of these rules:\n\n"
                f"{guardrails_text}\n\n"
                f"Email content:\n{email_content}\n\n"
                f"Reply with only 'PASS' or 'FAIL' and the violated rule."
            )

            # Quick validation via OpenAI
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": validation_prompt}],
                temperature=0,
                max_tokens=50,
            )

            result = response.choices[0].message.content.strip().upper()

            if "FAIL" in result:
                logger.warning(f"Guardrail violation detected: {result}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating against guardrails: {e}")
            # On validation error, fail safe (don't send)
            return False

    def _generate_subject_line(
        self,
        segment: str,
        step: int,
        campaign_type: str,
        email_template: dict,
    ) -> str:
        """Generate subject line for email.

        Args:
            segment: Behavioral segment
            step: Step number
            campaign_type: Campaign type
            email_template: Email template

        Returns:
            Subject line string
        """
        try:
            # Build subject line generation prompt
            context = {
                "segment": segment,
                "step": step,
                "campaign_type": campaign_type,
                "purpose": email_template.get("purpose", ""),
                "cta": email_template.get("cta", ""),
                "key_messages": email_template.get("key_messages", []),
            }

            subject_prompt = (
                f"Generate a compelling email subject line for:\n"
                f"Campaign: {campaign_type}\n"
                f"Step: {step}\n"
                f"Purpose: {context['purpose']}\n"
                f"CTA: {context['cta']}\n"
                f"Key messages: {', '.join(context['key_messages'])}\n\n"
                f"Respond with ONLY the subject line, no quotes or explanation."
            )

            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": subject_prompt}],
                temperature=0.7,
                max_tokens=100,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating subject line: {e}")
            # Fallback to template-based subject
            purpose = email_template.get("purpose", "")
            return f"{campaign_type.title()} - Step {step}: {purpose}"

    def _format_guardrails_for_prompt(self) -> str:
        """Format guardrails as a string for inclusion in OpenAI prompts.

        Returns:
            Formatted guardrails text
        """
        parts = []

        # Tone rules
        if "tone" in self.guardrails:
            tone_rules = self.guardrails["tone"]
            parts.append("TONE RULES:")
            parts.append(
                f"Use these tones: {', '.join(tone_rules.get('allowed', []))}"
            )
            parts.append(
                f"Never use these tones: {', '.join(tone_rules.get('forbidden', []))}"
            )

        # Hard prohibitions
        if "hard_prohibitions" in self.guardrails:
            parts.append("\nHARD PROHIBITIONS:")
            for rule in self.guardrails["hard_prohibitions"]:
                parts.append(f"- {rule}")

        # Safe phrases
        if "safe_phrases" in self.guardrails:
            parts.append("\nPREFERRED PHRASES:")
            for phrase in self.guardrails["safe_phrases"]:
                parts.append(f"- {phrase}")

        return "\n".join(parts)
