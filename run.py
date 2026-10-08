"""Application Entry Point"""
import os
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
            print('  python run.py create-default-admin - Create default admin (admin/admin123)')
            print('  python run.py seed-categories   - Seed default categories')
            sys.exit(1)
    else:
        # No command, run the server
        run_server()
