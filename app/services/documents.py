from datetime import datetime, timedelta

from app import db
from app.models import Invoice, InvoiceLineItem, Quote, QuoteLineItem
from app.services.settings import capture_branding_snapshot, serialize_branding_snapshot
from app.services.tax import GST_MODE_EXCLUSIVE, calculate_gst_breakdown


def normalize_document_items(raw_items):
    """Normalize incoming line items for quotes and invoices."""
    items = []
    for raw_item in raw_items or []:
        quantity = float(raw_item.get('quantity') or 0)
        unit_price = float(raw_item.get('unit_price') or 0)
        if quantity <= 0:
            continue

        items.append({
            'product_id': raw_item.get('product_id') or None,
            'service_id': raw_item.get('service_id') or None,
            'description': (raw_item.get('description') or '').strip(),
            'quantity': quantity,
            'unit_price': unit_price,
        })
    return items


def calculate_document_totals(items, gst_mode):
    lines_total = sum((item['quantity'] or 0) * (item['unit_price'] or 0) for item in items)
    return calculate_gst_breakdown(lines_total, gst_mode or GST_MODE_EXCLUSIVE)


def derive_invoice_status(total_amount, amount_paid):
    amount_paid = float(amount_paid or 0)
    total_amount = float(total_amount or 0)
    if amount_paid <= 0:
        return 'DRAFT'
    if amount_paid >= total_amount:
        return 'PAID'
    return 'PARTIAL'


def create_quote_record(data, quote_number, default_expiry_days=7):
    """Create and persist a quote with normalized totals."""
    gst_mode = (data.get('gst_mode') or GST_MODE_EXCLUSIVE).strip().lower()
    items = normalize_document_items(data.get('items') or data.get('line_items') or [])
    expiry_date = datetime.utcnow() + timedelta(days=default_expiry_days)
    if data.get('expiry_date'):
        expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d')

    quote = Quote(
        quote_number=quote_number,
        customer_id=int(data.get('customer_id')),
        quote_date=datetime.utcnow(),
        expiry_date=expiry_date,
        status=data.get('status') or 'DRAFT',
        gst_mode=gst_mode,
        notes=data.get('notes', ''),
        terms_and_conditions=data.get('terms_and_conditions'),
        branding_snapshot=serialize_branding_snapshot(capture_branding_snapshot()),
    )
    db.session.add(quote)
    db.session.flush()

    for item in items:
        db.session.add(QuoteLineItem(
            quote_id=quote.id,
            product_id=item['product_id'],
            service_id=item['service_id'],
            description=item['description'],
            quantity=item['quantity'],
            unit_price=item['unit_price'],
        ))

    totals = calculate_document_totals(items, gst_mode)
    quote.subtotal = totals['subtotal']
    quote.gst_amount = totals['gst_amount']
    quote.total_amount = totals['total_amount']
    return quote


def create_invoice_record(data, invoice_number, default_due_days=7, quote_id=None, customer_id=None):
    """Create and persist an invoice with normalized totals."""
    gst_mode = (data.get('gst_mode') or GST_MODE_EXCLUSIVE).strip().lower()
    advance_payment = max(float(data.get('advance_payment', 0) or 0), 0)
    due_date = datetime.utcnow() + timedelta(days=default_due_days)
    if data.get('due_date'):
        due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')

    items = normalize_document_items(data.get('items') or data.get('line_items') or [])
    invoice = Invoice(
        invoice_number=invoice_number,
        customer_id=int(customer_id or data.get('customer_id')),
        quote_id=quote_id or data.get('quote_id'),
        invoice_date=datetime.utcnow(),
        due_date=due_date,
        status='DRAFT',
        gst_mode=gst_mode,
        reference=(data.get('reference') or '').strip() or None,
        payment_mode=data.get('payment_mode'),
        notes=data.get('notes', ''),
        terms_and_conditions=data.get('terms_and_conditions'),
        branding_snapshot=serialize_branding_snapshot(capture_branding_snapshot()),
    )
    db.session.add(invoice)
    db.session.flush()

    for item in items:
        db.session.add(InvoiceLineItem(
            invoice_id=invoice.id,
            product_id=item['product_id'],
            service_id=item['service_id'],
            description=item['description'],
            quantity=item['quantity'],
            unit_price=item['unit_price'],
        ))

    totals = calculate_document_totals(items, gst_mode)
    invoice.subtotal = totals['subtotal']
    invoice.gst_amount = totals['gst_amount']
    invoice.total_amount = totals['total_amount']
    invoice.amount_paid = min(advance_payment, invoice.total_amount)
    invoice.status = derive_invoice_status(invoice.total_amount, invoice.amount_paid)
    return invoice
