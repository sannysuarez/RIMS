# Shop Ceramics Inventory Management System

A scalable, production-ready web application for managing ceramic shop inventory with comprehensive financial tracking, multi-section support, and advanced analytics.

## Features

### 🛍️ Core Features
- **Product Management**: Full inventory tracking for main products with comprehensive pricing
- **Purchase Tracking**: Detailed purchase transactions with historical pricing support
- **Expenses/Withdrawals**: Track all expenses and cash withdrawals with beneficiary information
- **Credits & Debts**: Manage customer credits with full payment tracking
- **Admin Account Settings**: Update the administrator's name, email, phone number, and password
- **Miscellaneous Items**: Separate inventory for non-standard items
- **Dashboard Analytics**: Real-time charts and metrics for business intelligence

### 📊 Dashboard Analytics
- **Total Liquidity**: Calculated from inventory value + cash + credits - expenses - debts
- **Debt Analysis**: Top 5 highest debtors with amounts
- **Top Products**: Best-selling products by quantity (top 10)
- **Category Sales**: Sales breakdown by product category
- **Monthly Trends**: Historical monthly financial data

### 🔐 Security & Access Control
- User authentication with secure password hashing
- Role-based access control (RBAC) for admin-only operations
- Admin-only permissions for deletions and critical edits
- Confirmation dialogs for destructive operations
- Session management with configurable timeouts

### 📱 User Interface
- **Blue Accent Color**: Professional blue theme throughout
- **Responsive Design**: Fully responsive for desktop, tablet, and mobile
- **Intuitive Navigation**: Sidebar navigation with clear section organization
- **Search & Filter**: Advanced search and sorting for all product lists
- **Data Tables**: Clean, sortable tables with pagination

## Technology Stack

```
Backend:
  - Flask 3.0.0          - Lightweight web framework
  - Flask-SQLAlchemy     - ORM for database operations
  - Flask-Login          - User session management
  - Flask-WTF            - Form handling with CSRF protection

Database:
  - SQLite3              - Embedded database (production-ready with migration to PostgreSQL)
  - SQLAlchemy           - Object-relational mapping

Frontend:
  - HTML5                - Semantic markup
  - CSS3                 - Responsive styling with blue accent theme
  - JavaScript           - Client-side interactions

Python:
  - Python 3.14+         - Latest Python version
  - All dependencies compatible with Python 3.14+
```

## Project Structure

```
raasu/
├── app/                        # Main application package
│   ├── __init__.py            # App factory
│   ├── models/                # Database models
│   │   ├── __init__.py
│   │   ├── user.py            # User model
│   │   ├── product.py         # Product & Category
│   │   ├── purchase.py        # Purchase transactions
│   │   ├── expense.py         # Expenses/Withdrawals
│   │   ├── credit.py          # Credits/Debts
│   │   └── misc.py            # Miscellaneous items
│   │
│   ├── routes/                # Blueprint routes
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication routes
│   │   ├── dashboard.py       # Dashboard & analytics
│   │   ├── products.py        # Product management
│   │   ├── purchases.py       # Purchase management
│   │   ├── expenses.py        # Expense management
│   │   ├── credits.py         # Credit/debt management
│   │   └── misc.py            # Miscellaneous routes
│   │
│   ├── templates/             # HTML templates
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── products/
│   │   ├── purchases/
│   │   ├── expenses/
│   │   ├── credits/
│   │   └── misc/
│   │
│   ├── static/                # Static files
│   │   ├── css/
│   │   │   └── style.css      # Blue-themed CSS
│   │   └── js/
│   │       └── app.js         # Client-side JavaScript
│   │
│   └── utils/                 # Utility functions
│       └── helpers.py         # Helper functions
│
├── config.py                  # Configuration management
├── run.py                     # Application entry point
├── requirements.txt           # Python dependencies
├── pseudo.txt                 # Detailed pseudocode
├── README.md                  # This file
├── .env                       # Environment variables (not in repo)
└── .gitignore                # Git ignore rules

Database Models:
├── User                       # Authentication
├── Category                   # Product categories
├── Product                    # Main inventory
├── Purchase                   # Purchase transactions
├── PurchaseItem              # Individual purchase items
├── Expense                   # Expenses/withdrawals
├── Credit                    # Customer credits
├── Debt                      # Debt transactions
├── MiscProduct               # Miscellaneous products
└── MiscPurchase              # Miscellaneous transactions
```

