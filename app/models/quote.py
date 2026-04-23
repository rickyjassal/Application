from datetime import datetime, timedelta
from app import db
from app.models import BaseModel
from app.services.tax import GST_MODE_EXCLUSIVE, calculate_gst_breakdown

class Quote(BaseModel):
    """Quote model"""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired')
    ]
    
    quote_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    
    # Status
    status = db.Column(db.String(50), default='DRAFT')
    
    # Dates
    quote_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    
    # Financial
    gst_mode = db.Column(db.String(20), default=GST_MODE_EXCLUSIVE, nullable=False)
    subtotal = db.Column(db.Float, default=0)
    gst_amount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)
    branding_snapshot = db.Column(db.Text)
    
    # Notes
    notes = db.Column(db.Text)
    terms_and_conditions = db.Column(db.Text)
    
    # Relationships
    line_items = db.relationship('QuoteLineItem', backref='quote', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return '<Quote {}>'.format(self.quote_number)
    
    def get_subtotal(self):
        """Calculate subtotal"""
        if self.subtotal is not None:
            return self.subtotal
        return calculate_gst_breakdown(
            sum(item.get_line_total() for item in self.line_items),
            self.gst_mode,
        )['subtotal']
    
    def get_gst(self):
        """Calculate GST (10% for Australia)"""
        if self.gst_amount is not None:
            return self.gst_amount
        return calculate_gst_breakdown(
            sum(item.get_line_total() for item in self.line_items),
            self.gst_mode,
        )['gst_amount']
    
    def get_total(self):
        """Calculate total including GST"""
        if self.total_amount is not None:
            return self.total_amount
        return calculate_gst_breakdown(
            sum(item.get_line_total() for item in self.line_items),
            self.gst_mode,
        )['total_amount']
    
    def is_expired(self):
        """Check if quote has expired"""
        return datetime.utcnow() > self.expiry_date

    def get_branding(self):
        from app.services.settings import get_document_branding
        return get_document_branding(self)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'quote_number': self.quote_number,
            'customer_id': self.customer_id,
            'status': self.status,
            'quote_date': self.quote_date.isoformat() if self.quote_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'gst_mode': self.gst_mode,
            'subtotal': self.get_subtotal(),
            'gst': self.get_gst(),
            'total': self.get_total(),
            'is_expired': self.is_expired(),
            'branding_snapshot': self.branding_snapshot,
        }


class QuoteLineItem(BaseModel):
    """Quote line item"""
    
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Float, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return '<QuoteLineItem {}>'.format(self.description)
    
    def get_line_total(self):
        """Calculate line total"""
        return self.quantity * self.unit_price
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'quote_id': self.quote_id,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'line_total': self.get_line_total()
        }
