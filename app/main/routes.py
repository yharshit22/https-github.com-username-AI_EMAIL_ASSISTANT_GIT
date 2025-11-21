import os
import logging
from datetime import datetime, timedelta

from flask import (
    render_template,
    request,
    flash,
    redirect,
    url_for,
    jsonify,
    current_app,
)
from flask_login import login_required, current_user
from sqlalchemy import or_, desc, func

from app import db
from app.main import bp
from app.models import Email, User
from app.email_client import EmailClient
from app.sentiment import analyze_email_sentiment
from app.priority import classify_priority
from app.ai_reply import generate_reply, regenerate_reply

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Helper: ALWAYS use the same "master" inbox user (from IMAP_USERNAME)
# ---------------------------------------------------------------------
def get_master_user_id() -> int:
    """
    Returns the user_id which owns the shared inbox.

    Priority:
    1) User whose email == IMAP_USERNAME (from config/.env)
    2) First active user in DB
    3) Fallback: current_user.id
    """
    imap_email = current_app.config.get("IMAP_USERNAME") or os.getenv("IMAP_USERNAME")

    # 1) Try to find user by IMAP email
    if imap_email:
        master = User.query.filter_by(email=imap_email).first()
        if master:
            return master.id

    # 2) First active user
    fallback = User.query.filter_by(is_active=True).order_by(User.id.asc()).first()
    if fallback:
        return fallback.id

    # 3) Fallback to current logged-in user
    if current_user and current_user.is_authenticated:
        return current_user.id

    # Ultimate fallback (shouldn't normally happen)
    return 1


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@bp.route("/")
@bp.route("/index")
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("main/index.html", title="AI Email Assistant")


@bp.route("/dashboard")
@login_required
def dashboard():
    """Dashboard page with email statistics (shared inbox)."""
    master_user_id = get_master_user_id()

    # Get email statistics FOR MASTER INBOX ONLY
    total_emails = Email.query.filter_by(user_id=master_user_id).count()

    # Emails from last 24 hours
    today_emails = (
        Email.query.filter_by(user_id=master_user_id)
        .filter(Email.received_at >= datetime.utcnow() - timedelta(days=1))
        .count()
    )

    # High priority emails
    high_priority_emails = Email.query.filter_by(
        user_id=master_user_id, priority="high"
    ).count()

    # Pending replies (emails that need attention)
    pending_replies = (
        Email.query.filter_by(user_id=master_user_id)
        .filter(Email.status.in_(["new", "in_progress"]))
        .count()
    )

    # Sentiment distribution
    sentiment_stats = (
        db.session.query(Email.sentiment, func.count(Email.id))
        .filter_by(user_id=master_user_id)
        .group_by(Email.sentiment)
        .all()
    )

    # Priority distribution
    priority_stats = (
        db.session.query(Email.priority, func.count(Email.id))
        .filter_by(user_id=master_user_id)
        .group_by(Email.priority)
        .all()
    )

    # Recent emails
    recent_emails = (
        Email.query.filter_by(user_id=master_user_id)
        .order_by(desc(Email.received_at))
        .limit(5)
        .all()
    )

    return render_template(
        "main/dashboard.html",
        title="Dashboard",
        total_emails=total_emails,
        today_emails=today_emails,
        high_priority_emails=high_priority_emails,
        pending_replies=pending_replies,
        sentiment_stats=sentiment_stats,
        priority_stats=priority_stats,
        recent_emails=recent_emails,
    )


@bp.route("/emails")
@login_required
def emails_list():
    """List all emails with filtering and pagination (shared inbox)."""
    master_user_id = get_master_user_id()

    # Get filter parameters
    page = request.args.get("page", 1, type=int)
    priority_filter = request.args.get("priority", "all")
    sentiment_filter = request.args.get("sentiment", "all")
    status_filter = request.args.get("status", "all")
    search_query = request.args.get("search", "")

    # Base query: ALWAYS master inbox
    query = Email.query.filter_by(user_id=master_user_id)

    # Apply filters
    if priority_filter != "all":
        query = query.filter_by(priority=priority_filter)

    if sentiment_filter != "all":
        query = query.filter_by(sentiment=sentiment_filter)

    if status_filter != "all":
        query = query.filter_by(status=status_filter)

    if search_query:
        query = query.filter(
            or_(
                Email.subject.ilike(f"%{search_query}%"),
                Email.body.ilike(f"%{search_query}%"),
                Email.from_address.ilike(f"%{search_query}%"),
            )
        )

    # Paginate results
    emails = query.order_by(desc(Email.received_at)).paginate(
        page=page,
        per_page=current_app.config["EMAILS_PER_PAGE"],
        error_out=False,
    )

    return render_template(
        "main/emails_list.html",
        title="Emails",
        emails=emails,
        priority_filter=priority_filter,
        sentiment_filter=sentiment_filter,
        status_filter=status_filter,
        search_query=search_query,
    )


@bp.route("/email/<int:email_id>")
@login_required
def email_detail(email_id):
    """Show email details (from shared inbox)."""
    master_user_id = get_master_user_id()

    # Make sure we only ever see the MASTER inbox email
    email = Email.query.filter_by(id=email_id, user_id=master_user_id).first_or_404()

    # Mark as read
    if not email.is_read:
        email.is_read = True
        db.session.commit()

    return render_template(
        "main/email_detail.html", title="Email Details", email=email
    )


