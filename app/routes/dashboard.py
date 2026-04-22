from flask import Blueprint, render_template, request
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')

@dashboard_bp.route('/')
def index():
    """Dashboard homepage - HTML UI"""
    try:
        return render_template('dashboard.html')
    except:
        # Fallback to JSON if template not found
        return {
            'message': 'Welcome to Business Management System',
            'version': '1.0.0'
        }, 200

@dashboard_bp.route('/api')
def api_index():
    """API endpoint"""
    return {
        'message': 'Welcome to Business Management System',
        'version': '1.0.0'
    }, 200

@dashboard_bp.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    from app.models import Invoice, Product, Customer, Payment, Quote
    from app import db
    from datetime import datetime, timedelta
    
    # Calculate stats for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    total_revenue = db.session.query(db.func.sum(Invoice.total_amount)).filter(
        Invoice.invoice_date >= thirty_days_ago,
        Invoice.status.in_(['ISSUED', 'PAID'])
    ).scalar() or 0
    
    total_customers = Customer.query.count()
    low_stock_products = Product.query.filter(
        Product.quantity_in_stock <= Product.reorder_level
    ).count()
    
    # Get quote notifications
    accepted_quotes = Quote.query.filter_by(status='ACCEPTED').all()
    rejected_quotes = Quote.query.filter_by(status='REJECTED').all()
    
    notifications = []
    
    for quote in accepted_quotes:
        notifications.append({
            'type': 'quote_accepted',
            'message': f'Quote {quote.quote_number} from {quote.customer.name if quote.customer else "Customer"} has been accepted',
            'quote_id': quote.id,
            'quote_number': quote.quote_number,
            'customer_name': quote.customer.name if quote.customer else 'Unknown',
            'date': quote.quote_date.isoformat() if quote.quote_date else None
        })
    
    for quote in rejected_quotes:
        notifications.append({
            'type': 'quote_rejected',
            'message': f'Quote {quote.quote_number} from {quote.customer.name if quote.customer else "Customer"} has been rejected',
            'quote_id': quote.id,
            'quote_number': quote.quote_number,
            'customer_name': quote.customer.name if quote.customer else 'Unknown',
            'date': quote.quote_date.isoformat() if quote.quote_date else None
        })
    
    return {
        'revenue_30_days': total_revenue,
        'total_customers': total_customers,
        'low_stock_items': low_stock_products,
        'notifications': notifications,
        'accepted_quotes_count': len(accepted_quotes),
        'rejected_quotes_count': len(rejected_quotes)
    }, 200

@dashboard_bp.route('/api/invoices/overdue')
def get_overdue_invoices():
    """Get overdue invoices with pagination"""
    from app.models import Invoice
    from app import db
    
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    today = datetime.utcnow().date()
    overdue_invoices = Invoice.query.filter(
        Invoice.due_date < today,
        Invoice.status != 'PAID'
    ).order_by(Invoice.due_date.desc()).paginate(page=page, per_page=per_page)
    
    return {
        'items': [{
            'id': inv.id,
            'invoice_number': inv.invoice_number,
            'customer_name': inv.customer.name if inv.customer else 'Unknown',
            'total_amount': float(inv.total_amount),
            'status': inv.status,
            'due_date': inv.due_date.isoformat() if inv.due_date else None,
            'days_overdue': (today - inv.due_date).days if inv.due_date else 0
        } for inv in overdue_invoices.items],
        'total': overdue_invoices.total,
        'pages': overdue_invoices.pages,
        'current_page': page
    }, 200

@dashboard_bp.route('/api/invoices/recent')
def get_recent_invoices():
    """Get recent invoices with pagination"""
    from app.models import Invoice
    from app import db
    
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    recent_invoices = Invoice.query.order_by(Invoice.invoice_date.desc()).paginate(page=page, per_page=per_page)
    
    return {
        'items': [{
            'id': inv.id,
            'invoice_number': inv.invoice_number,
            'customer_name': inv.customer.name if inv.customer else 'Unknown',
            'total_amount': float(inv.total_amount),
            'status': inv.status,
            'invoice_date': inv.invoice_date.isoformat() if inv.invoice_date else None
        } for inv in recent_invoices.items],
        'total': recent_invoices.total,
        'pages': recent_invoices.pages,
        'current_page': page
    }, 200

@dashboard_bp.route('/api/quotes/recent')
def get_recent_quotes():
    """Get recent quotes with pagination"""
    from app.models import Quote
    from app import db
    
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    recent_quotes = Quote.query.order_by(Quote.quote_date.desc()).paginate(page=page, per_page=per_page)
    
    return {
        'items': [{
            'id': quote.id,
            'quote_number': quote.quote_number,
            'customer_name': quote.customer.name if quote.customer else 'Unknown',
            'total_amount': float(quote.total_amount),
            'status': quote.status,
            'quote_date': quote.quote_date.isoformat() if quote.quote_date else None
        } for quote in recent_quotes.items],
        'total': recent_quotes.total,
        'pages': recent_quotes.pages,
        'current_page': page
    }, 200
