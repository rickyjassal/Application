from flask import Blueprint, request, jsonify
from app import db
from app.models import DiscountCode
from datetime import datetime

discounts_bp = Blueprint('discounts', __name__, url_prefix='/api/discounts')

@discounts_bp.route('', methods=['GET'])
def list_discounts():
    """List all discount codes"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    paginated = DiscountCode.query.paginate(page=page, per_page=per_page)
    
    return {
        'items': [d.to_dict() for d in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }, 200

@discounts_bp.route('', methods=['POST'])
def create_discount():
    """Create a new discount code"""
    data = request.get_json()
    
    discount = DiscountCode(
        code=data.get('code'),
        description=data.get('description'),
        discount_type=data.get('discount_type'),
        discount_value=data.get('discount_value'),
        valid_from=datetime.fromisoformat(data.get('valid_from')) if data.get('valid_from') else None,
        valid_until=datetime.fromisoformat(data.get('valid_until')) if data.get('valid_until') else None,
        max_uses=data.get('max_uses'),
        minimum_order_value=data.get('minimum_order_value', 0),
        maximum_discount_amount=data.get('maximum_discount_amount')
    )
    
    db.session.add(discount)
    db.session.commit()
    
    return discount.to_dict(), 201

@discounts_bp.route('/<int:discount_id>', methods=['GET'])
def get_discount(discount_id):
    """Get a specific discount code"""
    discount = DiscountCode.query.get_or_404(discount_id)
    return discount.to_dict(), 200

@discounts_bp.route('/<int:discount_id>', methods=['PUT'])
def update_discount(discount_id):
    """Update a discount code"""
    discount = DiscountCode.query.get_or_404(discount_id)
    data = request.get_json()
    
    discount.code = data.get('code', discount.code)
    discount.description = data.get('description', discount.description)
    discount.discount_type = data.get('discount_type', discount.discount_type)
    discount.discount_value = data.get('discount_value', discount.discount_value)
    discount.max_uses = data.get('max_uses', discount.max_uses)
    discount.minimum_order_value = data.get('minimum_order_value', discount.minimum_order_value)
    discount.maximum_discount_amount = data.get('maximum_discount_amount', discount.maximum_discount_amount)
    discount.is_active = data.get('is_active', discount.is_active)
    
    db.session.commit()
    
    return discount.to_dict(), 200

@discounts_bp.route('/<int:discount_id>', methods=['DELETE'])
def delete_discount(discount_id):
    """Delete a discount code"""
    discount = DiscountCode.query.get_or_404(discount_id)
    db.session.delete(discount)
    db.session.commit()
    
    return {'message': 'Discount code deleted successfully'}, 200

@discounts_bp.route('/validate/<code>', methods=['POST'])
def validate_discount(code):
    """Validate a discount code"""
    data = request.get_json()
    order_value = data.get('order_value', 0)
    
    discount = DiscountCode.query.filter_by(code=code).first()
    
    if not discount:
        return {'valid': False, 'message': 'Discount code not found'}, 404
    
    if not discount.is_valid():
        return {'valid': False, 'message': 'Discount code is not valid'}, 400
    
    discount_amount = discount.calculate_discount(order_value)
    
    return {
        'valid': True,
        'code': discount.code,
        'discount_amount': discount_amount,
        'final_amount': order_value - discount_amount
    }, 200

@discounts_bp.route('/types', methods=['GET'])
def get_discount_types():
    """Get available discount types"""
    return {
        'types': DiscountCode.DISCOUNT_TYPES
    }, 200
