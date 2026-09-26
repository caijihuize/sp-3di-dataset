#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python}"
"${PYTHON}" "${ROOT}/src/sp_dataset/extract_plddt.py" \
  --tar "${ROOT}/data/raw/swissprot_pdb_v6.tar" \
  --out "${ROOT}/data/interim/plddt.tsv"

\n