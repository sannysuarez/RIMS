
import os
import sqlite3
from pathlib import Path
from datetime import datetime

# These are the exact database paths configured in the live WSGI file.
BASE = Path.home() / "RIMS"
EXPECTED = {
    "raasu": BASE / "instance" / "raasu_dev.db",
    "itobe": BASE / "instance" / "raasu_itobe_dev.db",
}

os.environ["FLASK_ENV"] = "production"
os.environ["DATABASE_URL"] = f"sqlite:///{EXPECTED['raasu']}"
os.environ["ITOBE_DATABASE_URL"] = f"sqlite:///{EXPECTED['itobe']}"

from app import create_app, db
import app as app_package
from app.models import Category

app = create_app("production")

with app.app_context():

    # Verify the app is connected to exactly the intended databases.
    engines = db.engines
    actual = {
        "raasu": Path(engines[None].url.database).resolve(),
        "itobe": Path(engines["itobe"].url.database).resolve(),
    }

    for name, expected in EXPECTED.items():
        if actual[name] != expected.resolve():
            raise RuntimeError(
                f"Database mismatch for {name}: {actual[name]}"
            )

    # Check that custom schema helpers are available before resetting.
    helper_names = [
        "ensure_mdc_product_record_columns",
        "ensure_mdc_report_snapshot_columns",
        "ensure_mdc_report_admin_column",
        "ensure_expense_transaction_type_columns",
        "ensure_user_phone_number_column",
    ]

    helpers = [getattr(app_package, name) for name in helper_names]

    print("\nDatabases verified:")
    for name, path in actual.items():
        print(f"  {name.upper()}: {path}")

    confirmation = input(
        "\nThis will erase ALL records in both databases. "
        "Type RESET RIMS TEST DATA to continue: "
    )

    if confirmation != "RESET RIMS TEST DATA":
        raise SystemExit("Reset cancelled. No data was deleted.")

    # Back up both databases first.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = BASE / "db_backups" / f"before_reset_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for name, path in actual.items():
        if not path.exists():
            raise FileNotFoundError(f"Database not found: {path}")

        with sqlite3.connect(str(path)) as source:
            result = source.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                raise RuntimeError(f"{name} database integrity check failed: {result}")

            backup_path = backup_dir / f"{name}.db"
            with sqlite3.connect(str(backup_path)) as destination:
                source.backup(destination)

        print(f"Backup created: {backup_path}")

    # Drop and recreate all SQLAlchemy-managed tables in both databases.
    for name, engine in engines.items():
        db.Model.metadata.drop_all(bind=engine)
        db.Model.metadata.create_all(bind=engine)

        # Restore additional columns maintained by the application.
        for helper in helpers:
            helper(engine)

        # Seed the configured default categories.
        added = 0
        with engine.begin() as connection:
            existing = {
                value.strip().casefold()
                for value in connection.execute(
                    Category.__table__.select().with_only_columns(Category.name)
                ).scalars()
                if value
            }

            for item in app.config["DEFAULT_PRODUCT_CATEGORIES"]:
                category_name = item["name"].strip()

                if category_name.casefold() not in existing:
                    connection.execute(
                        Category.__table__.insert().values(
                            name=category_name,
                            description=item["description"],
                        )
                    )
                    existing.add(category_name.casefold())
                    added += 1

        location = "RAASU" if name is None else str(name).upper()
        print(f"{location}: reset complete; {added} categories added.")

    print(f"\nBackups saved in: {backup_dir}")
    print("Both databases have been reset successfully.")
PY