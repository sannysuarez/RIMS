"""Utility and Helper Functions"""
from functools import wraps
from flask_login import current_user
from flask import redirect, url_for, flash, current_app
from datetime import datetime
from decimal import Decimal


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin privileges required', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function


def format_currency(amount):
    """Format amount as currency (server-side version)"""
    if isinstance(amount, (int, float, Decimal)):
        return f"₦{amount:,.2f}"
    return f"₦{float(amount):,.2f}"


def normalize_category_name(category_name):
    """Normalize category names for comparison"""
    if category_name is None:
        return ''
    return str(category_name).strip().lower()


def get_restore_excluded_category_names():
    """Return normalized category names excluded from restore operations."""
    excluded = current_app.config.get('RESTORE_EXCLUDED_CATEGORY_NAMES', [])
    return {normalize_category_name(name) for name in excluded}


def is_restore_excluded_category(category_name):
    """Return True when the given category should be excluded during restore."""
    return normalize_category_name(category_name) in get_restore_excluded_category_names()


def filter_restore_products(products):
    """Exclude products that belong to restore-excluded categories."""
    filtered = []
    for product in products:
        category_name = None
        if hasattr(product, 'category') and product.category is not None:
            category_name = getattr(product.category, 'name', None)
        elif isinstance(product, dict):
            category_name = product.get('category') or product.get('category_name')

        if not is_restore_excluded_category(category_name):
            filtered.append(product)
    return filtered


def get_default_category_names():
    """Return normalized default category names for the application."""
    default_categories = current_app.config.get('DEFAULT_PRODUCT_CATEGORIES', [])
    return {normalize_category_name(cat['name']) for cat in default_categories}


def filter_default_categories(categories):
    """Return only categories that are part of the default seeded category list."""
    default_names = get_default_category_names()
    return [category for category in categories if normalize_category_name(category.name) in default_names]


def calculate_cost_per_pcs(cost_per_unit, quantity_per_unit):
    """Calculate cost per piece"""
    if quantity_per_unit == 0:
        return 0
    return cost_per_unit / quantity_per_unit


def validate_sell_price(sell_price_per_pcs, cost_per_pcs):
    """Validate that sell price is greater than cost"""
    return sell_price_per_pcs > cost_per_pcs


def calculate_total_pcs(quantity_units, quantity_per_unit):
    """Calculate total number of pieces"""
    return quantity_units * quantity_per_unit


def allowed_file(filename, allowed_extensions):
    """Check if file is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def format_date(date_obj):
    """Format date to locale string (server-side version)"""
    if isinstance(date_obj, str):
        date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime('%B %d, %Y')
    return str(date_obj)


def filter_products(products, search_query='', category_filter='', sort_by='created_at_desc'):
    """Server-side product filtering and sorting"""
    # Apply search filter
    if search_query:
        search_lower = search_query.lower()
        products = [p for p in products if
                   search_lower in p.name.lower() or
                   search_lower in str(p.unique_id).lower()]

    # Apply category filter
    if category_filter:
        products = [p for p in products if str(p.category_id) == category_filter]

    # Apply sorting
    if sort_by == 'price_asc':
        products.sort(key=lambda x: x.cost_per_pcs)
    elif sort_by == 'price_desc':
        products.sort(key=lambda x: x.cost_per_pcs, reverse=True)
    elif sort_by == 'quantity_asc':
        products.sort(key=lambda x: x.remaining_quantity_pcs)
    elif sort_by == 'quantity_desc':
        products.sort(key=lambda x: x.remaining_quantity_pcs, reverse=True)
    elif sort_by == 'name_asc':
        products.sort(key=lambda x: x.name)
    elif sort_by == 'name_desc':
        products.sort(key=lambda x: x.name, reverse=True)
    else:  # created_at_desc
        products.sort(key=lambda x: x.created_at, reverse=True)

    return products


def paginate_items(items, page, per_page=20):
    """Server-side pagination"""
    total_items = len(items)
    total_pages = (total_items + per_page - 1) // per_page

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    paginated_items = items[start_idx:end_idx]

    return {
        'items': paginated_items,
        'page': page,
        'per_page': per_page,
        'total_items': total_items,
        'total': total_items,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1,
        'next_num': page + 1 if page < total_pages else None,
        'prev_num': page - 1 if page > 1 else None
    }


def validate_form_data(form_data, required_fields):
    """Server-side form validation"""
    errors = []
    for field in required_fields:
        if not form_data.get(field) or str(form_data.get(field, '')).strip() == '':
            errors.append(f"{field.replace('_', ' ').title()} is required")
    return errors


def generate_unique_id(prefix="PRD"):
    """Generate unique ID for products"""
    import uuid
    return f"{prefix}{str(uuid.uuid4())[:8].upper()}"


def calculate_liquidity_summary(products, purchases, expenses, credits, debts, cash_input=0):
    """Calculate comprehensive liquidity summary"""
    # Product inventory value
    product_value = sum(p.calculate_liquidity_value() for p in products)

    # Cash input from latest MDC report replaces dashboard cash input logic
    total_cash_input = float(cash_input)
    total_purchases = total_cash_input

    # Total expenses
    total_expenses = sum(float(e.amount) for e in expenses)

    # Outstanding debts from unpaid customer credits
    total_debts = sum(float(c.remaining_balance) for c in credits)

    # Total paybacks received (for reporting only, not double-counted in liquidity)
    total_paybacks = sum(float(d.amount) for d in debts if d.transaction_type == 'payback')

    # Final liquidity calculation should include inventory, cash input, expenses and outstanding debts only
    total_liquidity = product_value + total_cash_input - total_expenses - total_debts

    return {
        'product_value': product_value,
        'total_purchases': total_purchases,
        'total_cash_input': total_cash_input,
        'total_expenses': total_expenses,
        'total_debts': total_debts,
        'total_paybacks': total_paybacks,
        'total_liquidity': total_liquidity
    }
