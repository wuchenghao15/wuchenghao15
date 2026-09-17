# ---------------------------------------------------------------------------
# m_flow.config.settings.save_embedding_config
#
# Mutate the global embedding configuration singleton at runtime and persist.
# ---------------------------------------------------------------------------
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from m_flow.shared.logging_utils import get_logger

_MASK_SENTINEL = "*****"
logger = get_logger("config.save_embedding")


class EmbeddingConfigDTO(BaseModel):
    """
    Transfer object carrying an embedding configuration update.

    The ``api_key`` field may contain the masked placeholder;
    in that case the stored key is left untouched.
    """

    api_key: str = Field(default="", description="API key (or masked placeholder)")
    model: str = Field(..., description="Model identifier")
    provider: str = Field(..., description="Provider slug, e.g. 'openai'")
    dimensions: Optional[int] = Field(default=None, description="Vector dimensions")
    endpoint: Optional[str] = Field(default=None, description="Custom API endpoint")


async def save_embedding_config(dto: EmbeddingConfigDTO, persist: bool = True) -> None:
    """
    Apply *dto* to the active embedding configuration.

    * ``provider``, ``model``, and ``dimensions`` are always overwritten.
    * ``api_key`` is written **only** when the caller supplies a
      non-empty, non-masked value.

    Args:
        dto: Configuration update data.
        persist: If True, also write changes to .env file for persistence.
    """
    from m_flow.adapters.vector.embeddings import get_embedding_config

    active_cfg = get_embedding_config()
    active_cfg.embedding_provider = dto.provider
    active_cfg.embedding_model = dto.model

    if dto.dimensions is not None:
        active_cfg.embedding_dimensions = dto.dimensions

    if dto.endpoint:
        active_cfg.embedding_endpoint = dto.endpoint

    key_is_real = _MASK_SENTINEL not in dto.api_key and dto.api_key.strip()
    if key_is_real:
        active_cfg.embedding_api_key = dto.api_key

    # Persist to .env file
    if persist:
        try:
            from m_flow.config.settings.persist_env import persist_env_values

            updates = {
                "EMBEDDING_PROVIDER": dto.provider,
                "EMBEDDING_MODEL": dto.model,
            }
            if dto.dimensions is not None:
                updates["EMBEDDING_DIMENSIONS"] = str(dto.dimensions)
            if dto.endpoint:
                updates["EMBEDDING_ENDPOINT"] = dto.endpoint
            if key_is_real:
                updates["EMBEDDING_API_KEY"] = dto.api_key

            await persist_env_values(updates)
            logger.info(f"Embedding config persisted: provider={dto.provider}, model={dto.model}")
        except Exception as e:
            logger.warning(f"Failed to persist embedding config to .env: {e}")


# Alias
EmbeddingConfig = EmbeddingConfigDTO
