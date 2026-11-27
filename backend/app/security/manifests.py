import hashlib
import hmac
import json
import re

from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID

from app.config import (
    EXCHANGE_KEY_LIBRARY,
    EXCHANGE_KEY_ACCOUNTING
)

from app.utils.dates import utc_now


def get_office_key(office: str) -> bytes:
    keys = {
        "LIBRARY": EXCHANGE_KEY_LIBRARY,
        "ACCOUNTING": EXCHANGE_KEY_ACCOUNTING
    }

    if office not in keys:
        raise ValueError("Unsupported import office.")

    return keys[office].encode("utf-8")


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sign(data: bytes, key: bytes) -> str:
    return hmac.new(
        key,
        data,
        hashlib.sha256
    ).hexdigest()


def canonical_json(data: dict) -> bytes:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False
    ).encode("utf-8")


def build_manifest(
    data: bytes,
    office: str,
    period_id: int,
    filename: str
) -> dict:

    key = get_office_key(office)

    manifest = {
        "batch_id": str(uuid4()),
        "office": office,
        "period_id": period_id,
        "filename": filename,
        "created_at": utc_now(),
        "sha256": sha256_of(data),
        "file_hmac": sign(data, key)
    }

    manifest["manifest_hmac"] = sign(
        canonical_json(manifest),
        key
    )

    return manifest

#Verification of manifest
def verify_manifest(
    data: bytes,
    manifest: dict,
    filename: str
):
    expected = {
        "batch_id",
        "office",
        "period_id",
        "filename",
        "created_at",
        "sha256",
        "file_hmac",
        "manifest_hmac"
    }

    if not isinstance(manifest, dict):
        raise ValueError("Invalid manifest.")

    if set(manifest) != expected:
        raise ValueError("Invalid manifest fields.")

    if type(manifest["period_id"]) is not int:
        raise ValueError("Invalid period ID.")

    if manifest["period_id"] <= 0:
        raise ValueError("Invalid period ID.")

    for field in expected - {"period_id"}:
        if not isinstance(manifest[field], str):
            raise ValueError("Invalid manifest field type.")

    office = manifest["office"]
    key = get_office_key(office)

    # Validate the batch identifier.
    try:
        batch_id = UUID(manifest["batch_id"])

        if str(batch_id) != manifest["batch_id"]:
            raise ValueError()

    except ValueError:
        raise ValueError("Invalid batch ID.") from None

    # Validate the filename and extension.
    extension = ".csv" if office == "ACCOUNTING" else ".xml"

    if (
        not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}",
            manifest["filename"]
        )
        or not manifest["filename"].endswith(extension)
        or manifest["filename"] != filename
    ):
        raise ValueError("Invalid or mismatched filename.")

    # Validate the UTC timestamp.
    try:
        created_at = datetime.fromisoformat(
            manifest["created_at"]
        )

        if (
            created_at.tzinfo != timezone.utc
            or created_at.isoformat(timespec="seconds")
            != manifest["created_at"]
        ):
            raise ValueError()

    except ValueError:
        raise ValueError("Invalid batch timestamp.") from None

    # Allow a small difference between office clocks.
    if created_at > (
        datetime.now(timezone.utc)
        + timedelta(minutes=5)
    ):
        raise ValueError("Batch timestamp is in the future.")

    # Validate hexadecimal signature formats.
    for field in (
        "sha256",
        "file_hmac",
        "manifest_hmac"
    ):
        if not re.fullmatch(
            r"[0-9a-f]{64}",
            manifest[field]
        ):
            raise ValueError("Invalid signature format.")

    # 1. Verify the manifest itself.
    unsigned_manifest = manifest.copy()

    supplied_signature = unsigned_manifest.pop(
        "manifest_hmac"
    )

    expected_signature = sign(
        canonical_json(unsigned_manifest),
        key
    )

    if not hmac.compare_digest(
        expected_signature,
        supplied_signature
    ):
        raise ValueError("Invalid manifest signature.")

    # 2. Verify the file fingerprint.
    if not hmac.compare_digest(
        sha256_of(data),
        manifest["sha256"]
    ):
        raise ValueError("File hash mismatch.")

    # 3. Verify the file signature.
    if not hmac.compare_digest(
        sign(data, key),
        manifest["file_hmac"]
    ):
        raise ValueError("Invalid file signature.")

# Reads the signed manifest safely
MAX_MANIFEST_BYTES = 16_384


def read_manifest(data: bytes) -> dict:
    if len(data) > MAX_MANIFEST_BYTES:
        raise ValueError("Manifest is too large.")

    def unique_fields(pairs):
        result = {}

        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate manifest field.")

            result[key] = value

        return result

    try:
        manifest = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=unique_fields
        )

    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("Invalid manifest JSON.") from None

    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a JSON object.")

    return manifest
