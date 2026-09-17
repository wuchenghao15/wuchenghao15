"""
Domain model catalogue for the m_flow knowledge-graph engine.

Re-exports every concrete node type so that downstream code can do::

    from m_flow.core.domain.models import Entity, TableRow, Event, ...
    # or for backward compatibility:
    from m_flow.core.domain.models import Entity, TableRow, Event, ...

Models are grouped by the memory subsystem they belong to.
"""

# ── Semantic / Structural models ────────────────────────────────────
from .ColumnValue import ColumnValue
from .Entity import Entity  # Entity is the new name, Entity is alias
from .EntityType import EntityType  # EntityType is new, EntityType is alias
from .Event import Event
from .Interval import Interval
from .memory_space import MemorySpace
from .MemoryTriplet import MemoryTriplet
from .TableRow import TableRow
from .TableType import TableType
from .Timestamp import Timestamp

# ── Episodic Memory models ──────────────────────────────────────────
from .Episode import Episode
from .Facet import Facet
from .FacetPoint import FacetPoint

# ── Procedural Memory models ───────────────────────────────────────
from .Procedure import Procedure
from .ProcedureContextPoint import ProcedureContextPoint
from .ProcedureStepPoint import ProcedureStepPoint

# DEPRECATED: Pack nodes removed from architecture (kept for legacy data compat)
from .ProcedureContextPack import ProcedureContextPack
from .ProcedureStepsPack import ProcedureStepsPack

# ── Preference Memory models ───────────────────────────────────────
from .PreferencePoint import PreferencePoint

__all__ = [
    # Semantic / Structural (New names)
    "Entity",
    "EntityType",
    # Semantic / Structural (Backward compatible aliases)
    "Entity",  # Deprecated: use Entity
    "EntityType",  # Deprecated: use EntityType
    # Other Semantic / Structural
    "ColumnValue",
    "Event",
    "Interval",
    "MemorySpace",
    "MemoryTriplet",
    "TableRow",
    "TableType",
    "Timestamp",
    # Episodic
    "Episode",
    "Facet",
    "FacetPoint",
    # Procedural
    "Procedure",
    "ProcedureContextPack",
    "ProcedureContextPoint",
    "ProcedureStepPoint",
    "ProcedureStepsPack",
    # Preference
    "PreferencePoint",
]
