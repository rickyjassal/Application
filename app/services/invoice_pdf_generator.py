"""Simple PDF generator for tax invoices without external PDF libraries."""

from app.services.simple_pdf import SimplePDFBuilder


class InvoicePDFGenerator:
    """Generate invoice PDFs using a lightweight pure-Python PDF writer."""

    def __init__(self, invoice):
        self.invoice = invoice

    def generate(self):
        branding = self.invoice.get_branding()
        customer = self.invoice.customer
        pdf = SimplePDFBuilder('Invoice {}'.format(self.invoice.invoice_number))

        pdf.add_line(branding.get('business_legal_name', branding.get('business_name', 'Business')))
        pdf.add_line('Address: {}'.format(branding.get('business_address', '')))
        pdf.add_line('ABN: {}'.format(branding.get('business_abn', '')))
        pdf.add_line('Contact: {}'.format(branding.get('business_contact_email', '')))
        pdf.add_blank_line()
        pdf.add_line('TAX INVOICE')
        pdf.add_line('Invoice Number: {}'.format(self.invoice.invoice_number))
        pdf.add_line('Invoice Date: {}'.format(self._fmt_date(self.invoice.invoice_date)))
        pdf.add_line('Due Date: {}'.format(self._fmt_date(self.invoice.due_date)))
        pdf.add_line('Reference: {}'.format(self.invoice.reference or 'N/A'))
        pdf.add_blank_line()
        pdf.add_line('Bill To:')
        pdf.add_line(customer.business_name if customer and customer.business_name else customer.name if customer else 'Customer', 1)
        pdf.add_line('ABN: {}'.format(customer.abn if customer and customer.abn else 'N/A'), 1)
        pdf.add_line('Address: {}'.format(customer.get_full_address() if customer else 'N/A'), 1)
        pdf.add_line('Phone: {}'.format(customer.phone if customer and customer.phone else 'N/A'), 1)
        pdf.add_line('Email: {}'.format(customer.email if customer and customer.email else 'N/A'), 1)
        pdf.add_blank_line()
        pdf.add_line('Items:')
        pdf.add_line('Description | Qty | Unit Price | Line Total', 1)
        for item in self.invoice.line_items:
            description = item.product.name if item.product else item.service.name if item.service else (item.description or '')
            pdf.add_line(
                '{} | {} | ${:.2f} | ${:.2f}'.format(
                    description,
                    self._fmt_number(item.quantity),
                    float(item.unit_price or 0),
                    float((item.quantity or 0) * (item.unit_price or 0)),
                ),
                1,
            )
        pdf.add_blank_line()
        pdf.add_line('Subtotal: ${:.2f}'.format(float(self.invoice.subtotal or 0)))
        pdf.add_line('{} ${:.2f}'.format(self._gst_label(), float(self.invoice.gst_amount or 0)))
        pdf.add_line('Total: ${:.2f}'.format(float(self.invoice.total_amount or 0)))
        pdf.add_line('Credit Note: ${:.2f}'.format(float(self.invoice.credit_note_amount or 0)))
        pdf.add_line('Advance: ${:.2f}'.format(float(self.invoice.amount_paid or 0)))
        pdf.add_line('Balance: ${:.2f}'.format(float(self.invoice.get_balance_due() or 0)))
        pdf.add_blank_line()
        pdf.add_line('Bank: {}'.format(branding.get('bank_name', '')))
        pdf.add_line('Account Name: {}'.format(branding.get('bank_account_name', '')))
        pdf.add_line('BSB: {}'.format(branding.get('bank_bsb', '')))
        pdf.add_line('Account Number: {}'.format(branding.get('bank_account_number', '')))
        if self.invoice.notes:
            pdf.add_blank_line()
            pdf.add_line('Notes:')
            for line in str(self.invoice.notes).splitlines():
                pdf.add_line(line, 1)
        return pdf.build()

    def _fmt_date(self, value):
        return value.strftime('%d/%b/%Y') if value else 'N/A'

    def _fmt_number(self, value):
        try:
            return '{:.2f}'.format(float(value or 0))
        except Exception:
            return str(value or 0)

    def _gst_label(self):
        if self.invoice.gst_mode == 'inclusive':
            return 'Included GST:'
        if self.invoice.gst_mode == 'none':
            return 'GST (none):'
        return 'GST:'
