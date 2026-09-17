"""
Chinese Coreference Resolution Module v3.0

Core Features:
1. Chinese word segmentation & entity recognition (person names, titles, locations, places, objects, time)
2. Coreference resolution (replacing pronouns with concrete entities)
3. Time normalization (converting relative time to absolute time ranges)
4. Entity canonicalization (mapping aliases to canonical names)

Architecture:
    Input text -> jieba segmentation -> rule correction -> HMM POS tagging -> entity classification -> coreference resolution -> output

Usage:

1. Quick usage (coreference resolution):
    from coreference_module import resolve

    text = "小明去北京。他在那里工作。"
    result = resolve(text)
    print(result)  # "小明去北京。小明在北京工作。"

2. Detailed usage (with replacement records):
    from coreference_module import CoreferenceResolver

    resolver = CoreferenceResolver()
    resolved, replacements = resolver.resolve_text("小明去北京。他在那里工作。")
    print(resolved)
    print(replacements)
    resolver.reset()

3. Structured output (for Memory Engine):
    from coreference_module import CoreferenceResolver

    resolver = CoreferenceResolver()
    output = resolver.resolve_text_structured("去年我去了北京。那时候天气很好。")
    print(output.resolved_text)    # resolved text
    print(output.mentions)         # entity mention list (with positions)
    print(output.time_extractions) # time normalization results

4. Time normalization:
    from coreference_module import normalize_time
    from datetime import datetime

    result = normalize_time("昨天", datetime(2026, 1, 12))
    print(result.start_dt, result.end_dt, result.precision)

5. Entity extraction:
    from coreference_module import NERService, extract_mentions

    # Method 1: Service class
    service = NERService()
    mentions = service.extract_mentions("小明在学校读书")

    # Method 2: Convenience function
    mentions = extract_mentions("小明在学校读书")

6. Entity canonicalization:
    from coreference_module import create_canonicalizer

    alias_map = {'PER_NAME': {'小张': '张三'}}
    canonicalizer = create_canonicalizer(alias_map)
    result = canonicalizer.canonicalize('小张', 'PER_NAME')
    print(result.canonical_text)  # 张三
"""

# === Tokenizer ===
from .tokenizer import (
    ChineseTokenizer,
    Token,
    Mention,
)

# === Coreference Resolver ===
from .coreference import (
    # Core classes
    CoreferenceResolver,
    StreamCorefSession,
    EntityTracker,
    Entity,
    # Data structures
    CorefOutput,
    Replacement,
    TimeSpan,
    # Convenience functions
    resolve,
    resolve_with_details,
    split_sentences,
)

# === NER Service ===
from .ner_adapter import (
    NERService,
    NERResult,
    MentionWithCanonical,
    extract_mentions,
    extract_entities,
)

# === Time Normalization ===
from .time_normalizer import (
    TimeNormalizer,
    TimeSpan as TimeSpanResult,  # avoid conflict with coreference TimeSpan
    normalize_time,
)

# === Entity Canonicalization ===
from .canonicalizer import (
    BaseCanonicalizer,
    DictCanonicalizer,
    RuleBasedCanonicalizer,
    ChainedCanonicalizer,
    CanonicalResult,  # defined solely in canonicalizer
    AliasCandidate,
    create_canonicalizer,
    canonicalize,
)

__version__ = "3.0.0"
__author__ = "Coreference Resolution System"

__all__ = [
    # === Tokenizer ===
    "ChineseTokenizer",
    "Token",
    "Mention",
    # === Coreference Resolution ===
    "CoreferenceResolver",
    "StreamCorefSession",
    "EntityTracker",
    "Entity",
    "CorefOutput",
    "Replacement",
    "TimeSpan",
    "CanonicalResult",
    "resolve",
    "resolve_with_details",
    "split_sentences",
    # === NER Service ===
    "NERService",
    "NERResult",
    "MentionWithCanonical",
    "extract_mentions",
    "extract_entities",
    # === Time Normalization ===
    "TimeNormalizer",
    "TimeSpanResult",
    "normalize_time",
    # === Entity Canonicalization ===
    "BaseCanonicalizer",
    "DictCanonicalizer",
    "RuleBasedCanonicalizer",
    "ChainedCanonicalizer",
    "AliasCandidate",
    "create_canonicalizer",
    "canonicalize",
]
