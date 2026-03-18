# rt-inflow-forecast-closed-loop

[English](README.md) | 简体中文

这是仓库中保留的“实证论文路线”示例，对应 `empirical-paper-writer` + `results-backfill` 工作流。

## 这个示例展示了什么

这个项目说明，这套工作流并不止停留在生成大纲：

- 题目被拆成了 claim、证据需求和论文计划
- 在 `paper/notes/design/` 和 `paper/issues/` 中建立了实验合同
- 识别并接入了公开数据集目标
- 实验结果被写入 `paper/results/`，然后再回填到论文正文
- 最终论文和结果图由这些保留下来的产物编译而成

## 这个项目保留了什么

- `paper/main.tex` 和 `paper/main.pdf`
- `paper/plan/` 和 `paper/issues/`
- `paper/results/*.csv` 和 `paper/results/*.json`
- `paper/figures/*.pdf`
- `experiments/` 下的可运行实验代码

## 数据说明

在开发阶段，工作流识别出 ResOpsUS v2 作为目标公开数据集，并在本地下载后用于保留下来的实验结果。为了让公开仓库保持轻量，原始数据目录已移除。

如果你要复现：

1. 下载 ResOpsUS v2。
2. 放到 `experiments/data/raw/ResOpsUS2/...`，或修改 `experiments/configs/default.yaml`。
3. 在 `experiments/` 下重新运行各实验套件。

## 建议阅读顺序

如果你想快速看懂这个示例，建议按这个顺序打开：

1. `paper/main.pdf`：最终论文产物
2. `paper/notes/design/experiment-matrix.csv`：实验合同
3. `paper/results/`：保留下来的已验证结果
4. `experiments/README.md`：数据和运行如何对应到结果
5. `experiments/configs/default.yaml`：数据路径和评估配置

## 为什么它适合作为 showcase

- 它展示了完整的实证路线：选题框架、设计工件、issues 合同、可运行实验、已验证结果文件和最终论文。
- 保留下来的 `paper/results/` 和 `paper/figures/` 都来自真实运行，不是占位内容。
