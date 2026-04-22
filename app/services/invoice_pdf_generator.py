"""Stable PDF generator for tax invoices using ReportLab."""

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

class InvoicePDFGenerator:
    """Generate invoice PDFs in a stable single-file format."""

    def __init__(self, invoice):
        self.invoice = invoice
        self.page_size = A4
        self.width, self.height = self.page_size
        self.styles = getSampleStyleSheet()

    def generate(self):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            leftMargin=14 * mm,
            rightMargin=14 * mm,
            topMargin=14 * mm,
            bottomMargin=12 * mm,
        )

        story = []
        story.extend(self._build_header())
        story.append(Spacer(1, 8 * mm))
        story.append(self._build_customer_block())
        story.append(Spacer(1, 6 * mm))
        story.append(self._build_line_items_table())
        story.append(Spacer(1, 6 * mm))
        story.append(self._build_summary_table())
        story.append(Spacer(1, 5 * mm))
        story.append(self._build_footer_note())

        if self.invoice.notes:
            story.append(Spacer(1, 4 * mm))
            story.append(self._build_notes_block())

        doc.build(story)
        buffer.seek(0)
        return buffer

    def _build_header(self):
        settings = self.invoice.get_branding()
        primary_color = settings.get('brand_primary_color', '#dc2626')
        logo_relative_path = settings.get('brand_logo_path', 'images/Logo.png')
        logo_path = Path(__file__).resolve().parents[1] / 'static' / Path(logo_relative_path)
        logo_flowable = Spacer(1, 1)
        if logo_path.exists():
            logo_width = 40 * mm
            logo_height = logo_width * 779 / 723
            logo_flowable = Image(str(logo_path), width=logo_width, height=logo_height)
            logo_flowable.hAlign = 'LEFT'

        label_style = ParagraphStyle(
            'HeaderLabel',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            textColor=colors.black,
        )
        value_style = ParagraphStyle(
            'HeaderValue',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            textColor=colors.black,
        )
        left_html = """
        <font name="Helvetica-Bold" size="14">{legal_name}</font><br/>
        <font name="Helvetica" size="9">ADDRESS:</font> <font name="Helvetica" size="9">{address}</font><br/>
        <font name="Helvetica" size="9">ABN:</font> <font name="Helvetica" size="9">{abn}</font><br/>
        <font name="Helvetica" size="9">CONTACT:</font> <font name="Helvetica" size="9">{email}</font>
        """.format(
            legal_name=self._escape(settings.get('business_legal_name', 'WESTERN IT SOLUTIONS PTY LTD')),
            address=self._escape(settings.get('business_address', 'Tarneit - 3029')),
            abn=self._escape(settings.get('business_abn', '95 670 634 465')),
            email=self._escape(settings.get('business_contact_email', 'info@westernitsolutions.com.au')),
        )

        right_meta_html = f"""
        <font name="Helvetica">Date:</font> <font name="Helvetica-Bold">{self._fmt_date(self.invoice.invoice_date)}</font><br/>
        <font name="Helvetica">Invoice:</font> <font name="Helvetica-Bold">{self.invoice.invoice_number}</font><br/>
        <font name="Helvetica">Ref:</font> <font name="Helvetica-Bold">{self.invoice.reference or 'N/A'}</font>
        """

        header_table = Table(
            [[
                [
                    logo_flowable,
                    Spacer(1, 3 * mm),
                    Paragraph(left_html, label_style),
                ],
                Paragraph(f'Tax Invoice<br/><br/>{right_meta_html}', ParagraphStyle(
                    'RightHeader',
                    parent=value_style,
                    fontSize=9,
                    leading=12,
                    alignment=2,
                )),
            ]],
            colWidths=[105 * mm, 58 * mm],
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

        return [header_table]

    def _build_customer_block(self):
        customer = self.invoice.customer
        customer_name = self._escape(
            customer.business_name if customer and customer.business_name else customer.name if customer else 'Customer'
        )
        customer_email = self._escape(customer.email if customer and customer.email else 'N/A')
        customer_phone = self._escape(customer.phone if customer and customer.phone else 'N/A')
        customer_abn = self._escape(customer.abn if customer and customer.abn else 'N/A')
        customer_address = self._escape(customer.get_full_address() if customer and customer.get_full_address() else 'N/A')

        name_style = ParagraphStyle(
            'CustomerName',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            spaceAfter=6,
        )
        label_style = ParagraphStyle(
            'CustomerLabel',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=13,
            alignment=0,
        )
        value_style = ParagraphStyle(
            'CustomerValue',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            alignment=0,
        )

        info_table = Table([
            [Paragraph('ABN:', label_style), Paragraph(customer_abn, value_style)],
            [Paragraph('ADDRESS:', label_style), Paragraph(customer_address, value_style)],
            [Paragraph('TEL:', label_style), Paragraph(customer_phone, value_style)],
            [Paragraph('EMAIL:', label_style), Paragraph(customer_email, value_style)],
        ], colWidths=[24 * mm, 106 * mm])
        info_table.hAlign = 'LEFT'
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))

        customer_table = Table([
            [Paragraph(customer_name, name_style)],
            [info_table],
        ], colWidths=[130 * mm])
        customer_table.hAlign = 'LEFT'
        customer_table.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        customer_wrapper = Table([
            ['', customer_table],
        ], colWidths=[15 * mm, 130 * mm])
        customer_wrapper.hAlign = 'LEFT'
        customer_wrapper.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        return customer_wrapper

    def _build_line_items_table(self):
        rows = [[
            Paragraph('<b>Description</b>', self._table_header_style()),
            Paragraph('<b>Price</b>', self._table_header_style()),
            Paragraph('<b>Quantity</b>', self._table_header_style()),
            Paragraph('<b>Total Amount</b>', self._table_header_style()),
        ]]
        item_row_count = 0

        for item in self.invoice.line_items:
            description = item.product.name if item.product else item.service.name if item.service else (item.description or '')
            rows.append([
                Paragraph(self._escape(description), self._table_cell_style(left=True)),
                Paragraph(f'${item.unit_price or 0:.2f}', self._table_cell_style()),
                Paragraph(f'{item.quantity or 0:.2f}', self._table_cell_style()),
                Paragraph(f'${(item.quantity or 0) * (item.unit_price or 0):.2f}', self._table_cell_style()),
            ])
            item_row_count += 1

        min_visible_rows = 7
        while len(rows) - 1 < min_visible_rows:
            rows.append([
                Paragraph('&nbsp;', self._table_cell_style(left=True)),
                Paragraph('&nbsp;', self._table_cell_style()),
                Paragraph('&nbsp;', self._table_cell_style()),
                Paragraph('&nbsp;', self._table_cell_style()),
            ])

        table = Table(rows, colWidths=[90 * mm, 23 * mm, 20 * mm, 30 * mm], repeatRows=1)
        styles = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#cfcfcf')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.black),
            ('LINEAFTER', (0, 0), (0, -1), 1.5, colors.black),
            ('LINEAFTER', (1, 0), (1, -1), 1.5, colors.black),
            ('LINEAFTER', (2, 0), (2, -1), 1.5, colors.black),
        ]

        for row_index in range(1, item_row_count + 1):
            styles.append(('LINEBELOW', (0, row_index), (-1, row_index), 1.5, colors.black))

        table.setStyle(TableStyle(styles))
        return table

    def _build_summary_table(self):
        settings = self.invoice.get_branding()
        primary_color = settings.get('brand_primary_color', '#dc2626')
        eft_style = ParagraphStyle(
            'Eft',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=13,
            textColor=colors.white,
        )
        due_style = ParagraphStyle(
            'Due',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.black,
        )
        gst_label = 'Included GST:' if self.invoice.gst_mode == 'inclusive' else 'GST:'
        gst_suffix = '(GST included)' if self.invoice.gst_mode == 'inclusive' else '(no GST)' if self.invoice.gst_mode == 'none' else '(inc-GST)'
        balance = self.invoice.get_balance_due()

        eft_box = Table([[
            Paragraph(
                'EFT DETAILS:<br/>'
                f'Bank: {self._escape(settings.get("bank_name", "CBA"))}<br/>'
                f'Account Name: {self._escape(settings.get("bank_account_name", "Western IT Solutions"))}<br/>'
                f'BSB: {self._escape(settings.get("bank_bsb", "062-692"))} A/C: {self._escape(settings.get("bank_account_number", "7997 5017"))}',
                eft_style,
            )
        ]], colWidths=[72 * mm])
        eft_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(primary_color)),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        due_box = Table([[
            Paragraph('Invoice Due Date:', ParagraphStyle(
                'DueLabel',
                parent=due_style,
                textColor=colors.HexColor(primary_color),
            )),
            Paragraph(self._fmt_date(self.invoice.due_date), ParagraphStyle(
                'DueValue',
                parent=due_style,
                alignment=2,
                fontSize=11,
            )),
        ]], colWidths=[40 * mm, 32 * mm])
        due_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff5e9')),
            ('LINEABOVE', (0, 0), (-1, -1), 0.5, colors.HexColor(primary_color)),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        eft_section = Table([[eft_box], [due_box]], colWidths=[72 * mm])
        eft_section.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

        summary_label_style = ParagraphStyle(
            'SumLabel',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            alignment=1,
        )
        summary_value_style = ParagraphStyle(
            'SumValue',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            alignment=1,
        )

        summary_grid = Table([
            [Paragraph('Subtotal:', summary_label_style), Paragraph(f'${self.invoice.subtotal or 0:.2f}', summary_value_style)],
            [Paragraph(gst_label, summary_label_style), Paragraph(f'${self.invoice.gst_amount or 0:.2f}', summary_value_style)],
            [Paragraph('Total:', summary_label_style), Paragraph(f'${self.invoice.total_amount or 0:.2f}', summary_value_style)],
            [Paragraph(gst_suffix, summary_label_style), Paragraph('&nbsp;', summary_value_style)],
            [Paragraph('Credit Note:', summary_label_style), Paragraph(f'${self.invoice.credit_note_amount or 0:.2f}', summary_value_style)],
            [Paragraph('Advance:', summary_label_style), Paragraph(f'${self.invoice.amount_paid or 0:.2f}', summary_value_style)],
            [Paragraph('Balance:', summary_label_style), Paragraph(f'${balance:.2f}', summary_value_style)],
        ], colWidths=[43 * mm, 48 * mm], rowHeights=[8 * mm] * 7)
        summary_grid.setStyle(TableStyle([
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#cfcfcf')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LINEBEFORE', (1, 0), (1, -1), 1.5, colors.black),
        ]))

        wrapper = Table([[
            eft_section,
            summary_grid,
        ]], colWidths=[72 * mm, 91 * mm])
        wrapper.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        return wrapper

    def _build_footer_note(self):
        style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=10,
            alignment=1,
            textTransform='uppercase',
        )
        return Paragraph('THANK YOU FOR YOUR BUSINESS!', style)

    def _build_notes_block(self):
        style = ParagraphStyle(
            'Notes',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            borderPadding=6,
            borderColor=colors.HexColor('#d8d8d8'),
            borderWidth=0.5,
            borderTop=1,
        )
        return Paragraph(f'<b>Notes:</b> {self._escape(self.invoice.notes)}', style)

    def _table_header_style(self):
        return ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            alignment=1,
        )

    def _table_cell_style(self, left=False):
        return ParagraphStyle(
            'TableCellLeft' if left else 'TableCell',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            alignment=0 if left else 1,
        )

    def _fmt_date(self, value):
        return value.strftime('%d/%b/%y') if value else 'N/A'

    def _escape(self, value):
        return (
            str(value or '')
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
        )
