"""PDF generator for Quotes."""

from datetime import datetime
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class QuotePDFGenerator:
    """Generate PDF quotes with frozen branding."""

    def __init__(self, quote, business_name="Western IT Solutions", business_email="info@westernitsolutions.com.au"):
        self.quote = quote
        self.branding = quote.get_branding()
        self.business_name = self.branding.get('business_name') or business_name
        self.business_email = self.branding.get('business_contact_email') or business_email
        self.primary_color = self.branding.get('brand_primary_color', '#dc2626')
        self.page_size = A4

    def generate(self):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.page_size, topMargin=0.5 * inch, bottomMargin=0.5 * inch)

        story = [
            self._build_header(),
            Spacer(1, 0.2 * inch),
            self._build_quote_info(),
            Spacer(1, 0.2 * inch),
            self._build_customer_info(),
            Spacer(1, 0.2 * inch),
            self._build_line_items_table(),
            Spacer(1, 0.2 * inch),
            self._build_totals_section(),
            Spacer(1, 0.3 * inch),
        ]

        if self.quote.terms_and_conditions:
            story.extend([self._build_terms_section(), Spacer(1, 0.2 * inch)])
        if self.quote.notes:
            story.extend([self._build_notes_section(), Spacer(1, 0.2 * inch)])

        story.append(self._build_footer())
        doc.build(story)
        buffer.seek(0)
        return buffer

    def _build_header(self):
        styles = getSampleStyleSheet()
        header_style = ParagraphStyle(
            'QuoteHeader',
            parent=styles['Normal'],
            fontSize=24,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor(self.primary_color),
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            'QuoteSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            spaceAfter=3,
        )

        logo_path = Path(__file__).resolve().parents[1] / 'static' / Path(self.branding.get('brand_logo_path', 'images/Logo.png'))
        logo_cell = ''
        if logo_path.exists():
            logo_cell = Image(str(logo_path), width=0.7 * inch, height=0.7 * inch, kind='proportional')

        return Table(
            [[logo_cell, Paragraph(self.business_name, header_style), Paragraph(f"Email: {self.business_email}", subtitle_style)]],
            colWidths=[0.9 * inch, 3.3 * inch, 2.3 * inch],
            style=TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]),
        )

    def _build_quote_info(self):
        styles = getSampleStyleSheet()
        label_style = ParagraphStyle(
            'QuoteInfoLabel',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor(self.primary_color),
        )
        value_style = ParagraphStyle(
            'QuoteInfoValue',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
        )

        data = [[
            Paragraph('Quote #', label_style),
            Paragraph(str(self.quote.quote_number), value_style),
            Paragraph('Date', label_style),
            Paragraph(self.quote.quote_date.strftime('%d %B %Y'), value_style),
            Paragraph('Valid Until', label_style),
            Paragraph(self.quote.expiry_date.strftime('%d %B %Y'), value_style),
        ]]
        return Table(
            data,
            colWidths=[1 * inch, 1.5 * inch, 0.8 * inch, 1.2 * inch, 1 * inch, 1.5 * inch],
            style=TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]),
        )

    def _build_customer_info(self):
        styles = getSampleStyleSheet()
        label_style = ParagraphStyle(
            'QuoteCustomerLabel',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor(self.primary_color),
        )
        value_style = ParagraphStyle(
            'QuoteCustomerValue',
            parent=styles['Normal'],
            fontSize=10,
        )

        customer = self.quote.customer
        customer_info = f"{customer.name}\n{customer.email or ''}\n"
        if customer.phone:
            customer_info += f"{customer.phone}\n"
        address_parts = [customer.street_address, customer.suburb, customer.state, customer.postcode]
        address_line = ', '.join(filter(None, address_parts))
        if address_line:
            customer_info += address_line

        return Table(
            [[Paragraph('BILL TO:', label_style), Paragraph(customer_info.replace('\n', '<br/>'), value_style)]],
            colWidths=[1 * inch, 5.5 * inch],
            style=TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]),
        )

    def _build_line_items_table(self):
        styles = getSampleStyleSheet()
        header_style = ParagraphStyle(
            'QuoteTableHeader',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.whitesmoke,
            alignment=1,
        )
        cell_style = ParagraphStyle(
            'QuoteTableCell',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica',
        )

        data = [[
            Paragraph('Description', header_style),
            Paragraph('Qty', header_style),
            Paragraph('Unit Price', header_style),
            Paragraph('Total', header_style),
        ]]

        for item in self.quote.line_items:
            data.append([
                Paragraph(str(item.description or ''), cell_style),
                Paragraph(f'{item.quantity}', cell_style),
                Paragraph(f'${item.unit_price:.2f}', cell_style),
                Paragraph(f'${item.get_line_total():.2f}', cell_style),
            ])

        return Table(
            data,
            colWidths=[3.5 * inch, 0.8 * inch, 1.2 * inch, 1.3 * inch],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.primary_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9f9f9')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]),
        )

    def _build_totals_section(self):
        styles = getSampleStyleSheet()
        label_style = ParagraphStyle(
            'QuoteTotalsLabel',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor(self.primary_color),
            alignment=2,
        )
        value_style = ParagraphStyle(
            'QuoteTotalsValue',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            alignment=2,
        )
        total_value_style = ParagraphStyle(
            'QuoteTotalsFinal',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor(self.primary_color),
            alignment=2,
        )

        data = [
            [Paragraph('', label_style), Paragraph('Subtotal:', label_style), Paragraph(f'${self.quote.get_subtotal():.2f}', value_style)],
            [Paragraph('', label_style), Paragraph('GST (10%):', label_style), Paragraph(f'${self.quote.get_gst():.2f}', value_style)],
            [Paragraph('', label_style), Paragraph('TOTAL:', label_style), Paragraph(f'${self.quote.get_total():.2f}', total_value_style)],
        ]
        return Table(
            data,
            colWidths=[3.5 * inch, 1.2 * inch, 1.3 * inch],
            style=TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#e8f0f7')),
                ('GRID', (1, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]),
        )

    def _build_terms_section(self):
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'QuoteTermsTitle',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor(self.primary_color),
            spaceAfter=6,
        )
        text_style = ParagraphStyle(
            'QuoteTermsText',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#333333'),
        )
        return Table(
            [[Paragraph('Terms and Conditions', title_style)], [Paragraph(self.quote.terms_and_conditions.replace('\n', '<br/>'), text_style)]],
            colWidths=[6.5 * inch],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]),
        )

    def _build_notes_section(self):
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'QuoteNotesTitle',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor(self.primary_color),
            spaceAfter=6,
        )
        text_style = ParagraphStyle(
            'QuoteNotesText',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#333333'),
        )
        return Table(
            [[Paragraph('Notes', title_style)], [Paragraph(self.quote.notes.replace('\n', '<br/>'), text_style)]],
            colWidths=[6.5 * inch],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]),
        )

    def _build_footer(self):
        styles = getSampleStyleSheet()
        footer_style = ParagraphStyle(
            'QuoteFooter',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#999999'),
            alignment=1,
            spaceAfter=3,
        )
        footer_text = Paragraph(
            f"Generated on {datetime.utcnow().strftime('%d %B %Y at %H:%M')} | "
            f"This quote is valid until {self.quote.expiry_date.strftime('%d %B %Y')}",
            footer_style,
        )
        return Table(
            [[footer_text]],
            colWidths=[6.5 * inch],
            style=TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]),
        )
