import csv
import json

from io import StringIO
from xml.etree import ElementTree as ET

from app.database import get_db

from app.services.clearance_service import (
    calculate_overall_status
)

#Retrieves and prepare report data
REPORT_FIELDS = [
    "period_id",
    "student_id_masked",
    "registrar",
    "library",
    "accounting",
    "student_affairs",
    "overall_status"
]


def build_clearance_report(period_id: int) -> list[dict]:
    with get_db() as conn:
        conn.execute("BEGIN")

        period = conn.execute("""
            SELECT period_id
            FROM clearance_periods
            WHERE period_id = ?
        """, (period_id,)).fetchone()

        if period is None:
            raise ValueError("Clearance period not found.")

        students = conn.execute("""
            SELECT student_id
            FROM students
            ORDER BY student_id
        """).fetchall()

        records = conn.execute("""
            SELECT student_id, office, status,
                   reason, updated_at
            FROM clearance_records
            WHERE period_id = ?
        """, (period_id,)).fetchall()

    # Group clearance records by student ID.
    grouped = {}

    for record in records:
        grouped.setdefault(
            record["student_id"], []
        ).append(dict(record))

    report = []

    for student in students:
        student_id = student["student_id"]

        summary = calculate_overall_status(
            grouped.get(student_id, [])
        )

        offices = {
            office["office"]: office["status"]
            for office in summary["offices"]
        }

        report.append({
            "period_id": period_id,
            "student_id_masked": "****-" + student_id[-4:],
            "registrar": offices["REGISTRAR"],
            "library": offices["LIBRARY"],
            "accounting": offices["ACCOUNTING"],
            "student_affairs": offices["STUDENT_AFFAIRS"],
            "overall_status": summary["overall_status"]
        })

    return report

#Protects CSV cells
def safe_csv_cell(value):
    text = str(value)

    if (
        text.startswith(("\t", "\r", "\n"))
        or text.lstrip().startswith(("=", "+", "-", "@"))
    ):
        return "'" + text

    return text

#GENERATE CSV

def export_csv(report: list[dict]) -> bytes:
    output = StringIO(newline="")

    writer = csv.DictWriter(
        output,
        fieldnames=REPORT_FIELDS
    )

    writer.writeheader()

    for record in report:
        writer.writerow({
            field: safe_csv_cell(record[field])
            for field in REPORT_FIELDS
        })

    return output.getvalue().encode("utf-8")

#Generate JSON
def export_json(report: list[dict]) -> bytes:
    return json.dumps(
        report,
        indent=4,
        ensure_ascii=False
    ).encode("utf-8")
    
#Generate XML
def export_xml(report: list[dict]) -> bytes:
    root = ET.Element("clearance_report")

    for record in report:
        student = ET.SubElement(
            root, "student"
        )

        for field in REPORT_FIELDS:
            element = ET.SubElement(
                student, field
            )

            element.text = str(record[field])

    ET.indent(root, space="    ")

    return ET.tostring(
        root,
        encoding="utf-8",
        xml_declaration=True
    )