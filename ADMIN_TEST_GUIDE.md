# 🎯 Admin Login System - Test Instructions

## Step-by-Step Testing Guide

Follow these exact steps to test your new admin login system with GUI-based data entry.

---

## ✅ Pre-Requirements

Make sure you have:
- [ ] Flask server not currently running
- [ ] Python 3.12+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Browser open (Chrome, Firefox, Edge, etc.)

---

## 🚀 Step 1: Start the Flask Server

### Open PowerShell/Terminal

```powershell
cd "c:\Users\parmi\Documents\Project\Mobile Database Management Tool"
```

### Start the server

```powershell
python run.py
```

### Expected output:
```
WARNING in app.run_unsafe: This is a development server. Do not use it in production applications.
Running on http://localhost:5001
Press CTRL+C to quit
```

✅ **Server is running on port 5001**

---

## 🔐 Step 2: Open Login Page

### In your browser, go to:
```
http://localhost:5001/login
```

### You should see:
- Professional login page with red branding
- Company logo emoji (🔐)
- "Admin Portal" heading
- Username input field
- Password input field
- "Sign In" button
- Demo credentials at bottom

✅ **Login page displayed**

---

## 📝 Step 3: Login with Admin Credentials

### Enter the following:

**Username:** `jassal`  
**Password:** `Western@3029`

### Important notes:
- ⚠️ Username is LOWERCASE (jassal, not Jassal)
- ⚠️ Password has capitals (Western@3029, not western@3029)
- ⚠️ @ symbol is an "@" not anything else

### Click "Sign In" button

✅ **You should be redirected to /admin/dashboard**

---

## 📊 Step 4: Verify Admin Dashboard

### After login, you should see:

**Header:**
- Company logo circle with "∆"
- "Admin Dashboard" title
- Your username: "jassal"
- "Logout" button

**Sidebar Menu:**
- 📊 Dashboard (highlighted in red)
- 📦 Products
- 👥 Customers
- 🔧 Services
- 📋 Quotes
- 🧾 Invoices

**Main Content:**
- "Dashboard Overview" heading
- 6 statistic cards showing:
  - Total Products: [number]
  - Total Customers: [number]
  - Total Services: [number]
  - Total Quotes: [number]
  - Total Invoices: [number]
  - Pending Quotes: [number]
- 4 quick action buttons:
  - ➕ Add Product
  - ➕ Add Customer
  - 📋 Create Quote
  - 🧾 Create Invoice

✅ **Dashboard loaded successfully**

---

## 📦 Step 5: Test Product Addition

### Click "➕ Add Product" button or click "📦 Products" in sidebar

### You should see:
- "Manage Products" heading
- "Add New Product" button
- A form with fields (hidden at first)

### Click "Add New Product" button

### The form should expand with fields:
- Product Name (required)
- SKU (required)
- Category
- Cost Price (required)
- Selling Price (required)
- Quantity in Stock
- Reorder Level
- Description

### Fill in test data:

```
Product Name:    Test iPhone Screen
SKU:             TEST-IPHONE-001
Category:        Mobile Repair
Cost Price:      100
Selling Price:   350
Quantity:        5
Reorder Level:   2
Description:     Test product for demonstration
```

### Click "Add Product" button

### You should see:
- Green success message: "✅ Product added successfully"
- Form clears
- Page reloads or data updates
- New product appears in the table below

✅ **Product created successfully**

---

## 👥 Step 6: Test Customer Addition

### Click "👥 Customers" in sidebar

### You should see:
- "Manage Customers" heading
- "Add New Customer" button
- Customer table (empty or with existing customers)

### Click "Add New Customer" button

### Fill in test data:

```
Customer Name:       Test Customer Ltd
Email:              test@example.com
Phone:              0410 123 456
Address:            123 Test Street
City:               Brisbane
State:              QLD
Postal Code:        4000
Country:            Australia
Customer Type:      Business
GST Registered:     ✓ (checked)
GST Number:         98 765 432 101
```

### Click "Add Customer" button

### You should see:
- Green success message
- Form clears
- Page updates
- New customer in table

✅ **Customer created successfully**

---

## 🔧 Step 7: Test Service Addition

### Click "🔧 Services" in sidebar

### Fill in test data:

```
Service Name:     Mobile Screen Replacement
Category:         Mobile Repair
Hourly Rate:      50.00
Description:      Professional screen replacement service
```

### Click "Add Service" button

### Verify:
- Success message appears
- New service in table

✅ **Service created successfully**

---

## 📋 Step 8: View Quotes

### Click "📋 Quotes" in sidebar

### You should see:
- Quote listing page
- Table with columns:
  - Quote #
  - Customer
  - Status
  - Date
  - Expiry Date
  - Actions button

### If quotes exist, they'll be displayed
### If no quotes, you'll see: "No quotes yet"

✅ **Quotes page working**

---

## 🧾 Step 9: View Invoices

### Click "🧾 Invoices" in sidebar

### You should see:
- Invoice listing page
- Table with columns:
  - Invoice #
  - Customer
  - Status
  - Date
  - Due Date
  - Actions button

### If invoices exist, they'll be displayed
### If no invoices, you'll see: "No invoices yet"

