"""
Entity Canonicalization Module (Canonicalizer)

Core Features:
1. Map entity aliases to canonical names
2. Support pluggable mapping backends (in-memory / database / KV store)
3. Return original value when no match is found (never guess)

Design Principles:
- Never modify when no match is found, ensuring alias absence doesn't hurt recall
- Unknown aliases are placed in a "learning candidate queue" for future LLM-based mapping updates
"""

from typing import Dict, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CanonicalResult:
    """Canonicalization result"""

    surface_text: str  # original text
    canonical_text: str  # canonicalized result
    entity_type: str  # entity type
    entity_id: Optional[str] = None  # entity ID (optional)
    confidence: float = 1.0  # confidence score
    evidence: str = ""  # evidence source: 'rule', 'alias_map', 'llm', 'default'


@dataclass
class AliasCandidate:
    """Alias candidate pending learning"""

    surface_text: str  # alias text
    entity_type: str  # entity type
    context: str  # context snippet
    timestamp: datetime  # discovery time
    suggested_canonical: Optional[str] = None  # suggested canonical name (if available)


class BaseCanonicalizer:
    """Base class for canonicalizers

    Subclasses must implement the _lookup method to provide specific mapping logic
    """

    def __init__(self):
        # Learning candidate queue
        self.alias_candidates: List[AliasCandidate] = []
        self.max_candidates = 1000  # max candidates to keep

    def canonicalize(self, surface_text: str, entity_type: str, context: str = "") -> CanonicalResult:
        """Canonicalize an entity

        Args:
            surface_text: original text
            entity_type: entity type
            context: context (optional, for disambiguation)

        Returns:
            CanonicalResult: canonicalization result
        """
        # 1. Look up mapping
        result = self._lookup(surface_text, entity_type)

        if result:
            return result

        # 2. Not found, add to candidate queue
        self._add_candidate(surface_text, entity_type, context)

        # 3. Return original value (never guess)
        return CanonicalResult(
            surface_text=surface_text,
            canonical_text=surface_text,  # original value
            entity_type=entity_type,
            confidence=0.5,  # low confidence
            evidence="default",
        )

    def _lookup(self, surface_text: str, entity_type: str) -> Optional[CanonicalResult]:
        """Look up mapping (implemented by subclasses)"""
        raise NotImplementedError

    def _add_candidate(self, surface_text: str, entity_type: str, context: str):
        """Add to candidate queue"""
        candidate = AliasCandidate(
            surface_text=surface_text,
            entity_type=entity_type,
            context=context[:200],  # limit context length
            timestamp=datetime.now(),
        )

        self.alias_candidates.append(candidate)

        # Limit queue size
        if len(self.alias_candidates) > self.max_candidates:
            self.alias_candidates = self.alias_candidates[-self.max_candidates :]

    def get_candidates(self) -> List[AliasCandidate]:
        """Get pending learning candidates"""
        return self.alias_candidates

    def clear_candidates(self):
        """Clear candidate queue"""
        self.alias_candidates.clear()


class DictCanonicalizer(BaseCanonicalizer):
    """In-memory dictionary based canonicalizer

    Suitable for:
    - Small-scale alias mappings
    - Development / testing environments
    - Scenarios without persistence requirements
    """

    def __init__(self, alias_map: Dict[str, Dict[str, str]] = None):
        """
        Args:
            alias_map: alias mapping table {entity_type: {alias: canonical}}
        """
        super().__init__()
        self.alias_map = alias_map or {}

    def _lookup(self, surface_text: str, entity_type: str) -> Optional[CanonicalResult]:
        """Look up mapping from dictionary"""
        type_map = self.alias_map.get(entity_type, {})
        canonical = type_map.get(surface_text)

        if canonical:
            return CanonicalResult(
                surface_text=surface_text,
                canonical_text=canonical,
                entity_type=entity_type,
                confidence=1.0,
                evidence="alias_map",
            )

        return None

    def add_alias(self, alias: str, canonical: str, entity_type: str):
        """Add an alias mapping"""
        if entity_type not in self.alias_map:
            self.alias_map[entity_type] = {}
        self.alias_map[entity_type][alias] = canonical

    def remove_alias(self, alias: str, entity_type: str):
        """Remove an alias mapping"""
        if entity_type in self.alias_map:
            self.alias_map[entity_type].pop(alias, None)


