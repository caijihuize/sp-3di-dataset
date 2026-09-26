"""Export split FASTA/Hugging Face rows and selected evaluation PDBs."""

from __future__ import annotations

import argparse
import csv
import gzip
import os
import re
import shutil
import tarfile
from pathlib import Path


def model_id(name):
    base = os.path.basename(name)
    return re.sub(r"\.pdb(?:\.gz)?$", "", base, flags=re.I).upper()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--records", required=True)
    p.add_argument("--manifest-dir", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--tar", default="")
    p.add_argument("--skip-pdb", action="store_true")
    p.add_argument("--overwrite", action="store_true")
    a = p.parse_args()
    records = {}
    with open(a.records, newline="") as h:
        for row in csv.DictReader(h, delimiter="\t"):
            records[row["id"]] = row
    manifest, out = Path(a.manifest_dir), Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    id_maps = {}
    for split in ("train", "valid", "test"):
        ids = (manifest / f"{split}_ids.txt").read_text().splitlines()
        missing = sorted(set(ids) - records.keys())
        if missing:
            raise SystemExit(f"{split}: {len(missing)} IDs missing from records, first={missing[:5]}")
        id_maps[split] = ids
        with open(out / f"{split}.fasta", "w") as h:
            for pid in ids:
                h.write(f">{pid}\n{records[pid]['aa']}\n")
        with open(out / f"{split}_3di.fasta", "w") as h:
            for pid in ids:
                h.write(f">{pid}\n{records[pid]['3di']}\n")
        with open(manifest / f"{split}_row_index.tsv", "w") as h:
            h.write("row_index\tid\n")
            for i, pid in enumerate(ids):
                h.write(f"{i}\t{pid}\n")

        try:
            from datasets import Dataset
        except ImportError:
            print("datasets package missing; wrote split FASTA and row-index manifests only")
            continue
        (out / "hf").mkdir(parents=True, exist_ok=True)
        hf_split = out / "hf" / split
        if hf_split.exists():
            if not a.overwrite:
                raise SystemExit(f"Output exists (pass --overwrite to replace): {hf_split}")
            shutil.rmtree(hf_split)
        ds = Dataset.from_dict({"sequence_x": [records[x]["3di"] for x in ids],
                                "sequence_y": [records[x]["aa"] for x in ids]})
        ds.save_to_disk(str(hf_split))

    if not a.tar or a.skip_pdb:
        return
    pdb_root = out / "pdb"
    for split in ("valid", "test"):
        (pdb_root / split).mkdir(parents=True, exist_ok=True)
        if a.overwrite:
            for existing in (pdb_root / split).glob("*.pdb"):
                existing.unlink()
    wanted = {pid: split for split in ("valid", "test") for pid in id_maps[split]}
    found = set()
    with tarfile.open(a.tar, "r") as archive:
        for member in archive:
            if not member.isfile() or not member.name.lower().endswith((".pdb", ".pdb.gz")):
                continue
            pid = model_id(member.name)
            if pid not in wanted:
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                continue
            data = extracted.read()
            if member.name.lower().endswith(".gz"):
                data = gzip.decompress(data)
            (pdb_root / wanted[pid] / f"{pid}.pdb").write_bytes(data)
            found.add(pid)
    missing = sorted(set(wanted) - found)
    (manifest / "pdb_missing_ids.txt").write_text("".join(f"{x}\n" for x in missing))
    print(f"PDB extracted: {len(found)}/{len(wanted)}; missing={len(missing)}")


if __name__ == "__main__":
    main()
\n