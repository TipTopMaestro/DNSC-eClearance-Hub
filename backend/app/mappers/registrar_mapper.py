
import re

from pydantic import ValidationError

from app.schemas import StudentRecord


EXPECTED_FIELDS = {
    "id",
    "name",
    "program",
    "year",
    "email"
}


def map_registrar_record(source) -> StudentRecord:
    # 1. Validate source structure.
    if not isinstance(source, dict):
        raise ValueError(
            "Student record must be an object."
        )

    if set(source) != EXPECTED_FIELDS:
        raise ValueError(
            "Missing or unexpected Registrar fields."
        )

    # 2. Validate text fields.
    for field in ("id", "name", "program", "email"):
        if not isinstance(source[field], str):
            raise ValueError(
                f"Invalid type for {field}."
            )

    # 3. Validate and convert year level.
    year = source["year"]

    if isinstance(year, str):
        year = year.strip()

        if not re.fullmatch(r"[1-4]", year):
            raise ValueError(
                "Year level is not a valid whole number."
            )

        year = int(year)

    elif type(year) is not int:
        raise ValueError(
            "Year level must be an integer."
        )

    # 4. Transform and validate the target schema.
    try:
        return StudentRecord(
            student_id=source["id"].strip(),
            full_name=source["name"].strip(),
            program=source["program"].strip().upper(),
            year_level=year,
            email=source["email"].strip()
        )

    except ValidationError as error:
        fields = ", ".join(
            str(item["loc"][0])
            for item in error.errors()
        )

        raise ValueError(
            f"Invalid student fields: {fields}"
        ) from None
