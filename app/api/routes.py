import logging
from flask import jsonify, request
from flask_login import login_required, current_user
from app import db
from app.api import bp
from app.models import Email
from app.sentiment import analyze_email_sentiment
from app.priority import classify_priority
from app.ai_reply import generate_reply

logger = logging.getLogger(__name__)

@bp.route('/emails', methods=['GET'])
@login_required
def get_emails():
    """Get emails with filtering and pagination"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        priority = request.args.get('priority')
        sentiment = request.args.get('sentiment')
        status = request.args.get('status')
        search = request.args.get('search')
        
        # Build query
        query = Email.query.filter_by(user_id=current_user.id)
        
        # Apply filters
        if priority:
            query = query.filter_by(priority=priority)
        if sentiment:
            query = query.filter_by(sentiment=sentiment)
        if status:
            query = query.filter_by(status=status)
        if search:
            query = query.filter(
                Email.subject.ilike(f'%{search}%') |
                Email.body.ilike(f'%{search}%') |
                Email.from_address.ilike(f'%{search}%')
            )
        
        # Paginate
        pagination = query.order_by(Email.received_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format response
        emails_data = []
        for email in pagination.items:
            emails_data.append({
                'id': email.id,
                'message_id': email.message_id,
                'from_address': email.from_address,
                'to_address': email.to_address,
                'subject': email.subject,
                'received_at': email.received_at.isoformat(),
                'sentiment': email.sentiment,
                'sentiment_score': email.sentiment_score,
                'priority': email.priority,
                'status': email.status,
                'is_read': email.is_read,
                'is_flagged': email.is_flagged
            })
        
        return jsonify({
            'emails': emails_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error in API get_emails: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/emails/<int:email_id>', methods=['GET'])
@login_required
def get_email(email_id):
    """Get single email details"""
    try:
        email = Email.query.filter_by(id=email_id, user_id=current_user.id).first_or_404()
        
        email_data = {
            'id': email.id,
            'message_id': email.message_id,
            'from_address': email.from_address,
            'to_address': email.to_address,
            'cc_address': email.cc_address,
            'subject': email.subject,
            'body': email.body,
            'body_plain': email.body_plain,
            'body_html': email.body_html,
            'received_at': email.received_at.isoformat(),
            'sentiment': email.sentiment,
            'sentiment_score': email.sentiment_score,
            'priority': email.priority,
            'status': email.status,
            'is_read': email.is_read,
            'is_flagged': email.is_flagged,
            'generated_reply': email.generated_reply,
            'replied_at': email.replied_at.isoformat() if email.replied_at else None,
            'attachments': [
                {
                    'filename': att.filename,
                    'content_type': att.content_type,
                    'size': att.size
                } for att in email.attachments
            ]
        }
        
        return jsonify(email_data)
        
    except Exception as e:
        logger.error(f"Error in API get_email: {str(e)}")
        return jsonify({'error': 'Email not found'}), 404

@bp.route('/emails/<int:email_id>/analyze', methods=['POST'])
@login_required
def analyze_email(email_id):
    """Analyze email sentiment and priority"""
    try:
        email = Email.query.filter_by(id=email_id, user_id=current_user.id).first_or_404()
        
        # Analyze sentiment
        sentiment, sentiment_score = analyze_email_sentiment(email.subject, email.body)
        email.sentiment = sentiment
        email.sentiment_score = sentiment_score
        
        # Classify priority
        priority, priority_confidence = classify_priority(email)
        email.priority = priority
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'priority': priority,
            'priority_confidence': priority_confidence
        })
        
    except Exception as e:
        logger.error(f"Error analyzing email {email_id}: {str(e)}")
        return jsonify({'error': 'Analysis failed'}), 500

@bp.route('/emails/<int:email_id>/generate_reply', methods=['POST'])
@login_required
def api_generate_reply(email_id):
    """Generate AI reply for email"""
    try:
        email = Email.query.filter_by(id=email_id, user_id=current_user.id).first_or_404()
        
        # Generate reply
        reply = generate_reply(email)
        
        if reply:
            email.generated_reply = reply
            email.status = 'in_progress'
            db.session.commit()
            
            return jsonify({
                'success': True,
                'reply': reply,
                'message': 'Reply generated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to generate reply'
            }), 500
            
    except Exception as e:
        logger.error(f"Error generating reply for email {email_id}: {str(e)}")
        return jsonify({'error': 'Reply generation failed'}), 500

@bp.route('/emails/<int:email_id>/regenerate_reply', methods=['POST'])
@login_required
def api_regenerate_reply(email_id):
    """Regenerate AI reply for email"""
    try:
        from app.ai_reply import regenerate_reply
        
        email = Email.query.filter_by(id=email_id, user_id=current_user.id).first_or_404()
        instructions = request.json.get('instructions', '')
        
        reply = regenerate_reply(email, instructions)
        
        if reply:
            email.generated_reply = reply
            db.session.commit()
            
            return jsonify({
                'success': True,
                'reply': reply,
                'message': 'Reply regenerated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to regenerate reply'
            }), 500
            
    except Exception as e:
        logger.error(f"Error regenerating reply for email {email_id}: {str(e)}")
        return jsonify({'error': 'Reply regeneration failed'}), 500

@bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Get email statistics"""
    try:
        # Basic counts
        total_emails = Email.query.filter_by(user_id=current_user.id).count()
        
        # Time-based stats (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_emails = Email.query.filter_by(user_id=current_user.id).filter(
            Email.received_at >= week_ago
        ).count()
        
        # Priority distribution
        priority_stats = db.session.query(
            Email.priority, func.count(Email.id)
        ).filter_by(user_id=current_user.id).group_by(Email.priority).all()
        
        # Sentiment distribution
        sentiment_stats = db.session.query(
            Email.sentiment, func.count(Email.id)
        ).filter_by(user_id=current_user.id).group_by(Email.sentiment).all()
        
        # Status distribution
        status_stats = db.session.query(
            Email.status, func.count(Email.id)
        ).filter_by(user_id=current_user.id).group_by(Email.status).all()
        
        return jsonify({
            'total_emails': total_emails,
            'recent_emails': recent_emails,
            'priority_distribution': dict(priority_stats),
            'sentiment_distribution': dict(sentiment_stats),
            'status_distribution': dict(status_stats)
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': 'Failed to get statistics'}), 500

@bp.route('/emails/bulk_action', methods=['POST'])
@login_required
def bulk_action():
    """Perform bulk action on emails"""
    try:
        data = request.json
        email_ids = data.get('email_ids', [])
        action = data.get('action')
        
        if not email_ids or not action:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Validate action
        valid_actions = ['mark_read', 'mark_unread', 'flag', 'unflag', 
                        'status_new', 'status_in_progress', 'status_replied', 'status_ignored']
        
        if action not in valid_actions:
            return jsonify({'error': 'Invalid action'}), 400
        
        # Get emails
        emails = Email.query.filter(
            Email.id.in_(email_ids),
            Email.user_id == current_user.id
        ).all()
        
        # Perform action
        updated_count = 0
        for email in emails:
            if action == 'mark_read':
                email.is_read = True
            elif action == 'mark_unread':
                email.is_read = False
            elif action == 'flag':
                email.is_flagged = True
            elif action == 'unflag':
                email.is_flagged = False
            elif action.startswith('status_'):
                email.status = action.replace('status_', '')
            
            updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{updated_count} emails updated',
            'updated_count': updated_count
        })
        
    except Exception as e:
        logger.error(f"Error in bulk action: {str(e)}")
        return jsonify({'error': 'Bulk action failed'}), 500

from datetime import datetime