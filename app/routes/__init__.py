"""
Routes package - Initialize all blueprints
"""

from .auth import auth_bp
from .admin import admin_bp
from .dashboard import dashboard_bp
from .products import products_bp
from .services import services_bp
from .customers import customers_bp
from .invoices import invoices_bp
from .quotes import quotes_bp
from .reports import reports_bp
from .discounts import discounts_bp
from .payments import payments_bp
from .finance import finance_bp

__all__ = [
    'auth_bp',
    'admin_bp',
    'dashboard_bp',
    'products_bp',
    'services_bp',
    'customers_bp',
    'invoices_bp',
    'quotes_bp',
    'reports_bp',
    'discounts_bp',
    'payments_bp',
    'finance_bp'
]
