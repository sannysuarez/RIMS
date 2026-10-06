"""Ruf-Yog Corner Products, Purchases, Expenses, Credits and MDC"""
from app import db
from datetime import datetime
from decimal import Decimal


class RufYogProduct(db.Model):
    """Ruf-Yog Corner product (special products section)"""
    __tablename__ = 'ruf_yog_products'
    
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    
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


class RufYogMDCReport(db.Model):
    """Monthly data collection report for Ruf-Yog"""
    __tablename__ = 'ruf_yog_mdc_reports'

    id = db.Column(db.Integer, primary_key=True)
    report_date = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    cash_input = db.Column(db.Numeric(12, 2), default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<RufYogMDCReport {self.id} {self.report_date.isoformat()}>'

    def to_dict(self):
        return {
            'id': self.id,
            'report_date': self.report_date.isoformat(),
            'cash_input': float(self.cash_input),
            'notes': self.notes
        }


class RufYogExpense(db.Model):
    """Ruf-Yog Corner expense or withdrawal"""
    __tablename__ = 'ruf_yog_expenses'

    id = db.Column(db.Integer, primary_key=True)
    beneficiary_name = db.Column(db.String(150), nullable=False, index=True)
    transaction_type = db.Column(db.String(20), nullable=False, default='expense', index=True)
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    expense_date = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def liquidity_effect(self):
        if self.transaction_type == 'return':
            return 0.0
        return float(self.amount or 0)

    def __repr__(self):
        return f'<RufYogExpense {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'beneficiary_name': self.beneficiary_name,
            'transaction_type': self.transaction_type,
            'description': self.description,
            'amount': float(self.amount),
            'effective_amount': self.liquidity_effect,
            'expense_date': self.expense_date.isoformat()
        }


class RufYogCredit(db.Model):
    """Customer credit/debt accounts for Ruf-Yog"""
    __tablename__ = 'ruf_yog_credits'

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(150), nullable=False, index=True)
    customer_contact = db.Column(db.String(20))
    total_credit = db.Column(db.Numeric(12, 2), default=0)
    paid_amount = db.Column(db.Numeric(12, 2), default=0)
    remaining_balance = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    debts = db.relationship('RufYogDebt', backref='credit', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<RufYogCredit {self.customer_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_contact': self.customer_contact,
            'total_credit': float(self.total_credit),
            'paid_amount': float(self.paid_amount),
            'remaining_balance': float(self.remaining_balance),
            'status': self.status
        }


class RufYogDebt(db.Model):
    """Debt/payback transactions for Ruf-Yog credit accounts"""
    __tablename__ = 'ruf_yog_debts'

    id = db.Column(db.Integer, primary_key=True)
    credit_id = db.Column(db.Integer, db.ForeignKey('ruf_yog_credits.id'), nullable=False, index=True)
    transaction_type = db.Column(db.String(20), nullable=False)  # credit, payback
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.Text)
    transaction_date = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<RufYogDebt {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'credit_id': self.credit_id,
            'transaction_type': self.transaction_type,
            'amount': float(self.amount),
            'description': self.description,
            'transaction_date': self.transaction_date.isoformat()
        }
