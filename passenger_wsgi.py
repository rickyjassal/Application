import os
import sys

BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, '.env'), override=True)

from app import create_app, db

application = create_app(os.getenv('FLASK_ENV', 'production'))

with application.app_context():
    db.create_all()
