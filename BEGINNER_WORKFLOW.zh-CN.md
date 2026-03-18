# AI 写论文工作流入门

这份文档面向第一次接触 `latex-arxiv-SKILL` 的用户。目标不是解释每个脚本的全部细节，而是把这个项目是如何用 AI 从“一个题目”走到“可编译 PDF”的完整路径讲清楚。

如果只记一句话：

`paper-from-zero` 负责“找方向和定框架”，`arxiv-paper-writer` / `empirical-paper-writer` 负责“按合同写”，`results-backfill` 负责“把真实实验结果灌回论文”，`Claude/Gemini` 负责“协作增强”，最后再经过引用审计和 LaTeX 编译门禁。

## 1. 先理解这个项目在做什么

这个仓库不是“让 AI 一次性写完论文”的脚本集合，而是一套带门禁的工作流。

它的核心原则有 4 个：

1. 先做研究框架，再写正文。
2. 先有执行合同，再逐项推进。
3. 先验证证据，再写确定性结论。
4. 先编译和审计通过，再交付。

这和很多初学者直接让模型“写一篇论文”完全不同。这里更强调：

- 文献搜索是显式步骤。
- 创新点不是一句口号，而是要落到 `contribution-map.yaml` 和 `evidence-matrix.csv`。
- 写作不是自由发挥，而是按 `issues.csv` 一项一项完成。
- 实验结果不能编，必须来自真实 `paper/results/*.csv`。

## 2. 整体流程图

```text
研究题目
  -> paper-from-zero
  -> 产出 5 个交接件
     - brief/topic-brief.md
     - brief/contribution-map.yaml
     - brief/evidence-matrix.csv
     - plan/outline-contract.md
     - plan/router-decision.md
  -> 路由
     - review  -> arxiv-paper-writer
     - empirical -> empirical-paper-writer
  -> 用户审批计划
  -> 生成 issues CSV
  -> 按 issue 写作 / 设计 / 画图 / 校验
  -> 如果是实验论文：设计实验 -> 生成代码骨架 -> 用户在外部环境跑实验
  -> results-backfill 回填真实结果
  -> latex-rhythm-refiner 润色
  -> citation audit + issue validate + compile
  -> main.pdf
```

## 3. 第一步：从题目出发，而不是直接写正文

起点通常是一句话题目，比如：

```text
面向实时预报调度的来水预报模型参数滚动率定与“预报-调度-实施”闭环耦合方法研究
```

这时应该先用 `paper-from-zero`，而不是马上写 `main.tex`。

### `paper-from-zero` 在做什么

它负责完成写论文前最关键的 5 件事：

1. 把题目拆成关键词和检索方向。
2. 搜 10 到 20 篇关键文献，建立初始研究快照。
3. 明确主张是什么，创新点在哪里，哪些地方容易被审稿人质疑。
4. 把每个 claim 对应到需要什么证据。
5. 判断这篇文章应该走“综述路线”还是“实验路线”。

### 这个阶段的输出文件

- `brief/topic-brief.md`
  - 题目、关键词、问题边界、候选方向。
- `brief/contribution-map.yaml`
  - 主 claim、次级 claim、non-goals、风险点、潜在 reviewer objections。
- `brief/evidence-matrix.csv`
  - 每个 claim 需要文献证据、实验、图表还是方法描述。
- `plan/outline-contract.md`
  - 章节结构、写作范围、计划。
- `plan/router-decision.md`
  - 最终决定是 `review` 还是 `empirical`。

### 这一阶段为什么重要

很多论文不是死在“不会写”，而是死在“主张不清楚”。

如果在这个阶段没有把下面几个问题说清楚，后面会越写越乱：

- 你的论文到底想证明什么？
- 这个贡献是综述型还是实证型？
- 哪些结果必须靠实验，哪些只靠引用就能支撑？
- 哪些 claim 风险最大？

## 4. 第二步：确立创新点，不是喊口号

初学者最常见的问题是把“创新点”写成很泛的句子，比如“提出一种新框架”“提升了性能”“更鲁棒”。

在这个项目里，创新点要被压缩成两个结构化对象：

### `contribution-map.yaml`

它要求你回答：

- 主 claim 是什么？
- 次级 claim 是什么？
- 哪些东西不是你的贡献？
- 你最怕审稿人怎么攻击？

### `evidence-matrix.csv`

它要求你回答：

- 每个 claim 需要哪类证据？
- 这个证据来自文献、实验、图、表还是方法定义？
- 当前是 `planned`、`placeholder` 还是 `verified`？