@bp.route("/email/<int:email_id>/generate_reply", methods=["POST"])
@login_required
def generate_email_reply(email_id):
    """Generate AI reply for an email (shared inbox)."""
    master_user_id = get_master_user_id()
    email = Email.query.filter_by(id=email_id, user_id=master_user_id).first_or_404()

    try:
        reply = generate_reply(email)

        if reply:
            email.generated_reply = reply
            email.status = "in_progress"
            db.session.commit()

            flash("AI reply generated successfully!", "success")
        else:
            flash("Failed to generate reply. Please try again.", "danger")

    except Exception as e:
        logger.error(f"Error generating reply for email {email_id}: {str(e)}")
        flash("Error generating reply. Please try again.", "danger")

    return redirect(url_for("main.email_detail", email_id=email_id))


@bp.route("/email/<int:email_id>/regenerate_reply", methods=["POST"])
@login_required
def regenerate_email_reply(email_id):
    """Regenerate AI reply for an email (shared inbox)."""
    master_user_id = get_master_user_id()
    email = Email.query.filter_by(id=email_id, user_id=master_user_id).first_or_404()

    try:
        instructions = request.form.get("instructions", "")
        reply = regenerate_reply(email, instructions)

        if reply:
            email.generated_reply = reply
            db.session.commit()

            flash("Reply regenerated successfully!", "success")
        else:
            flash("Failed to regenerate reply. Please try again.", "danger")

    except Exception as e:
        logger.error(f"Error regenerating reply for email {email_id}: {str(e)}")
        flash("Error regenerating reply. Please try again.", "danger")

    return redirect(url_for("main.email_detail", email_id=email_id))


@bp.route("/email/<int:email_id>/send_reply", methods=["POST"])
@login_required
def send_email_reply(email_id):
    """Send email reply (shared inbox, always from master account)."""
    master_user_id = get_master_user_id()
    email = Email.query.filter_by(id=email_id, user_id=master_user_id).first_or_404()

    try:
        reply_text = request.form.get("reply_text", "").strip()

        if not reply_text:
            flash("Please enter a reply message.", "warning")
            return redirect(url_for("main.email_detail", email_id=email_id))

        # Send email using email client bound to MASTER inbox
        email_client = EmailClient(master_user_id)

        success = email_client.send_email(
            to_address=email.from_address,
            subject=f"Re: {email.subject}",
            body=reply_text,
        )

        if success:
            email.status = "replied"
            email.replied_at = datetime.utcnow()
            db.session.commit()

            flash("Reply sent successfully!", "success")
        else:
            flash("Failed to send reply. Please try again.", "danger")

    except Exception as e:
        logger.error(f"Error sending reply for email {email_id}: {str(e)}")
        flash("Error sending reply. Please try again.", "danger")

    return redirect(url_for("main.email_detail", email_id=email_id))


@bp.route("/email/<int:email_id>/update_status", methods=["POST"])
@login_required
def update_email_status(email_id):
    """Update status of a single email (AJAX endpoint, shared inbox)."""
    master_user_id = get_master_user_id()

    # Make sure email belongs to MASTER inbox
    email = Email.query.filter_by(id=email_id, user_id=master_user_id).first_or_404()

    status = None

    # 1) JSON body
    if request.is_json:
        data = request.get_json(silent=True) or {}
        status = data.get("status")

    # 2) Fallback: form-encoded
    if not status:
        status = request.form.get("status")

    if not status:
        return jsonify({"success": False, "message": "Missing 'status' in request."}), 400

    email.status = status
    db.session.commit()

    return jsonify(
        {"success": True, "email_id": email.id, "new_status": email.status}
    ), 200


@bp.route("/fetch_emails", methods=["POST"])
@login_required
def fetch_emails():
    """
    Fetch emails from IMAP server.

    IMPORTANT: always fetch into MASTER inbox (single shared mailbox),
    regardless of which user clicked the button.
    """
    master_user_id = get_master_user_id()

    try:
        email_client = EmailClient(master_user_id)

        # Fetch recent emails
        emails_data = email_client.fetch_emails(limit=20, since_days=7)

        if not emails_data:
            flash(
                "No new emails found or unable to connect to email server.", "info"
            )
            return redirect(url_for("main.dashboard"))

        saved_count = 0

        for email_data in emails_data:
            # Check if email already exists for MASTER inbox
            existing_email = Email.query.filter_by(
                message_id=email_data["message_id"],
                user_id=master_user_id,
            ).first()

            if existing_email:
                logger.info(
                    "Email already exists (message_id=%s), skipping: %s",
                    email_data["message_id"],
                    email_data["subject"][:80],
                )
                continue

            # Create new email
            email = Email(
                message_id=email_data["message_id"],
                user_id=master_user_id,
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

            # Generate AI reply for high/medium priority
            if email.priority in ["high", "medium"]:
                reply = generate_reply(email, sentiment, priority)
                if reply:
                    email.generated_reply = reply

            db.session.add(email)
            saved_count += 1

        db.session.commit()

        flash(
            f"Successfully fetched and processed {saved_count} emails!", "success"
        )

    except Exception as e:
        logger.error(f"Error fetching emails: {str(e)}")
        flash("Error fetching emails. Please check your email configuration.", "danger")

    return redirect(url_for("main.dashboard"))


@bp.route("/settings")
@login_required
def settings():
    """Application settings page"""
    return render_template("main/settings.html", title="Settings")
