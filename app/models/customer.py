from app import db
from app.models import BaseModel

class Customer(BaseModel):
    """Customer model"""
    
    CUSTOMER_TYPES = [
        ('INDIVIDUAL', 'Individual'),
        ('BUSINESS', 'Business'),
        ('CASH', 'Cash Customer')
    ]
    
    # Basic Information
    name = db.Column(db.String(255), nullable=False)
    customer_type = db.Column(db.String(50), default='INDIVIDUAL')
    email = db.Column(db.String(255), unique=False)  # Allow nulls for cash customers
    phone = db.Column(db.String(20))
    
    # Business Information (for business customers)
    business_name = db.Column(db.String(255))
    abn = db.Column(db.String(50))  # Australian Business Number
    acn = db.Column(db.String(50))  # Australian Company Number
    
    # Address Information
    street_address = db.Column(db.String(255))
    suburb = db.Column(db.String(100))
    state = db.Column(db.String(50))
    postcode = db.Column(db.String(10))
    country = db.Column(db.String(100), default='Australia')
    
    # Account Information
    account_balance = db.Column(db.Float, default=0.0)  # For credit accounts
    is_active = db.Column(db.Boolean, default=True)
    
    # GST registration
    is_gst_registered = db.Column(db.Boolean, default=False)
    
    # Relationships
    invoices = db.relationship('Invoice', backref='customer', lazy=True, cascade='all, delete-orphan')
    quotes = db.relationship('Quote', backref='customer', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='customer', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return '<Customer {}>'.format(self.name)
    
    def get_full_address(self):
        """Get formatted full address"""
        parts = [self.street_address, self.suburb, self.state, self.postcode, self.country]
        return ', '.join(filter(None, parts))
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'customer_type': self.customer_type,
            'email': self.email,
            'phone': self.phone,
            'business_name': self.business_name,
            'abn': self.abn,
            'full_address': self.get_full_address(),
            'account_balance': self.account_balance,
            'is_gst_registered': self.is_gst_registered,
            'is_active': self.is_active
        }
