"""Integration tests for the persist_memory_nodes storage API.

Covers: basic insertion, empty input, custom edges, nested relationships,
triplet embedding, batch operations, bidirectional links, and error handling.
"""

import pathlib

import pytest
import pytest_asyncio

import m_flow
from m_flow.low_level import setup
from m_flow.core import MemoryNode
from m_flow.storage.add_memory_nodes import persist_memory_nodes
from m_flow.storage.exceptions import InvalidMemoryNodesInAddMemoryNodesError
from m_flow.adapters.graph import get_graph_provider

STORAGE_SUBDIR = "test_add_memory_nodes_integration"
ROOT = pathlib.Path(__file__).resolve().parents[3]


class Individual(MemoryNode):
    """A person entity used in graph integration tests."""

    label: str
    years: int
    metadata: dict = {"index_fields": ["label"]}


class Organisation(MemoryNode):
    """A corporate entity with sector information."""

    label: str
    sector: str
    metadata: dict = {"index_fields": ["label", "sector"]}


@pytest_asyncio.fixture
async def prepared_env():
    """Provision a clean system/data directory pair, tear down after test."""
    sys_path = str(ROOT / f".mflow/system/{STORAGE_SUBDIR}")
    dat_path = str(ROOT / f".data_storage/{STORAGE_SUBDIR}")

    m_flow.config.system_root_directory(sys_path)
    m_flow.config.data_root_directory(dat_path)

    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)
    await setup()

    yield

    try:
        await m_flow.prune.prune_data()
        await m_flow.prune.prune_system(metadata=True)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_memory_node_lifecycle(prepared_env):
    """End-to-end lifecycle test covering all persist_memory_nodes code-paths."""

    ind_alpha = Individual(label="Hana", years=28)
    ind_beta = Individual(label="Riku", years=34)
    inserted = await persist_memory_nodes([ind_alpha, ind_beta])

    assert inserted == [ind_alpha, ind_beta]
    assert len(inserted) == 2

    gengine = await get_graph_provider()
    g_nodes, g_edges = await gengine.get_graph_data()
    assert len(g_nodes) >= 2

    empty_result = await persist_memory_nodes([])
    assert empty_result == []

    ind_gamma = Individual(label="Yuki", years=41)
    ind_delta = Individual(label="Sota", years=26)
    link_spec = (
        str(ind_gamma.id),
        str(ind_delta.id),
        "knows",
        {"edge_text": "friends with"},
    )

    with_links = await persist_memory_nodes([ind_gamma, ind_delta], custom_edges=[link_spec])
    assert len(with_links) == 2

    g_nodes, g_edges = await gengine.get_graph_data()
    assert len(g_edges) == 1
    assert len(g_nodes) == 4

    class Staff(MemoryNode):
        label: str
        employer: Organisation
        metadata: dict = {"index_fields": ["label"]}

    org = Organisation(label="NovaSoft", sector="SaaS")
    staff_member = Staff(label="Mei", employer=org)

    nested_out = await persist_memory_nodes([staff_member])
    assert len(nested_out) == 1

    g_nodes, g_edges = await gengine.get_graph_data()
    assert len(g_nodes) == 6
    assert len(g_edges) == 2

    ind_eps = Individual(label="Kai", years=37)
    ind_zeta = Individual(label="Aoi", years=29)
    triplet_link = (
        str(ind_eps.id),
        str(ind_zeta.id),
        "married_to",
        {"edge_text": "is married to"},
    )

    triplet_out = await persist_memory_nodes([ind_eps, ind_zeta], custom_edges=[triplet_link], embed_triplets=True)
    assert len(triplet_out) == 2

    g_nodes, g_edges = await gengine.get_graph_data()
    assert len(g_nodes) == 8
    assert len(g_edges) == 3

    wave_a = [Individual(label="Ren", years=22), Individual(label="Saki", years=31)]
    wave_b = [Individual(label="Taro", years=45), Individual(label="Nao", years=39)]

    out_a = await persist_memory_nodes(wave_a)
    out_b = await persist_memory_nodes(wave_b)

    assert len(out_a) == 2
    assert len(out_b) == 2

    g_nodes, g_edges = await gengine.get_graph_data()
    assert len(g_nodes) == 12
    assert len(g_edges) == 3

    ind_eta = Individual(label="Jun", years=33)
    ind_theta = Individual(label="Mio", years=27)
    fwd = (str(ind_eta.id), str(ind_theta.id), "colleague_of", {"edge_text": "works with"})
    rev = (str(ind_theta.id), str(ind_eta.id), "colleague_of", {"edge_text": "works with"})

    bidir_out = await persist_memory_nodes([ind_eta, ind_theta], custom_edges=[fwd, rev])
    assert len(bidir_out) == 2

    g_nodes, g_edges = await gengine.get_graph_data()
    assert len(g_nodes) == 14
    assert len(g_edges) == 5

    bad_node = Individual(label="BadInput", years=99)
    with pytest.raises(InvalidMemoryNodesInAddMemoryNodesError, match="must be a list"):
        await persist_memory_nodes(bad_node)

    with pytest.raises(InvalidMemoryNodesInAddMemoryNodesError, match="must be a MemoryNode"):
        await persist_memory_nodes(["not", "datapoints"])

    closing_nodes, closing_edges = await gengine.get_graph_data()
    assert len(closing_nodes) == 14
    assert len(closing_edges) == 5
