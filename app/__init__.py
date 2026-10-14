"""Flask Application Factory"""
from flask import Flask, abort, has_request_context, redirect, render_template, session as flask_session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.session import Session as FlaskSQLAlchemySession
from flask_login import LoginManager, current_user
from sqlalchemy import inspect, text
from config import config_by_name
import os


class ShopRoutingSession(FlaskSQLAlchemySession):
    """Route shop data to its database while keeping users in the shared database."""

    def get_bind(self, mapper=None, clause=None, bind=None, **kwargs):
        if (
            mapper is not None
            and mapper.local_table.name != 'users'
            and has_request_context()
            and flask_session.get('active_shop', 'ceramics') == 'itobe'
        ):
            return db.engines['itobe']
        return super().get_bind(mapper=mapper, clause=clause, bind=bind, **kwargs)


# Initialize extensions
db = SQLAlchemy(session_options={'class_': ShopRoutingSession})
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

SHOP_NAMES = {
    'ceramics': 'Shop Ceramics',
    'itobe': 'Shop Itobe',
}


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
    
    def ensure_mdc_product_record_columns(engine):
        """Ensure mdc_product_records table has the price columns (schema migration helper)"""
        inspector = inspect(engine)
        if 'mdc_product_records' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('mdc_product_records')]
            with engine.begin() as connection:
                if 'cost_per_pcs_at_record' not in columns:
                    connection.execute(text('ALTER TABLE mdc_product_records ADD COLUMN cost_per_pcs_at_record NUMERIC(10, 2) DEFAULT 0'))
                if 'sell_price_per_pcs_at_record' not in columns:
                    connection.execute(text('ALTER TABLE mdc_product_records ADD COLUMN sell_price_per_pcs_at_record NUMERIC(10, 2) DEFAULT 0'))

    def ensure_mdc_report_snapshot_columns(engine):
        """Ensure mdc_reports table has snapshot columns for immutability"""
        inspector = inspect(engine)
        if 'mdc_reports' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('mdc_reports')]
            snapshot_columns = {
                'product_value': 'NUMERIC(12, 2)',
                'total_expenses': 'NUMERIC(12, 2)',
                'total_debts': 'NUMERIC(12, 2)',
                'total_paybacks': 'NUMERIC(12, 2)',
                'total_liquidity': 'NUMERIC(12, 2)',
                'cycle_profit': 'NUMERIC(12, 2)',
            }
            with engine.begin() as connection:
                for column_name, column_type in snapshot_columns.items():
                    if column_name not in columns:
                        connection.execute(text(
                            f'ALTER TABLE mdc_reports ADD COLUMN {column_name} {column_type} DEFAULT 0'
                        ))

    def ensure_expense_transaction_type_columns(engine):
        """Add transaction_type columns to older SQLite schemas."""
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        for table_name in ['expenses']:
            if table_name not in tables:
                continue
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            if 'transaction_type' not in columns:
                with engine.begin() as connection:
                    connection.execute(text(f'ALTER TABLE {table_name} ADD COLUMN transaction_type VARCHAR(20) DEFAULT "expense"'))

    def ensure_user_phone_number_column(engine):
        """Add the optional phone number field to existing user tables."""
        inspector = inspect(engine)
        if 'users' in inspector.get_table_names():
            columns = [column['name'] for column in inspector.get_columns('users')]
            if 'phone_number' not in columns:
                with engine.begin() as connection:
                    connection.execute(text('ALTER TABLE users ADD COLUMN phone_number VARCHAR(30)'))

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
        from app.models import Category

        db.create_all()
        db.Model.metadata.create_all(bind=db.engines['itobe'])

        if app.config.get('DEBUG') or app.config.get('TESTING'):
            default_categories = app.config.get('DEFAULT_PRODUCT_CATEGORIES', [])
            for engine in db.engines.values():
                with engine.begin() as connection:
                    existing_names = {
                        name.lower()
                        for name in connection.execute(
                            db.Model.metadata.tables['categories'].select()
                            .with_only_columns(Category.name)
                        ).scalars()
                    }

                    for category_data in default_categories:
                        if category_data['name'].lower() not in existing_names:
                            connection.execute(Category.__table__.insert().values(
                                name=category_data['name'],
                                description=category_data['description'],
                            ))

        for engine in db.engines.values():
            ensure_mdc_product_record_columns(engine)
            ensure_mdc_report_snapshot_columns(engine)
            ensure_expense_transaction_type_columns(engine)
            ensure_user_phone_number_column(engine)

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

    @app.route('/select-shop/<shop_name>')
    def select_shop(shop_name):
        if shop_name not in SHOP_NAMES:
            abort(404)
        flask_session['active_shop'] = shop_name
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    @app.context_processor
    def inject_shop_name():
        shop_name = flask_session.get('active_shop', 'ceramics')
        return {'active_shop_name': SHOP_NAMES.get(shop_name, SHOP_NAMES['ceramics'])}
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    return app
