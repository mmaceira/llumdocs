import os


def get_ollama_base() -> str:
    """
    Return the configured Ollama base URL.

    Falls back to localhost for non-Docker local development.
    """
    return os.getenv("OLLAMA_API_BASE", "http://localhost:11434").rstrip("/")
