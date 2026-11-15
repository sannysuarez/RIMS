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
        {'name': 'Water & Table Water', 'description': 'Bottled, sachet, and table water products'},
        {'name': 'Soft Drinks & Malt', 'description': 'Soft drinks and malt beverages'},
        {'name': 'Energy Drinks', 'description': 'Energy drink products'},
        {'name': 'Juices & Fruit Drinks', 'description': 'Juices and fruit drink products'},
        {'name': 'Dairy Drinks', 'description': 'Dairy drink products'},
        {'name': 'Biscuits & Snacks', 'description': 'Biscuits and snack products'},
        {'name': 'Bread & Bakery', 'description': 'Bread and bakery products'},
        {'name': 'Food Staples & Dry Goods', 'description': 'Food staples and dry goods'},
        {'name': 'Seasonings, Spices & Condiments', 'description': 'Seasonings, spices, and condiments'},
        {'name': 'Cooking Oil', 'description': 'Cooking oil products'},
        {'name': 'Canned, pack, and sachet Foods', 'description': 'Canned, packaged, and sachet foods'},
        {'name': 'Candy & Confectionery', 'description': 'Candy and confectionery products'},
        {'name': 'Beverage Mixes & Sugar', 'description': 'Beverage mixes and sugar'},
        {'name': 'Toiletries & Personal Care', 'description': 'Toiletries and personal care products'},
        {'name': 'Detergents & Cleaning Agents', 'description': 'Detergents and household cleaning agents'},
        {'name': 'Household & Utility Items', 'description': 'Household and utility items'},
        {'name': 'Baby Care & Diapers', 'description': 'Baby care products and diapers'},
        {'name': 'Mosquito & Insect Control', 'description': 'Mosquito and insect control products'},
        {'name': 'Feminine Hygiene', 'description': 'Feminine hygiene products'},
        {'name': 'Stationery', 'description': 'Stationery products'},
    ]

    # Categories that should be excluded when restoring development/test data
    RESTORE_EXCLUDED_CATEGORY_NAMES = [
        'Water & Table Water',
        'Soft Drinks & Malt',
        'Energy Drinks',
        'Juices & Fruit Drinks',
        'Dairy Drinks',
        'Biscuits & Snacks',
        'Bread & Bakery',
        'Food Staples & Dry Goods',
        'Seasonings, Spices & Condiments',
        'Cooking Oil',
        'Canned, pack, and sachet Foods',
        'Candy & Confectionery',
        'Beverage Mixes & Sugar',
        'Toiletries & Personal Care',
        'Detergents & Cleaning Agents',
        'Household & Utility Items',
        'Baby Care & Diapers',
        'Mosquito & Insect Control',
        'Feminine Hygiene',
        'Stationery',
    ]


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///raasu_dev.db'
    SQLALCHEMY_BINDS = {
        'itobe': os.environ.get('ITOBE_DATABASE_URL') or 'sqlite:///raasu_itobe_dev.db'
    }
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_BINDS = {'itobe': 'sqlite:///:memory:'}
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # Use SQLite for production (scalable with proper indexing)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///raasu_production.db'
    SQLALCHEMY_BINDS = {
        'itobe': os.environ.get('ITOBE_DATABASE_URL') or 'sqlite:///raasu_itobe_production.db'
    }


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
