from getpass import getpass

from app.database import (
    init_db,
    init_additional_tables
)

from app.repositories.users import (
    create_user,
    find_user_by_username
)

from app.repositories.students import find_student


def main():
    init_db()
    init_additional_tables()

    if find_student("2023-0104") is None:
        raise SystemExit(
            "Run scripts.seed_students first."
        )

    accounts = [
        {
            "username": "student01",
            "role": "STUDENT",
            "student_id": "2023-0104"
        },
        {
            "username": "library01",
            "role": "STAFF",
            "office": "LIBRARY"
        },
        {
            "username": "accounting01",
            "role": "STAFF",
            "office": "ACCOUNTING"
        },
        {
            "username": "registrar01",
            "role": "STAFF",
            "office": "REGISTRAR"
        },
        {
            "username": "affairs01",
            "role": "STAFF",
            "office": "STUDENT_AFFAIRS"
        },
        {
            "username": "admin01",
            "role": "ADMIN"
        }
    ]

    for account in accounts:
        username = account["username"]

        if find_user_by_username(username):
            print(f"{username} already exists.")
            continue

        password = getpass(
            f"Password for {username}: "
        )

        confirm = getpass("Confirm password: ")

        if password != confirm:
            print("Passwords do not match.")
            continue

        try:
            create_user(
                password=password,
                **account
            )

            print(f"{username} created successfully.")

        except ValueError as error:
            print(error)

    print("User setup finished.")


if __name__ == "__main__":
    main()
