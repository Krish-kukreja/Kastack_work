#!/bin/bash

# Start the Node.js frontend server in the background on port 3000
echo "Starting Node.js SSR server on port 3000..."
PORT=3000 node frontend/.output/server/index.mjs &

# Start the FastAPI backend server on port 7860
echo "Starting FastAPI backend..."
cd backend
uvicorn app:app --host 0.0.0.0 --port 7860
