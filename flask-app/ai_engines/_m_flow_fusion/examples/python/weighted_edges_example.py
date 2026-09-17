"""Demonstrate weighted edges between MemoryNode instances."""

import asyncio
from typing import Any
from pydantic import SkipValidation
from m_flow.api.v1.visualize.visualize import visualize_graph
from m_flow.core import MemoryNode
from m_flow.core.models.Edge import Edge
from m_flow.storage import persist_memory_nodes
import m_flow


# --- Domain: Music library with weighted relationships ---


class Song(MemoryNode):
    title: str
    genre: str


class Playlist(MemoryNode):
    name: str
    tracks: list[Song]


class Listener(MemoryNode):
    name: str
    favorites: SkipValidation[Any]  # (Edge, list[Song]) with play_count weight
    playlists: SkipValidation[Any]  # (Edge, list[Playlist])
    follows: SkipValidation[Any]  # (Edge, list["Listener"])


async def run():
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # Songs
    bohemian = Song(title="Bohemian Rhapsody", genre="Rock")
    imagine = Song(title="Imagine", genre="Pop")
    clair = Song(title="Clair de Lune", genre="Classical")
    billie = Song(title="Billie Jean", genre="Pop")

    # Playlists
    rock_mix = Playlist(name="Rock Classics", tracks=[bohemian])
    chill = Playlist(name="Chill Vibes", tracks=[imagine, clair])

    # Listeners with weighted edges
    alice = Listener(
        name="Alice",
        favorites=(Edge(relationship_name="listens_to", weight=95), [bohemian, imagine]),
        playlists=(Edge(relationship_name="curated"), [rock_mix, chill]),
        follows=(Edge(relationship_name="follows"), []),
    )
    bob = Listener(
        name="Bob",
        favorites=(Edge(relationship_name="listens_to", weight=80), [clair, billie]),
        playlists=(Edge(relationship_name="curated"), [chill]),
        follows=(Edge(relationship_name="follows", weight=70), [alice]),
    )

    all_nodes = [bohemian, imagine, clair, billie, rock_mix, chill, alice, bob]
    await persist_memory_nodes(all_nodes)

    print(f"Stored {len(all_nodes)} nodes with weighted edges.")
    await visualize_graph()


if __name__ == "__main__":
    asyncio.run(run())
