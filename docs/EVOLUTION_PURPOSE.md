# 🧘 演化目的检测 · Evolution Purpose Checker

> v3.0.0 · 王安石叩问 → 钱学森之问 × 霍金熵减 = 8 指标 0-100 评分
> 演化不只是扩张，更是有方向、有目的、有熵减的过程

---

## 📑 目录

- [王安石叩问](#王安石叩问)
- [钱学森之问 (4 指标)](#钱学森之问-4-指标)
- [霍金熵减 (4 指标)](#霍金熵减-4-指标)
- [8 指标综合评分](#8-指标综合评分)
- [评分算法](#评分算法)
- [Phase 切换门控](#phase-切换门控)
- [实测数据](#实测数据)

---

## 王安石叩问

> 王安石 (LIT-WAN-001):
> "天变不足畏，祖宗不足法，人言不足恤——但演化，究竟为了什么？"

王安石 Tab 每天叩问一次——演化引擎跑了一天，不是看跑了多少 cycle，而是看：
- **reinforced 增量** 是否有意义？
- **derived 增量** 是否真的是新的？
- **创新学习比** 是上升还是下降？
- **坍缩通过** 是自然坍缩还是强制补数？

---

## 钱学森之问 (4 指标)

### 背景

钱学森 (ENG-QIAN-001) 晚年之问：
> "为什么我们的学校总是培养不出杰出人才？"

演化引擎版钱学森之问——为什么我们的演化总是坍缩不到 7？

### 指标定义

#### Q1: Reinforced 增量 (权重 12.5%)

```
Q1 = normalize(reinforced_delta, target=1000)
reinforced_delta = reinforced_count(today) - reinforced_count(yesterday)
```

| 增量 | 得分 | 说明 |
|------|------|------|
| ≥ 1000 | 100 | 理想增长 |
| 500-1000 | 75 | 健康增长 |
| 100-500 | 50 | 缓慢增长 |
| < 100 | 25 | 停滞 |
| < 0 | 0 | 退化 |

#### Q2: Derived 增量 (权重 12.5%)

```
Q2 = normalize(derived_delta, target=500)
derived_delta = derived_count(today) - derived_count(yesterday)
```

Derived 是演化的核心——没有新衍生，演化就是原地踏步。

#### Q3: 创新学习比 (权重 12.5%)

```
Q3 = innovation_ratio = derived_delta / (reinforced_delta + 1)
```

| 比值 | 得分 | 说明 |
|------|------|------|
| ≥ 0.5 | 100 | 创新驱动 |
| 0.2-0.5 | 75 | 创新 + 学习平衡 |
| 0.1-0.2 | 50 | 以学习为主 |
| < 0.1 | 25 | 机械重复 |

#### Q4: 坍缩通过 (权重 12.5%)

```
Q4 = collapse_pass_rate = count(collapsed_to_7) / total_metrics
```

所有关键指标 (ai_employees / connections / rule_knowledge / derived / graph_nodes / graph_relations / messages / tables) 必须坍缩到 7。

---

## 霍金熵减 (4 指标)

### 背景

霍金 (SCI-HAWK-001) 关于黑洞熵的发现：
> 黑洞有熵，熵与事件视界面积成正比。宇宙整体熵在增加，但局部可以熵减。

演化引擎版霍金熵减——演化必须是局部熵减的过程，而非熵增的循环。

### 指标定义

#### H1: 坍缩终点 = 7 (权重 12.5%)

```
H1 = 100 if collapse_to_7(all_metrics) == 7 else 0
```

这是最硬的硬约束。任何指标不坍缩到 7，H1 = 0。

#### H2: 自然 Reinforced > 强制对齐 (权重 12.5%)

```
H2 = (natural_reinforced / (natural_reinforced + forced_alignment + 1)) × 100
```

| 比值 | 得分 | 说明 |
|------|------|------|
| ≥ 0.8 | 100 | 自然演化为主 |
| 0.5-0.8 | 75 | 自然 + 强制平衡 |
| 0.2-0.5 | 50 | 强制对齐过多 |
| < 0.2 | 25 | 几乎全是强制 |

**定义**：
- **natural_reinforced**: EigenFlux 连接自然强化（消息 > 10 次 → strength 增加）
- **forced_alignment**: auto_derive 强制补数（为了坍缩到 7 而补的 derived）

#### H3: CTC 零环 (权重 12.5%)

```
H3 = 100 if ctc_graph_has_no_cycle() else 0
```

**CTC (Blueprint-Topology-Causality)**:
- 每个 Flask Blueprint 的 import 依赖图
- 每个演化阶段的知识流向因果图
- 坍缩分类器的执行顺序因果图

任何一个有环 → H3 = 0。

**检测方法**：Tarjan SCC (强连通分量) 算法。

```python
def ctc_zero_ring() -> bool:
    """所有 CTC 因果图强连通分量大小 ≤ 1"""
    graphs = [
        blueprint_import_graph(),
        evolution_flow_graph(),
        collapse_classifier_graph(),
    ]
    for g in graphs:
        sccs = tarjan_scc(g)
        for scc in sccs:
            if len(scc) > 1:
                return False  # 有环
    return True  # 零环
```

#### H4: 无矛盾规则 (权重 12.5%)

```
H4 = 100 if no_rule_contradictions() else 0
```

**矛盾检测**：

| 矛盾类型 | 示例 |
|----------|------|
| 直接否定 | "reinforce 必须 > 0" vs "reinforce 可以 = 0" |
| 量词冲突 | "所有指标坍缩到 7" vs "部分指标不需要坍缩" |
| 时序矛盾 | "derive 在 reinforce 之前" vs "reinforce 在 derive 之前" |

**检测方法**：First-Order Logic (FOL) 定理证明。

```python
def no_rule_contradictions() -> bool:
    """规则知识库中不存在 FOL 可证的矛盾"""
    rules = load_all_rules()
    for i, r1 in enumerate(rules):
        for r2 in rules[i+1:]:
            if fol_prove(NOT(r1 ∧ r2)):
                return False
    return True
```

---

## 8 指标综合评分

### 公式

```
TOTAL = (Q1 + Q2 + Q3 + Q4 + H1 + H2 + H3 + H4) / 8
```

每指标满分 100，每指标权重 12.5%，总分 0-100。

### 评分等级

| 总分 | 等级 | 说明 | 行动 |
|------|------|------|------|
| 90-100 | **S** | 完美演化 | 进入 Phase 3 无限制扩张 |
| 80-89 | **A** | 优秀演化 | 维持 Phase 2 血肉填充 |
| 70-79 | **B** | 良好演化 | 维持 Phase 2，关注短板 |
| 60-69 | **C** | 及格演化 | 维持 Phase 1，加强 reinforce |
| 50-59 | **D** | 不及格 | 触发 auto_derive 全量补数 |
| < 50 | **F** | 失败 | 触发康熙 Layer 3 强制修复 |

### v3.0.0 实测估算

假设实测值：
| 指标 | 实测 | 得分 |
|------|------|------|
| Q1 Reinforced 增量 | ~800/天 | 75 |
| Q2 Derived 增量 | ~100/天 | 50 |
| Q3 创新学习比 | 100/800 = 0.125 | 50 |
| Q4 坍缩通过 | 8/8 = 100% | 100 |
| H1 坍缩终点=7 | ✅ | 100 |
| H2 自然 > 强制 | ~70% | 75 |
| H3 CTC 零环 | ✅ | 100 |
| H4 无矛盾规则 | ✅ | 100 |
| **总分** | | **81.25 → A** |

---

## 评分算法

### `EVOLUTION_PURPOSE_CHECKER`

```python
class EvolutionPurposeChecker:
    """演化目的检测模块 · 8 指标 0-100 评分"""

    def score(self) -> dict:
        q1 = self._q1_reinforced_delta()
        q2 = self._q2_derived_delta()
        q3 = self._q3_innovation_ratio()
        q4 = self._q4_collapse_pass()
        h1 = self._h1_collapse_7()
        h2 = self._h2_natural_vs_forced()
        h3 = self._h3_ctc_zero_ring()
        h4 = self._h4_no_contradictions()

        total = (q1 + q2 + q3 + q4 + h1 + h2 + h3 + h4) / 8
        grade = self._grade(total)

        return {
            'total': total,
            'grade': grade,
            'metrics': {
                'Q1_reinforced_delta': q1,
                'Q2_derived_delta': q2,
                'Q3_innovation_ratio': q3,
                'Q4_collapse_pass': q4,
                'H1_collapse_to_7': h1,
                'H2_natural_over_forced': h2,
                'H3_ctc_zero_ring': h3,
                'H4_no_contradictions': h4,
            },
            'recommendations': self._recommend(q1, q2, q3, q4, h1, h2, h3, h4),
        }

    def _grade(self, total: float) -> str:
        thresholds = [(90,'S'),(80,'A'),(70,'B'),(60,'C'),(50,'D')]
        for t, g in thresholds:
            if total >= t: return g
        return 'F'
```

---

## Phase 切换门控

演化引擎 Phase 切换必须通过 Purpose Checker：

```
Phase 1 → Phase 2 门控:
  ├── reinforced ≥ 2000
  ├── Q4 (坍缩通过) = 100
  ├── H1 (坍缩终点=7) = 100
  ├── H3 (CTC 零环) = 100
  └── TOTAL ≥ 60 (C)

Phase 2 → Phase 3 门控:
  ├── reinforced ≥ 10000
  ├── Q1 ≥ 75 (reinforced 增量健康)
  ├── Q3 ≥ 50 (创新学习比不低)
  ├── H2 ≥ 75 (自然演化为主)
  └── TOTAL ≥ 80 (A)
```

---

## 实测数据

### v3.0.0 演化目的每日检测（示例）

```
日期: 2026-09-19
┌─────────────────────────────────────────┐
│ EVOLUTION_PURPOSE_CHECKER               │
├─────────────────────────────────────────┤
│                                         │
│  🎯 钱学森之问 (50 分)                   │
│  Q1 Reinforced 增量  ████████░░ 75/100  │
│  Q2 Derived 增量     █████░░░░░ 50/100  │
│  Q3 创新学习比       █████░░░░░ 50/100  │
│  Q4 坍缩通过         ██████████ 100/100 │
│                                         │
│  🌌 霍金熵减 (50 分)                     │
│  H1 坍缩终点=7       ██████████ 100/100 │
│  H2 自然>强制        ████████░░ 75/100  │
│  H3 CTC 零环         ██████████ 100/100 │
│  H4 无矛盾规则       ██████████ 100/100 │
│                                         │
│  ─────────────────────────              │
│  总分: 81.25 → Grade A                  │
│  Phase: Phase 2 (2000 ≤ reinforced < 10000) │
│                                         │
│  建议:                                   │
│  · Q2 Derived 增量偏低 → 触发 auto_derive │
│  · Q3 创新学习比偏低 → 提升 derive 质量   │
│                                         │
└─────────────────────────────────────────┘
```

### 历史趋势

```
Day -7: ████████░░ 68 (C)  → Phase 1
Day -6: █████████░ 72 (B)  → Phase 1→2 门控
Day -5: ████████░░ 71 (B)  → 补 derived
Day -4: █████████░ 75 (B)  → CTC 零环修复
Day -3: █████████░ 78 (B)  → 自然 reinforce 提升
Day -2: █████████░ 80 (A)  → Phase 2 ✅
Day -1: █████████░ 80 (A)  → 维持
Day 0 : █████████░ 81 (A)  → 今天
```

---

*王安石介甫 (LIT-WAN-001) 叩问 · 钱学森星天 (ENG-QIAN-001) 指标 · 霍金宙光 (SCI-HAWK-001) 熵减*
*v3.0.0 · 2026-09-19*
