"""Dashboard Routes"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app import db
from app.models.product import Product, Category
from app.models.purchase import Purchase
from app.models.expense import Expense
from app.models.credit import Credit, Debt
from app.models.mdc import MDCReport
from app.models.ruf_yog import RufYogPurchase
from app.utils.helpers import calculate_liquidity_summary, format_currency
from sqlalchemy import func, desc
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard with analytics (server-side calculations)"""

    # Calculate date range (current month)
    today = datetime.now()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Get all data for comprehensive calculations
    products = Product.query.all()
    purchases = Purchase.query.all()
    credits = Credit.query.all()
    debts = Debt.query.all()
    latest_mdc = MDCReport.query.order_by(MDCReport.report_date.desc()).first()
    cash_input_amount = float(latest_mdc.cash_input) if latest_mdc else 0.0
    cycle_start = latest_mdc.report_date if latest_mdc else None

    if cycle_start:
        expenses = Expense.query.filter(Expense.expense_date >= cycle_start).all()
    else:
        expenses = Expense.query.all()

    # Use server-side liquidity calculation with the current MDC cycle expenses
    liquidity_data = calculate_liquidity_summary(
        products, purchases, expenses, credits, debts,
        cash_input=cash_input_amount
    )

    total_profit = sum(
        float((p.sell_price_per_pcs - p.cost_per_pcs) * p.sold_quantity_pcs)
        for p in products
    )

    # 2. Debts Analysis
    top_5_debtors = Credit.query.filter(Credit.remaining_balance > 0).order_by(
        desc(Credit.remaining_balance)
    ).limit(5).all()

    # 3. Top 10 Best Selling Products
    top_products = Product.query.order_by(desc(Product.sold_quantity_pcs)).limit(10).all()

    # 4. Sales by Category
    category_sales = db.session.query(
        Category.name,
        func.sum(Product.sold_quantity_pcs)
    ).join(Product).group_by(Category.name).all()

    # 5. Ruf-Yog Corner monthly sales
    ruf_yog_sales = db.session.query(
        func.sum(RufYogPurchase.quantity)
    ).filter(RufYogPurchase.transaction_date >= month_start).scalar() or 0

    # 6. Monthly trends (last 12 months)
    monthly_data = []
    for i in range(11, -1, -1):
        month = today - timedelta(days=30*i)
        month_start_calc = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end_calc = (month_start_calc + timedelta(days=32)).replace(day=1)

        effective_start = month_start_calc
        if cycle_start and month_end_calc > cycle_start:
            effective_start = max(month_start_calc, cycle_start)

        monthly_purchases = float(Purchase.query.filter(
            Purchase.purchase_date >= effective_start,
            Purchase.purchase_date < month_end_calc
        ).with_entities(func.sum(Purchase.total_amount)).scalar() or 0)

        monthly_expenses = float(Expense.query.filter(
            Expense.expense_date >= effective_start,
            Expense.expense_date < month_end_calc
        ).with_entities(func.sum(Expense.amount)).scalar() or 0)

        monthly_data.append({
            'month': month.strftime('%B'),
            'purchases': monthly_purchases,
            'expenses': monthly_expenses
        })

    analytics = {
        'total_liquidity': liquidity_data['total_liquidity'],
        'total_profit': total_profit,
        'last_cash_input': cash_input_amount,
        'last_mdc_date': latest_mdc.report_date if latest_mdc else None,
        'liquidity_breakdown': liquidity_data,
        'top_5_debtors': [d.to_dict() for d in top_5_debtors],
        'top_products': [p.to_dict() for p in top_products],
        'category_sales': [{'category': c[0], 'quantity': c[1] or 0} for c in category_sales],
        'ruf_yog_sales': ruf_yog_sales,
        'monthly_data': monthly_data
    }

    return render_template('dashboard/index.html', analytics=analytics)
