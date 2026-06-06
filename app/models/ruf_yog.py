"""Ruf-Yog Corner Products and Purchases"""
from app import db
from datetime import datetime
from decimal import Decimal


class RufYogProduct(db.Model):
    """Ruf-Yog Corner product (special products section)"""
    __tablename__ = 'ruf_yog_products'
    
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    
    unit_type = db.Column(db.String(50), nullable=False)  # unit, pack, etc.
    cost_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    sell_price_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    
    total_quantity = db.Column(db.Integer, default=0)
    remaining_quantity = db.Column(db.Integer, default=0)
    sold_quantity = db.Column(db.Integer, default=0)
    
    is_admin_edit_only = db.Column(db.Boolean, default=False)  # Restrict edits to admin
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    purchases = db.relationship('RufYogPurchase', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<RufYogProduct {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'unique_id': self.unique_id,
            'name': self.name,
            'unit_type': self.unit_type,
            'cost_per_unit': float(self.cost_per_unit),
            'sell_price_per_unit': float(self.sell_price_per_unit),
            'remaining_quantity': self.remaining_quantity,
            'sold_quantity': self.sold_quantity
        }


class RufYogPurchase(db.Model):
    """Ruf-Yog Corner purchase/sale transaction"""
    __tablename__ = 'ruf_yog_purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('ruf_yog_products.id'), nullable=False, index=True)
    
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    transaction_type = db.Column(db.String(20), default='purchase')  # purchase, sale
    
    transaction_date = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<RufYogPurchase {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_name': self.product.name if self.product else None,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total_amount': float(self.total_amount),
            'transaction_type': self.transaction_type,
            'transaction_date': self.transaction_date.isoformat()
        }
