from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.settings import get_app_settings


class StatementPDFGenerator:
    """Generate customer statement PDFs with current branding."""

    def __init__(self, customer, invoices, totals):
        self.customer = customer
        self.invoices = invoices
        self.totals = totals
        self.styles = getSampleStyleSheet()

    def generate(self):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=14 * mm,
            rightMargin=14 * mm,
            topMargin=14 * mm,
            bottomMargin=12 * mm,
        )

        story = []
        story.extend(self._build_header())
        story.append(Spacer(1, 7 * mm))
        story.append(self._build_table())
        doc.build(story)
        buffer.seek(0)
        return buffer

    def _build_header(self):
        settings = get_app_settings()
        primary_color = settings.get('brand_primary_color', '#b91c1c')
        title_style = ParagraphStyle(
            'StatementTitle',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor(primary_color),
        )
        body_style = ParagraphStyle(
            'StatementBody',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=13,
        )
        customer_name = self.customer.business_name or self.customer.name
        customer_address = self.customer.get_full_address() or 'N/A'

        header_table = Table([[
            Paragraph(
                f"<b>{self._escape(settings.get('business_legal_name', settings.get('business_name', 'Business')))}</b><br/>"
                f"{self._escape(settings.get('business_address', ''))}<br/>"
                f"ABN: {self._escape(settings.get('business_abn', ''))}<br/>"
                f"Contact: {self._escape(settings.get('business_contact_email', ''))}",
                body_style,
            ),
            Paragraph(
                f"<b>Customer Statement</b><br/><br/>"
                f"<b>{self._escape(customer_name)}</b><br/>"
                f"{self._escape(customer_address)}<br/>"
                f"{self._escape(self.customer.email or '')}",
                ParagraphStyle(
                    'StatementRight',
                    parent=body_style,
                    alignment=2,
                ),
            ),
        ]], colWidths=[95 * mm, 78 * mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        return [
            Paragraph('Customer Statement', title_style),
            Spacer(1, 3 * mm),
            header_table,
        ]

    def _build_table(self):
        rows = [[
            'Invoice #',
            'Invoice Date',
            'Due Date',
            'Status',
            'Total',
            'Paid',
            'Outstanding',
        ]]
        for invoice in self.invoices:
            rows.append([
                invoice.invoice_number,
                self._fmt_date(invoice.invoice_date),
                self._fmt_date(invoice.due_date),
                invoice.status,
                f"${float(invoice.total_amount or 0):.2f}",
                f"${float(invoice.amount_paid or 0):.2f}",
                f"${float(invoice.get_balance_due() or 0):.2f}",
            ])

        rows.append([
            '',
            '',
            '',
            'Totals',
            f"${float(self.totals.get('invoiced', 0)):.2f}",
            f"${float(self.totals.get('paid', 0)):.2f}",
            f"${float(self.totals.get('outstanding', 0)):.2f}",
        ])

        table = Table(rows, colWidths=[28 * mm, 25 * mm, 24 * mm, 24 * mm, 23 * mm, 23 * mm, 26 * mm], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(get_app_settings().get('brand_primary_color', '#b91c1c'))),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fef2f2')),
            ('GRID', (0, 0), (-1, -1), 0.6, colors.HexColor('#d1d5db')),
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        return table

    def _fmt_date(self, value):
        return value.strftime('%d/%m/%Y') if value else 'N/A'

    def _escape(self, value):
        return (
            str(value or '')
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
        )
