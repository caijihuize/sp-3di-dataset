#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FOLDSEEK_BIN="${FOLDSEEK_BIN:-foldseek}"
THREADS="${SLURM_CPUS_PER_TASK:-${THREADS:-32}}"
FSDB="${ROOT}/data/interim/foldseek/swissprot"
OUT="${AUDIT_DIR:-${ROOT}/data/interim}/structure"
mkdir -p "${OUT}"
for SPLIT in train valid test; do
  python "${ROOT}/src/sp_dataset/foldseek_keys.py" \
    --lookup "${FSDB}.lookup" --ids "${ROOT}/manifests/sp_v3/${SPLIT}_ids.txt" \
    --output "${OUT}/${SPLIT}.keys"
  "${FOLDSEEK_BIN}" createsubdb "${OUT}/${SPLIT}.keys" "${FSDB}" "${OUT}/${SPLIT}"
done
for QUERY in valid test; do
  "${FOLDSEEK_BIN}" search "${OUT}/${QUERY}" "${OUT}/train" \
    "${OUT}/${QUERY}_train.res" "${OUT}/tmp_${QUERY}" \
    --alignment-type 2 -a 1 -e 1e-3 -c 0.50 --cov-mode 0 \
    --max-seqs 10 --threads "${THREADS}"
  "${FOLDSEEK_BIN}" convertalis "${OUT}/${QUERY}" "${OUT}/train" \
    "${OUT}/${QUERY}_train.res" "${OUT}/${QUERY}_train.tsv" \
    --format-output query,target,fident,alnlen,qcov,tcov,evalue,bits,qtmscore,ttmscore
done
"${FOLDSEEK_BIN}" search "${OUT}/valid" "${OUT}/test" \
  "${OUT}/valid_test.res" "${OUT}/tmp_valid_test" \
  --alignment-type 2 -a 1 -e 1e-3 -c 0.50 --cov-mode 0 \
  --max-seqs 10 --threads "${THREADS}"
"${FOLDSEEK_BIN}" convertalis "${OUT}/valid" "${OUT}/test" \
  "${OUT}/valid_test.res" "${OUT}/valid_test.tsv" \
  --format-output query,target,fident,alnlen,qcov,tcov,evalue,bits,qtmscore,ttmscore
\n