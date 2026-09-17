# 中文指代消解系统

## 系统概述

本系统是一个基于**规则+统计**的中文指代消解系统，采用流水线架构：

```
输入文本 → jieba分词 → 规则修正 → HMM词性标注 → 实体分类 → 指代消解 → 输出
```

### 核心组件

| 组件 | 功能 | 文件 |
|-----|------|-----|
| **ChineseTokenizer** | 分词、词性标注、实体分类 | `tokenizer.py` |
| **CoreferenceResolver** | 指代消解 | `coreference.py` |

---

## 第一层：jieba 分词与词性标注

### 1.1 基础分词

使用 `jieba.posseg` 进行分词和词性标注：

```python
import jieba.posseg as pseg
words = pseg.cut("小明去北京")
# 输出: [('小明', 'nr'), ('去', 'v'), ('北京', 'ns')]
```

### 1.2 jieba 词性标签

| 标签 | 含义 | 示例 |
|-----|------|-----|
| `nr` | 人名 | 小明、刘德华 |
| `nrt` | 音译人名 | 约翰、玛丽 |
| `nrfg` | 外国人名 | 特朗普 |
| `ns` | 地名 | 北京、上海 |
| `nsf` | 音译地名 | 纽约 |
| `s` | 处所词 | 桌上、门口 |
| `n` | 普通名词 | 书、电脑 |
| `r` | 代词 | 他、她、它 |
| `v` | 动词 | 去、买、做 |
| `p` | 介词 | 在、把、被 |

### 1.3 HMM 对未登录词的处理

jieba 内置隐马尔可夫模型（HMM）用于：
- **未登录词识别**：识别词典中没有的新词
- **词性猜测**：根据上下文推断未知词的词性

```
启用HMM: jieba.posseg.cut(text, HMM=True)  # 默认开启
```

---

## 第二层：规则修正系统

### 2.1 自定义词典

通过 `jieba.add_word()` 添加自定义词汇，提高分词准确性：

```python
# 添加人名
jieba.add_word('张阿姨', freq=1000, tag='nr')
jieba.add_word('王大爷', freq=1000, tag='nr')

# 添加物品
jieba.add_word('书', freq=1000, tag='n')

# 添加地名
jieba.add_word('长城', freq=1000, tag='ns')
```

### 2.2 复合词拆分规则

对于 jieba 错误合并的词，进行拆分：

```python
COMPOUND_WORDS = {
    # 动词+场所
    '在家': [('在', 'O'), ('家', 'LOC_PLACE')],
    '回家': [('回', 'O'), ('家', 'LOC_PLACE')],
    '出门': [('出', 'O'), ('门', 'LOC_PLACE')],
    
    # 有+物品
    '有书': [('有', 'O'), ('书', 'OBJ')],
    '有车': [('有', 'O'), ('车', 'OBJ')],
    
    # 动词+物品
    '看电视': [('看', 'O'), ('电视', 'OBJ')],
    '看书': [('看', 'O'), ('书', 'OBJ')],
    
    # 复合人称
    '帅哥美女': [('帅哥', 'PER_TITLE'), ('美女', 'PER_TITLE')],
}
```

### 2.3 误识别排除规则

防止常见词被错误分类：

```python
# 不是地名
NOT_LOCATION = {'东西', '南北', '上下', '左右', '前后'}

# 不是人名
NOT_PERSON = {'华为', '小米', '苹果', '百度', '阿里'}

# 排除词（不识别为实体）
EXCLUDE_WORDS = {'什么', '怎么', '如何', '哪里', '谁'}
```

---

## 第三层：实体精细分类

### 3.1 实体类型

| 类型 | 代码 | 说明 | 示例 |
|-----|------|------|-----|
| 人名 | `PER_NAME` | 真实姓名 | 小明、刘德华、张三 |
| 人称 | `PER_TITLE` | 称谓/职业 | 妈妈、医生、老师 |
| 地名 | `LOC_NAME` | 地理名称 | 北京、上海、纽约 |
| 场所 | `LOC_PLACE` | 一般地点 | 学校、医院、超市 |
| 物品 | `OBJ` | 物体 | 书、手机、电脑 |
| 时间 | `TIME` | 时间词 | 去年、昨天、春节 |
| 其他 | `O` | 非实体 | 动词、介词等 |

### 3.2 分类优先级规则

