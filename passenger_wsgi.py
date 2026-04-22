"""
Bluehost Passenger WSGI entry point
This file is specifically configured for Bluehost Passenger Python support
"""

import sys
import os

# Add the application directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Create and configure the Flask application
from app import create_app, db

app = create_app(os.getenv('FLASK_ENV', 'production'))

# Initialize database tables if they don't exist
with app.app_context():
    db.create_all()

# IMPORTANT: Do not include app.run() at the end
# Passenger will call the 'app' object directly
