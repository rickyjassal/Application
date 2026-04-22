"""
WSGI entry point for production servers
"""

import os
from app import create_app, db

# Create application instance
app = create_app(os.getenv('FLASK_ENV', 'production'))

# Make sure database is initialized
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run()
