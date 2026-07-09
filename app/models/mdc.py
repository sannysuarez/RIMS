"""Monthly Data Collection records"""
from app import db
from datetime import datetime


class MDCReport(db.Model):
    """Monthly Data Collection / cash input report"""
    __tablename__ = 'mdc_reports'

    id = db.Column(db.Integer, primary_key=True)
    report_date = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    cash_input = db.Column(db.Numeric(12, 2), default=0)
    notes = db.Column(db.Text)
    # Snapshot fields for immutability: saved at time of MDC creation
    product_value = db.Column(db.Numeric(12, 2), default=0)
    total_expenses = db.Column(db.Numeric(12, 2), default=0)
    total_debts = db.Column(db.Numeric(12, 2), default=0)
    total_paybacks = db.Column(db.Numeric(12, 2), default=0)
    total_liquidity = db.Column(db.Numeric(12, 2), default=0)
    cycle_profit = db.Column(db.Numeric(12, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<MDCReport {self.id} {self.report_date.isoformat()}>'

    def to_dict(self):
        return {
            'id': self.id,
            'report_date': self.report_date.isoformat(),
            'cash_input': float(self.cash_input),
            'notes': self.notes
            ,
            'product_value': float(self.product_value),
            'total_expenses': float(self.total_expenses),
            'total_debts': float(self.total_debts),
            'total_paybacks': float(self.total_paybacks),
            'total_liquidity': float(self.total_liquidity),
            'cycle_profit': float(self.cycle_profit)
        }
