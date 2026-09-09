"""Expenses/Withdrawals Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.expense import Expense
from datetime import datetime

expenses_bp = Blueprint('expenses', __name__)


@expenses_bp.route('/')
@login_required
def index():
    """Display all expenses"""
    page = request.args.get('page', 1, type=int)
    expenses = Expense.query.order_by(Expense.expense_date.desc()).paginate(page=page, per_page=20)
    return render_template('expenses/index.html', expenses=expenses)


@expenses_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    """Add new expense/withdrawal"""
    if request.method == 'POST':
        beneficiary_name = request.form.get('beneficiary_name')
        beneficiary_address = request.form.get('beneficiary_address')
        amount = request.form.get('amount', type=float)
        description = request.form.get('description')
        expense_date = request.form.get('expense_date')

        errors = []
        if not beneficiary_name or not beneficiary_name.strip():
            errors.append('Beneficiary name is required')
        if amount is None or amount <= 0:
            errors.append('Amount must be greater than zero')
        if not expense_date:
            errors.append('Expense date is required')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('expenses/add.html',
                                   beneficiary_name=beneficiary_name,
                                   beneficiary_address=beneficiary_address,
                                   amount=request.form.get('amount', ''),
                                   description=description,
                                   expense_date=expense_date)

        expense = Expense(
            beneficiary_name=beneficiary_name.strip(),
            beneficiary_address=beneficiary_address.strip() if beneficiary_address else None,
            amount=amount,
            description=description.strip() if description else None,
            expense_date=datetime.fromisoformat(expense_date)
        )

        db.session.add(expense)
        db.session.commit()

        flash('Expense recorded successfully', 'success')
        return redirect(url_for('expenses.index'))

    return render_template('expenses/add.html')


@expenses_bp.route('/<int:expense_id>')
@login_required
def view_expense(expense_id):
    """View expense details"""
    expense = Expense.query.get_or_404(expense_id)
    return render_template('expenses/view.html', expense=expense)