✅ **Invoices page working**

---

## 🚪 Step 10: Test Logout

### Click "Logout" button (top right)

### You should be:
- Redirected to login page
- Session cleared
- Requirements to login again

✅ **Logout working successfully**

---

## 🔄 Step 11: Test Re-login

### Login again with:
- Username: `jassal`
- Password: `Western@3029`

### Verify:
- Login page accepts credentials
- Dashboard loads
- Your previously added data is still there

✅ **Re-login and persistence working**

---

## ⚠️ Step 12: Test Unauthorized Access

### Without logging out, open new tab and go to:
```
http://localhost:5001/admin/dashboard
```

### You should be:
- Redirected to login page
- Unable to access protected routes without session

✅ **Authorization protection working**

---

## ✅ Complete Testing Checklist

```
✅ Login page loads           [ ]
✅ Login succeeds            [ ]
✅ Dashboard displays        [ ]
✅ Sidebar navigation works  [ ]
✅ Can add product          [ ]
✅ Product appears in table  [ ]
✅ Can add customer         [ ]
✅ Customer appears in table [ ]
✅ Can add service          [ ]
✅ Service appears in table  [ ]
✅ Quotes page loads        [ ]
✅ Invoices page loads      [ ]
✅ Logout works             [ ]
✅ Re-login works           [ ]
✅ Data persists across login/logout [ ]
✅ Unauthorized access blocked [ ]
✅ All forms validate       [ ]
✅ Success messages display [ ]
✅ Error messages display (if needed) [ ]
✅ Profit calculations work (if applicable) [ ]
```

---

## 🐛 Troubleshooting

### Problem: "Cannot GET /login"
**Solution:** 
- Make sure Flask server is running: `python run.py`
- Check server output shows "Running on http://localhost:5001"

### Problem: "Invalid username or password"
**Solution:**
- Check username is exactly: `jassal` (all lowercase)
- Check password is exactly: `Western@3029` (with capitals)
- Copy from documentation to avoid typos

### Problem: Form won't submit
**Solution:**
- Check all required fields (marked with *) are filled
- Make sure email format is valid (contains @)
- Check for error message in red box

### Problem: New data not appearing
**Solution:**
- Wait a moment for page to update
- Try refreshing page (F5)
- Check success message appeared
- Check console for errors (F12 → Console tab)

### Problem: Session expired
**Solution:**
- Click Logout
- Login again
- Session may timeout after 7 days of inactivity

### Problem: Sidebar not visible
**Solution:**
- Try refreshing page
- Check browser window is wide enough
- On mobile, may need to click menu icon

---

## 📱 Testing on Different Devices

### Desktop Browser
- ✅ Full functionality
- ✅ All buttons accessible
- ✅ Forms easy to fill

### Tablet Browser
- ✅ Should work with responsive design
- ✅ Touch-friendly buttons

### Mobile Browser
- ⚠️ May need to scroll
- ⚠️ Sidebar might be collapsed
- ✅ Still functional

---

## 📊 Expected Data After Testing

After following all steps, you should have:

**Products:**
- Test iPhone Screen (from step 5)
- Any previously added products

**Customers:**
- Test Customer Ltd (from step 6)
- Any previously added customers

**Services:**
- Mobile Screen Replacement (from step 7)
- Any previously added services

**Quotes:**
- Previously created quotes (read-only)

**Invoices:**
- Previously created invoices (read-only)

---

## 🎉 Success Criteria

Your admin system is **working correctly** if:

1. ✅ Can login with jassal / Western@3029
2. ✅ Dashboard displays with all 6 statistic cards
3. ✅ Can navigate using sidebar menu
4. ✅ Can add products using the form
5. ✅ Can add customers using the form
6. ✅ Can add services using the form
7. ✅ Can view quotes and invoices
8. ✅ Can logout and login again
9. ✅ Data persists across sessions
10. ✅ Unauthorized access is blocked

**If all 10 items checked, your admin system is ready for use! 🚀**

---

## 📞 Next Steps

### If Testing Passed ✅
- Start using the admin system for your business
- Add real products, customers, and services
- Begin generating quotes and invoices
- See data live on the dashboard

### If Issues Found ❌
- Check the Troubleshooting section
- Review error messages carefully
- Check Flask console for technical errors
- Ensure all prerequisites are met

---

## 🎯 Good to Know

### Features Now Available
- ✅ Secure admin login portal
- ✅ Professional dashboard with stats
- ✅ GUI forms for data entry (no more CLI scripts!)
- ✅ Product management
- ✅ Customer management
- ✅ Service management
- ✅ Quote tracking
- ✅ Invoice tracking
- ✅ Session-based authentication
- ✅ Secure password storage

### Not Yet Implemented
- 🚧 Edit/Update functionality (read-only view mode)
- 🚧 Delete functionality (safety lock)
- 🚧 Create quotes through GUI
- 🚧 Create invoices through GUI
- 🚧 Payment tracking GUI
- 🚧 Reports and analytics

### Available Soon
- 📅 These features will be added in next updates
- 💬 API endpoints already support these operations

---

**Good luck with your testing! 🚀**

Questions? Check the documentation files in your project folder.