这一步的本质是把“创新点”从自然语言，变成可验证的研究合同。

## 5. 第三步：决定走综述路线还是实验路线

这是整个仓库最关键的分叉点。

### 什么时候走 `arxiv-paper-writer`

适合：

- survey
- tutorial
- taxonomy
- benchmark synthesis
- 主要贡献来自“整理、比较、归纳已有工作”

### 什么时候走 `empirical-paper-writer`

适合：

- 新方法
- 新实验设置
- 新训练策略
- 需要 ablation、robustness、efficiency 支撑的主张

### 经验判断

如果你的标题主张里有“improves / outperforms / reduces / yields”等需要数字证明的词，通常就应该走 `empirical`。

## 6. 第四步：审批前只搭骨架，不写正文

这是本项目的硬规则。

在计划没过、`issues.csv` 没生成之前：

- 可以写章节标题。
- 可以写 bullet。
- 可以放 seed citations。
- 可以放图表占位。
- 不能往 `main.tex` 里写完整正文段落。

原因很简单：如果框架和 claim 还没稳定，过早写 prose 会导致大量返工。

这也是 `AGENTS.md` 里最重要的门禁之一。

## 7. 第五步：如果是实验论文，先做设计，再写全文

`empirical-paper-writer` 不会一上来就写结果章节。它会先把实验设计做成结构化文件。

### 这一阶段会产出 3 个核心 CSV

- `notes/design/baselines.csv`
  - 记录 direct competitors、foundational baselines、ablation anchors。
- `notes/design/method-components.csv`
  - 把方法拆成模块，标记哪些是 novel，哪些可以做 ablation。
- `notes/design/experiment-matrix.csv`
  - 定义主对比、ablation、robustness、efficiency。

### 为什么要这样设计

因为实验论文的质量，很大程度上取决于：

- baseline 是否选得合理
- ablation 是否真在打你的核心贡献
- robustness 是否对应真实风险
- efficiency 是否和主张有关

如果这些不先做成矩阵，后面的 Results 章节会非常散。

## 8. 第六步：生成 issues CSV，它是执行合同

`issues/<timestamp>-<slug>.csv` 是整个项目的“施工图”。

它把工作拆成：

- `R*`：Research
- `E*`：Experiment
- `W*`：Writing
- `V*`：Visual
- `RF*`：Refinement
- `Q*`：QA

每一行 issue 都有这些关键字段：

- `Section_Path`
- `Claim_ID`
- `Evidence_Type`
- `Experiment_ID`
- `Result_Status`
- `Acceptance`
- `Depends_On`
- `Status`

### 为什么它这么重要

因为这里不是“让 AI 自己发挥”，而是：

- 做完什么才算 DONE，要写在 `Acceptance`
- 依赖谁，要写在 `Depends_On`
- 有无真实结果，要写在 `Result_Status`

换句话说，`issues.csv` 让论文写作从“聊天”变成“项目管理”。

## 9. 第七步：进入逐 issue 写作循环

一旦 plan 批准且 issues CSV 生成，才进入真正写作。

循环是这样的：

1. 研究当前 issue 需要的精确信息。
2. 写这一节或这一块内容。
3. 检查引用是否真的支持当前句子。
4. 如果涉及实验结果，区分：
   - `planned`
   - `placeholder`
   - `verified`
5. 跑审计和编译。
6. 满足 acceptance 后再标记 DONE。

### 这里的关键思想

不是“写完整篇论文”，而是“完成当前 issue”。

这让长论文也能被稳定拆解。

## 10. 第八步：结构图可以先做，结果图必须等真实结果

在实验论文里，图分两类：

### 结构图

可以在真实实验出来前生成，比如：

- 方法 pipeline
- 模块结构图
- problem setup 图

它们通常来自：

- `method-components.csv`
- 方法章节公式
- 数据流设计

### 结果图

必须等真实结果出现后生成，比如：

- main comparison
- ablation summary
- robustness figure
- runtime tradeoff

如果没有真实数据，只能保留 placeholder，不能写成事实。

## 11. 第九步：实验代码和运行是分开的

`empirical-paper-writer` 可以帮你搭：

- `experiments/` 代码骨架
- `configs/default.yaml`
- `run_all.py`
- evaluation / metrics / model stub

但它不会在 AI 会话里替你跑长实验。

原因：

- 时间太长
- 环境不稳定
- 结果必须来自用户自己的运行环境

通常是用户在外部环境里运行：

```text
conda activate <env>
cd <project>/experiments
python run_all.py --config configs/default.yaml
```

