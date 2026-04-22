import requests
import json

print("\n" + "="*70)
print("🎯 YOUR BUSINESS MANAGEMENT SYSTEM - LIVE DATA")
print("="*70)

# Get Products
print("\n1️⃣  PRODUCTS IN INVENTORY")
print("-" * 70)
response = requests.get('http://localhost:5001/api/products')
data = response.json()
print(f"Total Products: {data['total']}\n")
for product in data['items']:
    print(f"   📦 {product['name']}")
    print(f"      SKU: {product['sku']}")
    print(f"      Cost: ${product['cost_price']} → Selling: ${product['selling_price']}")
    print(f"      Profit: {product['profit_margin']:.1f}% | Stock: {product['quantity_in_stock']} units\n")

# Get Customers
print("\n2️⃣  CUSTOMERS")
print("-" * 70)
response = requests.get('http://localhost:5001/api/customers')
data = response.json()
print(f"Total Customers: {data['total']}\n")
for customer in data['items']:
    print(f"   👤 {customer['name']}")
    print(f"      Type: {customer['customer_type']}")
    if customer['email']:
        print(f"      Email: {customer['email']}")
    print(f"      Account Balance: ${customer['account_balance']}\n")

# Get Services
print("\n3️⃣  SERVICES")
print("-" * 70)
response = requests.get('http://localhost:5001/api/services')
data = response.json()
print(f"Total Services: {data['total']}\n")
for service in data['items']:
    print(f"   🔧 {service['name']}")
    print(f"      Base Price: ${service['base_price']}")
    if service['hourly_rate']:
        print(f"      Hourly Rate: ${service['hourly_rate']}\n")

# Get Invoices
print("\n4️⃣  INVOICES")
print("-" * 70)
response = requests.get('http://localhost:5001/api/invoices')
data = response.json()
print(f"Total Invoices: {data['total']}\n")
for invoice in data['items']:
    print(f"   📄 Invoice: {invoice['invoice_number']}")
    print(f"      Status: {invoice['status']} | Date: {invoice['invoice_date'][:10]}")
    print(f"      Subtotal: ${invoice['subtotal']} + GST ${invoice['gst_amount']} = ${invoice['total_amount']}")
    print(f"      Paid: ${invoice['amount_paid']} | Balance: ${invoice['balance_due']}\n")

# Get Discount Codes
print("\n5️⃣  DISCOUNT CODES")
print("-" * 70)
response = requests.get('http://localhost:5001/api/discounts')
data = response.json()
print(f"Total Discount Codes: {data['total']}\n")
for discount in data['items']:
    print(f"   🏷️  Code: {discount['code']}")
    print(f"      Type: {discount['discount_type']} | Value: {discount['discount_value']}")
    print(f"      Valid: {discount['is_valid']} | Uses: {discount['current_uses']}/{discount['max_uses']}\n")

# Get Sales Report
print("\n6️⃣  SALES REPORT (Last 30 Days)")
print("-" * 70)
response = requests.get('http://localhost:5001/api/reports/sales')
data = response.json()
print(f"Period: {data['period']['from'][:10]} to {data['period']['to'][:10]}")
print(f"Total Invoices: {data['total_invoices']}")
print(f"Total Sales: ${data['total_sales']}")
print(f"Total Paid: ${data['total_paid']}")
print(f"Outstanding: ${data['outstanding']}\n")

print("="*70)
print("✅ ALL SYSTEMS OPERATIONAL AND READY!")
print("="*70 + "\n")
