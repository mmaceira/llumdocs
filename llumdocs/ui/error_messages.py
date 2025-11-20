"""
Error message formatting utilities for UI components.

Provides user-friendly error messages that distinguish between different error types:
- Configuration problems (e.g., missing API keys, invalid model selection)
- Input validation errors (e.g., empty text)
- Model/backend errors (e.g., model refused request, network issues)
- Other runtime errors
"""

from __future__ import annotations

from llumdocs.llm import LLMConfigurationError
from llumdocs.services import EmailIntelligenceError
from llumdocs.services.image_description_service import ImageDescriptionError
from llumdocs.services.text_transform_service import TextTransformError
from llumdocs.services.translation_service import TranslationError


def is_configuration_error(exc: Exception) -> bool:
    """
    Check if an exception is a configuration error by examining the exception chain.

    Returns True if LLMConfigurationError appears anywhere in the exception chain.
    """
    current = exc
    seen = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, LLMConfigurationError):
            return True
        current = getattr(current, "__cause__", None) or getattr(current, "__context__", None)
    return False


def format_error_message(exc: Exception, default_message: str = "An error occurred") -> str:
    """
    Format an exception into a user-friendly error message.

    Args:
        exc: The exception to format.
        default_message: Default message if exception has no message.

    Returns:
        A formatted error message that distinguishes between:
        - Configuration errors: "Configuration error: ..."
        - Input validation errors: "Validation error: ..."
        - Model/backend errors: "Model error: ..." or "Service error: ..."
        - Analysis errors: "Analysis error: ..."
    """
    message = str(exc) if str(exc) else default_message

    # Check if it's a configuration error
    if is_configuration_error(exc):
        return f"Configuration error: {message}"

    # Check for common input validation patterns
    error_lower = message.lower()
    if any(
        phrase in error_lower
        for phrase in [
            "cannot be empty",
            "must not be empty",
            "is required",
            "invalid model selection",
            "must be",
            "must be one of",
            "please upload",
        ]
    ):
        return f"Validation error: {message}"

    # For service-specific errors, check their type
    if isinstance(exc, EmailIntelligenceError):
        # Email intelligence uses Hugging Face models, not LLM
        return f"Analysis error: {message}"

    if isinstance(exc, (TranslationError, TextTransformError, ImageDescriptionError)):
        # These are already wrapped, so check the underlying cause
        if not is_configuration_error(exc):
            # If it's not a config error, it's likely a model/backend issue
            return f"Service error: {message}"

    # Check for model/backend error patterns
    if any(
        phrase in error_lower
        for phrase in [
            "model",
            "llm",
            "request failed",
            "translation failed",
            "description failed",
            "refused",
            "timeout",
            "rate limit",
            "network",
            "connection",
        ]
    ):
        return f"Model error: {message}"

    return message
