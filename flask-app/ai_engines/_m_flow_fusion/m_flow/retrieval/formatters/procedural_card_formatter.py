"""
ProceduralCardFormatter.

Formats edges (or bundles) returned from bundle search into unified ProcedureCard structure.

Each card contains:
- title / procedure_key / version / is_active
- summary (coarse-grained)
- context (when/why/boundary)
- steps (list or pack.description)
- notes (risks/exceptions/prerequisites)
- provenance (source_refs, for debugging)

Key design:
- Cards don't need to list all points one by one
- Use pack.description/anchor_text as main content
- Saves cost and more stable
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge


@dataclass
class ProcedureCard:
    """
    Procedural card structure.

    Each card represents a complete Procedure.
    """

    # Basic information
    procedure_id: str
    title: str
    procedure_key: Optional[str] = None
    version: int = 1
    is_active: bool = True
    confidence: str = "high"  # high / medium / low

    # Content
    summary: str = ""  # Coarse-grained summary
    context: str = ""  # when/why/boundary merged text
    steps: str = ""  # Step list text

    # Optional supplements
    notes: str = ""  # Risks/exceptions/prerequisites
    provenance: List[str] = field(default_factory=list)  # source_refs

    # Retrieval metadata (from bundle)
    score: float = 0.0
    best_path: str = ""
    from_query_kinds: List[str] = field(default_factory=list)

    def to_text(self, include_provenance: bool = False) -> str:
        """
        Convert card to prompt-usable text format.

        Args:
            include_provenance: Whether to include source_refs (for debugging)

        Returns:
            Formatted card text
        """
        lines = []

        # Title line
        status = "[ACTIVE]" if self.is_active else "[DEPRECATED]"
        conf_emoji = {"high": "[HIGH]", "medium": "[MED]", "low": "[LOW]"}.get(self.confidence, "[LOW]")
        lines.append(f"[CARD] **{self.title}** (v{self.version}) {status} {conf_emoji}")

        if self.procedure_key:
            lines.append(f"   Key: `{self.procedure_key}`")

        # Summary
        if self.summary:
            lines.append(f"\n**Summary**: {self.summary}")

        # Context
        if self.context:
            lines.append(f"\n**Applicable Scenarios**:\n{self.context}")

        # Steps
        if self.steps:
            lines.append(f"\n**Steps**:\n{self.steps}")

        # Notes
        if self.notes:
            lines.append(f"\n**Notes**: {self.notes}")

        # Provenance (debug)
        if include_provenance and self.provenance:
            lines.append(f"\n[Source: {', '.join(self.provenance[:3])}]")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format (for API output)."""
        return {
            "procedure_id": self.procedure_id,
            "title": self.title,
            "procedure_key": self.procedure_key,
            "version": self.version,
            "is_active": self.is_active,
            "confidence": self.confidence,
            "summary": self.summary,
            "context": self.context,
            "steps": self.steps,
            "notes": self.notes,
            "provenance": self.provenance,
            "score": self.score,
            "best_path": self.best_path,
        }


