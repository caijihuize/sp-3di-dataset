# SP 数据集处理项目

本项目从 AlphaFold DB Swiss-Prot PDB 归档构建氨基酸（AA）与 Foldseek 3Di 配对数据。SP v3 采用按序列聚类分组的 train/valid/test 划分，执行跨划分泄漏审计，并导出逆折叠评测结构。

## 当前状态

SP v3 候选版本已完成构建并通过发布验证。当前包含 train 364,752 条、valid 1,000 条、test 1,000 条。已导出 2,000 个评测 PDB，解析出的序列均与对应 AA 记录一致。最终 MMseqs2 审计在设定阈值（identity 30%、双侧 coverage 80%）下未发现跨划分命中。

Foldseek 结构邻居用于报告和复核，不作为硬性排除条件。划分 ID、PDB 和 AA–3Di 数据将与代码仓库分开发布；数据发布材料记录原始归档 SHA-256、软件版本和构建参数。

公开数据集：[Hugging Face Hub](https://huggingface.co/datasets/caijihuize/sp-3di-dataset)。Hub 仓库包含配对序列、划分 ID、版本元数据和评测结构；不包含 27 GB 原始归档及中间搜索数据库。

## 获取数据

### 内容与划分

| 划分 | 条数 | PDB 结构 | ID 清单 |
|---|---:|---:|---|
| `train` | 364,752 | 未提供 | `ids/train_ids.txt` |
| `validation` | 1,000 | 1,000 | `ids/valid_ids.txt` |
| `test` | 1,000 | 1,000 | `ids/test_ids.txt` |

每条 Parquet 记录包含 `id`（AlphaFold 模型 ID）、`sequence_3di`（Foldseek 3Di 序列）和 `sequence_aa`（氨基酸序列）。ID 清单顺序与对应 Parquet 行顺序一致。验证集在 Parquet 中称为 `validation`，在 ID 文件和构建清单中称为 `valid`。PDB 文件名与记录中的 `id` 一致。

### 使用 🤗 Datasets 加载配对序列

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

### 下载 PDB 或完整数据

如尚未安装 Hugging Face 命令行工具，可运行 `pip install -U huggingface_hub`；公开文件无需令牌即可下载。

只下载 test PDB 和对应 ID 清单：

```bash
hf download caijihuize/sp-3di-dataset \
  --repo-type dataset \
  --include "structures/test/*.pdb" "ids/test_ids.txt" \
  --local-dir ./sp3di-test
```

验证集 PDB 路径为 `structures/validation/*.pdb`。若需完整下载，去掉 `--include` 并指定本地目录；完整发布包约 580 MiB。下载到完整目录后，可运行 `sha256sum -c checksums/SHA256SUMS` 校验文件。

### 来源与限制

`provenance/` 包含源归档校验和、MMseqs2/Foldseek 版本与参数、划分统计、聚类成员、排除记录以及审计和验证摘要。最终序列审计在 identity 至少 30%、双侧 coverage 至少 80% 的条件下未检出跨划分命中。Foldseek 结构邻居仅作报告，未作为硬性划分过滤；这些检查不代表折叠级别的新颖性。PDB 是 AlphaFold 预测结构；当前没有提供训练集 PDB。复用结构时请保留 AlphaFold 数据来源署名；许可与引用信息见 [Hugging Face 数据卡](https://huggingface.co/datasets/caijihuize/sp-3di-dataset)。

## 数据与划分规则

- 数据来源：[AlphaFold DB Swiss-Prot PDB v6](https://ftp.ebi.ac.uk/pub/databases/alphafold/latest/swissprot_pdb_v6.tar)，大文件不提交 Git。
- 记录 AA、3Di、pLDDT、AlphaFold ID、片段/模型后缀和原始成员信息。
- 过滤：长度至少 16、平均 CA pLDDT 至少 70、未知 AA 不超过 20%、AA/3Di 等长且 3Di 字母合法。
- MMseqs2 聚类初始阈值为 30% identity、80% 双侧 coverage；版本、比对模式、灵敏度、最大命中数及其余参数均记录在构建清单中。
- 同一聚类、同 accession 的片段及完全相同 AA 序列不能跨划分。
- valid/test 各从不同合格组中选 1,000 个代表。当前逆折叠流程的评测长度限定为 30–510；同组未选成员排除并记录。
- 对最终评测集与训练集执行序列搜索，发现冲突后按固定规则修复并重跑。片段/结构域匹配另行报告。
- Foldseek 检查评测结构与训练结构的相似邻居，主版本将此作为报告，不作为硬排除规则。

MMseqs2 聚类本身不能保证不存在跨划分同源，因此最终序列搜索是必需的。结果应表述为“在公布的搜索协议下未检出超过阈值的匹配”。

## 目录

见英文 [README](README.md)。原始归档、数据库、中间文件和运行日志不纳入代码仓库。划分 ID 与统计、审计报告随数据版本单独发布。

## 初始复现步骤

```bash
mamba env create -f environment.yml
mamba activate sp-dataset
bash scripts/00_record_source.sh
FEATURE_JOB=$(sbatch --parsable scripts/submit_01_features.sh)
SPLIT_JOB=$(sbatch --parsable --dependency="afterok:${FEATURE_JOB}" scripts/submit_02_cluster_split.sh)
AUDIT_JOB=$(sbatch --parsable --dependency="afterok:${SPLIT_JOB}" scripts/submit_03_audits.sh)
REPAIR_JOB=$(sbatch --parsable --dependency="afterok:${AUDIT_JOB}" scripts/submit_04_repair_cycle.sh)
sbatch --dependency="afterok:${REPAIR_JOB}" scripts/submit_05_final_audit.sh
```

请从仓库根目录提交，以便 Slurm 将日志写入 `runs/`。最终审计会将训练集按每块 50,000 条分片搜索，发现冲突时修复并重跑；通过后重新导出 PDB 并生成结构相似性报告和验证报告。AlphaFold 结构为预测结构；pLDDT 表示局部置信度，不代表实验正确性。序列隔离也不等于新折叠隔离；预训练暴露需单独审计。

如果批处理节点默认 Python 未安装 `datasets`，请设置 `SP_PYTHON` 指向包含该依赖的 Python 解释器。
\n
