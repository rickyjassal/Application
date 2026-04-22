#!/usr/bin/env python
"""
Sample Data Loader - Populate database with test data for development
Run: python seed_database.py
"""

from datetime import datetime, timedelta
from app import create_app, db
from app.models import (
    Product, Service, Customer, DiscountCode, 
    Invoice, InvoiceLineItem, Quote, QuoteLineItem, Payment
)

def seed_database():
    """Populate database with sample data"""
    
    app = create_app('development')
    
    with app.app_context():
        # Clear existing data (optional - comment out if you want to preserve)
        print("Clearing existing data...")
        db.session.query(Payment).delete()
        db.session.query(InvoiceLineItem).delete()
        db.session.query(Invoice).delete()
        db.session.query(QuoteLineItem).delete()
        db.session.query(Quote).delete()
        db.session.query(Product).delete()
        db.session.query(Service).delete()
        db.session.query(Customer).delete()
        db.session.query(DiscountCode).delete()
        db.session.commit()
        
        print("✓ Database cleared\n")
        
        # Add Products
        print("Adding Products...")
        products = [
            Product(
                name='iPhone 13 Screen Replacement',
                sku='APPLE-IPHONE13-SCREEN',
                category='Mobile Repair',
                description='Original Apple quality screen for iPhone 13',
                cost_price=120.00,
                selling_price=280.00,
                quantity_in_stock=15,
                reorder_level=5,
                is_active=True
            ),
            Product(
                name='MacBook Battery Replacement',
                sku='APPLE-BATTERY-001',
                category='Laptop Repair',
                description='OEM MacBook battery replacement',
                cost_price=65.00,
                selling_price=150.00,
                quantity_in_stock=8,
                reorder_level=3,
                is_active=True
            ),
            Product(
                name='Samsung Galaxy S22 Charging Port',
                sku='SAMSUNG-CHARGE-PORT',
                category='Mobile Repair',
                description='Charging port replacement for Samsung Galaxy S22',
                cost_price=35.00,
                selling_price=99.00,
                quantity_in_stock=20,
                reorder_level=5,
                is_active=True
            ),
            Product(
                name='Laptop Hard Drive SSD 512GB',
                sku='SSD-512GB-KINGSTON',
                category='Laptop Repair',
                description='Kingston 512GB SSD for laptop upgrades',
                cost_price=45.00,
                selling_price=120.00,
                quantity_in_stock=12,
                reorder_level=5,
                is_active=True
            ),
            Product(
                name='PC Graphics Card RTX 3060',
                sku='NVIDIA-RTX3060',
                category='IT Repair',
                description='NVIDIA RTX 3060 Graphics Card',
                cost_price=350.00,
                selling_price=650.00,
                quantity_in_stock=3,
                reorder_level=2,
                is_active=True
            ),
        ]
        db.session.add_all(products)
        db.session.commit()
        print(f"✓ Added {len(products)} products\n")
        
        # Add Services
        print("Adding Services...")
        services = [
            Service(
                name='Mobile Phone Repair',
                service_type='MOBILE_REPAIR',
                description='Screen replacement, battery, charging port, etc.',
                base_price=50.00,
                hourly_rate=60.00,
                is_active=True
            ),
            Service(
                name='Laptop Repair Service',
                service_type='LAPTOP_REPAIR',
                description='Hardware diagnostics, repairs, upgrades',
                base_price=75.00,
                hourly_rate=80.00,
                is_active=True
            ),
            Service(
                name='IT Support & Setup',
                service_type='IT_REPAIR',
                description='Network setup, virus removal, system optimization',
                base_price=100.00,
                hourly_rate=90.00,
                is_active=True
            ),
            Service(
                name='Website Design & Development',
                service_type='WEBSITE_DESIGN',
                description='Custom website design and deployment',
                base_price=500.00,
                hourly_rate=100.00,
                is_active=True
            ),
        ]
        db.session.add_all(services)
        db.session.commit()
        print(f"✓ Added {len(services)} services\n")
        
        # Add Customers
        print("Adding Customers...")
        customers = [
            Customer(
                name='John Smith',
                customer_type='INDIVIDUAL',
                email='john.smith@email.com',
                phone='0412345678',
                street_address='123 Main Street',
                suburb='Sydney',
                state='NSW',
                postcode='2000',
                country='Australia',
                is_gst_registered=False,
                is_active=True
            ),
            Customer(
                name='Acme Corporation',
                customer_type='BUSINESS',
                business_name='Acme Corp Pty Ltd',
                email='admin@acmecorp.com.au',
                phone='0287654321',
                abn='12345678901',
                acn='123456789',
                street_address='456 Business Ave',
                suburb='Melbourne',
                state='VIC',
                postcode='3000',
                country='Australia',
                is_gst_registered=True,
                is_active=True,
                account_balance=0.00
            ),
            Customer(
                name='Sarah Johnson',
                customer_type='INDIVIDUAL',
                email='sarah.j@email.com',
                phone='0498765432',
                street_address='789 Oak Lane',
                suburb='Brisbane',
                state='QLD',
                postcode='4000',
                country='Australia',
                is_gst_registered=False,
                is_active=True
            ),
            Customer(
                name='Cash Customer',
                customer_type='CASH',
                email=None,
                phone=None,
                is_gst_registered=False,
                is_active=True
            ),
        ]
        db.session.add_all(customers)
        db.session.commit()
        print(f"✓ Added {len(customers)} customers\n")
        
        # Add Discount Codes
        print("Adding Discount Codes...")
        discounts = [
            DiscountCode(
                code='WELCOME10',
                description='Welcome discount for first-time customers',
                discount_type='PERCENTAGE',
                discount_value=10.0,
                valid_from=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=90),
                max_uses=50,
                current_uses=2,
                minimum_order_value=50.00,
                is_active=True
            ),
            DiscountCode(
                code='SAVE25',
                description='Save $25 on orders over $200',
                discount_type='FIXED_AMOUNT',
                discount_value=25.00,
                valid_from=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=60),
                max_uses=30,
                current_uses=0,
                minimum_order_value=200.00,
                maximum_discount_amount=50.00,
                is_active=True
            ),
            DiscountCode(
                code='BULK15',
                description='15% discount on bulk orders',
                discount_type='PERCENTAGE',
                discount_value=15.0,
                valid_from=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=180),
                max_uses=None,  # Unlimited
                current_uses=0,
                minimum_order_value=500.00,
                is_active=True
            ),
        ]
        db.session.add_all(discounts)
        db.session.commit()
        print(f"✓ Added {len(discounts)} discount codes\n")
        
        # Add Quotes
        print("Adding Quotes...")
        now = datetime.utcnow()
        quote = Quote(
            quote_number=f"QT-{now.strftime('%Y%m%d')}-001",
            customer_id=1,  # John Smith
            status='DRAFT',
            quote_date=now,
            expiry_date=now + timedelta(days=30),
            notes='Standard pricing - valid for 30 days',
            terms_and_conditions='Payment due within 14 days of invoice'
        )
        
        # Add items to quote
        quote_item1 = QuoteLineItem(
            product_id=1,  # iPhone Screen
            description='iPhone 13 Screen Replacement',
            quantity=1,
            unit_price=280.00
        )
        quote_item2 = QuoteLineItem(
            service_id=1,  # Mobile Repair
            description='Labor - Screen installation',
            quantity=1,
            unit_price=50.00
        )
        quote.line_items.extend([quote_item1, quote_item2])
        
        db.session.add(quote)
        db.session.commit()
        print(f"✓ Added sample quote (QT-{now.strftime('%Y%m%d')}-001)\n")
        
        # Add Invoice
        print("Adding Invoice...")
        invoice = Invoice(
            invoice_number=f"INV-{now.strftime('%Y%m%d')}-001",
            customer_id=3,  # Sarah Johnson
            status='ISSUED',
            invoice_date=now,
            due_date=now + timedelta(days=14),
            payment_mode='ACCOUNT',
            notes='Thank you for your business!',
            terms_and_conditions='Payment due within 14 days'
        )
        
        # Add invoice items
        inv_item1 = InvoiceLineItem(
            product_id=2,  # MacBook Battery
            description='MacBook Battery Replacement',
            quantity=1,
            unit_price=150.00
        )
        invoice.line_items.append(inv_item1)
        
        # Calculate totals
        invoice.subtotal = 150.00
        invoice.gst_amount = invoice.subtotal * 0.10  # 10% GST
        invoice.discount_amount = 0
        invoice.total_amount = invoice.subtotal + invoice.gst_amount
        invoice.amount_paid = 0
        
        db.session.add(invoice)
        db.session.commit()
        print(f"✓ Added sample invoice (INV-{now.strftime('%Y%m%d')}-001)\n")
        
        # Add Payment
        print("Adding Payment...")
        payment = Payment(
            invoice_id=1,
            customer_id=3,
            amount=100.00,
            payment_mode='CASH',
            status='COMPLETED',
            payment_date=now,
            payment_reference='CASH-001'
        )
        db.session.add(payment)
        
        # Update invoice amount paid and status
        invoice.amount_paid = 100.00
        invoice.status = 'PARTIAL'
        db.session.commit()
        print(f"✓ Added sample payment\n")
        
        # Summary
        print("=" * 50)
        print("DATABASE SEEDING COMPLETE!")
        print("=" * 50)
        print(f"Products: {Product.query.count()}")
        print(f"Services: {Service.query.count()}")
        print(f"Customers: {Customer.query.count()}")
        print(f"Discount Codes: {DiscountCode.query.count()}")
        print(f"Quotes: {Quote.query.count()}")
        print(f"Invoices: {Invoice.query.count()}")
        print(f"Payments: {Payment.query.count()}")
        print("\nYou can now test the APIs!")
        print("Start the app: python run.py")
        print("Visit: http://localhost:5000")

if __name__ == '__main__':
    seed_database()
