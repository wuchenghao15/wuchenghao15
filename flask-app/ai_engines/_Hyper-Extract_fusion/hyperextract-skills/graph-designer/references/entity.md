# Entity Design Reference

Entity design patterns for graph types. See [SKILL.md](SKILL.md) for workflow.

---

## Basic Entity Fields

```yaml
entities:
  description: 'Node/entity definitions'
  fields:
    - name: name
      type: str
      description: 'Entity name (unique identifier)'
    - name: category
      type: str
      description: 'Entity type/category'
    - name: description
      type: str
      description: 'Brief description'
      required: false
      default: ''
```

---

## Multi-Type Nodes

If nodes can have multiple categories:

```yaml
    - name: category
      type: list
      description: 'Entity types (can be multiple)'
```

---

## Domain-Specific Fields

Add fields based on your domain:

```yaml
    - name: role
      type: str
      description: 'Role in current context'
      required: false
      default: ''
    - name: importance
      type: str
      description: 'Importance level: high, medium, low'
      required: false
      default: 'medium'
```

---

## Common Patterns

### Single Type Entities

```yaml
entities:
  description: 'Organization entities'
  fields:
    - name: name
      type: str
    - name: description
      type: str
      required: false
```

### Multi-Type Entities

```yaml
entities:
  description: 'Mixed entity types'
  fields:
    - name: name
      type: str
    - name: category
      type: str
    - name: description
      type: str
      required: false
```

### Typed Entities

```yaml
entities:
  description: 'Typed entities'
  fields:
    - name: name
      type: str
    - name: entity_type
      type: str
    - name: subtype
      type: str
      required: false
    - name: description
      type: str
      required: false
```

---

## Design Principles

1. **Name is primary**: Always include a name/identifier field
2. **Category helps**: Include category for multi-type graphs
3. **Description optional**: Add if entities need context
4. **Domain fields**: Add domain-specific attributes as needed
5. **Avoid redundancy**: Don't repeat information from relations
