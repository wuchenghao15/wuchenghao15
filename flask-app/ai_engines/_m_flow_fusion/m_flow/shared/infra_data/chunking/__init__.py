# m_flow.shared.infra_data.chunking
# Pluggable text segmentation backends for the m_flow ingestion pipeline.
#
# Supported backends are resolved at runtime via *create_chunking_engine*
# so the caller never depends on a concrete implementation directly.
#
# Available engines:
#   - DefaultChunkEngine    (regex / sentence / paragraph)
#   - LangchainChunkEngine  (RecursiveCharacterTextSplitter)
#   - HaystackChunkEngine   (Haystack document splitter)

_CHUNKING_PKG = "m_flow.shared.infra_data.chunking"
