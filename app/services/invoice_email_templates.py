"""Email template builder for invoices"""

import base64
from datetime import datetime
from pathlib import Path


class InvoiceEmailTemplate:
    """Build attractive HTML email templates for invoices"""

    @staticmethod
    def _get_logo_data_uri():
        """Convert logo image to base64 data URI for embedding in email"""
        return InvoiceEmailTemplate._get_logo_data_uri_for_path('images/Logo.png')

    @staticmethod
    def _get_logo_data_uri_for_path(relative_path):
        """Convert a branding logo image to base64 data URI for embedding in email"""
        try:
            logo_path = Path(__file__).parent.parent / 'static' / relative_path
            if logo_path.exists():
                with open(logo_path, 'rb') as f:
                    logo_data = base64.b64encode(f.read()).decode('utf-8')
                return f'data:image/png;base64,{logo_data}'
        except Exception as e:
            print(f"Error loading logo: {e}")
        return None

    @staticmethod
    def generate_invoice_email(invoice, business_name="Western IT Solutions", logo_url=None):
        """
        Generate attractive HTML email for invoice
        
        Args:
            invoice: Invoice object
            business_name: Company name
            logo_url: Optional logo URL
        
        Returns:
            HTML string
        """
        customer = invoice.customer
        branding = invoice.get_branding()
        primary_color = branding.get('brand_primary_color', '#dc3545')
        secondary_color = branding.get('brand_secondary_color', '#c82333')
        subtotal = invoice.subtotal or 0
        gst = invoice.gst_amount or 0
        discount = invoice.discount_amount or 0
        total = invoice.total_amount or 0
        paid = invoice.amount_paid or 0
        credit_note = invoice.credit_note_amount or 0
        balance = invoice.get_balance_due()
        
        # Build line items HTML
        line_items_html = ""
        for item in invoice.line_items:
            line_items_html += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 12px; font-size: 14px; color: #333;">{item.description or ''}</td>
                <td style="padding: 12px; text-align: center; font-size: 14px; color: #333;">{item.quantity}</td>
                <td style="padding: 12px; text-align: right; font-size: 14px; color: #333;">${item.unit_price:.2f}</td>
                <td style="padding: 12px; text-align: right; font-size: 14px; color: #333; font-weight: bold;">${item.get_line_total():.2f}</td>
            </tr>
            """
        
        # Terms and conditions section (if exists)
        terms_section = ""
        if invoice.terms_and_conditions:
            terms_section = f"""
            <div style="margin-top: 30px; padding: 15px; background-color: #ffe0e0; border-left: 4px solid {primary_color};">
                <h3 style="color: {primary_color}; margin-top: 0;">Terms and Conditions</h3>
                <p style="font-size: 13px; line-height: 1.6; color: #555; white-space: pre-wrap; margin: 0;">
                    {invoice.terms_and_conditions}
                </p>
            </div>
            """
        
        # Notes section (if exists)
        notes_section = ""
        if invoice.notes:
            notes_section = f"""
            <div style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107;">
                <h3 style="color: #856404; margin-top: 0;">Additional Notes</h3>
                <p style="font-size: 13px; line-height: 1.6; color: #855; white-space: pre-wrap; margin: 0;">
                    {invoice.notes}
                </p>
            </div>
            """
        
        # Payment status message
        payment_message = ""
        if balance > 0:
            payment_message = f"""
            <div style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107;">
                <h3 style="color: #856404; margin-top: 0;">Payment Due</h3>
                <p style="font-size: 14px; color: #855; margin: 0;">
                    <strong>Amount Outstanding: ${balance:.2f}</strong><br>
                    Due Date: <strong>{invoice.due_date.strftime('%d %B %Y') if invoice.due_date else 'Upon receipt'}</strong>
                </p>
            </div>
            """
        else:
            payment_message = """
            <div style="margin-top: 20px; padding: 15px; background-color: #d4edda; border-left: 4px solid #28a745;">
                <h3 style="color: #155724; margin-top: 0;">✓ Invoice Paid</h3>
                <p style="font-size: 14px; color: #155724; margin: 0;">
                    This invoice has been fully paid. Thank you!
                </p>
            </div>
            """
        
        # Get logo data URI for embedding in email
        logo_data_uri = InvoiceEmailTemplate._get_logo_data_uri_for_path(branding.get('brand_logo_path', 'images/Logo.png'))
        logo_html = ""
        if logo_data_uri:
            logo_html = f'<img src="{logo_data_uri}" alt="{business_name}" style="max-height: 60px; margin-bottom: 15px;">'
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 0;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .email-header {{
                    background: linear-gradient(135deg, {primary_color} 0%, {secondary_color} 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .email-header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 600;
                }}
                .logo {{  
                    text-align: center;
                    margin-bottom: 10px;
                }}
                .email-body {{
                    padding: 30px;
                }}
                .greeting {{
                    font-size: 16px;
                    color: #333;
                    margin-bottom: 20px;
                }}
                .invoice-details {{
                    background-color: #ffe0e0;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                    border-left: 4px solid {primary_color};
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 0;
                    font-size: 14px;
                    border-bottom: 1px solid #eee;
                }}
                .detail-row:last-child {{
                    border-bottom: none;
                }}
                .detail-label {{
                    font-weight: 600;
                    color: {primary_color};
                }}
                .detail-value {{
                    color: #666;
                }}
                .invoice-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                .invoice-table thead {{
                    background-color: {primary_color};
                    color: white;
                }}
                .invoice-table th {{
                    padding: 12px;
                    text-align: left;
                    font-weight: 600;
                    font-size: 14px;
                }}
                .invoice-table td {{
                    padding: 12px;
                    font-size: 14px;
                    color: #333;
                }}
                .invoice-table tbody tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .totals {{
                    text-align: right;
                    margin: 20px 0;
                    padding: 20px;
                    background-color: #ffe0e0;
                    border-radius: 5px;
                }}
                .total-row {{
                    display: flex;
                    justify-content: flex-end;
                    margin: 8px 0;
                    font-size: 14px;
                }}
                .total-row .label {{
                    font-weight: 600;
                    margin-right: 20px;
                    color: {primary_color};
                }}
                .total-row .value {{
                    min-width: 100px;
                    text-align: right;
                }}
                .total-row.final {{
                    font-size: 18px;
                    font-weight: bold;
                    color: {primary_color};
                    border-top: 2px solid {primary_color};
                    padding-top: 15px;
                    margin-top: 15px;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    color: #666;
                    font-size: 12px;
                    text-align: center;
                    padding: 20px;
                    border-top: 1px solid #eee;
                }}
                .footer-text {{
                    margin: 5px 0;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <div class="logo">{logo_html}</div>
                    <h1 style="margin-bottom: 5px;">Invoice #{invoice.invoice_number}</h1>
                    <p style="margin: 10px 0 0 0;">from {business_name}</p>
                </div>
                
                <div class="email-body">
                    <div class="greeting">
                        <p>Hello <strong>{customer.name}</strong>,</p>
                        <p>Please find your invoice details below. The complete invoice PDF attachment includes all details and payment instructions.</p>
                    </div>
                    
                    <div class="invoice-details">
                        <div class="detail-row">
                            <span class="detail-label">Invoice Date:</span>
                            <span class="detail-value">{invoice.invoice_date.strftime('%d %B %Y')}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Due Date:</span>
                            <span class="detail-value">{invoice.due_date.strftime('%d %B %Y') if invoice.due_date else 'Upon receipt'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Invoice ID:</span>
                            <span class="detail-value">{invoice.invoice_number}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Status:</span>
                            <span class="detail-value"><strong>{invoice.status}</strong></span>
                        </div>
                    </div>
                    
                    <h3 style="color: {primary_color}; margin-top: 25px;">Invoice Items</h3>
                    <table class="invoice-table">
                        <thead>
                            <tr>
                                <th>Description</th>
                                <th style="text-align: center; width: 80px;">Qty</th>
                                <th style="text-align: right; width: 120px;">Unit Price</th>
                                <th style="text-align: right; width: 120px;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {line_items_html}
                        </tbody>
                    </table>
                    
                    <div class="totals">
                        <div class="total-row">
                            <span class="label">Subtotal:</span>
                            <span class="value">${subtotal:.2f}</span>
                        </div>
                        {f'<div class="total-row"><span class="label">Discount:</span><span class="value">-${discount:.2f}</span></div>' if discount > 0 else ''}
                        <div class="total-row">
                            <span class="label">GST (10%):</span>
                            <span class="value">${gst:.2f}</span>
                        </div>
                        {f'<div class="total-row"><span class="label">Credit Note:</span><span class="value">${credit_note:.2f}</span></div>' if credit_note > 0 else ''}
                        <div class="total-row">
                            <span class="label">Amount Paid:</span>
                            <span class="value">${paid:.2f}</span>
                        </div>
                        <div class="total-row final">
                            <span class="label">BALANCE DUE:</span>
                            <span class="value">${balance:.2f}</span>
                        </div>
                    </div>
                    
                    {payment_message}
                    
                    <h3 style="color: #333; margin-top: 25px;">Payment Information</h3>
                    <p style="font-size: 14px; color: #555; line-height: 1.8;">
                        Please retain this invoice for your records. The complete invoice PDF with all details, terms, and payment instructions is attached to this email.
                    </p>
                    
                    {terms_section}
                    {notes_section}
                </div>
                
                <div class="footer">
                    <div class="footer-text">
                        <strong>{business_name}</strong>
                    </div>
                    <div class="footer-text">
                        Email: {customer.email or ''}
                    </div>
                    <div class="footer-text" style="margin-top: 10px; color: #999; border-top: 1px solid #ddd; padding-top: 10px; font-size: 11px;">
                        <strong>© All Rights Reserved {business_name}</strong><br><br>
                        This email and PDF attachment contain confidential information intended solely for the addressee. If you have received this email in error or were not expecting to receive this email, please contact us immediately and delete this email from your inbox. Unauthorized access, use, or dissemination of this information is strictly prohibited.
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
