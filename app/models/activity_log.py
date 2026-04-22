from datetime import datetime

from app import db
from app.models import BaseModel


class ActivityLog(BaseModel):
    """Track important admin and document actions."""

    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer)
    action = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    actor = db.Column(db.String(100))
    created_on = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<ActivityLog {self.entity_type}:{self.action}>'
