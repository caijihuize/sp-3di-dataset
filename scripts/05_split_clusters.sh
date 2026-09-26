#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python "${ROOT}/src/sp_dataset/split_clusters.py" \
  --records "${ROOT}/data/interim/candidates/records.tsv" \
  --clusters "${ROOT}/data/interim/mmseqs/clusters.tsv" \
  --out-dir "${ROOT}/manifests/sp_v3" --seed 42 \
  --valid-groups 1000 --test-groups 1000 --eval-min-length 30 --eval-max-length 510

\n