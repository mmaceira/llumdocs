#!/bin/bash
set -e

# Start Ollama in the background
echo "Starting Ollama server..."
/bin/ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
for i in {1..60}; do
    if ollama list > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "ERROR: Ollama failed to start after 60 seconds"
        exit 1
    fi
    sleep 1
done

# Function to check if a model exists
model_exists() {
    local model_name=$1
    ollama list 2>/dev/null | awk '{print $1}' | grep -q "^${model_name}$" || return 1
}

# Function to wait for model to be fully downloaded
wait_for_model() {
    local model_name=$1
    echo "Waiting for ${model_name} to be ready..."
    while ! model_exists "$model_name"; do
        sleep 2
    done
    echo "${model_name} is ready!"
}

# Pull models if they don't exist, and wait for completion
echo "Ensuring required models are available..."

if ! model_exists "llama3.1:8b"; then
    echo "Pulling llama3.1:8b (this may take a few minutes)..."
    ollama pull llama3.1:8b
    wait_for_model "llama3.1:8b"
else
    echo "llama3.1:8b already available"
fi

if ! model_exists "qwen3-vl:8b"; then
    echo "Pulling qwen3-vl:8b (this may take several minutes, ~6GB)..."
    ollama pull qwen3-vl:8b
    wait_for_model "qwen3-vl:8b"
else
    echo "qwen3-vl:8b already available"
fi

echo "=========================================="
echo "All models ready!"
echo "Available models:"
ollama list
echo "=========================================="
echo "Ollama is running and ready to serve requests."

# Wait for the Ollama process (this keeps the container running)
wait $OLLAMA_PID
