"""
Data type classification for ingestion.

Routes incoming data to appropriate DataType wrappers based on type.
"""

from __future__ import annotations

from io import BufferedReader
from os import path
from tempfile import SpooledTemporaryFile
from typing import BinaryIO, Union

from m_flow.ingestion.core.exceptions import IngestionError
from .data_types import BinaryData, S3BinaryData, TextData


def classify(data: Union[str, BinaryIO], filename: str | None = None):
    """
    Classify input data and wrap in appropriate DataType.

    Args:
        data: Raw input - string or binary file object.
        filename: Optional explicit filename for binary data.

    Returns:
        TextData, BinaryData, or S3BinaryData instance.

    Raises:
        IngestionError: If data type is not supported.
    """
    # String input → TextData
    if isinstance(data, str):
        return TextData(data)

    # Local binary file → BinaryData
    if isinstance(data, (BufferedReader, SpooledTemporaryFile)):
        name = filename or str(data.name).rsplit("/", 1)[-1]
        return BinaryData(data, name)

    # S3 file → S3BinaryData (optional dependency)
    try:
        from s3fs import S3File
    except ImportError:
        S3File = None

    if S3File is not None and isinstance(data, S3File):
        s3_uri = path.join("s3://", data.bucket, data.key)
        return S3BinaryData(s3_path=s3_uri, name=data.key)

    raise IngestionError(message=f"Unsupported data type for classify(): {type(data).__name__}")
