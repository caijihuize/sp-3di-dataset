# Data card (SP v3 candidate)

## Source

AlphaFold DB Swiss-Prot PDB v6 archive (`swissprot_pdb_v6.tar`), retrieved from the EBI AlphaFold DB download endpoint. The source archive is 28,580,050,944 bytes with SHA-256 `30873553b5f9fb5499be24ade2ec7f0fdbae570dda15237c2dbe1096ecda1eee`.

## Intended use

Paired amino-acid and Foldseek 3Di model training, plus sequence-cluster-isolated inverse-folding evaluation using selected AlphaFold predicted structures.

## Exclusions and known limits

Filtering excludes records failing sequence/structure pairing, residue alphabet, length, unknown-AA, or pLDDT requirements. The benchmark structures are predictions rather than experimental native structures. The sequence split does not establish fold novelty. Checkpoint pretraining and previous fine-tuning exposure are outside this dataset-processing pipeline and need separate audits.

## Release counts

The build retained 503,440 of 550,122 paired AA/3Di records after filtering and excluded 46,682. The resulting splits contain 364,752 train, 1,000 validation, and 1,000 test records. Evaluation PDB export and sequence-to-structure sequence checks passed. The final sequence audit detected no alignments at or above 30% identity with at least 80% coverage of both sequences. Foldseek structural-neighbor results are reported separately and do not determine split membership.

## Rights and attribution

Repository code uses the license stated in `LICENSE`. Source data and third-party tools retain their own terms. Review the source provider's current terms before redistributing structures or derived data.
\n