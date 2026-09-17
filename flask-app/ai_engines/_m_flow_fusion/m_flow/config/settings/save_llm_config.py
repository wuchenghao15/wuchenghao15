# ---------------------------------------------------------------------------
# m_flow.config.settings.save_llm_config
#
# Mutate the global LLM configuration singleton at runtime and persist to .env.
# ---------------------------------------------------------------------------
from __future__ import annotations

from pydantic import BaseModel, Field

from m_flow.llm import get_llm_config
from m_flow.shared.logging_utils import get_logger

_MASK_SENTINEL = "*****"
logger = get_logger("config.save_llm")


class LLMConfigDTO(BaseModel):
    """
    Transfer object carrying an LLM configuration update.

    The ``api_key`` field may contain the masked placeholder returned by
    :func:`get_settings`; in that case the stored key is left untouched.
    """

    api_key: str = Field(default="", description="API key (or masked placeholder)")
    model: str = Field(..., description="Model identifier, e.g. 'gpt-4o'")
    provider: str = Field(..., description="Provider slug, e.g. 'openai'")


async def save_llm_config(dto: LLMConfigDTO, persist: bool = True) -> None:
    """
    Apply *dto* to the active LLM configuration.

    * ``provider`` and ``model`` are always overwritten.
    * ``api_key`` is written **only** when the caller supplies a
      non-empty, non-masked value.

    Args:
        dto: Configuration update data.
        persist: If True, also write changes to .env file for persistence.
    """
    active_cfg = get_llm_config()
    active_cfg.llm_provider = dto.provider
    active_cfg.llm_model = dto.model

    key_is_real = _MASK_SENTINEL not in dto.api_key and dto.api_key.strip()
    if key_is_real:
        active_cfg.llm_api_key = dto.api_key

    # Persist to .env file
    if persist:
        try:
            from m_flow.config.settings.persist_env import persist_llm_config as _persist

            await _persist(
                provider=dto.provider,
                model=dto.model,
                api_key=dto.api_key if key_is_real else None,
            )
            logger.info(f"LLM config persisted: provider={dto.provider}, model={dto.model}")
        except Exception as e:
            logger.warning(f"Failed to persist LLM config to .env: {e}")
            # Don't raise - in-memory config is still updated


# Alias
LLMConfig = LLMConfigDTO
