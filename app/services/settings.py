from app import db
from app.models import AppSetting
import json


DEFAULT_APP_SETTINGS = {
    'business_name': 'Western IT Solutions',
    'business_legal_name': 'WESTERN IT SOLUTIONS PTY LTD',
    'business_address': 'Tarneit - 3029',
    'business_abn': '95 670 634 465',
    'business_contact_email': 'info@westernitsolutions.com.au',
    'bank_name': 'CBA',
    'bank_account_name': 'Western IT Solutions',
    'bank_bsb': '062-692',
    'bank_account_number': '7997 5017',
    'invoice_due_days': '7',
    'quote_expiry_days': '7',
    'brand_primary_color': '#dc2626',
    'brand_secondary_color': '#b91c1c',
    'brand_logo_path': 'images/Logo.png',
}

BRANDING_SETTING_KEYS = [
    'business_name',
    'business_legal_name',
    'business_address',
    'business_abn',
    'business_contact_email',
    'bank_name',
    'bank_account_name',
    'bank_bsb',
    'bank_account_number',
    'brand_primary_color',
    'brand_secondary_color',
    'brand_logo_path',
]


def get_app_settings():
    rows = AppSetting.query.all()
    settings = dict(DEFAULT_APP_SETTINGS)
    settings.update({row.key: row.value for row in rows if row.value is not None})
    return settings


def get_setting(key, default=None):
    settings = get_app_settings()
    if default is None:
        default = DEFAULT_APP_SETTINGS.get(key)
    return settings.get(key, default)


def update_settings(values):
    existing = {row.key: row for row in AppSetting.query.all()}
    for key, value in values.items():
        row = existing.get(key)
        if row is None:
            row = AppSetting(key=key)
            db.session.add(row)
        row.value = '' if value is None else str(value)


def normalize_color(value, default):
    value = (value or '').strip()
    if not value:
        return default
    if not value.startswith('#'):
        value = f'#{value}'
    if len(value) != 7:
        return default
    return value.lower()


def get_branding_settings():
    settings = get_app_settings()
    branding = {key: settings.get(key, DEFAULT_APP_SETTINGS.get(key, '')) for key in BRANDING_SETTING_KEYS}
    branding['brand_primary_color'] = normalize_color(branding.get('brand_primary_color'), DEFAULT_APP_SETTINGS['brand_primary_color'])
    branding['brand_secondary_color'] = normalize_color(branding.get('brand_secondary_color'), DEFAULT_APP_SETTINGS['brand_secondary_color'])
    branding['brand_logo_path'] = branding.get('brand_logo_path') or DEFAULT_APP_SETTINGS['brand_logo_path']
    return branding


def capture_branding_snapshot():
    return dict(get_branding_settings())


def serialize_branding_snapshot(values):
    return json.dumps(values or {}, sort_keys=True)


def parse_branding_snapshot(raw_value):
    if not raw_value:
        return None
    try:
        payload = json.loads(raw_value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    branding = dict(get_branding_settings())
    branding.update({key: value for key, value in payload.items() if value is not None})
    branding['brand_primary_color'] = normalize_color(branding.get('brand_primary_color'), DEFAULT_APP_SETTINGS['brand_primary_color'])
    branding['brand_secondary_color'] = normalize_color(branding.get('brand_secondary_color'), DEFAULT_APP_SETTINGS['brand_secondary_color'])
    branding['brand_logo_path'] = branding.get('brand_logo_path') or DEFAULT_APP_SETTINGS['brand_logo_path']
    return branding


def get_document_branding(document):
    snapshot = parse_branding_snapshot(getattr(document, 'branding_snapshot', None))
    return snapshot or get_branding_settings()
