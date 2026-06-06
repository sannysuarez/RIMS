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
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<MDCReport {self.id} {self.report_date.isoformat()}>'

    def to_dict(self):
        return {
            'id': self.id,
            'report_date': self.report_date.isoformat(),
            'cash_input': float(self.cash_input),
            'notes': self.notes
        }
