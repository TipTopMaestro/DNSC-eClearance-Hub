
from collections import Counter

from pydantic import ValidationError

from app.importers.accounting_csv import read_accounting_csv
from app.importers.library_xml import read_library_xml

from app.mappers.accounting_mapper import map_accounting_record
from app.mappers.library_mapper import map_library_record

from app.repositories.students import list_students
from app.repositories.periods import find_period

from app.schemas import ClearanceRecordInput
from app.utils.validators import validate_student_id


MAX_FILE_BYTES = 1_000_000


def prepare_import(
    data: bytes,
    office: str,
    period_id: int
):
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("Import file is too large.")

    if type(period_id) is not int or period_id <= 0:
        raise ValueError("Invalid clearance period ID.")

    if find_period(period_id) is None:
        raise ValueError("Clearance period not found.")

    # 1. Extract source records.
    if office == "ACCOUNTING":
        source_records = read_accounting_csv(data)
        mapper = map_accounting_record
        id_field = "student_no"

    elif office == "LIBRARY":
        source_records = read_library_xml(data)
        mapper = map_library_record
        id_field = "id"

    else:
        raise ValueError("Unsupported import office.")

    if not source_records:
        raise ValueError("Import file contains no records.")

    # 2. Retrieve the Registrar masterlist.
    student_ids = {
        student["student_id"]
        for student in list_students()
    }

    # Count repeated student IDs.
    counts = Counter(
        source[id_field].strip()
        for source in source_records
        if validate_student_id(source.get(id_field))
    )

    accepted = []
    rejected = []

    # 3. Validate and transform each record.
    for number, source in enumerate(
        source_records,
        start=1
    ):
        try:
            mapped = mapper(source)

            student_id = mapped["student_id"]

            if counts[student_id] > 1:
                raise ValueError("Duplicate student ID.")

            if student_id not in student_ids:
                raise ValueError(
                    "Student not found in Registrar masterlist."
                )

            # 4. Assign period and validate common schema.
            record = ClearanceRecordInput(
                **mapped,
                period_id=period_id
            )

            accepted.append(record)

        except ValidationError:
            rejected.append({
                "record_number": number,
                "reason": "Invalid clearance record."
            })

        except ValueError as error:
            rejected.append({
                "record_number": number,
                "reason": str(error)
            })

    return accepted, rejected
