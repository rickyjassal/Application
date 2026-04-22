# 🚀 QUICK START GUIDE

## Getting Started with Your Business Management System

Your system is fully running and ready to use! Here's what you need to know:

---

## 1. **Is the Server Running?** 

Check if your Flask server is running on `http://localhost:5001`

```powershell
# If NOT running, start it:
cd "c:\Users\parmi\Documents\Project\Mobile Database Management Tool"
python run.py
```

**Expected output:**
```
WARNING in app.run_unsafe: This is a development server. Do not use it in production applications.
Running on http://localhost:5001
```

---

## 2. **Access Your Dashboard**

Open your browser and go to:
```
http://localhost:5001
```

You'll see:
- **Sidebar**: Navigation menu with 9 sections
- **Company Logo**: Red and white circular logo
- **Dashboard**: Stats, charts, and data tables
- **Navigation Buttons**: Products, Customers, Quotes, Invoices, etc.

---

## 3. **Three Easy Ways to Add Data**

### **Method 1: Interactive Script (EASIEST)** ⭐
```powershell
python data_entry.py
```
Menu options:
- Add Products
- Add Customers  
- Generate Quotes
- View Data

---

### **Method 2: Example Scripts (Fast)**

**Add a Product:**
```powershell
python example_add_product.py
```
This adds: "Samsung Galaxy S24 Screen ($380)"

**Add a Customer:**
```powershell
python example_add_customer.py
```
This adds: "TechCorp Solutions" customer

**Generate a Quote:**
```powershell
python example_generate_quote.py
```
This creates a quote with products and services

---

### **Method 3: API Endpoints (Advanced)**

Use `curl` or Postman to POST data:

```bash
# Add Product
curl -X POST http://localhost:5001/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name":"iPhone Screen",
    "cost_price":120,
    "selling_price":350,
    "quantity_in_stock":5
  }'

# Add Customer  
curl -X POST http://localhost:5001/api/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name":"New Customer",
    "email":"email@example.com",
    "phone":"0400000000"
  }'
```

---

## 4. **Real-time Dashboard Updates**

After adding data:
1. Check the shell output for "✅ SUCCESS"
2. Go to `http://localhost:5001` in browser
3. Click the relevant section (Products, Customers, Quotes, etc.)
4. **New data appears automatically!**

---

## 5. **Common Tasks**

### **View All Products**
- Dashboard → Click "Products" tab
- Or: `GET http://localhost:5001/api/products`

### **View All Customers**
- Dashboard → Click "Customers" tab
- Or: `GET http://localhost:5001/api/customers`

### **View All Quotes**
- Dashboard → Click "Quotes" tab
- Or: `GET http://localhost:5001/api/quotes`

### **Generate Invoice from Quote**
```bash
curl -X PUT http://localhost:5001/api/quotes/1/convert \
  -H "Content-Type: application/json"
```

### **Record Payment**
```bash
curl -X POST http://localhost:5001/api/payments \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": 1,
    "amount": 100.00,
    "payment_method": "Cash",
    "notes": "Paid in full"
  }'
```

---

## 6. **Key Information**

| Item | Value |
|------|-------|
| **Server URL** | http://localhost:5001 |
| **Database** | business_management.db (SQLite) |
| **Main Dashboard** | http://localhost:5001 |
| **API Base** | http://localhost:5001/api |
| **Current Data** | 5 Products, 4 Customers, 17 records |

---

## 7. **Testing Your Data Entry**

**Recommended First Steps:**

1. **Run the interactive script:**
   ```powershell
   python data_entry.py
   ```

2. **Add a test product:**
   - Select option "1" (Add Product)
   - Enter: Name="Test Phone Screen", Price="$299", Quantity="10"
   - Confirm

3. **Check dashboard:**
   - Go to http://localhost:5001
   - Click "Products"
   - Your new product should appear in the table

4. **Try adding a customer:**
   - Back to terminal, select option "2" (Add Customer)
   - Enter customer details
   - Verify it appears in Products → Customers table

---

## 8. **What's Included**

✅ **Database**: 8 models, 50+ endpoints  
✅ **API**: Full CRUD operations on all entities  
✅ **Dashboard**: Professional UI with red branding  
✅ **Navigation**: 9 functional pages  
✅ **Data Entry**: Multiple methods (script, API, examples)  
✅ **Documentation**: Comprehensive guides  

---

## 9. **Need Help?**

- **How to add data?** → Read DATA_ENTRY_GUIDE.md
- **API endpoints?** → Read QUICK_REFERENCE.md
- **System architecture?** → Read ARCHITECTURE.md
- **Deployment?** → Read BLUEHOST_DEPLOYMENT.md

---

## ⚡ Next Steps

1. ✅ Make sure Flask server is running (`python run.py`)
2. ✅ Open dashboard at http://localhost:5001
3. ✅ Try `python data_entry.py` to add your first real data
4. ✅ Watch data appear live in the dashboard!
5. 🎉 Start managing your business!

---

**Questions?** Check the documentation files in your project folder.  
**Ready to deploy?** Follow BLUEHOST_DEPLOYMENT.md when you're ready for production.
