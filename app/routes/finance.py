"""
Financial analytics routes for Business Management System
"""
import csv
import io
from collections import defaultdict
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template, request, session, redirect, url_for, Response
from sqlalchemy.orm import joinedload
from sqlalchemy import or_

from app import db
from app.models import Customer, Invoice, InvoiceLineItem, Purchase, PurchaseLineItem, Supplier
from app.services.tax import gross_from_line_total, net_from_line_total

finance_bp = Blueprint('finance', __name__, url_prefix='/admin/finance')


def login_required(view_func):
    """Keep finance routes aligned with the admin session model."""
    from functools import wraps

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return view_func(*args, **kwargs)

    return wrapped


def _parse_date(value, end_of_day=False):
    if not value:
        return None
    dt = datetime.strptime(value, '%Y-%m-%d')
    if end_of_day:
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return dt


def _safe_float(value):
    return round(float(value or 0), 2)


def _get_filters(payload):
    payload = payload or {}
    return {
        'start_date': _parse_date(payload.get('start_date')),
        'end_date': _parse_date(payload.get('end_date'), end_of_day=True),
        'customer_id': int(payload['customer_id']) if payload.get('customer_id') else None,
        'invoice_status': payload.get('invoice_status', 'active'),
        'item_type': payload.get('item_type', 'all'),
        'group_by': payload.get('group_by', 'month'),
        'value_basis': payload.get('value_basis', 'received'),
        'search': (payload.get('search') or '').strip().lower(),
    }


def _apply_invoice_filters(query, filters):
    if filters['start_date']:
        query = query.filter(Invoice.invoice_date >= filters['start_date'])
    if filters['end_date']:
        query = query.filter(Invoice.invoice_date <= filters['end_date'])
    if filters['customer_id']:
        query = query.filter(Invoice.customer_id == filters['customer_id'])

    status_filter = filters['invoice_status']
    if status_filter == 'active':
        query = query.filter(Invoice.status.in_(['ISSUED', 'PAID', 'PARTIAL', 'OVERDUE']))
    elif status_filter != 'all':
        query = query.filter(Invoice.status == status_filter)

    return query


def _filtered_invoices(filters):
    query = (
        Invoice.query
        .options(
            joinedload(Invoice.customer),
            joinedload(Invoice.line_items).joinedload(InvoiceLineItem.product),
            joinedload(Invoice.line_items).joinedload(InvoiceLineItem.service),
        )
        .order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
    )
    return _apply_invoice_filters(query, filters).all()


def _filtered_purchases(filters):
    query = (
        Purchase.query
        .options(
            joinedload(Purchase.supplier),
            joinedload(Purchase.line_items).joinedload(PurchaseLineItem.product),
        )
        .order_by(Purchase.purchase_date.desc(), Purchase.id.desc())
    )

    if filters['start_date']:
        query = query.filter(Purchase.purchase_date >= filters['start_date'])
    if filters['end_date']:
        query = query.filter(Purchase.purchase_date <= filters['end_date'])
    if filters['search']:
        search = f"%{filters['search']}%"
        query = (
            query
            .join(Supplier, Purchase.supplier_id == Supplier.id)
            .outerjoin(PurchaseLineItem, PurchaseLineItem.purchase_id == Purchase.id)
            .filter(
                or_(
                    Supplier.name.ilike(search),
                    Supplier.business_name.ilike(search),
                    Purchase.purchase_number.ilike(search),
                    PurchaseLineItem.description.ilike(search),
                )
            )
        )
    return query.distinct().all()


def _invoice_ratio(invoice):
    total = float(invoice.total_amount or 0)
    if total <= 0:
        return 0
    return max(0, min(float(invoice.amount_paid or 0) / total, 1))


def _choose_value(invoiced, received, pending, basis):
    if basis == 'invoiced':
        return invoiced
    if basis == 'pending':
        return pending
    return received


def _line_matches_item_type(line_item, filters):
    item_type = filters['item_type']
    if item_type == 'product' and not line_item.product_id:
        return False
    if item_type == 'service' and not line_item.service_id:
        return False
    return True


def _line_matches_search(line_item, filters):
    search = filters['search']
    if not search:
        return True

    names = [
        line_item.description or '',
        line_item.product.name if line_item.product else '',
        line_item.service.name if line_item.service else '',
    ]
    return any(search in name.lower() for name in names if name)


