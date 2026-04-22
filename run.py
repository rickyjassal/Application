#!/usr/bin/env python
"""
Business Management System - Entry Point
"""

import os
from app import create_app, db
from app.models import (
    User, Product, Service, Customer, Invoice, InvoiceLineItem,
    Quote, QuoteLineItem, Payment, DiscountCode, InventoryTransaction
)

app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    """Create shell context for Flask CLI"""
    return {
        'db': db,
        'User': User,
        'Product': Product,
        'Service': Service,
        'Customer': Customer,
        'Invoice': Invoice,
        'InvoiceLineItem': InvoiceLineItem,
        'Quote': Quote,
        'QuoteLineItem': QuoteLineItem,
        'Payment': Payment,
        'DiscountCode': DiscountCode,
        'InventoryTransaction': InventoryTransaction
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)
