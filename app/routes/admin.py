from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, current_app, has_request_context, Response
from app import db
from app.models import (
    Product,
    Customer,
    Service,
    Quote,
    Invoice,
    QuoteLineItem,
    InvoiceLineItem,
    InventoryTransaction,
    Supplier,
    Purchase,
    PurchaseLineItem,
    AppSetting,
    ActivityLog,
    Payment,
    NotificationRead,
)
from app.services.mailer import send_email
from app.services.documents import (
    calculate_document_totals,
    create_invoice_record,
    create_quote_record,
)
from app.services.pdf_generator import QuotePDFGenerator
from app.services.invoice_pdf_generator import InvoicePDFGenerator
from app.services.email_templates import QuoteEmailTemplate
from app.services.invoice_email_templates import InvoiceEmailTemplate
from app.services.tax import (
    GST_MODE_EXCLUSIVE,
    GST_MODE_CHOICES,
    calculate_gst_breakdown,
    gst_label,
)
from app.services.settings import get_app_settings, update_settings, get_branding_settings, get_document_branding
from app.services.activity import log_activity
from app.services.reminders import get_due_overdue_invoices, run_overdue_reminders
from app.services.statement_pdf_generator import StatementPDFGenerator
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import or_
import uuid
import json
import os
from werkzeug.utils import secure_filename

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def refresh_overdue_invoices():
    """Mark due invoices as overdue when their due date has passed."""
    now = datetime.utcnow()
    overdue_invoices = Invoice.query.filter(
        Invoice.due_date.isnot(None),
        Invoice.due_date < now,
        Invoice.status.in_(['DRAFT', 'ISSUED', 'PARTIAL'])
    ).all()

    updated = False
    for invoice in overdue_invoices:
        if invoice.amount_paid >= (invoice.total_amount or 0):
            continue
        if invoice.status != 'OVERDUE':
            invoice.status = 'OVERDUE'
            updated = True

    if updated:
        db.session.commit()


def build_public_url(path):
    if has_request_context():
        base = request.url_root.rstrip('/')
    else:
        base = current_app.config.get('APP_BASE_URL', '').rstrip('/')
    return f'{base}{path}'


def build_dashboard_notifications(user_id):
    """Build dashboard bell notifications with read/unread state."""
    overdue_invoices = (
        Invoice.query
        .filter(Invoice.status == 'OVERDUE')
        .order_by(Invoice.due_date.asc(), Invoice.id.asc())
        .all()
    )
    reminder_candidates = get_due_overdue_invoices()
    low_stock_items = [product for product in Product.query.order_by(Product.quantity_in_stock.asc()).all() if product.is_low_stock()]

    read_rows = NotificationRead.query.filter_by(user_id=user_id).all() if user_id else []
    read_lookup = {row.notification_key: row for row in read_rows}

    notifications = []

    for invoice in overdue_invoices:
        key = f'invoice-overdue-{invoice.id}'
        row = read_lookup.get(key)
        notifications.append({
            'key': key,
            'group': 'Overdue Invoices',
            'title': invoice.invoice_number,
            'detail': f"{invoice.customer.name if invoice.customer else 'Unknown customer'} | Due {invoice.due_date.strftime('%d-%m-%Y') if invoice.due_date else 'N/A'}",
            'url': url_for('admin.view_invoice', invoice_id=invoice.id),
            'is_read': bool(row.is_read) if row else False,
            'sort_at': invoice.due_date or invoice.updated_at or invoice.created_at,
        })

    for invoice in reminder_candidates:
        key = f'invoice-reminder-{invoice.id}'
        row = read_lookup.get(key)
        notifications.append({
            'key': key,
            'group': 'Reminder Queue',
            'title': invoice.invoice_number,
            'detail': f"Reminder due for {invoice.customer.name if invoice.customer else 'Unknown customer'}",
            'url': url_for('admin.view_invoice', invoice_id=invoice.id),
            'is_read': bool(row.is_read) if row else False,
            'sort_at': invoice.last_reminder_at or invoice.due_date or invoice.updated_at or invoice.created_at,
        })

    for product in low_stock_items:
        key = f'product-lowstock-{product.id}'
        row = read_lookup.get(key)
        notifications.append({
            'key': key,
            'group': 'Low Stock',
            'title': product.name,
            'detail': f'{product.quantity_in_stock} left, reorder at {product.reorder_level}',
            'url': url_for('admin.inventory'),
            'is_read': bool(row.is_read) if row else False,
            'sort_at': product.updated_at or product.created_at,
        })

    notifications.sort(key=lambda item: item['sort_at'] or datetime.utcnow(), reverse=True)
    unread_count = sum(1 for item in notifications if not item['is_read'])
    return {
        'items': notifications,
        'unread_count': unread_count,
        'overdue_invoices': overdue_invoices,
        'reminder_candidates': reminder_candidates,
        'low_stock_items': low_stock_items,
    }


def set_notification_state(user_id, notification_key, is_read):
    row = NotificationRead.query.filter_by(user_id=user_id, notification_key=notification_key).first()
    if not row:
        row = NotificationRead(user_id=user_id, notification_key=notification_key)
        db.session.add(row)
    row.is_read = is_read
    row.read_at = datetime.utcnow() if is_read else None
    return row


def send_invoice_email_message(invoice):
    """Send invoice email with PDF attachment and attractive HTML template"""
    if not invoice.customer or not invoice.customer.email:
        raise RuntimeError('Customer record is missing email.')

    # Generate subject and text body
    branding = get_document_branding(invoice)
    business_name = branding.get('business_name', 'Western IT Solutions')
    subject = f'Invoice {invoice.invoice_number} from {business_name}'
    text_body = (
        f"Hello {invoice.customer.name},\n\n"
        f"Please find your invoice {invoice.invoice_number} attached.\n"
        f"Invoice total: ${invoice.total_amount:.2f}\n"
        f"Advance paid: ${invoice.amount_paid:.2f}\n"
        f"Balance due: ${invoice.get_balance_due():.2f}\n"
        f"Due date: {invoice.due_date.strftime('%d/%b/%Y') if invoice.due_date else 'N/A'}\n\n"
        f"Regards,\nAccounts\n{business_name}"
    )
    
    # Generate attractive HTML body
    html_body = InvoiceEmailTemplate.generate_invoice_email(
        invoice,
        business_name=business_name
    )
    
    # Generate PDF
    pdf_generator = InvoicePDFGenerator(invoice)
    pdf_buffer = pdf_generator.generate()
    pdf_filename = f'Invoice_{invoice.invoice_number}.pdf'
    
    # Send email with PDF attachment
    attachments = [(pdf_filename, pdf_buffer)]
    send_email(invoice.customer.email, subject, text_body, html_body, attachments)


def send_quote_email_message(quote):
    """Send quote email with PDF attachment and attractive HTML template"""
    if not quote.customer or not quote.customer.email:
        raise RuntimeError('Customer record is missing email.')

    # Build URLs for accept/reject (admin blueprint prefix is /admin)
    accept_url = build_public_url(f'/admin/quote/{quote.id}/accept')
    reject_url = build_public_url(f'/admin/quote/{quote.id}/reject')
    
    # Generate subject and text body
    branding = get_document_branding(quote)
    business_name = branding.get('business_name', 'Western IT Solutions')
    subject = f'Quote {quote.quote_number} from {business_name}'
    text_body = (
        f"Hello {quote.customer.name},\n\n"
        f"Please find your quote {quote.quote_number} attached.\n"
        f"Quote total: ${quote.get_total():.2f}\n"
        f"Expiry date: {quote.expiry_date.strftime('%d/%b/%Y') if quote.expiry_date else 'N/A'}\n\n"
        f"Accept: {accept_url}\n"
        f"Reject: {reject_url}\n\n"
        f"Regards,\nAccounts\n{business_name}"
    )
    
    # Generate attractive HTML body
    html_body = QuoteEmailTemplate.generate_quote_email(
        quote, 
        accept_url, 
        reject_url,
        business_name=business_name
    )
    
    # Generate PDF
    pdf_generator = QuotePDFGenerator(quote)
    pdf_buffer = pdf_generator.generate()
    pdf_filename = f'Quote_{quote.quote_number}.pdf'
    
    # Send email with PDF attachment
    attachments = [(pdf_filename, pdf_buffer)]
    send_email(quote.customer.email, subject, text_body, html_body, attachments)


def calculate_effective_invoice_total(invoice):
    return max(float(invoice.total_amount or 0) - float(invoice.credit_note_amount or 0), 0)


