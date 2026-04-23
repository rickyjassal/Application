from flask import Blueprint, request, jsonify
from app import db
from app.models import Quote, QuoteLineItem
from app.routes.utils import api_login_required
from app.services.documents import create_quote_record
from datetime import datetime, timedelta

quotes_bp = Blueprint('quotes', __name__, url_prefix='/api/quotes')

def generate_quote_number():
    """Generate unique quote number with format QT-YYYYMMDD-XXXX (continuous series from 1001)"""
    from app import db
    from app.models import Quote
    
    today = datetime.utcnow()
    date_str = today.strftime('%Y%m%d')
    
    # Find the latest quote number to get the next series number
    latest_quote = Quote.query.order_by(Quote.id.desc()).first()
    
    if latest_quote and latest_quote.quote_number:
        try:
            # Extract the series number from the latest quote (last 4 digits after the last dash)
            parts = latest_quote.quote_number.split('-')
            if len(parts) >= 3:
                series_number = int(parts[-1]) + 1
            else:
                series_number = 1001
        except (ValueError, IndexError):
            series_number = 1001
    else:
        series_number = 1001
    
    return "QT-{}-{}".format(date_str, series_number)

@quotes_bp.route('', methods=['GET'])
@api_login_required
def list_quotes():
    """List all quotes"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = Quote.query
    if status:
        query = query.filter_by(status=status)
    
    paginated = query.paginate(page=page, per_page=per_page)
    
    return {
        'items': [q.to_dict() for q in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }, 200

@quotes_bp.route('', methods=['POST'])
@api_login_required
def create_quote():
    """Create a new quote"""
    data = request.get_json()
    quote = create_quote_record(data or {}, generate_quote_number(), default_expiry_days=30)
    db.session.commit()
    return quote.to_dict(), 201

@quotes_bp.route('/<int:quote_id>', methods=['GET'])
@api_login_required
def get_quote(quote_id):
    """Get a specific quote"""
    quote = Quote.query.get_or_404(quote_id)
    result = quote.to_dict()
    result['line_items'] = [item.to_dict() for item in quote.line_items]
    result['customer'] = quote.customer.to_dict()
    return result, 200

@quotes_bp.route('/<int:quote_id>', methods=['PUT'])
@api_login_required
def update_quote(quote_id):
    """Update a quote"""
    quote = Quote.query.get_or_404(quote_id)
    data = request.get_json()
    
    quote.notes = data.get('notes', quote.notes)
    quote.terms_and_conditions = data.get('terms_and_conditions', quote.terms_and_conditions)
    quote.status = data.get('status', quote.status)
    
    db.session.commit()
    
    return quote.to_dict(), 200

@quotes_bp.route('/<int:quote_id>', methods=['DELETE'])
@api_login_required
def delete_quote(quote_id):
    """Delete a quote"""
    quote = Quote.query.get_or_404(quote_id)
    db.session.delete(quote)
    db.session.commit()
    
    return {'message': 'Quote deleted successfully'}, 200

@quotes_bp.route('/<int:quote_id>/items', methods=['POST'])
@api_login_required
def add_quote_item(quote_id):
    """Add item to quote"""
    quote = Quote.query.get_or_404(quote_id)
    data = request.get_json()
    
    item = QuoteLineItem(
        quote_id=quote_id,
        product_id=data.get('product_id'),
        service_id=data.get('service_id'),
        description=data.get('description'),
        quantity=data.get('quantity', 1),
        unit_price=data.get('unit_price')
    )
    
    db.session.add(item)
    db.session.commit()
    
    return item.to_dict(), 201

@quotes_bp.route('/items/<int:item_id>', methods=['DELETE'])
@api_login_required
def remove_quote_item(item_id):
    """Remove item from quote"""
    item = QuoteLineItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    
    return {'message': 'Item removed successfully'}, 200

@quotes_bp.route('/<int:quote_id>/send', methods=['POST'])
@api_login_required
def send_quote(quote_id):
    """Mark quote as sent"""
    quote = Quote.query.get_or_404(quote_id)
    quote.status = 'SENT'
    db.session.commit()
    
    return {'message': 'Quote sent successfully', 'quote': quote.to_dict()}, 200

@quotes_bp.route('/statuses', methods=['GET'])
@api_login_required
def get_statuses():
    """Get available quote statuses"""
    return {
        'statuses': Quote.STATUS_CHOICES
    }, 200