def _invoice_matches_search(invoice, filters):
    search = filters['search']
    if not search:
        return True

    values = [
        invoice.invoice_number or '',
        invoice.status or '',
        invoice.customer.name if invoice.customer else '',
        invoice.reference or '',
    ]
    return any(search in value.lower() for value in values if value)


def _customer_matches_search(invoice, filters):
    search = filters['search']
    if not search:
        return True

    customer_name = invoice.customer.name if invoice.customer else ''
    return search in customer_name.lower()


def _get_scoped_lines(invoice, filters):
    item_lines = [line for line in invoice.line_items if _line_matches_item_type(line, filters)]
    search = filters['search']
    invoice_search_match = _invoice_matches_search(invoice, filters) or _customer_matches_search(invoice, filters)

    if not search:
        return item_lines if filters['item_type'] != 'all' else list(invoice.line_items)

    if invoice_search_match:
        return item_lines if filters['item_type'] != 'all' else list(invoice.line_items)

    return [line for line in item_lines if _line_matches_search(line, filters)]


def _serialize_invoice(invoice, filters):
    ratio = _invoice_ratio(invoice)
    scoped_lines = _get_scoped_lines(invoice, filters)

    total_amount = 0
    amount_paid = 0
    products_total = 0
    products_received = 0
    services_total = 0
    services_received = 0

    for line_item in scoped_lines:
        entered_total = float(line_item.quantity or 0) * float(line_item.unit_price or 0)
        line_total = gross_from_line_total(entered_total, invoice.gst_mode or 'exclusive')
        total_amount += line_total
        amount_paid += line_total * ratio
        line_received = line_total * ratio
        if line_item.product_id:
            products_total += line_total
            products_received += line_received
        if line_item.service_id:
            services_total += line_total
            services_received += line_received

    pending = max(total_amount - amount_paid, 0)

    return {
        'invoice_number': invoice.invoice_number,
        'customer_name': invoice.customer.name if invoice.customer else 'N/A',
        'invoice_date': invoice.invoice_date.strftime('%d-%m-%Y') if invoice.invoice_date else 'N/A',
        'total_amount': _safe_float(total_amount),
        'amount_paid': _safe_float(amount_paid),
        'pending': _safe_float(pending),
        'status': invoice.status,
        'products_total': _safe_float(products_total),
        'products_received': _safe_float(products_received),
        'services_total': _safe_float(services_total),
        'services_received': _safe_float(services_received),
    }


def _build_summary(invoice_rows):
    total_invoiced = sum(float(inv['total_amount'] or 0) for inv in invoice_rows)
    total_received = sum(float(inv['amount_paid'] or 0) for inv in invoice_rows)
    total_pending = sum(float(inv['pending'] or 0) for inv in invoice_rows)
    paid_invoice_count = sum(1 for inv in invoice_rows if float(inv['amount_paid'] or 0) > 0)
    unique_customers = len({inv['customer_name'] for inv in invoice_rows if inv['customer_name']})
    total_products_received = sum(float(inv['products_received'] or 0) for inv in invoice_rows)
    total_services_received = sum(float(inv['services_received'] or 0) for inv in invoice_rows)

    return {
        'total_invoiced': _safe_float(total_invoiced),
        'total_received': _safe_float(total_received),
        'total_pending': _safe_float(total_pending),
        'total_invoices': len(invoice_rows),
        'paid_invoice_count': paid_invoice_count,
        'unique_customers': unique_customers,
        'total_products_received': _safe_float(total_products_received),
        'total_services_received': _safe_float(total_services_received),
        'sales_gst_collected': 0,
        'purchase_spend': 0,
        'purchase_gst_paid': 0,
        'net_gst_liability': 0,
        'estimated_net_profit': 0,
    }


def _build_purchase_summary(purchases):
    total_spend = 0
    total_gst = 0
    for purchase in purchases:
        total_spend += float(purchase.total_amount or 0)
        total_gst += float(purchase.gst_amount or 0)
    return {
        'purchase_spend': _safe_float(total_spend),
        'purchase_gst_paid': _safe_float(total_gst),
        'purchase_count': len(purchases),
    }


