"""Purchases Management Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.purchase import Purchase, PurchaseItem
from app.models.product import Product, Category
from datetime import datetime

purchases_bp = Blueprint('purchases', __name__)


@purchases_bp.route('/')
@login_required
def index():
    """Display all purchases"""
    page = request.args.get('page', 1, type=int)
    purchases = Purchase.query.order_by(Purchase.purchase_date.desc()).paginate(page=page, per_page=20)
    return render_template('purchases/index.html', purchases=purchases)


@purchases_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_purchase():
    """Add new purchase with multiple items"""
    if request.method == 'POST':
        purchase_date = request.form.get('purchase_date')
        notes = request.form.get('notes')
        
        if not purchase_date:
            flash('Purchase date is required', 'error')
            return redirect(url_for('purchases.add_purchase'))
        
        # Create purchase record
        purchase = Purchase(
            purchase_date=datetime.fromisoformat(purchase_date),
            total_amount=0,
            notes=notes
        )
        db.session.add(purchase)
        db.session.flush()  # Get purchase ID without committing
        
        total_amount = 0
        product_ids = request.form.getlist('product_id[]')
        quantity_units_list = request.form.getlist('quantity_units[]')
        cost_per_unit_list = request.form.getlist('cost_per_unit[]')
        
        if not product_ids or not any(pid.strip() for pid in product_ids):
            flash('At least one product must be selected', 'error')
            db.session.rollback()
            return redirect(url_for('purchases.add_purchase'))
        
        # Process each purchase item
        for i, product_id in enumerate(product_ids):
            if not product_id.strip():
                continue  # Skip empty rows
                
            try:
                product_id = int(product_id)
                quantity_units = int(quantity_units_list[i]) if i < len(quantity_units_list) else 0
                cost_per_unit = float(cost_per_unit_list[i]) if i < len(cost_per_unit_list) else 0.0
                
                if quantity_units <= 0 or cost_per_unit <= 0:
                    flash(f'Invalid quantity or cost for item {i+1}', 'error')
                    db.session.rollback()
                    return redirect(url_for('purchases.add_purchase'))
                
                product = Product.query.get_or_404(product_id)
                quantity_pcs = quantity_units * product.quantity_per_unit
                item_total = quantity_units * cost_per_unit
                
                item = PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=product_id,
                    quantity_units=quantity_units,
                    quantity_pcs=quantity_pcs,
                    cost_per_unit=cost_per_unit,
                    item_total=item_total
                )
                
                # Update product inventory
                product.total_quantity_units += quantity_units
                product.total_quantity_pcs += quantity_pcs
                product.remaining_quantity_units += quantity_units
                product.remaining_quantity_pcs += quantity_pcs
                product.cost_per_unit = cost_per_unit  # Update with latest price
                product.cost_per_pcs = cost_per_unit / product.quantity_per_unit
                
                db.session.add(item)
                total_amount += item_total
                
            except (ValueError, TypeError) as e:
                flash(f'Invalid data for item {i+1}', 'error')
                db.session.rollback()
                return redirect(url_for('purchases.add_purchase'))
        
        purchase.total_amount = total_amount
        db.session.commit()
        
        flash(f'Purchase added successfully with {len([pid for pid in product_ids if pid.strip()])} item(s)', 'success')
        return redirect(url_for('purchases.index'))
    
    products = Product.query.all()
    return render_template('purchases/add.html', products=products)


@purchases_bp.route('/<int:purchase_id>')
@login_required
def view_purchase(purchase_id):
    """View purchase details"""
    purchase = Purchase.query.get_or_404(purchase_id)
    return render_template('purchases/view.html', purchase=purchase)
