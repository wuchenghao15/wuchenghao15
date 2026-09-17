"""M-Flow low-level pipeline demo — structured graph ingestion."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, List, Mapping

from m_flow import config, prune, search, RecallMode, visualize_graph
from m_flow.low_level import setup, MemoryNode
from m_flow.pipelines import run_tasks, Task
from m_flow.storage import persist_memory_nodes
from m_flow.storage.index_relations import index_relations
from m_flow.auth.methods import get_seed_user
from m_flow.data.methods import load_or_create_datasets


class Person(MemoryNode):
    name: str
    metadata: dict = {"index_fields": ["name"]}


class Department(MemoryNode):
    name: str
    employees: list[Person]
    metadata: dict = {"index_fields": ["name"]}


class OrgCategory(MemoryNode):
    name: str = "Company"


class Company(MemoryNode):
    name: str
    departments: list[Department]
    is_type: OrgCategory
    metadata: dict = {"index_fields": ["name"]}


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "data"
SYSTEM_DIR = BASE_DIR / ".mflow/system"
OUTPUT_DIR = BASE_DIR / ".artifacts"
GRAPH_OUTPUT = OUTPUT_DIR / "graph_visualization.html"
COMPANIES_FILE = DATA_PATH / "companies.json"
PEOPLE_FILE = DATA_PATH / "people.json"


def _read_json(filepath: Path) -> Any:
    if not filepath.exists():
        raise FileNotFoundError(f"Required data file not found: {filepath}")
    return json.loads(filepath.read_text(encoding="utf-8"))


def _deduplicate(items: Iterable[Any]) -> list[Any]:
    visited: set = set()
    result: list[Any] = []
    for item in items:
        if item not in visited:
            visited.add(item)
            result.append(item)
    return result


def _extract_people(records: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [p for rec in records for p in rec.get("people", [])]


def _extract_companies(records: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [c for rec in records for c in rec.get("companies", [])]


def _create_person_nodes(people: Iterable[Mapping[str, Any]]) -> dict[str, Person]:
    return {p["name"]: Person(name=p["name"]) for p in people if p.get("name")}


def _group_by_department(people: Iterable[Mapping[str, Any]]) -> dict[str, list[str]]:
    dept_map: dict[str, list[str]] = defaultdict(list)
    for person in people:
        person_name = person.get("name")
        if not person_name:
            continue
        dept_map[person.get("department", "Unknown")].append(person_name)
    return dept_map


def _gather_department_names(
    dept_groups: Mapping[str, list[str]],
    companies: Iterable[Mapping[str, Any]],
) -> set[str]:
    all_names = set(dept_groups)
    for company in companies:
        for d in company.get("departments", []):
            all_names.add(d)
    return all_names


def _create_department_nodes(names: Iterable[str]) -> dict[str, Department]:
    return {n: Department(name=n, employees=[]) for n in names}


def _create_company_nodes(
    companies: Iterable[Mapping[str, Any]],
    category: OrgCategory,
) -> dict[str, Company]:
    return {c["name"]: Company(name=c["name"], departments=[], is_type=category) for c in companies if c.get("name")}


def _link_departments(
    raw_companies: Iterable[Mapping[str, Any]],
    dept_nodes: Mapping[str, Department],
    company_nodes: Mapping[str, Company],
) -> None:
    for cn in company_nodes:
        company_nodes[cn].departments = []
    for company in raw_companies:
        cn = company.get("name")
        if not cn:
            continue
        for dn in company.get("departments", []):
            dept = dept_nodes.get(dn)
            comp = company_nodes.get(cn)
            if dept and comp:
                comp.departments.append(dept)


def _link_employees(
    dept_groups: Mapping[str, list[str]],
    person_nodes: Mapping[str, Person],
    dept_nodes: Mapping[str, Department],
) -> None:
    for dept in dept_nodes.values():
        dept.employees = []
    for dept_name, member_names in dept_groups.items():
        target = dept_nodes.get(dept_name)
        if not target:
            continue
        target.employees = [person_nodes[n] for n in _deduplicate(member_names) if n in person_nodes]


def assemble_companies(records: Iterable[Mapping[str, Any]]) -> list[Company]:
    people_raw = _extract_people(records)
    companies_raw = _extract_companies(records)
    person_nodes = _create_person_nodes(people_raw)
    dept_groups = _group_by_department(people_raw)
    dept_names = _gather_department_names(dept_groups, companies_raw)
    dept_nodes = _create_department_nodes(dept_names)
    org_cat = OrgCategory()
    company_nodes = _create_company_nodes(companies_raw, org_cat)
    _link_departments(companies_raw, dept_nodes, company_nodes)
    _link_employees(dept_groups, person_nodes, dept_nodes)
    return list(company_nodes.values())


def _load_default_records() -> list[Mapping[str, Any]]:
    return [{"companies": _read_json(COMPANIES_FILE), "people": _read_json(PEOPLE_FILE)}]


def ingest_payloads(data: List[Any] | None) -> list[Company]:
    if not data or data == [None]:
        data = _load_default_records()
    return assemble_companies(data)


async def execute_workflow() -> None:
    logging.info("Initializing M-Flow system directory: %s", SYSTEM_DIR)
    config.system_root_directory(str(SYSTEM_DIR))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    await prune.prune_system(metadata=True)
    await setup()

    user = await get_seed_user()
    datasets = await load_or_create_datasets(["demo_dataset"], [], user)
    ds_id = datasets[0].id

    task_chain = [Task(ingest_payloads), Task(persist_memory_nodes)]
    pipeline = run_tasks(tasks=task_chain, dataset_id=ds_id, user=user, workflow_name="demo_pipeline")
    async for step_status in pipeline:
        logging.info("Pipeline step: %s", step_status)

    await index_relations()
    await visualize_graph(str(GRAPH_OUTPUT))

    result = await search(
        query_text="Who works for GreenFuture Solutions?",
        query_type=RecallMode.TRIPLET_COMPLETION,
    )
    logging.info("Query result: %s", result)


def _init_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


async def main() -> None:
    _init_logging()
    try:
        await execute_workflow()
    except Exception:
        logging.exception("Pipeline execution failed")
        raise


if __name__ == "__main__":
    asyncio.run(main())
