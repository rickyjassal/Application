from flask import Blueprint, request, jsonify
from app import db
from app.models import Service

services_bp = Blueprint('services', __name__, url_prefix='/api/services')

@services_bp.route('', methods=['GET'])
def list_services():
    """List all services"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    paginated = Service.query.paginate(page=page, per_page=per_page)
    
    return {
        'items': [s.to_dict() for s in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }, 200

@services_bp.route('', methods=['POST'])
def create_service():
    """Create a new service"""
    data = request.get_json()
    
    service = Service(
        name=data.get('name'),
        service_type=data.get('service_type'),
        description=data.get('description'),
        base_price=data.get('base_price'),
        hourly_rate=data.get('hourly_rate')
    )
    
    db.session.add(service)
    db.session.commit()
    
    return service.to_dict(), 201

@services_bp.route('/<int:service_id>', methods=['GET'])
def get_service(service_id):
    """Get a specific service"""
    service = Service.query.get_or_404(service_id)
    return service.to_dict(), 200

@services_bp.route('/<int:service_id>', methods=['PUT'])
def update_service(service_id):
    """Update a service"""
    service = Service.query.get_or_404(service_id)
    data = request.get_json()
    
    service.name = data.get('name', service.name)
    service.service_type = data.get('service_type', service.service_type)
    service.description = data.get('description', service.description)
    service.base_price = data.get('base_price', service.base_price)
    service.hourly_rate = data.get('hourly_rate', service.hourly_rate)
    service.is_active = data.get('is_active', service.is_active)
    
    db.session.commit()
    
    return service.to_dict(), 200

@services_bp.route('/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    """Delete a service"""
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    
    return {'message': 'Service deleted successfully'}, 200

@services_bp.route('/types', methods=['GET'])
def get_service_types():
    """Get available service types"""
    return {
        'types': Service.SERVICE_TYPES
    }, 200
