from app import create_app, db
from app.models import Customer, Product, Service

app = create_app('development')
with app.app_context():
    customers = Customer.query.count()
    products = Product.query.count()
    services = Service.query.count()
    
    print(f"Customers: {customers}")
    print(f"Products: {products}")
    print(f"Services: {services}")
    
    if customers > 0:
        cust = Customer.query.first()
        print(f"\nFirst Customer: {cust.name} ({cust.business_name})")
    
    if products > 0:
        prod = Product.query.first()
        print(f"First Product: {prod.name} - ${prod.selling_price}")
    
    if services > 0:
        svc = Service.query.first()
        print(f"First Service: {svc.name} - ${svc.base_price}")
