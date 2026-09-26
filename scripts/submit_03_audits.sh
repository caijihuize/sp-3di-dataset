#!/usr/bin/env bash
# Submit after split/export job finishes.
#SBATCH --job-name=spv3_audit
#SBATCH --partition=qgpu_3090
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --gres=gpu:1
#SBATCH --time=2-00:00:00
#SBATCH --output=runs/spv3_audit_%j.out
#SBATCH --error=runs/spv3_audit_%j.err
set -euo pipefail
ROOT="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "${ROOT}"
bash scripts/06_audit_sequences.sh
\n