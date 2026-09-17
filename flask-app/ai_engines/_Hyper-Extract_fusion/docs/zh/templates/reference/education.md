# 教育模板

课程材料、教学大纲和培养方案分析。

---

## 概述

教育模板从教学文档中提取教学结构：从教材和讲义抽取知识点图，从教学大纲抽取课程—模块—考核超图。

当原文在讲授概念及其学习依赖时，使用 `education/course_concept_graph`。当原文把一门课组织成模块、主题、考核和学习成果时，使用 `education/curriculum_structure`。从论文或百科全书抽取通用本体时，请改用 `general/concept_graph`。

---

## 模板

### course_concept_graph

**类型**：graph

**用途**：从课程材料中提取知识点及其教学依赖关系

**最适合**：
- 教材和讲义
- 课程读本
- 教程章节

**实体**：
- 知识点（概念、技能、方法、原理、例题）

**关系**：
- `先修` — 文本明确写出的学习顺序要求
- `组成` — 文本明确写出的部分-整体关系
- `相关` — 排除先修和组成后仍明确陈述的关联
- `示例` — 作为某知识点的例题或实例

=== "CLI"

    ```bash
    he parse lecture.md -t education/course_concept_graph -l zh
    ```

=== "Python"

    ```python
    ka = Template.create("education/course_concept_graph", "zh")
    result = ka.parse(lecture_notes)

    for edge in result.data.relations:
        print(f"{edge.source} -[{edge.type}]-> {edge.target}")
    ```

---

### curriculum_structure

**类型**：hypergraph

**用途**：从教学大纲中提取课程—模块—知识点—考核结构

**最适合**：
- 教学大纲
- 培养方案
- 课程简介

**实体**：
- 课程
- 模块（周次、单元）
- 知识点（该单元覆盖的主题）
- 考核（测验、作业、实验、考试）
- 学习成果

**超边**：
- 一个教学单元（`unit_name`），按角色分组 `courses`、`concepts`、`assessments`、`outcomes`

=== "CLI"

    ```bash
    he parse syllabus.md -t education/curriculum_structure -l zh
    ```

=== "Python"

    ```python
    ka = Template.create("education/curriculum_structure", "zh")
    result = ka.parse(syllabus_text)

    for unit in result.data.relations:
        print(f"{unit.unit_name}: {unit.concepts} / {unit.assessments}")
    ```

---

## 提示

1. **course_concept_graph 用于教材** — 正文中明确写出的学习依赖
2. **curriculum_structure 用于大纲** — 课程组织与考核对应
3. 不要仅凭章节顺序臆造先修，也不要添加大纲未点名的考核

---

## 参见

- [模板概览](overview.md)
- [通用模板](general.md) — 非课程概念文本请用 `general/concept_graph`
