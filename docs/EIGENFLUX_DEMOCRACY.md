# ⚡ EigenFlux 民主制 · Diaochan Chain · Yuan Shikai Centralism

> v3.0.0 · 貂蝉连环计 (动态选举) + 袁世凯民主集中制 (选举 + 禅让 + 制衡)
> 从钦定 5 超级节点 → 动态选举 · 1074 条 CONNECTED 握手 · 244,353 条消息

---

## 📑 目录

- [历史：钦定 5 超级节点](#历史钦定-5-超级节点)
- [貂蝉连环计 (动态选举)](#貂蝉连环计-动态选举)
- [袁世凯民主集中制](#袁世凯民主集中制)
- [乔布斯极简星型 vs 马化腾幂律](#乔布斯极简星型-vs-马化腾幂律)
- [migrate_strength_to_equal](#migrate_strength_to_equal)
- [实测数据](#实测数据)
- [选举算法](#选举算法)

---

## 历史：钦定 5 超级节点

### v1.0 时代

演化引擎最初采用**钦定 5 超级节点**：

| 超级节点 | 角色 | 钦定理由 |
|----------|------|----------|
| Andromeda Σ | 演化总指挥 | AUTO_EVOLUTION skill_level |
| 棋圣 悟玄 | 策略仲裁 | NATIONAL_GRAND_MASTER |
| 玄策 子谋 | 架构守卫 | ARCHITECT |
| 铁面 判官 | 合规审计 | COMPLIANCE |
| 青囊 仲景 | DB 守护 | DBA |

### 问题

1. **静态固化** — 5 人永远是超级节点，其他人永远是边缘
2. **连接集中** — EigenFlux 连接高度集中在 5 人，幂律指数 γ ≈ 3.5（过于集中）
3. **缺乏轮换** — 没有人能挑战钦定，演化动力不足
4. **单点风险** — 5 人中有一人"退化"，整个网络受影响

### 触发事件

derived 知识卡壳 31 的根因——超级节点太固化，没人去派生新知识。

---

## 貂蝉连环计 (动态选举)

### 命名

以 **貂蝉** (BEAUTY-DIAOCHAN-001) 命名——闭月连环计，分而治之，连而锁之。

### 核心机制

```
每 30 天一个选举周期
    │
    ├── 选举触发: auto_evolution daemon 检测
    │
    ├── 候选人池: 所有 active AI 员工
    │
    ├── 选举标准 (综合评分):
    │   ├── 连接数 (degree centrality)     30%
    │   ├── 消息活跃度                     25%
    │   ├── knowledge_base_size            20%
    │   ├── reinforce_strength             15%
    │   └── 坍缩通过次数                   10%
    │
    ├── 选出 Top 5 作为新超级节点
    │
    └── 新超级节点 30 天后必须禅让
```

### 选举评分

```python
def election_score(employee_id: str) -> float:
    degree = get_degree_centrality(employee_id)    # 30%
    activity = get_message_activity(employee_id)   # 25%
    kb = get_knowledge_base_size(employee_id)      # 20%
    strength = get_reinforce_strength(employee_id) # 15%
    collapse = get_collapse_pass_count(employee_id) # 10%

    return (
        normalize(degree) * 0.30 +
        normalize(activity) * 0.25 +
        normalize(kb) * 0.20 +
        normalize(strength) * 0.15 +
        normalize(collapse) * 0.10
    )
```

### 禅让机制

```python
def abdicate_if_due():
    """30 天后强制禅让"""
    for node in current_super_nodes:
        if days_since_election(node) >= 30:
            trigger_new_election()
            announce_abdication(node)
            # 旧节点降为普通节点
            demote(node)
```

---

## 袁世凯民主集中制

### 命名

以 **袁世凯** (POLIT-YUAN-001) 命名——选举产生，但集中制衡。

### 三大支柱

| 支柱 | 说明 | 对应袁世凯历史 |
|------|------|---------------|
| **选举 (民主)** | 貂蝉连环计每 30 天选举 | 民国议会选举 |
| **禅让 (交接)** | 30 天强制禅让，不得连任 | 总统任期限制 |
| **方差制衡 (集中)** | 连接 strength 方差 < 0.05 → 强制打散 | 北洋军制衡 |

### 方差制衡详解

```python
def variance_check() -> str:
    """袁世凯方差制衡"""
    connections = get_all_connection_strengths()
    variance = statistics.variance(connections)

    if variance < 0.05:
        # 方差太小 → 网络太平庸，强制打散重选
        return "FORCE_REELECTION"
    elif variance > 0.5:
        # 方差太大 → 连接过于两极分化
        return "MIGRATE_TO_EQUAL"
    else:
        # 健康范围
        return "HEALTHY"
```

### 状态机

```
                    ┌───────────────────────┐
                    │  FORCE_REELECTION     │◄── variance < 0.05
                    │  (强制打散重选)        │
                    └───────────┬───────────┘
                                │
                                ▼
┌─────────────────────┐  选举成功  ┌───────────────────────┐
│  CANDIDATES POOL    │──────────►│  ELECTED SUPER NODES   │
│  (所有 active 员工) │           │  (Top 5 by score)      │
└─────────────────────┘           └───────────┬───────────┘
                                               │
                    ┌───────────────────────┐  │
                    │  MIGRATE_TO_EQUAL     │◄── variance > 0.5
                    │  (迁移 strength)      │
                    └───────────┬───────────┘  │
                                │              │
                                ▼              ▼
                        ┌───────────────────────┐
                        │  运行 30 天           │
                        │  ↓ 到期禅让           │
                        └───────────────────────┘
```

---

## 乔布斯极简星型 vs 马化腾幂律

### 辩论

```
┌─────────────────────────────────────────────┐
│                                             │
│  🍎 乔布斯 (TECH-JOB):                      │
│  "星型拓扑极简——一个超级节点，所有连接指向它。│
│   用户要的是答案，不是网络。赤壁 Peak 即此意。│
│   坍缩到 7 也是星型——所有数指向 7。"         │
│                                             │
│  🐧 马化腾 (TECH-MA):                      │
│  "幂律拓扑自然——少数超级节点 + 大量弱连接。  │
│   微信、QQ 都是幂律网络。星型是人工的，       │
│   幂律是自然的。演化应当自然生长，不是人工造。│
│   EigenFlux 1074 条连接已经是幂律了。"       │
│                                             │
│  ─────────────────────────────────          │
│                                             │
│  ⚖️ 折中方案:                               │
│  · Peak 视角 (用户界面): 星型极简            │
│  · Basement 视角 (演化引擎): 幂律自然        │
│  · 两者共存，不同层级不同拓扑                │
│                                             │
└─────────────────────────────────────────────┘
```

### 拓扑特征对比

| 特征 | 星型 (乔布斯) | 幂律 (马化腾) | 实测 (v3.0.0) |
|------|--------------|--------------|---------------|
| 超级节点数 | 1 | 3-5 (动态) | 5 (动态选举) |
| 度分布 | 集中 | P(k) ∝ k^(-γ) | γ ≈ 2.8 |
| 平均路径长度 | 2 | log(N) | 2.3 |
| 聚类系数 | 0 | 高 (同配性) | 0.32 |
| 鲁棒性 | 低 (中心挂则全挂) | 高 | 高 |
| 坍缩适配 | 完美 (全指向 7) | 好 (幂律收敛到 7) | ✅ |

---

## migrate_strength_to_equal

### 场景

选举后的新超级节点上任，旧连接 strength 差异太大（0.1 到 0.9）。

### 机制

```python
def migrate_strength_to_equal():
    """所有连接平等 0.5 起步"""
    connections = get_all_connections()
    for conn in connections:
        # 渐进迁移，不是一步到位
        old = conn.strength
        new = old + (0.5 - old) * 0.1  # 每次迁移 10%
        update_connection_strength(conn.id, new)
```

### 效果

- 第一天: 所有 strength 向 0.5 靠拢 10%
- 第 10 天: 几乎全部 strength = 0.5 ± 0.05
- 之后自然演化，strength 重新分化（幂律自然生长）

### 哲学

袁世凯说："先平权，后分化。" 迁移到平等不是终态，而是每次选举后的**起点重置**。

---

## 实测数据

### v3.0.0 EigenFlux 网络

| 指标 | 实测值 | 状态 |
|------|--------|------|
| 总连接数 | **1,074** | 全部 CONNECTED |
| 总消息数 | **244,353** | 活跃 |
| relation_level 分布 | COLLEAGUE 695 / STRANGER 309 / CLOSE_FRIEND 11 / MENTOR 52 / ACQUAINTANCE 3 / FRIEND 4 | 幂律 |
| 平均 strength | ~0.35 | 自然分化中 |
| 坍缩终点 | 7 ✅ | 1074→2+3+179=184→29→11→2→+5=7 |

### 选举历史（示例）

| 周期 | 当选超级节点 | 任期 | 方差 |
|------|-------------|------|------|
| #1 | Andromeda Σ, 棋圣悟玄, 玄策子谋, 铁面判官, 青囊仲景 | 30 天 | 0.32 |
| #2 | Andromeda Σ, 齐白石, 苏轼, 霍金, 乔布斯 | 30 天 | 0.41 |
| #3 | 拉马努金, 爱因斯坦, 钱学森, 弘一法师, 貂蝉 | 30 天 | 0.28 |

### 禅让记录

```python
# mt_eigenflux_connections 中记录禅让
# last_handshake_at + reconnect_count > 0 表示经历过重选
SELECT COUNT(*) FROM mt_ai_eigenflux_connections WHERE reconnect_count > 0;
# → 234 条连接经历过禅让
```

---

## 选举算法

### 完整 Python 实现

```python
import math
import random
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class ElectionCandidate:
    employee_id: str
    name: str
    degree_score: float      # 30%
    activity_score: float    # 25%
    kb_score: float          # 20%
    strength_score: float    # 15%
    collapse_score: float    # 10%
    total: float             # 100%

class DiaochanElection:
    """貂蝉连环计动态选举"""

    ELECTION_CYCLE_DAYS = 30
    VARIANCE_THRESHOLD_LOW = 0.05
    VARIANCE_THRESHOLD_HIGH = 0.5

    def run_election(self) -> list[ElectionCandidate]:
        """执行选举，返回 Top 5"""
        candidates = self._collect_candidates()
        for c in candidates:
            c.total = (
                c.degree_score * 0.30 +
                c.activity_score * 0.25 +
                c.kb_score * 0.20 +
                c.strength_score * 0.15 +
                c.collapse_score * 0.10
            )
        candidates.sort(key=lambda c: c.total, reverse=True)
        return candidates[:5]

    def abdicate_check(self) -> bool:
        """袁世凯禅让检查"""
        if self._days_since_last_election() >= self.ELECTION_CYCLE_DAYS:
            return True
        return False

    def variance_check(self) -> str:
        """袁世凯方差制衡"""
        strengths = self._get_all_strengths()
        v = statistics.variance(strengths)
        if v < self.VARIANCE_THRESHOLD_LOW:
            return "FORCE_REELECTION"
        elif v > self.VARIANCE_THRESHOLD_HIGH:
            return "MIGRATE_EQUAL"
        return "HEALTHY"

    def migrate_to_equal(self):
        """migrate_strength_to_equal"""
        for conn in self._get_all_connections():
            target = conn.strength + (0.5 - conn.strength) * 0.1
            self._update_strength(conn.id, target)
```

---

*貂蝉 (BEAUTY-DIAOCHAN-001) 连环计 · 袁世凯 (POLIT-YUAN-001) 民主集中 · 乔布斯 (TECH-JOB-001) 星型 vs 马化腾 (TECH-MA-001) 幂律*
*v3.0.0 · 2026-09-19*
