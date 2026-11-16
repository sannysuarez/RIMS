import os
import sqlite3
from pathlib import Path
from datetime import datetime

BASE = Path.home() / "RIMS"

DATABASES = {
    "RAASU": BASE / "instance" / "raasu_dev.db",
    "ITOBE": BASE / "instance" / "raasu_itobe_dev.db",
}

os.environ["FLASK_ENV"] = "production"
os.environ["DATABASE_URL"] = f"sqlite:///{DATABASES['RAASU']}"
os.environ["ITOBE_DATABASE_URL"] = f"sqlite:///{DATABASES['ITOBE']}"

from app import create_app, db
from app.models import Category

app = create_app("production")

with app.app_context():
    engines = {
        "RAASU": db.engines[None],
        "ITOBE": db.engines["itobe"],
    }

    # Verify exact database paths.
    for name, engine in engines.items():
        actual = Path(engine.url.database).resolve()
        expected = DATABASES[name].resolve()

        if actual != expected:
            raise RuntimeError(
                f"{name} database mismatch: {actual}"
            )

        if not actual.exists():
            raise FileNotFoundError(actual)

    print("Verified databases:")
    for name, path in DATABASES.items():
        print(f"{name}: {path}")

    confirmation = input(
        "\nThis permanently clears BOTH databases. "
        "Type RESET RIMS TEST DATA to continue: "
    )

    if confirmation != "RESET RIMS TEST DATA":
        raise SystemExit("Reset cancelled.")

    # Back up both databases.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = BASE / "db_backups" / f"before_reset_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for name, path in DATABASES.items():
        with sqlite3.connect(str(path)) as source:
            check = source.execute("PRAGMA integrity_check").fetchone()[0]
            if check != "ok":
                raise RuntimeError(f"{name} integrity check failed: {check}")

            with sqlite3.connect(str(backup_dir / f"{name}.db")) as target:
                source.backup(target)

    print(f"\nBackups created: {backup_dir}")

    # Remove all SQLAlchemy-managed tables from both databases.
    for name, engine in engines.items():
        db.Model.metadata.drop_all(bind=engine)
        print(f"{name}: old tables cleared.")

# Reinitialize the application.
# create_app recreates tables and runs all five schema migration helpers.
fresh_app = create_app("production")

with fresh_app.app_context():
    for name, engine in {
        "RAASU": db.engines[None],
        "ITOBE": db.engines["itobe"],
    }.items():
        added = 0
        existing = set()

        with engine.begin() as connection:
            existing = {
                value.strip().casefold()
                for value in connection.execute(
                    Category.__table__.select().with_only_columns(Category.name)
                ).scalars()
                if value
            }

            for item in fresh_app.config["DEFAULT_PRODUCT_CATEGORIES"]:
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

        print(f"{name}: {added} categories seeded; {len(existing)} total.")

print("\nBoth databases have been reset and initialized successfully.")
PY