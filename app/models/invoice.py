from datetime import datetime
from app import db
from app.models import BaseModel
from app.services.tax import GST_MODE_EXCLUSIVE

class Invoice(BaseModel):
    """Invoice model"""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ISSUED', 'Issued'),
        ('PAID', 'Paid'),
        ('PARTIAL', 'Partially Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled')
    ]
    
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'))  # Optional - can be based on quote
    
    # Status
    status = db.Column(db.String(50), default='DRAFT')
    
    # Dates
    invoice_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    reference = db.Column(db.String(255))
    
    # Financial
    gst_mode = db.Column(db.String(20), default=GST_MODE_EXCLUSIVE, nullable=False)
    subtotal = db.Column(db.Float, default=0)
    gst_amount = db.Column(db.Float, default=0)
    discount_code_id = db.Column(db.Integer, db.ForeignKey('discount_code.id'))
    discount_amount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)
    amount_paid = db.Column(db.Float, default=0)
    branding_snapshot = db.Column(db.Text)
    resend_count = db.Column(db.Integer, default=0)
    last_resent_at = db.Column(db.DateTime)
    reminder_count = db.Column(db.Integer, default=0)
    last_reminder_at = db.Column(db.DateTime)
    credit_note_amount = db.Column(db.Float, default=0)
    credit_note_reason = db.Column(db.Text)
    
    # Payment mode
    payment_mode = db.Column(db.String(50))  # CASH or ACCOUNT
    
    # Notes
    notes = db.Column(db.Text)
    terms_and_conditions = db.Column(db.Text)
    
    # Relationships
    line_items = db.relationship('InvoiceLineItem', backref='invoice', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='invoice', lazy=True, cascade='all, delete-orphan')
    discount_code = db.relationship('DiscountCode')
    
    def __repr__(self):
        return '<Invoice {}>'.format(self.invoice_number)
    
    def get_balance_due(self):
        """Calculate balance due"""
        effective_total = max((self.total_amount or 0) - float(self.credit_note_amount or 0), 0)
        return effective_total - float(self.amount_paid or 0)
    
    def mark_paid(self):
        """Mark invoice as fully paid"""
        self.amount_paid = self.total_amount
        self.status = 'PAID'

    def get_branding(self):
        from app.services.settings import get_document_branding
        return get_document_branding(self)

    @staticmethod
    def generate_next_invoice_number():
        """Generate next invoice number with format INV-YYYYMMDD-XXXX (continuous series from 1001)"""
        from datetime import timedelta
        
        today = datetime.utcnow()
        date_str = today.strftime('%Y%m%d')
        
        # Find the latest invoice number to get the next series number
        latest_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        
        if latest_invoice and latest_invoice.invoice_number:
            try:
                # Extract the series number from the latest invoice (last 4 digits after the last dash)
                parts = latest_invoice.invoice_number.split('-')
                if len(parts) >= 3:
                    series_number = int(parts[-1]) + 1
                else:
                    series_number = 1001
            except (ValueError, IndexError):
                series_number = 1001
        else:
            series_number = 1001
        
        return "INV-{}-{}".format(date_str, series_number)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'customer_id': self.customer_id,
            'status': self.status,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'reference': self.reference,
            'gst_mode': self.gst_mode,
            'subtotal': self.subtotal,
            'gst_amount': self.gst_amount,
            'discount_amount': self.discount_amount,
            'total_amount': self.total_amount,
            'amount_paid': self.amount_paid,
            'balance_due': self.get_balance_due(),
            'payment_mode': self.payment_mode,
            'credit_note_amount': self.credit_note_amount,
            'credit_note_reason': self.credit_note_reason,
            'reminder_count': self.reminder_count,
            'branding_snapshot': self.branding_snapshot,
        }


class InvoiceLineItem(BaseModel):
    """Invoice line item"""
    
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Float, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return '<InvoiceLineItem {}>'.format(self.description)
    
    def get_line_total(self):
        """Calculate line total"""
        return self.quantity * self.unit_price
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'line_total': self.get_line_total()
        }
