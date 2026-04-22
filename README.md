# Business Management System

A comprehensive Python Flask web application for managing inventory, services, customers, quotes, and invoices with GST support and profit tracking.

## Features

### Inventory Management
- Add and manage products with cost and selling prices
- Track inventory quantities and low stock alerts
- Create inventory transactions for sales, purchases, returns, and adjustments
- Calculate profit margins per product

### Services Management
- Define services: IT Repair, Mobile Repair, Laptop Repair, Website Design, Other
- Set base pricing and hourly rates
- Manage service availability

### Customer Management
- Add individual and business customers
- Support for Australian Business Numbers (ABN) and ACN
- Track customer addresses and contact information
- Manage GST registration status
- Maintain customer account balances for credit sales

### Quotes & Invoices
- Create professional quotes with expiry dates
- Convert quotes to invoices
- Add both products and services to quotes/invoices
- Automatic GST calculation (10% for Australia)
- Support for multiple line items

### Discount System
- Pre-defined discount codes (percentage or fixed amount)
- Time-based validity (valid from/until dates)
- Usage limits and maximum discount amounts
- Minimum order value requirements
- Automatic discount validation and application

### Payment Management
- Multiple payment modes: Cash, Account/Credit, Cheque, Bank Transfer, Credit Card
- Pay invoices fully or partially
- Record payment references
- Track payment status

### Reporting
- Sales report by period
- Purchase/cost report
- Profit analysis with margin calculation
- Inventory status report
- Customer activity and spending report

### GST Compliance
- 10% GST charge on all invoices (Australian standard)
- GST tracking and reporting
- GST-registered customer tracking

## Project Structure