def _build_invoice_report(invoices, filters):
    items = []
    for invoice in invoices:
        serialized = _serialize_invoice(invoice, filters)
        if serialized['total_amount'] <= 0 and serialized['amount_paid'] <= 0 and serialized['pending'] <= 0:
            continue
        items.append(serialized)
    return items


def _build_customer_report(invoices, filters):
    grouped = {}

    for invoice in invoices:
        serialized = _serialize_invoice(invoice, filters)
        if serialized['total_amount'] <= 0 and serialized['amount_paid'] <= 0 and serialized['pending'] <= 0:
            continue

        customer_id = invoice.customer_id or 0
        bucket = grouped.setdefault(customer_id, {
            'customer_name': invoice.customer.name if invoice.customer else 'Unknown',
            'invoice_count': 0,
            'total_invoiced': 0,
            'total_received': 0,
            'total_pending': 0,
        })
        bucket['invoice_count'] += 1
        bucket['total_invoiced'] += float(serialized['total_amount'] or 0)
        bucket['total_received'] += float(serialized['amount_paid'] or 0)
        bucket['total_pending'] += float(serialized['pending'] or 0)

    items = []
    for item in grouped.values():
        item['total_invoiced'] = _safe_float(item['total_invoiced'])
        item['total_received'] = _safe_float(item['total_received'])
        item['total_pending'] = _safe_float(item['total_pending'])
        item['metric_value'] = _safe_float(_choose_value(
            item['total_invoiced'],
            item['total_received'],
            item['total_pending'],
            filters['value_basis']
        ))
        items.append(item)

    return sorted(items, key=lambda row: row['metric_value'], reverse=True)


def _build_item_report(invoices, filters):
    grouped = {}
    total_product_cost = 0

    for invoice in invoices:
        ratio = _invoice_ratio(invoice)
        for line_item in _get_scoped_lines(invoice, filters):
            entered_total = float(line_item.quantity or 0) * float(line_item.unit_price or 0)
            line_total = gross_from_line_total(entered_total, invoice.gst_mode or 'exclusive')
            line_received = line_total * ratio
            line_pending = max(line_total - line_received, 0)

            if line_item.product:
                item_key = ('product', line_item.product.id)
                item_name = line_item.product.name
                item_group = 'Product'
                total_product_cost += float(line_item.quantity or 0) * float(line_item.product.cost_price or 0) * ratio
            elif line_item.service:
                item_key = ('service', line_item.service.id)
                item_name = line_item.service.name
                item_group = 'Service'
            else:
                item_key = ('other', line_item.id)
                item_name = line_item.description or 'Unnamed Item'
                item_group = 'Other'

            bucket = grouped.setdefault(item_key, {
                'name': item_name,
                'type': item_group,
                'line_count': 0,
                'quantity': 0,
                'total_invoiced': 0,
                'total_received': 0,
                'total_pending': 0,
            })
            bucket['line_count'] += 1
            bucket['quantity'] += float(line_item.quantity or 0)
            bucket['total_invoiced'] += line_total
            bucket['total_received'] += line_received
            bucket['total_pending'] += line_pending

    items = []
    for item in grouped.values():
        metric_value = _choose_value(
            item['total_invoiced'],
            item['total_received'],
            item['total_pending'],
            filters['value_basis']
        )
        item['quantity'] = _safe_float(item['quantity'])
        item['total_invoiced'] = _safe_float(item['total_invoiced'])
        item['total_received'] = _safe_float(item['total_received'])
        item['total_pending'] = _safe_float(item['total_pending'])
        item['metric_value'] = _safe_float(metric_value)
        items.append(item)

    return sorted(items, key=lambda row: row['metric_value'], reverse=True), _safe_float(total_product_cost)


def _time_bucket_label(dt, group_by):
    if group_by == 'day':
        return dt.strftime('%d-%m-%Y')
    if group_by == 'week':
        week_start = dt - timedelta(days=dt.weekday())
        week_end = week_start + timedelta(days=6)
        return f"{week_start.strftime('%d-%m-%Y')} to {week_end.strftime('%d-%m-%Y')}"
    if group_by == 'year':
        return dt.strftime('%Y')
    return dt.strftime('%b %Y')


