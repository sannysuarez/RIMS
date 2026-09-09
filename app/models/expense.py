"""Expense/Withdrawal Model"""
from app import db
from datetime import datetime
from decimal import Decimal


class Expense(db.Model):
    """Expense/Withdrawal transactions"""
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    beneficiary_name = db.Column(db.String(150), nullable=False, index=True)
    beneficiary_address = db.Column(db.Text)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.Text)
    expense_date = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Expense {self.id}: {self.beneficiary_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'beneficiary_name': self.beneficiary_name,
            'amount': float(self.amount),
            'expense_date': self.expense_date.isoformat(),
            'description': self.description
        }
