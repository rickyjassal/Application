#!/usr/bin/env python3
"""
Example: Generate a new quote for a customer
"""
import requests
import json

# Server URL
BASE_URL = "http://localhost:5001/api"

# New quote data
new_quote = {
    "customer_id": 1,  # Change this to the customer ID you want
    "quote_date": "2025-03-17",
    "expiry_date": "2025-04-17",
    "items": [
        {
            "product_id": 1,
            "quantity": 2,
            "unit_price": 280.00
        },
        {
            "service_id": 1,
            "quantity": 4,
            "unit_price": 50.00
        }
    ],
    "notes": "Professional quote for mobile repair services"
}

print("="*70)
print("📋 GENERATING NEW QUOTE")
print("="*70)
print(f"\nQuote Details:")
print(f"  Customer ID: {new_quote['customer_id']}")
print(f"  Quote Date: {new_quote['quote_date']}")
print(f"  Expiry Date: {new_quote['expiry_date']}")
print(f"\n  Items:")
for idx, item in enumerate(new_quote['items'], 1):
    if 'product_id' in item:
        print(f"    {idx}. Product ID {item['product_id']}: "
              f"{item['quantity']} x ${item['unit_price']:.2f}")
    else:
        print(f"    {idx}. Service ID {item['service_id']}: "
              f"{item['quantity']} x ${item['unit_price']:.2f}")

try:
    print("\n⏳ Creating quote...")
    response = requests.post(f"{BASE_URL}/quotes", json=new_quote)
    
    if response.status_code == 201:
        result = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"  Quote ID: {result['id']}")
        print(f"  Quote Number: {result['quote_number']}")
        print(f"  Customer ID: {result['customer_id']}")
        print(f"  Status: {result['status']}")
        
        # Calculate totals
        subtotal = sum(item['quantity'] * item['unit_price'] 
                      for item in new_quote['items'])
        gst = subtotal * 0.10
        total = subtotal + gst
        print(f"\n  Subtotal: ${subtotal:.2f}")
        print(f"  GST (10%): ${gst:.2f}")
        print(f"  Total: ${total:.2f}")
        
        print(f"\n🔗 View all quotes at:")
        print(f"  http://localhost:5001 → Click 'Quotes' in the dashboard\n")
    else:
        print(f"\n❌ Error: {response.json()}")
        
except Exception as e:
    print(f"\n❌ Connection Error: {e}")
    print("\nMake sure the Flask server is running:")
    print("  python run.py")

print("\n" + "="*70)
print("💡 TIP: Once satisfied with a quote, convert it to invoice:")
print("   PUT http://localhost:5001/api/quotes/{quote_id}/convert")
print("="*70)
