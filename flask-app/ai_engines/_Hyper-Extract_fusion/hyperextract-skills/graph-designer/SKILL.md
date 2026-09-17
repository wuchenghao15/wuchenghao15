---
name: graph-designer
description: |
  Design YAML extraction templates for graph types (graph, hypergraph, temporal_graph, spatial_graph).
  Use when user says: "design graph", "create knowledge graph", "extract relationships", "temporal data", "spatial data".
  Trigger: User wants to extract entity relationships, multi-party events, or time/location-based data.
  Skip: User wants simple record extraction (use record-designer instead).
---

# Graph Designer: graph/hypergraph/temporal/spatial

## Input from Brainstorm

Receive design specs from brainstorm:
- Entity types and fields
- Relation types and fields
- Hypergraph grouping strategy
- Time/location requirements

## Workflow

1. **Confirm type** based on brainstorm specs
2. **Design entities** (output.entities)
3. **Design relations** (output.relations)
4. **Configure identifiers** (identifiers)
5. **Set display** (display)
6. **Write guideline** (guideline)
7. **Review and output YAML**

## Critical: Output vs Guideline

**Key Principle**: Schema defines "WHAT", Guideline defines "HOW TO DO WELL". DO NOT repeat schema definitions in guideline.

| Guideline Should Have | Guideline Should NOT Have |
|-----------------------|-------------------------|
| Extraction strategy ("extract valuable entities") | Field definitions ("name should be...") |
| Quality requirements ("maintain naming consistency") | Type descriptions ("type field is...") |
| Creation conditions ("only when text explicitly states") | Reference requirements ("must reference name field") |
| Common mistakes to avoid | Schema field descriptions |

## Type Confirmation

| Type | relation_members | Additional Config |
|------|-----------------|-------------------|
| graph | `{source, target}` | - |
| hypergraph (simple) | `participants` (string) | - |
| hypergraph (nested) | `[group_a, group_b]` (list) | - |
| temporal_graph | + type | `time_field` |
| spatial_graph | + type | `location_field` |
| spatio_temporal | + both | `time_field` + `location_field` |

## Output Template

```yaml
language: en

name: [TemplateName]
type: [type]
tags: [...]
description: '...'

output:
  entities:
    description: '...'
    fields:
      - name: name
        type: str
      - name: category
        type: str
  relations:
    description: '...'
    fields:
      # Type-specific fields

guideline:
  target: 'You are a [domain] expert...'
  rules_for_entities: [...]
  rules_for_relations: [...]

identifiers:
  entity_id: name
  relation_id: '...'
  relation_members: ...

display:
  entity_label: '{name} ({category})'
  relation_label: '...'
```

## Display Design Principles

**Important**: display.label is used for graph visualization. Edges connect two nodes (source/target), so the edge label should NOT repeat this information.

### Design Principles

| Principle | entity_label | relation_label |
|-----------|--------------|----------------|
| Node | Show core identifier | - |
| Edge | - | Show relation type + optional dimensions |
| Spatio-temporal | - | Show relation type + location + time |

### Recommended relation_label by Type

| Type | relation_label | Example |
|------|----------------|---------|
| graph | `{relation_type}` | `owns` |
| hypergraph | `{event_name}` or `{outcome}` | `Battle of Red Cliffs` |
| spatio_temporal_graph | `{relation_type}@{location}({event_date})` | `meets@Beijing(1985)` |

### Length Reference

- entity_label: Recommended 5-20 characters
- relation_label: Recommended 10-30 characters

## Quick Config Reference

### Binary Relations (graph)

```yaml
identifiers:
  relation_members:
    source: source
    target: target
```

### Hypergraph Simple

```yaml
identifiers:
  relation_members: participants  # STRING
```

### Hypergraph Nested

```yaml
identifiers:
  relation_members: [group_a, group_b]  # LIST
```

### Temporal

```yaml
identifiers:
  time_field: event_date
```

### Spatial

```yaml
identifiers:
  location_field: location
```

## Cases by Type

**Important**: Load only the case matching user's selected type.

| Type | Case File |
|------|-----------|
| graph | [cases/corporate-ownership.yaml](cases/corporate-ownership.yaml) |
| hypergraph | [cases/battle-analysis.yaml](cases/battle-analysis.yaml) |
| spatio_temporal_graph | [cases/biography-events.yaml](cases/biography-events.yaml) |

## Reference Files

**Important**: Check these files only when needed for the specific design task.

| Topic | When to Check |
|-------|--------------|
| [references/entity.md](references/entity.md) | When designing output.entities |
| [references/relation.md](references/relation.md) | When designing output.relations |
| [references/hypergraph.md](references/hypergraph.md) | For hypergraph type only |
| [references/dimensions.md](references/dimensions.md) | For temporal_graph/spatial_graph types |

---

## Design Checklist

### Entities
- [ ] Entity types cover key concepts?
- [ ] Entity granularity appropriate?
- [ ] Multi-type nodes handled?
- [ ] No redundant fields?

### Relations
- [ ] Relation types semantically clear?
- [ ] source/target reference entities?
- [ ] No ambiguous relations?

### Guideline (Must Check)
- [ ] No field definitions repeated from schema?
- [ ] Extraction strategy defined?
- [ ] Quality requirements specified (naming consistency)?
- [ ] Creation conditions clear ("only when text explicitly states")?
- [ ] Common mistakes warned?

### Hypergraph
- [ ] Participant count reasonable?
- [ ] Grouping strategy clear?
- [ ] Outcome defined?

### Identifiers
- [ ] entity_id references name field?
- [ ] relation_id template correct?
- [ ] relation_members configured?
- [ ] time/location_field specified?

### Multi-language
- [ ] `zh` descriptions use pure Chinese (no English terms like `entity(...)`)
- [ ] `en` descriptions use pure English (no Chinese characters)

### Entity-Relation Consistency
- [ ] source/target types match entities definition

### Relation Type Design
For **generic templates**: Use open-ended description
```yaml
en: 'Relation type, concisely describing the connection between entities'
```

For **domain-specific templates**: Can use predefined types
```yaml
en: 'Relation type: type_a/type_b/type_c'
```
