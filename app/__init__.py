from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import inspect, text
from dotenv import load_dotenv
import os
from config import config

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'), override=True)

db = SQLAlchemy()
migrate = Migrate()


def ensure_schema_updates():
    """Apply lightweight schema updates for existing databases."""
    inspector = inspect(db.engine)

    existing_tables = set(inspector.get_table_names())
    if 'invoice' not in existing_tables or 'quote' not in existing_tables:
        return

    invoice_columns = {column['name'] for column in inspector.get_columns('invoice')}
    quote_columns = {column['name'] for column in inspector.get_columns('quote')}

    schema_changed = False

    if 'reference' not in invoice_columns:
        db.session.execute(text("ALTER TABLE invoice ADD COLUMN reference VARCHAR(255)"))
        schema_changed = True

    if 'gst_mode' not in invoice_columns:
        db.session.execute(text("ALTER TABLE invoice ADD COLUMN gst_mode VARCHAR(20) DEFAULT 'exclusive'"))
        schema_changed = True

    if 'resend_count' not in invoice_columns:
        db.session.execute(text("ALTER TABLE invoice ADD COLUMN resend_count INTEGER DEFAULT 0"))
        schema_changed = True

    if 'last_resent_at' not in invoice_columns:
        db.session.execute(text("ALTER TABLE invoice ADD COLUMN last_resent_at DATETIME"))
        schema_changed = True

    if 'reminder_count' not in invoice_columns:
        db.session.execute(text("ALTER TABLE invoice ADD COLUMN reminder_count INTEGER DEFAULT 0"))
        schema_changed = True

    if 'last_reminder_at' not in invoice_columns:
        db.session.execute(text("ALTER TABLE invoice ADD COLUMN last_reminder_at DATETIME"))
        schema_changed = True

    if 'credit_note_amount' not in invoice_columns:
        db.session.execute(text("ALTER TABLE invoice ADD COLUMN credit_note_amount FLOAT DEFAULT 0"))
        schema_changed = True

    if 'credit_note_reason' not in invoice_columns:
        db.session.execute(text("ALTER TABLE invoice ADD COLUMN credit_note_reason TEXT"))
        schema_changed = True

    if 'branding_snapshot' not in invoice_columns:
        db.session.execute(text("ALTER TABLE invoice ADD COLUMN branding_snapshot TEXT"))
        schema_changed = True

    if 'subtotal' not in quote_columns:
        db.session.execute(text("ALTER TABLE quote ADD COLUMN subtotal FLOAT DEFAULT 0"))
        schema_changed = True

    if 'gst_amount' not in quote_columns:
        db.session.execute(text("ALTER TABLE quote ADD COLUMN gst_amount FLOAT DEFAULT 0"))
        schema_changed = True

    if 'total_amount' not in quote_columns:
        db.session.execute(text("ALTER TABLE quote ADD COLUMN total_amount FLOAT DEFAULT 0"))
        schema_changed = True

    if 'gst_mode' not in quote_columns:
        db.session.execute(text("ALTER TABLE quote ADD COLUMN gst_mode VARCHAR(20) DEFAULT 'exclusive'"))
        schema_changed = True

    if 'branding_snapshot' not in quote_columns:
        db.session.execute(text("ALTER TABLE quote ADD COLUMN branding_snapshot TEXT"))
        schema_changed = True

    if schema_changed:
        db.session.commit()


def backfill_document_branding_snapshots():
    """Freeze branding for older documents that predate branding snapshots."""
    from app.models import Invoice, Quote
    from app.services.settings import capture_branding_snapshot, serialize_branding_snapshot

    snapshot = serialize_branding_snapshot(capture_branding_snapshot())
    changed = False

    for invoice in Invoice.query.filter(Invoice.branding_snapshot.is_(None)).all():
        invoice.branding_snapshot = snapshot
        changed = True

    for quote in Quote.query.filter(Quote.branding_snapshot.is_(None)).all():
        quote.branding_snapshot = snapshot
        changed = True

    if changed:
        db.session.commit()


def create_app(config_name=None):
    """Application factory function"""
    
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static',
                static_url_path='/static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Set secret key for sessions
    app.secret_key = app.config.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from app.routes import (
        auth_bp, admin_bp, products_bp, services_bp, customers_bp, 
        invoices_bp, quotes_bp, reports_bp, 
        dashboard_bp, discounts_bp, payments_bp, finance_bp
    )
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(quotes_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(discounts_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(finance_bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
        ensure_schema_updates()
        backfill_document_branding_snapshots()

    from app.services.settings import get_app_settings, get_branding_settings

    @app.context_processor
    def inject_app_settings():
        return {'app_settings': get_app_settings(), 'branding_settings': get_branding_settings()}

    @app.cli.command('send-overdue-reminders')
    def send_overdue_reminders_command():
        """Send overdue reminder emails for invoices due for follow-up."""
        from app.services.reminders import run_overdue_reminders

        sent = run_overdue_reminders(actor='system')
        print(f'Sent {len(sent)} overdue reminder(s).')

    return app
