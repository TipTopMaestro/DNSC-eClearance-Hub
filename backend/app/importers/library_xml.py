from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException


def read_library_xml(data: bytes) -> list[dict]:
    try:
        root = ET.fromstring(
            data,
            forbid_dtd=True
        )

    except (ET.ParseError, DefusedXmlException):
        raise ValueError(
            "Malformed or unsafe Library XML."
        ) from None

    if root.tag != "library" or root.attrib:
        raise ValueError("Invalid Library XML root.")

    records = []

    for student in root:
        if student.tag != "student":
            raise ValueError("Unexpected XML element.")

        if set(student.attrib) - {"id"}:
            raise ValueError("Unexpected student attribute.")

        record = {
            "id": student.get("id")
        }

        for child in student:
            if (
                child.tag not in {
                    "unreturned_books",
                    "unpaid_fines"
                }
                or child.tag in record
                or child.attrib
                or len(child) > 0
            ):
                raise ValueError("Invalid Library XML structure.")

            record[child.tag] = child.text

        records.append(record)

    return records
