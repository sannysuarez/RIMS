"""Credit and Debt Models"""
from app import db
from datetime import datetime
from decimal import Decimal


class Credit(db.Model):
    """Customer credit/account records"""
    __tablename__ = 'credits'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(150), nullable=False, index=True)
    customer_contact = db.Column(db.String(20))
    total_credit = db.Column(db.Numeric(12, 2), default=0)
    paid_amount = db.Column(db.Numeric(12, 2), default=0)
    remaining_balance = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default='active')  # active, settled, defaulted
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    debts = db.relationship('Debt', backref='credit', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Credit {self.customer_name}>'
    
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


class Debt(db.Model):
    """Debt/Payback transactions"""
    __tablename__ = 'debts'
    
    id = db.Column(db.Integer, primary_key=True)
    credit_id = db.Column(db.Integer, db.ForeignKey('credits.id'), nullable=False, index=True)
    
    transaction_type = db.Column(db.String(20), nullable=False)  # credit, payback
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.Text)
    transaction_date = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Debt {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'credit_id': self.credit_id,
            'transaction_type': self.transaction_type,
            'amount': float(self.amount),
            'transaction_date': self.transaction_date.isoformat()
        }