## Installation & Setup

### Prerequisites
- Python 3.14+ installed
- pip package manager
- git (optional)

### Step 1: Create Virtual Environment

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt)
python -m venv venv
venv\Scripts\activate.bat

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Initialize Database

```bash
# Create tables and initialize database
python run.py init-db

# Create admin user
python run.py create-admin
```

### Step 4: Run Application

```bash
python run.py
```

Application will be available at `http://localhost:5000`

## Configuration

### Environment Variables (.env file)

```ini
FLASK_ENV=development
FLASK_APP=run.py
SECRET_KEY=your-secret-key-here-change-in-production
DATABASE_URL=sqlite:///raasu.db
```

### Configuration Classes

**DevelopmentConfig** (default):
- Debug: Enabled
- Database: SQLite (raasu_dev.db)
- Session: Not secure (for development)

**ProductionConfig**:
- Debug: Disabled
- Database: PostgreSQL (via DATABASE_URL)
- Session: HTTPS/Secure cookies only

**TestingConfig**:
- Debug: Disabled
- Database: In-memory SQLite
- CSRF: Disabled for testing

## Database Design

### Product Inventory System

The product model tracks:
- **Pricing Hierarchy**: 
  - `cost_per_unit`: Purchase price per pack/carton
  - `cost_per_pcs`: Derived from `cost_per_unit / quantity_per_unit`
  - `sell_price_per_pcs`: Selling price per individual piece
  
- **Quantity Tracking**:
  - `quantity_per_unit`: Constant items per pack (fixed after creation)
  - `total_quantity_units`: Total packs/cartons/pcs purchased
  - `total_quantity_pcs`: Total individual pieces (units × quantity_per_unit)
  - `remaining_quantity_pcs`: Available inventory
  - `sold_quantity_pcs`: Total sold (for analytics)

- **History**: All pricing is maintained per transaction (supports price fluctuations)

### Financial Tracking

**Liquidity Calculation Formula**:
```
Total Liquidity = (Product Inventory Value) 
                + (Total Cash Input from Purchases)
                - (Total Expenses/Withdrawals)
                - (Customer Credit Remaining Balances)
                - (Total Debts)
```

**Credit Management**:
- Track customer credits with full/partial payments
- Automatic balance calculation
- Transaction history with timestamps
- Status tracking (active, settled, defaulted)

## API Routes

### Authentication
- `GET/POST /auth/login` - User login
- `GET/POST /auth/register` - User registration (admin)
- `GET /auth/logout` - User logout

### Dashboard
- `GET /dashboard/` - Main dashboard with analytics

### Products
- `GET /products/` - List all products with search/sort
- `GET/POST /products/add` - Add new product
- `GET /products/<id>` - View product details
- `GET/POST /products/<id>/edit` - Edit product (admin)
- `POST /products/<id>/delete` - Delete product (admin)

### Purchases
- `GET /purchases/` - List purchases
- `GET/POST /purchases/add` - Record purchase
- `GET /purchases/<id>` - View purchase details

### Expenses
- `GET /expenses/` - List expenses
- `GET/POST /expenses/add` - Record expense
- `GET /expenses/<id>` - View expense

### Credits
- `GET /credits/credits` - List credits
- `GET/POST /credits/add-credit` - Add customer credit
- `GET/POST /credits/<id>/payback` - Record payment
- `GET /credits/<id>` - View credit details

