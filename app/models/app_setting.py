from app import db
from app.models import BaseModel


class AppSetting(BaseModel):
    """Simple key-value store for business settings."""

    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)

    def __repr__(self):
        return '<AppSetting {}>'.format(self.key)
