import logging
import sqlite3
import time

from pathlib import Path
from uuid import uuid4

from app.importers.pipeline import MAX_FILE_BYTES

from app.security.manifests import (
    read_manifest,
    MAX_MANIFEST_BYTES
)

from app.services.import_service import import_signed_file
from automation.daily_summary import generate_daily_summary


logger = logging.getLogger(__name__)


def process_batch(folder: Path):
    files = list(folder.iterdir())

    # A batch must contain exactly two regular files.
    if len(files) != 2 or any(
        file.is_symlink() or not file.is_file()
        for file in files
    ):
        raise ValueError("Invalid batch folder contents.")

    manifest_path = folder / "manifest.json"

    if manifest_path not in files:
        raise ValueError("Manifest file is missing.")

    data_path = next(
        file for file in files
        if file != manifest_path
    )

    if data_path.suffix not in {".csv", ".xml"}:
        raise ValueError("Unsupported file format.")

    with manifest_path.open("rb") as file:
        manifest = read_manifest(
            file.read(MAX_MANIFEST_BYTES + 1)
        )

    with data_path.open("rb") as file:
        data = file.read(MAX_FILE_BYTES + 1)

    return import_signed_file(
        data,
        manifest,
        data_path.name
    )


def process_drop(data_dir=Path("data")):
    drop = data_dir / "drop"
    archive = data_dir / "archive"
    rejected = data_dir / "rejected"

    for directory in (drop, archive, rejected):
        directory.mkdir(parents=True, exist_ok=True)

    results = {
        "processed": 0,
        "rejected": 0,
        "deferred": 0
    }

    for folder in sorted(drop.iterdir()):
        if folder.is_symlink() or not folder.is_dir():
            logger.warning("Skipped unexpected drop entry.")
            continue

        try:
            result = process_batch(folder)

        except ValueError as error:
            destination = rejected
            outcome = "rejected"

            logger.warning(
                "Batch rejected: %s",
                error
            )

        except (OSError, sqlite3.Error) as error:
            # Leave temporary failures for the next run.
            logger.error(
                "Batch deferred: %s",
                type(error).__name__
            )

            results["deferred"] += 1
            continue

        else:
            destination = archive
            outcome = "processed"

            logger.info(
                "Imported batch=%s office=%s accepted=%s rejected=%s",
                result["batch_id"],
                result["office"],
                result["accepted"],
                result["rejected"]
            )

        try:
            # Unique destination prevents name collisions.
            folder.rename(
                destination / uuid4().hex
            )

            results[outcome] += 1

        except OSError:
            logger.error("Unable to move batch folder.")
            results["deferred"] += 1

    return results


def main():
    Path("logs").mkdir(exist_ok=True)

    logging.Formatter.converter = time.gmtime

    logging.basicConfig(
        filename="logs/automation.log",
        level=logging.INFO,
        encoding="utf-8",
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ"
    )

    logger.info("Automation started.")

    results = process_drop()
    summary = generate_daily_summary()

    logger.info("Import results: %s", results)

    logger.info(
        "HOLD summary generated for period=%s",
        summary["period_id"]
    )

    logger.info("Automation finished.")

    print(results)

    return 1 if results["deferred"] else 0


if __name__ == "__main__":
    raise SystemExit(main())