from flask import Blueprint, request, jsonify
from app import db
from app.models import Payment
from datetime import datetime, timedelta
from app.routes.utils import api_login_required

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@payments_bp.route('', methods=['GET'])
@api_login_required
def list_payments():
    """List all payments"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    paginated = Payment.query.order_by(Payment.payment_date.desc()).paginate(page=page, per_page=per_page)
    
    return {
        'items': [p.to_dict() for p in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }, 200

@payments_bp.route('/<int:payment_id>', methods=['GET'])
@api_login_required
def get_payment(payment_id):
    """Get a specific payment"""
    payment = Payment.query.get_or_404(payment_id)
    return payment.to_dict(), 200

@payments_bp.route('/modes', methods=['GET'])
@api_login_required
def get_payment_modes():
    """Get available payment modes"""
    return {
        'modes': Payment.PAYMENT_MODES
    }, 200

@payments_bp.route('/status', methods=['GET'])
@api_login_required
def get_payment_statuses():
    """Get available payment statuses"""
    return {
        'statuses': Payment.PAYMENT_STATUS
    }, 200