def recalculate_invoice_status(invoice):
    effective_total = calculate_effective_invoice_total(invoice)
    amount_paid = float(invoice.amount_paid or 0)

    if effective_total <= 0:
        invoice.status = 'PAID'
    elif amount_paid >= effective_total:
        invoice.status = 'PAID'
    elif amount_paid > 0:
        invoice.status = 'PARTIAL'
    elif invoice.due_date and invoice.due_date < datetime.utcnow():
        invoice.status = 'OVERDUE'
    elif invoice.status not in ['CANCELLED']:
        invoice.status = 'ISSUED'
    return invoice.status


def invoice_line_to_dict(item):
    return {
        'id': item.id,
        'product_id': item.product_id,
        'service_id': item.service_id,
        'description': item.description,
        'quantity': item.quantity,
        'unit_price': item.unit_price,
    }


def quote_line_to_dict(item):
    return {
        'id': item.id,
        'product_id': item.product_id,
        'service_id': item.service_id,
        'description': item.description,
        'quantity': item.quantity,
        'unit_price': item.unit_price,
    }


def purchase_line_to_dict(item):
    return {
        'id': item.id,
        'product_id': item.product_id,
        'description': item.description,
        'quantity': item.quantity,
        'unit_price': item.unit_price,
    }


def quote_to_backup_dict(quote):
    payload = quote.to_dict()
    payload.update({
        'notes': quote.notes,
        'terms_and_conditions': quote.terms_and_conditions,
        'branding_snapshot': quote.branding_snapshot,
        'line_items': [quote_line_to_dict(item) for item in quote.line_items],
    })
    return payload


def invoice_to_backup_dict(invoice):
    payload = invoice.to_dict()
    payload.update({
        'quote_id': invoice.quote_id,
        'notes': invoice.notes,
        'terms_and_conditions': invoice.terms_and_conditions,
        'payment_mode': invoice.payment_mode,
        'branding_snapshot': invoice.branding_snapshot,
        'resend_count': invoice.resend_count,
        'last_resent_at': invoice.last_resent_at.isoformat() if invoice.last_resent_at else None,
        'last_reminder_at': invoice.last_reminder_at.isoformat() if invoice.last_reminder_at else None,
        'line_items': [invoice_line_to_dict(item) for item in invoice.line_items],
    })
    return payload


def purchase_to_backup_dict(purchase):
    return {
        'id': purchase.id,
        'purchase_number': purchase.purchase_number,
        'supplier_id': purchase.supplier_id,
        'purchase_date': purchase.purchase_date.isoformat() if purchase.purchase_date else None,
        'gst_mode': purchase.gst_mode,
        'subtotal': purchase.subtotal,
        'gst_amount': purchase.gst_amount,
        'total_amount': purchase.total_amount,
        'notes': purchase.notes,
        'line_items': [purchase_line_to_dict(item) for item in purchase.line_items],
    }


def supplier_to_backup_dict(supplier):
    return {
        'id': supplier.id,
        'name': supplier.name,
        'business_name': supplier.business_name,
        'email': supplier.email,
        'phone': supplier.phone,
        'abn': supplier.abn,
        'street_address': supplier.street_address,
        'suburb': supplier.suburb,
        'state': supplier.state,
        'postcode': supplier.postcode,
        'country': supplier.country,
        'is_gst_registered': supplier.is_gst_registered,
        'notes': supplier.notes,
    }


def customer_to_backup_dict(customer):
    return {
        'id': customer.id,
        'name': customer.name,
        'customer_type': customer.customer_type,
        'email': customer.email,
        'phone': customer.phone,
        'business_name': customer.business_name,
        'abn': customer.abn,
        'street_address': customer.street_address,
        'suburb': customer.suburb,
        'state': customer.state,
        'postcode': customer.postcode,
        'country': customer.country,
        'account_balance': customer.account_balance,
        'is_gst_registered': customer.is_gst_registered,
        'is_active': customer.is_active,
    }


def product_to_backup_dict(product):
    return {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'sku': product.sku,
        'category': product.category,
        'cost_price': product.cost_price,
        'selling_price': product.selling_price,
        'quantity_in_stock': product.quantity_in_stock,
        'reorder_level': product.reorder_level,
        'is_active': product.is_active,
    }


def service_to_backup_dict(service):
    return {
        'id': service.id,
        'name': service.name,
        'service_type': service.service_type,
        'description': service.description,
        'base_price': service.base_price,
        'hourly_rate': service.hourly_rate,
        'is_active': service.is_active,
    }


def payment_to_backup_dict(payment):
    return {
        'id': payment.id,
        'invoice_id': payment.invoice_id,
        'customer_id': payment.customer_id,
        'amount': payment.amount,
        'payment_mode': payment.payment_mode,
        'status': payment.status,
        'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
        'payment_reference': payment.payment_reference,
        'notes': payment.notes,
    }


def parse_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def sync_fields(instance, payload, field_map):
    for attr, default in field_map.items():
        value = payload.get(attr, default)
        setattr(instance, attr, value)


