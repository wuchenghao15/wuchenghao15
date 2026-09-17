from __future__ import annotations

from pathlib import Path

import pytest

from axon.core.ingestion.pipeline import PipelineResult, run_pipeline
from axon.core.storage.kuzu_backend import KuzuBackend
from axon.mcp.tools import handle_context, handle_dead_code, handle_impact, handle_query


@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    """Create a multi-language sample repository.

    Layout::

        sample_repo/
        +-- src/
        |   +-- models.py      User class with __init__, to_dict method
        |   +-- auth.py         validate(user: User) -> bool, imports User, calls check
        |   +-- check.py        check() function, calls verify()
        |   +-- verify.py       verify() -- leaf function
        |   +-- unused.py       orphan_func() -- dead code
        |   +-- types.py        UserID type alias
        +-- lib/
            +-- handler.ts      exported handler function, calls process
            +-- process.ts      process function
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    src = repo / "src"
    src.mkdir()

    (src / "models.py").write_text(
        "class User:\n"
        "    def __init__(self, name: str):\n"
        "        self.name = name\n"
        "\n"
        "    def to_dict(self) -> dict:\n"
        "        return {'name': self.name}\n",
        encoding="utf-8",
    )

    (src / "auth.py").write_text(
        "from .models import User\n"
        "from .check import check\n"
        "\n"
        "def validate(user: User) -> bool:\n"
        "    return check(user)\n",
        encoding="utf-8",
    )

    (src / "check.py").write_text(
        "from .verify import verify\n"
        "\n"
        "def check(obj) -> bool:\n"
        "    return verify(obj)\n",
        encoding="utf-8",
    )

    (src / "verify.py").write_text(
        "def verify(obj) -> bool:\n"
        "    return obj is not None\n",
        encoding="utf-8",
    )

    (src / "unused.py").write_text(
        "def orphan_func():\n"
        "    pass\n",
        encoding="utf-8",
    )

    (src / "types.py").write_text(
        "UserID = str\n",
        encoding="utf-8",
    )

    lib = repo / "lib"
    lib.mkdir()

    (lib / "handler.ts").write_text(
        "import { process } from './process';\n"
        "\n"
        "export function handler(req: Request): Response {\n"
        "    return process(req);\n"
        "}\n",
        encoding="utf-8",
    )

    (lib / "process.ts").write_text(
        "export function process(req: Request): Response {\n"
        "    return new Response('ok');\n"
        "}\n",
        encoding="utf-8",
    )

    return repo


@pytest.fixture()
def storage(tmp_path: Path) -> KuzuBackend:
    """Provide an initialised KuzuBackend."""
    db_path = tmp_path / "e2e_db"
    backend = KuzuBackend()
    backend.initialize(db_path)
    yield backend
    backend.close()


@pytest.fixture()
def pipeline_result(
    sample_repo: Path, storage: KuzuBackend
) -> PipelineResult:
    """Run the full pipeline once and return the result."""
    _, result = run_pipeline(sample_repo, storage)
    return result


class TestFileCount:
    def test_discovers_all_files(self, pipeline_result: PipelineResult) -> None:
        # 6 Python files + 2 TypeScript files = 8
        assert pipeline_result.files == 8


class TestSymbolCount:
    def test_minimum_symbols(self, pipeline_result: PipelineResult) -> None:
        # Python: User, __init__, to_dict, validate, check, verify, orphan_func
        # TS: handler, process
        # (UserID = str isn't parsed as a type alias by tree-sitter for Python <3.12)
        assert pipeline_result.symbols >= 9


class TestRelationshipTypes:
    def test_relationships_exist(self, pipeline_result: PipelineResult) -> None:
        assert pipeline_result.relationships > 0

    def test_contains_and_defines(
        self, sample_repo: Path, storage: KuzuBackend, pipeline_result: PipelineResult
    ) -> None:
        # CONTAINS: folder -> file
        rows = storage.execute_raw(
            "MATCH ()-[r:CodeRelation]->() "
            "WHERE r.rel_type = 'contains' "
            "RETURN count(r)"
        )
        assert rows[0][0] > 0

    def test_defines_exist(
        self, sample_repo: Path, storage: KuzuBackend, pipeline_result: PipelineResult
    ) -> None:
        rows = storage.execute_raw(
            "MATCH ()-[r:CodeRelation]->() "
            "WHERE r.rel_type = 'defines' "
            "RETURN count(r)"
        )
        assert rows[0][0] > 0

    def test_imports_exist(
        self, sample_repo: Path, storage: KuzuBackend, pipeline_result: PipelineResult
    ) -> None:
        rows = storage.execute_raw(
            "MATCH ()-[r:CodeRelation]->() "
            "WHERE r.rel_type = 'imports' "
            "RETURN count(r)"
        )
        assert rows[0][0] > 0

    def test_calls_exist(
        self, sample_repo: Path, storage: KuzuBackend, pipeline_result: PipelineResult
    ) -> None:
        rows = storage.execute_raw(
            "MATCH ()-[r:CodeRelation]->() "
            "WHERE r.rel_type = 'calls' "
            "RETURN count(r)"
        )
        assert rows[0][0] > 0


class TestDeadCode:
    def test_dead_code_detected(self, pipeline_result: PipelineResult) -> None:
        assert pipeline_result.dead_code >= 1

    def test_orphan_flagged(
        self, sample_repo: Path, storage: KuzuBackend, pipeline_result: PipelineResult
    ) -> None:
        node = storage.get_node("function:src/unused.py:orphan_func")
        assert node is not None
        assert node.is_dead is True


class TestFTSSearch:
    def test_search_validate(
        self, sample_repo: Path, storage: KuzuBackend, pipeline_result: PipelineResult
    ) -> None:
        results = storage.fts_search("validate", limit=5)
        assert len(results) > 0
        names = [r.node_name for r in results]
        assert "validate" in names

    def test_search_handler(
        self, sample_repo: Path, storage: KuzuBackend, pipeline_result: PipelineResult
    ) -> None:
        results = storage.fts_search("handler", limit=5)
        assert len(results) > 0
        names = [r.node_name for r in results]
        assert "handler" in names


class TestMCPContext:
    def test_context_validate(
        self, sample_repo: Path, storage: KuzuBackend, pipeline_result: PipelineResult
    ) -> None:
        result = handle_context(storage, "validate")

        assert "validate" in result.lower()
        # validate calls check, so callees should include check
        assert "check" in result.lower()

    def test_context_check(
        self, sample_repo: Path, storage: KuzuBackend, pipeline_result: PipelineResult
    ) -> None:
        result = handle_context(storage, "check")

        assert "check" in result.lower()


class TestMCPImpact:
    def test_impact_verify(
        self, sample_repo: Path, storage: KuzuBackend, pipeline_result: PipelineResult
    ) -> None:
        result = handle_impact(storage, "verify")

        # verify is called by check, which is called by validate
        # So the impact traversal should find downstream symbols
        assert "verify" in result.lower()


class TestMCPQuery:
    def test_query_user(
        self, sample_repo: Path, storage: KuzuBackend, pipeline_result: PipelineResult
    ) -> None:
        result = handle_query(storage, "User")
        assert "User" in result


class TestMCPDeadCode:
    def test_dead_code_tool(
        self, sample_repo: Path, storage: KuzuBackend, pipeline_result: PipelineResult
    ) -> None:
        result = handle_dead_code(storage)
        assert "orphan_func" in result


class TestIdempotency:
    def test_idempotent(
        self, sample_repo: Path, storage: KuzuBackend
    ) -> None:
        _, result1 = run_pipeline(sample_repo, storage)
        fn_count_after_run1 = storage.execute_raw("MATCH (n:Function) RETURN count(n)")[0][0]

        _, result2 = run_pipeline(sample_repo, storage)
        fn_count_after_run2 = storage.execute_raw("MATCH (n:Function) RETURN count(n)")[0][0]

        assert result1.files == result2.files
        assert result1.symbols == result2.symbols
        assert result1.relationships == result2.relationships
        assert result1.dead_code == result2.dead_code

        # DB-level check: running the pipeline twice must not duplicate Function nodes.
        assert fn_count_after_run2 == fn_count_after_run1
