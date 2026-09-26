"""Pair AA/3Di records by stable ID and write retained/excluded manifests."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

AA = set("ACDEFGHIKLMNPQRSTVWY")
DI = set("algvsredtipkfqnymhwc")
AF_RE = re.compile(r"(AF-[A-Z0-9]+-F\d+(?:-model_v\d+)?)", re.I)


def fasta(path: str):
    key, chunks = None, []
    with open(path, encoding="ascii", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if key is not None:
                    yield key, "".join(chunks)
                token = line[1:].split()[0]
                match = AF_RE.search(token)
                key = match.group(1).upper() if match else re.sub(r"_[A-Za-z0-9]+$", "", token)
                chunks = []
            else:
                chunks.append(line)
        if key is not None:
            yield key, "".join(chunks)


def unique_fasta(path: str, label: str):
    data = {}
    for key, seq in fasta(path):
        if key in data:
            raise ValueError(f"Duplicate normalized ID in {label}: {key}")
        data[key] = seq
    return data


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--aa", required=True)
    p.add_argument("--di", required=True)
    p.add_argument("--plddt", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--min-length", type=int, default=16)
    p.add_argument("--max-length", type=int, default=0)
    p.add_argument("--min-plddt", type=float, default=70)
    a = p.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    aa, di = unique_fasta(a.aa, "AA"), unique_fasta(a.di, "3Di")
    scores = {}
    with open(a.plddt, newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            token = row["id"]
            match = AF_RE.search(token)
            key = match.group(1).upper() if match else token
            scores[key] = float(row["mean_plddt"])

    counts = {"aa_records": len(aa), "3di_records": len(di), "plddt_records": len(scores)}
    excluded = []
    kept = []
    for key in sorted(set(aa) | set(di) | set(scores)):
        reason = None
        if key not in aa:
            reason = "missing_aa"
        elif key not in di:
            reason = "missing_3di"
        elif key not in scores:
            reason = "missing_plddt"
        else:
            aaseq, diseq = aa[key].upper(), di[key].lower()
            if len(aaseq) != len(diseq):
                reason = "length_mismatch"
            elif len(aaseq) < a.min_length:
                reason = "too_short"
            elif a.max_length and len(aaseq) > a.max_length:
                reason = "too_long"
            elif sum(ch not in AA for ch in aaseq) / len(aaseq) > 0.20:
                reason = "too_many_unknown_aa"
            elif any(ch not in DI for ch in diseq):
                reason = "invalid_3di"
            elif scores[key] < a.min_plddt:
                reason = "low_plddt"
        if reason:
            excluded.append((key, reason))
        else:
            kept.append((key, aa[key].upper(), di[key].lower(), scores[key]))

    with open(out / "records.tsv", "w", newline="") as h, \
         open(out / "aa.filtered.fasta", "w") as fa, \
         open(out / "3di.filtered.fasta", "w") as fd:
        writer = csv.writer(h, delimiter="\t", lineterminator="\n")
        writer.writerow(["id", "length", "mean_plddt", "aa", "3di"])
        for key, aaseq, diseq, score in kept:
            writer.writerow([key, len(aaseq), f"{score:.3f}", aaseq, diseq])
            fa.write(f">{key}\n{aaseq}\n")
            fd.write(f">{key}\n{diseq}\n")
    with open(out / "excluded.tsv", "w", newline="") as h:
        writer = csv.writer(h, delimiter="\t", lineterminator="\n")
        writer.writerow(["id", "reason"])
        writer.writerows(excluded)
    counts.update({"kept": len(kept), "excluded": len(excluded)})
    with open(out / "filter_counts.tsv", "w") as h:
        for key, value in counts.items():
            h.write(f"{key}\t{value}\n")
    print(counts)


if __name__ == "__main__":
    main()

\n