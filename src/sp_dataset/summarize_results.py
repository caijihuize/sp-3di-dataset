"""Create a compact, machine-readable SP v3 result and audit summary."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path


def tsv_rows(path: Path):
    if not path.is_file():
        return []
    with path.open() as handle:
        return [row for row in csv.reader(handle, delimiter="\t") if row]


def count_tsv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    return dict(line.rstrip("\n").split("\t", 1) for line in path.open())


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--sequence-audit", required=True)
    p.add_argument("--structure-audit", required=True)
    p.add_argument("--output", default="reports/sp_v3/summary.json")
    a = p.parse_args()
    root = Path(__file__).resolve().parents[2]
    manifests = root / "manifests/sp_v3"
    seq, struct = Path(a.sequence_audit), Path(a.structure_audit)
    split_ids = {name: (manifests / f"{name}_ids.txt").read_text().splitlines()
                 for name in ("train", "valid", "test")}
    flat = sum(split_ids.values(), [])
    sequence = {}
    for name in ("valid_train", "test_train", "valid_test"):
        rows = tsv_rows(seq / f"{name}.tsv")
        valid = [r for r in rows if len(r) >= 8 and float(r[2]) >= 0.30
                 and float(r[4]) >= 0.80 and float(r[5]) >= 0.80]
        sequence[name] = {
            "reported_alignments": len(rows),
            "threshold_violations": len(valid),
            "queries_with_violation": len({r[0] for r in valid}),
        }
    structure = {}
    for name in ("valid_train", "test_train", "valid_test"):
        rows = tsv_rows(struct / f"{name}.tsv")
        query_scores = [float(r[8]) for r in rows if len(r) > 9]
        target_scores = [float(r[9]) for r in rows if len(r) > 9]
        structure[name] = {
            "reported_neighbors": len(rows),
            "queries_with_neighbor": len({r[0] for r in rows if len(r) > 1}),
            "maximum_query_length_normalized_tmscore": max(query_scores) if query_scores else None,
            "median_query_length_normalized_tmscore": statistics.median(query_scores) if query_scores else None,
            "maximum_target_length_normalized_tmscore": max(target_scores) if target_scores else None,
            "median_target_length_normalized_tmscore": statistics.median(target_scores) if target_scores else None,
        }
    missing_pdb = manifests / "pdb_missing_ids.txt"
    report = {
        "dataset_version": "sp_v3_candidate",
        "split_counts": {k: len(v) for k, v in split_ids.items()},
        "split_ids_unique": len(flat) == len(set(flat)),
        "split_ids_disjoint": len(flat) == len(set(flat)),
        "filter_counts": count_tsv(root / "data/interim/candidates/filter_counts.tsv"),
        "cluster_split_counts": count_tsv(manifests / "split_counts.tsv"),
        "evaluation_pdb_missing": len(missing_pdb.read_text().splitlines()) if missing_pdb.exists() else None,
        "sequence_audit_protocol": {
            "minimum_identity": 0.30,
            "minimum_coverage_both_sequences": 0.80,
            "target_records_per_shard": 50000,
            "results": sequence,
        },
        "foldseek_structure_audit": {
            "alignment_type": 2,
            "evalue": 1e-3,
            "minimum_bidirectional_coverage": 0.50,
            "top_neighbors_per_query": 10,
            "tmscore_normalization": ["query_length", "target_length"],
            "results": structure,
        },
    }
    target = root / a.output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(target)


if __name__ == "__main__":
    main()
\n