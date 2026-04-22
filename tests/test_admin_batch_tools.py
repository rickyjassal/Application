import io
import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from app import create_app, db
from app.models import Customer, Invoice, InvoiceLineItem, Product
from app.services.documents import create_invoice_record, create_quote_record
from app.services.settings import update_settings


class AdminBatchToolsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()

            customer = Customer(
                name='Acme Corp',
                email='acme@example.com',
                phone='0400000000',
                business_name='Acme Corp',
            )
            product = Product(
                name='Router',
                sku='RT-01',
                category='Networking',
                cost_price=50,
                selling_price=110,
                quantity_in_stock=5,
                reorder_level=3,
            )
            db.session.add_all([customer, product])
            db.session.flush()

            invoice = Invoice(
                invoice_number='INV-TEST-1001',
                customer_id=customer.id,
                invoice_date=datetime.utcnow() - timedelta(days=10),
                due_date=datetime.utcnow() - timedelta(days=2),
                status='ISSUED',
                subtotal=100,
                gst_amount=10,
                total_amount=110,
                amount_paid=0,
            )
            db.session.add(invoice)
            db.session.flush()
            db.session.add(InvoiceLineItem(
                invoice_id=invoice.id,
                product_id=product.id,
                description='Router',
                quantity=1,
                unit_price=110,
            ))
            db.session.commit()
            self.customer_id = customer.id
            self.invoice_id = invoice.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _login(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'

    def test_statement_pdf_route_returns_pdf(self):
        self._login()
        response = self.client.get(f'/admin/customers/{self.customer_id}/statement/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertTrue(response.data.startswith(b'%PDF'))

    @patch('app.services.reminders.send_invoice_reminder_message')
    def test_single_reminder_updates_invoice_history(self, mock_send):
        self._login()
        response = self.client.post(f'/admin/invoice/{self.invoice_id}/remind')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        with self.app.app_context():
            invoice = Invoice.query.get(self.invoice_id)
            self.assertEqual(invoice.status, 'OVERDUE')
            self.assertEqual(invoice.reminder_count, 1)
            self.assertIsNotNone(invoice.last_reminder_at)
        self.assertEqual(mock_send.call_count, 1)

    def test_credit_note_reduces_balance_due(self):
        self._login()
        response = self.client.post(
            f'/admin/invoice/{self.invoice_id}/credit-note',
            json={'amount': 20, 'reason': 'Damaged item credit'},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['success'])
        self.assertAlmostEqual(payload['balance_due'], 90.0)
        with self.app.app_context():
            invoice = Invoice.query.get(self.invoice_id)
            self.assertAlmostEqual(invoice.credit_note_amount, 20.0)
            self.assertEqual(invoice.credit_note_reason, 'Damaged item credit')

    def test_backup_import_restores_customer_and_invoice(self):
        self._login()
        payload = {
            'settings': {'business_name': 'Imported Business'},
            'customers': [{
                'id': 25,
                'name': 'Imported Customer',
                'customer_type': 'BUSINESS',
                'email': 'imported@example.com',
                'phone': '0411111111',
                'business_name': 'Imported Customer Pty Ltd',
                'abn': '123',
                'street_address': '1 Test Street',
                'suburb': 'Sydney',
                'state': 'NSW',
                'postcode': '2000',
                'country': 'Australia',
                'account_balance': 0,
                'is_gst_registered': True,
                'is_active': True,
            }],
            'products': [],
            'services': [],
            'suppliers': [],
            'quotes': [],
            'invoices': [],
            'payments': [],
            'purchases': [],
            'inventory_transactions': [],
        }
        response = self.client.post(
            '/admin/tools/backup/import',
            data={'backup_file': (io.BytesIO(json.dumps(payload).encode('utf-8')), 'backup.json')},
            content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertTrue(result['success'])
        self.assertEqual(result['summary']['customers'], 1)
        with self.app.app_context():
            imported_customer = Customer.query.get(25)
            self.assertIsNotNone(imported_customer)
            self.assertEqual(imported_customer.email, 'imported@example.com')

    def test_document_branding_snapshot_stays_frozen_after_settings_change(self):
        with self.app.app_context():
            update_settings({
                'business_name': 'Brand One',
                'brand_primary_color': '#112233',
                'brand_secondary_color': '#223344',
                'brand_logo_path': 'images/Logo.png',
            })
            invoice = create_invoice_record(
                {
                    'customer_id': self.customer_id,
                    'gst_mode': 'exclusive',
                    'line_items': [{'description': 'Router', 'quantity': 1, 'unit_price': 110}],
                },
                'INV-SNAPSHOT-1',
                default_due_days=7,
            )
            quote = create_quote_record(
                {
                    'customer_id': self.customer_id,
                    'gst_mode': 'exclusive',
                    'line_items': [{'description': 'Router', 'quantity': 1, 'unit_price': 110}],
                },
                'QUO-SNAPSHOT-1',
                default_expiry_days=7,
            )
            db.session.commit()

            invoice_branding = invoice.get_branding()
            quote_branding = quote.get_branding()

            update_settings({
                'business_name': 'Brand Two',
                'brand_primary_color': '#aa0000',
                'brand_secondary_color': '#bb0000',
            })
            db.session.commit()

            self.assertEqual(invoice.get_branding()['business_name'], 'Brand One')
            self.assertEqual(invoice.get_branding()['brand_primary_color'], '#112233')
            self.assertEqual(quote.get_branding()['business_name'], 'Brand One')
            self.assertEqual(quote.get_branding()['brand_primary_color'], '#112233')
            self.assertEqual(invoice_branding['business_name'], 'Brand One')
            self.assertEqual(quote_branding['business_name'], 'Brand One')


if __name__ == '__main__':
    unittest.main()
