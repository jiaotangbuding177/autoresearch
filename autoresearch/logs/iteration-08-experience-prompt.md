# 迭代 8: Experience Replay 与自动 Prompt 优化

## 8.1 Experience Replay（经验回放）

### 核心概念
借鉴强化学习中的 Experience Replay：将历史执行轨迹存储起来，在新任务中查询和复用。

### 在 LLM Agent 中的应用

#### 机制
```
任务执行 → 成功/失败 → 存储轨迹（prompt + actions + outcome）
    ↓
新任务 → 查询相似历史轨迹 → 参考成功轨迹 / 避免失败轨迹
```

#### 关键组件
1. **轨迹存储** — 记录完整的执行过程
2. **相似度检索** — 找到与当前任务最相似的历史案例
3. **经验应用** — 将历史经验融入当前决策

#### 代表方法

##### ExpeL (Experience Learning)
- 从成功和失败中提取经验规则
- 将规则存储为自然语言
- 新任务时检索相关规则作为 Few-shot 示例

##### LATS (Language Agent Tree Search)
- 构建搜索树记录探索过程
- 使用蒙特卡洛树搜索（MCTS）策略
- 回溯并复用成功路径

##### Voyager (Minecraft Agent)
- 成功的技能代码存储到技能库
- 新任务时组合已有技能
- 持续积累可复用的行为原语

### 与 Reflexion 的对比

| 维度 | Reflexion | Experience Replay |
|------|-----------|-------------------|
| **存储内容** | 失败原因分析 | 完整执行轨迹 |
| **检索方式** | 简单追加到上下文 | 相似度匹配 |
| **应用方式** | 参考避免错误 | 直接复用成功策略 |
| **粒度** | 高层反思 | 具体行动序列 |
| **适用场景** | 需要理解"为什么失败" | 需要知道"怎么做" |

---

## 8.2 自动 Prompt 优化

### 核心问题
如何自动找到最优的 Prompt，而非依赖人工设计？

### 方法分类

#### 1. 基于搜索的方法

##### 遗传算法优化
```
种群 = [Prompt_1, Prompt_2, ..., Prompt_N]
while not converged:
    评估每个 Prompt 的任务成功率
    选择 Top-K
    交叉 + 变异生成新一代
```

##### 梯度启发式优化
- 虽然 LLM 没有梯度，但可以模拟
- 分析失败案例，提取改进方向
- 生成新 Prompt 变体

#### 2. 基于 LLM 的优化

##### OPRO (Optimization by Prompting)
```
历史 = [(Prompt_1, Score_1), (Prompt_2, Score_2), ...]

生成新 Prompt:
  "以下是历史 Prompt 和得分: {历史}
   请生成一个更好的 Prompt"
```

##### Automatic Prompt Engineer (APE)
- 生成大量 Prompt 候选
- 评估并筛选
- 迭代优化

#### 3. 基于反馈的优化

##### DSPy 框架
- 声明式定义 Prompt 模板
- 自动优化参数（Few-shot 示例、指令措辞）
- 支持多种优化器（BootstrapFewShot、MIPRO 等）

##### PromptSource
- Prompt 模板库
- 支持自动搜索最优模板

### 自动 Prompt 优化的挑战

1. **评估成本** — 每个 Prompt 变体需要在多个任务上评估
2. **过拟合风险** — 可能过拟合到验证集
3. **可解释性** — 自动生成的 Prompt 可能难以理解
4. **多目标平衡** — 成功率、成本、延迟的权衡

---

## 8.3 经验复用 vs Prompt 优化：对比

| 维度 | Experience Replay | Prompt Optimization |
|------|-------------------|----------------------|
| **优化对象** | 执行轨迹库 | Prompt 文本 |
| **学习方式** | 案例检索 | 参数调优 |
| **适应速度** | 即时（检索即用） | 需要迭代 |
| **泛化能力** | 依赖相似度 | 依赖 Prompt 设计 |
| **存储成本** | 高（完整轨迹） | 低（单个 Prompt） |
| **适用场景** | 任务有规律可循 | Prompt 敏感度高 |

---

## 8.4 组合策略

### 最佳实践
1. **初期** — 使用 Experience Replay 快速积累案例
2. **中期** — 从经验中提取规律，优化 Prompt
3. **长期** — 建立经验库 + 优化 Prompt 的双循环

### 实际案例

#### SWE-Agent
- 经验回放：存储成功的代码修复轨迹
- Prompt 优化：迭代改进工具调用 Prompt

#### OpenHands
- 多 Agent 协作产生丰富经验
- 自动提取最佳实践到 Prompt

---

## 核心启示

1. **经验是宝贵的** — Agent 的执行历史包含大量可学习信息
2. **检索是关键** — 如何高效找到相关经验是核心挑战
3. **Prompt 不是万能的** — 有些能力需要通过经验积累而非 Prompt 教会
4. **组合优于单一** — Experience Replay + Prompt Optimization 互补

---
**迭代状态**: 完成
