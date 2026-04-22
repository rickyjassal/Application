🌐 Login URL:     http://localhost:5001/login
📧 Username:      jassal
🔐 Password:      Western@3029
💾 Database:      business_management.db (SQLite)🌐 Login URL:     http://localhost:5001/login
📧 Username:      jassal
🔐 Password:      Western@3029
💾 Database:      business_management.db (SQLite)🌐 Login URL:     http://localhost:5001/login
📧 Username:      jassal
🔐 Password:      Western@3029
💾 Database:      business_management.db (SQLite)🌐 Login URL:     http://localhost:5001/login
📧 Username:      jassal
🔐 Password:      Western@3029
💾 Database:      business_management.db (SQLite)🌐 Login URL:     http://localhost:5001/login
📧 Username:      jassal
🔐 Password:      Western@3029
💾 Database:      business_management.db (SQLite)🌐 Login URL:     http://localhost:5001/login
📧 Username:      jassal
🔐 Password:      Western@3029
💾 Database:      business_management.db (SQLite)🌐 Login URL:     http://localhost:5001/login
📧 Username:      jassal
🔐 Password:      Western@3029
💾 Database:      business_management.db (SQLite)🌐 Login URL:     http://localhost:5001/login
📧 Username:      jassal
🔐 Password:      Western@3029
💾 Database:      business_management.db (SQLite)🌐 Login URL:     http://localhost:5001/login
📧 Username:      jassal
🔐 Password:      Western@3029
💾 Database:      business_management.db (SQLite)🌐 Login URL:     http://localhost:5001/login
📧 Username:      jassal
🔐 Password:      Western@3029
💾 Database:      business_management.db (SQLite)🌐 Login URL:     http://localhost:5001/login
📧 Username:      jassal
🔐 Password:      Western@3029
💾 Database:      business_management.db (SQLite)🌐 Login URL:     http://localhost:5001/login
📧 Username:      jassal
🔐 Password:      Western@3029
💾 Database:      business_management.db (SQLite)🌐 Login URL:     http://localhost:5001/login
📧 Username:      jassal
🔐 Password:      Western@3029
💾 Database:      business_management.db (SQLite)🌐 Login URL:     http://localhost:5001/login
📧 Username:      jassal
🔐 Password:      Western@3029
💾 Database:      business_management.db (SQLite)# Business Management System - Data Entry Guide

## 🎯 Three Ways to Add Data

### Option 1: Quick Data Entry Script (EASIEST) ⭐
**Run this command:**
```
python data_entry.py
```

**What you can do:**
- ➕ Add Products (name, SKU, price, cost, stock)
- ➕ Add Customers (individual, business, cash)
- 📄 Generate Quotes (select customer & product)
- 📊 View all records

**Example Session:**
```
Select option: 1
Product Name: iPhone 14 Screen
SKU: APPLE-IP14-SCREEN
Category: Mobile Repair
Description: Original screen replacement
Cost Price: 100
Selling Price: 280
Quantity: 10

✅ Product added successfully!
Profit Margin: 180.0%
```

---

### Option 2: API Endpoints (Advanced)
**For developers using Postman or curl**

#### Add Product
```
POST /api/products
{
  "name": "iPhone 14 Screen",
  "sku": "APPLE-IP14",
  "category": "Mobile Repair",
  "cost_price": 100,
  "selling_price": 280,
  "quantity_in_stock": 10
}
```

#### Add Customer
```
POST /api/customers
{
  "name": "John Doe",
  "customer_type": "INDIVIDUAL",
  "email": "john@email.com",
  "phone_number": "0437800000",
  "address": "123 Main St"
}
```

#### Create Invoice
```
POST /api/invoices
{
  "customer_id": 1,
  "line_items": [
    {
      "product_id": 1,
      "quantity": 2
    }
  ]
}
```

#### Generate Quote
```
POST /api/quotes
{
  "customer_id": 1,
  "line_items": [
    {
      "product_id": 1,
      "quantity": 1
    }
  ]
}
```

---

### Option 3: Web Dashboard Forms (Coming Soon)
We can add visual forms to the dashboard for a more user-friendly experience.

---

## 📌 Quick Start

**Step 1:** Open Terminal/PowerShell
```
cd "c:\Users\parmi\Documents\Project\Mobile Database Management Tool"
```

**Step 2:** Run the data entry script
```
python data_entry.py
```

**Step 3:** Follow the interactive prompts

**Step 4:** Go to http://localhost:5001 to see your data!

---

## 📊 Current Data

- 5 Products
- 4 Customers
- 4 Services
- 1 Invoice
- 3 Discount Codes
- 1 Quote

**All data is automatically formatted with:**
- ✅ GST calculations (10%)
- ✅ Profit margin calculations
- ✅ Stock tracking
- ✅ Invoice status management
