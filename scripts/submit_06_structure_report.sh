#!/usr/bin/env bash
#SBATCH --job-name=spv3_struct_report
#SBATCH --partition=qgpu_3090
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00
#SBATCH --output=runs/spv3_struct_report_%j.out
#SBATCH --error=runs/spv3_struct_report_%j.err
set -euo pipefail
ROOT="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "${ROOT}"
AUDIT_DIR="${ROOT}/data/interim/final_structure_normalized" bash scripts/08_audit_structures.sh
bash scripts/09_record_build.sh
LATEST_SEQUENCE_AUDIT="$(find "${ROOT}/data/interim" -maxdepth 4 -path '*/sequence/valid_train.tsv' -printf '%h\n' | sort | tail -1)"
python "${ROOT}/src/sp_dataset/summarize_results.py" \
  --sequence-audit "${LATEST_SEQUENCE_AUDIT}" \
  --structure-audit "${ROOT}/data/interim/final_structure_normalized/structure"
SP_PYTHON="${SP_PYTHON:-/hpcfs/fhome/caihuize/miniconda3/envs/ESM3_3Di_3090/bin/python}"
"${SP_PYTHON}" "${ROOT}/src/sp_dataset/validate_release.py"
\n