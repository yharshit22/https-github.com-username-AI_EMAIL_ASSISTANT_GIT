#!/usr/bin/env python3
"""
CLI Script for Fetching Emails

This script can be run manually or scheduled via cron to fetch emails periodically.
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

from sqlalchemy.exc import IntegrityError  # <<< NEW

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Email, User
from app.email_client import EmailClient
from app.sentiment import analyze_email_sentiment
from app.priority import classify_priority
from app.ai_reply import generate_reply


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/email_fetcher.log'),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


def fetch_emails_for_user(user_id, limit=50, since_days=7):
    """Fetch emails for a specific user"""
    logger = logging.getLogger(__name__)

    try:
        # Create email client
        email_client = EmailClient(user_id)

        # Fetch emails
        logger.info(
            f"Fetching emails for user {user_id} (limit: {limit}, since: {since_days} days)"
        )
        emails_data = email_client.fetch_emails(limit=limit, since_days=since_days)

        if not emails_data:
            logger.info(f"No new emails found for user {user_id}")
            return 0

        # Process and save emails
        saved_count = 0
        for email_data in emails_data:
            try:
                msg_id = email_data["message_id"]

                # --------- DUPLICATE CHECK (GLOBAL) ----------
                # Sirf message_id pe check – user_id mat use karo
                existing_email = Email.query.filter_by(
                    message_id=msg_id
                ).first()

                if existing_email:
                    logger.info(
                        "Email already exists (message_id=%s), skipping: %s",
                        msg_id,
                        (email_data.get("subject") or "")[:60],
                    )
                    continue
                # ----------------------------------------------

                # Create new email
                email = Email(
                    message_id=msg_id,
                    user_id=user_id,
                    from_address=email_data["from_address"],
                    to_address=email_data["to_address"],
                    cc_address=email_data["cc_address"],
                    subject=email_data["subject"],
                    body=email_data["body"],
                    body_plain=email_data["body_plain"],
                    body_html=email_data["body_html"],
                    received_at=email_data["received_at"],
                    message_size=email_data["message_size"],
                    in_reply_to=email_data["in_reply_to"],
                    references=email_data["references"],
                )

                # Analyze sentiment
                sentiment, confidence = analyze_email_sentiment(
                    email.subject, email.body
                )
                email.sentiment = sentiment
                email.sentiment_score = confidence

                # Classify priority
                priority, priority_confidence = classify_priority(email)
                email.priority = priority

                # Generate AI reply for high/medium priority emails
                if email.priority in ["high", "medium"]:
                    try:
                        reply = generate_reply(email, sentiment, priority)
                        if reply:
                            email.generated_reply = reply
                            logger.info(
                                "Generated AI reply for email: %s...",
                                email.subject[:50],
                            )
                    except Exception as e:
                        logger.warning(
                            "Failed to generate AI reply for %s: %s",
                            email.subject[:50],
                            str(e),
                        )

                # ---------- DB SAVE + ATTACHMENTS -------------
                db.session.add(email)
                # flush so that email.id is available for attachments
                db.session.flush()

                for attachment_data in email_data["attachments"]:
                    from app.models import EmailAttachment

                    attachment = EmailAttachment(
                        email_id=email.id,
                        filename=attachment_data["filename"],
                        content_type=attachment_data["content_type"],
                        size=attachment_data["size"],
                        content_id=attachment_data["content_id"],
                        is_inline=attachment_data["is_inline"],
                    )
                    db.session.add(attachment)

                saved_count += 1
                logger.info("Saved email: %s...", email.subject[:50])
                # ------------------------------------------------

            except IntegrityError as ie:
                # Mostly UNIQUE(message_id) wali error yahi hogi
                db.session.rollback()
                logger.warning(
                    "IntegrityError while saving email %s, skipping. Details: %s",
                    email_data.get("message_id"),
                    str(ie),
                )
                continue
            except Exception as e:
                db.session.rollback()
                logger.error(
                    "Error processing email %s: %s",
                    email_data.get("message_id"),
                    str(e),
                )
                continue

        db.session.commit()
        logger.info(f"Successfully processed {saved_count} emails for user {user_id}")
        return saved_count

    except Exception as e:
        logger.error(f"Error fetching emails for user {user_id}: {str(e)}")
        return 0


def main():
    """Main function"""
    # Setup logging
    logger = setup_logging()

    # Create Flask app context
    app = create_app("development")

    with app.app_context():
        try:
            # Get command line arguments
            import argparse

            parser = argparse.ArgumentParser(
                description="Fetch emails for AI Email Assistant"
            )
            parser.add_argument(
                "--user-id",
                type=int,
                help="Specific user ID to fetch emails for",
            )
            parser.add_argument(
                "--limit",
                type=int,
                default=50,
                help="Maximum number of emails to fetch",
            )
            parser.add_argument(
                "--since-days",
                type=int,
                default=7,
                help="Fetch emails since N days ago",
            )
            parser.add_argument(
                "--all-users",
                action="store_true",
                help="Fetch emails for all active users",
            )

            args = parser.parse_args()

            logger.info("Starting email fetch process")
            logger.info(
                "Arguments: user_id=%s, limit=%s, since_days=%s, all_users=%s",
                args.user_id,
                args.limit,
                args.since_days,
                args.all_users,
            )

            # Determine which users to process
            users_to_process = []

            if args.user_id:
                # Specific user
                user = User.query.get(args.user_id)
                if user and user.is_active:
                    users_to_process = [user]
                else:
                    logger.error(f"User {args.user_id} not found or inactive")
                    return    
                
                # Always process ONLY the primary fetch user
            primary_id = int(os.getenv("PRIMARY_FETCH_USER_ID", "1"))
            primary_user = User.query.get(primary_id)

            if not primary_user:
                logger.error(f"PRIMARY_FETCH_USER_ID={primary_id} not found in database!")
                return

            users_to_process = [primary_user]
            logger.info(f"Using PRIMARY_FETCH_USER: {primary_user.email}")

                
                

            if not users_to_process:
                logger.info("No active users found")
                return

            # Process each user
            total_emails_saved = 0

            for user in users_to_process:
                try:
                    logger.info(f"Processing user: {user.email}")
                    emails_saved = fetch_emails_for_user(
                        user.id,
                        limit=args.limit,
                        since_days=args.since_days,
                    )
                    total_emails_saved += emails_saved

                except Exception as e:
                    logger.error(
                        "Error processing user %s: %s",
                        user.email,
                        str(e),
                    )
                    continue

            logger.info(
                "Email fetch process completed. Total emails saved: %s",
                total_emails_saved,
            )

            # Print summary
            print("\n" + "=" * 60)
            print("EMAIL FETCH SUMMARY")
            print("=" * 60)
            print(f"Processed users: {len(users_to_process)}")
            print(f"Total emails saved: {total_emails_saved}")
            print(
                "Process completed at:",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            print("=" * 60)

        except Exception as e:
            logger.error(f"Fatal error in main process: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main()
