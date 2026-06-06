"""Application Configuration Module"""
import os
from datetime import timedelta


class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File uploads
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'xlsx', 'xls'}

    # Default product categories for development and seeded data
    DEFAULT_PRODUCT_CATEGORIES = [
        {'name': 'bottle water', 'description': 'Bottled drinking water products'},
        {'name': 'sachet water', 'description': 'Sachet drinking water products'},
        {'name': 'energy drink', 'description': 'Energy drink products'},
        {'name': 'juice drink', 'description': 'Juice drink products'},
        {'name': 'carbonated drink', 'description': 'Carbonated drink products'},
        {'name': 'dairy drink', 'description': 'Dairy drink products'},
        {'name': 'hot beverage', 'description': 'Hot beverage products'},
        {'name': 'house hold', 'description': 'Household products'},
        {'name': 'toiletry', 'description': 'Toiletry products'},
        {'name': 'cooking', 'description': 'Cooking products'},
        {'name': 'snack', 'description': 'Snack products'},
        {'name': 'bakery', 'description': 'Bakery products'},
        {'name': 'candy', 'description': 'Candy products'}
    ]

    # Categories that should be excluded when restoring development/test data
    RESTORE_EXCLUDED_CATEGORY_NAMES = [
        'bottle water',
        'sachet water',
        'energy drink',
        'juice drink',
        'carbonated drink',
        'dairy drink',
        'hot beverage',
        'house hold',
        'toiletry',
        'cooking',
        'snack',
        'bakery',
        'candy'
    ]


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///raasu_dev.db'
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # Use SQLite for production (scalable with proper indexing)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///raasu_production.db'


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
