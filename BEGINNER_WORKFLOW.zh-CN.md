# AI 写论文工作流入门

这份文档面向第一次接触 `latex-paper-skills` 的用户。目标不是解释每个脚本的全部细节，而是让你快速理解：这套仓库如何把“一个题目”推进到“可编译 PDF”。

如果只记一句话：

`paper-from-zero` 负责“找方向和定框架”，`arxiv-paper-writer` / `empirical-paper-writer` 负责“按合同写”，`results-backfill` 负责“把真实实验结果灌回论文”，`Claude/Gemini` 负责“协作增强”，最后再经过引用审计和 LaTeX 编译门禁。

## 1. 先理解这个项目在做什么

这个仓库不是“让 AI 一次性写完论文”的脚本集合，而是一套带门禁的工作流。

它强调 4 个原则：

1. 先做研究框架，再写正文。
2. 先有执行合同，再逐项推进。
3. 先验证证据，再写确定性结论。
4. 先通过审计和编译，再交付。

你可以把它理解成：AI 不是自由发挥写手，而是按阶段推进的论文项目助手。

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

起点通常是一句话题目（你可以指定AI写），比如：

```text
面向实时预报调度的来水预报模型参数滚动率定与“预报-调度-实施”闭环耦合方法研究
```

这时应该先用 `paper-from-zero`，而不是马上写 `main.tex`。

这个阶段的任务只有 5 件：

1. 把题目拆成关键词和检索方向。
2. 找 10 到 20 篇关键文献，形成研究快照。
3. 明确主张、风险点和潜在质疑。
4. 给每个 claim 配证据。
5. 判断走综述路线还是实验路线。

这个阶段会留下 5 份关键交接件：

- `brief/topic-brief.md`
- `brief/contribution-map.yaml`
- `brief/evidence-matrix.csv`
- `plan/outline-contract.md`
- `plan/router-decision.md`

如果这里没做扎实，后面通常会出现“主张不清”“证据不够”“写着写着改方向”的问题。

## 4. 第二步：把创新点写成结构，不要写成口号

在这套 workflow 里，创新点不是一句“提出新框架”“性能更强”，而是两个结构化对象：

### `contribution-map.yaml`

用来回答：

- 主 claim 是什么？
- 次级 claim 是什么？
- 哪些内容不是你的贡献？
- 审稿人最可能攻击哪里？

### `evidence-matrix.csv`

用来回答：

- 每个 claim 需要哪类证据？
- 证据来自文献、实验、图表还是方法定义？
- 当前状态是 `planned`、`placeholder` 还是 `verified`？

这一步的目标，是把“想法”压缩成“可核验的研究合同”。

## 5. 第三步：决定走综述路线还是实验路线

这是整个仓库最关键的分叉点。

### 什么时候走 `arxiv-paper-writer`

适合：

- survey
- tutorial
- taxonomy
- benchmark synthesis
- 主要贡献来自整理、比较、归纳已有工作

### 什么时候走 `empirical-paper-writer`

适合：

- 新方法
- 新实验设置
- 新训练策略
- 需要 ablation、robustness、efficiency 支撑的主张

经验上，如果标题里有 “improves / outperforms / reduces / yields” 这类必须靠数字证明的词，通常就该走 `empirical`。

## 6. 第四步：审批前只搭骨架，不写正文

这是本项目的硬规则。

在计划没过、`issues.csv` 没生成之前：

- 可以写章节标题
- 可以写 bullet
- 可以放 seed citations
- 可以放图表占位
- 不能往 `main.tex` 里写完整正文段落

原因很简单：框架和 claim 还没稳定时，过早写 prose 只会导致返工。

## 7. 第五步：如果是实验论文，先做设计，再写全文

`empirical-paper-writer` 不会先写 Results，而是先产出设计文件。

最关键的是 3 个 CSV：

- `notes/design/baselines.csv`
- `notes/design/method-components.csv`
- `notes/design/experiment-matrix.csv`

它们分别回答：

- 你和谁比
- 你的方法能拆成哪些模块
- 要做哪些主实验、消融、鲁棒性和效率测试

先把这些设计清楚，Results 章节才不会散。

## 8. 第六步：生成 issues CSV，它是执行合同

`issues/<timestamp>-<slug>.csv` 是整个项目的施工图。

它把工作拆成 `R* / E* / W* / V* / RF* / Q*` 等不同类型的 issue，并记录：

- `Acceptance`
- `Depends_On`
- `Result_Status`
- `Status`

它的作用不是“列任务”，而是把论文写作从聊天变成可追踪的项目执行。

