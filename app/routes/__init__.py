"""Routes package init"""
from .auth import auth_bp
from .dashboard import dashboard_bp
from .products import products_bp
from .purchases import purchases_bp
from .expenses import expenses_bp
from .credits import credits_bp
from .settings import settings_bp
from .misc import misc_bp

__all__ = [
    'auth_bp', 'dashboard_bp', 'products_bp', 'purchases_bp',
    'expenses_bp', 'credits_bp', 'settings_bp', 'misc_bp'
]
