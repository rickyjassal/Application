from flask import Blueprint, request, jsonify
from app import db
from app.models import Invoice, Payment, Product, InventoryTransaction
from datetime import datetime, timedelta
from sqlalchemy import func
from app.routes.utils import api_login_required

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@reports_bp.route('/sales', methods=['GET'])
@api_login_required
def sales_report():
    """Generate sales report"""
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    # Default to last 30 days
    if not from_date:
        from_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
    if not to_date:
        to_date = datetime.utcnow().isoformat()
    
    from_dt = datetime.fromisoformat(from_date)
    to_dt = datetime.fromisoformat(to_date)
    
    invoices = Invoice.query.filter(
        Invoice.invoice_date >= from_dt,
        Invoice.invoice_date <= to_dt,
        Invoice.status.in_(['ISSUED', 'PAID'])
    ).all()
    
    total_sales = sum(inv.total_amount for inv in invoices)
    total_paid = sum(inv.amount_paid for inv in invoices)
    
    return {
        'period': {
            'from': from_date,
            'to': to_date
        },
        'total_invoices': len(invoices),
        'total_sales': total_sales,
        'total_paid': total_paid,
        'outstanding': total_sales - total_paid,
        'invoices': [i.to_dict() for i in invoices]
    }, 200

@reports_bp.route('/purchases', methods=['GET'])
@api_login_required
def purchases_report():
    """Generate purchase/cost report"""
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    # Default to last 30 days
    if not from_date:
        from_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
    if not to_date:
        to_date = datetime.utcnow().isoformat()
    
    from_dt = datetime.fromisoformat(from_date)
    to_dt = datetime.fromisoformat(to_date)
    
    # Get all products sold in period
    invoices = Invoice.query.filter(
        Invoice.invoice_date >= from_dt,
        Invoice.invoice_date <= to_dt,
        Invoice.status.in_(['ISSUED', 'PAID'])
    ).all()
    
    products_sold = {}
    total_cost = 0
    total_revenue = 0
    
    for invoice in invoices:
        for item in invoice.line_items:
            if item.product_id:
                product = item.product
                if product.id not in products_sold:
                    products_sold[product.id] = {
                        'name': product.name,
                        'quantity': 0,
                        'cost': 0,
                        'revenue': 0,
                        'profit': 0
                    }
                
                quantity = item.quantity
                cost = quantity * product.cost_price
                revenue = item.get_line_total()
                
                products_sold[product.id]['quantity'] += quantity
                products_sold[product.id]['cost'] += cost
                products_sold[product.id]['revenue'] += revenue
                products_sold[product.id]['profit'] = products_sold[product.id]['revenue'] - products_sold[product.id]['cost']
                
                total_cost += cost
                total_revenue += revenue
    
    return {
        'period': {
            'from': from_date,
            'to': to_date
        },
        'total_cost': total_cost,
        'total_revenue': total_revenue,
        'total_profit': total_revenue - total_cost,
        'products': products_sold
    }, 200

@reports_bp.route('/profit', methods=['GET'])
@api_login_required
def profit_report():
    """Generate profit report"""
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    # Default to last month
    if not from_date:
        from_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
    if not to_date:
        to_date = datetime.utcnow().isoformat()
    
    from_dt = datetime.fromisoformat(from_date)
    to_dt = datetime.fromisoformat(to_date)
    
    invoices = Invoice.query.filter(
        Invoice.invoice_date >= from_dt,
        Invoice.invoice_date <= to_dt,
        Invoice.status.in_(['ISSUED', 'PAID'])
    ).all()
    
    total_revenue = 0
    total_cost = 0
    
    for invoice in invoices:
        for item in invoice.line_items:
            if item.product_id:
                product = item.product
                total_revenue += item.get_line_total()
                total_cost += item.quantity * product.cost_price
            else:
                # Service - assume margin-based cost
                total_revenue += item.get_line_total()
                # Services typically have higher margins
                total_cost += item.get_line_total() * 0.3  # Assume 30% cost, 70% profit
    
    total_profit = total_revenue - total_cost
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        'period': {
            'from': from_date,
            'to': to_date
        },
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'profit_margin_percentage': round(profit_margin, 2)
    }, 200

@reports_bp.route('/inventory', methods=['GET'])
@api_login_required
def inventory_report():
    """Generate inventory report"""
    products = Product.query.all()
    
    low_stock = []
    sufficient_stock = []
    
    for product in products:
        product_data = product.to_dict()
        product_data['stock_value'] = product.quantity_in_stock * product.selling_price
        
        if product.is_low_stock():
            low_stock.append(product_data)
        else:
            sufficient_stock.append(product_data)
    
    return {
        'total_products': len(products),
        'low_stock_count': len(low_stock),
        'low_stock_items': low_stock,
        'sufficient_stock_items': sufficient_stock
    }, 200

@reports_bp.route('/customer-activity', methods=['GET'])
@api_login_required
def customer_activity_report():
    """Generate customer activity report"""
    from app.models import Customer
    
    customers = Customer.query.all()
    customer_data = []
    
    for customer in customers:
        total_spent = db.session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.customer_id == customer.id,
            Invoice.status.in_(['ISSUED', 'PAID'])
        ).scalar() or 0
        
        invoice_count = Invoice.query.filter_by(customer_id=customer.id).count()
        
        customer_data.append({
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'total_spent': total_spent,
            'invoice_count': invoice_count,
            'account_balance': customer.account_balance
        })
    
    # Sort by total spent
    customer_data.sort(key=lambda x: x['total_spent'], reverse=True)
    
    return {
        'total_customers': len(customers),
        'customers': customer_data
    }, 200
