import os
from datetime import timedelta


def env_flag(name, default='false'):
    return os.environ.get(name, default).strip().lower() == 'true'


class Config:
    """Base configuration"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    APP_BASE_URL = os.environ.get('APP_BASE_URL', 'http://127.0.0.1:5001')
    
    # GST configuration
    GST_RATE = 0.10  # 10% GST for Australia
    
    # Application settings
    ITEMS_PER_PAGE = 20

    # Email configuration
    MAIL_HOST = os.environ.get('MAIL_HOST', 'mail.westernitsolutions.com.au')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    MAIL_USE_SSL = env_flag('MAIL_USE_SSL', 'true')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'accounts@westernitsolutions.com.au')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'accounts@westernitsolutions.com.au')
    MAIL_TIMEOUT = int(os.environ.get('MAIL_TIMEOUT', 10))
    MAIL_ENABLED = (
        env_flag('MAIL_ENABLED', 'false') and
        bool(MAIL_HOST and MAIL_USERNAME and MAIL_PASSWORD)
    )


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///business_management.db'
    SECRET_KEY = 'dev-secret-key-change-in-production'


class ProductionConfig(Config):
    """Production configuration for Bluehost"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    APP_BASE_URL = 'https://app.application.westernitsolutions.com.au'
    
    # For Bluehost MySQL connection (optional - can use SQLite too)
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@hostname/dbname'
    
    # For SQLite (simpler deployment)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///business_management.db'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-this-to-random-secret-key'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
