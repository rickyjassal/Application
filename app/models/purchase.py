from datetime import datetime

from app import db
from app.models import BaseModel
from app.services.tax import GST_MODE_EXCLUSIVE


class Purchase(BaseModel):
    """Supplier purchase header."""

    purchase_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    gst_mode = db.Column(db.String(20), default=GST_MODE_EXCLUSIVE, nullable=False)
    subtotal = db.Column(db.Float, default=0)
    gst_amount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)

    line_items = db.relationship('PurchaseLineItem', backref='purchase', lazy=True, cascade='all, delete-orphan')

    @staticmethod
    def generate_next_purchase_number():
        today = datetime.utcnow()
        date_str = today.strftime('%Y%m%d')
        latest_purchase = Purchase.query.order_by(Purchase.id.desc()).first()
        if latest_purchase and latest_purchase.purchase_number:
            try:
                parts = latest_purchase.purchase_number.split('-')
                sequence = int(parts[-1]) + 1 if len(parts) >= 3 else 1001
            except (ValueError, IndexError):
                sequence = 1001
        else:
            sequence = 1001
        return "PUR-{}-{}".format(date_str, sequence)


class PurchaseLineItem(BaseModel):
    """Line items for supplier purchases."""

    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Float, default=1, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    def get_line_total(self):
        return float(self.quantity or 0) * float(self.unit_price or 0)
