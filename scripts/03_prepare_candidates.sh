#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python "${ROOT}/src/sp_dataset/prepare_candidates.py" \
  --aa "${ROOT}/data/interim/aa.fasta" \
  --di "${ROOT}/data/interim/3di.fasta" \
  --plddt "${ROOT}/data/interim/plddt.tsv" \
  --out-dir "${ROOT}/data/interim/candidates" \
  --min-length 16 --min-plddt 70

\n