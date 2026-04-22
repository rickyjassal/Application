from app.services.settings import get_app_settings
from app.services.simple_pdf import SimplePDFBuilder


class StatementPDFGenerator:
    """Generate customer statement PDFs without external PDF libraries."""

    def __init__(self, customer, invoices, totals):
        self.customer = customer
        self.invoices = invoices
        self.totals = totals

    def generate(self):
        settings = get_app_settings()
        customer_name = self.customer.business_name or self.customer.name
        pdf = SimplePDFBuilder('Statement {}'.format(customer_name))

        pdf.add_line(settings.get('business_legal_name', settings.get('business_name', 'Business')))
        pdf.add_line('Address: {}'.format(settings.get('business_address', '')))
        pdf.add_line('ABN: {}'.format(settings.get('business_abn', '')))
        pdf.add_line('Contact: {}'.format(settings.get('business_contact_email', '')))
        pdf.add_blank_line()
        pdf.add_line('CUSTOMER STATEMENT')
        pdf.add_line('Customer: {}'.format(customer_name))
        pdf.add_line('Email: {}'.format(self.customer.email or 'N/A'))
        pdf.add_line('Address: {}'.format(self.customer.get_full_address() or 'N/A'))
        pdf.add_blank_line()
        pdf.add_line('Invoices:')
        pdf.add_line('Invoice | Date | Due | Status | Total | Paid | Balance', 1)
        for invoice in self.invoices:
            pdf.add_line(
                '{} | {} | {} | {} | ${:.2f} | ${:.2f} | ${:.2f}'.format(
                    invoice.invoice_number,
                    self._fmt_date(invoice.invoice_date),
                    self._fmt_date(invoice.due_date),
                    invoice.status,
                    float(invoice.total_amount or 0),
                    float(invoice.amount_paid or 0),
                    float(invoice.get_balance_due() or 0),
                ),
                1,
            )
        pdf.add_blank_line()
        pdf.add_line('Total Invoiced: ${:.2f}'.format(float(self.totals.get('total_invoiced', 0))))
        pdf.add_line('Total Paid: ${:.2f}'.format(float(self.totals.get('total_paid', 0))))
        pdf.add_line('Outstanding: ${:.2f}'.format(float(self.totals.get('outstanding', 0))))
        return pdf.build()

    def _fmt_date(self, value):
        return value.strftime('%d/%m/%Y') if value else 'N/A'