## 9. 第七步：进入逐 issue 写作循环

一旦 plan 批准且 issues CSV 生成，才进入真正写作。

每一轮只做 6 件事：

1. 研究当前 issue 需要的精确信息。
2. 写这一块内容。
3. 检查引用是否真的支持当前句子。
4. 如果涉及实验结果，区分 `planned / placeholder / verified`。
5. 跑审计和编译。
6. 满足 acceptance 后再标记 DONE。

核心思想只有一句话：不是“写完整篇论文”，而是“完成当前 issue”。

## 10. 第八步：结构图可以先做，结果图必须等真实结果

实验论文里的图分两类：

### 结构图

可以在实验前生成，例如：

- 方法 pipeline
- 模块结构图
- problem setup 图

### 结果图

必须等真实结果出现后生成，例如：

- main comparison
- ablation summary
- robustness figure
- runtime tradeoff

没有真实数据时，只能保留 placeholder，不能把图写成事实。

## 11. 第九步：实验代码和运行是分开的

`empirical-paper-writer` 可以帮你搭：

- `experiments/` 代码骨架
- `configs/default.yaml`
- `run_all.py`
- evaluation / metrics / model stub

但它不会在 AI 会话里替你跑长实验。真正的实验通常由作者在自己的环境（或者云服务器）里执行，跑完后把真实结果放进 `paper/results/`。

最重要的边界是：

```text
AI 可以设计实验、组织写作、分析结果；
AI 不能把没有跑出来的结果写成已经验证的事实。
```

## 12. 第十步：用 `results-backfill` 回填真实实验结果

`results-backfill` 的作用不是重复写论文，而是把草稿中的占位结果升级成被真实 CSV / JSON 支撑的内容。

它通常会做 6 件事：

1. 扫描 `paper/results/` 下的结果文件。
2. 对照 `experiment-matrix.csv` 识别结果类型。
3. 把 `Result_Status` 更新成 `verified`。
4. 用真实数字填表和画图。
5. 把假设性表述改成带数字的 factual claim。
6. 回写摘要、结论和贡献列表。

这里最重要的规则是：只能用真实结果文件里的数字。

## 13. 第十一步：Claude 和 Gemini 怎么协作

这两个协作者不是“第二个作者”，而是两个偏向不同的 AI 合作者。

### Gemini 负责广度

适合：

- 扩文献池
- 找相邻方向
- 生成关键词簇
- 提供候选 framing

### Claude 负责深度

适合：

- claim stress test
- evidence sufficiency audit
- reviewer objection 模拟
- Results / Discussion / figure polish

开始协作前，先跑 `check-collaborators`，避免把时间花在 CLI 配置问题上。

## 14. 第十二步：最后的润色、QA 和编译

收尾阶段主要做 3 类事：

### 1. 文本润色

用 `latex-rhythm-refiner` 调整句长和段落节奏，同时保持所有 `\cite{}` 不动。

### 2. 质量门禁

重点包括：

- `citation_policy.py`
- `validate_empirical_paper_issues.py`

### 3. 编译门禁

最终至少要满足：

- `main.tex` 可编译
- `main.pdf` 成功生成
- warning 在可接受范围内

## 15. 这次项目是怎么走完这一套流程的

仓库里的 `projects/rt-inflow-forecast-closed-loop/` 就是一条完整的实证路线样例：

1. `paper-from-zero` 做选题、贡献图、证据矩阵和路由。
2. `empirical-paper-writer` 生成草稿、实验设计、issues 和代码骨架。
3. 作者在 `experiments/` 中补全并运行实验，生成真实结果文件。
4. `results-backfill` 把真实结果写回正文、表格、图和摘要。
5. 最后通过 citation audit、issues validate 和 compile gate，得到 `main.pdf`。

## 16. 推荐给新手的最小使用姿势

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

## 17. FAQ：实验是谁来跑

默认不是 AI 在写作流程里把实验全跑完，而是分工明确：

- AI 负责设计实验和搭建工程
- 作者负责在真实环境里运行实验
- `results-backfill` 负责把真实结果写回论文

所以 `empirical-paper-writer` 负责的是“设计 + 草稿 + 代码骨架”，不是“代替作者生成实验事实”。

## 19. 你真正应该形成的心智模型

把这个项目想成一个“分阶段、可回溯、可审计”的 AI 论文工厂，而不是聊天机器人。

最重要的不是“模型一次写得多漂亮”，而是：

- 前期有研究框架
- 中期有执行合同
- 后期有真实证据
- 最终有审计和编译门禁

只要这 4 层在，论文就能稳定推进。
