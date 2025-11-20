# Setting Up GPU Support for LlumDocs

## Prerequisites Check

First, verify you have NVIDIA drivers installed:
```bash
nvidia-smi
```

If this works, you have drivers. Next, check if Docker has NVIDIA runtime:
```bash
docker info | grep -i runtime
```

If you see `nvidia` in the runtimes list, you're all set! If not, follow the installation steps below.

## Quick Start (CPU Mode)

For now, you can run in CPU mode:

```bash
cd docker
docker compose --profile cpu --profile ui up --build
```

Or use the dedicated CPU file:
```bash
docker-compose -f docker-compose.ui.yml up --build
```

## Setting Up GPU Support

To enable GPU acceleration for Ollama, you need to install NVIDIA Container Toolkit:

### Ubuntu/Debian

```bash
# Add NVIDIA's GPG key
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install NVIDIA Container Toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Restart Docker daemon
sudo systemctl restart docker

# Verify installation
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

### After Installation

Once NVIDIA Container Toolkit is installed, you can use GPU mode:

```bash
# Using profiles (requires docker-compose v2)
docker compose --profile gpu --profile ui up --build

# Or use the dedicated GPU file
docker-compose -f docker-compose.gpu-ui.yml up --build
```

## Verify GPU Access

After starting with GPU support, verify Ollama can see the GPU:

```bash
docker compose exec ollama ollama run llama3.1:8b "test"
# Or
docker-compose -f docker-compose.gpu-ui.yml exec ollama ollama run llama3.1:8b "test"
```

If GPU is working, you should see faster inference times.

## Troubleshooting GPU Issues

### Error: "unknown or invalid runtime name: nvidia"

This means NVIDIA Container Toolkit is not installed. Follow the installation steps above.

### Error: "could not select device driver"

This usually means:
1. NVIDIA drivers are not installed - run `nvidia-smi` to check
2. Docker daemon needs restart after installing NVIDIA Container Toolkit:
   ```bash
   sudo systemctl restart docker
   ```

### GPU Not Being Used

Even with GPU runtime, Ollama might use CPU if:
1. The model is too small for GPU acceleration
2. GPU memory is insufficient
3. Ollama is configured to use CPU

Check GPU usage:
```bash
# In another terminal, watch GPU usage
watch -n 1 nvidia-smi

# Then run a model in Ollama
docker compose exec ollama ollama run llama3.1:8b "Write a story"
```

If GPU memory usage increases, GPU is working!

### Using Host Ollama with GPU

If you're using host Ollama (not Docker Ollama), GPU support depends on how Ollama was installed on the host. Host Ollama will automatically use GPU if:
- NVIDIA drivers are installed
- Ollama was installed with GPU support
- GPU is available

The Docker services can connect to host Ollama with GPU support - just ensure `OLLAMA_API_BASE=http://host.docker.internal:11434` in your `.env`.
