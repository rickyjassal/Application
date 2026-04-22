#!/usr/bin/env python3
"""
Example: Add a new customer to the system
"""
import requests
import json

# Server URL
BASE_URL = "http://localhost:5001/api"

# New customer data
new_customer = {
    "name": "TechCorp Solutions",
    "email": "contact@techcorp.com.au",
    "phone": "02 9555 1234",
    "address": "123 Tech Park, Brisbane QLD 4000",
    "city": "Brisbane",
    "state": "QLD",
    "postal_code": "4000",
    "country": "Australia",
    "customer_type": "Business",
    "gst_registered": True,
    "gst_number": "98 765 432 101"
}

print("="*70)
print("👤 ADDING NEW CUSTOMER TO SYSTEM")
print("="*70)
print(f"\nCustomer Details:")
print(f"  Name: {new_customer['name']}")
print(f"  Type: {new_customer['customer_type']}")
print(f"  Email: {new_customer['email']}")
print(f"  Phone: {new_customer['phone']}")
print(f"  Address: {new_customer['address']}")
print(f"  GST Registered: {'Yes' if new_customer['gst_registered'] else 'No'}")
if new_customer['gst_registered']:
    print(f"  GST Number: {new_customer['gst_number']}")

try:
    print("\n⏳ Adding to database...")
    response = requests.post(f"{BASE_URL}/customers", json=new_customer)
    
    if response.status_code == 201:
        result = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"  Customer ID: {result['id']}")
        print(f"  Name: {result['name']}")
        print(f"  Email: {result['email']}")
        
        print(f"\n🔗 View all customers at:")
        print(f"  http://localhost:5001 → Click 'Customers' in the dashboard\n")
    else:
        print(f"\n❌ Error: {response.json()}")
        
except Exception as e:
    print(f"\n❌ Connection Error: {e}")
    print("\nMake sure the Flask server is running:")
    print("  python run.py")
