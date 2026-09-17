"""Contract tests for every name in the method registry.

Each registered method must construct via Template.create, record
``metadata["template"]``, and dump/load. Search shape is checked when an
empty KA can actually search; otherwise the case is xfailed (strict=False).
"""

import pytest

from hyperextract.methods.registry import list_methods
from hyperextract.utils.template_engine import Template

METHOD_NAMES = sorted(list_methods())

# Extra constructor kwargs some methods need beyond llm/embedder.
METHOD_CREATE_KWARGS: dict[str, dict] = {
    "atom": {"observation_time": "2024-06-15"},
}


def _create(name: str, llm_client, embedder):
    return Template.create(
        f"method/{name}",
        llm_client=llm_client,
        embedder=embedder,
        **METHOD_CREATE_KWARGS.get(name, {}),
    )


@pytest.mark.parametrize("name", METHOD_NAMES)
def test_create_sets_template_metadata(name, llm_client, embedder):
    instance = _create(name, llm_client, embedder)
    assert instance.metadata["template"] == f"method/{name}"


@pytest.mark.parametrize("name", METHOD_NAMES)
def test_dump_then_load(name, llm_client, embedder, tmp_path):
    instance = _create(name, llm_client, embedder)
    dest = tmp_path / name
    instance.dump(dest)
    instance.load(dest)


@pytest.mark.parametrize("name", METHOD_NAMES)
def test_search_shape(name, llm_client, embedder):
    instance = _create(name, llm_client, embedder)
    if not callable(getattr(instance, "search", None)):
        pytest.skip("no search")
    try:
        result = instance.search("query")
    except TypeError:
        try:
            result = instance.search("query", top_k=1)
        except ValueError as exc:
            pytest.xfail(reason=f"search not runnable on empty KA: {exc}")
    except ValueError as exc:
        pytest.xfail(reason=f"search not runnable on empty KA: {exc}")

    autotype = list_methods()[name]["type"]
    if autotype == "document":
        assert isinstance(result, list)
        return
    if name == "graph_rag":
        assert isinstance(result, tuple) and len(result) == 3
        return
    if name == "cog_rag":
        assert isinstance(result, dict)
        assert "themes" in result and "entities" in result
        return
    assert isinstance(result, tuple), f"{name} search returned {type(result)}"
    assert len(result) == 2
