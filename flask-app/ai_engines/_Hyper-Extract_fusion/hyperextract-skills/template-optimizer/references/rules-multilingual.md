# Multi-language Consistency Rules

Ensure language purity in bilingual templates.

---

## Core Principle

**Each language field should use that language's own terminology.**

| Field | Rule | Example |
|-------|------|---------|
| `zh` | Pure Chinese | `类型：实体` |
| `en` | Pure English | `Type: entity` |

---

## Common Issues

### Issue 1: Mixed Language in zh

```
❌ Wrong
zh: '类型：entity(实体)/abstract(抽象概念)'
en: 'Type: entity/abstract'

✅ Correct
zh: '类型：实体/抽象概念'
en: 'Type: entity/abstract'
```

**Pattern to detect**: `[a-zA-Z]+\([^)]+\)` in zh fields

### Issue 2: Mixed Language in en

```
❌ Wrong
zh: '类型：实体/抽象'
en: 'Type: 实体/抽象'

✅ Correct
zh: '类型：实体/抽象'
en: 'Type: entity/abstract'
```

**Pattern to detect**: `[\u4e00-\u9fa5]+` in en fields

---

## Auto-fix Rules

1. **Remove English terms from zh**: Extract `entity(...)` → `实体`
2. **Remove Chinese chars from en**: Translate to English equivalents

---

## Translation Patterns

When translating enum values:

| Original (zh) | English (en) |
|--------------|--------------|
| 实体 | entity |
| 抽象概念 | abstract |
| 过程 | process |
| 关系 | relation |
| 高/中/低 | high/medium/low |
| 人物/事件/地点 | person/event/location |

---

## Special Cases

### Field Names vs Field Values

```
# Field names can be in English (they're identifiers)
name: type
description:
  zh: '类型'
  en: 'Type'

# Field values should match language
description:
  zh: '类型：实体'  # zh values in Chinese
  en: 'Type: entity'  # en values in English
```
