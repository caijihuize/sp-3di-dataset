# SP v3 methodology

This document freezes the intended method. The release manifest must contain the exact effective commands, software versions, source archive hash, and any deviations.

## Record identity and preprocessing

Preserve the complete normalized AlphaFold model ID, including fragment and model version. Never silently merge records solely because a parser shortened their identifiers. Pair AA and 3Di by normalized ID, enforce equal residue counts and alphabet checks, then apply length, unknown-residue, and mean CA pLDDT filters. Every record receives one inclusion/exclusion reason.

## Similarity groups

Initial proposal: MMseqs2 at 30% sequence identity and 80% coverage of both aligned sequences (`--cov-mode 0`, explicit identity calculation). Keep MMseqs2 clusters as indivisible split units. Merge groups for identical AA sequences and fragments of a shared UniProt accession. If an accession maps to multiple clusters, union them before splitting and report the resulting group-size distribution.

Representative clustering is an assignment procedure, not a guarantee that all members of different clusters are below the threshold. Therefore, search the final exported splits across their full members and repair any detected cross-split conflict before release. Exact parameters and sensitivity limits must be frozen and disclosed.

## Split design

Select 1,000 validation and 1,000 test groups, one representative per group, after the inverse-folding eligibility filter (30–510 residues). Choose representatives by descending mean pLDDT and then ascending stable ID. Use seed 42 and deterministic sorted candidate input. All other members of selected groups are excluded from train and recorded. Training otherwise retains eligible records, except exact-sequence duplicates may be reduced to one deterministic representative as explicitly recorded in the manifest.

If 2,000 eligible groups do not exist after checks, fail the release build with diagnostics; do not silently relax identity, coverage, or quality limits.

## Audits

Run all-member sequence searches for train–valid, train–test and valid–test. Handle any violating groups with a deterministic, documented repair and rerun until no reported violation remains. Separately inspect high-coverage local fragment/domain matches because bidirectional 80% coverage can miss a short sequence contained within a longer protein.

Run Foldseek searches from valid/test structures against all train structures, recording coverage, E-value, alignment score, and the exact TM-score normalization. The primary v3 split is sequence-cluster-isolated; structure similarity is a reported property. A structural split would be a separate frozen release protocol.

## Reproducibility and scope

Freeze archive SHA-256, tool versions, effective commands, seed, candidate ordering, split IDs, code revision, and output checksums. The AA/3Di training schema remains compatible with the existing consumer (`sequence_x=3Di`, `sequence_y=AA`). AlphaFold predictions and model-training exposure are limitations to state in any benchmark report.

\n