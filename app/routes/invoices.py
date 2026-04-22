from flask import Blueprint, request, jsonify
from app import db
from app.models import Invoice, InvoiceLineItem, InventoryTransaction, Payment, DiscountCode, Quote, Customer
from app.routes.utils import api_login_required
from app.services.documents import create_invoice_record
from datetime import datetime, timedelta
from config import Config

invoices_bp = Blueprint('invoices', __name__, url_prefix='/api/invoices')

def generate_invoice_number():
    """Generate unique invoice number"""
    return Invoice.generate_next_invoice_number()

@invoices_bp.route('', methods=['GET'])
@api_login_required
def list_invoices():
    """List all invoices"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = Invoice.query
    if status:
        query = query.filter_by(status=status)
    
    paginated = query.order_by(Invoice.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return {
        'items': [i.to_dict() for i in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }, 200

@invoices_bp.route('', methods=['POST'])
@api_login_required
def create_invoice():
    """Create a new invoice"""
    data = request.get_json()

    invoice = create_invoice_record(data or {}, generate_invoice_number(), default_due_days=7)

    # Update inventory if product
    for item in data.get('line_items', []):
        # Update inventory if product
        if item.get('product_id'):
            product_id = item.get('product_id')
            from app.models import Product
            product = Product.query.get(product_id)
            if product:
                product.quantity_in_stock -= item.get('quantity', 1)
                
                # Create inventory transaction
                inv_trans = InventoryTransaction(
                    product_id=product_id,
                    transaction_type='SALE',
                    quantity=-item.get('quantity', 1),
                    reference_id=invoice.invoice_number
                )
                db.session.add(inv_trans)
    
    # Apply discount if provided
    discount_code_id = data.get('discount_code_id')
    if discount_code_id:
        discount_code = DiscountCode.query.get(discount_code_id)
        if discount_code and discount_code.is_valid():
            invoice.discount_code_id = discount_code_id
            invoice.discount_amount = discount_code.calculate_discount(invoice.subtotal or 0)
            discount_code.use()
    
    # Calculate GST on (subtotal - discount)
    taxable_amount = (invoice.subtotal or 0) - invoice.discount_amount
    invoice.gst_amount = taxable_amount * Config.GST_RATE
    
    # Calculate total
    invoice.total_amount = taxable_amount + invoice.gst_amount
    
    db.session.commit()
    
    return invoice.to_dict(), 201

@invoices_bp.route('/<int:invoice_id>', methods=['GET'])
@api_login_required
def get_invoice(invoice_id):
    """Get a specific invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    result = invoice.to_dict()
    result['line_items'] = [item.to_dict() for item in invoice.line_items]
    result['customer'] = invoice.customer.to_dict()
    result['payments'] = [p.to_dict() for p in invoice.payments]
    return result, 200

@invoices_bp.route('/<int:invoice_id>', methods=['PUT'])
@api_login_required
def update_invoice(invoice_id):
    """Update an invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    data = request.get_json()
    
    invoice.notes = data.get('notes', invoice.notes)
    invoice.terms_and_conditions = data.get('terms_and_conditions', invoice.terms_and_conditions)
    invoice.payment_mode = data.get('payment_mode', invoice.payment_mode)
    invoice.status = data.get('status', invoice.status)
    
    db.session.commit()
    
    return invoice.to_dict(), 200

@invoices_bp.route('/<int:invoice_id>', methods=['DELETE'])
@api_login_required
def delete_invoice(invoice_id):
    """Delete an invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    db.session.delete(invoice)
    db.session.commit()
    
    return {'message': 'Invoice deleted successfully'}, 200

@invoices_bp.route('/<int:invoice_id>/issue', methods=['POST'])
@api_login_required
def issue_invoice(invoice_id):
    """Issue an invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.status = 'ISSUED'
    db.session.commit()
    
    return {'message': 'Invoice issued successfully', 'invoice': invoice.to_dict()}, 200

@invoices_bp.route('/<int:invoice_id>/pay', methods=['POST'])
@api_login_required
def record_payment(invoice_id):
    """Record a payment for invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    data = request.get_json()
    
    payment = Payment(
        invoice_id=invoice_id,
        customer_id=invoice.customer_id,
        amount=data.get('amount'),
        payment_mode=data.get('payment_mode', 'CASH'),
        status='COMPLETED',
        payment_reference=data.get('payment_reference'),
        notes=data.get('notes')
    )
    
    invoice.amount_paid += payment.amount
    
    if invoice.amount_paid >= invoice.total_amount:
        invoice.status = 'PAID'
    elif invoice.amount_paid > 0:
        invoice.status = 'PARTIAL'
    
    db.session.add(payment)
    db.session.commit()
    
    return payment.to_dict(), 201

@invoices_bp.route('/statuses', methods=['GET'])
@api_login_required
def get_statuses():
    """Get available invoice statuses"""
    return {
        'statuses': Invoice.STATUS_CHOICES
    }, 200

@invoices_bp.route('/payment-modes', methods=['GET'])
@api_login_required
def get_payment_modes():
    """Get available payment modes"""
    return {
        'modes': Payment.PAYMENT_MODES
    }, 200

@invoices_bp.route('/<int:invoice_id>/from-quote/<int:quote_id>', methods=['POST'])
@api_login_required
def create_invoice_from_quote(invoice_id, quote_id):
    """Create invoice from an existing quote"""
    quote = Quote.query.get_or_404(quote_id)
    
    # Create invoice
    invoice = Invoice(
        invoice_number=generate_invoice_number(),
        customer_id=quote.customer_id,
        quote_id=quote_id,
        status='DRAFT',
        invoice_date=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=7)
    )
    
    # Copy line items from quote
    for quote_item in quote.line_items:
        invoice_item = InvoiceLineItem(
            product_id=quote_item.product_id,
            service_id=quote_item.service_id,
            description=quote_item.description,
            quantity=quote_item.quantity,
            unit_price=quote_item.unit_price
        )
        invoice.line_items.append(invoice_item)
    
    # Calculate totals
    invoice.subtotal = quote.get_subtotal()
    invoice.gst_amount = quote.get_gst()
    invoice.total_amount = quote.get_total()
    
    db.session.add(invoice)
    quote.status = 'ACCEPTED'
    db.session.commit()
    
    return invoice.to_dict(), 201
