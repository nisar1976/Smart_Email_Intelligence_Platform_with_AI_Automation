"""Email open, click, and conversion tracking."""

import logging
from datetime import datetime
from typing import Optional
from src.config import settings

logger = logging.getLogger(__name__)


class EmailTracker:
    """Records email engagement events (opens, clicks, conversions)."""

    def __init__(self):
        """Initialize tracker with database connection."""
        self.db_url = settings.database_url
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database for tracking if not already done."""
        try:
            if self.db_url.startswith("sqlite:"):
                # Simple SQLite initialization
                import sqlite3
                from urllib.parse import urlparse

                db_path = urlparse(self.db_url).path
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Create tables if they don't exist
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS email_opens (
                        email_id TEXT,
                        contact_id TEXT,
                        timestamp DATETIME,
                        PRIMARY KEY (email_id, contact_id)
                    )
                    """
                )

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS email_clicks (
                        email_id TEXT,
                        contact_id TEXT,
                        link TEXT,
                        timestamp DATETIME,
                        PRIMARY KEY (email_id, contact_id, link)
                    )
                    """
                )

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS email_conversions (
                        email_id TEXT,
                        contact_id TEXT,
                        conversion_type TEXT,
                        timestamp DATETIME,
                        PRIMARY KEY (email_id, contact_id, conversion_type)
                    )
                    """
                )

                conn.commit()
                conn.close()
                logger.info("Email tracker database initialized")

        except Exception as e:
            logger.error(f"Error initializing tracker database: {e}")

    def record_open(
        self, email_id: str, contact_id: str, timestamp: datetime
    ) -> None:
        """Record that an email was opened by a contact.

        Args:
            email_id: Email ID
            contact_id: Contact ID
            timestamp: When the email was opened
        """
        try:
            if self.db_url.startswith("sqlite:"):
                import sqlite3
                from urllib.parse import urlparse

                db_path = urlparse(self.db_url).path
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO email_opens
                    (email_id, contact_id, timestamp)
                    VALUES (?, ?, ?)
                    """,
                    (email_id, contact_id, timestamp),
                )

                conn.commit()
                conn.close()

                logger.debug(f"Recorded open: email={email_id}, contact={contact_id}")

        except Exception as e:
            logger.error(f"Error recording email open: {e}")

    def record_click(
        self, email_id: str, contact_id: str, link: str, timestamp: datetime
    ) -> None:
        """Record that a contact clicked a link in an email.

        Args:
            email_id: Email ID
            contact_id: Contact ID
            link: URL that was clicked
            timestamp: When the link was clicked
        """
        try:
            if self.db_url.startswith("sqlite:"):
                import sqlite3
                from urllib.parse import urlparse

                db_path = urlparse(self.db_url).path
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO email_clicks
                    (email_id, contact_id, link, timestamp)
                    VALUES (?, ?, ?, ?)
                    """,
                    (email_id, contact_id, link, timestamp),
                )

                conn.commit()
                conn.close()

                logger.debug(f"Recorded click: email={email_id}, contact={contact_id}, link={link}")

        except Exception as e:
            logger.error(f"Error recording email click: {e}")

    def record_conversion(
        self,
        email_id: str,
        contact_id: str,
        conversion_type: str,
        timestamp: datetime,
    ) -> None:
        """Record a conversion event attributed to an email.

        Args:
            email_id: Email ID
            contact_id: Contact ID
            conversion_type: Type of conversion
                (phoenix_signup, visionary_upgrade, infinity_upgrade, purchase)
            timestamp: When the conversion occurred
        """
        valid_types = [
            "phoenix_signup",
            "visionary_upgrade",
            "infinity_upgrade",
            "purchase",
        ]

        if conversion_type not in valid_types:
            logger.warning(f"Unknown conversion type: {conversion_type}")
            return

        try:
            if self.db_url.startswith("sqlite:"):
                import sqlite3
                from urllib.parse import urlparse

                db_path = urlparse(self.db_url).path
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO email_conversions
                    (email_id, contact_id, conversion_type, timestamp)
                    VALUES (?, ?, ?, ?)
                    """,
                    (email_id, contact_id, conversion_type, timestamp),
                )

                conn.commit()
                conn.close()

                logger.debug(
                    f"Recorded conversion: email={email_id}, contact={contact_id}, "
                    f"type={conversion_type}"
                )

        except Exception as e:
            logger.error(f"Error recording conversion: {e}")

    def get_email_stats(self, email_id: str) -> dict:
        """Get engagement statistics for a single email.

        Args:
            email_id: Email ID

        Returns:
            Dict with open count, click count, conversion count
        """
        try:
            if self.db_url.startswith("sqlite:"):
                import sqlite3
                from urllib.parse import urlparse

                db_path = urlparse(self.db_url).path
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Count opens
                cursor.execute(
                    "SELECT COUNT(DISTINCT contact_id) FROM email_opens WHERE email_id = ?",
                    (email_id,),
                )
                open_count = cursor.fetchone()[0]

                # Count clicks
                cursor.execute(
                    "SELECT COUNT(DISTINCT contact_id) FROM email_clicks WHERE email_id = ?",
                    (email_id,),
                )
                click_count = cursor.fetchone()[0]

                # Count conversions
                cursor.execute(
                    "SELECT COUNT(DISTINCT contact_id) FROM email_conversions WHERE email_id = ?",
                    (email_id,),
                )
                conversion_count = cursor.fetchone()[0]

                conn.close()

                return {
                    "email_id": email_id,
                    "total_opens": open_count,
                    "total_clicks": click_count,
                    "total_conversions": conversion_count,
                }

        except Exception as e:
            logger.error(f"Error getting email stats: {e}")
            return {
                "email_id": email_id,
                "total_opens": 0,
                "total_clicks": 0,
                "total_conversions": 0,
            }
