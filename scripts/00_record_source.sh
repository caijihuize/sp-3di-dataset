#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python "${ROOT}/src/sp_dataset/provenance.py" \
  "${ROOT}/data/raw/swissprot_pdb_v6.tar" \
  --url "https://ftp.ebi.ac.uk/pub/databases/alphafold/latest/swissprot_pdb_v6.tar" \
  --output "${ROOT}/manifests/sp_v3/source_manifest.json"

\n