#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -z "${SP_PYTHON:-}" && -x /hpcfs/fhome/caihuize/miniconda3/envs/ESM3_3Di_3090/bin/python ]]; then
  SP_PYTHON=/hpcfs/fhome/caihuize/miniconda3/envs/ESM3_3Di_3090/bin/python
fi
SP_PYTHON="${SP_PYTHON:-python}"
"${SP_PYTHON}" -c 'import datasets' >/dev/null 2>&1 || {
  echo "datasets package unavailable in ${SP_PYTHON}; install environment.yml or set SP_PYTHON" >&2
  exit 1
}
EXPORT_ARGS=()
if [[ "${SKIP_PDB:-0}" == "1" ]]; then
  EXPORT_ARGS+=(--skip-pdb)
else
  EXPORT_ARGS+=(--tar "${ROOT}/data/raw/swissprot_pdb_v6.tar")
fi
"${SP_PYTHON}" "${ROOT}/src/sp_dataset/export_splits.py" \
  --records "${ROOT}/data/interim/candidates/records.tsv" \
  --manifest-dir "${ROOT}/manifests/sp_v3" \
  --out-dir "${ROOT}/data/processed/sp_v3" --overwrite "${EXPORT_ARGS[@]}"
\n