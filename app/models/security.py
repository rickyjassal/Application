from app import db
from datetime import datetime


class SecurityQuestion(db.Model):
    """Security questions for password recovery"""
    __tablename__ = 'security_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.String(255), nullable=False)  # Stored as lowercase for comparison
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='security_questions')
    
    def __repr__(self):
        return f'<SecurityQuestion {self.question}>'
