import argparse
import json

from pathlib import Path

from app.security.manifests import (
    build_manifest,
    verify_manifest
)

from app.importers.pipeline import MAX_FILE_BYTES


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("file", type=Path)

    parser.add_argument(
        "office",
        choices=["LIBRARY", "ACCOUNTING"]
    )

    parser.add_argument("period_id", type=int)
    parser.add_argument("output", type=Path)

    args = parser.parse_args()

    try:
        with args.file.open("rb") as file:
            data = file.read(MAX_FILE_BYTES + 1)

        if len(data) > MAX_FILE_BYTES:
            raise ValueError("Import file is too large.")

        manifest = build_manifest(
            data,
            args.office,
            args.period_id,
            args.file.name
        )

        verify_manifest(
            data,
            manifest,
            args.file.name
        )

        args.output.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with args.output.open(
            "x",
            encoding="utf-8"
        ) as file:
            json.dump(manifest, file, indent=4)

    except (OSError, ValueError) as error:
        parser.exit(1, f"Signing failed: {error}\n")

    print("Manifest created:", args.output)
    print("Batch ID:", manifest["batch_id"])


if __name__ == "__main__":
    main()
