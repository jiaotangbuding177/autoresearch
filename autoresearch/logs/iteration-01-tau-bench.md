# 迭代 1: τ-bench 深度调研

## 基本信息
- **论文**: τ^τ-bench: An Environment for End-To-End, Realistic Agent Construction
- **arXiv ID**: 2609.04611
- **提交日期**: 2026年9月3日
- **作者**: Quan Shi, Keshav Dhandhania, Karthik Narasimhan, Victor Barres (Sierra × Princeton)
- **仓库**: https://github.com/sierra-research/tau-bench

## 核心创新
τ^τ-bench 将 **Agent 构建本身** 作为评测任务，而非评测 Agent 的表现。这是一个根本性的范式转变：从"Agent 能不能完成任务"到"Agent 能不能交付一个完整的 Agent 系统"。

## 任务设计
开发者 Agent 接收：
- 真实业务记录（business records）
- 客户需求文档（client requirements）
- 生产环境 API（production API）
- 继承的代码库（inherited codebase）
- 服务成本预算限制（serving-cost limits）

**目标**：交付一个完整的客服 Agent 系统。

## 评测方法
- 构建的 Agent 被部署到与模拟用户的测试对话中
- 跨 4 个领域的 53 个任务
- 专家编写的参考方案作为性能上限

## 关键结果
| 配置 | 通过率 |
|------|--------|
| Claude Opus 5 + Claude Code（最强配置）| **23.9%** |
| 专家参考方案 | **82.2%** |
| 差距 | 58.3 个百分点 |

## "会写代码" vs "能交付系统" 的鸿沟

论文揭示了与人类开发者相似的系统性失败模式：

1. **表面查询代替深度理解** — "issue shallow queries in place of deep comprehension"
   - Agent 倾向于写快速能跑的代码，而非深入理解业务逻辑

2. **缺乏客户沟通** — "communicate little with the client"
   - 不会主动确认需求、不会迭代设计方案

3. **架构实验不足** — "experiment too little with agent architecture and serving spend"
   - 交付第一个能运行的设计就停止，不探索更优方案

4. **成本意识缺失** — 不考虑服务成本预算限制

## 评测设计亮点

### 1. 长周期任务（Long Horizon）
不是单轮问答，而是完整的项目交付流程，需要多步骤规划。

### 2. 真实约束（Realistic Constraints）
- 遗留代码库：必须阅读和理解现有代码
- 生产 API：与真实系统集成
- 预算限制：必须在成本约束下交付
- 客户需求：需要理解模糊的自然语言需求

### 3. 端到端评测
不是评测代码片段，而是评测最终交付的系统在与用户交互中的表现。

## 对 Agent 评测的启示

1. **从能力测试到交付测试** — 现有基准测试"能不能做"，τ-bench 测试"能不能交付"
2. **约束下的优化** — 真实工程是在约束中寻找最优解，而非追求理论最优
3. **迭代与沟通** — 优秀交付需要需求澄清、方案迭代、客户沟通
4. **系统思维** — 不是写代码，而是构建可维护、可扩展的系统

## 局限性（待进一步调研）
- 4 个领域的代表性？
- 模拟用户与真实用户的差距？
- 服务成本预算如何量化？
- 其他模型（GPT-4o、Gemini）的表现？

## 下一步
- 调研 τ-bench 原始版本（airline/retail 领域）的结果
- 对比 SWE-bench 的代码能力评测
- 探索自我进化机制如何帮助 Agent 提升交付能力

---
**迭代状态**: 完成
**覆盖度**: 核心设计、评测方法、关键结果、启示 ✓
**待补充**: 更多实验数据、与其他基准的对比
