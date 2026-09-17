"""
Langchain-based text chunker.

Uses RecursiveCharacterTextSplitter for intelligent splitting.
"""

from __future__ import annotations

from uuid import NAMESPACE_OID, uuid5

from langchain_text_splitters import RecursiveCharacterTextSplitter

from m_flow.adapters.vector import get_vector_provider
from m_flow.ingestion.chunking.Chunker import Chunker
from m_flow.shared.logging_utils import get_logger

from .models.ContentFragment import ContentFragment

logger = get_logger()


class LangchainChunker(Chunker):
    """
    Recursive text splitter using Langchain.

    Splits text at natural boundaries (paragraphs, sentences)
    while respecting size and overlap constraints.
    """

    def __init__(
        self,
        document,
        get_text: callable,
        max_chunk_tokens: int,
        chunk_size: int = 1024,
        chunk_overlap: int = 10,
    ):
        """
        Configure chunker.

        Args:
            document: Source document.
            get_text: Async text generator.
            max_chunk_tokens: Token limit per chunk.
            chunk_size: Target character count.
            chunk_overlap: Overlap characters.
        """
        super().__init__(document, get_text, max_chunk_tokens, chunk_size)

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=lambda t: len(t.split()),
        )

    async def read(self):
        """
        Generate content fragments.

        Yields:
            ContentFragment for each chunk.

        Raises:
            ValueError: If chunk exceeds token limit.
        """
        tokenizer = get_vector_provider().embedding_engine.tokenizer

        async for text_block in self.get_text():
            splits = self._splitter.split_text(text_block)

            for split in splits:
                tokens = tokenizer.count_tokens(split)

                if tokens > self.max_chunk_tokens:
                    raise ValueError(
                        f"Chunk has {tokens} tokens, exceeds limit of {self.max_chunk_tokens}. "
                        f"Reduce chunk_size parameter."
                    )

                yield ContentFragment(
                    id=uuid5(NAMESPACE_OID, split),
                    text=split,
                    word_count=len(split.split()),
                    token_count=tokens,
                    is_part_of=self.document,
                    chunk_index=self.chunk_index,
                    cut_type="recursive",
                    contains=[],
                    metadata={"index_fields": ["text"]},
                )

                self.chunk_index += 1
