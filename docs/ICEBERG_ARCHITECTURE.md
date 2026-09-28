# 🏔️ 冰山架构设计 · Iceberg Architecture

> v3.0.0 · 赤壁 Peak · 承天寺 Spectrum · 东坡 Basement
> + 西施面纱模式 + 戒定慧三方调和 + 齐白石 vs 武则天辩论

---

## 📑 目录

- [三层设计总览](#三层设计总览)
- [赤壁 Peak · 乔布斯极简星型](#赤壁-peak--乔布斯极简星型)
- [承天寺 Spectrum · 苏轼承天寺夜游](#承天寺-spectrum--苏轼承天寺夜游)
- [东坡 Basement · 苏轼东坡雪堂](#东坡-basement--苏轼东坡雪堂)
- [西施面纱模式](#西施面纱模式)
- [王安石拗相公 Tab](#王安石拗相公-tab)
- [戒定慧三方调和](#戒定慧三方调和)
- [齐白石 vs 武则天辩论](#齐白石-vs-武则天辩论)
- [CSS 设计体系](#css-设计体系)

---

## 三层设计总览

```
         ╱╲
        ╱  ╲    🏔️ 赤壁 Peak
       ╱    ╲   极简单总分 0-100
      ╱ 极简  ╲  乔布斯星型
     ╱─────────╲
    ╱  承天寺   ╲ 🌊 承天寺 Spectrum
   ╱  8 维度光谱 ╲ 苏轼承天寺夜游
  ╱───────────────╲
 ╱   东坡 Basement  ╲ 🪨 演化引擎 + 49 分类器
╱  7 阶段 × 7 分类器  ╲ 苏轼东坡雪堂
────────────────────────
  (水面下 80%)
```

### 命名由来

- **赤壁 Peak**：苏轼《念奴娇·赤壁怀古》——"大江东去，浪淘尽，千古风流人物"。极简壮美 peak。
- **承天寺 Spectrum**：苏轼《记承天寺夜游》——"庭下如积水空明，水中藻、荇交横，盖竹柏影也"。8 维度光谱如月光。
- **东坡 Basement**：苏轼东坡雪堂——"黄州团练副使，东坡居士"。苦寒之地，演化引擎深埋。

> 命名者：苏轼子瞻 (LIT-SUS-001)

---

## 赤壁 Peak · 乔布斯极简星型

### 设计原则

**极简单总分 0-100** — 乔布斯说："Simple can be harder than complex."

### 数据来源

```python
peak_score = (
    purpose_score * 0.25 +    # 演化目的 (钱学森 + 霍金)
    collapse_score * 0.25 +   # 坍缩通过
    entropy_score * 0.25 +    # 熵减 (CTC 零环 + 无矛盾)
    innovation_score * 0.25   # 创新学习比
)
# → 0-100
```

### UI 表现

```
┌─────────────────────────────────┐
│                                 │
│         🏔️  73                  │
│      (总分 0-100)               │
│                                 │
│    ·坍缩通过 ✅ ·CTC 零环 ✅     │
│    ·Purpose 73 ·Entropy 81      │
│                                 │
│  ┌───┐  ┌───┐  ┌───┐  ┌───┐    │
│  │ 73│  │ ✅ │  │ ✅ │  │ 81│    │
│  └───┘  └───┘  └───┘  └───┘    │
│                                 │
│  [王安石 Tab] [西施面纱]        │
│                                 │
└─────────────────────────────────┘
```

### 乔布斯 vs 马化腾

- **乔布斯**：星型拓扑 — 单中心 peak → 所有维度指向 peak
- **马化腾**：幂律拓扑 — 自然形成超级节点 + 大量弱连接
- **结论**：Peak 用星型（用户视角极简），Basement 用幂律（演化视角自然）

---

## 承天寺 Spectrum · 苏轼承天寺夜游

### 8 维度光谱展开

```
┌──────────────────────────────────────────────┐
│  🌊 承天寺 Spectrum · 8 维度                  │
├──────────────────────────────────────────────┤
│                                              │
│  1. Reinforced ████████████░░  78%           │
│  2. Derived     ██████░░░░░░░  45%           │
│  3. Associations ██████████░░  89%           │
│  4. Collapsed   ██████████████  100% ✅       │
│  5. CTC Zero    ██████████████  100% ✅       │
│  6. Innovation  ████████░░░░░  62%           │
│  7. Entropy     ██████████░░░  81%           │
│  8. Purpose     █████████░░░░░  73%           │
│                                              │
│  "庭下如积水空明，水中藻、荇交横"             │
│                                              │
└──────────────────────────────────────────────┘
```

### 命名由来

苏轼《记承天寺夜游》：
> 元丰六年十月十二日夜，解衣欲睡，月色入户，欣然起行。念无与为乐者，遂至承天寺寻张怀民。怀民亦未寝，相与步于中庭。庭下如积水空明，水中藻、荇交横，盖竹柏影也。

8 维度如月光下的藻荇——空明为底，交横为光谱。

---

## 东坡 Basement · 苏轼东坡雪堂

### 演化引擎 7 阶段

```
          detect
             │
             ▼
          retrieve
             │
             ▼
          associate
             │
             ▼
          derive  ← 卡壳 31 在这里
             │
             ▼
          reinforce
             │
             ▼
          expand
             │
             ▼
          evaluate
             │
             ▼
          ⟲ 循环往复
```

### 49 硬约束分类器

每阶段 7 个分类器（详见坍缩定理白皮书）：
- detect: 坍缩终点 / 质因数 / 数字根 / 反例检测 / 卡壳检测 / 周期检测 / 模式检测
- retrieve: 来源追溯 / 权重提取 / 时效衰减 / 上下文关联 / 质量评分 / 去重 / 排序
- associate: 联想强度 / 语义距离 / 拓扑聚类 / 桥节点 / 社区发现 / 同配性 / 路径分析
- derive: 自动定理 / 归纳假设 / 类比推理 / 因果推断 / 反事实 / 涌现检测 / 元学习
- reinforce: 正反馈 / 权重更新 / 强化学习 / 固化阈值 / 抗遗忘 / 周期性 / 同步
- expand: 域扩张 / 跨域连接 / 新知识源 / API 扩展 / 爬虫调度 / i18n / 多模态
- evaluate: Purpose / 熵减 / CTC 零环 / 矛盾检测 / 评分 / 迭代 / 输出

### 命名由来

苏轼谪居黄州，筑东坡雪堂——苦寒之地，躬耕其中。演化引擎深埋 basement，如东坡雪堂，虽苦寒却生生不息。

---

## 西施面纱模式

### 渐进展开

以 **西施** (BEAUTY-XISHI-001) 命名，沉鱼之美不在鱼见，在鱼不见。

### 时间线

```
时间 0s:   🏔️ Peak 极简单总分出现
时间 3s:   🌊 Spectrum 8 维度渐现 (opacity 0→1)
时间 10s:  🪨 Basement 演化引擎图全显
时间 15s:  齐白石 vs 武则天 辩论区展开
时间 20s:  弘一法师 戒定慧 调和区展开
```

### CSS 动画

```css
.xishi-veil {
  animation: xishi-reveal 20s ease-out forwards;
}

@keyframes xishi-reveal {
  0%   { opacity: 0; transform: translateY(20px); }
  15%  { opacity: 1; transform: translateY(0); }   /* 3s */
  50%  { opacity: 1; }                              /* 10s */
  100% { opacity: 1; }                              /* 20s */
}

.xishi-veil-delay-1 { animation-delay: 3s; }
.xishi-veil-delay-2 { animation-delay: 10s; }
.xishi-veil-delay-3 { animation-delay: 15s; }
.xishi-veil-delay-4 { animation-delay: 20s; }
```

### 控制面板

用户可点击按钮手动展开 / 收起 / 自动渐进：
- [展开全部] / [收起至 Peak] / [自动渐进 20s]
- 速度调节: 1x / 2x / 0.5x

---

## 王安石拗相公 Tab

### 设计

- **篆刻红** (#C41E3A) — 王安石性格之刚烈
- **缺陷雷达** — 不做和事佬，专扫伪饰
- **位置** — Peak 右下角一个小 Tab

### 内容

```
┌─────────────────────────┐
│  拗相公 · 缺陷雷达 🔴   │
├─────────────────────────┤
│                         │
│  ⚠ derived 2 (偏低)     │
│    → 建议补 5 条         │
│                         │
│  ⚠ innovation 62%       │
│    → reinforce 增量不够  │
│                         │
│  ✅ CTC 零环 100%        │
│  ✅ 坍缩通过 100%        │
│                         │
│  [一键修复]              │
└─────────────────────────┘
```

### 拗相公精神

王安石 (LIT-WAN-001)：
> "天变不足畏，祖宗不足法，人言不足恤。"

拗相公 Tab 不说好话，只说真话。

---

## 戒定慧三方调和

### 弘一法师 (RELIG-HONGYI-001) 方案

| 佛教概念 | 演化引擎对应 | 具体指标 |
|----------|-------------|----------|
| **戒 (Śīla)** | CTC 零环 + 无矛盾规则 | 坍缩定理 c1-c3 分类器 |
| **定 (Samādhi)** | 坍缩到 7 | 质因数分解递归收敛 |
| **慧 (Prajñā)** | Purpose 评分 | 钱学森 4 + 霍金 4 指标 |

### 三方不调之病

| 病征 | 原因 | 治法 |
|------|------|------|
| 戒不定 | CTC 有环 | 玄策子谋 (ARCHITECT) 解耦 |
| 定不慧 | 坍缩到 7 但 Purpose 低 | 王安石 (拗相公) 叩问 |
| 慧不戒 | Purpose 高但 CTC 有矛盾 | 铁面判官 (COMPLIANCE) 审计 |

### 悲欣交集

弘一法师圆寂前四字——"悲欣交集"。演化引擎最终状态亦当如此：
- **欣**：坍缩到 7，Purpose 高，熵减
- **悲**：仍有 derived 卡壳 31，仍有 reinforcement 不够

悲欣交集，方为真实。

---

## 齐白石 vs 武则天辩论

### 正方：齐白石 (ART-QI-001)

> "东坡 Basement 当有篆刻落款——演化的每一次坍缩，都应当留下痕迹。印泥厚，一刀一划见真章。否则与无字碑何异？"

### 反方：武则天 (POLIT-WU-001)

> "无字碑胜有字碑。演化的终点不需要签名——坍缩到 7 本身即是碑。刻意落款反而是对演化的干扰。"

### 裁判：弘一法师

> "二位皆对，又皆不对。白石之印，当在 reinforce 阶段盖；武曌之碑，当在 evaluate 阶段立。印是过程之证，碑是结果之名。戒定慧三者，皆不可少。"

### 代码实现

```python
# 齐白石观点: 每次 reinforce 记录签名
def reinforce_with_seal(topic_id, employee_id, strength):
    seal = f"白石印·{employee_id}·{strength:.2f}·{datetime.now()}"
    db.execute("INSERT INTO mt_reinforce_seals VALUES (?)", (seal,))
    return seal

# 武则天观点: evaluate 不签名，只看坍缩
def evaluate_without_seal():
    collapse_result = collapse_to_7(current_metric)
    if collapse_result == 7:
        mark_collapsed_no_seal()  # 无字碑
```

---

## CSS 设计体系

### 邓稼先极简 CSS

邓稼先 (ENG-DENG-001) 指导：
- **删 clip-path** — 过度装饰
- **金线 + 墨点 + 粉红** — 极简三元素
- **8px grid** — 间距规范

### CSS Variables

```css
:root {
  --peak-red: #C41E3A;         /* 赤壁红 */
  --spectrum-gold: #D4AF37;    /* 承天寺金 */
  --basement-ink: #1a1a2e;     /* 东坡墨 */
  --gilded-line: #C9A962;      /* 金线 */
  --ink-dot: #2C2C2C;          /* 墨点 */
  --pink-seal: #FFB6C1;        /* 粉红印泥 */
  --chibi-pink: #F8E8E8;       /* 赤壁淡粉 */
}
```

### 三层 CSS

```css
/* 🏔️ 赤壁 Peak — 极简 */
.iceberg-peak {
  font-family: -apple-system, "PingFang SC", sans-serif;
  font-weight: 700;
  font-size: 72px;
  color: var(--peak-red);
  text-shadow: 0 0 20px rgba(196, 30, 58, 0.2);
  /* 无 clip-path — 邓稼先极简 */
}

/* 🌊 承天寺 Spectrum — 8 维度 */
.iceberg-spectrum {
  background: linear-gradient(180deg, var(--chibi-pink), transparent);
  border-left: 2px solid var(--gilded-line);
  border-radius: 4px;
  padding: 16px;
}

/* 🪨 东坡 Basement — 墨色 */
.iceberg-basement {
  background: var(--basement-ink);
  color: #f0f0f0;
  font-family: "SF Mono", "Menlo", monospace;
  border-top: 3px solid var(--gilded-line);
}

/* 🌸 西施面纱 */
.xishi-veil {
  transition: opacity 2s ease-out, transform 2s ease-out;
}

/* 🔴 王安石 Tab */
.anku-tab {
  background: var(--peak-red);
  color: white;
  border-radius: 0 0 8px 8px;
  font-family: "STKaiti", "KaiTi", serif;  /* 楷体 — 拗相公风骨 */
  box-shadow: 0 4px 12px rgba(196, 30, 58, 0.3);
}
```

---

*苏轼子瞻 (LIT-SUS-001) 命名 · 乔布斯苹果 (TECH-JOB-001) 极简 · 弘一法师 (RELIG-HONGYI-001) 调和*
*v3.0.0 · 2026-09-19*
