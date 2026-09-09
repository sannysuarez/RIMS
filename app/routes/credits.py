"""Credits/Debts Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.credit import Credit, Debt
from datetime import datetime
from decimal import Decimal

credits_bp = Blueprint('credits', __name__)


@credits_bp.route('/')
@login_required
def index_credits():
    """Display all customer credits"""
    page = request.args.get('page', 1, type=int)
    credits = Credit.query.order_by(Credit.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('credits/index.html', credits=credits)


@credits_bp.route('/add-credit', methods=['GET', 'POST'])
@login_required
def add_credit():
    """Add new customer credit"""
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        customer_contact = request.form.get('customer_contact')
        total_credit_str = request.form.get('total_credit', '')
        description = request.form.get('description')
        transaction_date = request.form.get('transaction_date')

        errors = []
        if not customer_name or not customer_name.strip():
            errors.append('Customer name is required')

        try:
            total_credit = Decimal(total_credit_str)
        except Exception:
            total_credit = None
        if total_credit is None or total_credit <= 0:
            errors.append('Total credit must be greater than zero')
        if not transaction_date:
            errors.append('Credit date is required')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('credits/add_credit.html',
                                   customer_name=customer_name,
                                   customer_contact=customer_contact,
                                   total_credit=total_credit_str,
                                   description=description,
                                   transaction_date=transaction_date)

        credit = Credit(
            customer_name=customer_name.strip(),
            customer_contact=customer_contact.strip() if customer_contact else None,
            total_credit=total_credit,
            remaining_balance=total_credit,
            paid_amount=Decimal('0.00'),
            status='active'
        )

        db.session.add(credit)
        db.session.flush()

        credit_date = datetime.fromisoformat(transaction_date)
        debt = Debt(
            credit_id=credit.id,
            transaction_type='credit',
            amount=total_credit,
            description=description.strip() if description else 'Initial credit',
            transaction_date=credit_date
        )

        db.session.add(debt)
        db.session.commit()

        flash('Customer credit added successfully', 'success')
        return redirect(url_for('credits.index_credits'))

    return render_template('credits/add_credit.html')


@credits_bp.route('/<int:credit_id>/payback', methods=['GET', 'POST'])
@login_required
def add_payback(credit_id):
    """Record payback for credit"""
    credit = Credit.query.get_or_404(credit_id)
    
    if request.method == 'POST':
        amount_str = request.form.get('amount', '')
        description = request.form.get('description')
        transaction_date = request.form.get('transaction_date')

        errors = []
        try:
            amount = Decimal(amount_str)
        except Exception:
            amount = None

        if amount is None or amount <= 0:
            errors.append('Payment amount must be greater than zero')
        elif amount > credit.remaining_balance:
            errors.append('Payment amount exceeds remaining balance')

        if not transaction_date:
            errors.append('Payment date is required')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('credits/add_payback.html', credit=credit,
                                   amount=amount_str,
                                   description=description,
                                   transaction_date=transaction_date)

        payback_date = datetime.fromisoformat(transaction_date)

        debt = Debt(
            credit_id=credit_id,
            transaction_type='payback',
            amount=amount,
            description=description.strip() if description else 'Credit payback',
            transaction_date=payback_date
        )

        credit.paid_amount += amount
        credit.remaining_balance -= amount
        credit.status = 'settled' if credit.remaining_balance <= 0 else 'active'

        db.session.add(debt)
        db.session.commit()
        
        flash('Payment recorded successfully', 'success')
        return redirect(url_for('credits.index_credits'))
    
    return render_template('credits/add_payback.html', credit=credit)


@credits_bp.route('/<int:credit_id>')
@login_required
def view_credit(credit_id):
    """View credit details"""
    credit = Credit.query.get_or_404(credit_id)
    debts = Debt.query.filter_by(credit_id=credit_id).order_by(Debt.transaction_date.desc()).all()
    return render_template('credits/view.html', credit=credit, debts=debts)
