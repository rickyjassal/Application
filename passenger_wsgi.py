import os
import site
import sys

BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)
site.addsitedir(os.path.expanduser("~/.local/lib/python3.6/site-packages"))

from app import create_app, db

application = create_app(os.getenv('FLASK_ENV', 'production'))

with application.app_context():
    db.create_all()
