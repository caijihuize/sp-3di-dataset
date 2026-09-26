# SP Dataset Processing

Reproducible processing of the AlphaFold Database Swiss-Prot PDB archive into paired amino-acid (AA) and Foldseek 3Di sequences. Version 3 is designed around sequence-cluster-aware train/validation/test splits, explicit leakage audits, and inverse-folding evaluation structures.

中文说明见 [README.zh-CN.md](README.zh-CN.md)。

## Status

The SP v3 candidate build has completed and passed release validation. It contains 364,752 training records, 1,000 validation records, and 1,000 test records. All 2,000 evaluation PDBs were exported, and their parsed amino-acid sequences match the AA records. The final MMseqs2 audit found no cross-split alignments meeting the configured thresholds (30% identity and 80% coverage of both sequences).

Foldseek structural neighbors are reported for review; they are not used as a hard exclusion. The split ID lists and PDB/AA–3Di data are distributed separately from this code repository. The source archive SHA-256, software versions, and build parameters are recorded in the build metadata for the data release.

The public dataset release is hosted on the [Hugging Face Hub](https://huggingface.co/datasets/caijihuize/sp-3di-dataset). The Hub repository contains the paired sequences, split IDs, release metadata, and evaluation structures. The 27 GB source archive and intermediate search databases are not mirrored there.

## Get the dataset

### Contents

| Split | Records | PDB structures | ID list |
|---|---:|---:|---|
| `train` | 364,752 | Not included | `ids/train_ids.txt` |
| `validation` | 1,000 | 1,000 | `ids/valid_ids.txt` |
| `test` | 1,000 | 1,000 | `ids/test_ids.txt` |

Each Parquet row has three columns: `id` (AlphaFold model ID), `sequence_3di` (Foldseek 3Di), and `sequence_aa` (amino-acid sequence). ID files follow the same row order as the corresponding Parquet split. Validation is called `validation` in Parquet filenames and `valid` in the ID filename and build manifests. PDB filenames match the row `id`.

### Load sequence pairs with 🤗 Datasets

```bash
pip install datasets
```

```python
from datasets import load_dataset

base = "hf://datasets/caijihuize/sp-3di-dataset/data/"
dataset = load_dataset("parquet", data_files={
    "train": base + "train-00000-of-00001.parquet",
    "validation": base + "validation-00000-of-00001.parquet",
    "test": base + "test-00000-of-00001.parquet",
})
example = dataset["test"][0]
print(example["id"], example["sequence_3di"], example["sequence_aa"])
```

### Download PDB structures or all release files

Install and authenticate the Hugging Face CLI if needed (`pip install -U huggingface_hub`, then `hf auth login`). Public files can also be downloaded without a token.

Download only the test PDBs and their ID list:

```bash
hf download caijihuize/sp-3di-dataset \
  --repo-type dataset \
  --include "structures/test/*.pdb" "ids/test_ids.txt" \
  --local-dir ./sp3di-test
```

Use `structures/validation/*.pdb` for validation structures. To download the complete release, omit `--include` and select a local directory; the full release is about 580 MiB. Verify downloaded files from that directory with `sha256sum -c checksums/SHA256SUMS`.

### Provenance and limitations

`provenance/` contains the source checksum, MMseqs2/Foldseek versions and parameters, split counts, cluster membership, exclusions, and audit/validation summaries. The final sequence audit detected no alignments at or above 30% identity with at least 80% coverage of both sequences. Foldseek structural neighbors are reported but are not a hard split filter. These checks do not establish fold novelty. The PDBs are AlphaFold predictions; no training-split PDB files are included.

The AlphaFold source data are distributed under CC BY 4.0; retain source attribution when reusing the structures. See the [dataset card](https://huggingface.co/datasets/caijihuize/sp-3di-dataset) for citations and release details.

## Data source

Source: [AlphaFold DB Swiss-Prot PDB v6 archive](https://ftp.ebi.ac.uk/pub/databases/alphafold/latest/swissprot_pdb_v6.tar). The archive is intentionally excluded from Git. Place it at `data/raw/swissprot_pdb_v6.tar`; record and verify its SHA-256 with `scripts/00_record_source.sh`.

## v3 protocol

- Parse records by stable AlphaFold identifier; retain accession, fragment/model suffix, source member and chain metadata.
- Require AA/3Di equal lengths; minimum sequence length 16; mean CA pLDDT at least 70; no more than 20% unknown AA; valid 3Di alphabet.
- Cluster amino-acid sequences with MMseqs2 at 30% identity and 80% bidirectional coverage. Freeze alignment mode, sensitivity, max hits, clustering mode and binary version with the run manifest.
- Keep each final group within one split. Force fragments from the same accession and exact-AA duplicates into the same group.
- Select 1,000 validation and 1,000 test representatives from distinct eligible groups. Evaluation structures are restricted to lengths 30–510 for the current inverse-folding workflow. Non-selected members of held-out groups are excluded and listed.
- Search every final held-out split against training sequences, repair detected conflicts deterministically, and rerun the audit. Report partial/domain matches separately.
- Use Foldseek to report structural neighbors of evaluation structures against training structures. Structural similarity is reported as an audit and is not a hard exclusion in the primary v3 protocol.
- Publish split ID manifests, group mapping, exclusion reasons, row-to-ID mapping, parameter/tool manifest, audit summaries and data-card statistics with the dataset release.

MMseqs2 clustering does not alone prove the absence of cross-split homologs, so the final search audit is mandatory. Results should be described as “no violations detected under the published search protocol.”

## Repository layout

```text
configs/       versioned processing parameters
src/           parsing, provenance, filtering, clustering and audit code
scripts/       reproducible command-line entry points and Slurm submission
data/raw/      source archive (excluded from Git)
data/interim/  Foldseek database, FASTA and temporary results (excluded)
data/processed/ final datasets and evaluation PDBs (excluded)
manifests/     generated split IDs and machine-readable provenance (released with the dataset)
reports/       generated statistics and audit summaries (released with the dataset)
runs/          local Slurm logs (excluded)
docs/          method, reproduction guide and data card
```

## Reproduction

```bash
mamba env create -f environment.yml
mamba activate sp-dataset
bash scripts/00_record_source.sh
FEATURE_JOB=$(sbatch --parsable scripts/submit_01_features.sh)
SPLIT_JOB=$(sbatch --parsable --dependency="afterok:${FEATURE_JOB}" scripts/submit_02_cluster_split.sh)
AUDIT_JOB=$(sbatch --parsable --dependency="afterok:${SPLIT_JOB}" scripts/submit_03_audits.sh)
REPAIR_JOB=$(sbatch --parsable --dependency="afterok:${AUDIT_JOB}" scripts/submit_04_repair_cycle.sh)
FINAL_JOB=$(sbatch --parsable --dependency="afterok:${REPAIR_JOB}" scripts/submit_05_final_audit.sh)
sbatch --dependency="afterok:${FINAL_JOB}" scripts/submit_06_structure_report.sh
```

All commands are submitted from the repository root so Slurm logs land under `runs/`. The sequence audit searches training targets in 50,000-record shards to avoid per-query result-list caps. Repair detected conflicts and rerun the audit until it reports no threshold hits; the final audit script automates this loop, exports PDBs, and runs structural searches. The final structure-report job writes summary and validation reports. Do not use v3 evaluation IDs for model selection after evaluation.

On the current cluster, set `SP_PYTHON` to the Python interpreter in an environment with the `datasets` package if it is not on the batch job's default `PATH`.

## Limitations

The source structures are AlphaFold predictions, not experimentally determined structures. pLDDT is a local model-confidence measure and does not certify biological correctness. Sequence isolation does not guarantee structural-fold novelty, and pretrained-model exposure requires a separate checkpoint audit.

## License and citation

The MIT license in this repository applies to original code and documentation. It does not relicense AlphaFold DB data or third-party software. See `CITATION.cff` and the data-source citation in `docs/data_card.md` before redistribution.
\n
