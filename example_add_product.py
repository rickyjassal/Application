#!/usr/bin/env python3
"""
Example: Add a new product to the system
"""
import requests
import json

# Server URL
BASE_URL = "http://localhost:5001/api"

# New product data
new_product = {
    "name": "Samsung Galaxy S24 Screen",
    "sku": "SAMSUNG-S24-SCREEN",
    "category": "Mobile Repair",
    "description": "Original Samsung screen replacement",
    "cost_price": 150,
    "selling_price": 380,
    "quantity_in_stock": 8,
    "reorder_level": 5
}

print("="*70)
print("📦 ADDING NEW PRODUCT TO SYSTEM")
print("="*70)
print(f"\nProduct Details:")
print(f"  Name: {new_product['name']}")
print(f"  Cost: ${new_product['cost_price']}")
print(f"  Price: ${new_product['selling_price']}")
print(f"  Profit: {((new_product['selling_price'] - new_product['cost_price']) / new_product['cost_price'] * 100):.1f}%")
print(f"  Stock: {new_product['quantity_in_stock']} units")

try:
    print("\n⏳ Adding to database...")
    response = requests.post(f"{BASE_URL}/products", json=new_product)
    
    if response.status_code == 201:
        result = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"  Product ID: {result['id']}")
        print(f"  Name: {result['name']}")
        print(f"  Price: ${result['selling_price']}")
        
        # Show how to view it
        print(f"\n🔗 View it at:")
        print(f"  http://localhost:5001/api/products")
        print(f"  Or go to Dashboard → Products in the UI\n")
    else:
        print(f"\n❌ Error: {response.json()}")
        
except Exception as e:
    print(f"\n❌ Connection Error: {e}")
    print("\nMake sure the Flask server is running:")
    print("  python run.py")
