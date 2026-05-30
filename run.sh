#!/bin/bash

# Create necessary directories
mkdir -p docs 

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo "Error: backend directory not found"
    exit 1
fi

echo "Starting Course Materials RAG System..."
echo "Make sure you have set your ANTHROPIC_API_KEY in .env"

# Pick a random available port (avoid 1234 used by main server)
PORT=$(python3 -c "import socket; s=socket.socket(); s.bind(('',0)); print(s.getsockname()[1]); s.close()")
echo "Starting on port $PORT"

# Change to backend directory and start the server
cd backend && uv run uvicorn app:app --reload --port "$PORT"