跑完后，把真实结果放到 `paper/results/`。

### AI 设计的实验，数据是怎么得到的？

这是初学者最容易误解的地方。

`AI 设计实验` 不等于 `AI 生成数据`。这里至少有 3 层东西要分开看：

1. `实验设计`
   - 由 AI 和用户一起确定要比较什么、做哪些 ablation、看哪些指标、怎样组织实验矩阵。
   - 这些内容通常落在 `baselines.csv`、`method-components.csv`、`experiment-matrix.csv`。
2. `原始样本数据`
   - 来自真实公开数据集、用户自己的数据，或者被明确声明的仿真/合成数据。
   - 这部分不是 AI 凭空写出来的。
3. `实验结果数据`
   - 来自你真正运行 `experiments/` 代码后生成的 CSV / JSON。
   - 这部分才是后续 Results、表格、曲线和摘要里能引用的数字来源。

以这次的 `rt-inflow-forecast-closed-loop` 项目为例：

- 原始数据集在 `projects/rt-inflow-forecast-closed-loop/experiments/configs/default.yaml` 里配置。
- 默认使用的是 `ResOpsUS v2`，路径写在：
  - `projects/rt-inflow-forecast-closed-loop/experiments/configs/default.yaml`
  - `data.resopsus.time_series_all_dir`
  - `data.resopsus.reservoir_attributes_csv`
- 数据读取逻辑在 `projects/rt-inflow-forecast-closed-loop/experiments/data/resopsus.py`。
- 这里会真正去读 `ResOpsUS_<DAM_ID>.csv`，解析日期，过滤时间窗口，并检查 `storage`、`inflow`、`outflow` 这些列是否完整。

也就是说，这个项目里的数据流是：

```text
真实数据集 -> data loader -> 训练 / 评估代码 -> paper/results/*.csv|*.json -> results-backfill -> 正文 / 表 / 图
```

你可以把它理解成：

- AI 负责 `实验方案`
- 代码负责 `执行实验`
- 数据集负责 `提供样本`
- `paper/results/` 负责 `承接真实结果`
- `results-backfill` 负责 `把真实结果写回论文`

再强调一次：`results-backfill` 只能消费已经存在的真实结果文件，不能替你“脑补一个更好看的数字”。

如果你看到论文里有鲁棒性实验、延迟观测、缺测、扰动场景，也要区分两种情况：

- 如果它们来自真实数据集上的程序化变换，那本质上还是“基于真实数据生成的实验条件”。
- 如果它们来自纯仿真器，那就必须在论文里明确说清楚仿真来源、参数和假设。

所以，这套工作流里最重要的边界是：

```text
AI 可以设计实验、组织写作、分析结果；
AI 不能把没有跑出来的结果写成已经验证的事实。
```

## 12. 第十步：用 `results-backfill` 回填真实实验结果

这是很多人第一次看这个项目时最容易忽略的一步。

`results-backfill` 不是重复写论文，而是把“草稿中的占位结果”升级成“被真实 CSV 支撑的论文”。

### 它会做什么

1. 扫描 `paper/results/` 下的 CSV / JSON。
2. 对照 `experiment-matrix.csv` 识别每个结果文件属于哪类实验。
3. 把 `Result_Status` 从 `planned` / `placeholder` 更新成 `verified`。
4. 用真实数字填表、画图、写 Results narrative。
5. 把 `(hypothesis)` 变成带数字的 factual claim。
6. 回写摘要、结论和贡献列表。

### 这里最重要的规则

- 只能用真实结果文件里的数字。
- 不能把“看起来应该更好”写成“已经更好”。
- 结论必须是 bounded claim。

例如可以写：

```text
reduces mean CRPS by 16.3%
```

不能写：

```text
substantially improves forecasting quality
```

除非后面紧跟真实数值。

## 13. 第十一步：Claude 和 Gemini 怎么协作

这两个协作者不是“第二个作者”，而是两个偏向不同的 AI 合作者。

### Gemini 负责广度

适合：

- 扩文献池
- 找相邻方向
- 生成关键词簇
- 提供 3 到 5 个候选 framing

典型位置：

- `paper-from-zero` 的早期文献搜索阶段
- evidence-matrix coverage 不足时

### Claude 负责深度

适合：

- claim stress test
- evidence sufficiency audit
- reviewer objection 模拟
- 更像顶会/期刊的语言和图表审查

典型位置：

- `contribution-map.yaml` 初稿之后
- evidence matrix 初稿之后
- Results / Discussion / figure polish 阶段

