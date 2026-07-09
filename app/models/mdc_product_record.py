"""MDC Product Records - tracks sold/remaining quantities per product per MDC cycle"""
from app import db
from datetime import datetime


class MDCProductRecord(db.Model):
    """Product sales/stock record for each MDC cycle"""
    __tablename__ = 'mdc_product_records'

    id = db.Column(db.Integer, primary_key=True)
    mdc_report_id = db.Column(db.Integer, db.ForeignKey('mdc_reports.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    
    # Quantities recorded at this MDC cycle
    sold_quantity_pcs = db.Column(db.Integer, default=0)
    remaining_quantity_pcs = db.Column(db.Integer, default=0)
    
    # Prices recorded at this MDC cycle (immutable snapshot)
    cost_per_pcs_at_record = db.Column(db.Numeric(10, 2), default=0)
    sell_price_per_pcs_at_record = db.Column(db.Numeric(10, 2), default=0)
    
    # Timestamp of the MDC cycle
    recorded_at = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    
    # Relationships
    mdc_report = db.relationship('MDCReport', backref=db.backref('product_records', lazy=True, cascade='all, delete-orphan'))
    product = db.relationship('Product', backref=db.backref('mdc_records', lazy=True, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<MDCProductRecord MDC#{self.mdc_report_id} Product#{self.product_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'mdc_report_id': self.mdc_report_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'sold_quantity_pcs': self.sold_quantity_pcs,
            'remaining_quantity_pcs': self.remaining_quantity_pcs,
            'cost_per_pcs_at_record': float(self.cost_per_pcs_at_record),
            'sell_price_per_pcs_at_record': float(self.sell_price_per_pcs_at_record),
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }
