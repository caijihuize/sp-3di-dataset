#!/usr/bin/env bash
# Submit after features finish.
#SBATCH --job-name=spv3_cluster
#SBATCH --partition=qgpu_3090
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --gres=gpu:1
#SBATCH --time=2-00:00:00
#SBATCH --output=runs/spv3_cluster_%j.out
#SBATCH --error=runs/spv3_cluster_%j.err
set -euo pipefail
ROOT="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "${ROOT}"
bash scripts/03_prepare_candidates.sh
bash scripts/04_mmseqs_cluster.sh
bash scripts/05_split_clusters.sh
bash scripts/07_export_splits.sh
bash scripts/09_record_build.sh
\n