### Settings
- `GET/POST /settings/` - Update the signed-in administrator's account details

### Miscellaneous
- `GET /misc/` - Misc products
- `GET/POST /misc/add-product` - Add product
- `GET/POST /misc/add-purchase` - Add purchase
- `GET /misc/<id>` - View product

## Scalability Features

### Database Optimization
- ✅ Indexed queries on frequently searched fields (name, unique_id, customer_name)
- ✅ Efficient date range queries for analytics
- ✅ Lazy loading relationships to prevent N+1 queries
- ✅ Proper foreign key relationships with cascading deletes

### Performance
- ✅ Pagination on all list views (20 items per page)
- ✅ Multi-directional sorting capability
- ✅ Lazy-loaded relationships
- ✅ Database connection pooling (SQLAlchemy)

### Architecture
- ✅ Factory pattern for app initialization (easy multi-instance support)
- ✅ Blueprint-based module organization
- ✅ Separation of concerns (routes, models, templates)
- ✅ Environment-based configuration

### Future Enhancements
- Multi-shop support (add `shop_id` to all tables)
- Multi-currency support (currency field in expenses)
- Advanced reporting (PDF/Excel exports)
- Real-time inventory alerts
- Barcode scanning integration
- REST API for mobile app
- Machine learning for demand forecasting
- Redis caching for analytics
- Celery background tasks for reports
- WebSocket real-time updates

## Security Considerations

### Implemented
- ✅ Secure password hashing (Werkzeug)
- ✅ CSRF protection (Flask-WTF)
- ✅ Session management with timeouts
- ✅ Role-based access control (RBAC)
- ✅ Login required decorators (@login_required)
- ✅ Admin-only operations with confirmations

### Recommendations
- Use HTTPS in production
- Deploy behind reverse proxy (Nginx)
- Use PostgreSQL instead of SQLite in production
- Enable SQL query logging during development
- Implement rate limiting
- Use environment variables for secrets
- Regular security audits
- Keep dependencies updated

## Development Workflow

### Running in Development Mode
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run development server
python run.py
```

### Creating Database Migrations (Future)
```bash
# When using Alembic migrations
flask db init
flask db migrate -m "Description"
flask db upgrade
```

### Database Shell
```bash
python -c "from run import app; app.app_context().push()"
```

## Troubleshooting

### Virtual Environment Issues
```bash
# Recreate venv if needed
rmdir /s venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Database Errors
```bash
# Reset database
rm raasu_dev.db
python run.py init-db
```

### Import Errors
```bash
# Ensure venv is activated
.\venv\Scripts\Activate.ps1

# Reinstall packages
pip install --force-reinstall -r requirements.txt
```

## Testing

Run tests:
```bash
pytest tests/
```

Coverage report:
```bash
pytest --cov=app tests/
```

## Production Deployment

### Options
1. **Heroku**: `git push heroku main`
2. **AWS EC2**: Use Gunicorn + Nginx
3. **DigitalOcean**: Gunicorn + Nginx + Supervisor
4. **Docker**: Containerize with Docker

### Pre-Deploymenti  Checklist
- [ ] Set `FLASK_ENV=production`
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure PostgreSQL database
- [ ] Enable HTTPS/SSL
- [ ] Set up domain name
- [ ] Configure email for notifications
- [ ] Set up logging and monitoring
- [ ] Enable backup strategy
- [ ] Configure rate limiting
- [ ] Test payment integrations (if needed)

### Gunicorn Command
```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues, questions, or suggestions:
- Create an issue on GitHub
- Email: sannysuarez4@gmail.com
- Documentation: [Full Docs](./pseudo.txt)

## Version History

### v1.0.0 (Initial Release)
- Core inventory management
- Financial tracking
- Multi-section support
- Dashboard with analytics
- User authentication
- Blue-themed UI

---

**Built with ❤️ for efficient ceramic shop management**

Last Updated: April 20, 2026
