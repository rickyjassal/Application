from datetime import datetime

from app import db


class NotificationRead(db.Model):
    """Track read/unread notification state per admin user."""

    __tablename__ = 'notification_read'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    notification_key = db.Column(db.String(120), nullable=False, index=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    read_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'notification_key', name='uq_notification_read_user_key'),
    )

    def __repr__(self):
        return '<NotificationRead {}:{}:{}>'.format(self.user_id, self.notification_key, self.is_read)
