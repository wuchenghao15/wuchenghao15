"""
FacetPoint (fine-grained detail node).

FacetPoint is a fine-grained "information point/proposition point/micro-fact point" node under a Facet.
It replaces the current approach of "Facet.aliases_text enumerating all information points in facet.description",
turning these information points into first-class nodes on the graph, enabling:
- Independent vectorization and matching (sharper)
- Independent reranking and explanation (controllable)
- Independent evidence linking (traceable)

Design principles:
- Model layer does not limit quantity/character count
- Strategy left to write-side Stage2
"""

from typing import Optional, List
from m_flow.core import MemoryNode


class FacetPoint(MemoryNode):
    """
    Fine-grained information point under a Facet.

    Represents a single proposition, fact, or detail that can be:
    - Independently vectorized and retrieved
    - Independently scored and explained
    - Independently linked to evidence
    """

    # Graph readability: recommend name = search_text
    name: str

    # Main retrieval handle (short, sharp)
    search_text: str

    # Optional: few synonyms/paraphrases (structured storage)
    aliases: Optional[List[str]] = None

    # Optional: concatenated text of "\n".join(aliases) (participates in vectorization fallback recall)
    aliases_text: Optional[str] = None

    # Optional: explanatory expansion (for RAG, not indexed)
    description: Optional[str] = None

    # Display-only field: NOT indexed, but displayed when the node is retrieved
    # This field is not populated by standard ingestion pipelines.
    # Users can manually set this field to add additional context/notes that will be shown
    # when this FacetPoint is retrieved, without affecting search/retrieval behavior.
    display_only: Optional[str] = None

    # Optional: evidence links (pointing to ContentFragment)
    # Format: List[tuple[Edge, ContentFragment]] or List[ContentFragment]
    supported_by: Optional[List] = None

    # Index fields: only search_text as main entry
    # NOTE: aliases_text not indexed (same as Facet)
    metadata: dict = {"index_fields": ["search_text"]}
