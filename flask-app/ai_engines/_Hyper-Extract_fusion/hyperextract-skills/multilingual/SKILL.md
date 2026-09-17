---
name: multilingual
description: |
  Convert Hyper-Extract YAML templates to multi-language support.
  Use when user says: "add translation", "multilingual", "convert language", "support Chinese and English".
  Trigger: User wants to add Chinese/English/Japanese translation to their template.
  Skip: User wants to design a new template (use record-designer or graph-designer instead).
---

# Multilingual Converter

## Translatable Fields

The following fields can be translated:

- description
- output.description
- fields[].description
- guideline.target
- guideline.rules

## Non-Translatable Fields

The following fields should NOT be translated:

- name, type, tags
- field names (name in fields)
- identifiers
- display

---

## Conversion Modes

### Mode 1: Single → Bilingual

```yaml
# Before (single language)
language: zh
description: '财务报告摘要'

# After (bilingual)
language: [zh, en]  # YAML list format
description:
  zh: '财务报告摘要'
  en: 'Financial Report Summary'
```

## Mode 2: Expand Existing Translation

```yaml
# Before (has zh only)
description:
  zh: '财务报告摘要'

# After (add en)
description:
  zh: '财务报告摘要'
  en: 'Financial Report Summary'
```

## Mode 3: Add New Language

```yaml
# Before (zh + en)
# After (add ja)
description:
  zh: '财务报告摘要'
  en: 'Financial Report Summary'
  ja: '財務報告サマリー'
```

## Translation Guidelines

### Field Descriptions

| Original | English | Notes |
|----------|---------|-------|
| 公司名称 | Company name | Direct |
| 营收金额 | Revenue amount | Direct |
| 关键词 | Keyword/Term | Choose based on context |

### Target/Rules

```yaml
target:
  zh: '你是一位财务分析师，请从财报中提取关键信息。'
  en: 'You are a financial analyst. Extract key information from financial reports.'

rules:
  zh:
    - '每个字段对应一个独立的信息项'
  en:
    - 'Each field corresponds to an independent information item'
```

### Multi-language Consistency

When translating field values (like enum options), maintain language purity:

| Original | Chinese Translation | English Translation |
|----------|-------------------|-------------------|
| `类型：实体/抽象` | `类型：实体/抽象` | `Type: entity/abstract` |
| `重要性：高/中/低` | `重要性：高/中/低` | `Significance: high/medium/low` |

Do NOT translate inline: `类型：entity(实体)` → wrong!

## Translation Checklist

- [ ] Preserve technical terms consistently
- [ ] Maintain same meaning across languages
- [ ] Keep field names in source language
- [ ] Update language field to indicate multi-language (use list format)

## Output Format

```yaml
## Multilingual Conversion Result

language: [zh, en]  # YAML list format

# All translatable fields now have both zh and en

## Translation Mapping

| Field Path | Chinese | English |
|------------|---------|---------|
| description | ... | ... |
| output.description | ... | ... |
| fields[].description | ... | ... |
| guideline.target | ... | ... |
| guideline.rules | ... | ... |
```

## Notes

- Use professional domain terminology
- Maintain consistent terminology across fields
- Keep YAML structure clean and readable
- Field names (name) should NOT be translated
- Use YAML list format for language field: `language: [zh, en]`
