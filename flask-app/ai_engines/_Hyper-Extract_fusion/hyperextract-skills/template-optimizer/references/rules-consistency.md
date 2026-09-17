# Schema vs Guideline Consistency

Separation of concerns between schema definition and extraction guidelines.

---

## Core Principle

| Schema (output) | Guideline (rules) |
|-----------------|------------------|
| Defines WHAT | Defines HOW TO DO WELL |
| Field structure | Extraction strategy |
| Type definitions | Quality requirements |
| Descriptions | Common mistakes |

---

## What Belongs Where

### Schema (output)

```yaml
output:
  entities:
    fields:
      - name: name
        type: str
        description: 'Person name'  # What it is
        required: true
```

### Guideline (rules)

```yaml
guideline:
  rules_for_entities:
    - 'Extract full names as they appear in text'
    - 'Maintain naming consistency throughout document'
    - 'Only extract named persons, not pronouns'
```

---

## Common Mistakes

### ❌ Repeating Schema in Guideline

```yaml
# Wrong - repeats schema
guideline:
  rules_for_entities:
    - 'Extract name field as entity name'
    - 'Extract type field as entity category'
```

## ✅ Guideline Focuses on Extraction

```yaml
# Correct - explains how to extract
guideline:
  rules_for_entities:
    - 'Extract full names as they appear'
    - 'Categorize based on context clues'
```

---

## Checklist

| Check | Guideline Should | Guideline Should NOT |
|-------|-----------------|---------------------|
| Field names | Extraction strategy | "name should be..." |
| Field types | Quality requirements | "type field is..." |
| Required/optional | Creation conditions | "required: true" |
| Descriptions | Common mistakes | Schema definitions |

---

## Examples

### Model Template

```yaml
# Schema
output:
  fields:
    - name: company_name
      type: str
      description: 'Company name'

# Guideline
guideline:
  rules:
    - 'Extract official company names'
    - 'Use abbreviations if that's how they appear'
    - 'Standardize formats like "Inc.", "Ltd."'
```

## Graph Template

```yaml
# Schema
relations:
  fields:
    - name: type
      description: 'Relationship type'

# Guideline
rules_for_relations:
    - 'Use verbs or prepositions to describe relations'
    - 'Match terminology from source text'
    - 'Keep relation types consistent'
```

---

## Detection

Flag for review when guideline contains:
- Field definitions from schema
- "should be" or "must be" referencing schema fields
- Repetition of `description` content
