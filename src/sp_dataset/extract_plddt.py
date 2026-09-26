"""Stream a PDB tar and calculate mean CA B-factor (AlphaFold pLDDT) per model."""

from __future__ import annotations

import argparse
import gzip
import os
import tarfile


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tar", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--max-models", type=int, default=0, help="0 means all records")
    a = p.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    written = skipped = 0
    with tarfile.open(a.tar, "r") as archive, open(a.out, "w") as out:
        out.write("id\tmean_plddt\tn_ca\n")
        for member in archive:
            if not member.isfile() or not member.name.lower().endswith((".pdb", ".pdb.gz")):
                continue
            source = archive.extractfile(member)
            if source is None:
                skipped += 1
                continue
            try:
                data = gzip.decompress(source.read()) if member.name.lower().endswith(".gz") else source.read()
            except (OSError, EOFError):
                skipped += 1
                continue
            total = count = 0
            for line in data.splitlines():
                if line.startswith(b"ATOM") and len(line) >= 66 and line[12:16] == b" CA ":
                    try:
                        total += float(line[60:66])
                        count += 1
                    except ValueError:
                        pass
            if not count:
                skipped += 1
                continue
            model = os.path.basename(member.name)
            model = model[:-7] if model.lower().endswith(".pdb.gz") else model[:-4]
            out.write(f"{model}\t{total / count:.3f}\t{count}\n")
            written += 1
            if written % 2000 == 0:
                print(f"[INFO] parsed {written} structures", flush=True)
            if a.max_models and written >= a.max_models:
                break
    print(f"[INFO] wrote={written} skipped={skipped} output={a.out}")


if __name__ == "__main__":
    main()

\n