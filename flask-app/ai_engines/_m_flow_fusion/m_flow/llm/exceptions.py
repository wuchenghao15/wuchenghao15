"""
LLM Module Exceptions
=====================

Exception classes for LLM-related errors including API configuration,
provider compatibility, and content policy violations.
"""

from m_flow.exceptions.exceptions import BadInputError


class ContentPolicyFilterError(BadInputError):
    """
    Raised when content is rejected by the LLM's content policy filter.

    This occurs when the input or generated output violates the
    provider's usage policies.
    """

    pass


class LLMAPIKeyNotSetError(BadInputError):
    """
    Raised when the required LLM API key is missing from configuration.

    Ensure the appropriate API key environment variable is set
    (e.g., OPENAI_API_KEY, ANTHROPIC_API_KEY).
    """

    ERROR_NAME = "LLMAPIKeyNotSetError"
    DEFAULT_MESSAGE = "LLM API key is not configured."

    def __init__(self, message: str = DEFAULT_MESSAGE):
        super().__init__(message, self.ERROR_NAME)


class UnsupportedLLMProviderError(BadInputError):
    """
    Raised when attempting to use an LLM provider that is not supported.

    Check the supported providers list in the documentation.
    """

    ERROR_NAME = "UnsupportedLLMProviderError"

    def __init__(self, provider: str):
        error_msg = f"LLM provider '{provider}' is not supported."
        super().__init__(error_msg, self.ERROR_NAME)


class MissingSystemPromptPathError(BadInputError):
    """
    Raised when no system prompt file path is specified.

    A system prompt is required for most LLM operations to guide
    the model's behavior and response format.
    """

    ERROR_NAME = "MissingSystemPromptPathError"
    DEFAULT_MESSAGE = "System prompt path is required but not provided."

    def __init__(self, name: str = ERROR_NAME):
        super().__init__(self.DEFAULT_MESSAGE, name)