def restore_backup_payload(payload):
    summary = {
        'customers': 0,
        'products': 0,
        'services': 0,
        'suppliers': 0,
        'quotes': 0,
        'invoices': 0,
        'payments': 0,
        'purchases': 0,
        'inventory_transactions': 0,
    }

    settings_payload = payload.get('settings') or {}
    if settings_payload:
        update_settings(settings_payload)

    for item in payload.get('customers', []):
        customer = Customer.query.get(item.get('id')) if item.get('id') else None
        if not customer:
            customer = Customer(id=item.get('id'))
            db.session.add(customer)
        customer.name = item.get('name') or customer.name
        customer.customer_type = item.get('customer_type') or 'INDIVIDUAL'
        customer.email = item.get('email')
        customer.phone = item.get('phone')
        customer.business_name = item.get('business_name')
        customer.abn = item.get('abn')
        customer.street_address = item.get('street_address')
        customer.suburb = item.get('suburb')
        customer.state = item.get('state')
        customer.postcode = item.get('postcode')
        customer.country = item.get('country') or 'Australia'
        customer.account_balance = float(item.get('account_balance') or 0)
        customer.is_gst_registered = bool(item.get('is_gst_registered', False))
        customer.is_active = bool(item.get('is_active', True))
        summary['customers'] += 1

    for item in payload.get('products', []):
        product = Product.query.get(item.get('id')) if item.get('id') else None
        if not product:
            product = Product(id=item.get('id'))
            db.session.add(product)
        product.name = item.get('name') or product.name
        product.description = item.get('description')
        product.sku = item.get('sku')
        product.category = item.get('category') or product.category or 'General'
        product.cost_price = float(item.get('cost_price') or 0)
        product.selling_price = float(item.get('selling_price') or 0)
        product.quantity_in_stock = int(item.get('quantity_in_stock') or 0)
        product.reorder_level = int(item.get('reorder_level') or product.reorder_level or 10)
        product.is_active = bool(item.get('is_active', True))
        summary['products'] += 1

    for item in payload.get('services', []):
        service = Service.query.get(item.get('id')) if item.get('id') else None
        if not service:
            service = Service(id=item.get('id'))
            db.session.add(service)
        service.name = item.get('name') or service.name
        service.service_type = item.get('service_type') or service.service_type or 'OTHER'
        service.description = item.get('description')
        service.base_price = float(item.get('base_price') or 0)
        service.hourly_rate = float(item['hourly_rate']) if item.get('hourly_rate') is not None else None
        service.is_active = bool(item.get('is_active', True))
        summary['services'] += 1

    for item in payload.get('suppliers', []):
        supplier = Supplier.query.get(item.get('id')) if item.get('id') else None
        if not supplier:
            supplier = Supplier(id=item.get('id'))
            db.session.add(supplier)
        supplier.name = item.get('name') or supplier.name
        supplier.business_name = item.get('business_name')
        supplier.email = item.get('email')
        supplier.phone = item.get('phone')
        supplier.abn = item.get('abn')
        supplier.street_address = item.get('street_address')
        supplier.suburb = item.get('suburb')
        supplier.state = item.get('state')
        supplier.postcode = item.get('postcode')
        supplier.country = item.get('country') or 'Australia'
        supplier.is_gst_registered = bool(item.get('is_gst_registered', True))
        supplier.notes = item.get('notes')
        summary['suppliers'] += 1

    db.session.flush()

    for item in payload.get('quotes', []):
        quote = Quote.query.get(item.get('id')) if item.get('id') else None
        if not quote:
            quote = Quote(id=item.get('id'))
            db.session.add(quote)
        quote.quote_number = item.get('quote_number') or quote.quote_number
        quote.customer_id = item.get('customer_id')
        quote.status = item.get('status') or 'DRAFT'
        quote.quote_date = parse_datetime(item.get('quote_date')) or datetime.utcnow()
        quote.expiry_date = parse_datetime(item.get('expiry_date'))
        quote.gst_mode = item.get('gst_mode') or GST_MODE_EXCLUSIVE
        quote.subtotal = float(item.get('subtotal') or 0)
        quote.gst_amount = float(item.get('gst') or item.get('gst_amount') or 0)
        quote.total_amount = float(item.get('total') or item.get('total_amount') or 0)
        quote.branding_snapshot = item.get('branding_snapshot')
        quote.notes = item.get('notes')
        quote.terms_and_conditions = item.get('terms_and_conditions')
        quote.line_items.clear()
        for line in item.get('line_items', []):
            quote.line_items.append(QuoteLineItem(
                id=line.get('id'),
                product_id=line.get('product_id'),
                service_id=line.get('service_id'),
                description=line.get('description') or '',
                quantity=float(line.get('quantity') or 0),
                unit_price=float(line.get('unit_price') or 0),
            ))
        summary['quotes'] += 1

    for item in payload.get('invoices', []):
        invoice = Invoice.query.get(item.get('id')) if item.get('id') else None
        if not invoice:
            invoice = Invoice(id=item.get('id'))
            db.session.add(invoice)
        invoice.invoice_number = item.get('invoice_number') or invoice.invoice_number
        invoice.customer_id = item.get('customer_id')
        invoice.quote_id = item.get('quote_id')
        invoice.status = item.get('status') or 'DRAFT'
        invoice.invoice_date = parse_datetime(item.get('invoice_date')) or datetime.utcnow()
        invoice.due_date = parse_datetime(item.get('due_date'))
        invoice.reference = item.get('reference')
        invoice.gst_mode = item.get('gst_mode') or GST_MODE_EXCLUSIVE
        invoice.subtotal = float(item.get('subtotal') or 0)
        invoice.gst_amount = float(item.get('gst_amount') or 0)
        invoice.discount_amount = float(item.get('discount_amount') or 0)
        invoice.total_amount = float(item.get('total_amount') or 0)
        invoice.amount_paid = float(item.get('amount_paid') or 0)
        invoice.branding_snapshot = item.get('branding_snapshot')
        invoice.payment_mode = item.get('payment_mode')
        invoice.notes = item.get('notes')
        invoice.terms_and_conditions = item.get('terms_and_conditions')
        invoice.resend_count = int(item.get('resend_count') or 0)
        invoice.last_resent_at = parse_datetime(item.get('last_resent_at'))
        invoice.reminder_count = int(item.get('reminder_count') or 0)
        invoice.last_reminder_at = parse_datetime(item.get('last_reminder_at'))
        invoice.credit_note_amount = float(item.get('credit_note_amount') or 0)
        invoice.credit_note_reason = item.get('credit_note_reason')
        invoice.line_items.clear()
        for line in item.get('line_items', []):
            invoice.line_items.append(InvoiceLineItem(
                id=line.get('id'),
                product_id=line.get('product_id'),
                service_id=line.get('service_id'),
                description=line.get('description') or '',
                quantity=float(line.get('quantity') or 0),
                unit_price=float(line.get('unit_price') or 0),
            ))
        summary['invoices'] += 1

    for item in payload.get('purchases', []):
        purchase = Purchase.query.get(item.get('id')) if item.get('id') else None
        if not purchase:
            purchase = Purchase(id=item.get('id'))
            db.session.add(purchase)
        purchase.purchase_number = item.get('purchase_number') or purchase.purchase_number
        purchase.supplier_id = item.get('supplier_id')
        purchase.purchase_date = parse_datetime(item.get('purchase_date')) or datetime.utcnow()
        purchase.gst_mode = item.get('gst_mode') or GST_MODE_EXCLUSIVE
        purchase.subtotal = float(item.get('subtotal') or 0)
        purchase.gst_amount = float(item.get('gst_amount') or 0)
        purchase.total_amount = float(item.get('total_amount') or 0)
        purchase.notes = item.get('notes')
        purchase.line_items.clear()
        for line in item.get('line_items', []):
            purchase.line_items.append(PurchaseLineItem(
                id=line.get('id'),
                product_id=line.get('product_id'),
                description=line.get('description') or '',
                quantity=float(line.get('quantity') or 0),
                unit_price=float(line.get('unit_price') or 0),
            ))
        summary['purchases'] += 1

    for item in payload.get('payments', []):
        payment = Payment.query.get(item.get('id')) if item.get('id') else None
        if not payment:
            payment = Payment(id=item.get('id'))
            db.session.add(payment)
        payment.invoice_id = item.get('invoice_id')
        payment.customer_id = item.get('customer_id')
        payment.amount = float(item.get('amount') or 0)
        payment.payment_mode = item.get('payment_mode') or 'BANK_TRANSFER'
        payment.status = item.get('status') or 'COMPLETED'
        payment.payment_date = parse_datetime(item.get('payment_date')) or datetime.utcnow()
        payment.payment_reference = item.get('payment_reference')
        payment.notes = item.get('notes')
        summary['payments'] += 1

    for item in payload.get('inventory_transactions', []):
        transaction = InventoryTransaction.query.get(item.get('id')) if item.get('id') else None
        if not transaction:
            transaction = InventoryTransaction(id=item.get('id'))
            db.session.add(transaction)
        transaction.product_id = item.get('product_id')
        transaction.transaction_type = item.get('transaction_type') or 'ADJUSTMENT'
        transaction.quantity = int(item.get('quantity') or 0)
        transaction.reference_id = item.get('reference_id')
        transaction.notes = item.get('notes')
        transaction.transaction_date = parse_datetime(item.get('transaction_date')) or datetime.utcnow()
        summary['inventory_transactions'] += 1

    return summary


