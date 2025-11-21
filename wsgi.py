#!/usr/bin/env python3
"""
WSGI Entry Point for Production Deployment

This file is used by WSGI servers like Gunicorn for production deployment.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Create the Flask application instance
app = create_app('production')

# Configure logging for production
if __name__ != '__main__':
    import logging
    from logging.handlers import RotatingFileHandler
    
    # Set up file logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/email_assistant.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('AI Email Assistant startup')

# This is the WSGI application instance
application = app