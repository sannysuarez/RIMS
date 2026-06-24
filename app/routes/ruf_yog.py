"""Ruf-Yog Corner Routes - Independent Mini Application"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.ruf_yog import (
    RufYogProduct, RufYogPurchase, RufYogMDCReport,
    RufYogExpense, RufYogCredit, RufYogDebt
)
from datetime import datetime
from decimal import Decimal
from app.utils.helpers import admin_required, format_currency
import uuid

ruf_yog_bp = Blueprint('ruf_yog', __name__)


@ruf_yog_bp.route('/')
@login_required
def index():
    """Ruf-Yog Corner dashboard"""
    latest_mdc = RufYogMDCReport.query.order_by(RufYogMDCReport.report_date.desc()).first()
    cycle_start = latest_mdc.report_date if latest_mdc else None

    products = RufYogProduct.query.order_by(RufYogProduct.name).all()
    recent_purchases = RufYogPurchase.query.order_by(RufYogPurchase.transaction_date.desc()).limit(8).all()
    recent_expenses = RufYogExpense.query.order_by(RufYogExpense.expense_date.desc()).limit(6).all()
    active_credits = RufYogCredit.query.filter(RufYogCredit.remaining_balance > 0).order_by(RufYogCredit.created_at.desc()).limit(6).all()

    if cycle_start:
        cycle_expenses = RufYogExpense.query.filter(RufYogExpense.expense_date >= cycle_start).all()
        cycle_purchases = RufYogPurchase.query.filter(RufYogPurchase.transaction_date >= cycle_start).all()
    else:
        cycle_expenses = RufYogExpense.query.all()
        cycle_purchases = RufYogPurchase.query.all()

    total_expenses = sum(float(expense.amount) for expense in cycle_expenses)
    total_purchase_cost = sum(float(purchase.total_amount) for purchase in cycle_purchases)
    total_remaining_credit = sum(float(credit.remaining_balance) for credit in RufYogCredit.query.all())
    total_paid_credit = sum(float(credit.paid_amount) for credit in RufYogCredit.query.all())
    total_product_profit = sum(
        float((product.sell_price_per_unit - product.cost_per_unit) * product.sold_quantity)
        for product in products
    )

    return render_template(
        'ruf_yog/index.html',
        products=products,
        latest_mdc=latest_mdc,
        recent_purchases=recent_purchases,
        recent_expenses=recent_expenses,
        active_credits=active_credits,
        total_expenses=total_expenses,
        total_purchase_cost=total_purchase_cost,
        total_remaining_credit=total_remaining_credit,
        total_paid_credit=total_paid_credit,
        total_product_profit=total_product_profit,
        cycle_start=cycle_start,
        format_currency=format_currency
    )


@ruf_yog_bp.route('/products')
@login_required
def products():
    """List Ruf-Yog products"""
    page = request.args.get('page', 1, type=int)
    products = RufYogProduct.query.order_by(RufYogProduct.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('ruf_yog/products.html', products=products)


@ruf_yog_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Add new Ruf-Yog product"""
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        cost_per_unit = request.form.get('cost_per_unit', type=float)
        sell_price_per_unit = request.form.get('sell_price_per_unit', type=float)
        quantity = request.form.get('quantity', type=int)

        if not product_name or cost_per_unit is None or sell_price_per_unit is None or quantity is None:
            flash('All fields are required', 'danger')
            return render_template('ruf_yog/add_product.html', product_name=product_name,
                                   cost_per_unit=cost_per_unit,
                                   sell_price_per_unit=sell_price_per_unit, quantity=quantity)
        
        if quantity <= 0:
            flash('Quantity must be a positive number', 'danger')
            return render_template('ruf_yog/add_product.html', product_name=product_name,
                                   cost_per_unit=cost_per_unit,
                                   sell_price_per_unit=sell_price_per_unit, quantity=quantity)
        
        if cost_per_unit <= 0 or sell_price_per_unit <= 0:
            flash('Cost and sell price must be positive numbers', 'danger')
            return render_template('ruf_yog/add_product.html', product_name=product_name,
                                   cost_per_unit=cost_per_unit,
                                   sell_price_per_unit=sell_price_per_unit, quantity=quantity)

        unique_id = str(uuid.uuid4())[:8].upper()

        product = RufYogProduct(
            unique_id=unique_id,
            name=product_name.strip(),
            cost_per_unit=cost_per_unit,
            sell_price_per_unit=sell_price_per_unit,
            total_quantity=quantity,
            remaining_quantity=quantity
        )

        db.session.add(product)
        db.session.commit()

        flash('Ruf-Yog product added successfully', 'success')
        return redirect(url_for('ruf_yog.products'))

    return render_template('ruf_yog/add_product.html')


