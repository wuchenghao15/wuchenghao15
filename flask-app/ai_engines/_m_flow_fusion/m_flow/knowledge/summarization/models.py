from typing import List, Optional

from m_flow.core import MemoryNode
from m_flow.ingestion.chunking.models import ContentFragment
from m_flow.shared.data_models import Section


class FragmentDigest(MemoryNode):
    """
    Represent a text summary derived from a document chunk.

    This class encapsulates a text summary as well as its associated metadata. The public
    instance variables include 'text' for the summary content and 'made_from' which
    indicates the source document chunk. The 'metadata' instance variable contains
    additional information such as indexed fields.

    Enhanced with optional 'sections' field for structured semantic segmentation.
    When sections is populated, each section represents a coherent subtopic.
    The 'text' field is maintained for backward compatibility.

    Content Routing Enhancement:
    - routing_type: "episodic" or "atomic" (set by route_content task)
    - segment_id: Unique identifier for episodic segment grouping
    - segment_topic: Suggested topic label for the segment
    """

    text: str
    made_from: ContentFragment
    # Optional structured sections for fine-grained facet generation
    sections: Optional[List[Section]] = None
    # Overall topic extracted from sectioned summary
    overall_topic: Optional[str] = None

    # Content Routing fields (set by route_content task)
    # Use Optional[str] instead of Enum to avoid circular import with episodic.models
    routing_type: Optional[str] = None  # "episodic" or "atomic"
    segment_id: Optional[str] = None  # Groups chunks into episodic segments
    segment_topic: Optional[str] = None  # Suggested topic for the segment

    metadata: dict = {"index_fields": ["text"]}
