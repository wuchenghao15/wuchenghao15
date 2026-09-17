"""
Pydantic models for knowledge extraction, chunking, and content classification.

This module contains:
- Knowledge graph node/edge definitions
- Chunking strategy enums
- Content type classifiers
- Summary structures
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from m_flow.llm.config import get_llm_config

# ---------------------------------------------------------------------------
# Provider-specific KG node/edge definitions
# ---------------------------------------------------------------------------

_provider = get_llm_config().llm_provider.lower()

if _provider == "gemini":

    class KGNode(BaseModel):
        """Knowledge graph node (Gemini variant with label)."""

        id: str
        name: str
        type: str
        description: str
        label: str

else:

    class KGNode(BaseModel):
        """Knowledge graph node."""

        id: str
        name: str
        type: str
        description: str


class KGRelation(BaseModel):
    """Directed relationship between two nodes."""

    source_node_id: str
    target_node_id: str
    relationship_name: str


class ExtractedGraph(BaseModel):
    """Container for LLM-extracted knowledge."""

    nodes: List[KGNode] = Field(default_factory=list)
    edges: List[KGRelation] = Field(default_factory=list)

    if _provider == "gemini":
        summary: str = ""
        description: str = ""


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


class GQLQuery(BaseModel):
    """GraphQL query wrapper."""

    query: str


class AnswerPayload(BaseModel):
    """Single answer response."""

    answer: str


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


class ChunkMode(str, Enum):
    """Text segmentation strategies."""

    EXACT = "exact"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"
    CODE = "code"
    LANGCHAIN_CHARACTER = "langchain_character"


class ChunkBackend(str, Enum):
    """Underlying chunking engine."""

    LANGCHAIN_ENGINE = "langchain"
    DEFAULT_ENGINE = "default"
    HAYSTACK_ENGINE = "haystack"


# Aliases

# ---------------------------------------------------------------------------
# Summaries
# ---------------------------------------------------------------------------


class GraphSummary(BaseModel):
    """Summary containing nodes and edges."""

    nodes: List[KGNode] = Field(default_factory=list)
    edges: List[KGRelation] = Field(default_factory=list)


class CompressedText(BaseModel):
    """Compressed representation preserving key facts."""

    headline: str = Field(..., alias="summary")
    body: str = Field(..., alias="description")

    class Config:
        populate_by_name = True


class TopicSection(BaseModel):
    """Thematic segment of a document."""

    heading: str = Field(..., alias="title")
    text: str = Field(
        ...,
        alias="content",
        description="COMPRESSED summary - NEVER copy text verbatim. Rephrase in your own words with maximum information density.",
    )

    class Config:
        populate_by_name = True


Section = TopicSection


class MultiSectionSummary(BaseModel):
    """Structured summary with logical sections."""

    topic: str = Field(..., alias="overall_topic")
    parts: List[TopicSection] = Field(default_factory=list, alias="sections")

    class Config:
        populate_by_name = True

    def to_flat_text(self) -> str:
        segments = [self.topic]
        for p in self.parts:
            segments.append(f"【{p.heading}】{p.text}")
        return " ".join(segments)


SectionedSummary = MultiSectionSummary

# ---------------------------------------------------------------------------
# Unified Episodic + Procedural Routing Output
# ---------------------------------------------------------------------------


class ProceduralCandidate(BaseModel):
    """
    Single procedural candidate identified from content.

    Used by both unified routing (episodic + procedural) and standalone Router.
    Each candidate represents a potential piece of procedural knowledge to extract.
    """

    search_text: str = Field(
        ...,
        description="Retrieval handle (15-50 chars) - concise phrase for searching this procedure",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    reason: str = Field(..., description="Brief explanation why this is procedural knowledge")
    procedural_type: str = Field(
        ..., description="Type: 'user_preference' | 'user_habit' | 'reusable_process' | 'persona'"
    )


class ProceduralCandidateList(BaseModel):
    """List of 0-N procedural candidates."""

    candidates: List[ProceduralCandidate] = Field(default_factory=list)


class SectionedSummaryWithProcedural(BaseModel):
    """
    Unified output for sectioned summarization + procedural routing.

    Used when both episodic and procedural memory are enabled,
    combining the summarization and routing decision in a single LLM call.

    Now outputs 0-N candidates instead of a single binary decision.
    """

    topic: str = Field(..., alias="overall_topic")
    parts: List[TopicSection] = Field(default_factory=list, alias="sections")
    # New: 0-N procedural candidates (replaces single procedural decision)
    candidates: List[ProceduralCandidate] = Field(
        default_factory=list, description="0-N procedural candidates identified from this content"
    )

    class Config:
        populate_by_name = True

    def to_flat_text(self) -> str:
        segments = [self.topic]
        for p in self.parts:
            segments.append(f"【{p.heading}】{p.text}")
        return " ".join(segments)

    def to_sectioned_summary(self) -> MultiSectionSummary:
        """Convert to plain SectionedSummary (without procedural)."""
        return MultiSectionSummary(topic=self.topic, parts=self.parts)


class ChunkDigest(BaseModel):
    """Brief summary with chunk reference."""

    text: str
    chunk_id: str


class ChunkDigestList(BaseModel):
    """Collection of chunk digests."""

    items: List[ChunkDigest] = Field(..., alias="summaries")

    class Config:
        populate_by_name = True


# ---------------------------------------------------------------------------
# Content classification enums
# ---------------------------------------------------------------------------


class TextCategory(str, Enum):
    """Fine-grained text content labels for document classification."""

    ARTICLES = "article"
    BOOKS = "book"
    NEWS = "news"
    RESEARCH = "research_paper"
    SOCIAL = "social_post"
    WEB = "web_content"
    NARRATIVE = "narrative"
    TABULAR = "spreadsheet"
    FORMS = "form"
    DATA = "structured_data"
    CODE = "source_code"
    SHELL = "shell_script"
    MARKUP = "markup"
    CONFIG = "config_file"
    CHAT = "chat_log"
    SUPPORT = "support_log"
    BOT_DATA = "bot_training"
    TEXTBOOK = "textbook"
    EXAMS = "exam"
    ELEARN = "elearning"
    POETRY = "poetry"
    SCREENPLAY = "screenplay"
    LYRICS = "lyrics"
    MANUALS = "manual"
    SPECS = "tech_spec"
    FAQ = "faq"
    CONTRACTS = "contract"
    LEGAL = "legal_doc"
    POLICY = "policy"
    CLINICAL = "clinical_report"
    MEDICAL = "medical_record"
    SCIENTIFIC = "scientific_paper"
    FINANCIAL = "financial_report"
    BUSINESS = "business_plan"
    MARKET = "market_analysis"
    ADS = "advertisement"
    CATALOGS = "catalog"
    PR = "press_release"
    FORMAL_EMAIL = "formal_email"
    PERSONAL_EMAIL = "personal_email"
    CAPTIONS = "caption"
    ANNOTATIONS = "annotation"
    VOCAB = "vocabulary"
    LANGUAGE_EX = "language_exercise"
    REGULATORY = "regulatory_doc"
    OTHER = "other_text"


class AudioCategory(str, Enum):
    MUSIC = "music"
    PODCAST = "podcast"
    AUDIOBOOK = "audiobook"
    INTERVIEW = "interview"
    SFX = "sound_effect"
    OTHER = "other_audio"


class ImageCategory(str, Enum):
    PHOTO = "photo"
    ILLUSTRATION = "illustration"
    INFOGRAPHIC = "infographic"
    ART = "artwork"
    SCREENSHOT = "screenshot"
    OTHER = "other_image"


ImageSubclass = ImageCategory


class VideoCategory(str, Enum):
    FILM = "film"
    DOCUMENTARY = "documentary"
    TUTORIAL = "tutorial"
    ANIMATION = "animation"
    LIVE = "live_event"
    OTHER = "other_video"


VideoSubclass = VideoCategory


class MultimediaCategory(str, Enum):
    INTERACTIVE = "interactive"
    VR_AR = "vr_ar"
    MIXED = "mixed_media"
    ELEARN_MODULE = "elearning_module"
    EXHIBITION = "virtual_exhibition"
    OTHER = "other_multimedia"


MultimediaSubclass = MultimediaCategory


class ThreeDCategory(str, Enum):
    ARCHITECTURE = "architecture_3d"
    PRODUCT = "product_model"
    ANIM_3D = "animation_3d"
    SCI_VIZ = "scientific_viz"
    VR_OBJ = "vr_object"
    OTHER = "other_3d"


Model3DSubclass = ThreeDCategory


class ProceduralCategory(str, Enum):
    GUIDE = "how_to_guide"
    WORKFLOW = "workflow"
    SIM = "simulation"
    RECIPE = "recipe"
    OTHER = "other_procedural"


ProceduralSubclass = ProceduralCategory

# ---------------------------------------------------------------------------
# Content type wrappers
# ---------------------------------------------------------------------------


class BaseContentType(BaseModel):
    kind: str = Field(..., alias="type")

    class Config:
        populate_by_name = True


ContentType = BaseContentType


class TextualContent(BaseContentType):
    kind: str = "text"
    categories: List[TextCategory] = Field(..., alias="subclass")


TextContent = TextualContent


class AudioContent(BaseContentType):
    kind: str = "audio"
    categories: List[AudioCategory] = Field(..., alias="subclass")


class ImageContent(BaseContentType):
    kind: str = "image"
    categories: List[ImageCategory] = Field(..., alias="subclass")


class VideoContent(BaseContentType):
    kind: str = "video"
    categories: List[VideoCategory] = Field(..., alias="subclass")


class MultimediaContent(BaseContentType):
    kind: str = "multimedia"
    categories: List[MultimediaCategory] = Field(..., alias="subclass")


class ThreeDContent(BaseContentType):
    kind: str = "3d_model"
    categories: List[ThreeDCategory] = Field(..., alias="subclass")


Model3DContent = ThreeDContent


class ProceduralContent(BaseContentType):
    kind: str = "procedural"
    categories: List[ProceduralCategory] = Field(..., alias="subclass")


AnyContentLabel = Union[
    TextualContent,
    AudioContent,
    ImageContent,
    VideoContent,
    MultimediaContent,
    ThreeDContent,
    ProceduralContent,
]


class ContentPrediction(BaseModel):
    label: AnyContentLabel


# ---------------------------------------------------------------------------
# Graph DB type
# ---------------------------------------------------------------------------


class GraphStore(Enum):
    NETWORKX = auto()
    NEO4J = auto()
    KUZU = auto()


# ---------------------------------------------------------------------------
# Document / relationship helpers
# ---------------------------------------------------------------------------


class RelationSpec(BaseModel):
    kind: str = Field(..., alias="type")
    src: Optional[str] = Field(None, alias="source")
    dst: Optional[str] = Field(None, alias="target")
    attrs: Optional[Dict[str, Any]] = Field(None, alias="properties")

    class Config:
        populate_by_name = True


class DocType(BaseModel):
    type_id: str
    description: str
    default_relationship: RelationSpec = RelationSpec(kind="is_type")


class CategorySpec(BaseModel):
    category_id: str
    name: str
    default_relationship: RelationSpec = RelationSpec(kind="categorized_as")


class DocMeta(BaseModel):
    id: str
    type: str
    title: str


class LocationSpec(BaseModel):
    location_id: str
    description: str
    default_relationship: RelationSpec = RelationSpec(kind="located_in")


class UserAttrs(BaseModel):
    custom: Optional[Dict[str, Any]] = Field(None, alias="custom_properties")
    location: Optional[LocationSpec] = None

    class Config:
        populate_by_name = True


class GraphModelDefaults(BaseModel):
    node_id: str
    user_attrs: UserAttrs = Field(default_factory=UserAttrs, alias="user_properties")
    docs: List[DocMeta] = Field(default_factory=list, alias="documents")
    fields: Optional[Dict[str, Any]] = Field(default_factory=dict, alias="default_fields")
    default_relationship: RelationSpec = RelationSpec(kind="has_properties")

    class Config:
        populate_by_name = True
