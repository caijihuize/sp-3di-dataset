"""Small utilities to record input and tool provenance."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: str | Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def version(command: str) -> str:
    try:
        result = subprocess.run([command, "version"], check=False, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=30)
        return result.stdout.strip().splitlines()[0] if result.stdout.strip() else f"exit={result.returncode}"
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"unavailable: {exc}"


def write_source_manifest(archive: str | Path, output: str | Path, url: str) -> dict:
    archive = Path(archive).resolve(strict=True)
    record = {
        "source_url": url,
        "archive_name": archive.name,
        "archive_bytes": archive.stat().st_size,
        "sha256": sha256_file(archive),
        "archive_path_at_generation": str(archive),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "mmseqs_version": version(os.environ.get("MMSEQS_BIN", "mmseqs")),
        "foldseek_version": version(os.environ.get("FOLDSEEK_BIN", "foldseek")),
    }
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Hash the source archive and record tool versions")
    parser.add_argument("archive")
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", default="manifests/sp_v3/source_manifest.json")
    args = parser.parse_args()
    record = write_source_manifest(args.archive, args.output, args.url)
    print(json.dumps(record, indent=2))

\n