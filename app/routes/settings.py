"""Admin account settings routes."""
import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models.user import User

settings_bp = Blueprint('settings', __name__)

EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PHONE_PATTERN = re.compile(r'^\+?[0-9][0-9\s().-]*$')


@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def account():
    """Let an administrator update their own account details."""
    if not current_user.is_admin:
        flash('Only administrators can access account settings.', 'error')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []
        if not username or len(username) > 80:
            errors.append('Name is required and must be 80 characters or fewer.')
        if not email or len(email) > 120 or not EMAIL_PATTERN.fullmatch(email):
            errors.append('Enter a valid email address (up to 120 characters).')
        if (
            len(phone_number) > 30
            or not PHONE_PATTERN.fullmatch(phone_number)
            or not 7 <= sum(character.isdigit() for character in phone_number) <= 15
        ):
            errors.append('Enter a valid phone number with 7 to 15 digits.')

        existing_username = User.query.filter(
            User.username == username,
            User.id != current_user.id
        ).first()
        if existing_username:
            errors.append('That name is already in use.')

        existing_email = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()
        if existing_email:
            errors.append('That email address is already in use.')

        if new_password:
            if not current_password or not current_user.check_password(current_password):
                errors.append('Enter your current password to change it.')
            if len(new_password) < 8:
                errors.append('New password must be at least 8 characters long.')
            if new_password != confirm_password:
                errors.append('New password and confirmation do not match.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'settings/account.html',
                username=username,
                email=email,
                phone_number=phone_number
            )

        current_user.username = username
        current_user.email = email
        current_user.phone_number = phone_number
        if new_password:
            current_user.set_password(new_password)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        flash('Account settings updated successfully.', 'success')
        return redirect(url_for('settings.account'))

    return render_template('settings/account.html')
