"""Miscellaneous Products Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.misc import MiscProduct, MiscPurchase
from datetime import datetime
import uuid

misc_bp = Blueprint('misc', __name__)


@misc_bp.route('/')
@login_required
def index():
    """Display miscellaneous products"""
    page = request.args.get('page', 1, type=int)
    products = MiscProduct.query.order_by(MiscProduct.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('misc/index.html', products=products)


@misc_bp.route('/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    """Add new miscellaneous product"""
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        cost_per_unit = request.form.get('cost_per_unit', type=float)
        sell_price_per_unit = request.form.get('sell_price_per_unit', type=float)
        quantity = request.form.get('quantity', type=int)
        
        unique_id = str(uuid.uuid4())[:8].upper()
        
        product = MiscProduct(
            unique_id=unique_id,
            name=product_name,
            cost_per_unit=cost_per_unit,
            sell_price_per_unit=sell_price_per_unit,
            total_quantity=quantity,
            remaining_quantity=quantity
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Miscellaneous product added successfully', 'success')
        return redirect(url_for('misc.index'))
    
    return render_template('misc/add_product.html')


@misc_bp.route('/add-purchase', methods=['GET', 'POST'])
@login_required
def add_purchase():
    """Add purchase to miscellaneous product"""
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        quantity = request.form.get('quantity', type=int)
        cost_per_unit = request.form.get('cost_per_unit', type=float)
        
        product = MiscProduct.query.get_or_404(product_id)
        total_amount = quantity * cost_per_unit
        
        purchase = MiscPurchase(
            product_id=product_id,
            quantity=quantity,
            cost_per_unit=cost_per_unit,
            total_amount=total_amount,
            purchase_date=datetime.now()
        )
        
        product.total_quantity += quantity
        product.remaining_quantity += quantity
        
        db.session.add(purchase)
        db.session.commit()
        
        flash('Purchase recorded successfully', 'success')
        return redirect(url_for('misc.index'))
    
    products = MiscProduct.query.all()
    return render_template('misc/add_purchase.html', products=products)


@misc_bp.route('/<int:product_id>')
@login_required
def view_product(product_id):
    """View miscellaneous product details"""
    product = MiscProduct.query.get_or_404(product_id)
    purchases = MiscPurchase.query.filter_by(product_id=product_id).order_by(
        MiscPurchase.purchase_date.desc()
    ).all()
    return render_template('misc/view.html', product=product, purchases=purchases)
