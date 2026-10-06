"""Expense/Withdrawal Model"""
from app import db
from datetime import datetime
from decimal import Decimal


class Expense(db.Model):
    """Expense/Withdrawal transactions."""
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    beneficiary_name = db.Column(db.String(150), nullable=False, index=True)
    beneficiary_address = db.Column(db.Text)
    transaction_type = db.Column(db.String(20), nullable=False, default='expense', index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.Text)
    expense_date = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def liquidity_effect(self):
        """Return the amount that should be deducted from liquidity.

        Expense return/refund entries are preserved for audit trails but must not add
        value back into liquidity. They therefore contribute zero to the net deduction.
        """
        if self.transaction_type == 'return':
            return 0.0
        return float(self.amount or 0)

    def __repr__(self):
        return f'<Expense {self.id}: {self.beneficiary_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'beneficiary_name': self.beneficiary_name,
            'transaction_type': self.transaction_type,
            'amount': float(self.amount),
            'effective_amount': self.liquidity_effect,
            'expense_date': self.expense_date.isoformat(),
            'description': self.description
        }