```
├── app/
│   ├── models/              # Database models
│   │   ├── product.py      # Product inventory model
│   │   ├── service.py      # Service offerings
│   │   ├── customer.py     # Customer data
│   │   ├── invoice.py      # Invoices and line items
│   │   ├── quote.py        # Quotes and line items
│   │   ├── payment.py      # Payment records
│   │   ├── discount.py     # Discount codes
│   │   └── inventory.py    # Inventory transactions
│   ├── routes/              # API endpoints
│   │   ├── dashboard.py    # Dashboard stats
│   │   ├── products.py     # Product CRUD
│   │   ├── services.py     # Service CRUD
│   │   ├── customers.py    # Customer CRUD
│   │   ├── invoices.py     # Invoice management
│   │   ├── quotes.py       # Quote management
│   │   ├── payments.py     # Payment recording
│   │   ├── discounts.py    # Discount code management
│   │   └── reports.py      # Business reports
│   ├── templates/           # HTML templates (for future frontend)
│   ├── static/              # CSS, JS files
│   └── __init__.py         # App factory
├── migrations/              # Database migrations
├── config.py               # Configuration settings
├── run.py                  # Application entry point
├── wsgi.py                 # WSGI entry for production servers
├── passenger_wsgi.py       # Bluehost Passenger WSGI
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Installation

### Local Development

1. Clone the repository:
```bash
cd "Mobile Database Management Tool"
```

2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Mac/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

For newer local environments where you want to keep the original modern stack instead of the Bluehost Python 3.6 compatibility stack:
```bash
pip install -r requirements-modern.txt
```

4. Create .env file from template:
```bash
copy .env.example .env
```

5. Initialize the database:
```bash
python
>>> from app import create_app, db
>>> app = create_app('development')
>>> with app.app_context():
>>>     db.create_all()
>>> exit()
```

6. Run the application:
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## API Endpoints

### Dashboard
- `GET /` - Dashboard home
- `GET /api/stats` - Dashboard statistics

### Products
- `GET /api/products` - List all products
- `POST /api/products` - Create product
- `GET /api/products/<id>` - Get product
- `PUT /api/products/<id>` - Update product
- `DELETE /api/products/<id>` - Delete product
- `GET /api/products/low-stock` - Get low stock items

### Services
- `GET /api/services` - List all services
- `POST /api/services` - Create service
- `GET /api/services/<id>` - Get service
- `PUT /api/services/<id>` - Update service
- `DELETE /api/services/<id>` - Delete service
- `GET /api/services/types` - Get service types

### Customers
- `GET /api/customers` - List all customers
- `POST /api/customers` - Create customer
- `GET /api/customers/<id>` - Get customer
- `PUT /api/customers/<id>` - Update customer
- `DELETE /api/customers/<id>` - Delete customer
- `GET /api/customers/types` - Get customer types

### Quotes
- `GET /api/quotes` - List all quotes
- `POST /api/quotes` - Create quote
- `GET /api/quotes/<id>` - Get quote
- `PUT /api/quotes/<id>` - Update quote
- `DELETE /api/quotes/<id>` - Delete quote
- `POST /api/quotes/<id>/items` - Add item to quote
- `DELETE /api/quotes/items/<id>` - Remove item from quote
- `POST /api/quotes/<id>/send` - Send quote
- `GET /api/quotes/statuses` - Get quote statuses

### Invoices
- `GET /api/invoices` - List all invoices
- `POST /api/invoices` - Create invoice
- `GET /api/invoices/<id>` - Get invoice
- `PUT /api/invoices/<id>` - Update invoice
- `DELETE /api/invoices/<id>` - Delete invoice
- `POST /api/invoices/<id>/issue` - Issue invoice
- `POST /api/invoices/<id>/pay` - Record payment
- `POST /api/invoices/<id>/from-quote/<quote_id>` - Create from quote

### Discounts
- `GET /api/discounts` - List discount codes
- `POST /api/discounts` - Create discount code
- `GET /api/discounts/<id>` - Get discount
- `PUT /api/discounts/<id>` - Update discount
- `DELETE /api/discounts/<id>` - Delete discount
- `POST /api/discounts/validate/<code>` - Validate discount code

### Payments
- `GET /api/payments` - List all payments
- `GET /api/payments/<id>` - Get payment

### Reports
- `GET /api/reports/sales` - Sales report (with date range)
- `GET /api/reports/purchases` - Purchase/cost report
- `GET /api/reports/profit` - Profit analysis
- `GET /api/reports/inventory` - Inventory status
- `GET /api/reports/customer-activity` - Customer activity

## Deployment to Bluehost

### Important Notes
- **No Docker required** on Bluehost shared hosting
- Bluehost uses Passenger WSGI to run Python applications
- We use SQLite by default (file-based database) for easier setup
- For high-traffic scenarios, use Bluehost's MySQL database

### Deployment Steps

See [BLUEHOST_DEPLOYMENT.md](BLUEHOST_DEPLOYMENT.md) for complete Bluehost deployment guide.

## Database

### Default: SQLite (Development)
- File-based database stored as `business_management.db`
- Perfect for single-server deployments
- No external database setup needed

### Optional: MySQL (Bluehost Production)
- Create MySQL database via Bluehost cPanel
- Update `DATABASE_URL` in `.env`
- Requires PyMySQL package (included in requirements.txt)

## Configuration

All configuration is in `config.py`. Environment-specific settings:

- **Development**: SQLite, Debug enabled, SQL logging enabled
- **Production**: MySQL, Debug disabled, Minimal logging
- **Testing**: In-memory SQLite for fast tests

## Environment Variables

Create a `.env` file based on `.env.example`:

```
FLASK_ENV=production
DATABASE_URL=mysql+pymysql://user:password@host/dbname
SECRET_KEY=your-production-secret-key
```

## GST Configuration

GST rate is set to 10% (Australian standard). To change:
- Edit `config.py` and set `GST_RATE` in the Config class
- Applied automatically to all invoice calculations
- Tracked separately in invoice records

## Common Tasks

### Backup Database
```bash
# Copy the database file
cp business_management.db business_management.db.backup
```

### Reset Database (Development Only!)
```bash
python
>>> from app import create_app, db
>>> app = create_app('development')
>>> with app.app_context():
>>>     db.drop_all()
>>>     db.create_all()
>>> exit()
```

### Add Sample Data
See the Flask shell context for available models. Tools will be added in future updates.

## Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:5000 | xargs kill -9
```

### Database Connection Error
- Ensure `.env` has correct `DATABASE_URL`
- Check MySQL credentials on Bluehost
- Verify database exists and user has permissions

### Import Errors
- Ensure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`
- Check Python version (3.7+)

## License

This project is created for Western IT Solutions.

## Support

For issues or feature requests, contact the development team.
