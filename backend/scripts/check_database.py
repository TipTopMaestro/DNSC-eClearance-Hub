
from app.database import get_db


def main():
    with get_db() as conn:
        tables = conn.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = ?
            ORDER BY name
        """, ("table",)).fetchall()

        print("Database tables:")

        for table in tables:
            print("-", table["name"])


if __name__ == "__main__":
    main()
