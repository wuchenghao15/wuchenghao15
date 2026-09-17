"""
Retrieval Data Structures
=========================

Pydantic models for capturing user interactions and feedback
within the M-flow retrieval subsystem.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, confloat

from m_flow.core.models.MemoryNode import MemoryNode
from m_flow.core.domain.models.memory_space import MemorySpace


# --- Interaction Models ---


class MflowUserInteraction(MemoryNode):
    """
    Captures a complete interaction cycle between user and system.

    An interaction includes the user's query, the generated response,
    and the context used to produce that response.

    Attributes
    ----------
    question : str
        The user's input question or query text.
    answer : str
        The system's generated response.
    context : str
        Retrieved context used for response generation.
    memory_spaces : MemorySpace | None
        Optional reference to a containing memory space.
    """

    question: str
    answer: str
    context: str
    memory_spaces: Optional[MemorySpace] = None


# --- Feedback Models ---


class MflowUserFeedback(MemoryNode):
    """
    Stores user-provided feedback on system responses.

    Used to improve response quality through feedback loops
    and evaluation metrics.

    Attributes
    ----------
    feedback : str
        User's textual feedback commentary.
    sentiment : str
        Categorical sentiment label.
    score : float
        Numerical rating value.
    memory_spaces : MemorySpace | None
        Optional reference to a containing memory space.
    """

    feedback: str
    sentiment: str
    score: float
    memory_spaces: Optional[MemorySpace] = None


class UserFeedbackSentiment(str, Enum):
    """
    Enumeration of possible sentiment categories.

    Used to classify user feedback into discrete sentiment buckets.
    """

    positive = "positive"
    negative = "negative"
    neutral = "neutral"


class UserFeedbackEvaluation(BaseModel):
    """
    Structured assessment of user feedback.

    Combines quantitative score with qualitative sentiment
    classification for comprehensive analysis.

    Attributes
    ----------
    score : float
        Rating on scale from -5 (worst) to +5 (best).
    evaluation : UserFeedbackSentiment
        Categorical sentiment classification.
    """

    score: confloat(ge=-5, le=5) = Field(
        ...,
        description="Rating scale: -5 (very negative) to +5 (very positive)",
    )
    evaluation: UserFeedbackSentiment
