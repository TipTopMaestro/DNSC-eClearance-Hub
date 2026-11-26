
def mask_student_id(student_id: str) -> str:
    if len(student_id) <= 4:
        return "*" * len(student_id)

    return (
        "*" * (len(student_id) - 4)
        + student_id[-4:]
    )


def mask_email(email: str) -> str:
    user, domain = email.split("@", 1)

    return (
        user[0]
        + "*" * (len(user) - 1)
        + "@"
        + domain
    )


def safe_cell(value) -> str:
    text = "" if value is None else str(value)

    stripped = text.lstrip()

    if (
        stripped.startswith(("=", "+", "-", "@"))
        or text.startswith(("\t", "\r", "\n"))
    ):
        return "'" + text

    return text
