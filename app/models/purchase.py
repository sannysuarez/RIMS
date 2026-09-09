"""Purchase and PurchaseItem Models"""
from app import db
from datetime import datetime
from decimal import Decimal


class Purchase(db.Model):
    """Purchase transaction record"""
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_date = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    invoice_path = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    items = db.relationship('PurchaseItem', backref='purchase', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Purchase {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'purchase_date': self.purchase_date.isoformat(),
            'total_amount': float(self.total_amount),
            'items': [item.to_dict() for item in self.items]
        }


class PurchaseItem(db.Model):
    """Individual item in a purchase"""
    __tablename__ = 'purchase_items'
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    
    quantity_units = db.Column(db.Integer, nullable=False)  # Number of packs/cartons/pcs
    quantity_pcs = db.Column(db.Integer, nullable=False)  # Total pieces: quantity_units * quantity_per_unit
    cost_per_unit = db.Column(db.Numeric(10, 2), nullable=False)  # Can differ from original product cost
    item_total = db.Column(db.Numeric(12, 2), nullable=False)  # quantity_units * cost_per_unit
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PurchaseItem {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'quantity_units': self.quantity_units,
            'quantity_pcs': self.quantity_pcs,
            'cost_per_unit': float(self.cost_per_unit),
            'item_total': float(self.item_total)
        }
