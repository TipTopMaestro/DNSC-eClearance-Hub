import csv
from io import StringIO


def read_accounting_csv(data: bytes) -> list[dict]:
    try:
        text = data.decode("utf-8-sig")

        reader = csv.DictReader(
            StringIO(text, newline=""),
            strict=True
        )

        expected = {"student_no", "balance"}
        headers = reader.fieldnames or []

        if len(headers) != 2 or set(headers) != expected:
            raise ValueError("Invalid Accounting CSV headers.")

        return list(reader)

    except UnicodeDecodeError:
        raise ValueError("CSV must use UTF-8 encoding.") from None

    except csv.Error:
        raise ValueError("Malformed Accounting CSV.") from None
