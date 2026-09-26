#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MMSEQS_BIN="${MMSEQS_BIN:-mmseqs}"
THREADS="${SLURM_CPUS_PER_TASK:-${THREADS:-32}}"
IN="${ROOT}/data/interim/candidates/aa.filtered.fasta"
OUT="${ROOT}/data/interim/mmseqs"
mkdir -p "${OUT}"
"${MMSEQS_BIN}" createdb "${IN}" "${OUT}/seqdb"
"${MMSEQS_BIN}" cluster "${OUT}/seqdb" "${OUT}/clusterdb" "${OUT}/tmp" \
  --min-seq-id 0.30 -c 0.80 --cov-mode 0 --alignment-mode 3 \
  --cluster-mode 0 -s 7.5 --max-seqs 300 --threads "${THREADS}"
"${MMSEQS_BIN}" createtsv "${OUT}/seqdb" "${OUT}/seqdb" "${OUT}/clusterdb" "${OUT}/clusters.tsv"
"${MMSEQS_BIN}" version > "${OUT}/version.txt"
printf '%q ' "${MMSEQS_BIN}" cluster "${OUT}/seqdb" "${OUT}/clusterdb" "${OUT}/tmp" \
  --min-seq-id 0.30 -c 0.80 --cov-mode 0 --alignment-mode 3 --cluster-mode 0 -s 7.5 --max-seqs 300 --threads "${THREADS}" \
  > "${OUT}/command.txt"

\n