# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-07

### Added

- **Core Coreference Resolution**
  - Support for 11 pronoun types: person, possessive, object, location, time, ordinal, event, formal deictic, ambiguous, generic, bound variable
  - Semantic role analysis for accurate antecedent selection
  - Entity tracking with person/object/location/time stacks
  - Reduplicative structure handling (冗余复指删除)

- **Non-Resolution Rules**
  - First/second person pronouns (我、你、您)
  - Reflexive pronouns (自己、本人)
  - Emphatic reflexives (他自己、她本人)
  - Generic pronouns (人家、别人、有人)
  - Bound variables (每个学生都带了他的书)
  - First sentence without antecedent

- **Stream Processing**
  - `StreamCorefSession` for real-time sentence-by-sentence resolution
  - State management with `reset()` method

- **Structured Output**
  - `resolve_text_structured()` returning `ResolvedText` dataclass
  - Includes resolved text, replacements, mentions, and time extractions

- **Time Normalization**
  - Relative time expressions (昨天、上周、去年)
  - Fuzzy time expressions (最近、以前)
  - Time period recognition (早上、下午)

- **NER Service**
  - Extract PER, LOC, OBJ, TIME entities
  - Position information for each entity

- **English Support**
  - Basic English coreference resolution module
  - He/she/they/it pronoun handling

- **Testing**
  - 85 pytest test cases
  - 100% pass rate
  - 100% branch coverage for `_find_replacement`

### Fixed

- Dead code in `_get_pronoun_type()` (unreachable `return 'OBJECT'`)
- Missing first-person plural possessives in `SELF_PRONOUNS` (`我们的`, `咱们的`)
- Redundant `import re` statements in `tokenizer.py`

### Changed

- Extracted scoring magic numbers to `_ScoreWeights` dataclass
- Improved exception handling in `syntax_adapter.py` with specific types + logging

---

## [Unreleased]

### Planned

- Phase 3: Refactor `_find_replacement()` (916 lines → modular handlers)
- Phase 4: Refactor `resolve_sentence()` (285 lines → cleaner structure)
- CI/CD with GitHub Actions
- PyPI package publication
