# Quote Email System - Implementation Guide

## Overview
Your quote email system has been fully enhanced with:
- **Professional PDF Attachments** - Beautiful, branded PDF quotes with all details
- **Attractive HTML Emails** - Modern, responsive email templates with inline styling
- **Accept/Reject Functionality** - Customers can instantly accept or reject quotes directly from email
- **Admin Notifications** - Automatic emails to admin when quotes are accepted/rejected

## Features Implemented

### 1. PDF Quote Generator (`app/services/pdf_generator.py`)
Generates professional PDF documents with:
- Business branding and contact information
- Quote number, date, and expiry date
- Customer information
- Itemized list with quantities and pricing
- Subtotal, GST (10%), and Total calculations
- Terms and conditions section
- Additional notes
- Professional formatting with colors and styling

**Usage:**
```python
from app.services.pdf_generator import QuotePDFGenerator

pdf_generator = QuotePDFGenerator(quote, business_name="Western IT Solutions")
pdf_buffer = pdf_generator.generate()  # Returns BytesIO object
```

### 2. HTML Email Template (`app/services/email_templates.py`)
Creates visually appealing HTML emails with:
- Responsive design that works on all devices
- Blue gradient header with quote number
- Quote summary with dates and ID
- Professional line items table
- Clear financial breakdown (Subtotal, GST, Total)
- **Prominent Accept/Reject buttons** with hover effects
- Terms and conditions display
- Additional notes section
- Professional footer with confidentiality notice

**Usage:**
```python
from app.services.email_templates import QuoteEmailTemplate

html_body = QuoteEmailTemplate.generate_quote_email(
    quote,
    accept_url="https://example.com/quote/1/accept",
    reject_url="https://example.com/quote/1/reject",
    business_name="Western IT Solutions"
)
```

### 3. Enhanced Email Service (`app/services/mailer.py`)
Updated to support:
- Multiple attachments
- MIME multipart messages for better email client compatibility
- Both text and HTML email bodies
- Base64 encoding for binary attachments (PDFs)

**Usage:**
```python
from app.services.mailer import send_email

attachments = [("quote.pdf", pdf_buffer)]
send_email(
    recipient="customer@example.com",
    subject="Your Quote",
    text_body="Plain text version",
    html_body="<html>...</html>",
    attachments=attachments
)
```

### 4. Quote Acceptance Endpoint
**Route:** `/quote/<quote_id>/accept` (GET or POST)

**Features:**
- No login required - customers can access directly from email
- Validates quote hasn't expired
- Updates quote status to 'ACCEPTED'
- Sends admin notification email
- Returns success message

**Response:**
```json
{
    "success": true,
    "message": "Thank you! Your quote has been accepted. We will be in touch shortly.",
    "quote_number": "QT-20240407-ABC12345"
}
```

### 5. Quote Rejection Endpoint
**Route:** `/quote/<quote_id>/reject` (GET or POST)

**Features:**
- No login required - customers can access directly from email
- Updates quote status to 'REJECTED'
- Sends admin notification email
- Returns success message

**Response:**
```json
{
    "success": true,
    "message": "Thank you for your response. We appreciate your consideration.",
    "quote_number": "QT-20240407-ABC12345"
}
```

## How It Works - Step by Step

### 1. Admin Creates & Sends Quote
- Admin creates quote in the admin panel
- Admin clicks "Email Quote" button
- System automatically:
  1. Generates professional PDF with all quote details
  2. Creates attractive HTML email with Accept/Reject buttons
  3. Generates secure URLs for the customer (no login needed)
  4. Sends email with PDF attachment to customer
  5. Updates quote status to 'SENT'

### 2. Customer Receives Email
Customer receives email with:
- Professional HTML formatting
- Complete quote summary
- Itemized breakdown with pricing
- **Green "Accept Quote" button**
- **Red "Reject Quote" button**
- PDF attachment for printing/reference

### 3. Customer Accepts Quote
- Clicks "Accept Quote" button in email
- Takes them to `/quote/<id>/accept`
- Quote status updates to 'ACCEPTED'
- Admin receives notification email about acceptance
- Customer sees confirmation message

### 4. Customer Rejects Quote (or accepts differently)
- Clicks "Reject Quote" button
- Takes them to `/quote/<id>/reject`
- Quote status updates to 'REJECTED'
- Admin receives notification email about rejection
- Customer sees thank you message

## Email Templates

### Customer Quote Email
- Header with quote number and company name
- Customer greeting with personalized name
- Quote summary section
- Itemized quote table
- Total calculations (Subtotal, GST, Total)
- Expiry warning
- Call-to-action buttons
- Terms and conditions (if any)
- Additional notes (if any)
- Professional footer

