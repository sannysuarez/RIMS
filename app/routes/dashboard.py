"""Dashboard Routes"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app import db
from app.models.product import Product, Category
from app.models.purchase import Purchase
from app.models.expense import Expense
from app.models.credit import Credit, Debt
from app.models.mdc import MDCReport
from app.models.mdc_product_record import MDCProductRecord
from app.models.ruf_yog import RufYogPurchase
from app.utils.helpers import calculate_liquidity_summary, format_currency
from sqlalchemy import func, desc
from datetime import datetime, timedelta


dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard with analytics (server-side calculations)"""

    # Get all data for comprehensive calculations
    products = Product.query.all()
    purchases = Purchase.query.all()
    credits = Credit.query.all()
    debts = Debt.query.all()
    latest_mdc = MDCReport.query.order_by(MDCReport.report_date.desc()).first()
    cash_input_amount = float(latest_mdc.cash_input) if latest_mdc else 0.0
    cycle_start = latest_mdc.report_date if latest_mdc else None

    # Expenses are based purely on MDC cycle boundaries (not monthly)
    if cycle_start:
        # Get expenses on or after the latest MDC was created (belongs to current cycle)
        current_cycle_expenses = Expense.query.filter(Expense.expense_date >= cycle_start).all()
    else:
        # If no MDC exists yet, get all expenses
        current_cycle_expenses = Expense.query.all()

    # CRITICAL: Calculate liquidity correctly considering MDC snapshots
    # If we have a latest MDC, use its snapshot as the baseline, then adjust for current cycle
    if latest_mdc:
        # Start with the liquidity from the latest MDC (includes all past expenses deducted)
        base_liquidity = float(latest_mdc.total_liquidity)
        # Add current cycle expenses (deducted)
        current_expenses_total = sum(float(e.amount) for e in current_cycle_expenses)

        # Include credit/debt transactions that happened after the latest MDC so they show immediately
        debts_since_mdc = Debt.query.filter(Debt.transaction_date >= cycle_start).all()
        new_credits_total = sum(float(d.amount) for d in debts_since_mdc if d.transaction_type == 'credit')
        new_paybacks_total = sum(float(d.amount) for d in debts_since_mdc if d.transaction_type == 'payback')

        # Net new debts added since last MDC (credits increase debts, paybacks decrease them)
        net_new_debts = new_credits_total - new_paybacks_total

        # Current total liquidity = baseline - current expenses - net new debts
        total_liquidity = base_liquidity - current_expenses_total - net_new_debts

        # Build liquidity breakdown for display (include adjustments from current cycle)
        liquidity_data = {
            'product_value': float(latest_mdc.product_value or 0),
            'total_purchases': cash_input_amount,
            'total_cash_input': cash_input_amount,
            'total_expenses': current_expenses_total,  # Only current cycle
            'total_debts': float(latest_mdc.total_debts or 0) + new_credits_total - new_paybacks_total,
            'total_paybacks': float(latest_mdc.total_paybacks or 0) + new_paybacks_total,
            'total_liquidity': total_liquidity
        }
    else:
        # No MDC yet: simple calculation with all expenses so far
        current_cycle_expenses = current_cycle_expenses  # All expenses
        current_expenses_total = sum(float(e.amount) for e in current_cycle_expenses)
        
        liquidity_data = {
            'product_value': sum(p.calculate_liquidity_value() for p in products),
            'total_purchases': 0,
            'total_cash_input': 0,
            'total_expenses': current_expenses_total,
            'total_debts': sum(float(c.remaining_balance) for c in credits),
            'total_paybacks': 0,
            'total_liquidity': sum(p.calculate_liquidity_value() for p in products) - current_expenses_total - sum(
                float(c.remaining_balance) for c in credits
            )
        }

    # Calculate total profit from all MDC cycles (immutable, based on recorded prices)
    all_mdc_product_records = MDCProductRecord.query.all()
    total_profit = sum(
        float((pr.sell_price_per_pcs_at_record - pr.cost_per_pcs_at_record) * pr.sold_quantity_pcs)
        for pr in all_mdc_product_records
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

    # 5. Ruf-Yog Corner sales (from current MDC cycle)
    ruf_yog_sales = db.session.query(
        func.sum(RufYogPurchase.quantity)
    ).filter(RufYogPurchase.transaction_date >= cycle_start).scalar() or 0 if cycle_start else db.session.query(func.sum(RufYogPurchase.quantity)).scalar() or 0

    # 6. MDC Cycle Sales Trends - get all MDC cycles and their product sales (LIFO order)
    all_mdc_reports = MDCReport.query.order_by(MDCReport.report_date.desc()).all()
    total_mdc_count = len(all_mdc_reports)
    
    mdc_cycle_data = []
    for idx, mdc in enumerate(all_mdc_reports):
        # Get all product records for this MDC cycle
        product_records = MDCProductRecord.query.filter_by(mdc_report_id=mdc.id).all()
        
        # Calculate actual cycle number (1 being the oldest, displayed at bottom)
        actual_cycle_number = total_mdc_count - idx
        
        total_sold = sum(pr.sold_quantity_pcs for pr in product_records)
        total_remaining = sum(pr.remaining_quantity_pcs for pr in product_records)
        
        # Calculate profit from sold units in this cycle using recorded prices
        cycle_profit = sum(
            float((pr.sell_price_per_pcs_at_record - pr.cost_per_pcs_at_record) * pr.sold_quantity_pcs)
            for pr in product_records
        )
        # Determine expense window: from this mdc.report_date up to (but not including) the next older mdc
        next_older_mdc = all_mdc_reports[idx+1] if (idx + 1) < total_mdc_count else None
        if next_older_mdc:
            expenses_in_cycle = Expense.query.filter(
                Expense.expense_date >= mdc.report_date,
                Expense.expense_date < next_older_mdc.report_date
            ).all()
            debts_in_cycle = Debt.query.filter(
                Debt.transaction_date >= mdc.report_date,
                Debt.transaction_date < next_older_mdc.report_date
            ).all()
        else:
            expenses_in_cycle = Expense.query.filter(Expense.expense_date >= mdc.report_date).all()
            debts_in_cycle = Debt.query.filter(Debt.transaction_date >= mdc.report_date).all()

        # Product inventory value for this cycle based on recorded prices and remaining qty
        # Prefer stored immutable snapshots on the MDC report if available (saved when the cycle was created)
        try:
            has_snapshot = any([
                getattr(mdc, 'product_value', None) is not None,
                getattr(mdc, 'total_liquidity', None) is not None,
                getattr(mdc, 'cycle_profit', None) is not None
            ])
        except Exception:
            has_snapshot = False

        if has_snapshot and (float(getattr(mdc, 'product_value', 0)) or float(getattr(mdc, 'total_liquidity', 0)) or float(getattr(mdc, 'cycle_profit', 0))):
            # Use stored snapshot fields to ensure immutability of past cycles
            product_value_cycle = float(getattr(mdc, 'product_value', 0) or 0)
            cycle_total_cash_input = float(mdc.cash_input)
            cycle_total_expenses = float(getattr(mdc, 'total_expenses', 0) or 0)
            cycle_total_debts = float(getattr(mdc, 'total_debts', 0) or 0)
            cycle_total_paybacks = float(getattr(mdc, 'total_paybacks', 0) or 0)
            cycle_total_liquidity = float(getattr(mdc, 'total_liquidity', 0) or 0)
            # prefer stored cycle profit
            cycle_profit = float(getattr(mdc, 'cycle_profit', 0) or 0)
        else:
            # Recompute from product records and expenses if snapshot missing
            product_value_cycle = sum(float(pr.remaining_quantity_pcs) * float(pr.cost_per_pcs_at_record) for pr in product_records)

            # Outstanding debts snapshot (credits created up to this cycle)
            outstanding_debts_total = db.session.query(func.coalesce(func.sum(Credit.remaining_balance), 0)).filter(Credit.created_at <= mdc.report_date).scalar() or 0.0

            # Cycle-level liquidity breakdown (mirrors calculate_liquidity_summary but using cycle snapshots)
            cycle_total_cash_input = float(mdc.cash_input)
            cycle_total_expenses = sum(float(e.amount) for e in expenses_in_cycle)
            cycle_total_debts = float(outstanding_debts_total)
            cycle_total_paybacks = sum(float(d.amount) for d in debts_in_cycle if d.transaction_type == 'payback')

            cycle_total_liquidity = product_value_cycle + cycle_total_cash_input - cycle_total_expenses - cycle_total_debts

        mdc_cycle_data.append({
            'cycle_number': actual_cycle_number,
            'date': mdc.report_date.strftime('%b %d, %Y'),
            'timestamp': mdc.report_date.isoformat(),
            'total_sold': total_sold,
            'total_remaining': total_remaining,
            'cash_input': float(mdc.cash_input),
            'cycle_profit': cycle_profit,
            'total_liquidity': cycle_total_liquidity,
            'liquidity_breakdown': {
                'product_value': product_value_cycle,
                'total_cash_input': cycle_total_cash_input,
                'total_expenses': cycle_total_expenses,
                'total_debts': cycle_total_debts,
                'total_paybacks': cycle_total_paybacks,
                'total_liquidity': cycle_total_liquidity
            },
            'expenses_total': cycle_total_expenses,
            'expenses': [e.to_dict() for e in expenses_in_cycle],
            'outstanding_debts': cycle_total_debts,
            'product_details': [
                {
                    'product_name': pr.product.name,
                    'sold': pr.sold_quantity_pcs,
                    'remaining': pr.remaining_quantity_pcs
                }
                for pr in product_records
            ]
        })

    # Only show up to 5 recent cycles on the dashboard; provide total count for lookup/navigation
    displayed_mdc_cycles = mdc_cycle_data[:5]

    # Current MDC cycle expenses/withdrawals (for prominent display on dashboard)
    current_expenses_sorted = sorted(current_cycle_expenses, key=lambda x: x.expense_date, reverse=True)
    current_cycle_expenses_list = [e.to_dict() for e in current_expenses_sorted]

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
        'mdc_cycle_data': displayed_mdc_cycles,
        'mdc_total_count': total_mdc_count,
        'current_cycle_expenses': current_cycle_expenses_list,
        'current_cycle_expenses_total': liquidity_data['total_expenses']
    }

    return render_template('dashboard/index.html', analytics=analytics)