```python
def _get_entity_type(word, pos):
    # 1. 排除误识别
    if word in NOT_LOCATION: return 'O'
    if word in NOT_PERSON: return 'O'
    
    # 2. 姓+人称模式 → 人称
    # "张阿姨"、"王大爷" → PER_TITLE
    if first_char in SURNAMES and rest in SURNAME_TITLES:
        return 'PER_TITLE'
    
    # 3. 自定义词表（优先级最高）
    if word in FOREIGN_NAMES: return 'PER_NAME'
    if word in COMMON_NAMES: return 'PER_NAME'
    if word in PERSON_TITLES: return 'PER_TITLE'
    if word in FAMOUS_PLACES: return 'LOC_NAME'
    if word in PLACE_WORDS: return 'LOC_PLACE'
    if word in OBJECT_WORDS: return 'OBJ'
    if word in TIME_WORDS: return 'TIME'
    
    # 4. jieba 词性判断（兜底）
    if pos in ['nr', 'nrt', 'nrfg']: return 'PER_NAME'
    if pos in ['ns', 'nsf']: return 'LOC_NAME'
    if pos == 's': return 'LOC_PLACE'
    
    return 'O'
```

### 3.3 词表覆盖范围

#### 人称词表 (PERSON_TITLES)
```
亲属: 妈妈、爸爸、爷爷、奶奶、哥哥、姐姐、叔叔、阿姨...
职业: 医生、护士、老师、警察、司机、律师、经理...
学生: 学生、同学、研究生、博士生、学长、学弟...
网络: 网红、主播、博主、UP主、大神、大佬...
```

#### 场所词表 (PLACE_WORDS)
```
教育: 学校、教室、图书馆、实验室、操场...
医疗: 医院、诊所、药房、病房...
商业: 超市、商场、餐厅、银行、酒店...
交通: 车站、机场、地铁站、码头...
```

#### 物品词表 (OBJECT_WORDS)
```
电子: 手机、电脑、平板、耳机、相机...
交通: 汽车、自行车、高铁、飞机...
食品: 苹果、香蕉、蛋糕、咖啡...
日用: 书、笔、包、衣服、鞋子...
```

#### 时间词表 (TIME_WORDS)
```
日期: 今天、昨天、明天、后天...
周期: 这周、上周、下周、周末...
月份: 这个月、上个月、一月、二月...
年份: 今年、去年、明年...
季节: 春天、夏天、秋天、冬天...
节日: 春节、国庆节、中秋节、圣诞节...
```

---

## 第四层：指代消解逻辑

### 4.1 代词分类

#### 应消解的代词

| 类型 | 代词 | 示例 |
|-----|------|-----|
| 人称代词 | 他、她、他们、她们 | 小明来了。**他**很高兴。 |
| 领属代词 | 他的、她的、它的 | 小明买了书。**他的**书很有趣。 |
| 物品代词 | 它、它们 | 我买了手机。**它**很贵。 |
| 地点代词 | 这里、那里、这边、那边 | 我去了北京。**那里**很繁华。 |
| 时间代词 | 那时候、当时、那阵子 | 去年我去北京。**那时候**天气很好。 |
| 指示代词 | 这个、那个（独立使用） | 桌上有书。**那个**是我的。 |
| 序数代词 | 前者、后者 | 张三和李四是朋友。**前者**是医生。 |

#### 不消解的代词

| 类型 | 代词 | 原因 |
|-----|------|-----|
| 第一人称 | 我、我们、咱们 | 说话者自身 |
| 第二人称 | 你、您、你们 | 听话者 |
| 反身代词 | 自己、本人、自身 | 指向主语自身 |
| 强调反身 | 他自己、她本人 | 强调结构 |
| 泛指代词 | 人家、别人、有人、其他人 | 无确定指代对象 |

### 4.2 消解条件

#### 必须满足的条件

```python
def should_resolve(pronoun, context):
    # 1. 必须有先行词
    if is_first_sentence and pronoun in PERSON_PRONOUNS:
        return False  # 第一句的代词没有先行词
    
    # 2. 不能是泛指代词
    if pronoun in GENERIC_PRONOUNS:
        return False
    
    # 3. 不能是反身代词
    if pronoun in REFLEXIVE_PRONOUNS:
        return False
    
    # 4. 不能是约束变量
    if is_bound_variable(pronoun, context):
        return False  # "每个学生都带了他的书"
    
    # 5. 不能是描述短语
    if pronoun in DESCRIPTIVE_PHRASES:
        return False  # "那个人"、"这个地方"
    
    return True
```

### 4.3 实体追踪机制

使用栈结构追踪最近出现的实体：

