from app import db
from app.models import BaseModel


class Supplier(BaseModel):
    """Supplier/vendor model for purchase tracking."""

    name = db.Column(db.String(255), nullable=False, index=True)
    business_name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    abn = db.Column(db.String(50))
    street_address = db.Column(db.String(255))
    suburb = db.Column(db.String(100))
    state = db.Column(db.String(50))
    postcode = db.Column(db.String(20))
    country = db.Column(db.String(100), default='Australia')
    is_gst_registered = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)

    purchases = db.relationship('Purchase', backref='supplier', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Supplier {self.name}>'

    def get_full_address(self):
        parts = [self.street_address, self.suburb, self.state, self.postcode, self.country]
        return ', '.join(filter(None, parts))
