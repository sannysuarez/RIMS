"""Miscellaneous Products and Purchases"""
from app import db
from datetime import datetime
from decimal import Decimal


class MiscProduct(db.Model):
    """Miscellaneous product (outside main inventory)"""
    __tablename__ = 'misc_products'
    
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    
    cost_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    sell_price_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    
    total_quantity = db.Column(db.Integer, default=0)
    remaining_quantity = db.Column(db.Integer, default=0)
    sold_quantity = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    purchases = db.relationship('MiscPurchase', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<MiscProduct {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'unique_id': self.unique_id,
            'name': self.name,
            'cost_per_unit': float(self.cost_per_unit),
            'sell_price_per_unit': float(self.sell_price_per_unit),
            'remaining_quantity': self.remaining_quantity,
            'sold_quantity': self.sold_quantity
        }


class MiscPurchase(db.Model):
    """Miscellaneous purchase transaction"""
    __tablename__ = 'misc_purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('misc_products.id'), nullable=False, index=True)
    
    quantity = db.Column(db.Integer, nullable=False)
    cost_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    
    purchase_date = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<MiscPurchase {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_name': self.product.name if self.product else None,
            'quantity': self.quantity,
            'cost_per_unit': float(self.cost_per_unit),
            'total_amount': float(self.total_amount)
        }