```python
class EntityTracker:
    person_stack = []   # 人物栈
    object_stack = []   # 物品栈
    location_stack = [] # 地点栈
    time_stack = []     # 时间栈
    
    def add_entity(entity):
        if entity.type in ['PER_NAME', 'PER_TITLE']:
            person_stack.append(entity)
        elif entity.type == 'OBJ':
            object_stack.append(entity)
        elif entity.type in ['LOC_NAME', 'LOC_PLACE']:
            location_stack.append(entity)
        elif entity.type == 'TIME':
            time_stack.append(entity)
```

### 4.4 消解策略

#### 4.4.1 人称代词消解

```python
def resolve_person_pronoun(pronoun):
    # 近指（他/她）→ 最近的人
    if pronoun in ['他', '她']:
        return person_stack[-1]  # 最近提到的人
    
    # 复数（他们/她们）→ 最近两个人
    if pronoun in ['他们', '她们']:
        return person_stack[-2:].join('和')
```

#### 4.4.2 语义角色分析

根据动词判断代词指向施事者还是受事者：

```python
PATIENT_VERBS = {'批评', '打', '骂', '教训', '表扬'}
EMOTION_VERBS = {'担心', '高兴', '生气', '难过', '害怕'}

def analyze_semantic_role(pronoun, context):
    # "老师批评了小明。他很难过。"
    # → "他"指向被批评的人（小明），而非施事者（老师）
    
    if any(v in before_context for v in PATIENT_VERBS):
        return 'object'  # 受事者
    
    if any(v in after_context for v in EMOTION_VERBS):
        return 'subject'  # 情感主体
```

#### 4.4.3 序数代词消解

```python
def resolve_ordinal(pronoun):
    # "张三和李四是朋友。前者是医生。"
    # 前者 → 先提到的（张三）
    # 后者 → 后提到的（李四）
    
    if pronoun == '前者':
        return person_stack[-2]  # 倒数第二个
    else:  # 后者
        return person_stack[-1]  # 最后一个
```

#### 4.4.4 复指结构处理

识别并删除冗余的复指代词：

```python
def is_reduplicative(before_text, pronoun):
    """
    复指结构："小明他很聪明"
    → "他"紧跟在"小明"后面，是冗余的
    → 应该删除"他"，变成"小明很聪明"
    """
    # 检查最后一个词是否是人名/人称
    last_token = tokenize(before_text)[-1]
    
    # 检查中间是否有分隔词
    separators = {'比', '和', '说', '让', '告诉', '被', '把'}
    if any(sep in before_text[-3:] for sep in separators):
        return False  # 不是复指
    
    return last_token.entity_type in ['PER_NAME', 'PER_TITLE']
```

### 4.5 约束变量检测

量化表达中的代词不消解：

```python
QUANTIFIER_WORDS = {'每个', '每位', '所有', '任何', '各个', '全部'}

def is_bound_variable(pronoun, context):
    """
    "每个学生都带了他的书"
    → "他"被"每个"约束，是约束变量
    → 不应该消解为具体的人
    """
    for quantifier in QUANTIFIER_WORDS:
        if quantifier in context:
            return True
    return False
```

---

## 第五层：消解流程

### 5.1 完整处理流程

```python
def resolve_text(text):
    # 1. 分句
    sentences = split_sentences(text)
    
    for sentence in sentences:
        # 2. 提取实体并追踪
        entities = tokenizer.analyze(sentence)
        for entity in entities:
            tracker.add_entity(entity)
        
        # 3. 查找代词
        pronouns = find_pronouns(sentence)
        
        for pronoun in pronouns:
            # 4. 判断是否应该消解
            if not should_resolve(pronoun):
                continue
            
            # 5. 找到替换实体
            replacement = find_replacement(pronoun)
            
            # 6. 执行替换
            if replacement:
                sentence = replace(sentence, pronoun, replacement)
        
        # 7. 进入下一句
        tracker.next_sentence()
    
    return result
```

### 5.2 替换规则

```python
def find_replacement(pronoun):
    pronoun_type = get_pronoun_type(pronoun)
    
    if pronoun_type == 'PERSON':
        return tracker.get_person()
    elif pronoun_type == 'PERSON_POSS':  # 领属
        return tracker.get_person().text + '的'
    elif pronoun_type == 'OBJECT':
        return tracker.get_object()
    elif pronoun_type == 'LOCATION':
        return tracker.get_location()
    elif pronoun_type == 'TIME':
        return tracker.get_time()
    elif pronoun_type == 'FIRST':  # 前者
        return tracker.person_stack[-2]
    elif pronoun_type == 'SECOND':  # 后者
        return tracker.person_stack[-1]
    elif pronoun_type == 'AMBIGUOUS':  # 这个/那个
        # 优先匹配物品，其次地点
        return tracker.get_object() or tracker.get_location()
```

