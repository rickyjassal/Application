#!/usr/bin/env python
"""
QUICK TEST - Verify your application works
Run: python quick_test.py
"""

print("=" * 60)
print("BUSINESS MANAGEMENT SYSTEM - QUICK TEST")
print("=" * 60)

# Test 1: Import Flask
print("\n[1/5] Testing Flask import...")
try:
    import flask
    print("✅ Flask installed successfully")
except ImportError:
    print("❌ Flask not installed - run: pip install -r requirements.txt")

# Test 2: Import SQLAlchemy
print("\n[2/5] Testing SQLAlchemy import...")
try:
    import sqlalchemy
    print("✅ SQLAlchemy installed successfully")
except ImportError:
    print("❌ SQLAlchemy not installed - run: pip install -r requirements.txt")

# Test 3: Test app creation
print("\n[3/5] Testing app creation...")
try:
    from app import create_app, db
    app = create_app('development')
    print("✅ App created successfully")
except Exception as e:
    print(f"❌ Error creating app: {e}")
    exit(1)

# Test 4: Test database initialization
print("\n[4/5] Testing database initialization...")
try:
    with app.app_context():
        db.create_all()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"❌ Error initializing database: {e}")
    exit(1)

# Test 5: Test models
print("\n[5/5] Testing database models...")
try:
    from app.models import Product, Service, Customer, Invoice, Quote, Payment
    with app.app_context():
        product_count = Product.query.count()
        service_count = Service.query.count()
        customer_count = Customer.query.count()
    print(f"✅ Models working correctly")
    print(f"   - Products: {product_count}")
    print(f"   - Services: {service_count}")
    print(f"   - Customers: {customer_count}")
except Exception as e:
    print(f"❌ Error with models: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nNext steps:")
print("1. Run: python run.py")
print("2. Open: http://localhost:5000")
print("3. Follow: SETUP.md for full documentation")
print("\n" + "=" * 60)