class ProceduralCardFormatter:
    """
    Card formatter.

    Converts edges or bundles returned from bundle search into structured ProcedureCard list.
    """

    def __init__(
        self,
        max_summary_length: int = 300,
        max_context_length: int = 500,
        max_steps_length: int = 800,
        include_inactive: bool = True,
    ):
        """
        Initialize formatter.

        Args:
            max_summary_length: Maximum summary length
            max_context_length: Maximum context length
            max_steps_length: Maximum steps length
            include_inactive: Whether to include non-active procedures
        """
        self.max_summary_length = max_summary_length
        self.max_context_length = max_context_length
        self.max_steps_length = max_steps_length
        self.include_inactive = include_inactive

    def format_from_edges(
        self,
        edges: List[Edge],
        bundles_metadata: Optional[List[Dict]] = None,
    ) -> List[ProcedureCard]:
        """
        Build ProcedureCard list from edges.

        Args:
            edges: Edge list returned from bundle search
            bundles_metadata: Optional bundle metadata (contains score, etc.)

        Returns:
            ProcedureCard list, sorted by score
        """
        # 1. Aggregate edges by procedure_id
        proc_edges: Dict[str, List[Edge]] = {}
        proc_nodes: Dict[str, Any] = {}

        for edge in edges:
            for node in (edge.node1, edge.node2):
                node_type = node.attributes.get("type")
                node_id = str(node.id)

                if node_type == "Procedure":
                    if node_id not in proc_nodes:
                        proc_nodes[node_id] = node
                        proc_edges[node_id] = []
                    proc_edges[node_id].append(edge)
                    break

        # 2. Build metadata index
        bundle_info: Dict[str, Dict] = {}
        if bundles_metadata:
            for b in bundles_metadata:
                pid = b.get("procedure_id")
                if pid:
                    bundle_info[pid] = b

        # 3. Build card for each Procedure
        cards: List[ProcedureCard] = []

        for proc_id, proc_node in proc_nodes.items():
            attrs = proc_node.attributes
            props = attrs.get("properties") or {}
            if isinstance(props, str):
                import json

                try:
                    props = json.loads(props)
                except (json.JSONDecodeError, TypeError):
                    props = {}

            # Basic information
            status = props.get("status") or attrs.get("status", "active")
            is_active = status == "active"

            if not is_active and not self.include_inactive:
                continue

            card = ProcedureCard(
                procedure_id=proc_id,
                title=attrs.get("name") or props.get("name", "Procedure"),
                procedure_key=props.get("signature") or props.get("procedure_key"),
                version=props.get("version") or attrs.get("version", 1),
                is_active=is_active,
                confidence=props.get("confidence", "high"),
                summary=self._truncate(props.get("summary") or attrs.get("summary", ""), self.max_summary_length),
                provenance=props.get("source_refs") or [],
            )

            # Extract context and steps from Procedure attributes (new architecture)
            # or from edge_text aggregation (fallback)
            context_str = props.get("context_text") or attrs.get("context_text") or ""
            steps_str = props.get("points_text") or attrs.get("points_text") or ""

            # Fallback: if Procedure doesn't have display attributes,
            # aggregate from Point edge_text (works for both new and legacy data)
            if not context_str or not steps_str:
                for edge in proc_edges.get(proc_id, []):
                    et = edge.attributes.get("edge_text") or ""
                    for node in (edge.node1, edge.node2):
                        nt = node.attributes.get("type", "")
                        if nt == "ProcedureContextPoint" and not context_str:
                            context_str = et
                        elif nt == "ProcedureStepPoint" and not steps_str:
                            steps_str = et
                        # Legacy: Pack nodes
                        elif nt == "ProcedureContextPack" and not context_str:
                            np = node.attributes.get("properties") or {}
                            if isinstance(np, str):
                                import json

                                try:
                                    np = json.loads(np)
                                except (json.JSONDecodeError, TypeError):
                                    np = {}
                            context_str = np.get("anchor_text") or node.attributes.get("anchor_text") or ""
                        elif nt == "ProcedureStepsPack" and not steps_str:
                            np = node.attributes.get("properties") or {}
                            if isinstance(np, str):
                                import json

                                try:
                                    np = json.loads(np)
                                except (json.JSONDecodeError, TypeError):
                                    np = {}
                            steps_str = np.get("anchor_text") or node.attributes.get("anchor_text") or ""

            card.context = self._truncate(context_str, self.max_context_length)
            card.steps = self._truncate(steps_str, self.max_steps_length)

            # Add bundle metadata
            if proc_id in bundle_info:
                bi = bundle_info[proc_id]
                card.score = bi.get("score", 0.0)
                card.best_path = bi.get("best_path", "")
                card.from_query_kinds = bi.get("from_query_kinds", [])

            cards.append(card)

        # 4. Sort by score (lower score is better)
        cards.sort(key=lambda c: c.score)

        return cards

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text to specified length."""
        if not text:
            return ""
        text = text.strip()
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."


def format_procedure_cards(
    edges: List[Edge],
    bundles_metadata: Optional[List[Dict]] = None,
    max_cards: int = 3,
    include_inactive: bool = True,
) -> List[ProcedureCard]:
    """
    Convenience function: format ProcedureCard list from edges.

    Args:
        edges: Edge list returned from bundle search
        bundles_metadata: Optional bundle metadata
        max_cards: Maximum number of cards to return
        include_inactive: Whether to include non-active procedures

    Returns:
        ProcedureCard list
    """
    formatter = ProceduralCardFormatter(include_inactive=include_inactive)
    cards = formatter.format_from_edges(edges, bundles_metadata)
    return cards[:max_cards]


def cards_to_prompt_block(
    cards: List[ProcedureCard],
    block_title: str = "Related Procedural Memory",
    include_provenance: bool = False,
) -> str:
    """
    Convert multiple cards to prompt block.

    Args:
        cards: ProcedureCard list
        block_title: Block title
        include_provenance: Whether to include provenance information

    Returns:
        Formatted prompt block text
    """
    if not cards:
        return ""

    lines = [f"### {block_title}\n"]

    for i, card in enumerate(cards, 1):
        lines.append(f"---\n**Procedure {i}**\n")
        lines.append(card.to_text(include_provenance=include_provenance))
        lines.append("")

    # Add instruction
    lines.append("---")
    lines.append(
        "*Note: The above procedural memory is for reference only. Please adjust based on the current situation. If it conflicts with user's current constraints, please confirm with the user first.*"
    )

    return "\n".join(lines)
