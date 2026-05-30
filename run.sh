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

# Use 1234 in the main repo; pick a random free port in a worktree (.git is a file, not a dir)
if [ -f ".git" ]; then
    PORT=$(python3 -c "import socket; s=socket.socket(); s.bind(('',0)); print(s.getsockname()[1]); s.close()")
else
    PORT=1234
fi
echo "Starting on port $PORT"

# Change to backend directory and start the server
cd backend && uv run uvicorn app:app --reload --port "$PORT"
