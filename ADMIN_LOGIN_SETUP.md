# 🔐 Admin Login System - Setup Guide

## Features

✅ Secure admin login authentication  
✅ Username: `jassal` | Password: `Western@3029`  
✅ GUI-based data entry forms  
✅ Manage products, customers, services, quotes, and invoices  
✅ Professional dashboard with statistics  
✅ Session-based authentication  

---

## Login Instructions

### 1. Start the Flask Server
```powershell
cd "c:\Users\parmi\Documents\Project\Mobile Database Management Tool"
python run.py
```

### 2. Open Login Page
Go to: `http://localhost:5001/login`

### 3. Enter Credentials
- **Username:** `jassal`
- **Password:** `Western@3029`

### 4. Access Admin Dashboard
After login, you'll be redirected to: `http://localhost:5001/admin/dashboard`

---

## Admin Dashboard Features

### 📊 Dashboard Overview
- Real-time statistics showing:
  - Total Products
  - Total Customers
  - Total Services
  - Total Quotes
  - Total Invoices
  - Pending Quotes

### 📦 Products Management
- View all products
- Add new products with:
  - Name, SKU, Category
  - Cost Price, Selling Price
  - Quantity in Stock
  - Reorder Level
- Calculate profit margins automatically

### 👥 Customers Management
- View all customers
- Add new customers with:
  - Name, Email, Phone
  - Address, City, State, Postal Code
  - Customer Type (Individual/Business)
  - GST Registration info

### 🔧 Services Management
- View all services
- Add new services with:
  - Service Name, Category
  - Hourly Rate
  - Description

### 📋 Quotes Management
- View all quotes
- Quote status tracking
- Customer information

### 🧾 Invoices Management
- View all invoices
- Invoice status tracking
- Payment tracking

---

## Navigation

**Sidebar Menu:**
- 📊 Dashboard - Main overview
- 📦 Products - Product management
- 👥 Customers - Customer management
- 🔧 Services - Service management
- 📋 Quotes - Quote management
- 🧾 Invoices - Invoice management

**Quick Actions:**
- ➕ Add Product
- ➕ Add Customer
- 📋 Create Quote
- 🧾 Create Invoice

---

## Form Data Entry

### Adding a Product
1. Click "Add New Product" button
2. Fill in the form:
   - Product Name (required)
   - SKU (required)
   - Category
   - Cost Price (required)
   - Selling Price (required)
   - Quantity in Stock
   - Reorder Level
   - Description
3. Click "Add Product"
4. Product appears in the table below

### Adding a Customer
1. Click "Add New Customer" button
2. Fill in the form:
   - Customer Name (required)
   - Email (required)
   - Phone (required)
   - Address
   - City, State, Postal Code
   - Customer Type (Individual/Business)
   - GST Registration checkbox
   - GST Number
3. Click "Add Customer"
4. Customer appears in the table below

### Adding a Service
1. Click "Add New Service" button
2. Fill in the form:
   - Service Name (required)
   - Category
   - Hourly Rate (required)
   - Description
3. Click "Add Service"
4. Service appears in the table below

---

## User Accounts

### Default Admin Account
- **Username:** jassal
- **Password:** Western@3029
- **Email:** admin@westernsolutions.com

### To Add More Admin Users
Use the Flask shell:
```python
from app import create_app, db
from app.models.user import User

app = create_app('development')
with app.app_context():
    user = User(username='newadmin', email='newadmin@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    print(f"✅ Admin user 'newadmin' created successfully")
```

---

## Logout

- Click "Logout" button in the top-right corner
- You'll be redirected to the login page
- Session will be cleared

---

## Security Notes

- ✅ Passwords are hashed using werkzeug.security
- ✅ Session-based authentication
- ✅ All routes require login (except /login)
- ⚠️ Change SECRET_KEY in production
- ⚠️ Use HTTPS in production deployment

---

## Troubleshooting

### "Invalid username or password"
- Check capitalization: username is `jassal` (lowercase)
- Check password: `Western@3029` (With capital W and capital S)

### "Session expired"
- Your session has timed out
- Click "Logout" and login again

### "Page not found"
- Make sure you're logged in
- Check the URL is `http://localhost:5001/admin/...`

### "Database error when adding data"
- Ensure all required fields are filled
- Check for duplicate SKUs or emails
- See the error message for details

---

## File Structure

```
app/
├── models/
│   └── user.py           # User authentication model
├── routes/
│   ├── auth.py           # Login/Logout routes
│   └── admin.py          # Admin dashboard routes
└── templates/
    ├── login.html        # Login page
    └── admin/
        ├── dashboard.html     # Admin dashboard
        ├── products.html      # Products management
        ├── customers.html     # Customers management
        ├── services.html      # Services management
        ├── quotes.html        # Quotes listing
        └── invoices.html      # Invoices listing
```

---

## Next Steps

1. ✅ Start the Flask server
2. ✅ Go to http://localhost:5001/ (redirects to login)
3. ✅ Login with credentials provided
4. ✅ Start adding products, customers, and services
5. ✅ Generate quotes and invoices
6. ✅ Track your business data in real-time!

---

**Questions?** Check the main documentation files for more details.