@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Admin dashboard with statistics and quick actions"""
    try:
        refresh_overdue_invoices()
        notifications = build_dashboard_notifications(session.get('user_id'))
        low_stock_items = notifications['low_stock_items']
        overdue_invoices = notifications['overdue_invoices']
        reminder_candidates = notifications['reminder_candidates']
        today = datetime.utcnow()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        current_month_invoices = (
            Invoice.query
            .filter(Invoice.invoice_date >= month_start, Invoice.invoice_date < month_end)
            .filter(Invoice.status.in_(['ISSUED', 'PARTIAL', 'PAID', 'OVERDUE']))
            .all()
        )
        current_month_purchases = (
            Purchase.query
            .filter(Purchase.purchase_date >= month_start, Purchase.purchase_date < month_end)
            .all()
        )
        overdue_balance = round(sum(float(invoice.get_balance_due() or 0) for invoice in overdue_invoices), 2)
        outstanding_balance = round(sum(float(invoice.get_balance_due() or 0) for invoice in Invoice.query.filter(Invoice.status.in_(['ISSUED', 'PARTIAL', 'OVERDUE'])).all()), 2)
        gst_due = round(
            sum(float(invoice.gst_amount or 0) for invoice in current_month_invoices) -
            sum(float(purchase.gst_amount or 0) for purchase in current_month_purchases),
            2,
        )
        stats = {
            'total_products': Product.query.count(),
            'total_customers': Customer.query.count(),
            'total_services': Service.query.count(),
            'total_quotes': Quote.query.count(),
            'total_invoices': Invoice.query.count(),
            'pending_quotes': Quote.query.filter(Quote.status.in_(['Pending', 'DRAFT', 'SENT'])).count(),
            'overdue_invoices': len(overdue_invoices),
            'low_stock_count': len(low_stock_items),
            'reminders_due': len(reminder_candidates),
            'overdue_balance': overdue_balance,
            'outstanding_balance': outstanding_balance,
            'gst_due': gst_due,
        }
        
        # Get all data for management sections
        all_products = Product.query.all()
        all_customers = Customer.query.all()
        all_services = Service.query.all()
        all_quotes = Quote.query.all()
        all_invoices = Invoice.query.all()
        
        return render_template('admin/dashboard.html', 
                             username=session.get('username'),
                             stats=stats,
                             overdue_invoices=overdue_invoices,
                             reminder_candidates=reminder_candidates,
                             low_stock_items=low_stock_items,
                             notifications=notifications['items'],
                             unread_notifications=notifications['unread_count'],
                             products=all_products,
                             customers=all_customers,
                             services=all_services,
                             quotes=all_quotes,
                              invoices=all_invoices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/products', methods=['GET', 'POST'])
@login_required
def products():
    """Manage products - list and add"""
    if request.method == 'POST':
        data = request.get_json()
        try:
            product = Product(
                name=data.get('name'),
                sku=data.get('sku', ''),
                category=data.get('category', ''),
                description=data.get('description', ''),
                cost_price=float(data.get('cost_price')),
                selling_price=float(data.get('selling_price')),
                quantity_in_stock=int(data.get('quantity_in_stock', 0)),
                reorder_level=int(data.get('reorder_level', 5))
            )
            db.session.add(product)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Product added successfully', 'id': product.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    # GET - Show products page
    products_list = Product.query.all()
    return render_template('admin/products.html', 
                          username=session.get('username'),
                          products=products_list)


@admin_bp.route('/customers', methods=['GET', 'POST', 'PUT'])
@login_required
def customers():
    """Manage customers - list and add"""
    if request.method == 'PUT':
        data = request.get_json()
        customer = Customer.query.get(data.get('id'))
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404

        try:
            name = (data.get('name') or customer.name or '').strip()
            email = (data.get('email') or '').strip()
            if not name:
                return jsonify({'success': False, 'message': 'Customer name is required.'}), 400
            if not email:
                return jsonify({'success': False, 'message': 'Customer email is required.'}), 400

            customer.name = name
            customer.email = email
            customer.phone = data.get('phone', customer.phone)
            customer.street_address = data.get('street_address', customer.street_address)
            customer.suburb = data.get('suburb', customer.suburb)
            customer.state = data.get('state', customer.state)
            customer.postcode = data.get('postcode', customer.postcode)
            customer.country = data.get('country', customer.country)
            customer.customer_type = data.get('customer_type', customer.customer_type)
            customer.business_name = data.get('business_name', customer.business_name)
            customer.abn = data.get('abn', customer.abn)
            customer.is_gst_registered = data.get('is_gst_registered', customer.is_gst_registered)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Customer updated successfully', 'id': customer.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400

    if request.method == 'POST':
        data = request.get_json()
        try:
            name = (data.get('name') or '').strip()
            email = (data.get('email') or '').strip()
            if not name:
                return jsonify({'success': False, 'message': 'Customer name is required.'}), 400
            if not email:
                return jsonify({'success': False, 'message': 'Customer email is required.'}), 400

            customer = Customer(
                name=name,
                email=email,
                phone=data.get('phone'),
                street_address=data.get('street_address', ''),
                suburb=data.get('suburb', ''),
                state=data.get('state', ''),
                postcode=data.get('postcode', ''),
                country=data.get('country', 'Australia'),
                customer_type=data.get('customer_type', 'INDIVIDUAL'),
                business_name=data.get('business_name', ''),
                abn=data.get('abn', ''),
                is_gst_registered=data.get('is_gst_registered', False)
            )
            db.session.add(customer)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Customer added successfully', 'id': customer.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    # GET - Show customers page
    customers_list = Customer.query.all()
    return render_template('admin/customers.html', 
                          username=session.get('username'),
                          customers=customers_list)


@admin_bp.route('/services', methods=['GET', 'POST'])
@login_required
def services():
    """Manage services - list and add"""
    if request.method == 'POST':
        data = request.get_json()
        try:
            service = Service(
                name=data.get('name'),
                description=data.get('description', ''),
                service_type=data.get('service_type', 'OTHER'),
                base_price=float(data.get('base_price', 0)),
                hourly_rate=float(data.get('hourly_rate')) if data.get('hourly_rate') else None,
                is_active=data.get('is_active', True)
            )
            db.session.add(service)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Service added successfully', 'id': service.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    # GET - Show services page
    services_list = Service.query.all()
    return render_template('admin/services.html', 
                          username=session.get('username'),
                          services=services_list)


@admin_bp.route('/inventory', methods=['GET'])
@login_required
def inventory():
    """Inventory dashboard with stock overview and recent movements."""
    products_list = Product.query.order_by(Product.name.asc()).all()
    transactions = (
        InventoryTransaction.query
        .order_by(InventoryTransaction.transaction_date.desc(), InventoryTransaction.id.desc())
        .limit(50)
        .all()
    )
    low_stock_items = [product for product in products_list if product.is_low_stock()]
    total_stock_value = sum((product.quantity_in_stock or 0) * float(product.cost_price or 0) for product in products_list)
    return render_template(
        'admin/inventory.html',
        username=session.get('username'),
        products=products_list,
        transactions=transactions,
        low_stock_items=low_stock_items,
        total_stock_value=round(total_stock_value, 2),
    )


@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Manage branding and document defaults used across the application."""
    if request.method == 'POST':
        data = request.form.to_dict() if request.form else (request.get_json() or {})
        try:
            updated_values = {
                'business_name': (data.get('business_name') or '').strip(),
                'business_legal_name': (data.get('business_legal_name') or '').strip(),
                'business_address': (data.get('business_address') or '').strip(),
                'business_abn': (data.get('business_abn') or '').strip(),
                'business_contact_email': (data.get('business_contact_email') or '').strip(),
                'bank_name': (data.get('bank_name') or '').strip(),
                'bank_account_name': (data.get('bank_account_name') or '').strip(),
                'bank_bsb': (data.get('bank_bsb') or '').strip(),
                'bank_account_number': (data.get('bank_account_number') or '').strip(),
                'invoice_due_days': (data.get('invoice_due_days') or '7').strip(),
                'quote_expiry_days': (data.get('quote_expiry_days') or '7').strip(),
                'brand_primary_color': (data.get('brand_primary_color') or '').strip(),
                'brand_secondary_color': (data.get('brand_secondary_color') or '').strip(),
            }

            logo_file = request.files.get('brand_logo')
            if logo_file and logo_file.filename:
                filename = secure_filename(logo_file.filename)
                extension = os.path.splitext(filename)[1].lower() or '.png'
                storage_name = f'brand_{uuid.uuid4().hex}{extension}'
                relative_path = os.path.join('uploads', 'branding', storage_name)
                full_dir = os.path.join(current_app.static_folder, 'uploads', 'branding')
                os.makedirs(full_dir, exist_ok=True)
                logo_file.save(os.path.join(full_dir, storage_name))
                updated_values['brand_logo_path'] = relative_path.replace('\\', '/')

            update_settings(updated_values)
            log_activity(
                'branding',
                'updated',
                'Branding settings updated',
                actor=session.get('username'),
            )
            db.session.commit()
            return jsonify({'success': True, 'message': 'Branding updated successfully', 'settings': get_app_settings()})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400

    return render_template(
        'admin/settings.html',
        username=session.get('username'),
        settings=get_app_settings(),
        branding=get_branding_settings(),
    )


@admin_bp.route('/activity', methods=['GET'])
@login_required
def activity():
    """Recent reminder history and audit trail."""
    logs = ActivityLog.query.order_by(ActivityLog.created_on.desc(), ActivityLog.id.desc()).limit(200).all()
    return render_template(
        'admin/activity.html',
        username=session.get('username'),
        logs=logs,
    )


@admin_bp.route('/reminders/run', methods=['POST'])
@login_required
def run_reminders():
    """Send overdue reminders that are due for follow-up."""
    try:
        sent = run_overdue_reminders(actor=session.get('username'))
        message = f'{len(sent)} overdue reminder(s) sent.' if sent else 'No overdue reminders were due right now.'
        return jsonify({'success': True, 'message': message, 'sent': sent})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@admin_bp.route('/notifications/read', methods=['POST'])
