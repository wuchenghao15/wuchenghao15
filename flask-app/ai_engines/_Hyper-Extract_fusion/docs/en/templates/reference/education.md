# Education Templates

Course materials, syllabi, and curriculum analysis.

---

## Overview

Education templates extract pedagogical structure from teaching documents: knowledge-point graphs from textbooks and lecture notes, and course–module–assessment hypergraphs from syllabi.

Use `education/course_concept_graph` when the source teaches concepts and their learning dependencies. Use `education/curriculum_structure` when the source organizes a course into modules, topics, assessments, and outcomes. For general ontology extraction from papers or encyclopedias, use `general/concept_graph` instead.

---

## Templates

### course_concept_graph

**Type**: graph

**Purpose**: Extract knowledge points and pedagogical dependencies from course materials

**Best for**:
- Textbooks and lecture notes
- Course readers
- Tutorial chapters

**Entities**:
- Knowledge points (concepts, skills, procedures, principles, examples)

**Relations**:
- `prerequisite_of` — Explicit learning-order requirement
- `part_of` — Explicit part-whole membership
- `related_to` — Explicit association that is not prerequisite or part-whole
- `example_of` — Worked example or illustration of a knowledge point

=== "CLI"

    ```bash
    he parse lecture.md -t education/course_concept_graph -l en
    ```

=== "Python"

    ```python
    ka = Template.create("education/course_concept_graph", "en")
    result = ka.parse(lecture_notes)

    for edge in result.data.relations:
        print(f"{edge.source} -[{edge.type}]-> {edge.target}")
    ```

---

### curriculum_structure

**Type**: hypergraph

**Purpose**: Extract course–module–concept–assessment structure from syllabi

**Best for**:
- Course syllabi
- Program / curriculum plans
- Course outlines

**Entities**:
- Courses
- Modules (weeks, units)
- Concepts (topics the unit covers)
- Assessments (quiz, homework, lab, exam)
- Learning outcomes

**Hyperedges**:
- One teaching unit (`unit_name`) grouping `courses`, `concepts`, `assessments`, and `outcomes`

=== "CLI"

    ```bash
    he parse syllabus.md -t education/curriculum_structure -l en
    ```

=== "Python"

    ```python
    ka = Template.create("education/curriculum_structure", "en")
    result = ka.parse(syllabus_text)

    for unit in result.data.relations:
        print(f"{unit.unit_name}: {unit.concepts} / {unit.assessments}")
    ```

---

## Tips

1. **course_concept_graph for textbooks** — Learning dependencies stated in the prose
2. **curriculum_structure for syllabi** — Course organization and assessment mapping
3. Do not invent prerequisites from chapter order, or assessments the syllabus does not name

---

## See Also

- [Template Overview](overview.md)
- [General Templates](general.md) — `general/concept_graph` for non-course conceptual text
