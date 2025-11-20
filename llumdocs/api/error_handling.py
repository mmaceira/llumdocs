"""
Standardized error handling for FastAPI endpoints.

This module provides utilities to map service errors to appropriate HTTP status codes:
- Configuration errors (LLMConfigurationError) → 400 Bad Request
- Validation errors (service errors without backend cause) → 400 Bad Request
- Runtime/backend errors → 500 Internal Server Error
"""

from __future__ import annotations

from fastapi import HTTPException, status

from llumdocs.llm import LLMConfigurationError
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


def has_backend_error_cause(exc: Exception) -> bool:
    """
    Check if an exception wraps a backend error (non-configuration error).

    Returns True if the exception has a __cause__ that is not a configuration error.
    This indicates a backend/runtime failure rather than a validation issue.
    """
    cause = getattr(exc, "__cause__", None)
    if cause is None:
        return False
    # If it's a configuration error, it's handled separately
    if isinstance(cause, LLMConfigurationError):
        return False
    # If there's any other exception as cause, it's a backend error
    return isinstance(cause, Exception)


def handle_service_error(exc: Exception, default_message: str = "Service error") -> HTTPException:
    """
    Map a service error to an appropriate HTTP exception.

    Args:
        exc: The service exception to handle.
        default_message: Default message if exception has no message.

    Returns:
        HTTPException with appropriate status code:
        - 400 Bad Request for configuration/validation errors
        - 500 Internal Server Error for runtime/backend errors
    """
    message = str(exc) if str(exc) else default_message

    # Configuration errors always return 400
    if is_configuration_error(exc):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    # Service errors (TextTransformError, TranslationError, ImageDescriptionError)
    # should return 400 for validation errors, 500 for backend errors
    if isinstance(exc, (TextTransformError, TranslationError, ImageDescriptionError)):
        # If it wraps a backend error (non-config), it's a 500
        if has_backend_error_cause(exc):
            return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
        # Otherwise, it's a validation error (no cause or config error cause)
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    # Default to 500 for unknown errors
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
