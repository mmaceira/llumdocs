# LiteLLM Setup Example

This folder contains a simple example setup for using LiteLLM with Ollama (llama3.1:8b) and OpenAI.

## Prerequisites

### 1. Install Ollama

Visit [https://ollama.ai](https://ollama.ai) and install Ollama for your system:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Then pull the llama3.1:8b model:
```bash
ollama pull llama3.1:8b
```

Make sure Ollama is running:
```bash
ollama serve
```

#### Testing Ollama

To verify that Ollama is working correctly:

1. **Check if Ollama is running on the expected port**:
```bash
lsof -i :11434
```
This should show that port 11434 is in use by the Ollama service.

2. **List available models**:
```bash
ollama list
```
This should show `llama3.1:8b` (or any other models you've pulled).

3. **Test the model interactively**:
```bash
ollama run llama3.1:8b
```
This will start an interactive chat session with the model. Type a message and press Enter to test. Type `/bye` or press Ctrl+D to exit.

### 2. OpenAI API Key (Optional)

If you want to use OpenAI, copy the `.env.template` file to `.env` and add your API key:

```bash
cp .env.template .env
```

Then edit `.env` and replace `your-api-key-here` with your actual OpenAI API key.

## Installation

1. Install `uv` (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create a virtual environment and install dependencies:
```bash
uv sync
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

## Usage

Run the example script:
```bash
python example_litellm.py
```

## What the Example Shows

1. **Ollama Example**: Uses llama3.1:8b model via Ollama
2. **OpenAI Example**: Uses OpenAI's GPT models (if API key is set)
3. **Unified Interface**: Demonstrates how LiteLLM provides a unified interface for different providers

## LiteLLM Model Format

LiteLLM uses a simple format to specify models:
- Ollama: `ollama/llama3.1:8b`
- OpenAI: `gpt-3.5-turbo`, `gpt-4`, etc.

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
