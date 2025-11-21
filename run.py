#!/usr/bin/env python3
"""
AI Email Assistant - Main Application Entry Point

This script runs the Flask development server. For production deployment,
use a WSGI server like Gunicorn with the wsgi.py file.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def main():
    """Main function to run the application"""
    # Get environment from environment variable, default to development
    env = os.environ.get('FLASK_ENV', 'development')
    
    # Create Flask app
    app = create_app(env)
    
    # Print startup message
    print("=" * 60)
    print("AI Email Assistant - Development Server")
    print("=" * 60)
    print(f"Environment: {env}")
    print(f"Debug Mode: {app.debug}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI'].split('://')[0]}://...")
    print("=" * 60)
    
    # Run the development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=(env == 'development'),
        use_reloader=(env == 'development')
    )

if __name__ == '__main__':
    main()