from app import db
from app.models import BaseModel

class Service(BaseModel):
    """Service offering model"""
    
    SERVICE_TYPES = [
        ('IT_REPAIR', 'IT Repair'),
        ('MOBILE_REPAIR', 'Mobile Repair'),
        ('LAPTOP_REPAIR', 'Laptop Repair'),
        ('WEBSITE_DESIGN', 'Website Design'),
        ('OTHER', 'Other Service')
    ]
    
    name = db.Column(db.String(255), nullable=False, unique=True)
    service_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    
    # Pricing
    base_price = db.Column(db.Float, nullable=False)
    hourly_rate = db.Column(db.Float)  # Optional for time-based services
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    invoice_items = db.relationship('InvoiceLineItem', backref='service', lazy=True, cascade='all, delete-orphan')
    quote_items = db.relationship('QuoteLineItem', backref='service', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return '<Service {}>'.format(self.name)
    
    def get_service_type_display(self):
        """Get display name for service type"""
        for code, display in self.SERVICE_TYPES:
            if code == self.service_type:
                return display
        return self.service_type
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'service_type': self.service_type,
            'description': self.description,
            'base_price': self.base_price,
            'hourly_rate': self.hourly_rate,
            'is_active': self.is_active
        }