def _time_bucket_key(dt, group_by):
    if group_by == 'day':
        return dt.strftime('%Y-%m-%d')
    if group_by == 'week':
        week_start = dt - timedelta(days=dt.weekday())
        return week_start.strftime('%Y-%m-%d')
    if group_by == 'year':
        return dt.strftime('%Y')
    return dt.strftime('%Y-%m')


def _build_time_report(invoices, filters):
    grouped = defaultdict(lambda: {
        'label': '',
        'invoice_count': 0,
        'total_invoiced': 0,
        'total_received': 0,
        'total_pending': 0,
    })

    for invoice in invoices:
        serialized = _serialize_invoice(invoice, filters)
        if not invoice.invoice_date:
            continue
        if serialized['total_amount'] <= 0 and serialized['amount_paid'] <= 0 and serialized['pending'] <= 0:
            continue

        key = _time_bucket_key(invoice.invoice_date, filters['group_by'])
        bucket = grouped[key]
        bucket['label'] = _time_bucket_label(invoice.invoice_date, filters['group_by'])
        bucket['invoice_count'] += 1
        bucket['total_invoiced'] += float(serialized['total_amount'] or 0)
        bucket['total_received'] += float(serialized['amount_paid'] or 0)
        bucket['total_pending'] += float(serialized['pending'] or 0)

    items = []
    for key in sorted(grouped.keys(), reverse=True):
        bucket = grouped[key]
        bucket['total_invoiced'] = _safe_float(bucket['total_invoiced'])
        bucket['total_received'] = _safe_float(bucket['total_received'])
        bucket['total_pending'] = _safe_float(bucket['total_pending'])
        bucket['metric_value'] = _safe_float(_choose_value(
            bucket['total_invoiced'],
            bucket['total_received'],
            bucket['total_pending'],
            filters['value_basis']
        ))
        items.append({
            'period': bucket['label'],
            'invoice_count': bucket['invoice_count'],
            'total_invoiced': bucket['total_invoiced'],
            'total_received': bucket['total_received'],
            'total_pending': bucket['total_pending'],
            'metric_value': bucket['metric_value'],
        })

    return items


def _build_chart_data(customer_items, item_items, time_items):
    return {
        'top_customers': customer_items[:5],
        'top_items': item_items[:5],
        'time_trend': list(reversed(time_items[:6])),
    }


def _generate_report_payload(filters):
    invoices = _filtered_invoices(filters)
    purchases = _filtered_purchases(filters)
    invoice_items = _build_invoice_report(invoices, filters)
    summary = _build_summary(invoice_items)
    purchase_summary = _build_purchase_summary(purchases)
    customer_items = _build_customer_report(invoices, filters)
    item_items, product_cost_received = _build_item_report(invoices, filters)
    time_items = _build_time_report(invoices, filters)
    metric_total = _safe_float(sum(item['metric_value'] for item in item_items))
    sales_gst_collected = _safe_float(sum(float(invoice.gst_amount or 0) for invoice in invoices))
    summary['estimated_product_cost_received'] = product_cost_received
    summary['estimated_product_gross_profit'] = _safe_float(summary['total_products_received'] - product_cost_received)
    summary['sales_gst_collected'] = sales_gst_collected
    summary['purchase_spend'] = purchase_summary['purchase_spend']
    summary['purchase_gst_paid'] = purchase_summary['purchase_gst_paid']
    summary['net_gst_liability'] = _safe_float(sales_gst_collected - purchase_summary['purchase_gst_paid'])
    summary['estimated_net_profit'] = _safe_float(summary['total_received'] - purchase_summary['purchase_spend'])

    return {
        'summary': summary,
        'filters': {
            'group_by': filters['group_by'],
            'value_basis': filters['value_basis'],
        },
        'invoice_wise': {
            'items': invoice_items,
            'total': len(invoice_items),
        },
        'customer_wise': {
            'items': customer_items,
            'total': len(customer_items),
        },
        'item_wise': {
            'items': item_items,
            'total': len(item_items),
            'metric_total': metric_total,
        },
        'time_wise': {
            'items': time_items,
            'total': len(time_items),
        },
        'charts': _build_chart_data(customer_items, item_items, time_items),
    }


