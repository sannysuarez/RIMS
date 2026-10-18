"""Application Entry Point"""
import os
import re
import sys
from dotenv import load_dotenv
from app import create_app, db
from app.models import User, Product, Category, Purchase, PurchaseItem, Expense, Credit, Debt, MiscProduct, MiscPurchase

# Load environment variables
load_dotenv()

app = create_app(os.environ.get('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    """Register models for Flask shell"""
    return {
        'db': db,
        'User': User,
        'Product': Product,
        'Category': Category,
        'Purchase': Purchase,
        'PurchaseItem': PurchaseItem,
        'Expense': Expense,
        'Credit': Credit,
        'Debt': Debt,
        'MiscProduct': MiscProduct,
        'MiscPurchase': MiscPurchase,
    }


@app.cli.command()
def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print('Database initialized.')


def create_admin_helper():
    """Create an admin user"""
    username = input('Enter admin username: ')
    email = input('Enter admin email: ')
    password = input('Enter admin password: ')

    with app.app_context():
        if User.query.filter_by(username=username).first():
            print('Username already exists.')
            return

        admin = User(username=username, email=email, is_admin=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f'Admin user {username} created successfully.')


@app.cli.command()
def create_admin():
    create_admin_helper()


def create_initial_admins_helper():
    """Provision the named initial administrators from Render environment secrets."""
    accounts = [
        ('Ibrahim', 'ADMIN_IBRAHIM_PASSWORD', 'ADMIN_IBRAHIM_EMAIL', 'ibrahim@rims.invalid'),
        ('Sanni', 'ADMIN_SANNI_PASSWORD', 'ADMIN_SANNI_EMAIL', 'sanni@rims.invalid'),
    ]

    with app.app_context():
        admins_to_create = []
        emails_in_use = set()

        for username, password_variable, email_variable, default_email in accounts:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                if not existing_user.is_admin:
                    raise SystemExit(
                        f'User {username} already exists but is not an administrator; '
                        'resolve this account before provisioning.'
                    )
                print(f'Administrator {username} already exists; leaving it unchanged.')
                continue

            password = os.environ.get(password_variable, '')
            if len(password) < 12:
                raise SystemExit(
                    f'Set {password_variable} to a password of at least 12 characters.'
                )

            email = os.environ.get(email_variable, default_email).strip()
            if not email or len(email) > 120 or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
                raise SystemExit(f'Set {email_variable} to a valid email address.')
            if email in emails_in_use or User.query.filter_by(email=email).first():
                raise SystemExit(f'Email address for {username} is already in use.')

            emails_in_use.add(email)
            admins_to_create.append((username, email, password))

        if not admins_to_create:
            print('Both initial administrator accounts already exist.')
            return

        for username, email, password in admins_to_create:
            admin = User(username=username, email=email, is_admin=True)
            admin.set_password(password)
            db.session.add(admin)

        db.session.commit()
        for username, _, _ in admins_to_create:
            print(f'Administrator {username} created successfully.')


@app.cli.command()
def create_initial_admins():
    """Create the Ibrahim and Sanni administrator accounts."""
    create_initial_admins_helper()


def reset_initial_admin_passwords_helper():
    """Reset the named administrators' passwords from Render environment secrets."""
    accounts = [
        ('Ibrahim', 'ADMIN_IBRAHIM_PASSWORD'),
        ('Sanni', 'ADMIN_SANNI_PASSWORD'),
    ]

    with app.app_context():
        admins = []
        for username, password_variable in accounts:
            password = os.environ.get(password_variable, '')
            if len(password) < 12:
                raise SystemExit(
                    f'Set {password_variable} to a password of at least 12 characters.'
                )

            admin = User.query.filter_by(username=username).first()
            if not admin or not admin.is_admin:
                raise SystemExit(
                    f'Administrator {username} does not exist; run '
                    'create-initial-admins first.'
                )
            admins.append((admin, password))

        for admin, password in admins:
            admin.set_password(password)

        db.session.commit()
        print('Passwords reset successfully for Ibrahim and Sanni.')


@app.cli.command()
def reset_initial_admin_passwords():
    """Reset both named administrator passwords from environment secrets."""
    reset_initial_admin_passwords_helper()


def seed_categories_helper():
    """Seed default categories"""
    with app.app_context():
        existing_names = {category.name.lower() for category in Category.query.all()}
        categories_added = 0
        default_categories = app.config.get('DEFAULT_PRODUCT_CATEGORIES', [])

        for cat_data in default_categories:
            if cat_data['name'].lower() in existing_names:
                continue
            category = Category(name=cat_data['name'], description=cat_data['description'])
            db.session.add(category)
            categories_added += 1

        if categories_added == 0:
            print('All default categories already exist.')
            return

        db.session.commit()
        print(f'Default categories seeded successfully. Added {categories_added} categories.')


@app.cli.command()
def seed_categories():
    seed_categories_helper()


def run_server():
    """Start the development server"""
    app.run(debug=True, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Check if a command was passed
        command = sys.argv[1]
        if command == 'init-db':
            with app.app_context():
                db.create_all()
                print('✅ Database initialized.')
        elif command == 'create-admin':
            create_admin_helper()
        elif command == 'create-initial-admins':
            create_initial_admins_helper()
        elif command == 'reset-initial-admin-passwords':
            reset_initial_admin_passwords_helper()
        elif command == 'create-default-admin':
            with app.app_context():
                if User.query.filter_by(username='admin').first():
                    print('⚠️  Default admin user already exists.')
                    print('Login with:')
                    print('  Username: admin')
                    print('  Password: admin123')
                    sys.exit(0)
                
                admin = User(username='admin', email='admin@shopceramics.com', is_admin=True)
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print('✅ Default admin user created successfully!')
                print('Login with:')
                print('  Username: admin')
                print('  Password: admin123')
        elif command == 'seed-categories':
            seed_categories_helper()
        else:
            print(f'Unknown command: {command}')
            print('Available commands:')
            print('  python run.py init-db           - Initialize the database')
            print('  python run.py create-admin      - Create an admin user (interactive)')
            print('  python run.py create-initial-admins - Create Ibrahim and Sanni admins')
            print('  python run.py reset-initial-admin-passwords - Reset both named admin passwords')
            print('  python run.py create-default-admin - Create default admin (admin/admin123)')
            print('  python run.py seed-categories   - Seed default categories')
            sys.exit(1)
    else:
        # No command, run the server
        run_server()
