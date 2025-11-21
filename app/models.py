from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    emails = db.relationship('Email', backref='user', lazy='dynamic')
    ai_usage = db.relationship('AIModelUsage', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class EmailThread(db.Model):
    __tablename__ = 'email_threads'
    
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    subject = db.Column(db.String(500))
    participant_count = db.Column(db.Integer, default=0)
    message_count = db.Column(db.Integer, default=0)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    emails = db.relationship('Email', backref='thread', lazy='dynamic')

    def __repr__(self):
        return f'<EmailThread {self.thread_id}>'


class Email(db.Model):
    __tablename__ = 'emails'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(255), unique=True, nullable=False, index=True)

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('email_threads.id'), nullable=True)
    
    # Email headers
    from_address = db.Column(db.String(255), nullable=False, index=True)
    to_address = db.Column(db.String(255), nullable=False)
    cc_address = db.Column(db.String(500))
    subject = db.Column(db.String(500), nullable=False)
    body = db.Column(db.Text)
    body_plain = db.Column(db.Text)
    body_html = db.Column(db.Text)
    
    # Timestamps
    received_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    replied_at = db.Column(db.DateTime)
    
    # Analysis results
    sentiment = db.Column(db.String(20), index=True)  # positive, negative, neutral
    sentiment_score = db.Column(db.Float)  # confidence score
    priority = db.Column(db.String(20), index=True)  # high, medium, low
    
    # Status and workflow
    status = db.Column(db.String(20), default='new', index=True)  # new, in_progress, replied, ignored
    is_read = db.Column(db.Boolean, default=False)
    is_flagged = db.Column(db.Boolean, default=False)
    
    # AI-generated content
    generated_reply = db.Column(db.Text)
    ai_model_used = db.Column(db.String(50))
    
    # Email metadata
    message_size = db.Column(db.Integer)
    in_reply_to = db.Column(db.String(255))
    references = db.Column(db.Text)
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_email_user_status', 'user_id', 'status'),
        db.Index('idx_email_user_priority', 'user_id', 'priority'),
        db.Index('idx_email_user_sentiment', 'user_id', 'sentiment'),
        db.Index('idx_email_received_at', 'received_at'),
    )
    
    def __repr__(self):
        return f'<Email {self.subject} from {self.from_address}>'
    
    @property
    def sentiment_badge_class(self):
        """Return Bootstrap badge class for sentiment"""
        classes = {
            'positive': 'badge-success',
            'negative': 'badge-danger',
            'neutral': 'badge-secondary'
        }
        return classes.get(self.sentiment, 'badge-secondary')
    
    @property
    def priority_badge_class(self):
        """Return Bootstrap badge class for priority"""
        classes = {
            'high': 'badge-danger',
            'medium': 'badge-warning',
            'low': 'badge-secondary'
        }
        return classes.get(self.priority, 'badge-secondary')
    
    @property
    def status_badge_class(self):
        """Return Bootstrap badge class for status"""
        classes = {
            'new': 'badge-primary',
            'in_progress': 'badge-warning',
            'replied': 'badge-success',
            'ignored': 'badge-secondary'
        }
        return classes.get(self.status, 'badge-secondary')


class EmailAttachment(db.Model):
    __tablename__ = 'email_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('emails.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(100))
    size = db.Column(db.Integer)
    content_id = db.Column(db.String(255))
    is_inline = db.Column(db.Boolean, default=False)
    
    # Relationship
    email = db.relationship('Email', backref='attachments')

    def __repr__(self):
        return f'<EmailAttachment {self.filename}>'


class AIModelUsage(db.Model):
    __tablename__ = 'ai_model_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    model_name = db.Column(db.String(50), nullable=False)
    operation = db.Column(db.String(50), nullable=False)  # sentiment, reply, etc.
    tokens_used = db.Column(db.Integer)
    cost = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AIModelUsage {self.model_name} {self.operation}>'


# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
