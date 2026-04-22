# Quick Reference - Business Management System

## What Has Been Created

### Core Application Components

✅ **Database Models** (app/models/)
- Product - Inventory management with stock tracking
- Service - Service offerings (IT, Mobile, Laptop, Website Design)
- Customer - Individual and business customers with ABN/ACN support
- Invoice & InvoiceLineItem - Financial transactions with GST
- Quote & QuoteLineItem - Quote management with conversion to invoice
- Payment - Payment recording with multiple modes
- DiscountCode - Discount code management with validation
- InventoryTransaction - Inventory change logging

✅ **API Routes** (app/routes/)
- Dashboard - Statistics and overview
- Products - CRUD operations and low-stock tracking
- Services - CRUD operations by service type
- Customers - CRUD operations with customer type support
- Invoices - Full invoice lifecycle management
- Quotes - Quote creation, tracking, and conversion
- Discounts - Discount code management and validation
- Payments - Payment recording
- Reports - Sales, purchases, profit, inventory, customer activity

✅ **Configuration**
- config.py - Environment-specific settings (Development, Production, Testing)
- .env.example - Environment variables template
- requirements.txt - Python dependencies

✅ **Deployment Files**
- wsgi.py - WSGI entry point for production
- passenger_wsgi.py - Bluehost-specific WSGI configuration
- .htaccess - Apache/Bluehost web server configuration
- Passenger configuration via cPanel (manual setup)

✅ **Documentation**
- README.md - Complete project overview and API documentation
- BLUEHOST_DEPLOYMENT.md - Step-by-step Bluehost deployment guide
- SETUP.md - Local development and testing guide
- ARCHITECTURE.md - System design and architecture overview
- This file - Quick reference

## Quick Start Commands

### Local Development

```bash
# 1. Setup virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize database
python -c "from app import create_app, db; app = create_app(); db.create_all()"

# 4. Run application
python run.py

# 5. Access at http://localhost:5000
```

### Bluehost Deployment

```bash
# 1. SSH to server
ssh username@domain.com.au
cd ~/public_html/Application

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env from template
cp .env.example .env
# Edit: nano .env (set FLASK_ENV=production)

# 5. Initialize database
python3 << 'EOF'
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
EOF

# 6. Setup Passenger in cPanel
# - Setup Python App
# - Path: /home/username/public_html/Application
# - Startup file: passenger_wsgi.py

# 7. Set permissions
chmod 755 .
chmod 777 business_management.db
chmod 777 venv/lib/python*/site-packages

# 8. Restart Passenger
touch tmp/restart.txt

# 9. Visit: https://westernitsolutions.com.au/Application
```

## Key Features Available

### Inventory & Products
- [x] Add/Edit/Delete products
- [x] Track stock levels
- [x] Low stock alerts
- [x] Cost price vs selling price
- [x] Profit margin calculation
- [x] Inventory transaction logging

### Services
- [x] Define services (IT, Mobile, Laptop, Website Design)
- [x] Set base prices and hourly rates
- [x] Manage service activation

### Customers
- [x] Add individual and business customers
- [x] Support Australian ABN/ACN
- [x] Track addresses
- [x] GST registration status
- [x] Account balance for credit sales

### Quotes & Invoices
- [x] Create professional quotes
- [x] Set expiry dates
- [x] Convert quotes to invoices
- [x] Add products and services
- [x] Auto GST calculation (10%)
- [x] Automatic inventory updates on sale

### Discounts
- [x] Pre-defined discount codes
- [x] Percentage or fixed amount
- [x] Time-based validity
- [x] Usage limits
- [x] Minimum order values
- [x] Validation before application

### Payments
- [x] Record payments
- [x] Multiple payment modes (Cash, Account, Cheque, Bank Transfer, Credit Card)
- [x] Partial payment support
- [x] Payment references and notes

### Reports
- [x] Sales report by date range
- [x] Purchase/cost report
- [x] Profit analysis
- [x] Inventory status
- [x] Customer activity report

### Financial
- [x] GST calculation (10% Australian standard)
- [x] Invoice totals including GST
- [x] Discount application before GST
- [x] Payment tracking
- [x] Balance due calculation

## API Endpoint Summary

### Inventory
```
GET/POST   /api/products
GET/PUT/DELETE /api/products/<id>
GET        /api/products/low-stock
```

### Services
```
GET/POST   /api/services
GET/PUT/DELETE /api/services/<id>
GET        /api/services/types
```

### Customers
```
GET/POST   /api/customers
GET/PUT/DELETE /api/customers/<id>
GET        /api/customers/types
```

### Quotes
```
GET/POST   /api/quotes
GET/PUT/DELETE /api/quotes/<id>
POST       /api/quotes/<id>/items
DELETE     /api/quotes/items/<id>
POST       /api/quotes/<id>/send
GET        /api/quotes/statuses
```

### Invoices
```
GET/POST   /api/invoices
GET/PUT/DELETE /api/invoices/<id>
POST       /api/invoices/<id>/issue
POST       /api/invoices/<id>/pay
POST       /api/invoices/<id>/from-quote/<quote_id>
GET        /api/invoices/statuses
GET        /api/invoices/payment-modes
```

### Discounts
```
GET/POST   /api/discounts
GET/PUT/DELETE /api/discounts/<id>
POST       /api/discounts/validate/<code>
GET        /api/discounts/types
```

