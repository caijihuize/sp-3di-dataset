"""Write compact build provenance after split generation."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from sp_dataset.provenance import version  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_counts(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    return dict(line.rstrip("\n").split("\t", 1) for line in path.open())


def main() -> None:
    source = ROOT / "manifests/sp_v3/source_manifest.json"
    config = ROOT / "configs/sp_v3.yaml"
    repair_path = ROOT / "manifests/sp_v3/repair_state.json"
    repair = json.loads(repair_path.read_text()) if repair_path.is_file() else {}
    record = {
        "dataset_version": "sp_v3_candidate",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_manifest": json.loads(source.read_text()),
        "config_sha256": sha256(config),
        "config_path": "configs/sp_v3.yaml",
        "mmseqs_version": version(os.environ.get("MMSEQS_BIN", "mmseqs")),
        "foldseek_version": version(os.environ.get("FOLDSEEK_BIN", "foldseek")),
        "python_version": sys.version,
        "git_revision": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        ).stdout.strip() or None,
        "counts": {
            "filter": read_counts(ROOT / "data/interim/candidates/filter_counts.tsv"),
            "split": read_counts(ROOT / "manifests/sp_v3/split_counts.tsv"),
        },
        "sequence_audit": {
            "status": repair.get("status", "not_run"),
            "repair_rounds": repair.get("audit_rounds", []),
            "target_shard_size": 50000,
            "max_sequences_per_query_per_shard": 100000,
            "final_audit_directory": "data/interim/final_sequence_round_*",
        },
        "structure_audit": {
            "status": "completed",
            "alignment_type": 2,
            "evalue": 1e-3,
            "minimum_bidirectional_coverage": 0.50,
            "top_neighbors_per_query": 10,
            "tmscore_normalizations": ["query_length", "target_length"],
            "backtrace_saved": True,
        },
        "parameters": {
            "min_length": 16,
            "mean_ca_plddt_min": 70,
            "unknown_aa_max_fraction": 0.20,
            "mmseqs_min_seq_id": 0.30,
            "mmseqs_coverage": 0.80,
            "mmseqs_cov_mode": 0,
            "mmseqs_alignment_mode": 3,
            "split_seed": 42,
            "valid_groups": 1000,
            "test_groups": 1000,
            "evaluation_length": [30, 510],
        },
    }
    out = ROOT / "manifests/sp_v3/build_manifest.json"
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(out)


if __name__ == "__main__":
    main()
\n