def _csv_rows_for_report(report_type, payload):
    summary = payload['summary']
    if report_type == 'summary':
        return [
            ['Metric', 'Value'],
            ['Total Received', summary['total_received']],
            ['Total Invoiced', summary['total_invoiced']],
            ['Total Pending', summary['total_pending']],
            ['Total Invoices', summary['total_invoices']],
            ['Paid Or Partial Invoices', summary['paid_invoice_count']],
            ['Unique Customers', summary['unique_customers']],
            ['Products Received', summary['total_products_received']],
            ['Services Received', summary['total_services_received']],
            ['Estimated Product Cost Received', summary['estimated_product_cost_received']],
            ['Estimated Product Gross Profit', summary['estimated_product_gross_profit']],
            ['Sales GST Collected', summary['sales_gst_collected']],
            ['Purchase Spend', summary['purchase_spend']],
            ['Purchase GST Paid', summary['purchase_gst_paid']],
            ['Net GST Liability', summary['net_gst_liability']],
            ['Estimated Net Profit', summary['estimated_net_profit']],
        ]
    if report_type == 'invoice':
        rows = [[
            'Invoice Number', 'Customer', 'Invoice Date', 'Status', 'Total Amount',
            'Amount Paid', 'Pending', 'Products Total', 'Products Received',
            'Services Total', 'Services Received'
        ]]
        for item in payload['invoice_wise']['items']:
            rows.append([
                item['invoice_number'], item['customer_name'], item['invoice_date'], item['status'],
                item['total_amount'], item['amount_paid'], item['pending'],
                item['products_total'], item['products_received'],
                item['services_total'], item['services_received']
            ])
        return rows
    if report_type == 'customer':
        rows = [['Customer', 'Invoice Count', 'Total Invoiced', 'Total Received', 'Pending']]
        for item in payload['customer_wise']['items']:
            rows.append([
                item['customer_name'], item['invoice_count'], item['total_invoiced'],
                item['total_received'], item['total_pending']
            ])
        return rows
    if report_type == 'item':
        rows = [[
            'Name', 'Type', 'Line Count', 'Quantity', 'Total Invoiced',
            'Total Received', 'Pending', 'Current Metric'
        ]]
        for item in payload['item_wise']['items']:
            rows.append([
                item['name'], item['type'], item['line_count'], item['quantity'],
                item['total_invoiced'], item['total_received'], item['total_pending'],
                item['metric_value']
            ])
        return rows

    rows = [['Period', 'Invoice Count', 'Total Invoiced', 'Total Received', 'Pending', 'Current Metric']]
    for item in payload['time_wise']['items']:
        rows.append([
            item['period'], item['invoice_count'], item['total_invoiced'],
            item['total_received'], item['total_pending'], item['metric_value']
        ])
    return rows


@finance_bp.route('/')
@login_required
def dashboard():
    """Main finance analytics dashboard"""
    customers = Customer.query.order_by(Customer.name.asc()).all()
    return render_template('admin/finance.html', customers=customers, username=session.get('username'))


@finance_bp.route('/api/reports', methods=['POST'])
@login_required
def get_reports():
    """Return all finance report datasets based on selected filters."""
    filters = _get_filters(request.get_json())
    return jsonify(_generate_report_payload(filters))


@finance_bp.route('/api/export', methods=['POST'])
@login_required
def export_report():
    """Export current filtered finance report as CSV."""
    payload = request.get_json() or {}
    filters = _get_filters(payload)
    report_type = payload.get('report_type', 'invoice')
    report_payload = _generate_report_payload(filters)
    rows = _csv_rows_for_report(report_type, report_payload)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    csv_data = buffer.getvalue()
    buffer.close()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'finance_{report_type}_{timestamp}.csv'

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@finance_bp.route('/api/lookups', methods=['GET'])
@login_required
def get_lookups():
    """Lookups for dynamic filter controls."""
    customer_rows = Customer.query.order_by(Customer.name.asc()).all()
    return jsonify({
        'customers': [{'id': customer.id, 'name': customer.name} for customer in customer_rows],
        'invoice_statuses': ['active', 'all', 'PAID', 'PARTIAL', 'ISSUED', 'OVERDUE', 'DRAFT', 'CANCELLED'],
        'group_by_options': ['day', 'week', 'month', 'year'],
        'value_basis_options': ['received', 'invoiced', 'pending'],
        'item_types': ['all', 'product', 'service'],
    })
