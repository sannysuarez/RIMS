"""Flask Application Factory"""
from flask import Flask, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
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
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.products import products_bp
    from app.routes.purchases import purchases_bp
    from app.routes.expenses import expenses_bp
    from app.routes.credits import credits_bp
    from app.routes.ruf_yog import ruf_yog_bp
    from app.routes.misc import misc_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(purchases_bp, url_prefix='/purchases')
    app.register_blueprint(expenses_bp, url_prefix='/expenses')
    app.register_blueprint(credits_bp, url_prefix='/credits')
    app.register_blueprint(ruf_yog_bp, url_prefix='/ruf-yog')
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
