#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE="${ROOT}/data/raw/swissprot_pdb_v6.tar"
WORK="${ROOT}/data/interim"
FOLDSEEK_BIN="${FOLDSEEK_BIN:-foldseek}"
THREADS="${SLURM_CPUS_PER_TASK:-${THREADS:-16}}"
DB="${WORK}/foldseek/swissprot"
mkdir -p "${WORK}/foldseek"
[[ -s "${ARCHIVE}" ]] || { echo "Missing source archive: ${ARCHIVE}" >&2; exit 2; }
"${FOLDSEEK_BIN}" createdb "${ARCHIVE}" "${DB}" --threads "${THREADS}" \
  --file-include "\\.pdb(\\.gz)?$" -v 3
"${FOLDSEEK_BIN}" convert2fasta "${DB}" "${WORK}/aa.fasta"
"${FOLDSEEK_BIN}" lndb "${DB}_h" "${DB}_ss_h"
"${FOLDSEEK_BIN}" convert2fasta "${DB}_ss" "${WORK}/3di.fasta"
echo "AA: ${WORK}/aa.fasta"
echo "3Di: ${WORK}/3di.fasta"
\n