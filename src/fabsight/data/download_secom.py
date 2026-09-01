"""Download and cache the official UCI SECOM dataset."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

import requests

from fabsight.config import SECOM_RAW_DIR

SECOM_URL = "https://archive.ics.uci.edu/static/public/179/secom.zip"
REQUIRED_FILES = ("secom.data", "secom_labels.data")


class SecomDownloadError(RuntimeError):
    """Raised when SECOM cannot be obtained from the official source."""


def missing_files(raw_dir: Path = SECOM_RAW_DIR) -> list[str]:
    """Return required SECOM filenames that are not cached."""
    return [name for name in REQUIRED_FILES if not (raw_dir / name).is_file()]


def manual_download_instructions(raw_dir: Path = SECOM_RAW_DIR) -> str:
    """Give exact recovery instructions for an unavailable network."""
    return (
        "Download the 'SECOM' dataset from the official UCI Machine Learning "
        "Repository:\nhttps://archive.ics.uci.edu/dataset/179/secom\n"
        f"Place secom.data and secom_labels.data in:\n{raw_dir.resolve()}"
    )


def download_secom(
    raw_dir: Path = SECOM_RAW_DIR, *, force: bool = False, timeout: int = 60
) -> tuple[Path, Path]:
    """Download SECOM once, safely extract required files, and return their paths."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    if not force and not missing_files(raw_dir):
        return tuple(raw_dir / name for name in REQUIRED_FILES)  # type: ignore[return-value]

    try:
        response = requests.get(SECOM_URL, timeout=timeout)
        response.raise_for_status()
        with tempfile.TemporaryDirectory(prefix="fabsight-secom-") as temp_name:
            temp_dir = Path(temp_name)
            archive_path = temp_dir / "secom.zip"
            archive_path.write_bytes(response.content)
            with zipfile.ZipFile(archive_path) as archive:
                for filename in REQUIRED_FILES:
                    matches = [
                        member
                        for member in archive.infolist()
                        if not member.is_dir() and Path(member.filename).name == filename
                    ]
                    if len(matches) != 1:
                        raise SecomDownloadError(
                            f"Official archive did not contain exactly one {filename}."
                        )
                    # Reading a named member directly avoids trusting archive paths.
                    with archive.open(matches[0]) as source, (raw_dir / filename).open(
                        "wb"
                    ) as destination:
                        shutil.copyfileobj(source, destination)
    except (requests.RequestException, OSError, zipfile.BadZipFile) as exc:
        raise SecomDownloadError(
            f"Could not download the official SECOM dataset: {exc}\n\n"
            f"{manual_download_instructions(raw_dir)}"
        ) from exc

    remaining = missing_files(raw_dir)
    if remaining:
        raise SecomDownloadError(
            f"Download finished but files are missing: {', '.join(remaining)}\n\n"
            f"{manual_download_instructions(raw_dir)}"
        )
    return tuple(raw_dir / name for name in REQUIRED_FILES)  # type: ignore[return-value]
