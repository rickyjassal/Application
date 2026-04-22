# Project Setup and Development Guide

## Quick Start

### 1. Initial Setup

```bash
# Navigate to project
cd "Mobile Database Management Tool"

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. First Run

```bash
# Initialize the application
python

>>> from app import create_app, db
>>> app = create_app('development')
>>> with app.app_context():
>>>     db.create_all()
>>> exit()
```

### 3. Start Development Server

```bash
python run.py
```

Visit: `http://localhost:5000`

## Database Management

### Create Initial Tables

```bash
python -c "from app import create_app, db; app = create_app(); db.create_all()"
```

### Add Sample Data

```bash
python

from app import create_app, db
from app.models import Product, Service, Customer, DiscountCode
from datetime import datetime, timedelta

app = create_app('development')

with app.app_context():
    # Add sample product
    product = Product(
        name='iPhone Screen Repair',
        sku='REPAIR-001',
        category='Mobile Repair',
        cost_price=50.00,
        selling_price=150.00,
        quantity_in_stock=10,
        reorder_level=5
    )
    
    # Add sample service
    service = Service(
        name='Website Design',
        service_type='WEBSITE_DESIGN',
        base_price=500.00,
        hourly_rate=75.00
    )
    
    # Add sample customer
    customer = Customer(
        name='John Smith',
        customer_type='INDIVIDUAL',
        email='john@example.com',
        phone='0400123456',
        street_address='123 Main St',
        suburb='Sydney',
        state='NSW',
        postcode='2000',
        is_gst_registered=True
    )
    
    # Add sample discount
    discount = DiscountCode(
        code='WELCOME10',
        description='Welcome discount for new customers',
        discount_type='PERCENTAGE',
        discount_value=10,
        valid_from=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(days=30),
        max_uses=50,
        minimum_order_value=100
    )
    
    db.session.add_all([product, service, customer, discount])
    db.session.commit()
    
    print("Sample data added successfully!")
```

### Reset Database (Development Only!)

```bash
python

from app import create_app, db

app = create_app('development')

with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database reset!")
```

## API Testing

### Using cURL

```bash
# Get all products
curl http://localhost:5000/api/products

# Create a product
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "iPhone 13",
    "sku": "APPLE-001",
    "category": "Electronics",
    "cost_price": 800,
    "selling_price": 1200,
    "quantity_in_stock": 5
  }'

# Get customers
curl http://localhost:5000/api/customers

# Create invoice
curl -X POST http://localhost:5000/api/invoices \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "payment_mode": "CASH",
    "line_items": [
      {
        "product_id": 1,
        "description": "iPhone Screen Repair",
        "quantity": 1,
        "unit_price": 150
      }
    ]
  }'
```

### Using Postman

1. Import the API endpoints
2. Create requests for each endpoint
3. Test CRUD operations
4. Save requests for future use

### Using Python Requests

```python
import requests
import json

BASE_URL = 'http://localhost:5000/api'

# Create a product
product_data = {
    'name': 'MacBook Battery',
    'sku': 'APPLE-BATT-001',
    'category': 'Electronics',
    'cost_price': 30,
    'selling_price': 80,
    'quantity_in_stock': 20
}

response = requests.post(f'{BASE_URL}/products', json=product_data)
print(response.json())

# Get all products
response = requests.get(f'{BASE_URL}/products')
print(response.json())
```

## Development Workflow

### Creating New Tables/Models

1. **Create model file** in `app/models/`
2. **Import in** `app/models/__init__.py`
3. **Create database**: Python REPL or flask shell
4. **Update routes** if needed

### Creating New Routes

1. **Create blueprint** file in `app/routes/`
2. **Import in** `app/routes/__init__.py`
3. **Register in** `app/__init__.py` - `create_app()` function
4. **Test endpoints** using cURL/Postman

### Example: Adding a New Feature

Let's say you want to add "Supplier" management:

1. Create `app/models/supplier.py`:
```python
from app import db
from app.models import BaseModel

class Supplier(BaseModel):
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    # ... more fields
```

2. Import in `app/models/__init__.py`:
```python
from app.models.supplier import Supplier
```

3. Create `app/routes/suppliers.py` with CRUD operations

4. Import in `app/routes/__init__.py`:
```python
from .suppliers import suppliers_bp
```

5. Register in `app/__init__.py`:
```python
app.register_blueprint(suppliers_bp)
```

6. Initialize database with new model

## Configuration

### Development Config

- Debug: Enabled
- SQLite database
- SQL query logging enabled
- Detailed error pages

### Production Config (Bluehost)

- Debug: Disabled
- Can use SQLite or MySQL
- Minimal logging
- Production security settings

### Changing Config

Edit `.env` file:
```
FLASK_ENV=development  # or production
```

## Debugging

### Enable SQL Logging

In development, SQL queries are logged by default. View in console output.

### Use Flask Shell

```bash
python -m flask shell

# Now you have access to:
>>> from app import db
>>> from app.models import Product
>>> products = Product.query.all()
>>> print(products)
```

### Common Issues

1. **Import errors**: Ensure all BluePrints are registered
2. **Database not found**: Run `db.create_all()`
3. **Port in use**: Change port in `run.py`
4. **404 errors**: Check URL paths in routes

## Performance Tips

1. **Use pagination** for large datasets (built into routes)
2. **Add database indexes** for frequently queried fields
3. **Cache reports** if running frequently
4. **Monitor database size** for SQLite

## Production Checklist

Before deploying to Bluehost:

- [ ] Update SECRET_KEY in config
- [ ] Set FLASK_ENV=production
- [ ] Test all features
- [ ] Backup database
- [ ] Verify SSL certificate
- [ ] Set up error logging
- [ ] Configure database backups
- [ ] Test invoice generation
- [ ] Verify GST calculations
- [ ] Test payment recording
- [ ] Test report generation

## Useful Commands

```bash
# Run application
python run.py

# Access Flask shell
flask shell

# List all registered routes
flask routes

# Run tests (when added)
pytest

# Generate requirements from installed packages
pip freeze > requirements.txt

# Check code style
flake8 app/

# Format code
black app/
```

## File Structure Explanation

```
├── app/                          # Application package
│   ├── models/                   # Database models (ORM definitions)
│   ├── routes/                   # API endpoints and views
│   ├── templates/                # HTML templates (for future frontend)
│   ├── static/                   # CSS, JavaScript, images
│   │   ├── css/
│   │   └── js/
│   └── __init__.py              # Flask app factory
│
├── migrations/                   # Database migration scripts
├── config.py                    # Configuration settings
├── run.py                       # Development server entry point
├── wsgi.py                      # Production WSGI entry
├── passenger_wsgi.py            # Bluehost-specific WSGI
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
├── README.md                    # Project overview
├── BLUEHOST_DEPLOYMENT.md       # Deployment guide
└── SETUP.md                     # This file
```

## Next Steps

1. Complete Quick Start above
2. Explore API endpoints
3. Create test data
4. Test features locally
5. Review BLUEHOST_DEPLOYMENT.md when ready
6. Deploy to production

Happy coding!
