"""Flask Application Factory"""
from flask import Flask, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from sqlalchemy import inspect, text
from config import config_by_name
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app(config_name=None):
    """
    Application factory function
    
    Args:
        config_name (str): Configuration environment (development, testing, production)
    
    Returns:
        Flask: Configured Flask application instance
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    def ensure_mdc_product_record_columns():
        """Ensure mdc_product_records table has the price columns (schema migration helper)"""
        inspector = inspect(db.engine)
        if 'mdc_product_records' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('mdc_product_records')]
            if 'cost_per_pcs_at_record' not in columns:
                db.session.execute(text('ALTER TABLE mdc_product_records ADD COLUMN cost_per_pcs_at_record NUMERIC(10, 2) DEFAULT 0'))
                db.session.commit()
            if 'sell_price_per_pcs_at_record' not in columns:
                db.session.execute(text('ALTER TABLE mdc_product_records ADD COLUMN sell_price_per_pcs_at_record NUMERIC(10, 2) DEFAULT 0'))
                db.session.commit()

    def ensure_mdc_report_snapshot_columns():
        """Ensure mdc_reports table has snapshot columns for immutability"""
        inspector = inspect(db.engine)
        if 'mdc_reports' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('mdc_reports')]
            # Add numeric snapshot columns if missing
            if 'product_value' not in columns:
                db.session.execute(text('ALTER TABLE mdc_reports ADD COLUMN product_value NUMERIC(12, 2) DEFAULT 0'))
                db.session.commit()
            if 'total_expenses' not in columns:
                db.session.execute(text('ALTER TABLE mdc_reports ADD COLUMN total_expenses NUMERIC(12, 2) DEFAULT 0'))
                db.session.commit()
            if 'total_debts' not in columns:
                db.session.execute(text('ALTER TABLE mdc_reports ADD COLUMN total_debts NUMERIC(12, 2) DEFAULT 0'))
                db.session.commit()
            if 'total_paybacks' not in columns:
                db.session.execute(text('ALTER TABLE mdc_reports ADD COLUMN total_paybacks NUMERIC(12, 2) DEFAULT 0'))
                db.session.commit()
            if 'total_liquidity' not in columns:
                db.session.execute(text('ALTER TABLE mdc_reports ADD COLUMN total_liquidity NUMERIC(12, 2) DEFAULT 0'))
                db.session.commit()
            if 'cycle_profit' not in columns:
                db.session.execute(text('ALTER TABLE mdc_reports ADD COLUMN cycle_profit NUMERIC(12, 2) DEFAULT 0'))
                db.session.commit()

    def ensure_expense_transaction_type_columns():
        """Add transaction_type columns to older SQLite schemas."""
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        for table_name in ['expenses']:
            if table_name not in tables:
                continue
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            if 'transaction_type' not in columns:
                db.session.execute(text(f'ALTER TABLE {table_name} ADD COLUMN transaction_type VARCHAR(20) DEFAULT "expense"'))
                db.session.commit()

    def ensure_user_phone_number_column():
        """Add the optional phone number field to existing user tables."""
        inspector = inspect(db.engine)
        if 'users' in inspector.get_table_names():
            columns = [column['name'] for column in inspector.get_columns('users')]
            if 'phone_number' not in columns:
                db.session.execute(text('ALTER TABLE users ADD COLUMN phone_number VARCHAR(30)'))
                db.session.commit()

    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.products import products_bp
    from app.routes.purchases import purchases_bp
    from app.routes.expenses import expenses_bp
    from app.routes.credits import credits_bp
    from app.routes.settings import settings_bp
    from app.routes.misc import misc_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(purchases_bp, url_prefix='/purchases')
    app.register_blueprint(expenses_bp, url_prefix='/expenses')
    app.register_blueprint(credits_bp, url_prefix='/credits')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(misc_bp, url_prefix='/misc')
    
    # Create database tables
    with app.app_context():
        db.create_all()

        if app.config.get('DEBUG') or app.config.get('TESTING'):
            from app.models.product import Category
            default_categories = app.config.get('DEFAULT_PRODUCT_CATEGORIES', [])
            existing_names = {category.name.lower() for category in Category.query.all()}

            for cat_data in default_categories:
                if cat_data['name'].lower() not in existing_names:
                    db.session.add(Category(name=cat_data['name'], description=cat_data['description']))

            if db.session.new:
                db.session.commit()
        
        # Ensure MDC product record schema is up to date
        ensure_mdc_product_record_columns()
        # Ensure MDC reports snapshot columns exist (for older databases)
        ensure_mdc_report_snapshot_columns()
        # Ensure older SQLite schemas include the transaction_type column used by expense tracking.
        ensure_expense_transaction_type_columns()
        ensure_user_phone_number_column()

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register template filters and globals
    from app.utils.helpers import format_currency
    from datetime import datetime
    app.jinja_env.globals.update(format_currency=format_currency, datetime=datetime)
    
    # Root route - show shop selection
    @app.route('/')
    def index():
        return render_template('shop_select.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    return app
