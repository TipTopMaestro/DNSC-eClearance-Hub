
from pathlib import Path

from app.config import DATABASE_PATH
from app.database import (
    init_db,
    init_additional_tables,
    init_registrar_tables
)


def main():
    db_path = Path(DATABASE_PATH).resolve()

    # Only allow resetting our local development database.
    allowed_path = Path("data/clearance.db").resolve()

    if db_path != allowed_path:
        raise SystemExit(
            "Reset denied: not the development database."
        )

    print("=" * 50)
    print("DNSC e-Clearance Hub - Database Reset")
    print("=" * 50)

    print(f"Database: {db_path}")
    print("WARNING: All stored database records will be deleted.")
    print("Stop the API server before continuing.")

    confirmation = input(
        "Type RESET to continue: "
    )

    if confirmation != "RESET":
        print("Database reset cancelled.")
        return

    # Delete the database and SQLite auxiliary files.
    for suffix in ("", "-wal", "-shm", "-journal"):
        path = Path(str(db_path) + suffix)

        if path.exists():
            path.unlink()
            print(f"Deleted: {path.name}")

    # Recreate all database tables.
    init_db()
    init_additional_tables()
    init_registrar_tables()

    print("\nDatabase reset successfully.")
    print("All tables have been recreated.")
    print("Run seed scripts to populate the database.")


if __name__ == "__main__":
    main()