@login_required
def mark_notification_read():
    """Mark a single dashboard notification as read or unread."""
    data = request.get_json() or {}
    notification_key = (data.get('key') or '').strip()
    if not notification_key:
        return jsonify({'success': False, 'message': 'Notification key is required.'}), 400

    try:
        is_read = bool(data.get('is_read', True))
        set_notification_state(session.get('user_id'), notification_key, is_read)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Notification updated.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@admin_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_notifications_read_all():
    """Mark all current dashboard notifications as read."""
    try:
        notifications = build_dashboard_notifications(session.get('user_id'))
        for item in notifications['items']:
            set_notification_state(session.get('user_id'), item['key'], True)
        db.session.commit()
        return jsonify({'success': True, 'message': 'All notifications marked as read.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@admin_bp.route('/customers/<int:customer_id>/statement', methods=['GET'])
@login_required
def customer_statement(customer_id):
    """Customer statement with invoice/payment balance history."""
    customer = Customer.query.get_or_404(customer_id)
    invoices = (
        Invoice.query
        .filter_by(customer_id=customer_id)
        .order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
        .all()
    )
    totals = {
        'invoiced': round(sum(float(invoice.total_amount or 0) for invoice in invoices), 2),
        'paid': round(sum(float(invoice.amount_paid or 0) for invoice in invoices), 2),
    }
    totals['outstanding'] = round(sum(float(invoice.get_balance_due() or 0) for invoice in invoices), 2)
    return render_template(
        'admin/customer_statement.html',
        username=session.get('username'),
        customer=customer,
        invoices=invoices,
        totals=totals,
    )


@admin_bp.route('/customers/<int:customer_id>/statement/pdf', methods=['GET'])
@login_required
def customer_statement_pdf(customer_id):
    """Download the current customer statement as PDF."""
    customer = Customer.query.get_or_404(customer_id)
    invoices = (
        Invoice.query
        .filter_by(customer_id=customer_id)
        .order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
        .all()
    )
    totals = {
        'invoiced': round(sum(float(invoice.total_amount or 0) for invoice in invoices), 2),
        'paid': round(sum(float(invoice.amount_paid or 0) for invoice in invoices), 2),
        'outstanding': round(sum(float(invoice.get_balance_due() or 0) for invoice in invoices), 2),
    }
    pdf_buffer = StatementPDFGenerator(customer, invoices, totals).generate()
    filename = f'statement_{customer.id}_{datetime.utcnow().strftime("%Y%m%d")}.pdf'
    return Response(
        pdf_buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@admin_bp.route('/reports/bas-gst', methods=['GET'])
@login_required
def bas_gst_report():
    """Simple BAS/GST summary report."""
    from_date_raw = (request.args.get('from_date') or '').strip()
    to_date_raw = (request.args.get('to_date') or '').strip()

    from_date = datetime.strptime(from_date_raw, '%Y-%m-%d') if from_date_raw else datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    to_date = datetime.strptime(to_date_raw, '%Y-%m-%d') + timedelta(days=1) if to_date_raw else datetime.utcnow() + timedelta(days=1)

    invoices = (
        Invoice.query
        .filter(Invoice.invoice_date >= from_date, Invoice.invoice_date < to_date)
        .filter(Invoice.status.in_(['PAID', 'PARTIAL', 'ISSUED', 'OVERDUE']))
        .all()
    )
    purchases = (
        Purchase.query
        .filter(Purchase.purchase_date >= from_date, Purchase.purchase_date < to_date)
        .all()
    )

    sales_ex_gst = round(sum(float(invoice.subtotal or 0) for invoice in invoices), 2)
    sales_gst = round(sum(float(invoice.gst_amount or 0) for invoice in invoices), 2)
    purchase_ex_gst = round(sum(float(purchase.subtotal or 0) for purchase in purchases), 2)
    purchase_gst = round(sum(float(purchase.gst_amount or 0) for purchase in purchases), 2)

    report = {
        'sales_ex_gst': sales_ex_gst,
        'sales_gst': sales_gst,
        'sales_inc_gst': round(sales_ex_gst + sales_gst, 2),
        'purchase_ex_gst': purchase_ex_gst,
        'purchase_gst': purchase_gst,
        'purchase_inc_gst': round(purchase_ex_gst + purchase_gst, 2),
        'net_gst_payable': round(sales_gst - purchase_gst, 2),
    }
    return render_template(
        'admin/bas_gst_report.html',
        username=session.get('username'),
        report=report,
        from_date=from_date.strftime('%Y-%m-%d'),
        to_date=(to_date - timedelta(days=1)).strftime('%Y-%m-%d'),
    )


@admin_bp.route('/inventory/adjust', methods=['POST'])
@login_required
def adjust_inventory():
    """Manual stock adjustment with audit trail."""
    data = request.get_json() or {}
    product = Product.query.get(data.get('product_id'))
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    try:
        delta = int(data.get('quantity_delta') or 0)
        if delta == 0:
            return jsonify({'success': False, 'message': 'Adjustment quantity cannot be zero'}), 400

        product.quantity_in_stock = int(product.quantity_in_stock or 0) + delta
        note = (data.get('notes') or '').strip() or 'Manual stock adjustment'
        db.session.add(InventoryTransaction(
            product_id=product.id,
            transaction_type='ADJUSTMENT',
            quantity=delta,
            reference_id=f'ADJ-{product.id}',
            notes=note,
        ))
        log_activity(
            'inventory',
            'adjusted',
            f'{product.name} adjusted by {delta}. {note}',
            entity_id=product.id,
            actor=session.get('username'),
        )
        db.session.commit()
        return jsonify({'success': True, 'message': 'Stock adjusted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@admin_bp.route('/tools/backup', methods=['GET'])
@login_required
def backup_tools():
    """Backup and export tools."""
    return render_template('admin/backup_tools.html', username=session.get('username'))


@admin_bp.route('/tools/backup/export', methods=['GET'])
@login_required
def export_backup():
    """Export a JSON backup of key business records."""
    payload = {
        'exported_at': datetime.utcnow().isoformat(),
        'settings': get_app_settings(),
        'customers': [customer_to_backup_dict(customer) for customer in Customer.query.order_by(Customer.id.asc()).all()],
        'products': [product_to_backup_dict(product) for product in Product.query.order_by(Product.id.asc()).all()],
        'services': [service_to_backup_dict(service) for service in Service.query.order_by(Service.id.asc()).all()],
        'suppliers': [supplier_to_backup_dict(supplier) for supplier in Supplier.query.order_by(Supplier.id.asc()).all()],
        'quotes': [quote_to_backup_dict(quote) for quote in Quote.query.order_by(Quote.id.asc()).all()],
        'invoices': [invoice_to_backup_dict(invoice) for invoice in Invoice.query.order_by(Invoice.id.asc()).all()],
        'payments': [payment_to_backup_dict(payment) for payment in Payment.query.order_by(Payment.id.asc()).all()],
        'purchases': [purchase_to_backup_dict(purchase) for purchase in Purchase.query.order_by(Purchase.id.asc()).all()],
        'inventory_transactions': [tx.to_dict() for tx in InventoryTransaction.query.order_by(InventoryTransaction.id.asc()).all()],
    }
    log_activity('backup', 'exported', 'JSON backup exported', actor=session.get('username'))
    db.session.commit()
    data = json.dumps(payload, indent=2)
    filename = f'backup_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
    return Response(data, mimetype='application/json', headers={'Content-Disposition': f'attachment; filename="{filename}"'})


@admin_bp.route('/tools/backup/import', methods=['POST'])
@login_required
def import_backup():
    """Restore a backup JSON payload into the current database."""
    upload = request.files.get('backup_file')
    if not upload:
        return jsonify({'success': False, 'message': 'Choose a backup JSON file first.'}), 400

    try:
        payload = json.load(upload.stream)
        summary = restore_backup_payload(payload)
        log_activity('backup', 'imported', 'JSON backup imported', actor=session.get('username'))
        db.session.commit()
        return jsonify({'success': True, 'message': 'Backup imported successfully.', 'summary': summary})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@admin_bp.route('/purchases', methods=['GET', 'POST'])
@login_required
def purchases():
    """Manage supplier purchases and stock receipts."""
    if request.method == 'POST':
        data = request.get_json() or {}
        try:
            supplier_id = data.get('supplier_id')
            if supplier_id:
                supplier = Supplier.query.get(int(supplier_id))
            else:
                supplier_name = (data.get('supplier_name') or '').strip()
                if not supplier_name:
                    return jsonify({'success': False, 'message': 'Supplier name is required'}), 400

                supplier = Supplier(
                    name=supplier_name,
                    business_name=(data.get('supplier_business_name') or '').strip() or None,
                    email=(data.get('supplier_email') or '').strip() or None,
                    phone=(data.get('supplier_phone') or '').strip() or None,
                    abn=(data.get('supplier_abn') or '').strip() or None,
                    street_address=(data.get('supplier_address') or '').strip() or None,
                    suburb=(data.get('supplier_suburb') or '').strip() or None,
                    state=(data.get('supplier_state') or '').strip() or None,
                    postcode=(data.get('supplier_postcode') or '').strip() or None,
                    country=(data.get('supplier_country') or '').strip() or 'Australia',
                    is_gst_registered=bool(data.get('supplier_is_gst_registered', True)),
                    notes=(data.get('supplier_notes') or '').strip() or None,
                )
                db.session.add(supplier)
                db.session.flush()

            items = data.get('items') or []
            if not items:
                return jsonify({'success': False, 'message': 'Add at least one purchase item'}), 400

            gst_mode = (data.get('gst_mode') or GST_MODE_EXCLUSIVE).strip().lower()
            purchase_date = datetime.utcnow()
            if data.get('purchase_date'):
                purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d')

            purchase = Purchase(
                purchase_number=Purchase.generate_next_purchase_number(),
                supplier_id=supplier.id,
                purchase_date=purchase_date,
                gst_mode=gst_mode,
                notes=(data.get('notes') or '').strip() or None,
            )
            db.session.add(purchase)
            db.session.flush()

            for item in items:
                product = Product.query.get(int(item.get('product_id')))
                if not product:
                    raise ValueError('Selected product was not found.')

                quantity = float(item.get('quantity') or 0)
                unit_price = float(item.get('unit_price') or 0)
                if quantity <= 0:
                    raise ValueError('Purchase quantity must be greater than zero.')

                line_item = PurchaseLineItem(
                    purchase_id=purchase.id,
                    product_id=product.id,
                    description=(item.get('description') or product.name).strip(),
                    quantity=quantity,
                    unit_price=unit_price,
                )
                db.session.add(line_item)

                product.quantity_in_stock = int((product.quantity_in_stock or 0) + quantity)
                if gst_mode == 'inclusive':
                    product.cost_price = round(unit_price / 1.1, 2)
                else:
                    product.cost_price = round(unit_price, 2)
                db.session.add(InventoryTransaction(
                    product_id=product.id,
                    transaction_type='PURCHASE',
                    quantity=int(round(quantity)),
                    reference_id=purchase.purchase_number,
                    notes=f'Purchase from {supplier.name}',
                ))

            totals = calculate_document_totals(items, gst_mode)
            purchase.subtotal = totals['subtotal']
            purchase.gst_amount = totals['gst_amount']
            purchase.total_amount = totals['total_amount']

            db.session.commit()
            return jsonify({'success': True, 'message': 'Purchase saved successfully', 'id': purchase.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400

    purchases_list = (
        Purchase.query
        .order_by(Purchase.purchase_date.desc(), Purchase.id.desc())
        .limit(20)
        .all()
    )
    suppliers = Supplier.query.order_by(Supplier.name.asc()).all()
    products_list = Product.query.order_by(Product.name.asc()).all()
    return render_template(
        'admin/purchases.html',
        username=session.get('username'),
        purchases=purchases_list,
        suppliers=suppliers,
        products=products_list,
        products_json=[product.to_dict() for product in products_list],
        gst_modes=[{'value': value, 'label': label} for value, label in GST_MODE_CHOICES],
    )


@admin_bp.route('/suppliers', methods=['GET', 'POST', 'PUT'])
@login_required
def suppliers():
    """Manage suppliers separately from purchase entry."""
    if request.method in ['POST', 'PUT']:
        data = request.get_json() or {}
        supplier = None
        if request.method == 'PUT':
            supplier = Supplier.query.get(data.get('id'))
            if not supplier:
                return jsonify({'success': False, 'message': 'Supplier not found'}), 404
        else:
            supplier = Supplier()
            db.session.add(supplier)

        try:
            supplier.name = (data.get('name') or supplier.name or '').strip()
            if not supplier.name:
                return jsonify({'success': False, 'message': 'Supplier name is required'}), 400

            supplier.business_name = (data.get('business_name') or '').strip() or None
            supplier.email = (data.get('email') or '').strip() or None
            supplier.phone = (data.get('phone') or '').strip() or None
            supplier.abn = (data.get('abn') or '').strip() or None
            supplier.street_address = (data.get('street_address') or '').strip() or None
            supplier.suburb = (data.get('suburb') or '').strip() or None
            supplier.state = (data.get('state') or '').strip() or None
            supplier.postcode = (data.get('postcode') or '').strip() or None
            supplier.country = (data.get('country') or '').strip() or 'Australia'
            supplier.is_gst_registered = bool(data.get('is_gst_registered', True))
            supplier.notes = (data.get('notes') or '').strip() or None

            db.session.commit()
            action = 'updated' if request.method == 'PUT' else 'added'
            return jsonify({'success': True, 'message': f'Supplier {action} successfully', 'id': supplier.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400

    suppliers_list = Supplier.query.order_by(Supplier.name.asc()).all()
    return render_template(
        'admin/suppliers.html',
        username=session.get('username'),
        suppliers=suppliers_list,
    )


@admin_bp.route('/quotes', methods=['GET'])
@login_required
def quotes():
    """View and manage quotes"""
    quotes_list = Quote.query.all()
    for quote in quotes_list:
        try:
            lines_total = sum((item.quantity or 0) * (item.unit_price or 0) for item in quote.line_items)
            totals = calculate_gst_breakdown(lines_total, quote.gst_mode or GST_MODE_EXCLUSIVE)
            quote.subtotal = totals['subtotal']
            quote.gst_amount = totals['gst_amount']
            quote.total_amount = totals['total_amount']
        except Exception:
            quote.total_amount = 0

    return render_template('admin/quotes.html', 
                          username=session.get('username'),
                          quotes=quotes_list)


@admin_bp.route('/quotes/create', methods=['GET', 'POST'])
@admin_bp.route('/create-quote', methods=['GET', 'POST'])
@login_required
def create_quote():
    """Create new quote"""
    if request.method == 'POST':
        data = request.get_json()
        try:
            from app.routes.quotes import generate_quote_number
            default_expiry_days = int(get_app_settings().get('quote_expiry_days', '7') or 7)
            quote = create_quote_record(
                {**(data or {}), 'status': 'Pending'},
                generate_quote_number(),
                default_expiry_days=default_expiry_days,
            )
            log_activity('quote', 'created', f'Quote {quote.quote_number} created', entity_id=quote.id, actor=session.get('username'))
            db.session.commit()
            return jsonify({'success': True, 'message': 'Quote created successfully', 'id': quote.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    # GET - Show create quote form
    customers = Customer.query.all()
    products = [{'id': p.id, 'name': p.name, 'selling_price': p.selling_price} for p in Product.query.all()]
    services = [{'id': s.id, 'name': s.name, 'base_price': s.base_price} for s in Service.query.all()]
    
    return render_template('admin/create_quote.html',
                          username=session.get('username'),
                          customers=customers,
                          products=products,
                          services=services,
                          gst_modes=[{'value': value, 'label': label} for value, label in GST_MODE_CHOICES])


@admin_bp.route('/invoices', methods=['GET'])
@login_required
def invoices():
    """View and manage invoices"""
    refresh_overdue_invoices()

    status = (request.args.get('status') or '').strip()
    customer = (request.args.get('customer') or '').strip()
    item = (request.args.get('item') or '').strip()
    due_from_raw = (request.args.get('due_from') or '').strip()
    due_to_raw = (request.args.get('due_to') or '').strip()
    sort = (request.args.get('sort') or 'due_date').strip()

    query = Invoice.query.join(Customer, Invoice.customer_id == Customer.id)

    if status:
        query = query.filter(Invoice.status == status)

    if customer:
        query = query.filter(
            or_(
                Customer.name.ilike(f'%{customer}%'),
                Customer.business_name.ilike(f'%{customer}%')
            )
        )

    if item:
        query = (
            query
            .outerjoin(InvoiceLineItem, InvoiceLineItem.invoice_id == Invoice.id)
            .outerjoin(Product, Product.id == InvoiceLineItem.product_id)
            .outerjoin(Service, Service.id == InvoiceLineItem.service_id)
            .filter(
                or_(
                    InvoiceLineItem.description.ilike(f'%{item}%'),
                    Product.name.ilike(f'%{item}%'),
                    Service.name.ilike(f'%{item}%')
                )
            )
        )

    if due_from_raw:
        try:
            due_from = datetime.strptime(due_from_raw, '%Y-%m-%d')
            query = query.filter(Invoice.due_date >= due_from)
        except ValueError:
            due_from_raw = ''

    if due_to_raw:
        try:
            due_to = datetime.strptime(due_to_raw, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Invoice.due_date < due_to)
        except ValueError:
            due_to_raw = ''

    if sort == 'invoice_date':
        query = query.order_by(Invoice.invoice_date.desc())
    elif sort == 'customer':
        query = query.order_by(Customer.name.asc(), Invoice.due_date.asc())
    else:
        query = query.order_by(Invoice.due_date.asc().nullslast(), Invoice.invoice_date.desc())

    invoices_list = query.distinct().all()
    return render_template('admin/invoices.html', 
                          username=session.get('username'),
                          invoices=invoices_list,
                          filters={
                              'status': status,
                              'customer': customer,
                              'item': item,
                              'due_from': due_from_raw,
                              'due_to': due_to_raw,
                              'sort': sort,
                          })


@admin_bp.route('/search', methods=['GET'])
@login_required
def global_search():
    """Global live search across customers, products, services, invoices, and quotes."""
    query_text = (request.args.get('q') or '').strip()
    if len(query_text) < 1:
        return jsonify({'results': []})

    like = f'%{query_text}%'
    results = []

    for customer in Customer.query.filter(
        or_(Customer.name.ilike(like), Customer.business_name.ilike(like))
    ).limit(5).all():
        results.append({
            'type': 'Customer',
            'title': customer.business_name or customer.name,
            'subtitle': customer.name if customer.business_name else (customer.email or customer.phone or 'Customer record'),
            'url': '/admin/customers'
        })

    for product in Product.query.filter(
        or_(Product.name.ilike(like), Product.sku.ilike(like), Product.description.ilike(like))
    ).limit(5).all():
        results.append({
            'type': 'Item',
            'title': product.name,
            'subtitle': product.sku or 'Product',
            'url': '/admin/products'
        })

    for service in Service.query.filter(
        or_(Service.name.ilike(like), Service.description.ilike(like))
    ).limit(5).all():
        results.append({
            'type': 'Item',
            'title': service.name,
            'subtitle': 'Service',
            'url': '/admin/services'
        })

    for invoice in (
        Invoice.query
        .join(Customer, Invoice.customer_id == Customer.id)
        .filter(
            or_(
                Invoice.invoice_number.ilike(like),
                Customer.name.ilike(like),
                Customer.business_name.ilike(like)
            )
        )
        .limit(5)
        .all()
    ):
        results.append({
            'type': 'Invoice',
            'title': invoice.invoice_number,
            'subtitle': f"{invoice.customer.name} • {invoice.status}",
            'url': f'/admin/invoice/{invoice.id}'
        })

    for quote in (
        Quote.query
        .join(Customer, Quote.customer_id == Customer.id)
        .filter(
            or_(
                Quote.quote_number.ilike(like),
                Customer.name.ilike(like),
                Customer.business_name.ilike(like)
            )
        )
        .limit(5)
        .all()
    ):
        results.append({
            'type': 'Quote',
            'title': quote.quote_number,
            'subtitle': f"{quote.customer.name} • {quote.status}",
            'url': f'/admin/quote/{quote.id}'
        })

    return jsonify({'results': results[:12]})


@admin_bp.route('/invoices/create', methods=['GET', 'POST'])
@admin_bp.route('/create-invoice', methods=['GET', 'POST'])
@login_required
def create_invoice():
    """Create new invoice"""
    if request.method == 'POST':
        data = request.get_json()
        try:
            invoice = create_invoice_record(
                data or {},
                Invoice.generate_next_invoice_number(),
                default_due_days=7,
            )
            log_activity('invoice', 'created', f'Invoice {invoice.invoice_number} created', entity_id=invoice.id, actor=session.get('username'))
            db.session.commit()
            return jsonify({'success': True, 'message': 'Invoice created successfully', 'id': invoice.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    # GET - Show create invoice form
    customers = Customer.query.all()
    products = [{'id': p.id, 'name': p.name, 'selling_price': p.selling_price} for p in Product.query.all()]
    services = [{'id': s.id, 'name': s.name, 'base_price': s.base_price} for s in Service.query.all()]
    default_due_days = int(get_app_settings().get('invoice_due_days', '7') or 7)
    
    return render_template('admin/create_invoice.html',
                          username=session.get('username'),
                          customers=customers,
                          products=products,
                          services=services,
                          gst_modes=[{'value': value, 'label': label} for value, label in GST_MODE_CHOICES],
                          default_due_date=(datetime.utcnow() + timedelta(days=default_due_days)).strftime('%Y-%m-%d'))


@admin_bp.route('/dashboard-stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    """API endpoint for dashboard statistics"""
    try:
        stats = {
            'products': Product.query.count(),
            'customers': Customer.query.count(),
            'services': Service.query.count(),
            'quotes': Quote.query.count(),
            'invoices': Invoice.query.count(),
            'pending_quotes': Quote.query.filter_by(status='Pending').count(),
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/quotes', methods=['GET'])
@login_required
def get_all_quotes():
    """Get all quotes with details"""
    try:
        quotes = Quote.query.all()
        return jsonify({
            'success': True,
            'quotes': [quote.to_dict() for quote in quotes]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/api/invoices', methods=['GET'])
@login_required
def get_all_invoices():
    """Get all invoices with details"""
    try:
        invoices = Invoice.query.all()
        return jsonify({
            'success': True,
            'invoices': [invoice.to_dict() for invoice in invoices]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/quote/<int:quote_id>', methods=['GET'])
@login_required
def view_quote(quote_id):
    """View detailed quote information"""
    try:
        quote = Quote.query.get(quote_id)
        if not quote:
            return jsonify({'error': 'Quote not found'}), 404
        
        return render_template('admin/view_quote.html',
                             username=session.get('username'),
                             quote=quote,
                             branding=quote.get_branding())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/quote/<int:quote_id>/email', methods=['POST'])
@login_required
def email_quote(quote_id):
    """Email a quote to the customer."""
    try:
        quote = Quote.query.get(quote_id)
        if not quote:
            return jsonify({'success': False, 'message': 'Quote not found'}), 404

        send_quote_email_message(quote)
        log_activity('quote', 'emailed', f'Quote {quote.quote_number} emailed to {quote.customer.email}', entity_id=quote.id, actor=session.get('username'))
        if quote.status == 'Pending':
            quote.status = 'SENT'
        db.session.commit()
        return jsonify({'success': True, 'message': f'Quote emailed to {quote.customer.email}.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@admin_bp.route('/quote/<int:quote_id>/accept', methods=['GET', 'POST'])
def accept_quote(quote_id):
    """Public endpoint for customer to accept quote"""
    try:
        quote = Quote.query.get(quote_id)
        if not quote:
            return render_template('quote_response.html', 
                                 success=False, 
                                 title='Quote Not Found',
                                 message='The quote you are trying to accept could not be found.'), 404
        
        if quote.is_expired():
            return render_template('quote_response.html',
                                 success=False,
                                 title='Quote Expired',
                                 message='This quote has expired. Please contact us for a new quote.')
        
        quote.status = 'ACCEPTED'
        db.session.commit()
        
        # Send confirmation email to admin (don't let it block the response)
        try:
            admin_email = current_app.config.get('MAIL_DEFAULT_SENDER', 'info@westernitsolutions.com.au')
            if current_app.config.get('MAIL_ENABLED', False):
                subject = f'Quote {quote.quote_number} - ACCEPTED by {quote.customer.name}'
                text_body = f"""
Quote {quote.quote_number} has been accepted!

Customer: {quote.customer.name}
Email: {quote.customer.email}
Quote Total: ${quote.get_total():.2f}
Accepted on: {datetime.utcnow().strftime('%d %B %Y %H:%M')}

Please proceed with creating an invoice for this quote.
                """
                html_body = f"""
                <h2>Quote Accepted! ✓</h2>
                <p>Quote <strong>{quote.quote_number}</strong> has been accepted by the customer.</p>
                <ul>
                    <li>Customer: <strong>{quote.customer.name}</strong></li>
                    <li>Email: <strong>{quote.customer.email}</strong></li>
                    <li>Quote Total: <strong>${quote.get_total():.2f}</strong></li>
                    <li>Accepted on: <strong>{datetime.utcnow().strftime('%d %B %Y %H:%M')}</strong></li>
                </ul>
                <p>Please proceed with creating an invoice for this quote.</p>
                """
                send_email(admin_email, subject, text_body, html_body)
        except Exception as e:
            print(f"Warning: Could not send admin notification: {str(e)}")
        
        return render_template('quote_response.html',
                             success=True,
                             title='Quote Accepted',
                             message=f'Thank you! Your quote has been accepted. Quote #{quote.quote_number} is now in our system.')
    except Exception as e:
        return render_template('quote_response.html',
                             success=False,
                             title='Error Processing Quote',
                             message=f'An error occurred: {str(e)}')


@admin_bp.route('/quote/<int:quote_id>/reject', methods=['GET', 'POST'])
def reject_quote(quote_id):
    """Public endpoint for customer to reject quote"""
    try:
        quote = Quote.query.get(quote_id)
        if not quote:
            return render_template('quote_response.html',
                                 success=False,
                                 title='Quote Not Found',
                                 message='The quote you are trying to reject could not be found.'), 404
        
        quote.status = 'REJECTED'
        db.session.commit()
        
        # Send rejection notification to admin (don't let it block the response)
        try:
            admin_email = current_app.config.get('MAIL_DEFAULT_SENDER', 'info@westernitsolutions.com.au')
            if current_app.config.get('MAIL_ENABLED', False):
                subject = f'Quote {quote.quote_number} - REJECTED by {quote.customer.name}'
                text_body = f"""
Quote {quote.quote_number} has been rejected.

Customer: {quote.customer.name}
Email: {quote.customer.email}
Quote Total: ${quote.get_total():.2f}
Rejected on: {datetime.utcnow().strftime('%d %B %Y %H:%M')}

Please follow up with the customer if needed.
                """
                html_body = f"""
                <h2>Quote Rejected</h2>
                <p>Quote <strong>{quote.quote_number}</strong> has been rejected by the customer.</p>
                <ul>
                    <li>Customer: <strong>{quote.customer.name}</strong></li>
                    <li>Email: <strong>{quote.customer.email}</strong></li>
                    <li>Quote Total: <strong>${quote.get_total():.2f}</strong></li>
                    <li>Rejected on: <strong>{datetime.utcnow().strftime('%d %B %Y %H:%M')}</strong></li>
                </ul>
                <p>Please follow up with the customer if needed.</p>
                """
                send_email(admin_email, subject, text_body, html_body)
        except Exception as e:
            print(f"Warning: Could not send admin notification: {str(e)}")
        
        return render_template('quote_response.html',
                             success=True,
                             title='Quote Rejected',
                             message='Thank you for your response. We appreciate your consideration.')
    except Exception as e:
        return render_template('quote_response.html',
                             success=False,
                             title='Error Processing Quote',
                             message=f'An error occurred: {str(e)}')


@admin_bp.route('/quote/<int:quote_id>/convert-to-invoice', methods=['GET', 'POST'])
@login_required
def convert_quote_to_invoice(quote_id):
    """Convert accepted quote to invoice"""
    quote = Quote.query.get(quote_id)
    if not quote:
        return jsonify({'error': 'Quote not found'}), 404
    
    if quote.status != 'ACCEPTED':
        return jsonify({'error': 'Only accepted quotes can be converted to invoices'}), 400
    
    if request.method == 'POST':
        data = request.get_json()
        try:
            payload = dict(data or {})
            payload.setdefault('gst_mode', quote.gst_mode or GST_MODE_EXCLUSIVE)
            payload.setdefault('notes', quote.notes or '')
            invoice = create_invoice_record(
                payload,
                Invoice.generate_next_invoice_number(),
                default_due_days=7,
                quote_id=quote_id,
                customer_id=quote.customer_id,
            )
            log_activity('invoice', 'created_from_quote', f'Invoice {invoice.invoice_number} created from quote {quote.quote_number}', entity_id=invoice.id, actor=session.get('username'))
            db.session.commit()
            return jsonify({'success': True, 'message': 'Invoice created successfully', 'id': invoice.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    # GET - Show form with quote data pre-populated
    products = [{'id': p.id, 'name': p.name, 'selling_price': p.selling_price} for p in Product.query.all()]
    services = [{'id': s.id, 'name': s.name, 'base_price': s.base_price} for s in Service.query.all()]
    default_due_days = int(get_app_settings().get('invoice_due_days', '7') or 7)
    
    return render_template('admin/convert_quote_to_invoice.html',
                          username=session.get('username'),
                          quote=quote,
                          products=products,
                          services=services,
                          gst_modes=[{'value': value, 'label': label} for value, label in GST_MODE_CHOICES],
                          gst_mode_label=gst_label(quote.gst_mode or GST_MODE_EXCLUSIVE),
                          default_due_date=(datetime.utcnow() + timedelta(days=default_due_days)).strftime('%Y-%m-%d'),
                          now=datetime.utcnow)


@admin_bp.route('/invoice/<int:invoice_id>', methods=['GET'])
@login_required
def view_invoice(invoice_id):
    """View detailed invoice information"""
    try:
        refresh_overdue_invoices()
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404
        
        return render_template('admin/view_invoice.html',
                             username=session.get('username'),
                             invoice=invoice,
                             branding=invoice.get_branding())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/invoice/<int:invoice_id>/print', methods=['GET'])
@login_required
def print_invoice(invoice_id):
    """Print-friendly invoice view with fixed layout"""
    try:
        refresh_overdue_invoices()
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return jsonify({'error': 'Invoice not found'}), 404

        return render_template('admin/print_invoice.html',
                             username=session.get('username'),
                             invoice=invoice,
                             branding=invoice.get_branding())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/invoice/<int:invoice_id>/email', methods=['POST'])
@login_required
def email_invoice(invoice_id):
    """Email an invoice to the customer."""
    try:
        refresh_overdue_invoices()
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return jsonify({'success': False, 'message': 'Invoice not found'}), 404

        send_invoice_email_message(invoice)
        if invoice.status == 'OVERDUE':
            invoice.resend_count = int(invoice.resend_count or 0) + 1
            invoice.last_resent_at = datetime.utcnow()
            log_activity('invoice', 'resent', f'Invoice {invoice.invoice_number} resent to {invoice.customer.email}', entity_id=invoice.id, actor=session.get('username'))
        else:
            log_activity('invoice', 'emailed', f'Invoice {invoice.invoice_number} emailed to {invoice.customer.email}', entity_id=invoice.id, actor=session.get('username'))
        if invoice.status == 'DRAFT':
            invoice.status = 'ISSUED'
        db.session.commit()
        return jsonify({'success': True, 'message': f'Invoice emailed to {invoice.customer.email}.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@admin_bp.route('/invoice/<int:invoice_id>/remind', methods=['POST'])
@login_required
def remind_invoice(invoice_id):
    """Send a single overdue reminder for an invoice."""
    from app.services.reminders import send_invoice_reminder_message

    invoice = Invoice.query.get_or_404(invoice_id)
    try:
        if invoice.get_balance_due() <= 0:
            return jsonify({'success': False, 'message': 'This invoice has no outstanding balance.'}), 400
        send_invoice_reminder_message(invoice)
        invoice.status = 'OVERDUE'
        invoice.reminder_count = int(invoice.reminder_count or 0) + 1
        invoice.last_reminder_at = datetime.utcnow()
        log_activity(
            'invoice',
            'reminder_sent',
            f'Overdue reminder sent for {invoice.invoice_number} to {invoice.customer.email}',
            entity_id=invoice.id,
            actor=session.get('username'),
        )
        db.session.commit()
        return jsonify({'success': True, 'message': f'Reminder sent to {invoice.customer.email}.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@admin_bp.route('/invoice/<int:invoice_id>/credit-note', methods=['POST'])
@login_required
def apply_credit_note(invoice_id):
    """Apply a credit note amount against an invoice."""
    invoice = Invoice.query.get_or_404(invoice_id)
    data = request.get_json() or {}

    try:
        credit_amount = round(float(data.get('amount') or 0), 2)
        if credit_amount <= 0:
            return jsonify({'success': False, 'message': 'Credit note amount must be greater than zero.'}), 400
        if credit_amount > float(invoice.total_amount or 0):
            return jsonify({'success': False, 'message': 'Credit note cannot exceed the invoice total.'}), 400

        invoice.credit_note_amount = credit_amount
        invoice.credit_note_reason = (data.get('reason') or '').strip() or None
        recalculate_invoice_status(invoice)
        log_activity(
            'invoice',
            'credit_note_applied',
            f'Credit note ${credit_amount:.2f} applied to {invoice.invoice_number}',
            entity_id=invoice.id,
            actor=session.get('username'),
        )
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Credit note applied successfully.',
            'balance_due': invoice.get_balance_due(),
            'status': invoice.status,
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400


@admin_bp.route('/invoice/<int:invoice_id>/refund', methods=['POST'])
@login_required
def refund_invoice(invoice_id):
    """Record a refund against an invoice."""
    invoice = Invoice.query.get_or_404(invoice_id)
    data = request.get_json() or {}

    try:
        refund_amount = round(float(data.get('amount') or 0), 2)
        if refund_amount <= 0:
            return jsonify({'success': False, 'message': 'Refund amount must be greater than zero.'}), 400
        if refund_amount > float(invoice.amount_paid or 0):
            return jsonify({'success': False, 'message': 'Refund cannot exceed the amount already paid.'}), 400

        payment = Payment(
            invoice_id=invoice.id,
            customer_id=invoice.customer_id,
            amount=-refund_amount,
            payment_mode=(data.get('payment_mode') or 'BANK_TRANSFER').strip() or 'BANK_TRANSFER',
            payment_reference=(data.get('payment_reference') or '').strip() or None,
            status='REFUNDED',
            payment_date=datetime.utcnow(),
            notes=(data.get('notes') or 'Refund recorded from invoice screen').strip(),
        )
        db.session.add(payment)
        invoice.amount_paid = round(float(invoice.amount_paid or 0) - refund_amount, 2)
        recalculate_invoice_status(invoice)
        log_activity(
            'invoice',
            'refund_recorded',
            f'Refund ${refund_amount:.2f} recorded for {invoice.invoice_number}',
            entity_id=invoice.id,
            actor=session.get('username'),
        )
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Refund recorded successfully.',
            'balance_due': invoice.get_balance_due(),
            'status': invoice.status,
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
