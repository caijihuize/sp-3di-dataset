#!/usr/bin/env bash
#SBATCH --job-name=spv3_features
#SBATCH --partition=qgpu_3090
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --time=2-00:00:00
#SBATCH --output=runs/spv3_features_%j.out
#SBATCH --error=runs/spv3_features_%j.err
set -euo pipefail
ROOT="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "${ROOT}"
bash scripts/01_extract_features.sh
bash scripts/02_extract_plddt.sh
\n