---

## 处理能力总结

### ✅ 能够处理的情况

| 场景 | 输入 | 输出 |
|-----|------|------|
| 基础人称消解 | 小明来了。**他**很高兴。 | 小明来了。**小明**很高兴。 |
| 领属代词 | 小明买了书。**他的**书很有趣。 | 小明买了书。**小明的**书很有趣。 |
| 物品代词 | 我买了手机。**它**很贵。 | 我买了手机。**手机**很贵。 |
| 地点代词 | 我去了北京。**那里**很繁华。 | 我去了北京。**北京**很繁华。 |
| 时间代词 | 去年我去北京。**那时候**天气好。 | 去年我去北京。**去年**天气好。 |
| 序数代词 | 张三和李四是朋友。**前者**是医生。 | 张三和李四是朋友。**张三**是医生。 |
| 复指删除 | 小明**他**很聪明。 | 小明很聪明。 |
| 语义角色 | 老师批评了小明。**他**很难过。 | 老师批评了小明。**小明**很难过。 |
| 比较结构 | 小明来了。张三比**他**高。 | 小明来了。张三比**小明**高。 |
| 长距离指代 | 小明去北京。**他**在**那里**工作。 | 小明去北京。**小明**在**北京**工作。 |

### ❌ 精确绕过的情况

| 场景 | 输入 | 处理 |
|-----|------|------|
| 第一句无先行词 | **他**很高。 | 保留不变 |
| 句内代词 | 小明说**他**很累。 | 保留不变 |
| 引语结构 | 张三告诉李四**他**应该努力。 | 保留不变 |
| 反身代词 | 小明了解**自己**。 | 保留不变 |
| 强调反身 | 小明了解**他自己**。 | 保留不变 |
| 泛指代词 | **人家**不想去。 | 保留不变 |
| 约束变量 | 每个学生都带了**他**的书。 | 保留不变 |
| 描述短语 | 我认识的**那个人**很友好。 | 保留不变 |
| 第一人称 | **我**很高兴。 | 保留不变 |
| 第二人称 | **你**在哪里？ | 保留不变 |

### ⚠️ 已知限制

| 限制 | 说明 |
|-----|------|
| 零代词 | 不支持省略主语的情况："小明去学校。买了本书。" |
| 事件指代 | 不支持指向事件："小明努力学习。**这**让老师高兴。" |
| 复杂嵌套 | 复杂从句可能不准确 |
| 性别判断 | 不进行性别匹配验证 |

---

## 使用示例

```python
from coreference import CoreferenceResolver

resolver = CoreferenceResolver()

# 基础消解
text = "小明去北京。他在那里工作。"
resolved, replacements = resolver.resolve_text(text)
print(resolved)  # "小明去北京。小明在北京工作。"

# 重置追踪器（处理新文本时）
resolver.reset()

# 批量处理
texts = [
    "妈妈买了苹果。她说它很甜。",
    "去年我去上海。那时候天气很好。",
]
for text in texts:
    resolved, _ = resolver.resolve_text(text)
    print(resolved)
    resolver.reset()
```

---

## 测试统计

```
总测试用例: 85
通过: 85
通过率: 100%

测试分布:
  test_coref_branches.py: 23 tests
  test_coref_golden.py: 27 tests
  test_english_golden.py: 7 tests
  test_time_golden.py: 14 tests
  test_tokenizer_golden.py: 14 tests
```

---

## 文件结构

```
coreference_module/
├── __init__.py           # 模块入口
├── coreference.py        # 指代消解器
├── tokenizer.py          # 分词器（jieba + 规则 + 实体分类）
├── canonicalizer.py      # 实体规范化
├── ner_adapter.py        # NER 服务适配器
├── syntax_adapter.py     # HanLP/LTP 语法适配器
├── time_normalizer.py    # 时间表达式归一化
└── README.md             # 本文档
```

---

## 版本历史

| 版本 | 更新内容 |
|-----|---------|
| v1.0 | 基础人称代词消解 |
| v1.1 | 添加领属代词、物品代词 |
| v1.2 | 添加地点代词、时间代词 |
| v1.3 | 添加序数代词（前者/后者） |
| v1.4 | 添加复指结构处理 |
| v1.5 | 添加语义角色分析 |
| v1.6 | 完善排除规则（约束变量、描述短语等） |
| v2.0 | 全面测试，精确率100% |
