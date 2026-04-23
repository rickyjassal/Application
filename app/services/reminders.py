from datetime import datetime, timedelta

from app import db
from app.models import Invoice
from app.services.activity import log_activity
from app.services.mailer import send_email
from app.services.settings import get_app_settings


def get_due_overdue_invoices(limit=None):
    """Return overdue invoices that are eligible for another reminder."""
    now = datetime.utcnow()
    cooldown = now - timedelta(hours=24)
    query = (
        Invoice.query
        .filter(Invoice.due_date.isnot(None))
        .filter(Invoice.due_date < now)
        .filter(Invoice.status.in_(['ISSUED', 'PARTIAL', 'OVERDUE']))
        .order_by(Invoice.due_date.asc(), Invoice.id.asc())
    )

    due_invoices = []
    for invoice in query.all():
        if not invoice.customer or not invoice.customer.email:
            continue
        if invoice.get_balance_due() <= 0:
            continue
        if invoice.last_reminder_at and invoice.last_reminder_at > cooldown:
            continue
        due_invoices.append(invoice)
        if limit and len(due_invoices) >= limit:
            break
    return due_invoices


def send_invoice_reminder_message(invoice):
    """Send an overdue reminder email with the current invoice PDF attached."""
    if not invoice.customer or not invoice.customer.email:
        raise RuntimeError('Customer email is not available for this invoice.')

    settings = get_app_settings()
    business_name = settings.get('business_name', 'Western IT Solutions')
    balance_due = invoice.get_balance_due()
    due_date_text = invoice.due_date.strftime('%d %B %Y') if invoice.due_date else 'Immediately'
    from app.services.invoice_email_templates import InvoiceEmailTemplate
    from app.services.invoice_pdf_generator import InvoicePDFGenerator

    subject = 'Overdue Reminder: Invoice {} from {}'.format(invoice.invoice_number, business_name)
    text_body = (
        "Hello {},\n\n"
        "This is a reminder that invoice {} is overdue.\n"
        "Outstanding amount: ${:.2f}\n"
        "Due date: {}\n\n"
        "Please arrange payment at your earliest convenience. "
        "The latest invoice PDF is attached for your reference.\n\n"
        "Regards,\nAccounts\n{}"
    ).format(
        invoice.customer.name,
        invoice.invoice_number,
        balance_due,
        due_date_text,
        business_name
    )
    html_body = InvoiceEmailTemplate.generate_invoice_email(
        invoice,
        business_name=business_name,
    )
    pdf_buffer = InvoicePDFGenerator(invoice).generate()
    send_email(
        invoice.customer.email,
        subject,
        text_body,
        html_body,
        [('Invoice_{}.pdf'.format(invoice.invoice_number), pdf_buffer)],
    )


def run_overdue_reminders(actor=None, limit=None):
    """Send reminders for overdue invoices and record audit trail."""
    sent = []
    for invoice in get_due_overdue_invoices(limit=limit):
        send_invoice_reminder_message(invoice)
        invoice.status = 'OVERDUE'
        invoice.reminder_count = int(invoice.reminder_count or 0) + 1
        invoice.last_reminder_at = datetime.utcnow()
        log_activity(
            'invoice',
            'reminder_sent',
            'Overdue reminder sent for {} to {}'.format(invoice.invoice_number, invoice.customer.email),
            entity_id=invoice.id,
            actor=actor,
        )
        sent.append(invoice.invoice_number)

    if sent:
        db.session.commit()
    return sent
