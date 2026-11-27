import argparse
import json
from pathlib import Path

from app.importers.pipeline import (
    prepare_import,
    MAX_FILE_BYTES
)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("period_id", type=int)

    args = parser.parse_args()

    files = [
        ("LIBRARY", "mock_sources/library.xml"),
        ("ACCOUNTING", "mock_sources/accounting.csv")
    ]

    for office, filename in files:
        print(f"\n--- {office} ---")

        try:
            with Path(filename).open("rb") as file:
                data = file.read(MAX_FILE_BYTES + 1)

            accepted, rejected = prepare_import(
                data,
                office,
                args.period_id
            )

        except (OSError, ValueError) as error:
            print(f"Import failed: {error}")
            continue

        print(f"Accepted: {len(accepted)}")
        print(f"Rejected: {len(rejected)}")

        print(json.dumps({
            "accepted": [
                record.model_dump()
                for record in accepted
            ],
            "rejected": rejected
        }, indent=4))


if __name__ == "__main__":
    main()
