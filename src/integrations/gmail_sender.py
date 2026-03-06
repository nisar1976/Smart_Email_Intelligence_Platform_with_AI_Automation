"""Gmail SMTP integration for sending emails."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime


class GmailSender:
    """Sends emails via Gmail SMTP using App Password."""

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465

    def __init__(self, email: str, app_password: str):
        """Initialize Gmail sender with credentials.

        Args:
            email: Gmail email address
            app_password: Gmail App Password (16-char code from Google Account)

        Raises:
            ValueError: If credentials are invalid
        """
        if not email or not app_password:
            raise ValueError("Email and app password are required")

        self.email = email
        self.app_password = app_password
        self._test_connection()

    def _test_connection(self) -> bool:
        """Test Gmail SMTP connection.

        Returns:
            True if connection successful

        Raises:
            ConnectionError: If connection fails
        """
        try:
            server = smtplib.SMTP_SSL(self.SMTP_SERVER, self.SMTP_PORT, timeout=5)
            server.login(self.email, self.app_password)
            server.quit()
            return True
        except smtplib.SMTPAuthenticationError:
            raise ConnectionError("Gmail authentication failed. Check email and app password.")
        except smtplib.SMTPException as e:
            raise ConnectionError(f"SMTP error: {str(e)}")
        except Exception as e:
            raise ConnectionError(f"Connection failed: {str(e)}")

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = True,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send a single email via Gmail SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            body: Email body (HTML or plain text)
            is_html: Whether body is HTML (default: True)
            cc: List of CC email addresses
            bcc: List of BCC email addresses

        Returns:
            True if email sent successfully

        Raises:
            ValueError: If email address is invalid
            ConnectionError: If SMTP connection fails
        """
        if not to_email or "@" not in to_email:
            raise ValueError(f"Invalid recipient email: {to_email}")

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.email
            message["To"] = to_email

            if cc:
                message["Cc"] = ", ".join(cc)

            # Attach body
            mime_type = "html" if is_html else "plain"
            message.attach(MIMEText(body, mime_type))

            # Connect to Gmail SMTP
            server = smtplib.SMTP_SSL(self.SMTP_SERVER, self.SMTP_PORT, timeout=10)
            server.login(self.email, self.app_password)

            # Prepare recipient list
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            # Send email
            server.sendmail(self.email, recipients, message.as_string())
            server.quit()

            return True

        except smtplib.SMTPException as e:
            raise ConnectionError(f"Failed to send email: {str(e)}")
        except Exception as e:
            raise ConnectionError(f"Unexpected error sending email: {str(e)}")

    def send_campaign(
        self,
        emails: List[Dict[str, str]],
        recipients: List[str],
        subject_template: Optional[str] = None
    ) -> Dict[str, int]:
        """Send email campaign to multiple recipients.

        Args:
            emails: List of email dicts with keys: subject, body
            recipients: List of recipient email addresses
            subject_template: Optional subject line template (can include placeholders)

        Returns:
            Dict with success_count and fail_count

        Raises:
            ValueError: If inputs are invalid
        """
        if not emails or not recipients:
            raise ValueError("Emails and recipients are required")

        if len(emails) == 0:
            raise ValueError("At least one email is required")

        success_count = 0
        fail_count = 0
        failures = []

        # Send each email to each recipient
        for recipient in recipients:
            for email_content in emails:
                try:
                    subject = email_content.get("subject", "OHM Email")
                    body = email_content.get("body", "")

                    # Apply subject template if provided
                    if subject_template:
                        subject = subject_template.format(
                            subject=subject,
                            recipient=recipient,
                            date=datetime.now().strftime("%Y-%m-%d")
                        )

                    self.send_email(recipient, subject, body, is_html=True)
                    success_count += 1

                except Exception as e:
                    fail_count += 1
                    failures.append(f"{recipient}: {str(e)}")

        return {
            "success_count": success_count,
            "fail_count": fail_count,
            "total": success_count + fail_count,
            "failures": failures if failures else []
        }

    def send_batch(self, batch: List[Dict]) -> Dict:
        """Send batch of individual emails.

        Args:
            batch: List of dicts with keys: to_email, subject, body, is_html (optional)

        Returns:
            Dict with success/fail counts
        """
        success_count = 0
        fail_count = 0
        failures = []

        for email_dict in batch:
            try:
                self.send_email(
                    to_email=email_dict["to_email"],
                    subject=email_dict["subject"],
                    body=email_dict["body"],
                    is_html=email_dict.get("is_html", True),
                    cc=email_dict.get("cc"),
                    bcc=email_dict.get("bcc")
                )
                success_count += 1
            except Exception as e:
                fail_count += 1
                failures.append(f"{email_dict.get('to_email', 'unknown')}: {str(e)}")

        return {
            "success_count": success_count,
            "fail_count": fail_count,
            "total": success_count + fail_count,
            "failures": failures if failures else []
        }
