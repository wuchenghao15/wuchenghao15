"""
LlamaIndex Data Transformation
==============================

Utilities for extracting file paths from LlamaIndex document objects.
"""

from __future__ import annotations

from typing import Union

from llama_index.core import Document
from llama_index.core.schema import ImageDocument

from m_flow.ingestion.core import save_data_to_file


async def get_data_from_llama_index(
    memory_node: Union[Document, ImageDocument],
) -> str:
    """
    Extract or create a file path from a LlamaIndex document.

    For documents with existing file paths in metadata, returns that path.
    For documents with only text content, saves the content to a new file
    and returns the created file path.

    Parameters
    ----------
    memory_node : Document | ImageDocument
        A LlamaIndex document object to process.

    Returns
    -------
    str
        File system path where the document content is stored.

    Notes
    -----
    Uses strict type checking to distinguish between Document base class
    and its subclasses. Only exact Document or ImageDocument instances
    are processed.
    """
    # Handle standard text documents
    if type(memory_node) is Document:
        existing_path = memory_node.metadata.get("file_path")
        if existing_path is not None:
            return existing_path
        # No existing path - save content to new file
        return await save_data_to_file(memory_node.text)

    # Handle image documents
    if type(memory_node) is ImageDocument:
        if memory_node.image_path is not None:
            return memory_node.image_path
        # No image path - save text content to file
        return await save_data_to_file(memory_node.text)

    # Unsupported document type
    raise TypeError(f"Expected Document or ImageDocument, got {type(memory_node).__name__}")
