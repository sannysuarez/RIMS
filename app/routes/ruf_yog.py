"""Ruf-Yog Corner Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.ruf_yog import RufYogProduct, RufYogPurchase
from datetime import datetime
import uuid

ruf_yog_bp = Blueprint('ruf_yog', __name__)


@ruf_yog_bp.route('/')
@login_required
def index():
    """Ruf-Yog Corner products"""
    page = request.args.get('page', 1, type=int)
    products = RufYogProduct.query.order_by(RufYogProduct.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('ruf_yog/index.html', products=products)


@ruf_yog_bp.route('/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    """Add new Ruf-Yog product"""
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        unit_type = request.form.get('unit_type')
        cost_per_unit = request.form.get('cost_per_unit', type=float)
        sell_price_per_unit = request.form.get('sell_price_per_unit', type=float)
        quantity = request.form.get('quantity', type=int)
        
        unique_id = str(uuid.uuid4())[:8].upper()
        
        product = RufYogProduct(
            unique_id=unique_id,
            name=product_name,
            unit_type=unit_type,
            cost_per_unit=cost_per_unit,
            sell_price_per_unit=sell_price_per_unit,
            total_quantity=quantity,
            remaining_quantity=quantity
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Ruf-Yog product added successfully', 'success')
        return redirect(url_for('ruf_yog.index'))
    
    return render_template('ruf_yog/add_product.html')


@ruf_yog_bp.route('/add-purchase', methods=['GET', 'POST'])
@login_required
def add_purchase():
    """Add purchase to existing Ruf-Yog product"""
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        quantity = request.form.get('quantity', type=int)
        unit_price = request.form.get('unit_price', type=float)
        
        product = RufYogProduct.query.get_or_404(product_id)
        total_amount = quantity * unit_price
        
        purchase = RufYogPurchase(
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            total_amount=total_amount,
            transaction_date=datetime.now()
        )
        
        product.total_quantity += quantity
        product.remaining_quantity += quantity
        
        db.session.add(purchase)
        db.session.commit()
        
        flash('Purchase recorded successfully', 'success')
        return redirect(url_for('ruf_yog.index'))
    
    products = RufYogProduct.query.all()
    return render_template('ruf_yog/add_purchase.html', products=products)


@ruf_yog_bp.route('/<int:product_id>')
@login_required
def view_product(product_id):
    """View Ruf-Yog product details"""
    product = RufYogProduct.query.get_or_404(product_id)
    purchases = RufYogPurchase.query.filter_by(product_id=product_id).order_by(
        RufYogPurchase.transaction_date.desc()
    ).all()
    return render_template('ruf_yog/view.html', product=product, purchases=purchases)


@ruf_yog_bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit Ruf-Yog product (admin only)"""
    if not current_user.is_admin:
        flash('Unauthorized', 'error')
        return redirect(url_for('ruf_yog.index'))
    
    product = RufYogProduct.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name', product.name)
        product.cost_per_unit = request.form.get('cost_per_unit', type=float) or product.cost_per_unit
        product.sell_price_per_unit = request.form.get('sell_price_per_unit', type=float) or product.sell_price_per_unit
        db.session.commit()
        flash('Product updated successfully', 'success')
        return redirect(url_for('ruf_yog.view_product', product_id=product_id))
    
    return render_template('ruf_yog/edit.html', product=product)
