"""
Simple example using LiteLLM with Ollama (llama3.1:8b) and OpenAI.

Make sure you have:
1. Ollama installed and running locally
2. llama3.1:8b model pulled: `ollama pull llama3.1:8b`
3. OpenAI API key set in environment variable: OPENAI_API_KEY
"""

import os

from litellm import completion


# Example 1: Using Ollama with llama3.1:8b
def example_ollama():
    """Example using Ollama llama3.1:8b model"""
    print("=" * 50)
    print("Example 1: Using Ollama llama3.1:8b")
    print("=" * 50)

    response = completion(
        model="ollama/llama3.1:8b",
        messages=[{"role": "user", "content": "Explain what LiteLLM is in one sentence."}],
        api_base="http://localhost:11434",  # Default Ollama endpoint
    )

    print(f"Response: {response.choices[0].message.content}\n")
    return response


# Example 2: Using OpenAI
def example_openai():
    """Example using OpenAI (requires OPENAI_API_KEY environment variable)"""
    print("=" * 50)
    print("Example 2: Using OpenAI")
    print("=" * 50)

    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Skipping OpenAI example.")
        return None

    response = completion(
        model="gpt-3.5-turbo",  # or "gpt-4", "gpt-4-turbo", etc.
        messages=[{"role": "user", "content": "Explain what LiteLLM is in one sentence."}],
    )

    print(f"Response: {response.choices[0].message.content}\n")
    return response


# Example 3: Unified interface - try both
def example_unified():
    """Example showing unified interface - same code works with different providers"""
    print("=" * 50)
    print("Example 3: Unified Interface")
    print("=" * 50)

    models = []

    # Add Ollama
    models.append(
        {"name": "Ollama", "model": "ollama/llama3.1:8b", "api_base": "http://localhost:11434"}
    )

    # Add OpenAI if key is available
    if os.getenv("OPENAI_API_KEY"):
        models.append({"name": "OpenAI", "model": "gpt-3.5-turbo", "api_base": None})

    for model_config in models:
        try:
            print(f"\nTrying {model_config['name']}...")
            kwargs = {
                "model": model_config["model"],
                "messages": [{"role": "user", "content": "Say hello in one sentence."}],
            }

            if model_config["api_base"]:
                kwargs["api_base"] = model_config["api_base"]

            response = completion(**kwargs)
            print(f"{model_config['name']} response: {response.choices[0].message.content}")
        except Exception as e:
            print(f"Error with {model_config['name']}: {str(e)}")


if __name__ == "__main__":
    print("\nLiteLLM Setup Example")
    print("=" * 50)
    print("\nThis example demonstrates LiteLLM with:")
    print("- Ollama (llama3.1:8b)")
    print("- OpenAI\n")

    # Run examples
    try:
        print("Running Ollama example...")
        example_ollama()
    except Exception as e:
        print(f"Ollama example failed: {str(e)}")
        print("Make sure Ollama is running: ollama serve")
        print("And the model is pulled: ollama pull llama3.1:8b\n")

    try:
        print("Running OpenAI example...")
        example_openai()
    except Exception as e:
        print(f"OpenAI example failed: {str(e)}\n")

    example_unified()
