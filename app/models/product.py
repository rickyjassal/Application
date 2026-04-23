from app import db
from app.models import BaseModel

class Product(BaseModel):
    """Product/Inventory item model"""
    
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    description = db.Column(db.Text)
    sku = db.Column(db.String(100), unique=True, index=True)
    category = db.Column(db.String(100), nullable=False)
    
    # Pricing
    cost_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    
    # Inventory
    quantity_in_stock = db.Column(db.Integer, default=0)
    reorder_level = db.Column(db.Integer, default=10)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    invoice_items = db.relationship('InvoiceLineItem', backref='product', lazy=True, cascade='all, delete-orphan')
    quote_items = db.relationship('QuoteLineItem', backref='product', lazy=True, cascade='all, delete-orphan')
    purchase_items = db.relationship('PurchaseLineItem', backref='product', lazy=True, cascade='all, delete-orphan')
    inventory_transactions = db.relationship('InventoryTransaction', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return '<Product {}>'.format(self.name)
    
    def get_profit_margin(self):
        """Calculate profit margin percentage"""
        if self.cost_price == 0:
            return 0
        return ((self.selling_price - self.cost_price) / self.cost_price) * 100
    
    def is_low_stock(self):
        """Check if product is below reorder level"""
        return self.quantity_in_stock <= self.reorder_level
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sku': self.sku,
            'category': self.category,
            'cost_price': self.cost_price,
            'selling_price': self.selling_price,
            'quantity_in_stock': self.quantity_in_stock,
            'profit_margin': self.get_profit_margin(),
            'is_active': self.is_active,
            'is_low_stock': self.is_low_stock()
        }
