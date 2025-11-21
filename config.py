import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///email_assistant.db'
    
    # Email configuration
    IMAP_HOST = os.environ.get('IMAP_HOST', 'imap.gmail.com')
    IMAP_PORT = int(os.environ.get('IMAP_PORT', '993'))
    IMAP_USERNAME = os.environ.get('IMAP_USERNAME')
    IMAP_PASSWORD = os.environ.get('IMAP_PASSWORD')
    
    SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    
    # AI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Security
    BCRYPT_LOG_ROUNDS = 12
    
    # Pagination
    EMAILS_PER_PAGE = 20
    
    # Application settings
    AUTO_FETCH_ENABLED = os.environ.get('AUTO_FETCH_ENABLED', 'false').lower() == 'true'
    FETCH_INTERVAL_MINUTES = int(os.environ.get('FETCH_INTERVAL_MINUTES', '30'))

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}