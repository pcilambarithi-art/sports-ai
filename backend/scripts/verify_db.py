"""Verify active database connectivity, schema tables, and static badge catalog."""

from sqlalchemy import inspect, text

from app.core.config import settings
from app.db.database import SessionLocal, engine
from app.db.init_db import init_db


def main() -> None:
    print(f"Configured DATABASE_URL dialect: {settings.DATABASE_URL.split('://')[0]}")
    init_db()
    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names())
    print(f"Verified {len(tables)} database tables:")
    for t in tables:
        print(f"  - {t}")

    db = SessionLocal()
    try:
        badge_count = db.execute(text("SELECT COUNT(*) FROM achievements")).scalar()
        user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        print(f"\nAchievement catalog entries : {badge_count}")
        print(f"Registered users            : {user_count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
