# Dimension Design Reference

Time and space dimension patterns. See [SKILL.md](SKILL.md) for workflow.

---

## Temporal Graph

### Add Time Field to Relations

```yaml
relations:
  fields:
    - name: source
      type: str
    - name: target
      type: str
    - name: relation_type
      type: str
    - name: event_date
      type: str
      description: 'When the relation occurred'
      required: false
      default: ''
```

### Configure Time Identifier

```yaml
identifiers:
  entity_id: name
  relation_id: '{source}|{relation_type}|{target}|{event_date}'
  relation_members:
    source: source
    target: target
  time_field: event_date
```

### Time Handling Rules

```yaml
guideline:
  rules_for_time:
    - 'Observation time: {observation_time}'
    - 'Absolute dates: Keep as-is (e.g., 2024-01-01)'
    - 'Relative time: Convert to absolute'
    - 'Fuzzy time: Leave empty, do not guess'
```

---

## Spatial Graph

### Add Location Field to Relations

```yaml
relations:
  fields:
    - name: source
      type: str
    - name: target
      type: str
    - name: relation_type
      type: str
    - name: location
      type: str
      description: 'Where the relation occurred'
      required: false
      default: ''
```

### Configure Location Identifier

```yaml
identifiers:
  entity_id: name
  relation_id: '{source}|{relation_type}|{target}|{location}'
  relation_members:
    source: source
    target: target
  location_field: location
```

### Location Handling Rules

```yaml
guideline:
  rules_for_location:
    - 'Observation location: {observation_location}'
    - 'Structured: Keep as-is (e.g., Beijing, China)'
    - 'Fuzzy: Use observation_location'
    - 'Coordinates: Keep as-is'
```

---

## Spatio-Temporal Graph

Combines both dimensions:

```yaml
relations:
  fields:
    - name: source
      type: str
    - name: target
      type: str
    - name: relation_type
      type: str
    - name: event_date
      type: str
    - name: location
      type: str

identifiers:
  time_field: event_date
  location_field: location
```

---

## Dimension Selection Checklist

### Time Dimension?

- [ ] Relation has temporal aspect?
- [ ] Same entities can have multiple relations at different times?
- [ ] Time is edge property, not node property?
- [ ] **If 3+ yes → temporal_graph**

### Location Dimension?

- [ ] Relation has spatial aspect?
- [ ] Same entities can have relations at different locations?
- [ ] Location is edge property, not node property?
- [ ] **If 3+ yes → spatial_graph**
