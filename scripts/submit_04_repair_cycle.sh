#!/usr/bin/env bash
#SBATCH --job-name=spv3_repair
#SBATCH --partition=qgpu_3090
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --gres=gpu:1
#SBATCH --time=2-00:00:00
#SBATCH --output=runs/spv3_repair_%j.out
#SBATCH --error=runs/spv3_repair_%j.err
set -euo pipefail
ROOT="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "${ROOT}"
PYTHON="${PYTHON:-python}"
REPAIR="${ROOT}/src/sp_dataset/repair_sequence_conflicts.py"
RECORDS="${ROOT}/data/interim/candidates/records.tsv"
MANIFESTS="${ROOT}/manifests/sp_v3"
STATUS_FILE="${MANIFESTS}/repair_state.json"
CURRENT_AUDIT="${ROOT}/data/interim/sequence"

"${PYTHON}" "${REPAIR}" --records "${RECORDS}" --manifest-dir "${MANIFESTS}" \
  --audit-dir "${CURRENT_AUDIT}"
for ROUND in $(seq -w 1 20); do
  STATUS=$("${PYTHON}" -c 'import json,sys; print(json.load(open(sys.argv[1])).get("status", "unknown"))' "${STATUS_FILE}")
  if [[ "${STATUS}" == "sequence_audit_passed" ]]; then break; fi
  SKIP_PDB=1 bash scripts/07_export_splits.sh
  CURRENT_AUDIT="${ROOT}/data/interim/audit_round_${ROUND}"
  AUDIT_DIR="${CURRENT_AUDIT}" bash scripts/06_audit_sequences.sh
  "${PYTHON}" "${REPAIR}" --records "${RECORDS}" --manifest-dir "${MANIFESTS}" \
    --audit-dir "${CURRENT_AUDIT}/sequence"
done
STATUS=$("${PYTHON}" -c 'import json,sys; print(json.load(open(sys.argv[1])).get("status", "unknown"))' "${STATUS_FILE}")
if [[ "${STATUS}" != "sequence_audit_passed" ]]; then
  echo "Sequence conflicts remain after 20 repair rounds; inspect audit outputs." >&2
  exit 1
fi
\n