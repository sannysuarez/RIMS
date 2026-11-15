#!/usr/bin/env bash
set -e

echo "=================================="
echo " RIMS CATEGORY SYNCHRONIZATION"
echo "=================================="

python - <<'PY'
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import Category

app = create_app('production')

with app.app_context():
    categories = app.config['DEFAULT_PRODUCT_CATEGORIES']

    for bind, engine in db.engines.items():
        with engine.begin() as connection:

            existing = {
                name.strip().casefold()
                for name in connection.execute(
                    Category.__table__.select().with_only_columns(
                        Category.name
                    )
                ).scalars()
                if name
            }

            added = 0

            for item in categories:
                name = item['name'].strip()

                if name.casefold() not in existing:
                    connection.execute(
                        Category.__table__.insert().values(
                            name=name,
                            description=item['description']
                        )
                    )
                    existing.add(name.casefold())
                    added += 1

        location = 'RAASU' if bind is None else bind.upper()

        print(f"{location}: {added} added, {len(existing)} total")

print("\nCategory synchronization completed successfully!")
PY
