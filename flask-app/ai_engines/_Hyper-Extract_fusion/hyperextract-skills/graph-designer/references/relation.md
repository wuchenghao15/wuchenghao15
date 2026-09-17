# Relation Design Reference

Relation design patterns for graph types. See [SKILL.md](SKILL.md) for workflow.

---

## Binary Relations

### Basic Structure

```yaml
relations:
  description: 'Edge/relation definitions'
  fields:
    - name: source
      type: str
      description: 'Source entity name'
    - name: target
      type: str
      description: 'Target entity name'
    - name: relation_type
      type: str
      description: 'Type of relationship'
```

### With Properties

```yaml
relations:
  fields:
    - name: source
      type: str
    - name: target
      type: str
    - name: relation_type
      type: str
    - name: strength
      type: str
      required: false
    - name: description
      type: str
      required: false
```

---

## Common Relation Types

| Category | Types |
|----------|-------|
| Social | owns, works_for, married_to, parent_of, sibling_of |
| Organizational | subsidiary_of, competitor_of, partner_with, acquired_by |
| Causal | causes, enables, prevents, leads_to, results_in |
| Spatial | located_at, adjacent_to, part_of, contains |
| Temporal | preceded_by, followed_by, concurrent_with, overlaps |
| Dependency | depends_on, requires, imports, exports |

---

## Identifier Configuration

### Binary Relations

```yaml
identifiers:
  entity_id: name
  relation_id: '{source}|{relation_type}|{target}'
  relation_members:
    source: source
    target: target
```

### Identifier Template Syntax

- `{field_name}`: Insert field value
- `{source}`: Source entity name
- `{relation_type}`: Relation type
- `{target}`: Target entity name

---

## Design Principles

1. **Source and Target**: Required for binary relations
2. **Relation Type**: Use predefined or custom types
3. **Properties**: Add optional fields for edge attributes
4. **Clear Names**: Use semantic relation type names
5. **Consistency**: Keep relation types consistent
