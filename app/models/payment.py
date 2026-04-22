from datetime import datetime
from app import db
from app.models import BaseModel

class Payment(BaseModel):
    """Payment model"""
    
    PAYMENT_MODES = [
        ('CASH', 'Cash'),
        ('ACCOUNT', 'Account/Credit'),
        ('CHEQUE', 'Cheque'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CREDIT_CARD', 'Credit Card')
    ]
    
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded')
    ]
    
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)
    payment_mode = db.Column(db.String(50), nullable=False)
    
    # Reference
    payment_reference = db.Column(db.String(100))  # Cheque number, transaction ID, etc.
    
    # Status
    status = db.Column(db.String(50), default='COMPLETED')
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Notes
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Payment {self.amount} for Invoice {self.invoice_id}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'customer_id': self.customer_id,
            'amount': self.amount,
            'payment_mode': self.payment_mode,
            'status': self.status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_reference': self.payment_reference
        }
