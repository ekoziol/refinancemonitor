# Multi-stage Dockerfile for refi_alert
# Matches railway.json NIXPACKS configuration

# Build stage for frontend assets
FROM node:20-slim AS frontend-builder

WORKDIR /app

# Copy frontend package files and install dependencies
COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm install

# Copy frontend source and build (outputs to /app/refi_monitor/static/react/)
COPY frontend/ ./
RUN npm run build

# Build stage for root CSS
FROM node:20-slim AS css-builder

WORKDIR /app

# Copy root package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy CSS source files and config
COPY postcss.config.js ./
COPY tailwind.config.js ./
COPY refi_monitor/static/src/ refi_monitor/static/src/

# Build CSS
RUN npm run build:css

# Final Python runtime stage
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend assets from frontend-builder
COPY --from=frontend-builder /app/refi_monitor/static/react ./refi_monitor/static/react

# Copy built CSS from css-builder
COPY --from=css-builder /app/refi_monitor/static/dist ./refi_monitor/static/dist

# Copy and set up entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose port (Railway uses $PORT env var)
EXPOSE 8080

# Use entrypoint script for startup
ENTRYPOINT ["docker-entrypoint.sh"]
