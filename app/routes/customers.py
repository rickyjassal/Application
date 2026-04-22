from flask import Blueprint, request, jsonify
from app import db
from app.models import Customer

customers_bp = Blueprint('customers', __name__, url_prefix='/api/customers')

@customers_bp.route('', methods=['GET'])
def list_customers():
    """List all customers"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    paginated = Customer.query.paginate(page=page, per_page=per_page)
    
    return {
        'items': [c.to_dict() for c in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }, 200

@customers_bp.route('', methods=['POST'])
def create_customer():
    """Create a new customer"""
    data = request.get_json()
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()

    if not name:
        return {'success': False, 'message': 'Customer name is required.'}, 400
    if not email:
        return {'success': False, 'message': 'Customer email is required.'}, 400
    
    customer = Customer(
        name=name,
        customer_type=data.get('customer_type', 'INDIVIDUAL'),
        email=email,
        phone=data.get('phone'),
        business_name=data.get('business_name'),
        abn=data.get('abn'),
        acn=data.get('acn'),
        street_address=data.get('street_address'),
        suburb=data.get('suburb'),
        state=data.get('state'),
        postcode=data.get('postcode'),
        country=data.get('country', 'Australia'),
        is_gst_registered=data.get('is_gst_registered', False)
    )
    
    db.session.add(customer)
    db.session.commit()
    
    return customer.to_dict(), 201

@customers_bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get a specific customer"""
    customer = Customer.query.get_or_404(customer_id)
    return customer.to_dict(), 200

@customers_bp.route('/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Update a customer"""
    customer = Customer.query.get_or_404(customer_id)
    data = request.get_json()
    name = (data.get('name') if data.get('name') is not None else customer.name or '').strip()
    email = (data.get('email') if data.get('email') is not None else customer.email or '').strip()

    if not name:
        return {'success': False, 'message': 'Customer name is required.'}, 400
    if not email:
        return {'success': False, 'message': 'Customer email is required.'}, 400
    
    customer.name = name
    customer.customer_type = data.get('customer_type', customer.customer_type)
    customer.email = email
    customer.phone = data.get('phone', customer.phone)
    customer.business_name = data.get('business_name', customer.business_name)
    customer.abn = data.get('abn', customer.abn)
    customer.acn = data.get('acn', customer.acn)
    customer.street_address = data.get('street_address', customer.street_address)
    customer.suburb = data.get('suburb', customer.suburb)
    customer.state = data.get('state', customer.state)
    customer.postcode = data.get('postcode', customer.postcode)
    customer.country = data.get('country', customer.country)
    customer.is_gst_registered = data.get('is_gst_registered', customer.is_gst_registered)
    
    db.session.commit()
    
    return customer.to_dict(), 200

@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete a customer"""
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    
    return {'message': 'Customer deleted successfully'}, 200

@customers_bp.route('/types', methods=['GET'])
def get_customer_types():
    """Get available customer types"""
    return {
        'types': Customer.CUSTOMER_TYPES
    }, 200
