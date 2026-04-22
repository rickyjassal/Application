#!/usr/bin/env python3
"""
Quick data entry script for adding products, customers, and quotes
"""
import requests
import json

BASE_URL = "http://localhost:5001/api"

def add_product():
    """Add a new product"""
    print("\n" + "="*60)
    print("➕ ADD NEW PRODUCT")
    print("="*60)
    
    name = input("Product Name: ")
    sku = input("SKU (e.g., PROD-001): ")
    category = input("Category (e.g., Mobile Repair): ")
    description = input("Description: ")
    cost_price = float(input("Cost Price ($): "))
    selling_price = float(input("Selling Price ($): "))
    quantity = int(input("Quantity in Stock: "))
    
    data = {
        "name": name,
        "sku": sku,
        "category": category,
        "description": description,
        "cost_price": cost_price,
        "selling_price": selling_price,
        "quantity_in_stock": quantity,
        "reorder_level": max(5, quantity // 2)
    }
    
    try:
        response = requests.post(f"{BASE_URL}/products", json=data)
        if response.status_code == 201:
            print(f"\n✅ Product added successfully!")
            print(f"Profit Margin: {((selling_price - cost_price) / cost_price * 100):.1f}%")
        else:
            print(f"❌ Error: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")

def add_customer():
    """Add a new customer"""
    print("\n" + "="*60)
    print("➕ ADD NEW CUSTOMER")
    print("="*60)
    
    name = input("Customer Name: ")
    customer_type = input("Type (INDIVIDUAL/BUSINESS/CASH): ").upper()
    email = input("Email (optional): ") or None
    phone = input("Phone: ")
    
    if customer_type == "BUSINESS":
        abn = input("ABN: ")
        address = input("Business Address: ")
    else:
        abn = None
        address = input("Address: ")
    
    data = {
        "name": name,
        "customer_type": customer_type,
        "email": email,
        "phone_number": phone,
        "address": address,
        "abn_acn": abn
    }
    
    try:
        response = requests.post(f"{BASE_URL}/customers", json=data)
        if response.status_code == 201:
            print(f"\n✅ Customer added successfully!")
        else:
            print(f"❌ Error: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")

def generate_quote():
    """Generate a new quote"""
    print("\n" + "="*60)
    print("📄 GENERATE NEW QUOTE")
    print("="*60)
    
    # List customers
    try:
        customers_resp = requests.get(f"{BASE_URL}/customers")
        customers = customers_resp.json()['items']
        
        print("\nAvailable Customers:")
        for i, cust in enumerate(customers, 1):
            print(f"{i}. {cust['name']} ({cust['customer_type']})")
        
        customer_idx = int(input("Select customer (number): ")) - 1
        customer_id = customers[customer_idx]['id']
        
        # List products
        products_resp = requests.get(f"{BASE_URL}/products")
        products = products_resp.json()['items']
        
        print("\nAvailable Products:")
        for i, prod in enumerate(products, 1):
            print(f"{i}. {prod['name']} - ${prod['selling_price']}")
        
        product_idx = int(input("Select product (number): ")) - 1
        product_id = products[product_idx]['id']
        quantity = int(input("Quantity: "))
        
        data = {
            "customer_id": customer_id,
            "line_items": [
                {
                    "product_id": product_id,
                    "quantity": quantity
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/quotes", json=data)
        if response.status_code == 201:
            quote = response.json()
            print(f"\n✅ Quote generated successfully!")
            print(f"Quote #: {quote.get('quote_number')}")
            print(f"Amount: ${quote.get('total_amount')}")
        else:
            print(f"❌ Error: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")

def view_data():
    """View all data"""
    print("\n" + "="*60)
    print("📊 VIEW DATA")
    print("="*60)
    
    menus = {
        "1": ("Products", "products"),
        "2": ("Customers", "customers"),
        "3": ("Invoices", "invoices"),
        "4": ("Quotes", "quotes")
    }
    
    for key, (name, endpoint) in menus.items():
        print(f"{key}. {name}")
    
    choice = input("\nSelect (1-4): ")
    if choice in menus:
        try:
            response = requests.get(f"{BASE_URL}/{menus[choice][1]}")
            data = response.json()
            name = menus[choice][0]
            print(f"\n{name}: {data.get('total', 0)} records")
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Main menu"""
    while True:
        print("\n" + "="*60)
        print("🎯 BUSINESS MANAGEMENT SYSTEM - DATA ENTRY")
        print("="*60)
        print("""
1. ➕ Add Product
2. ➕ Add Customer
3. 📄 Generate Quote
4. 📊 View Data
5. 🚪 Exit
        """)
        
        choice = input("Select option (1-5): ").strip()
        
        if choice == "1":
            add_product()
        elif choice == "2":
            add_customer()
        elif choice == "3":
            generate_quote()
        elif choice == "4":
            view_data()
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main()
