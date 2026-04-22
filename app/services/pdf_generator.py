"""Simple PDF generator for quotes without external PDF libraries."""

from app.services.simple_pdf import SimplePDFBuilder


class QuotePDFGenerator:
    """Generate quote PDFs using a lightweight pure-Python PDF writer."""

    def __init__(self, quote, business_name="Western IT Solutions", business_email="info@westernitsolutions.com.au"):
        self.quote = quote
        self.branding = quote.get_branding()
        self.business_name = self.branding.get('business_name') or business_name
        self.business_email = self.branding.get('business_contact_email') or business_email

    def generate(self):
        customer = self.quote.customer
        pdf = SimplePDFBuilder('Quote {}'.format(self.quote.quote_number))

        pdf.add_line(self.branding.get('business_legal_name', self.business_name))
        pdf.add_line('Address: {}'.format(self.branding.get('business_address', '')))
        pdf.add_line('ABN: {}'.format(self.branding.get('business_abn', '')))
        pdf.add_line('Contact: {}'.format(self.business_email))
        pdf.add_blank_line()
        pdf.add_line('QUOTE')
        pdf.add_line('Quote Number: {}'.format(self.quote.quote_number))
        pdf.add_line('Quote Date: {}'.format(self._fmt_date(self.quote.quote_date)))
        pdf.add_line('Expiry Date: {}'.format(self._fmt_date(self.quote.expiry_date)))
        pdf.add_line('Status: {}'.format(self.quote.status or 'DRAFT'))
        pdf.add_blank_line()
        pdf.add_line('Customer:')
        pdf.add_line(customer.business_name if customer and customer.business_name else customer.name if customer else 'Customer', 1)
        pdf.add_line('Email: {}'.format(customer.email if customer and customer.email else 'N/A'), 1)
        pdf.add_line('Phone: {}'.format(customer.phone if customer and customer.phone else 'N/A'), 1)
        pdf.add_line('Address: {}'.format(customer.get_full_address() if customer else 'N/A'), 1)
        pdf.add_blank_line()
        pdf.add_line('Items:')
        pdf.add_line('Description | Qty | Unit Price | Line Total', 1)
        for item in self.quote.line_items:
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
        pdf.add_line('Subtotal: ${:.2f}'.format(float(self.quote.get_subtotal() or 0)))
        pdf.add_line('{} ${:.2f}'.format(self._gst_label(), float(self.quote.get_gst() or 0)))
        pdf.add_line('Total: ${:.2f}'.format(float(self.quote.get_total() or 0)))
        if self.quote.terms_and_conditions:
            pdf.add_blank_line()
            pdf.add_line('Terms and Conditions:')
            for line in str(self.quote.terms_and_conditions).splitlines():
                pdf.add_line(line, 1)
        if self.quote.notes:
            pdf.add_blank_line()
            pdf.add_line('Notes:')
            for line in str(self.quote.notes).splitlines():
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
        if self.quote.gst_mode == 'inclusive':
            return 'Included GST:'
        if self.quote.gst_mode == 'none':
            return 'GST (none):'
        return 'GST:'
