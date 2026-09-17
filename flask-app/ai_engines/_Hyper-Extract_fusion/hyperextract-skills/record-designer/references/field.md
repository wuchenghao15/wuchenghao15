# Field Design Reference

Field design patterns for record types. See [SKILL.md](SKILL.md) for workflow.

---

## Field Definition Template

```yaml
output:
  description: 'Output structure description'
  fields:
    - name: field_name        # snake_case, must be unique
      type: str/int/float/list # data type
      description: 'What this field captures'
      required: true/false     # is this mandatory?
      default: 'value'         # default when missing
```

---

## Field Type Guidelines

| Type | Use When | Example |
|------|----------|---------|
| str | Text values | names, descriptions |
| int | Whole numbers | counts, years |
| float | Decimal numbers | prices, percentages |
| list | Multiple values | tags, categories |

---

## Common Patterns

### Information Card

```yaml
output:
  fields:
    - name: title
      type: str
      required: true
    - name: category
      type: str
    - name: description
      type: str
    - name: tags
      type: list
      required: false
```

### Structured Record

```yaml
output:
  fields:
    - name: name
      type: str
    - name: status
      type: str
    - name: value
      type: float
    - name: notes
      type: str
      required: false
```

### Ordered List

```yaml
output:
  fields:
    - name: order
      type: int
    - name: item
      type: str
```

---

## Design Principles

1. **Clear Names**: Use snake_case, semantic names
2. **Appropriate Types**: Match data type to content
3. **Required vs Optional**: Only required if truly needed
4. **Safe Defaults**: Provide meaningful defaults
5. **Complete Descriptions**: Explain what field captures
