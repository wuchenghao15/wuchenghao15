"""
API Data Transfer Objects
=========================

Foundation classes for M-flow's API request/response models.
These base classes provide consistent serialization behavior
across all API endpoints.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


def _make_dto_config() -> ConfigDict:
    """Create configuration for DTO models with camelCase aliasing."""
    return ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class OutDTO(BaseModel):
    """
    Foundation for API response payloads.

    Inheriting from this class ensures:
    - Automatic snake_case to camelCase conversion in JSON
    - Consistent serialization across all responses

    Example
    -------
    >>> class UserResponse(OutDTO):
    ...     user_name: str
    ...     created_at: datetime
    """

    model_config = _make_dto_config()


class InDTO(BaseModel):
    """
    Foundation for API request payloads.

    Inheriting from this class ensures:
    - Accepts both camelCase and snake_case in requests
    - Consistent validation across all endpoints

    Example
    -------
    >>> class CreateUserRequest(InDTO):
    ...     user_name: str
    ...     email: str
    """

    model_config = _make_dto_config()
