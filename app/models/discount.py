from datetime import datetime
from app import db
from app.models import BaseModel

class DiscountCode(BaseModel):
    """Discount code model"""
    
    DISCOUNT_TYPES = [
        ('PERCENTAGE', 'Percentage'),
        ('FIXED_AMOUNT', 'Fixed Amount')
    ]
    
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    
    # Discount configuration
    discount_type = db.Column(db.String(50), nullable=False)  # PERCENTAGE or FIXED_AMOUNT
    discount_value = db.Column(db.Float, nullable=False)  # percentage value or amount
    
    # Validity
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    
    # Usage limits
    max_uses = db.Column(db.Integer)  # None = unlimited
    current_uses = db.Column(db.Integer, default=0)
    
    # Constraints
    minimum_order_value = db.Column(db.Float, default=0)  # Minimum order value to use this code
    maximum_discount_amount = db.Column(db.Float)  # Maximum discount that can be applied
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return '<DiscountCode {}>'.format(self.code)
    
    def is_valid(self):
        """Check if discount code is currently valid"""
        now = datetime.utcnow()
        
        if not self.is_active:
            return False
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        
        return True
    
    def calculate_discount(self, order_value):
        """Calculate discount amount based on order value"""
        
        if not self.is_valid():
            return 0
        
        if order_value < self.minimum_order_value:
            return 0
        
        if self.discount_type == 'PERCENTAGE':
            discount = (order_value * self.discount_value) / 100
        else:  # FIXED_AMOUNT
            discount = self.discount_value
        
        # Apply maximum discount limit if set
        if self.maximum_discount_amount:
            discount = min(discount, self.maximum_discount_amount)
        
        # Discount cannot exceed order value
        discount = min(discount, order_value)
        
        return discount
    
    def use(self):
        """Increment usage counter"""
        self.current_uses += 1
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'code': self.code,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'is_valid': self.is_valid(),
            'current_uses': self.current_uses,
            'max_uses': self.max_uses,
            'minimum_order_value': self.minimum_order_value,
            'is_active': self.is_active
        }
