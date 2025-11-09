# syntax=docker/dockerfile:1
FROM python:3.13-slim

# Install system dependencies (ffmpeg for audio streaming)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Prevent Python from writing .pyc and enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy requirement file separately to leverage build cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY michelangelo.py main.py README.md entrypoint.sh .env ./
RUN chmod +x entrypoint.sh
# Copy .env only if present (optional) - better to inject via environment instead
# You can pass discord_token via docker run -e discord_token=... or compose file.
 
# # Non-root user for security (optional)
# RUN useradd -m botuser && chown -R botuser:botuser /app
# USER botuser

# Entrypoint
ENTRYPOINT ["./entrypoint.sh"]
