"""Product and Category Models"""
from app import db
from datetime import datetime
from decimal import Decimal


class Category(db.Model):
    """Product categories"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    products = db.relationship('Product', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }


class Product(db.Model):
    """Main product model"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)
    
    # Packaging info
    unit_type = db.Column(db.String(50), nullable=False)  # pack, carton, pcs
    quantity_per_unit = db.Column(db.Integer, nullable=False)  # e.g., 12 items per pack
    
    # Pricing - stored as Decimal for accuracy
    cost_per_unit = db.Column(db.Numeric(10, 2), nullable=False)  # Purchase price per pack/carton
    cost_per_pcs = db.Column(db.Numeric(10, 2), nullable=False)  # Calculated: cost_per_unit / quantity_per_unit
    sell_price_per_pcs = db.Column(db.Numeric(10, 2), nullable=False)  # Selling price per piece
    
    # Stock tracking
    total_quantity_units = db.Column(db.Integer, default=0)  # Total packs/cartons/pcs
    total_quantity_pcs = db.Column(db.Integer, default=0)  # Total individual pieces
    remaining_quantity_units = db.Column(db.Integer, default=0)
    remaining_quantity_pcs = db.Column(db.Integer, default=0)
    sold_quantity_pcs = db.Column(db.Integer, default=0)
    
    # Metadata
    invoice_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    purchases = db.relationship('PurchaseItem', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def calculate_liquidity_value(self):
        """Calculate product contribution to total liquidity"""
        return float(self.remaining_quantity_pcs * self.cost_per_pcs)

    @property
    def total_profit_margin(self):
        """Calculate profit margin from sold units"""
        return float((self.sell_price_per_pcs - self.cost_per_pcs) * self.sold_quantity_pcs)

    def to_dict(self):
        return {
            'id': self.id,
            'unique_id': self.unique_id,
            'name': self.name,
            'category': self.category.name if self.category else None,
            'unit_type': self.unit_type,
            'quantity_per_unit': self.quantity_per_unit,
            'cost_per_unit': float(self.cost_per_unit),
            'cost_per_pcs': float(self.cost_per_pcs),
            'sell_price_per_pcs': float(self.sell_price_per_pcs),
            'total_quantity_units': self.total_quantity_units,
            'remaining_quantity_units': self.remaining_quantity_units,
            'sold_quantity_pcs': self.sold_quantity_pcs,
            'created_at': self.created_at.isoformat()
        }
