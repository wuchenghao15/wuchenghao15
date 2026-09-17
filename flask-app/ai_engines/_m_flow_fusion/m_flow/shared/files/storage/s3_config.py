"""
S3 and AWS configuration management.

Provides settings for AWS/S3-compatible storage services,
loaded from environment variables and .env files.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings
from m_flow.config.env_compat import MflowSettings, SettingsConfigDict


class S3Config(MflowSettings):
    """
    Configuration for S3-compatible object storage.

    All fields are optional. When not explicitly set, the underlying
    AWS SDK (boto3/s3fs) uses its standard credential resolution:
    environment variables, instance profiles, credential files, etc.

    Attributes:
        aws_region: AWS region identifier (e.g., "us-east-1").
        aws_endpoint_url: Custom S3-compatible endpoint URL.
        aws_access_key_id: AWS access key for authentication.
        aws_secret_access_key: AWS secret key for authentication.
        aws_session_token: Temporary session token for assumed roles.
        aws_profile_name: Named profile from AWS credentials file.
        aws_bedrock_runtime_endpoint: Custom Bedrock runtime endpoint.
    """

    model_config = SettingsConfigDict(
        env_prefix="MFLOW_",
        env_file=".env",
        extra="allow",
    )

    aws_region: Optional[str] = Field(
        default=None,
        description="AWS region name",
    )

    aws_endpoint_url: Optional[str] = Field(
        default=None,
        description="Custom S3 endpoint URL",
    )

    aws_access_key_id: Optional[str] = Field(
        default=None,
        description="AWS access key",
    )

    aws_secret_access_key: Optional[str] = Field(
        default=None,
        description="AWS secret key",
    )

    aws_session_token: Optional[str] = Field(
        default=None,
        description="Session token for temporary credentials",
    )

    aws_profile_name: Optional[str] = Field(
        default=None,
        description="Named AWS profile",
    )

    aws_bedrock_runtime_endpoint: Optional[str] = Field(
        default=None,
        description="Bedrock runtime endpoint URL",
    )


@lru_cache(maxsize=1)
def get_s3_config() -> S3Config:
    """
    Retrieve the cached S3 configuration singleton.

    Returns:
        S3Config instance loaded from environment.
    """
    return S3Config()


def reset_s3_config() -> None:
    """Clear the configuration cache (for testing)."""
    get_s3_config.cache_clear()
