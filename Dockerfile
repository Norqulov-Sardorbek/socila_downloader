FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including ffmpeg and clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python optimizations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/downloads /app/outputs

# Set up environment variables with defaults
ENV BOT_TOKEN="your_bot_token_here"
ENV DEBUG="False"
ENV RAILWAY_ENVIRONMENT="True"

# Health check (optional but recommended)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)"

# Run the bot
CMD ["python", "-m", "bot"]