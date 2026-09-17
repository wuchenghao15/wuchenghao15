"""
Context management utilities for M-flow.

This package provides lightweight context-aware state management for
pipeline operations. The context system allows passing execution state
between pipeline stages without explicit parameter threading.

Architecture Notes
------------------

The context system was simplified in v0.5.0. The previous BaseContextProvider
class has been removed. Context management is now handled through:

1. Python's contextvars for request-scoped state
2. Explicit parameter passing for pipeline configuration
3. Singleton configuration objects for global settings

See Also
--------
m_flow.shared.settings : Global settings management
m_flow.pipeline : Pipeline execution context
"""

# Package marker - no public exports at this level
__all__: list[str] = []

# Version indicator for this module's structure
_CONTEXT_VERSION: str = "2.0"
