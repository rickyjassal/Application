import unittest

from app import create_app, db
from app.models import Customer


class ApiSecurityAndDocumentsTestCase(unittest.TestCase):
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
            )
            db.session.add(customer)
            db.session.commit()
            self.customer_id = customer.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _login(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'

    def test_api_routes_require_login(self):
        for path in ['/api/invoices', '/api/quotes', '/api/payments', '/api/reports/sales']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 401, path)

    def test_quote_api_uses_gst_inclusive_totals(self):
        self._login()
        response = self.client.post('/api/quotes', json={
            'customer_id': self.customer_id,
            'gst_mode': 'inclusive',
            'line_items': [
                {
                    'description': 'Service A',
                    'quantity': 2,
                    'unit_price': 110,
                }
            ],
        })
        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload['gst_mode'], 'inclusive')
        self.assertAlmostEqual(payload['subtotal'], 200.0)
        self.assertAlmostEqual(payload['gst'], 20.0)
        self.assertAlmostEqual(payload['total'], 220.0)

    def test_invoice_api_uses_shared_totals_and_status(self):
        self._login()
        response = self.client.post('/api/invoices', json={
            'customer_id': self.customer_id,
            'gst_mode': 'exclusive',
            'advance_payment': 55,
            'line_items': [
                {
                    'description': 'Service B',
                    'quantity': 1,
                    'unit_price': 100,
                }
            ],
        })
        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload['gst_mode'], 'exclusive')
        self.assertAlmostEqual(payload['subtotal'], 100.0)
        self.assertAlmostEqual(payload['gst_amount'], 10.0)
        self.assertAlmostEqual(payload['total_amount'], 110.0)
        self.assertAlmostEqual(payload['amount_paid'], 55.0)
        self.assertEqual(payload['balance_due'], 55.0)
        self.assertEqual(payload['status'], 'PARTIAL')


if __name__ == '__main__':
    unittest.main()
