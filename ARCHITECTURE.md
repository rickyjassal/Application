# Architecture Overview - Business Management System

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Web Browser User                        │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
      ┌──────────────────────────────────────┐
      │    westernitsolutions.com.au/         │
      │        Application                    │
      │    (Web Interface + API)              │
      └──────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌────────────┐ ┌─────────┐ ┌──────────┐
    │  Flask     │ │SQLAlchemy
    │  Framework │ │ORM      │ │Database  │
    │            │ │         │ │(SQLite/  │
    │  Routes:   │ │Models:  │ │MySQL)    │
    │  - API     │ │- Product │         │
    │  - Views   │ │- Service │         │
    │  - Docs    │ │- Customer         │
    │            │ │- Invoice │         │
    │            │ │- Payment │         │
    └────────────┘ └─────────┘ └──────────┘
```

## Technology Stack

### Backend
- **Framework**: Flask 2.3 (Python 3.6+)
- **Database ORM**: SQLAlchemy
- **Database**: SQLite (default) / MySQL (production)
- **WSGI Server**: 
  - Development: Flask development server
  - Production (Bluehost): Passenger WSGI

### Frontend (Future)
- HTML5 / Bootstrap (Static files included)
- JavaScript/AJAX for dynamic updates

### Deployment
- **Hosting**: Bluehost (shared hosting)
- **Domain**: westernitsolutions.com.au/Application
- **SSL**: AutoSSL (included with Bluehost)

## Data Flow

### Creating an Invoice

```
User Input (Web Form) 
    ↓
POST /api/invoices (Flask Route)
    ↓
InvoiceLineItem Model (ORM)
    ↓
Product Model (Update Inventory)
    ↓
InventoryTransaction Model (Track change)
    ↓
SQLite/MySQL Database
    ↓
JSON Response to Frontend
    ↓
Invoice Display
```

### Generating Sales Report

```
GET /api/reports/sales
    ↓
Query Invoices from Database (filtered by date)
    ↓
Calculate Totals & Grouping
    ↓
Return JSON Report
    ↓
Frontend renders Report
```

## Database Schema

### Core Tables

**products**
- Product inventory items
- Tracks stock levels, pricing

**services**
- Service offerings
- IT Repair, Mobile Repair, Laptop Repair, Website Design

**customers**
- Customer details (individuals and businesses)
- Supports ABN, ACN for Australian businesses
- GST registration tracking

**quotes**
- Quotes sent to customers
- Can be converted to invoices
- Status tracking, expiry dates

**invoices**
- Financial transactions
- GST calculation
- Payment tracking

**invoice_line_items**
- Individual items on invoice
- Links to product or service

**payments**
- Payment records
- Multiple payment modes support

**discount_codes**
- Pre-defined discount codes
- Validates before application
- Usage tracking

**inventory_transactions**
- Record of all inventory changes
- Sales, purchases, returns, adjustments

## Key Features

### Financial Management
- GST Compliance (10% Australian standard)
- Multiple payment modes (Cash, Account, Cheque, Bank Transfer, Credit Card)
- Discount code application
- Profit/revenue tracking

### Inventory Control
- Stock level tracking
- Low stock alerts
- Inventory transactions logging
- Cost vs selling price tracking

### Customer Relations
- Customer database
- Quote to invoice conversion
- Payment history
- Account balance tracking

### Reporting
- Sales reports by period
- Cost/purchase reports
- Profit analysis
- Customer activity tracking

## API Structure

All APIs follow RESTful principles:

```
GET    /api/products              - List all
POST   /api/products              - Create
GET    /api/products/<id>         - Get one
PUT    /api/products/<id>         - Update
DELETE /api/products/<id>         - Delete
```

Same pattern for: services, customers, invoices, quotes, discounts, payments

Special endpoints:
- `/api/reports/*` - Business analytics
- `/api/invoices/<id>/pay` - Record payment
- `/api/quotes/<id>/send` - Send quote

## Security Considerations

### Current Implementation
- SECRET_KEY for session security
- Database-level constraints
- Input validation through ORM

### Production Recommendations
- Use HTTPS (Bluehost AutoSSL)
- Change SECRET_KEY in production
- Add authentication/authorization
- Implement request rate limiting
- Add audit logging
- Validate all user inputs
- Use prepared statements (SQLAlchemy does this)
- Regular security updates

## Scalability Path

### As you grow:

1. **Small Scale** (Current - SQLite):
   - Single server setup
   - File-based database
   - Good for <100 daily users

2. **Medium Scale** (SQLite → MySQL):
   - Upgrade to Bluehost MySQL
   - Better performance
   - Good for <1000 daily users

3. **Large Scale** (Professional Hosting):
   - Dedicated server / VPS
   - Real application server (Gunicorn/uWSGI)
   - PostgreSQL database
   - Redis caching
   - Load balancer
   - Separate database server

## Deployment on Bluehost

### No Docker Needed!

Bluehost uses **Passenger WSGI** which:
- Is built into shared hosting
- Automatically starts/stops your application
- Manages Python virtual environment
- No Docker containers required
- Simpler setup and management
- Direct file system access

### Bluehost File Structure

```
/home/username/
├── public_html/
│   └── Application/          ← Your app directory
│       ├── app/
│       ├── venv/             ← Virtual environment
│       ├── business_management.db
│       ├── passenger_wsgi.py ← Entry point
│       ├── .env              ← Configuration
│       └── ...
```

### Why SQLite for Bluehost?

- No separate database server needed
- Simpler deployment
- Automatic backups (just copy file)
- Good for business application with ~100-500 invoices/month
- Can upgrade to MySQL later if needed

## File Organization

```
Model Layer (ORM)
    ↓ (SQLAlchemy)
Database Layer (SQLite/MySQL)
    ↓
API Routes (Flask Blueprint)
    ↓
JSON Response
    ↓
Frontend (HTML/JS)
```

## Configuration Management

```
config.py (Base settings)
    ├── DevelopmentConfig
    │   └── SQLite + Debug
    ├── ProductionConfig
    │   └── MySQL + No Debug (for Bluehost)
    └── TestingConfig
        └── In-memory Database
```

## Monitoring & Maintenance

### Regular Tasks
- Database backups (weekly)
- Log review (monthly)
- Usage monitoring (monthly)
- Software updates (as needed)

### Key Metrics to Watch
- Database file size
- Disk space availability
- Number of invoices/month
- Peak traffic times

## Migration Path

From Development to Bluehost:

1. Test locally ✓
2. Upload files to Bluehost
3. Set up venv & dependencies
4. Configure Passenger
5. Initialize database
6. Test endpoints
7. Go live!

## Support & Documentation

- **API Docs**: See README.md
- **Deployment**: See BLUEHOST_DEPLOYMENT.md
- **Setup**: See SETUP.md
- **Code Comments**: Throughout source files
