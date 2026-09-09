#!/usr/bin/env python3
"""
Reset Script - Restart the application to a clean state
Deletes database, clears uploads, and reinitializes everything
"""

import os
import sys
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the app instance
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config_by_name
from app import db, login_manager
from app.models import User, Product, Category

def reset_application(env='development', create_admin=True):
    """
    Reset the application to a clean state
    
    Args:
        env (str): Environment to reset ('development' or 'production')
        create_admin (bool): Whether to create a default admin user
    """
    
    # Create a minimal app for reset purposes (skip auto-initialization)
    app = Flask(__name__)
    app.config.from_object(config_by_name[env])
    db.init_app(app)
    login_manager.init_app(app)
    
    # Define database file path
    if env == 'development':
        db_path = 'instance/raasu_dev.db'
    else:
        db_path = 'instance/raasu_production.db'
    
    # Define upload folder
    upload_folder = 'app/static/uploads'
    
    print("=" * 60)
    print(f"RIMS Application Reset Script ({env.upper()} Environment)")
    print("=" * 60)
    print()
    
    # Step 1: Delete database
    print("Step 1: Removing database...")
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"  ✓ Deleted {db_path}")
    else:
        print(f"  ℹ Database file not found at {db_path}")
    print()
    
    # Step 2: Clear uploads folder
    print("Step 2: Clearing uploads folder...")
    if os.path.exists(upload_folder):
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"  ✓ Deleted {filename}")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"  ✓ Deleted folder {filename}")
        print(f"  ✓ Uploads folder cleared")
    else:
        print(f"  ℹ Uploads folder not found at {upload_folder}")
    print()
    
    # Step 3: Recreate database schema
    print("Step 3: Recreating database schema...")
    with app.app_context():
        # Create all tables
        print("  • Creating new tables...")
        db.create_all()
        print("  ✓ Database schema created")
    print()
    
    # Step 4: Seed default categories
    print("Step 4: Seeding default product categories...")
    with app.app_context():
        from config import Config
        
        for category_data in Config.DEFAULT_PRODUCT_CATEGORIES:
            existing = Category.query.filter_by(name=category_data['name']).first()
            if not existing:
                category = Category(
                    name=category_data['name'],
                    description=category_data['description']
                )
                db.session.add(category)
        
        db.session.commit()
        category_count = Category.query.count()
        print(f"  ✓ Created {category_count} default categories")
    print()
    
    # Step 5: Create default admin user (if requested)
    if create_admin:
        print("Step 5: Creating default admin user...")
        with app.app_context():
            # Check if any users exist
            user_count = User.query.count()
            
            if user_count == 0:
                default_admin = User(
                    username='admin',
                    email='admin@rims.local',
                    is_admin=True
                )
                # Set password
                default_admin.set_password('admin123')
                db.session.add(default_admin)
                db.session.commit()
                print("  ✓ Created default admin user:")
                print("    - Username: admin")
                print("    - Password: admin123")
                print("    - Email: admin@rims.local")
                print("  ⚠️  IMPORTANT: Change the password after first login!")
            else:
                print(f"  ℹ Skipped: {user_count} user(s) already exist")
    print()
    
    # Summary
    print("=" * 60)
    print("✓ APPLICATION RESET COMPLETE")
    print("=" * 60)
    print()
    print("What was reset:")
    print("  • Database (raasu_dev.db)")
    print("  • All database tables")
    print("  • Uploaded files")
    print("  • Default categories (recreated)")
    if create_admin:
        print("  • Admin user (created)")
    print()
    print("You can now start developing/testing with a clean slate!")
    print()


def show_help():
    """Display usage information"""
    print("RIMS Reset Script")
    print()
    print("Usage: python reset.py [options]")
    print()
    print("Options:")
    print("  --dev              Reset development environment (default)")
    print("  --prod             Reset production environment")
    print("  --no-admin         Skip creating default admin user")
    print("  --help             Show this help message")
    print()
    print("Examples:")
    print("  python reset.py                    # Reset dev, create admin")
    print("  python reset.py --prod             # Reset production")
    print("  python reset.py --dev --no-admin   # Reset dev, no admin user")
    print()


if __name__ == '__main__':
    env = 'development'
    create_admin = True
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == '--help':
                show_help()
                sys.exit(0)
            elif arg == '--prod':
                env = 'production'
            elif arg == '--dev':
                env = 'development'
            elif arg == '--no-admin':
                create_admin = False
            else:
                print(f"Unknown argument: {arg}")
                show_help()
                sys.exit(1)
    
    try:
        reset_application(env=env, create_admin=create_admin)
    except Exception as e:
        print()
        print("=" * 60)
        print("✗ ERROR DURING RESET")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)
