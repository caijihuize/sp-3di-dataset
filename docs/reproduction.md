# Reproduction guide

1. Obtain the source archive and place it at `data/raw/swissprot_pdb_v6.tar`.
2. Run `scripts/00_record_source.sh` and retain the generated archive checksum.
3. Create the pinned software environment and record `mmseqs version`, `foldseek version`, Python and package versions.
4. Run AA/3Di feature extraction and pLDDT extraction from the exact source archive.
5. Apply configured filters and write all retained and excluded IDs with reasons.
6. Run MMseqs2 clustering; freeze its effective command and outputs.
7. Merge same-accession fragments and exact sequence groups, assign split groups deterministically, export candidate splits.
8. Run all-member cross-split sequence audits and deterministic repairs; rerun until the protocol reports no violations.
9. Run Foldseek structural-neighbor audits, export assessment structures, and write the final manifest and checksums.
10. Run `scripts/submit_06_structure_report.sh` after the final audit to generate normalized Foldseek reports and validate the exported release.
11. Compare the resulting ID manifests to the manifests distributed with the matching dataset release for exact reproduction.

Large inputs, Foldseek/MMseqs databases, intermediate search results, and full HF/PDB outputs are excluded from Git. Download endpoints and checksums belong in the release manifest.
\n