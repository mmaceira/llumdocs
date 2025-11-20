# Docker Setup for LlumDocs

This directory contains Docker Compose configurations for different deployment scenarios.

## Prerequisites

### Install Docker Compose

Docker Compose profiles require Docker Compose v2.0+ (plugin version). Install it:

**Option 1: Install Docker Compose plugin (recommended)**
```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Verify installation
docker compose version
```

**Option 2: Install standalone docker-compose (v1)**
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

Note: Standalone docker-compose (v1) doesn't support profiles. You'll need Docker Compose v2+ to use this setup.

## Usage with Profiles (Docker Compose v2+)

### Building Images

**Important:** When the Dockerfile changes (e.g., after adding email intelligence support), rebuild with `--no-cache` to ensure all dependencies are installed:

```bash
cd docker
docker compose --profile cpu --profile ui build --no-cache
```

Then start the services:
```bash
docker compose --profile cpu --profile ui up -d
```

Or build and start in one command:
```bash
cd docker
docker compose --profile cpu --profile ui up --build --no-cache
```

### CPU-only setup
```bash
cd docker
docker compose --profile cpu up --build
```

### GPU setup (requires NVIDIA Container Toolkit)
```bash
cd docker
docker compose --profile gpu up --build
```

### With Gradio UI
```bash
cd docker
docker compose --profile ui up --build
```

### GPU + UI together
```bash
cd docker
docker compose --profile gpu --profile ui up --build
```

### With pre-bundled HuggingFace models (faster first request)
```bash
cd docker
docker compose --profile hf-bundled up --build
```

**Note:** The regular `api` service includes email intelligence support, but models download on first use. The `api-hf` service pre-downloads models during build for faster first requests (but creates a larger image).

## Model Downloads

### Ollama Models (Text & Vision)

Ollama models are **automatically downloaded** when the container starts. The entrypoint script ensures both required models are available:

- `llama3.1:8b` - Text model for translation, summaries, etc.
- `qwen3-vl:8b` - Vision model for image description

Models are stored in the `ollama_models` Docker volume and persist across container restarts. On first start, the download may take 5-10 minutes depending on your connection.

**Manual pull (if needed):**
```bash
# If using docker compose (v2)
docker compose exec ollama ollama pull llama3.1:8b
docker compose exec ollama ollama pull qwen3-vl:8b

# If using docker-compose (v1)
docker-compose exec ollama ollama pull llama3.1:8b
docker-compose exec ollama ollama pull qwen3-vl:8b
```

### HuggingFace Models (Email Intelligence)

Email intelligence models are downloaded **on first use** when using the regular `api` service:

- `MoritzLaurer/bge-m3-zeroshot-v2.0` - Email routing classification
- `cybersectony/phishing-email-detection-distilbert_v2.1` - Phishing detection
- `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual` - Sentiment analysis

Models are cached in the `hf_cache` Docker volume at `/models/hf` and persist across restarts.

**Pre-download models (optional):** Use the `api-hf` service which pre-downloads models during build for faster first requests.

## Access Services

- FastAPI API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Gradio UI: http://localhost:7860
- Ollama (Docker): http://localhost:11435 (or 11434 if host Ollama is not running)

## Environment Configuration

Before starting, ensure you have a `.env` file in the project root:

```bash
cd /path/to/LlumDocs
cp .env.template .env
# Edit .env with your API keys and preferences
```

Key variables:
- `OPENAI_API_KEY` - Your OpenAI API key (optional, if using Ollama only)
- `LLUMDOCS_DEFAULT_MODEL` - Default text model (e.g., `gpt-4o-mini` or `ollama/llama3.1:8b`)
- `LLUMDOCS_DEFAULT_VISION_MODEL` - Default vision model (e.g., `o4-mini` or `ollama/qwen3-vl:8b`)
- `OLLAMA_API_BASE` - Ollama server URL (defaults to `http://ollama:11434` for Docker Ollama, or `http://host.docker.internal:11434` for host Ollama)
- `HF_HOME` - HuggingFace cache directory (defaults to `/models/hf` in containers)

## Using Host Ollama (Recommended)

If you already have Ollama running on your host machine, the Docker services will automatically connect to it via `host.docker.internal:11434`. This avoids port conflicts and lets you use your existing Ollama setup.

To use Docker Ollama instead, set in your `.env`:
```bash
OLLAMA_API_BASE=http://ollama:11434
```

Note: Docker Ollama runs on port 11435 externally to avoid conflicts with host Ollama.

## Troubleshooting

### Port Already in Use

If you get errors like `bind: address already in use`, you have services running on those ports:

**Check what's using the ports:**
```bash
ss -tlnp | grep -E ':(8000|7860|11434)'
```

**Options:**
1. **Stop host services** (if you want to use Docker):
   ```bash
   pkill -f "uvicorn llumdocs"
   pkill -f "llumdocs.ui.main"
   pkill -f "ollama serve"
   ```

2. **Use different ports** - Edit `docker/docker-compose.yml` and change the port mappings:
   ```yaml
   ports:
     - "8001:8000"  # API on 8001 instead of 8000
     - "7861:7860"  # UI on 7861 instead of 7860
   ```

3. **Use host services** - Keep using your existing host services and just use Docker for specific components.

### Docker Ollama Port Conflict

If host Ollama is running on 11434, Docker Ollama will use port 11435. To change this, edit `docker/docker-compose.yml`:
```yaml
ports:
  - "11434:11434"  # Change back if host Ollama is stopped
```

### GPU Runtime Not Found

If you see `unknown or invalid runtime name: nvidia`, see `SETUP_GPU.md` for NVIDIA Container Toolkit installation instructions.

### View Logs

```bash
# All services
docker compose logs

# Specific service
docker compose logs api
docker compose logs ui
docker compose logs ollama

# Follow logs
docker compose logs -f
```

### Rebuilding After Changes

If you modify the Dockerfile or dependencies, rebuild with `--no-cache`:

```bash
cd docker
# Rebuild specific services
docker compose build --no-cache api
docker compose build --no-cache ui

# Rebuild all services
docker compose build --no-cache

# Rebuild and restart
docker compose up --build --no-cache -d
```

### Stop Services

```bash
# Stop but keep containers
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove containers + volumes (⚠️ deletes model caches)
docker compose down -v
```

**Warning:** `docker compose down -v` removes all volumes, including `ollama_models` and `hf_cache`, which means models will need to be re-downloaded on next start.
