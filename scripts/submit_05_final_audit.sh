#!/usr/bin/env bash
#SBATCH --job-name=spv3_finalaudit
#SBATCH --partition=qgpu_3090
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --gres=gpu:1
#SBATCH --time=2-00:00:00
#SBATCH --output=runs/spv3_finalaudit_%j.out
#SBATCH --error=runs/spv3_finalaudit_%j.err
set -euo pipefail
ROOT="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "${ROOT}"
PYTHON="${PYTHON:-python}"
REPAIR="${ROOT}/src/sp_dataset/repair_sequence_conflicts.py"
RECORDS="${ROOT}/data/interim/candidates/records.tsv"
MANIFESTS="${ROOT}/manifests/sp_v3"
STATUS_FILE="${MANIFESTS}/repair_state.json"

for ROUND in $(seq -w 1 20); do
  AUDIT_DIR="${ROOT}/data/interim/final_sequence_round_${ROUND}"
  AUDIT_DIR="${AUDIT_DIR}" bash scripts/06_audit_sequences.sh
  "${PYTHON}" "${REPAIR}" --records "${RECORDS}" --manifest-dir "${MANIFESTS}" \
    --audit-dir "${AUDIT_DIR}/sequence"
  STATUS=$("${PYTHON}" -c 'import json,sys; print(json.load(open(sys.argv[1])).get("status", "unknown"))' "${STATUS_FILE}")
  if [[ "${STATUS}" == "sequence_audit_passed" ]]; then break; fi
  SKIP_PDB=1 bash scripts/07_export_splits.sh
done
STATUS=$("${PYTHON}" -c 'import json,sys; print(json.load(open(sys.argv[1])).get("status", "unknown"))' "${STATUS_FILE}")
if [[ "${STATUS}" != "sequence_audit_passed" ]]; then
  echo "Sequence conflicts remain after 20 sharded audit rounds." >&2
  exit 1
fi
bash scripts/07_export_splits.sh
AUDIT_DIR="${ROOT}/data/interim/final_audit_sharded" bash scripts/08_audit_structures.sh
bash scripts/09_record_build.sh
python "${ROOT}/src/sp_dataset/summarize_results.py" \
  --sequence-audit "${AUDIT_DIR}/sequence" \
  --structure-audit "${ROOT}/data/interim/final_audit_sharded/structure"
\n