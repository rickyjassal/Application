from flask import Blueprint, request, jsonify
from app import db
from app.models import Product
from datetime import datetime

products_bp = Blueprint('products', __name__, url_prefix='/api/products')

@products_bp.route('', methods=['GET'])
def list_products():
    """List all products"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    paginated = Product.query.paginate(page=page, per_page=per_page)
    
    return {
        'items': [p.to_dict() for p in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }, 200

@products_bp.route('', methods=['POST'])
def create_product():
    """Create a new product"""
    data = request.get_json()
    
    product = Product(
        name=data.get('name'),
        description=data.get('description'),
        sku=data.get('sku'),
        category=data.get('category'),
        cost_price=data.get('cost_price'),
        selling_price=data.get('selling_price'),
        quantity_in_stock=data.get('quantity_in_stock', 0),
        reorder_level=data.get('reorder_level', 10)
    )
    
    db.session.add(product)
    db.session.commit()
    
    return product.to_dict(), 201

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product"""
    product = Product.query.get_or_404(product_id)
    return product.to_dict(), 200

@products_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.sku = data.get('sku', product.sku)
    product.category = data.get('category', product.category)
    product.cost_price = data.get('cost_price', product.cost_price)
    product.selling_price = data.get('selling_price', product.selling_price)
    product.quantity_in_stock = data.get('quantity_in_stock', product.quantity_in_stock)
    product.reorder_level = data.get('reorder_level', product.reorder_level)
    product.is_active = data.get('is_active', product.is_active)
    
    db.session.commit()
    
    return product.to_dict(), 200

@products_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    
    return {'message': 'Product deleted successfully'}, 200

@products_bp.route('/low-stock', methods=['GET'])
def get_low_stock():
    """Get low stock items"""
    products = Product.query.filter(
        Product.quantity_in_stock <= Product.reorder_level
    ).all()
    
    return {
        'items': [p.to_dict() for p in products],
        'count': len(products)
    }, 200
