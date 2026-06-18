# Stage 1: Build the React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy frontend source
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./

# Build the frontend using Vite
RUN npm run build

# Stage 2: Serve with FastAPI backend
FROM python:3.10-slim
WORKDIR /app

# Install Node.js (needed to run the SSR frontend)
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


# Install backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and data pipeline outputs
COPY backend/ backend/
COPY data/processed/ data/processed/

# Copy the built frontend static files from Stage 1
COPY --from=frontend-builder /app/frontend/.output /app/frontend/.output

# Copy start script
COPY start.sh .
RUN chmod +x start.sh

# Hugging Face Spaces default port is 7860
EXPOSE 7860

# Command to run both servers
CMD ["./start.sh"]
