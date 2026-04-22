from app import db
from app.models import ActivityLog


def log_activity(entity_type, action, message, entity_id=None, actor=None):
    entry = ActivityLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        message=message,
        actor=actor,
    )
    db.session.add(entry)
    return entry