### Admin Notification Emails

#### Acceptance Notification
```
Subject: Quote {number} - ACCEPTED by {customer_name}
Content:
- Customer name and email
- Quote total amount
- Timestamp of acceptance
- Prompt to create invoice
```

#### Rejection Notification
```
Subject: Quote {number} - REJECTED by {customer_name}
Content:
- Customer name and email
- Quote total amount
- Timestamp of rejection
- Prompt to follow up
```

## Files Modified/Created

### New Files:
1. **`app/services/pdf_generator.py`** - PDF generation with ReportLab
2. **`app/services/email_templates.py`** - HTML email template builder

### Modified Files:
1. **`requirements.txt`** - Added: reportlab, Pillow, gunicorn
2. **`app/services/mailer.py`** - Added attachment support
3. **`app/routes/admin.py`** - 
   - Updated imports
   - Updated `send_quote_email_message()` function
   - Added `/quote/<id>/accept` endpoint
   - Added `/quote/<id>/reject` endpoint

## Installation

### 1. Install New Dependencies
```bash
pip install -r requirements.txt
```

### 2. Verify Configuration
Ensure your `config.py` has these email settings:
```python
MAIL_ENABLED = True
MAIL_HOST = 'your.mail.server'
MAIL_PORT = 587  # or 465 for SSL
MAIL_USERNAME = 'your-email@company.com'
MAIL_PASSWORD = 'your-password'
MAIL_DEFAULT_SENDER = 'noreply@company.com'
```

### 3. Base URL Configuration
Update `APP_BASE_URL` in config for correct links in emails:
```python
APP_BASE_URL = 'https://westernitsolutions.com.au/Application'
```

## Testing

### 1. Test Quote Email
```bash
# Log in to admin panel
# Create or open a quote
# Click "Email Quote" button
# Check customer inbox for email
```

### 2. Verify PDF Attachment
- Check email for PDF attachment
- Open PDF to verify formatting
- Check that all quote details are present

### 3. Test Accept/Reject
- Open email in email client
- Click "Accept Quote" button
- Should see success message (or integrate with your frontend)
- Check admin email for notification
- Check admin panel - quote status should be 'ACCEPTED'
- Repeat for "Reject Quote"

### 4. Check Quote Status Updates
```bash
# In admin panel, view quote
# Verify status changed from DRAFT -> SENT -> ACCEPTED/REJECTED
```

## Customization Options

### Change Colors in PDF
Edit `app/services/pdf_generator.py`:
```python
colors.HexColor('#1a5490')  # Change this hex code
```

### Change Business Name
Pass as parameter:
```python
pdf_generator = QuotePDFGenerator(
    quote, 
    business_name="Your Company Name"
)
```

### Add Logo to PDF
Edit `app/services/pdf_generator.py` to include image in header:
```python
from reportlab.platypus import Image
# Add image to header section
```

### Customize Email Look
Edit `app/services/email_templates.py` - modify CSS styles in the HTML template

## Database

The `Quote` model was already tracking status with these options:
- `DRAFT` - Quote created but not sent
- `SENT` - Quote emailed to customer
- `ACCEPTED` - Customer accepted the quote
- `REJECTED` - Customer rejected the quote
- `EXPIRED` - Quote expiry date has passed

## Security Notes

✓ Accept/Reject endpoints don't require login (by design - customers access from email)
✓ Quote ID from URL is checked against database
✓ Expiry validation prevents accepting expired quotes
✓ Admin gets notified of all actions
✓ Quote status is immutable once set

## Next Steps

1. **Send test quote emails** - Verify everything looks good
2. **Test PDF rendering** - Confirm PDF displays correctly
3. **Test Accept/Reject** - Ensure workflow is smooth
4. **Add custom logo** - Optional: Integrate company logo in PDF
5. **Customize colors/branding** - Adjust colors to match your brand
6. **Create invoice from accepted quote** - Optional: Auto-create invoice when accepted

## Support

If PDF isn't generating:
- Check if reportlab and Pillow are installed: `pip install reportlab Pillow`
- Check temp directory has write permissions
- Check quote has line items

If emails don't arrive:
- Verify email configuration in config.py
- Check spam/junk folder
- Review server logs for SMTP errors

## Future Enhancements

Potential improvements:
- Add QR code linking to quote in PDF
- Include company logo in email header
- Add tracking: when customer opens email
- Add payment methods/links in email
- Auto-create invoice for accepted quotes
- Add company signature/contact info to email footer
