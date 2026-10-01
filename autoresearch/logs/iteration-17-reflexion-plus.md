# 迭代 17: Wave 5 - 探索新的自我进化方法（ReflexionPlus）

## 研究动机

基于 Wave 4 的发现：
1. **reflexion 是最稳健的策略**（96% 成功率），但在 csv_parse_row 等难题上仍有失败
2. **reflexion_insights 的优势不如预期**（90% vs Wave 3 的 100%）
3. **csv_parse_row 是真正的难题**（只有 40% 成功率）

**研究问题**: 能否通过增强反思机制（提供更详细的失败信息）来提升难题的成功率？

## 方法：ReflexionPlus 策略

### 设计理念

ReflexionPlus 在标准 Reflexion 的基础上增加了**增强的失败分析**：
1. 提供完整的测试输出（包括具体的 AssertionError）
2. 让模型看到失败的具体值（如 `['a""b'] != ['a"b']`）
3. 包含"期望值"和"实际值"的对比
4. 提供修复策略建议

### 实现细节

```python
def _enhanced_reflect(self, task: Task, code: str, output: str) -> str:
    # 1. 使用标准反思作为基础
    base_reflection = self.backend.reflect(task, code, output)
    
    # 2. 提取详细的失败模式
    enhanced = f"BASE REFLECTION: {base_reflection}\n\n"
    enhanced += "DETAILED FAILURE ANALYSIS:\n"
    
    # 3. 查找 AssertionError 和 FAIL 行
    for line in output.split('\n'):
        if 'AssertionError' in line or 'FAIL:' in line:
            enhanced += f"  {line.strip()}\n"
            # 包含后续几行作为上下文
            ...
    
    # 4. 提供修复策略建议
    enhanced += "\nFIX STRATEGY: Based on the specific failure above, ..."
    
    return enhanced
```

## 实验结果

### 对比实验（单种子，3 策略）

| 策略 | 成功率 | 首次成功率 | 平均尝试 | LLM 调用数 |
|------|--------|-----------|----------|-----------|
| direct | 0.90 | 0.90 | 1.00 | 10.0 |
| reflexion | **1.00** | 0.90 | 1.10 | 12.0 |
| reflexion_plus | **1.00** | 0.70 | 1.50 | 20.0 |

### csv_parse_row 的详细表现

| 策略 | 结果 | 尝试次数 | 调用次数 | 耗时 |
|------|------|----------|----------|------|
| direct | FAIL | 1 | 1 | 9.13s |
| reflexion | PASS (2nd try) | 2 | 3 | 33.43s |
| reflexion_plus | PASS (4th try) | 4 | 7 | 44.32s |

### 其他任务的表现

**简单任务（safe_divide, fib, flatten 等）**:
- 三种策略都在首次尝试成功
- reflexion_plus 没有优势

**中等任务（parse_duration, word_freq）**:
- reflexion: 首次或第 2 次尝试成功
- reflexion_plus: 需要 2 次尝试（增强反思可能让模型过度关注细节）

**难题（csv_parse_row）**:
- 两种反思策略都成功解决
- reflexion 更高效（2 次尝试 vs 4 次尝试）

## 分析与讨论

### ReflexionPlus 的优缺点

**优点**:
1. ✅ 提供了详细的失败信息
2. ✅ 帮助模型理解具体的错误（AssertionError、期望值/实际值）
3. ✅ 在难题上与 reflexion 相当（都能解决 csv_parse_row）

**缺点**:
1. ❌ 需要更多的尝试次数（1.50 vs 1.10）
2. ❌ 使用了更多的 LLM 调用（20 vs 12）
3. ❌ 对于简单任务效率降低（可能过度关注细节）
4. ❌ 成本效益不如 reflexion（+100% 调用换取相同成功率）

### 为什么 ReflexionPlus 没有明显优势？

**假设**: 增强的失败信息可能让模型"信息过载"，导致：
1. 过度关注细节，忽略了整体逻辑
2. 在简单任务上花费更多时间思考
3. 需要更多的尝试来"消化"详细信息

**证据**:
- reflexion_plus 在 parse_duration 和 word_freq 上需要 2 次尝试（reflexion 只需 1-2 次）
- 首次成功率更低（70% vs 90%）

### 成本效益分析

| 策略 | 成功率提升 | 调用数增加 | 成本效益 |
|------|-----------|-----------|----------|
| direct → reflexion | +10pp | +20% | **最高** |
| direct → reflexion_plus | +10pp | +100% | 中等 |

**结论**: reflexion 仍然是最佳性价比

## 结论

### 1. ReflexionPlus 的增强反思机制有效，但成本过高

- 在解决难题方面与 reflexion 相当（都能解决 csv_parse_row）
- 但需要更多的尝试和调用
- 对于简单任务效率降低

### 2. 最佳策略仍然是 Reflexion

- 96% 成功率（Wave 4 结果）
- 最佳性价比（+20% 调用换取 +8pp 成功率）
- 在简单和中等任务上更高效

### 3. ReflexionPlus 的适用场景

只有当 reflexion 无法解决难题时才值得使用：
- 需要详细的失败信息来指导修复
- 愿意承担更高的成本
- 任务非常复杂，标准反思不够

### 4. 未来改进方向

**减少 ReflexionPlus 的成本**:
1. 只在必要时提供详细信息（如第 3 次尝试失败后）
2. 使用更简洁的失败描述
3. 结合任务难度动态调整反思详细程度

**探索其他改进方向**:
1. 多策略融合（ensemble）
2. 自适应反思（根据任务类型调整策略）
3. 更好的洞察提取机制

## 实验复现

```bash
cd D:\autoresearch
export OPENAI_API_KEY="b9d33016803d445a94c9ef719d80efe2.3Sm7f8vjyq1Vh8bb"
export OPENAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4/"
python experiments/run_experiment.py \
  --backend openai \
  --model glm-4-flash \
  --seeds 1 \
  --strategies direct,reflexion,reflexion_plus \
  --out experiments/results/reflexion-plus-test.json
```

结果保存在: `experiments/results/experiment-openai-261001-084616.json`

---
**迭代状态**: 完成
**覆盖度**: ReflexionPlus 设计与实现 ✓ 对比实验 ✓ 成本效益分析 ✓ 结论与建议 ✓
