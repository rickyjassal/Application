from datetime import datetime
from app import db
from app.models import BaseModel

class InventoryTransaction(BaseModel):
    """Inventory transaction model for tracking stock movements"""
    
    TRANSACTION_TYPES = [
        ('PURCHASE', 'Purchase'),
        ('SALE', 'Sale'),
        ('RETURN', 'Return'),
        ('ADJUSTMENT', 'Adjustment'),
        ('DAMAGE', 'Damage/Loss')
    ]
    
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    
    transaction_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reference_id = db.Column(db.String(100))  # Invoice/Quote ID
    
    notes = db.Column(db.Text)
    
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<InventoryTransaction {self.transaction_type} - {self.quantity}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'reference_id': self.reference_id,
            'notes': self.notes,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None
        }
