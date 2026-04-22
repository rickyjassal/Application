#!/usr/bin/env python3
"""
Test script to verify all navigation pages are working
"""
import requests
import json

BASE_URL = "http://localhost:5001/api"

pages = {
    "Dashboard": "GET /",
    "Products": "GET /api/products",
    "Services": "GET /api/services",
    "Customers": "GET /api/customers",
    "Invoices": "GET /api/invoices",
    "Quotes": "GET /api/quotes",
    "Payments": "GET /api/payments",
    "Discount Codes": "GET /api/discounts",
    "Sales Reports": "GET /api/reports/sales"
}

print("\n" + "="*70)
print("🧪 NAVIGATION FUNCTIONALITY TEST")
print("="*70 + "\n")

passed = 0
failed = 0

for page_name, endpoint in pages.items():
    try:
        if "Dashboard" in page_name:
            response = requests.get("http://localhost:5001", timeout=5)
        else:
            response = requests.get(BASE_URL + endpoint.replace("GET /api", ""), timeout=5)
        
        if response.status_code == 200:
            print(f"✅ {page_name:20} - {endpoint:30} - OK")
            passed += 1
        else:
            print(f"❌ {page_name:20} - {endpoint:30} - Status: {response.status_code}")
            failed += 1
    except Exception as e:
        print(f"❌ {page_name:20} - {endpoint:30} - Error: {str(e)[:30]}")
        failed += 1

print("\n" + "="*70)
print(f"Results: {passed} Passed ✅ | {failed} Failed ❌")
print("="*70 + "\n")

if failed == 0:
    print("🎉 All navigation pages are working correctly!")
else:
    print(f"⚠️  {failed} page(s) need attention")
