"""Validate final ID/HF alignment and inverse-folding PDB sequence mapping."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from datasets import load_from_disk

AA3_TO_1 = {
    "ALA":"A", "ARG":"R", "ASN":"N", "ASP":"D", "CYS":"C", "GLN":"Q",
    "GLU":"E", "GLY":"G", "HIS":"H", "ILE":"I", "LEU":"L", "LYS":"K",
    "MET":"M", "PHE":"F", "PRO":"P", "SER":"S", "THR":"T", "TRP":"W",
    "TYR":"Y", "VAL":"V", "UNK":"X",
}


def pdb_sequence(path: Path) -> str:
    seen = set()
    residues = []
    for line in path.read_text(errors="replace").splitlines():
        if not line.startswith("ATOM") or line[12:16] != " CA ":
            continue
        key = (line[21:22], line[22:27])
        if key in seen:
            continue
        seen.add(key)
        residues.append(AA3_TO_1.get(line[17:20].strip(), "X"))
    return "".join(residues)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = root / "manifests/sp_v3"
    processed = root / "data/processed/sp_v3"
    records = {}
    with (root / "data/interim/candidates/records.tsv").open(newline="") as h:
        records = {row["id"]: row for row in csv.DictReader(h, delimiter="\t")}
    split_ids = {name: (manifest / f"{name}_ids.txt").read_text().splitlines()
                 for name in ("train", "valid", "test")}
    all_ids = sum(split_ids.values(), [])
    checks = {
        "ids_unique_and_disjoint": len(all_ids) == len(set(all_ids)),
        "split_counts": {k: len(v) for k, v in split_ids.items()},
        "hf_rows_match_id_counts": {},
        "hf_row_order_matches_manifests": {},
        "evaluation_pdb_counts": {},
        "evaluation_pdb_sequence_matches_aa": {},
    }
    if not checks["ids_unique_and_disjoint"]:
        raise SystemExit("Split ID files contain duplicate IDs or cross-split overlap")
    for split, ids in split_ids.items():
        index_rows = list(csv.DictReader((manifest / f"{split}_row_index.tsv").open(), delimiter="\t"))
        checks["hf_row_order_matches_manifests"][split] = [r["id"] for r in index_rows] == ids
        if not checks["hf_row_order_matches_manifests"][split]:
            raise SystemExit(f"{split} row_index.tsv does not match its ID manifest")
        dataset = load_from_disk(str(processed / "hf" / split))
        checks["hf_rows_match_id_counts"][split] = len(dataset) == len(ids)
        if not checks["hf_rows_match_id_counts"][split]:
            raise SystemExit(f"{split} HF row count does not match ID manifest")
        if dataset.column_names != ["sequence_x", "sequence_y"]:
            raise SystemExit(f"Unexpected {split} columns: {dataset.column_names}")
        for i, pid in enumerate(ids):
            if dataset[i]["sequence_x"] != records[pid]["3di"] or dataset[i]["sequence_y"] != records[pid]["aa"]:
                raise SystemExit(f"HF row order/content mismatch at {split}:{i} ({pid})")

    for split in ("valid", "test"):
        ids = split_ids[split]
        pdb_dir = processed / "pdb" / split
        checks["evaluation_pdb_counts"][split] = len(list(pdb_dir.glob("*.pdb")))
        if checks["evaluation_pdb_counts"][split] != len(ids):
            raise SystemExit(f"{split} PDB count differs from split IDs")
        mismatches = []
        for pid in ids:
            path = pdb_dir / f"{pid}.pdb"
            if not path.is_file():
                mismatches.append({"id": pid, "reason": "missing_pdb"})
                continue
            observed = pdb_sequence(path)
            expected = records[pid]["aa"]
            if observed != expected:
                mismatches.append({"id": pid, "reason": "sequence_mismatch",
                                   "pdb_length": len(observed), "aa_length": len(expected)})
        checks["evaluation_pdb_sequence_matches_aa"][split] = {"checked": len(ids), "mismatches": mismatches}
        if mismatches:
            raise SystemExit(f"{split}: {len(mismatches)} PDB/AA sequence mismatches; see report")
    checks["status"] = "passed"
    target = root / "reports/sp_v3/validation.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(checks, indent=2) + "\n")
    print(target)


if __name__ == "__main__":
    main()

\n