class RuleBasedCanonicalizer(BaseCanonicalizer):
    """Rule-based canonicalizer

    Suitable for:
    - Common variant rules (e.g. nickname -> full name)
    - Standardization (e.g. whitespace removal, fullwidth to halfwidth)
    """

    def __init__(self):
        super().__init__()

        # Common person name alias rules
        self.person_rules = {
            # Rules like nickname -> real name require additional info; simple example here
        }

        # Location name aliases
        self.location_rules = {
            "帝都": "北京",
            "魔都": "上海",
            "花城": "广州",
            "鹏城": "深圳",
            "泉城": "济南",
            "蓉城": "成都",
            "江城": "武汉",
            "春城": "昆明",
            "冰城": "哈尔滨",
            "石头城": "南京",
        }

    def _lookup(self, surface_text: str, entity_type: str) -> Optional[CanonicalResult]:
        """Apply rules"""
        canonical = None

        if entity_type in ["PER_NAME", "PER_TITLE"]:
            canonical = self.person_rules.get(surface_text)
        elif entity_type in ["LOC_NAME", "LOC_PLACE"]:
            canonical = self.location_rules.get(surface_text)

        if canonical:
            return CanonicalResult(
                surface_text=surface_text,
                canonical_text=canonical,
                entity_type=entity_type,
                confidence=0.9,
                evidence="rule",
            )

        return None


class ChainedCanonicalizer(BaseCanonicalizer):
    """Chained canonicalizer

    Tries multiple canonicalizers in order; returns the first match
    """

    def __init__(self, canonicalizers: List[BaseCanonicalizer] = None):
        super().__init__()
        self.canonicalizers = canonicalizers or []

    def add_canonicalizer(self, canonicalizer: BaseCanonicalizer):
        """Add a canonicalizer to the chain"""
        self.canonicalizers.append(canonicalizer)

    def _lookup(self, surface_text: str, entity_type: str) -> Optional[CanonicalResult]:
        """Try each canonicalizer in order"""
        for canonicalizer in self.canonicalizers:
            result = canonicalizer._lookup(surface_text, entity_type)
            if result:
                return result
        return None


# === Convenience Functions ===


def create_canonicalizer(alias_map: Dict[str, Dict[str, str]] = None) -> BaseCanonicalizer:
    """Create a canonicalizer

    Creates a chained canonicalizer by default: rules -> dictionary
    """
    chain = ChainedCanonicalizer()

    # 1. Rule-based canonicalization
    chain.add_canonicalizer(RuleBasedCanonicalizer())

    # 2. Dictionary-based canonicalization
    if alias_map:
        chain.add_canonicalizer(DictCanonicalizer(alias_map))

    return chain


def canonicalize(surface_text: str, entity_type: str) -> CanonicalResult:
    """Quick canonicalization (stateless)"""
    canonicalizer = RuleBasedCanonicalizer()
    return canonicalizer.canonicalize(surface_text, entity_type)


# === Test ===

if __name__ == "__main__":
    print("=" * 70)
    print("Entity Canonicalization Test")
    print("=" * 70)

    # Create canonicalizer
    alias_map = {
        "PER_NAME": {
            "小张": "张三",
            "张子": "张三",
            "老王": "王五",
        },
        "LOC_NAME": {
            "BJ": "北京",
            "SH": "上海",
        },
    }

    canonicalizer = create_canonicalizer(alias_map)

    tests = [
        ("小张", "PER_NAME"),
        ("张子", "PER_NAME"),
        ("李四", "PER_NAME"),  # unknown, should return original value
        ("帝都", "LOC_NAME"),  # rule match
        ("魔都", "LOC_NAME"),  # rule match
        ("BJ", "LOC_NAME"),  # dictionary match
        ("杭州", "LOC_NAME"),  # unknown
    ]

    for surface, etype in tests:
        result = canonicalizer.canonicalize(surface, etype)
        print(
            f"  {surface:8} ({etype}) -> {result.canonical_text} "
            f"[conf={result.confidence:.1f}, evidence={result.evidence}]"
        )

    print()
    print("Learning candidates:")
    for candidate in canonicalizer.get_candidates():
        print(f"  {candidate.surface_text} ({candidate.entity_type})")
