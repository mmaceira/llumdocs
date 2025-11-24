# LiteLLM Setup Example

This folder contains a simple example setup for using LiteLLM with Ollama (llama3.1:8b, qwen3-vl:8b) and OpenAI.

> ✅ For end-to-end project installation (Python env, LiteLLM providers, environment variables), follow `docs/INSTALL.md`. The instructions below focus only on the helper scripts that live in this folder.

## Usage

### Running the Scripts

Run the basic example script:
```bash
python example_litellm.py
```

Run the Gradio web interface:
```bash
python example_litellm_gradio.py
```

The Gradio interface will be available at `http://localhost:7860` (or the URL shown in the terminal).

### Calling the Runnables Programmatically

You can also import and use the functions from the example scripts in your own code:

#### Using `example_litellm.py` Functions

```python
from example_litellm import example_ollama, example_openai, example_unified

# Call individual examples
response = example_ollama()  # Returns a LiteLLM response object
response = example_openai()  # Returns a LiteLLM response object or None if API key not set
example_unified()  # Runs examples for all available models
```

Each function:
- **`example_ollama()`**: Calls Ollama with llama3.1:8b model. Returns a `litellm.ModelResponse` object.
- **`example_openai()`**: Calls OpenAI GPT-3.5-turbo (requires `OPENAI_API_KEY`). Returns a `litellm.ModelResponse` object or `None` if API key is not set.
- **`example_unified()`**: Demonstrates the unified interface by trying all available models. Does not return a value.

#### Using `example_litellm_gradio.py` Functions

```python
from example_litellm_gradio import (
    get_available_models,
    chat_with_llm,
    create_gradio_interface
)

# Get list of available models
models = get_available_models()
# Returns: [("Ollama (llama3.1:8b)", "ollama/llama3.1:8b"), ...]

# Chat with a model programmatically
history = []
history, _ = chat_with_llm(
    model_choice="ollama/llama3.1:8b",
    user_message="Hello, how are you?",
    history=history
)
# Returns: (updated_history, empty_message_string)

# Create and launch the Gradio interface
demo = create_gradio_interface()
demo.launch(share=False, server_name="0.0.0.0", server_port=7860)
```

Function details:
- **`get_available_models()`**: Returns a list of tuples `(display_name, model_id)` for all available models based on environment setup.
- **`chat_with_llm(model_choice, user_message, history)`**: Sends a message to the specified model and returns updated chat history. Handles both Ollama and OpenAI models automatically.
- **`create_gradio_interface()`**: Creates and returns a Gradio Blocks interface. Call `.launch()` on the returned object to start the web server.

#### Direct LiteLLM Usage

You can also use LiteLLM directly in your code:

```python
from litellm import completion

# Ollama text model example
# Note: keep_alive=0 unloads the model immediately after inference
response = completion(
    model="ollama/llama3.1:8b",
    messages=[{"role": "user", "content": "Your message here"}],
    api_base="http://localhost:11434",
    keep_alive=0  # Unload model immediately after inference
)
print(response.choices[0].message.content)

# Ollama vision model example (for image description)
# Note: Vision models require image data in the messages
# Note: keep_alive=0 unloads the model immediately after inference
response = completion(
    model="ollama/qwen3-vl:8b",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this image"},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
        ]
    }],
    api_base="http://localhost:11434",
    keep_alive=0  # Unload model immediately after inference
)
print(response.choices[0].message.content)

# OpenAI example
response = completion(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Your message here"}]
)
print(response.choices[0].message.content)
```

## What the Example Shows

1. **Ollama Example**: Uses llama3.1:8b model via Ollama
2. **OpenAI Example**: Uses OpenAI's GPT models (if API key is set)
3. **Unified Interface**: Demonstrates how LiteLLM provides a unified interface for different providers

## LiteLLM Model Format

LiteLLM uses a simple format to specify models:
- Ollama (text): `ollama/llama3.1:8b`
- Ollama (vision): `ollama/qwen3-vl:8b`
- OpenAI: `gpt-3.5-turbo`, `gpt-4`, `o4-mini`, etc.

## Configuration

### Ollama Configuration

By default, Ollama runs on `http://localhost:11434`. If you're running it on a different host/port, update the `api_base` parameter:

```python
response = completion(
    model="ollama/llama3.1:8b",
    messages=[...],
    api_base="http://your-ollama-host:port"
)
```

### OpenAI Configuration

OpenAI is configured via environment variable `OPENAI_API_KEY`. LiteLLM will automatically use it.

## Next Steps

- Check out [LiteLLM Documentation](https://docs.litellm.ai/)
- Explore other supported providers
- Set up LiteLLM Proxy for production use
