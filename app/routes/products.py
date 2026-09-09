"""Products Management Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.product import Product, Category
from app.models.mdc import MDCReport
from app.models.mdc_product_record import MDCProductRecord
from app.models.expense import Expense
from app.models.credit import Credit, Debt
from sqlalchemy import func
from app.utils.helpers import (
    admin_required, format_currency, filter_products,
    paginate_items, validate_form_data, generate_unique_id,
    filter_default_categories
)
from datetime import datetime
import uuid

products_bp = Blueprint('products', __name__)


@products_bp.route('/')
@login_required
def index():
    """Display all products with search and sort (server-side)"""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'created_at_desc')
    category_filter = request.args.get('category', '')

    # Get all products (we'll filter and paginate server-side)
    all_products = Product.query.all()

    # Apply server-side filtering and sorting
    filtered_products = filter_products(
        all_products,
        search_query=search_query,
        category_filter=category_filter,
        sort_by=sort_by
    )

   

    # Apply server-side pagination
    pagination_result = paginate_items(filtered_products, page, per_page=20)

    categories = Category.query.order_by(Category.name).all()
    if current_app.config.get('DEBUG') or current_app.config.get('TESTING'):
        categories = filter_default_categories(categories)

    return render_template('products/index.html',
                         products=pagination_result['items'],
                         pagination=pagination_result,
                         categories=categories,
                         search_query=search_query,
                         sort_by=sort_by,
                         category_filter=category_filter,
                        )


@products_bp.route('/mdc', methods=['GET', 'POST'])
@login_required
@admin_required
def mdc():
    """Admin-only monthly data collection view for manual stock counting"""
    products = Product.query.order_by(Product.name).all()
    latest_mdc = MDCReport.query.order_by(MDCReport.report_date.desc()).first()

    if request.method == 'POST':
        errors = []
        cash_input_raw = request.form.get('cash_input', '').strip()
        cash_input_value = 0.0

        if cash_input_raw:
            try:
                cash_input_value = float(cash_input_raw)
            except ValueError:
                errors.append('Invalid cash input amount')

        if cash_input_value < 0:
            errors.append('Cash input cannot be negative')

        for product in products:
            field_name = f'remaining_{product.id}'
            if field_name not in request.form:
                continue

            remaining_value_raw = request.form.get(field_name, '').strip()
            if remaining_value_raw == '':
                continue

            try:
                remaining_quantity_pcs = int(remaining_value_raw)
            except ValueError:
                errors.append(f'Invalid remaining quantity for {product.name}')
                continue

            if remaining_quantity_pcs < 0 or remaining_quantity_pcs > product.total_quantity_pcs:
                errors.append(
                    f'Remaining quantity for {product.name} must be between 0 and {product.total_quantity_pcs}'
                )
                continue

            product.remaining_quantity_pcs = remaining_quantity_pcs
            product.remaining_quantity_units = remaining_quantity_pcs // product.quantity_per_unit
            product.sold_quantity_pcs = max(product.total_quantity_pcs - remaining_quantity_pcs, 0)

        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('products.mdc'))

        # Create MDC report for this cycle
        mdc_report = MDCReport(cash_input=cash_input_value, report_date=datetime.now())
        db.session.add(mdc_report)
        db.session.flush()  # Flush to get the ID without committing yet

        # Create product records for this MDC cycle and update product quantities
        product_value_sum = 0.0
        cycle_profit_sum = 0.0
        for product in products:
            sold_quantity_pcs = max(product.total_quantity_pcs - product.remaining_quantity_pcs, 0)

            # Record the sale in this MDC cycle with current prices (immutable snapshot)
            product_record = MDCProductRecord(
                mdc_report_id=mdc_report.id,
                product_id=product.id,
                sold_quantity_pcs=sold_quantity_pcs,
                remaining_quantity_pcs=product.remaining_quantity_pcs,
                cost_per_pcs_at_record=product.cost_per_pcs,
                sell_price_per_pcs_at_record=product.sell_price_per_pcs,
                recorded_at=datetime.now()
            )
            db.session.add(product_record)

            # Accumulate cycle snapshot values
            product_value_sum += float(product.remaining_quantity_pcs) * float(product.cost_per_pcs)
            cycle_profit_sum += float((product.sell_price_per_pcs - product.cost_per_pcs) * sold_quantity_pcs)

            # Update product baseline for next cycle: remaining becomes the new total
            product.total_quantity_pcs = product.remaining_quantity_pcs
            product.total_quantity_units = product.remaining_quantity_units
            product.sold_quantity_pcs = 0  # Reset sold for next cycle

        # Compute expenses and debts snapshot for this cycle window
        # The previous latest_mdc is the older boundary (if any)
        start_date = latest_mdc.report_date if latest_mdc else None
        end_date = mdc_report.report_date

        if start_date:
            expenses_in_cycle = Expense.query.filter(Expense.expense_date > start_date, Expense.expense_date <= end_date).all()
            debts_in_cycle = Debt.query.filter(Debt.transaction_date > start_date, Debt.transaction_date <= end_date).all()
        else:
            expenses_in_cycle = Expense.query.filter(Expense.expense_date <= end_date).all()
            debts_in_cycle = Debt.query.filter(Debt.transaction_date <= end_date).all()

        total_expenses_cycle = sum(float(e.amount) for e in expenses_in_cycle)
        total_paybacks_cycle = sum(float(d.amount) for d in debts_in_cycle if d.transaction_type == 'payback')
        # snapshot of outstanding debts up to end_date
        outstanding_debts_total = db.session.query(func.coalesce(func.sum(Credit.remaining_balance), 0)).filter(Credit.created_at <= end_date).scalar() or 0.0
        outstanding_debts_total = float(outstanding_debts_total)

        # Set snapshot fields on the MDC report so historical cycles remain immutable
        mdc_report.product_value = product_value_sum
        mdc_report.total_expenses = total_expenses_cycle
        mdc_report.total_paybacks = total_paybacks_cycle
        mdc_report.total_debts = outstanding_debts_total
        mdc_report.total_liquidity = product_value_sum + float(cash_input_value) - total_expenses_cycle - outstanding_debts_total
        mdc_report.cycle_profit = cycle_profit_sum

        db.session.commit()

        flash('Monthly stock counts and cash input saved successfully.', 'success')
        return redirect(url_for('products.mdc'))

    return render_template('products/mdc.html', products=products, latest_mdc=latest_mdc)



@products_bp.route('/mdc/reports')
@login_required
def mdc_reports():
    """List MDC reports with search and pagination"""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()

    # Query base
    query = MDCReport.query.order_by(MDCReport.report_date.desc())

    if search_query:
        # allow searching by id or by date substring
        if search_query.isdigit():
            query = query.filter(MDCReport.id == int(search_query))
        else:
            # naive date substring search on formatted date
            all_reports = query.all()
            filtered = [r for r in all_reports if search_query.lower() in r.report_date.strftime('%b %d, %Y').lower()]
            # paginate filtered list manually
            pagination = paginate_items(filtered, page, per_page=20)
            return render_template('products/mdc_reports.html', reports=pagination['items'], pagination=pagination, search_query=search_query)

    # use flask/sqlalchemy pagination via list for consistency with helpers
    all_reports = query.all()
    pagination = paginate_items(all_reports, page, per_page=20)

    return render_template('products/mdc_reports.html', reports=pagination['items'], pagination=pagination, search_query=search_query)


@products_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Add new product with server-side validation"""
    if request.method == 'POST':
        # Server-side form validation
        required_fields = ['product_name', 'category_id', 'unit_type',
                          'quantity_per_unit', 'quantity_units', 'cost_per_unit', 'sell_price_per_pcs']

        errors = validate_form_data(request.form, required_fields)
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('products.add_product'))

        product_name = request.form.get('product_name')
        category_id = request.form.get('category_id', type=int)
        unit_type = request.form.get('unit_type')
        quantity_per_unit = request.form.get('quantity_per_unit', type=int)
        quantity_units = request.form.get('quantity_units', type=int)
        cost_per_unit = request.form.get('cost_per_unit', type=float)
        sell_price_per_pcs = request.form.get('sell_price_per_pcs', type=float)

        # Check if product exists (server-side)
        if Product.query.filter_by(name=product_name).first():
            flash('Product already exists', 'error')
            return redirect(url_for('products.add_product'))

        # Server-side business logic validation
        cost_per_pcs = cost_per_unit / quantity_per_unit
        if sell_price_per_pcs <= cost_per_pcs:
            flash('Sell price must be greater than cost price per piece', 'error')
            return redirect(url_for('products.add_product'))

        unique_id = generate_unique_id("PRD")
        total_quantity_pcs = quantity_units * quantity_per_unit

        product = Product(
            unique_id=unique_id,
            name=product_name,
            category_id=category_id,
            unit_type=unit_type,
            quantity_per_unit=quantity_per_unit,
            cost_per_unit=cost_per_unit,
            cost_per_pcs=cost_per_pcs,
            sell_price_per_pcs=sell_price_per_pcs,
            total_quantity_units=quantity_units,
            total_quantity_pcs=total_quantity_pcs,
            remaining_quantity_units=quantity_units,
            remaining_quantity_pcs=total_quantity_pcs
        )

        db.session.add(product)
        db.session.commit()

        flash(f'Product {product_name} added successfully with ID: {unique_id}', 'success')
        return redirect(url_for('products.index'))

    categories = Category.query.order_by(Category.name).all()
    if current_app.config.get('DEBUG') or current_app.config.get('TESTING'):
        categories = filter_default_categories(categories)
    return render_template('products/add.html', categories=categories)


@products_bp.route('/<int:product_id>')
@login_required
def view_product(product_id):
    """View product details"""
    product = Product.query.get_or_404(product_id)
    return render_template('products/view.html', product=product)


@products_bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit product (admin only)"""
    if not current_user.is_admin:
        flash('Unauthorized', 'error')
        return redirect(url_for('products.index'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.sell_price_per_pcs = request.form.get('sell_price_per_pcs', type=float)
        db.session.commit()
        flash('Product updated successfully', 'success')
        return redirect(url_for('products.view_product', product_id=product_id))
    
    return render_template('products/edit.html', product=product)


@products_bp.route('/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete product (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully', 'success')
    return redirect(url_for('products.index'))
