#!/usr/bin/env bash
# All-member cross-split sequence search. Review hits at the configured identity
# and coverage thresholds before any split manifest is considered releasable.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MMSEQS_BIN="${MMSEQS_BIN:-mmseqs}"
THREADS="${SLURM_CPUS_PER_TASK:-${THREADS:-32}}"
IN="${ROOT}/data/processed/sp_v3"
OUT="${AUDIT_DIR:-${ROOT}/data/interim}/sequence"
mkdir -p "${OUT}"
CHUNKS="${OUT}/target_chunks"
python "${ROOT}/src/sp_dataset/split_fasta.py" --input "${IN}/train.fasta" \
  --out-dir "${CHUNKS}" --records-per-shard 50000
for QUERY in valid test; do
  "${MMSEQS_BIN}" createdb "${IN}/${QUERY}.fasta" "${OUT}/${QUERY}.db"
  : > "${OUT}/${QUERY}_train.tsv"
  SHARD=0
  for TARGET_FASTA in "${CHUNKS}"/target_*.fasta; do
    TARGET_DB="${OUT}/${QUERY}_target_${SHARD}.db"
    RESULT_DB="${OUT}/${QUERY}_target_${SHARD}.res"
    "${MMSEQS_BIN}" createdb "${TARGET_FASTA}" "${TARGET_DB}"
    "${MMSEQS_BIN}" search "${OUT}/${QUERY}.db" "${TARGET_DB}" \
      "${RESULT_DB}" "${OUT}/tmp_${QUERY}_${SHARD}" \
      --min-seq-id 0.30 -c 0.80 --cov-mode 0 --alignment-mode 3 \
      -s 7.5 --max-seqs 100000 --threads "${THREADS}"
    "${MMSEQS_BIN}" convertalis "${OUT}/${QUERY}.db" "${TARGET_DB}" \
      "${RESULT_DB}" "${OUT}/${QUERY}_target_${SHARD}.tsv" \
      --format-output query,target,fident,alnlen,qcov,tcov,evalue,bits
    cat "${OUT}/${QUERY}_target_${SHARD}.tsv" >> "${OUT}/${QUERY}_train.tsv"
    SHARD=$((SHARD + 1))
  done
done
"${MMSEQS_BIN}" createdb "${IN}/valid.fasta" "${OUT}/valid_audit.db"
"${MMSEQS_BIN}" createdb "${IN}/test.fasta" "${OUT}/test_audit.db"
"${MMSEQS_BIN}" search "${OUT}/valid_audit.db" "${OUT}/test_audit.db" \
  "${OUT}/valid_test.res" "${OUT}/tmp_valid_test" \
  --min-seq-id 0.30 -c 0.80 --cov-mode 0 --alignment-mode 3 \
  -s 7.5 --max-seqs 500000 --threads "${THREADS}"
"${MMSEQS_BIN}" convertalis "${OUT}/valid_audit.db" "${OUT}/test_audit.db" \
  "${OUT}/valid_test.res" "${OUT}/valid_test.tsv" \
  --format-output query,target,fident,alnlen,qcov,tcov,evalue,bits
echo "Review TSVs in ${OUT}; any threshold hit requires split repair and a complete rerun."
\n