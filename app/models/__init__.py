from datetime import datetime
from app import db

class BaseModel(db.Model):
    """Base model with common fields"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# Import all models
from app.models.user import User
from app.models.security import SecurityQuestion
from app.models.product import Product
from app.models.service import Service
from app.models.customer import Customer
from app.models.discount import DiscountCode
from app.models.invoice import Invoice, InvoiceLineItem
from app.models.quote import Quote, QuoteLineItem
from app.models.payment import Payment
from app.models.inventory import InventoryTransaction
from app.models.supplier import Supplier
from app.models.purchase import Purchase, PurchaseLineItem
from app.models.app_setting import AppSetting
from app.models.activity_log import ActivityLog
from app.models.notification_read import NotificationRead

__all__ = [
    'BaseModel',
    'User',
    'SecurityQuestion',
    'Product',
    'Service',
    'Customer',
    'DiscountCode',
    'Invoice',
    'InvoiceLineItem',
    'Quote',
    'QuoteLineItem',
    'Payment',
    'InventoryTransaction',
    'Supplier',
    'Purchase',
    'PurchaseLineItem',
    'AppSetting',
    'ActivityLog',
    'NotificationRead'
]