### 协作前的正确顺序

先跑 `check-collaborators`，确认：

- Gemini CLI 可用
- Claude Code CLI 可用
- 已登录
- API 可达

否则你会把时间浪费在工具配置上，而不是论文本身。

## 14. 第十二步：最后的润色、QA 和编译

论文进入收尾阶段时，要做 3 类事情。

### 1. 文本润色

用 `latex-rhythm-refiner`：

- 调整句长和段落节奏
- 去掉填充词
- 保持所有 `\cite{}` 不动

### 2. 质量门禁

主要包括：

- `citation_policy.py`
  - BibTeX lint
  - audit-tex
  - 引用策略检查
- `validate_empirical_paper_issues.py`
  - issue 完整性
  - 依赖检查
  - 占位内容审计

### 3. 编译门禁

最终需要：

- `main.tex` 可编译
- `main.pdf` 生成成功
- warning 处于可接受范围

## 15. 这次项目是怎么走完这一套流程的

以仓库里的这个项目为例：

- `projects/rt-inflow-forecast-closed-loop/`

它大致经历了下面这些阶段：

1. 用 `paper-from-zero` 从题目出发，完成文献搜索、贡献图、证据矩阵、路由决策。
2. 路由到 `empirical-paper-writer`，生成 LaTeX 草稿、实验设计、issues CSV、实验代码骨架。
3. 在 `experiments/` 中补全并运行实验，生成 `paper/results/*.csv` 和配套 JSON。
4. 用 `results-backfill` 把真实结果回填到 `paper/main.tex`、结果表、结果图和摘要里。
5. 用 `collaborating-with-claude` 做深度审查，包括：
   - claim 压测
   - 结果叙事强化
   - 图表表达修正
6. 最后通过 citation audit、issues validate 和 compile gate，得到 `main.pdf`。

这也是本仓库最完整的一条“实证论文路线”样例。

## 16. 初学者最容易犯的 8 个错误

1. 一开始就让 AI 写完整正文，没有先做 contribution map。
2. 没有用户审批就往 `main.tex` 写大段 prose。
3. 没有 `issues.csv` 就开始推进，导致后面无法追踪状态。
4. 把 placeholder 结果写成 verified 结果。
5. 往 `ref.bib` 里加了没核验的引用。
6. baseline 选得太弱，导致主张看起来“赢了”，但没有说服力。
7. 实验跑完后不做 `results-backfill`，而是手动改正文，最后 issue 状态和 LaTeX 内容脱节。
8. 把 Claude/Gemini 当作事实来源，而不是协作者和候选建议提供者。

## 17. 推荐给新手的最小使用姿势

### 先从完整路线开始

```text
Use the paper-from-zero skill. My topic is: <你的研究题目>
```

### 如果已经确定是实验论文

```text
Use the empirical-paper-writer skill. The project is empirical. Build the plan, design artifacts, and issues contract first.
```

### 实验已经跑完，要回填

```text
Use the results-backfill skill. The draft exists and paper/results/ now contains verified experiment CSVs.
```

### 要请 Claude 做深度审查

```text
Use the collaborating-with-claude skill to stress-test the claims, check evidence sufficiency, and polish figures/results language.
```

## 18. FAQ：实验是谁来跑

### Q: 项目内部，实验是直接跑完吗？还是后续作者提供？

默认不是“AI 在写作流程里自动把实验全跑完”，而是：

- 项目内部会先生成可运行的 `experiments/` 工程、配置文件和运行入口。
- 真正的长实验通常由作者/用户后续在自己的本地环境里执行。
- 跑完后，真实结果会写入 `paper/results/`。
- `results-backfill` 再把这些真实结果回填到正文、图表、表格和摘要里。

所以更准确地说，这个仓库采用的是：

```text
AI 负责设计实验和搭建工程；
作者负责在真实环境里运行实验；
回填流程负责把真实结果写回论文。
```

这也是为什么文档里一直强调：

- `empirical-paper-writer` 负责“设计 + 草稿 + 代码骨架”
- `results-backfill` 负责“消费真实结果”
- 不能把没有跑出来的数字写成 `verified`

## 19. 你真正应该形成的心智模型

把这个项目想成一个“分阶段、可回溯、可审计”的 AI 论文工厂，而不是聊天机器人。

最重要的不是“模型一次写得多漂亮”，而是：

- 前期有研究框架
- 中期有执行合同
- 后期有真实证据
- 最终有审计和编译门禁

只要这 4 层在，论文就能稳定推进。
