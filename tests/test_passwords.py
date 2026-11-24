from app.security.passwords import (
    hash_password,
    check_password
)


def test_correct_password():
    stored = hash_password("DemoPassword123!")

    assert check_password(
        "DemoPassword123!", stored
    )


def test_wrong_password():
    stored = hash_password("DemoPassword123!")

    assert not check_password(
        "WrongPassword", stored
    )


def test_random_salt():
    first = hash_password("DemoPassword123!")
    second = hash_password("DemoPassword123!")

    assert first != second
