# evolve_lab — 自我进化策略对比实验

一个小型可运行实验框架，用**真实代码执行验证**对比 5 种自我进化策略在 8 个代码生成任务上的表现。

## 快速开始

```bash
# 1. 先验证任务套件（正确解必须通过、buggy 变体必须失败、签名必须唯一）
python experiments/scripts/verify_tasks.py

# 2. Mock 后端跑对比实验（离线，确定性，可复现）
python experiments/run_experiment.py --seeds 1,2,3

# 3. 真实后端（任何 OpenAI 兼容端点）
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.deepseek.com/v1   # 可选
python experiments/run_experiment.py --backend openai --model deepseek-chat --seeds 1
```

## 对比的 5 种策略

| 策略 | 外部反馈 | 反思记忆 | 跨任务洞察 | 采样 |
|------|----------|----------|------------|------|
| `direct` | ✗ | ✗ | ✗ | 1 |
| `best_of_n` | ✓（仅用于选择）| ✗ | ✗ | 5 |
| `self_refine` | ✗（内部自省）| 轮内 | ✗ | 1 |
| `reflexion` | ✓（测试输出）| ✓ | ✗ | 1 |
| `reflexion_insights` | ✓ | ✓ | ✓（ExpeL 风格）| 1 |

## 设计要点

### 真实验证，不做模拟
每个候选解法都在**独立 Python 子进程**中运行真实单元测试（20s 超时）。
反思所依据的失败信息来自真实执行的输出，不是编造的。

### 任务套件（8 任务 / 19 个典型失败变体）
每个任务包含：自然语言描述、参考正确解、2-3 个"典型错误"变体
（每个变体有独特的失败签名）、真实 unittest 测试。

签名契约由 `scripts/verify_tasks.py` 机器验证：
- 正确解必须通过全部测试
- buggy 变体必须失败
- 每个变体的签名必须出现在它自己的失败输出中
- 签名不得出现在正确解或其它变体的输出中（唯一性）

### MockBackend 说明（重要）
本机无 API key 时使用 mock 后端。它的行为模型：
- 新尝试按 `task.base_p`（0.30-0.45）概率生成正确解，否则从该任务的
  典型错误变体中抽样
- 反思文本提到过的失败模式会被后续生成规避（模拟 Reflexion 记忆）
- 每条跨任务洞察使 base_p +0.05（模拟 ExpeL 迁移）
- 自省（无外部信号）每轮以 `--critique-accuracy`（默认 0.5）概率发现当前 bug
- 完全确定性：RNG 由 `(seed, task, attempt, ...)` 的 SHA256 派生，同种子重跑结果一致

**它验证什么**：框架机制、策略差异的方向与量级、指标设计是否有效。
**它不验证什么**：真实 LLM 的行为。换 `--backend openai` 即接真实模型。

### 指标
- `success` — 预算内最终通过的任务比例
- `first-try` — 首次生成即通过的比例（直觉能力）
- `attempts` — 成功任务的平均尝试次数（迭代效率）
- `calls` — LLM 调用总数（成本代理）
- `1st-half` / `2nd-half` — 前后半段任务的首次成功率（洞察迁移曲线）

## 文件结构

```
experiments/
├── run_experiment.py         — CLI 入口
├── evolve_lab/
│   ├── tasks.py              — 任务套件
│   ├── backends.py           — MockBackend + OpenAIBackend
│   ├── strategies.py         — 5 种策略
│   ├── sandbox.py            — 真实子进程执行验证
│   └── runner.py             — 编排 + 指标聚合
├── scripts/verify_tasks.py   — 任务套件契约验证器
└── results/                  — JSON 报告（含每次运行的全部明细）
```

## 局限与注意

- 任务规模小（8 个函数级任务），结论是机制性的，不是能力定论
- Mock 的参数（base_p / critique_accuracy）会显著影响数值；敏感度分析见
  `results/sens-*.txt`（0.2 / 0.35 / 0.5 三档自省准确率）
- 真实后端运行会产生任意代码并在本机执行——仅在你信任的模型输出上使用；
  生产环境应加真正的沙箱（容器/权限隔离）
- 真实后端下 `reflect()` 的反馈包含测试输出，可能泄露测试内容；
  这正是"外部反馈"的定义，但与封闭评测的纪律不同，勿混淆