### Reports
```
GET /api/reports/sales
GET /api/reports/purchases
GET /api/reports/profit
GET /api/reports/inventory
GET /api/reports/customer-activity
```

## Database Models Overview

### Product
- name, sku, category
- cost_price, selling_price
- quantity_in_stock, reorder_level
- is_active

### Service
- name, service_type (enum)
- description
- base_price, hourly_rate
- is_active

### Customer
- name, customer_type (INDIVIDUAL/BUSINESS/CASH)
- email, phone
- business_name, abn, acn (for business)
- street_address, suburb, state, postcode
- account_balance, is_active, is_gst_registered

### Invoice
- invoice_number (unique)
- customer_id, quote_id (optional)
- status (DRAFT/ISSUED/PAID/PARTIAL/OVERDUE/CANCELLED)
- invoice_date, due_date
- subtotal, gst_amount, discount_amount, total_amount
- amount_paid, payment_mode

### Quote
- quote_number (unique)
- customer_id
- status (DRAFT/SENT/ACCEPTED/REJECTED/EXPIRED)
- quote_date, expiry_date
- notes, terms_and_conditions

### Payment
- invoice_id, customer_id
- amount, payment_mode
- status (PENDING/COMPLETED/FAILED/REFUNDED)
- payment_date, payment_reference

### DiscountCode
- code (unique)
- discount_type (PERCENTAGE/FIXED_AMOUNT)
- discount_value
- valid_from, valid_until
- max_uses, current_uses
- minimum_order_value, maximum_discount_amount

### InventoryTransaction
- product_id
- transaction_type (PURCHASE/SALE/RETURN/ADJUSTMENT/DAMAGE)
- quantity, reference_id, notes
- transaction_date

## Important Configuration

### Production Settings (Bluehost)
```
FLASK_ENV=production
SECRET_KEY=<generate-random-secure-key>
DATABASE_URL=sqlite:///business_management.db
# Or: mysql+pymysql://user:password@host/dbname
```

### GST Configuration
- Hardcoded to 10% (Australian standard)
- Location: config.py → Config.GST_RATE
- Applied to all invoices automatically

### Database
- Default: SQLite (file-based, no setup needed)
- Optional: MySQL (better for high volume)
- Stored as: business_management.db

## Troubleshooting

### "502 Bad Gateway" on Bluehost
1. Check error logs: `tail -f ~/public_html/Application/tmp/error.log`
2. Verify dependencies: `pip install -r requirements.txt`
3. Restart Passenger: `touch tmp/restart.txt`

### Database Permission Error
```bash
chmod 666 business_management.db
chmod 755 .
```

### Module Not Found
Ensure virtual environment is active and requirements installed.

### Port 5000 Already in Use (Local)
```bash
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

## Bluehost Directory Structure

```
/home/username/
├── public_html/
│   └── Application/
│       ├── app/ ......................... Application code
│       ├── migrations/ .................. Database migrations
│       ├── venv/ ........................ Virtual environment
│       ├── business_management.db ....... SQLite database
│       ├── run.py ....................... Development entry
│       ├── wsgi.py ...................... Production WSGI
│       ├── passenger_wsgi.py ............ Bluehost WSGI
│       ├── config.py .................... Configuration
│       ├── .env ......................... Environment vars
│       ├── .env.example ................. Template
│       ├── .htaccess .................... Web server config
│       ├── requirements.txt ............. Dependencies
│       ├── README.md .................... Docs
│       ├── BLUEHOST_DEPLOYMENT.md ....... Deployment guide
│       ├── SETUP.md ..................... Setup guide
│       └── ARCHITECTURE.md .............. Architecture docs
```

## Why No Docker?

Bluehost shared hosting:
- ✅ Doesn't support Docker
- ✅ Passenger WSGI = simpler deployment
- ✅ Direct file system access
- ✅ Automatic app management
- ✅ No additional setup needed

Traditional Docker flow (not Bluehost):
```
Build > Push Registry > Pull > Run Container
```

Bluehost flow (current setup):
```
Upload Files > Configure Passenger > Done!
```

## Next Steps After Deployment

1. **Test Core Functions**
   - Add a customer
   - Add a product
   - Create a quote
   - Convert to invoice
   - Record payment

2. **Generate Reports**
   - Sales report
   - Profit analysis
   - Inventory status

3. **Setup Backups**
   - Daily backups via cPanel

4. **Monitor**
   - Check error logs weekly
   - Monitor database size
   - Review reports

5. **Frontend Development** (Future)
   - HTML UI templates
   - JavaScript for dynamic features
   - Dashboard visualization

## Support Resources

- Flask Docs: https://flask.palletsprojects.com/
- SQLAlchemy Docs: https://sqlalchemy.org/
- Bluehost Support: https://www.bluehost.com/support
- Python Docs: https://docs.python.org/3/

## Contact & Maintenance

This application is created for: **Western IT Solutions**
Domain: **www.westernitsolutions.com.au**
App Path: **/Application**

For technical support:
- Review error logs
- Check documentation in repository
- Contact development team

---

**Version**: 1.0.0
**Created**: 2026
**Framework**: Flask 2.3 + SQLAlchemy
**Database**: SQLite (Default) / MySQL (Optional)
**Deployment**: Bluehost Passenger WSGI
