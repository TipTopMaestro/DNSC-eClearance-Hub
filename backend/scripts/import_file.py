import argparse
import json

from pathlib import Path

from app.importers.pipeline import MAX_FILE_BYTES

from app.security.manifests import (
    read_manifest,
    MAX_MANIFEST_BYTES
)

from app.services.import_service import (
    import_signed_file
)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("file", type=Path)
    parser.add_argument("manifest", type=Path)

    args = parser.parse_args()

    try:
        with args.file.open("rb") as file:
            data = file.read(MAX_FILE_BYTES + 1)

        with args.manifest.open("rb") as file:
            manifest = read_manifest(
                file.read(MAX_MANIFEST_BYTES + 1)
            )

        result = import_signed_file(
            data,
            manifest,
            args.file.name
        )

    except (OSError, ValueError) as error:
        parser.exit(1, f"Import rejected: {error}\n")

    print("Import completed successfully.")
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
