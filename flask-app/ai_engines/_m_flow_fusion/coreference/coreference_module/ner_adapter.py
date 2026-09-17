"""
NER Service Adapter

Provides a standardized NER interface for Memory Engine consumption.

Main Features:
1. extract(): backward-compatible interface, returns entities grouped by type
2. extract_mentions(): new interface, returns Mention list with position info
"""

from typing import List, Dict, Optional, Callable
from dataclasses import dataclass

try:
    from .tokenizer import ChineseTokenizer, Mention
    from .canonicalizer import CanonicalResult
except ImportError:
    from tokenizer import ChineseTokenizer, Mention
    from canonicalizer import CanonicalResult


@dataclass
class NERResult:
    """NER result (backward-compatible interface)"""

    PER: List[str]  # persons (names + titles)
    LOC: List[str]  # locations (named + places)
    TIME: List[str]  # time expressions
    OBJ: List[str]  # objects


@dataclass
class MentionWithCanonical(Mention):
    """Mention with canonicalization info"""

    canonical: Optional[str] = None  # canonicalized result
    entity_id: Optional[str] = None  # entity ID
    confidence: float = 1.0  # confidence score


class NERService:
    """NER Service"""

    def __init__(self):
        self.tokenizer = ChineseTokenizer()

    def extract(self, text: str) -> NERResult:
        """Extract entities (backward-compatible interface)

        Args:
            text: input text

        Returns:
            NERResult: entities grouped by type
        """
        result = self.tokenizer.analyze(text)

        return NERResult(
            PER=result["person_names"] + result["person_titles"],
            LOC=result["location_names"] + result["location_places"],
            TIME=result["times"],
            OBJ=result["objects"],
        )

    def extract_mentions(
        self, text: str, canonicalizer: Optional[Callable[[str, str], CanonicalResult]] = None
    ) -> List[Mention]:
        """Extract entity Mentions (new interface, with position info)

        Differences from extract():
        1. Preserves entity occurrence order in the original text
        2. Includes precise character position info (start, end)
        3. Supports optional canonicalization

        Args:
            text: input text
            canonicalizer: optional canonicalization function (surface, type) -> CanonicalResult

        Returns:
            List[Mention]: entity mentions in occurrence order
        """
        mentions = self.tokenizer.analyze_mentions(text)

        if canonicalizer:
            # Canonicalize mentions and return version with canonicalization info
            result = []
            for mention in mentions:
                canonical_result = canonicalizer(mention.surface, mention.type)
                result.append(
                    MentionWithCanonical(
                        surface=mention.surface,
                        type=mention.type,
                        start=mention.start,
                        end=mention.end,
                        sentence_id=mention.sentence_id,
                        canonical=canonical_result.canonical_text,
                        entity_id=canonical_result.entity_id,
                        confidence=canonical_result.confidence,
                    )
                )
            return result

        return mentions

    def extract_by_type(self, text: str, entity_type: str) -> List[Mention]:
        """Extract entities by type

        Args:
            text: input text
            entity_type: entity type (PER_NAME, PER_TITLE, LOC_NAME, LOC_PLACE, OBJ, TIME)

        Returns:
            List[Mention]: entities of the specified type
        """
        mentions = self.tokenizer.analyze_mentions(text)
        return [m for m in mentions if m.type == entity_type]

    def extract_persons(self, text: str) -> List[Mention]:
        """Extract person entities (names + titles)"""
        mentions = self.tokenizer.analyze_mentions(text)
        return [m for m in mentions if m.type in ["PER_NAME", "PER_TITLE"]]

    def extract_locations(self, text: str) -> List[Mention]:
        """Extract location entities (named + places)"""
        mentions = self.tokenizer.analyze_mentions(text)
        return [m for m in mentions if m.type in ["LOC_NAME", "LOC_PLACE"]]

    def extract_times(self, text: str) -> List[Mention]:
        """Extract time entities"""
        mentions = self.tokenizer.analyze_mentions(text)
        return [m for m in mentions if m.type == "TIME"]

    def extract_objects(self, text: str) -> List[Mention]:
        """Extract object entities"""
        mentions = self.tokenizer.analyze_mentions(text)
        return [m for m in mentions if m.type == "OBJ"]


# === Convenience Functions ===


def extract_mentions(text: str) -> List[Mention]:
    """Quick mention extraction"""
    service = NERService()
    return service.extract_mentions(text)


def extract_entities(text: str) -> NERResult:
    """Quick entity extraction (backward-compatible interface)"""
    service = NERService()
    return service.extract(text)


# === Test ===

if __name__ == "__main__":
    print("=" * 70)
    print("NER Service Test")
    print("=" * 70)

    service = NERService()

    tests = [
        "小明在学校读书",
        "妈妈去超市买苹果",
        "去年我去了北京",
        "刘德华和张学友是好朋友",
    ]

    for text in tests:
        print(f"\nInput: {text}")

        # Legacy interface
        result = service.extract(text)
        print(f"  Legacy: PER={result.PER}, LOC={result.LOC}, TIME={result.TIME}, OBJ={result.OBJ}")

        # New interface
        mentions = service.extract_mentions(text)
        print(f"  New:    {[(m.surface, m.type, f'[{m.start}:{m.end}]') for m in mentions]}")
