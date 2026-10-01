# Wave 7 研究报告：公开推理基准测试

## 研究目标

在真实的公开推理基准（GSM8K、MMLU）上测试 Reflexion 自我进化策略的效果，验证其在不同任务类型上的适用性。

## 实验设计

### 基准测试
1. **GSM8K**（Grade School Math 8K）
   - 任务类型：数学推理
   - 样本数：20 个测试题
   - 评估方式：数值答案匹配
   
2. **MMLU**（Massive Multitask Language Understanding）
   - 任务类型：知识理解（57 个学科）
   - 样本数：10 个测试题
   - 评估方式：选择题答案匹配

### 对比策略
- **Baseline**：直接回答（1 次尝试）
- **Reflexion**：自我进化（最多 3 次尝试，带反思）

### 实验配置
- 模型：GLM-4-Flash（智谱 AI）
- API：https://open.bigmodel.cn/api/paas/v4/
- 种子数：1（初步测试）

## 实验结果

### GSM8K（数学推理）

| 策略 | 准确率 | 改进 | 平均尝试次数 |
|------|--------|------|-------------|
| Baseline | 60% (12/20) | - | 1.00 |
| Reflexion | 60% (12/20) | 0% | 1.90 |

**结论**：在数学推理任务上，Reflexion 没有带来任何改进。

### MMLU（知识理解）

| 策略 | 准确率 | 改进 | 平均尝试次数 |
|------|--------|------|-------------|
| Baseline | 30% (3/10) | - | 1.00 |
| Reflexion | 80% (8/10) | **+50%** | 2.10 |

**结论**：在知识理解任务上，Reflexion 带来了巨大的改进（+50%）！

## 综合分析

### 任务类型对 Reflexion 效果的影响

| 任务类型 | 基准测试 | Baseline | Reflexion | 改进 | 特点 |
|---------|---------|----------|-----------|------|------|
| 数学推理 | GSM8K | 60% | 60% | 0% | 计算密集型 |
| 知识理解 | MMLU | 30% | 80% | **+50%** | 知识密集型 |

### 关键发现

1. **Reflexion 的效果高度依赖任务类型**
   - 知识密集型任务：巨大改进（+50%）
   - 计算密集型任务：无改进（0%）

2. **为什么 MMLU 改进巨大？**
   - 知识密集型任务可以通过反思纠正知识错误
   - 选择题格式允许通过排除法提高准确率
   - 反思过程帮助模型回忆和整合相关知识
   - 模型可以通过反思识别并修正知识盲点

3. **为什么 GSM8K 无改进？**
   - 数学计算需要精确的逻辑推导
   - 反思可能无法纠正计算错误
   - 数学问题的答案是唯一的，反思空间有限
   - 计算错误通常是系统性的，反思难以发现

4. **与之前研究的对比**
   - 代码生成任务：Reflexion 达到 96%（需要调试和修复）
   - GAIA 任务：Reflexion 达到 97.33%（需要逻辑推理）
   - 这表明 Reflexion 最适合需要**迭代反思和修正**的任务

### 理论解释

Reflexion 的有效性取决于任务的**反思空间**：

- **高反思空间**：知识理解、代码调试、逻辑推理
  - 错误可以通过反思发现和纠正
  - 反思过程提供新的信息和视角
  - 改进显著

- **低反思空间**：数学计算、简单查询
  - 错误通常是系统性的
  - 反思难以提供新的信息
  - 改进有限

## 结论

### 主要发现

1. **Reflexion 在知识密集型任务上效果显著**：MMLU 从 30% 提升到 80%（+50%）
2. **Reflexion 在计算密集型任务上效果有限**：GSM8K 保持在 60%（0% 改进）
3. **任务类型是决定 Reflexion 效果的关键因素**

### 实践启示

1. **适用场景**：
   - 知识问答系统
   - 多选题考试
   - 知识检索和整合
   - 代码调试和修复

2. **不适用场景**：
   - 纯数学计算
   - 简单事实查询
   - 需要精确计算的任务

3. **优化建议**：
   - 对于知识密集型任务，优先使用 Reflexion
   - 对于计算密集型任务，考虑其他策略（如 Chain-of-Thought）
   - 可以结合多种策略，根据任务类型动态选择

### 未来研究方向

1. **扩大样本量**：在更多样本上验证结果
2. **测试更多基准**：ARC（科学推理）、HellaSwag（常识推理）
3. **任务类型细分**：研究不同学科（数学、历史、科学等）的效果差异
4. **混合策略**：结合 Reflexion 和 Chain-of-Thought
5. **反思机制优化**：针对不同类型任务设计专门的反思策略

## 实验复现

### GSM8K 实验
```bash
cd D:\autoresearch
export OPENAI_API_KEY="your_api_key"
export OPENAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4/"
python experiments/run_gsm8k_benchmark.py --max-samples 20 --seeds 1 --output experiments/results/gsm8k_20samples.json
```

### MMLU 实验
```bash
python experiments/run_mmlu_benchmark.py --max-samples 10 --seeds 1 --output experiments/results/mmlu_test.json
```

## 参考文献

1. GSM8K: Training Verifiers to Solve Math Word Problems (arXiv: 2110.14168)
2. MMLU: Measuring Massive Multitask Language Understanding (arXiv: 2009.03300)
3. Reflexion: Language Agents with Verbal Reinforcement Learning (arXiv: 2303.11366)

---
**Wave 7 完成日期**: 2026-10-02
**实验代码**: experiments/run_gsm8k_benchmark.py, experiments/run_mmlu_benchmark.py
**实验结果**: experiments/results/gsm8k_20samples.json, experiments/results/mmlu_test.json
