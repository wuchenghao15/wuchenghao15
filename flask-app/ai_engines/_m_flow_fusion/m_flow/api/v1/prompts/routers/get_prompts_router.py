"""
Prompts API Router

REST API endpoints for managing LLM prompt templates.
Provides CRUD operations and reset-to-default functionality.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from m_flow.api.DTO import InDTO, OutDTO
from m_flow.root_dir import get_absolute_path
from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    from m_flow.auth.models import User

_log = get_logger()

# Default prompts directory
_PROMPTS_DIR = "./llm/prompts"
_BACKUP_DIR = "./llm/prompts_defaults"


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


class PromptDTO(OutDTO):
    """Prompt template metadata and content."""

    name: str = Field(..., description="Prompt filename (without extension)")
    filename: str = Field(..., description="Full filename with extension")
    category: str = Field(..., description="Prompt category based on prefix")
    content: str = Field(..., description="Prompt template content")
    description: Optional[str] = Field(None, description="Prompt description")
    is_modified: bool = Field(False, description="Whether prompt differs from default")


class PromptListItemDTO(OutDTO):
    """Prompt list item (without full content)."""

    name: str
    filename: str
    category: str
    description: Optional[str] = None
    is_modified: bool = False


class PromptUpdateDTO(InDTO):
    """Prompt update request."""

    content: str = Field(..., description="New prompt content")


class PromptCategoryDTO(OutDTO):
    """Grouped prompts by category."""

    category: str
    prompts: List[PromptListItemDTO]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def _get_prompts_path() -> Path:
    """Get absolute path to prompts directory."""
    return Path(get_absolute_path(_PROMPTS_DIR))


def _get_defaults_path() -> Path:
    """Get absolute path to default prompts backup."""
    return Path(get_absolute_path(_BACKUP_DIR))


def _ensure_defaults_backup() -> None:
    """
    Ensure default prompts are backed up.

    First time called, copies all prompts to backup directory.
    """
    prompts_path = _get_prompts_path()
    defaults_path = _get_defaults_path()

    if not defaults_path.exists():
        defaults_path.mkdir(parents=True, exist_ok=True)
        # Copy all .txt files as defaults
        for prompt_file in prompts_path.glob("*.txt"):
            shutil.copy2(prompt_file, defaults_path / prompt_file.name)
        _log.info(f"Created prompts backup at {defaults_path}")


def _categorize_prompt(filename: str) -> str:
    """
    Determine prompt category from filename based on actual function.

    Categories:
    - answering: Question answering and context generation
    - episodic: Episode/Facet extraction and routing
    - entity: Entity extraction and description
    - graph: Knowledge graph generation
    - summarization: Content summarization
    - processing: Text processing utilities
    - evaluation: Benchmarks and testing
    """
    name = filename.lower()

    # Answering: question answering and context generation
    # Note: summarize_search_results is for Q&A response, not general summarization
    if (
        name.startswith("answer")
        or name.startswith("direct_answer")
        or "retrieval_context" in name
        or name == "search_result_deduplicator.txt"
    ):
        return "answering"

    # Episodic: Episode/Facet extraction and routing
    if name.startswith("episodic") or name.startswith("episode"):
        return "episodic"

    # Entity: entity extraction and description
    if "entity" in name or name == "optimize_merged_description.txt":
        return "entity"

    # Graph: knowledge graph generation
    if name.startswith("generate_graph") or name.startswith("knowledge_graph_extractor"):
        return "graph"

    # Summarization: content summarization (general purpose)
    if name.startswith("summarize"):
        return "summarization"

    # Processing: text processing utilities
    if name in ("sentence_grouping.txt", "content_classifier.txt"):
        return "processing"

    # Evaluation: benchmarks and testing
    if "benchmark" in name:
        return "evaluation"

    return "other"


def _get_prompt_description(filename: str) -> str:
    """Generate human-readable description for prompt."""
    descriptions = {
        # Answering - Question answering and context generation
        "direct_answer.txt": "Default system prompt for answering user questions",
        "answer_procedure_question.txt": "Answer how-to and procedural questions",
        "retrieval_context.txt": "Generate context for Cypher-based retrieval",
        "graph_retrieval_context.txt": "Generate Q&A context from graph triplets",
        "search_result_deduplicator.txt": "Summarize retrieved search results for response",
        # Episodic - Episode/Facet extraction and routing
        "episodic_extract_facet_points.txt": "Extract detailed FacetPoints from Episode content",
        "episodic_route_decision.txt": "Decide routing: create new Episode or merge into existing",
        "episodic_select_entities.txt": "Select relevant entities from text for Episode linking",
        "episodic_point_rewrite.txt": "Rewrite and refine FacetPoint content",
        "episodic_point_generate_missing.txt": "Generate missing FacetPoints to complete Episode",
        "episode_size_audit.txt": "Audit Episode size and quality for optimization",
        # Entity - Entity extraction and description
        "extract_entity_names.txt": "Extract entity names from text with form preservation",
        "write_entity_descriptions.txt": "Generate descriptive text for entities",
        "optimize_merged_description.txt": "Optimize merged entity descriptions",
        # Graph - Knowledge graph generation
        "knowledge_graph_extractor.txt": "Generate knowledge graph from text",
        # Summarization - Content summarization
        "semantic_compressor.txt": "General-purpose content summarization",
        "summarize_content_atomic.txt": "Generate atomic (single-topic) summary",
        "summarize_content_text.txt": "Generate sectioned summary with topic grouping",
        "summarize_content_text_with_naming.txt": "Sectioned summary with Episode naming (used when content routing is disabled)",
        # Processing - Text processing utilities
        "sentence_grouping.txt": "Group sentences by semantic similarity",
        "content_classifier.txt": "Classify content into predefined categories",
        # Evaluation - Benchmarks and testing
        "benchmark_qa_system.txt": "Benchmark prompt for evaluation tests",
    }
    return descriptions.get(filename, "")


def _is_prompt_modified(filename: str) -> bool:
    """Check if prompt differs from default."""
    prompts_path = _get_prompts_path()
    defaults_path = _get_defaults_path()

    current_file = prompts_path / filename
    default_file = defaults_path / filename

    if not default_file.exists():
        return False

    try:
        current_content = current_file.read_text(encoding="utf-8")
        default_content = default_file.read_text(encoding="utf-8")
        return current_content != default_content
    except Exception:
        return False


def _validate_filename(filename: str) -> str:
    """
    Validate and sanitize prompt filename.

    Security: Prevents path traversal attacks by ensuring filename:
    - Contains no directory separators (/, \\)
    - Does not contain '..'
    - Is not an absolute path
    - Ends with .txt extension

    Args:
        filename: Raw filename from user input

    Returns:
        Sanitized filename

    Raises:
        HTTPException 400: If filename is invalid/dangerous
    """
    # Strip whitespace
    filename = filename.strip()

    # Check for path traversal attempts
    if ".." in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename: path traversal not allowed"
        )

    # Check for directory separators
    if "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename: directory separators not allowed"
        )

    # Check for absolute paths
    if os.path.isabs(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename: absolute paths not allowed"
        )

    # Ensure .txt extension
    if not filename.endswith(".txt"):
        filename = f"{filename}.txt"

    return filename


# ---------------------------------------------------------------------------
# Auth Dependency
# ---------------------------------------------------------------------------


def _auth():
    """Return authentication dependency."""
    from m_flow.auth.methods import get_authenticated_user

    return get_authenticated_user


# ---------------------------------------------------------------------------
# Router Factory
# ---------------------------------------------------------------------------


def get_prompts_router() -> APIRouter:
    """
    Construct prompts management router.

    Endpoints:
        GET /           - List all prompts (grouped by category)
        GET /{filename} - Get single prompt content
        PUT /{filename} - Update prompt content
        POST /{filename}/reset - Reset prompt to default
        POST /reset-all - Reset all prompts to defaults
    """
    router = APIRouter()

    @router.get("", response_model=List[PromptCategoryDTO])
    async def list_prompts(user: "User" = Depends(_auth())):
        """
        List all available prompt templates grouped by category.

        Returns prompts organized into categories like:
        - episodic: Episode/Facet extraction
        - summarize: Summarization tasks
        - extract: Entity/Graph extraction
        - answer: Question answering
        - classify: Content classification
        - procedural: Procedural memory
        """
        _ensure_defaults_backup()
        prompts_path = _get_prompts_path()

        # Collect all prompts
        categories: dict[str, list[PromptListItemDTO]] = {}

        for prompt_file in sorted(prompts_path.glob("*.txt")):
            filename = prompt_file.name
            # Skip benchmark files
            if "benchmark" in filename.lower():
                continue

            category = _categorize_prompt(filename)

            prompt_item = PromptListItemDTO(
                name=prompt_file.stem,
                filename=filename,
                category=category,
                description=_get_prompt_description(filename),
                is_modified=_is_prompt_modified(filename),
            )

            if category not in categories:
                categories[category] = []
            categories[category].append(prompt_item)

        # Convert to list of category DTOs
        result = [PromptCategoryDTO(category=cat, prompts=prompts) for cat, prompts in sorted(categories.items())]

        return result

    @router.get("/{filename}", response_model=PromptDTO)
    async def get_prompt(
        filename: str,
        user: "User" = Depends(_auth()),
    ):
        """
        Get a single prompt template by filename.

        Args:
            filename: Prompt filename (with .txt extension)

        Returns:
            PromptDTO with full content
        """
        # Validate and sanitize filename (security: prevent path traversal)
        filename = _validate_filename(filename)

        _ensure_defaults_backup()
        prompts_path = _get_prompts_path()
        prompt_file = prompts_path / filename

        if not prompt_file.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prompt not found: {filename}")

        try:
            content = prompt_file.read_text(encoding="utf-8")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to read prompt: {e}")

        return PromptDTO(
            name=prompt_file.stem,
            filename=filename,
            category=_categorize_prompt(filename),
            content=content,
            description=_get_prompt_description(filename),
            is_modified=_is_prompt_modified(filename),
        )

    @router.put("/{filename}", response_model=PromptDTO)
    async def update_prompt(
        filename: str,
        payload: PromptUpdateDTO,
        user: "User" = Depends(_auth()),
    ):
        """
        Update a prompt template's content.

        Args:
            filename: Prompt filename
            payload: New prompt content

        Returns:
            Updated PromptDTO
        """
        # Validate and sanitize filename (security: prevent path traversal)
        filename = _validate_filename(filename)

        _ensure_defaults_backup()
        prompts_path = _get_prompts_path()
        prompt_file = prompts_path / filename

        if not prompt_file.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prompt not found: {filename}")

        try:
            prompt_file.write_text(payload.content, encoding="utf-8")
            _log.info(f"Updated prompt: {filename}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to write prompt: {e}"
            )

        return PromptDTO(
            name=prompt_file.stem,
            filename=filename,
            category=_categorize_prompt(filename),
            content=payload.content,
            description=_get_prompt_description(filename),
            is_modified=_is_prompt_modified(filename),
        )

    @router.post("/{filename}/reset", response_model=PromptDTO)
    async def reset_prompt(
        filename: str,
        user: "User" = Depends(_auth()),
    ):
        """
        Reset a prompt to its default content.

        Args:
            filename: Prompt filename

        Returns:
            Reset PromptDTO with default content
        """
        # Validate and sanitize filename (security: prevent path traversal)
        filename = _validate_filename(filename)

        _ensure_defaults_backup()
        prompts_path = _get_prompts_path()
        defaults_path = _get_defaults_path()

        prompt_file = prompts_path / filename
        default_file = defaults_path / filename

        if not prompt_file.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prompt not found: {filename}")

        if not default_file.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Default not found for: {filename}")

        try:
            default_content = default_file.read_text(encoding="utf-8")
            prompt_file.write_text(default_content, encoding="utf-8")
            _log.info(f"Reset prompt to default: {filename}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to reset prompt: {e}"
            )

        return PromptDTO(
            name=prompt_file.stem,
            filename=filename,
            category=_categorize_prompt(filename),
            content=default_content,
            description=_get_prompt_description(filename),
            is_modified=False,
        )

    @router.post("/reset-all", response_model=dict)
    async def reset_all_prompts(user: "User" = Depends(_auth())):
        """
        Reset all prompts to their default values.

        Returns:
            Summary of reset operation
        """
        _ensure_defaults_backup()
        prompts_path = _get_prompts_path()
        defaults_path = _get_defaults_path()

        reset_count = 0
        errors = []

        for default_file in defaults_path.glob("*.txt"):
            try:
                default_content = default_file.read_text(encoding="utf-8")
                target_file = prompts_path / default_file.name
                target_file.write_text(default_content, encoding="utf-8")
                reset_count += 1
            except Exception as e:
                errors.append(f"{default_file.name}: {e}")

        _log.info(f"Reset {reset_count} prompts to defaults")

        return {
            "reset_count": reset_count,
            "errors": errors if errors else None,
            "message": f"Successfully reset {reset_count} prompts to defaults",
        }

    return router