@ruf_yog_bp.route('/products/<int:product_id>')
@login_required
def view_product(product_id):
    """View Ruf-Yog product details"""
    product = RufYogProduct.query.get_or_404(product_id)
    purchases = RufYogPurchase.query.filter_by(product_id=product_id).order_by(
        RufYogPurchase.transaction_date.desc()
    ).all()
    return render_template('ruf_yog/view.html', product=product, purchases=purchases)


@ruf_yog_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit Ruf-Yog product (admin only)"""
    if not current_user.is_admin:
        flash('Unauthorized', 'danger')
        return redirect(url_for('ruf_yog.products'))

    product = RufYogProduct.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form.get('name', product.name)
        product.cost_per_unit = request.form.get('cost_per_unit', type=float) or product.cost_per_unit
        product.sell_price_per_unit = request.form.get('sell_price_per_unit', type=float) or product.sell_price_per_unit
        db.session.commit()
        flash('Product updated successfully', 'success')
        return redirect(url_for('ruf_yog.view_product', product_id=product_id))

    return render_template('ruf_yog/edit.html', product=product)


@ruf_yog_bp.route('/purchases')
@login_required
def purchases():
    """List Ruf-Yog stock purchases"""
    page = request.args.get('page', 1, type=int)
    purchases = RufYogPurchase.query.order_by(RufYogPurchase.transaction_date.desc()).paginate(page=page, per_page=20)
    return render_template('ruf_yog/purchases.html', purchases=purchases)


@ruf_yog_bp.route('/purchases/add', methods=['GET', 'POST'])
@login_required
def add_purchase():
    """Record a new Ruf-Yog stock purchase"""
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        quantity = request.form.get('quantity', type=int)
        unit_price = request.form.get('unit_price', type=float)

        product = RufYogProduct.query.get_or_404(product_id)
        if product is None or quantity is None or unit_price is None:
            flash('All fields are required', 'danger')
            return redirect(url_for('ruf_yog.add_purchase'))

        total_amount = quantity * unit_price
        purchase = RufYogPurchase(
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            total_amount=total_amount,
            transaction_type='purchase',
            transaction_date=datetime.now()
        )

        product.total_quantity += quantity
        product.remaining_quantity += quantity

        db.session.add(purchase)
        db.session.commit()

        flash('Purchase recorded successfully', 'success')
        return redirect(url_for('ruf_yog.purchases'))

    products = RufYogProduct.query.order_by(RufYogProduct.name).all()
    return render_template('ruf_yog/add_purchase.html', products=products)


@ruf_yog_bp.route('/mdc', methods=['GET', 'POST'])
@login_required
@admin_required
def mdc():
    """Independent Ruf-Yog MDC report"""
    products = RufYogProduct.query.order_by(RufYogProduct.name).all()
    latest_mdc = RufYogMDCReport.query.order_by(RufYogMDCReport.report_date.desc()).first()

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
                remaining_quantity = int(remaining_value_raw)
            except ValueError:
                errors.append(f'Invalid remaining quantity for {product.name}')
                continue
            if remaining_quantity < 0 or remaining_quantity > product.total_quantity:
                errors.append(f'Remaining quantity for {product.name} must be between 0 and {product.total_quantity}')
                continue
            product.remaining_quantity = remaining_quantity
            product.sold_quantity = max(product.total_quantity - remaining_quantity, 0)

        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('ruf_yog.mdc'))

        mdc_report = RufYogMDCReport(cash_input=cash_input_value, report_date=datetime.now())
        db.session.add(mdc_report)
        db.session.commit()

        flash('Ruf-Yog MDC report saved successfully', 'success')
        return redirect(url_for('ruf_yog.mdc'))

    return render_template('ruf_yog/mdc.html', products=products, latest_mdc=latest_mdc)


@ruf_yog_bp.route('/expenses')
@login_required
def expenses():
    """List Ruf-Yog expenses"""
    page = request.args.get('page', 1, type=int)
    expenses = RufYogExpense.query.order_by(RufYogExpense.expense_date.desc()).paginate(page=page, per_page=20)
    return render_template('ruf_yog/expenses.html', expenses=expenses)


@ruf_yog_bp.route('/expenses/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    """Record a Ruf-Yog withdrawal or expense"""
    if request.method == 'POST':
        beneficiary_name = request.form.get('beneficiary_name')
        description = request.form.get('description')
        amount = request.form.get('amount', type=float)
        expense_date = request.form.get('expense_date')

        if not beneficiary_name or amount is None or amount <= 0 or not expense_date:
            flash('All fields are required and amount must be positive', 'danger')
            return render_template('ruf_yog/add_expense.html', beneficiary_name=beneficiary_name,
                                   description=description, amount=amount, expense_date=expense_date)

        expense = RufYogExpense(
            beneficiary_name=beneficiary_name.strip(),
            description=description.strip() if description else None,
            amount=amount,
            expense_date=datetime.fromisoformat(expense_date)
        )

        db.session.add(expense)
        db.session.commit()

        flash('Expense recorded successfully', 'success')
        return redirect(url_for('ruf_yog.expenses'))

    return render_template('ruf_yog/add_expense.html')


@ruf_yog_bp.route('/expenses/<int:expense_id>')
@login_required
def view_expense(expense_id):
    """View Ruf-Yog expense details"""
    expense = RufYogExpense.query.get_or_404(expense_id)
    return render_template('ruf_yog/view_expense.html', expense=expense)


@ruf_yog_bp.route('/credits')
@login_required
def credits():
    """List Ruf-Yog customer credit accounts"""
    page = request.args.get('page', 1, type=int)
    credits = RufYogCredit.query.order_by(RufYogCredit.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('ruf_yog/credits.html', credits=credits)


@ruf_yog_bp.route('/credits/add', methods=['GET', 'POST'])
@login_required
def add_credit():
    """Add new Ruf-Yog credit account"""
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        customer_contact = request.form.get('customer_contact')
        total_credit = request.form.get('total_credit', type=float)
        description = request.form.get('description')
        transaction_date = request.form.get('transaction_date')

        if not customer_name or total_credit is None or total_credit <= 0 or not transaction_date:
            flash('All fields are required and credit amount must be positive', 'danger')
            return render_template('ruf_yog/add_credit.html', customer_name=customer_name,
                                   customer_contact=customer_contact, total_credit=total_credit,
                                   description=description, transaction_date=transaction_date)

        credit = RufYogCredit(
            customer_name=customer_name.strip(),
            customer_contact=customer_contact.strip() if customer_contact else None,
            total_credit=total_credit,
            remaining_balance=total_credit,
            paid_amount=0.0,
            status='active'
        )

        db.session.add(credit)
        db.session.flush()

        debt = RufYogDebt(
            credit_id=credit.id,
            transaction_type='credit',
            amount=total_credit,
            description=description.strip() if description else 'Initial credit',
            transaction_date=datetime.fromisoformat(transaction_date)
        )

        db.session.add(debt)
        db.session.commit()

        flash('Customer credit added successfully', 'success')
        return redirect(url_for('ruf_yog.credits'))

    return render_template('ruf_yog/add_credit.html')


@ruf_yog_bp.route('/credits/<int:credit_id>/payback', methods=['GET', 'POST'])
@login_required
def add_payback(credit_id):
    """Record payback for Ruf-Yog credit"""
    credit = RufYogCredit.query.get_or_404(credit_id)
    if request.method == 'POST':
        amount = request.form.get('amount', type=float)
        description = request.form.get('description')
        transaction_date = request.form.get('transaction_date')

        if amount is None or amount <= 0 or amount > float(credit.remaining_balance) or not transaction_date:
            flash('Valid payment amount and date are required', 'danger')
            return render_template('ruf_yog/add_payback.html', credit=credit,
                                   amount=amount, description=description,
                                   transaction_date=transaction_date)

        debt = RufYogDebt(
            credit_id=credit_id,
            transaction_type='payback',
            amount=amount,
            description=description.strip() if description else 'Credit payback',
            transaction_date=datetime.fromisoformat(transaction_date)
        )

        credit.paid_amount += amount
        credit.remaining_balance -= amount
        credit.status = 'settled' if credit.remaining_balance <= 0 else 'active'

        db.session.add(debt)
        db.session.commit()

        flash('Payback recorded successfully', 'success')
        return redirect(url_for('ruf_yog.credits'))

    return render_template('ruf_yog/add_payback.html', credit=credit)


@ruf_yog_bp.route('/credits/<int:credit_id>')
@login_required
def view_credit(credit_id):
    """View Ruf-Yog credit details"""
    credit = RufYogCredit.query.get_or_404(credit_id)
    debts = RufYogDebt.query.filter_by(credit_id=credit_id).order_by(RufYogDebt.transaction_date.desc()).all()
    return render_template('ruf_yog/view_credit.html', credit=credit, debts=debts)
