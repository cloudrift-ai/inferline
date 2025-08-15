FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml /app/
RUN pip install --upgrade pip && \
    pip install -e .

# Copy application code
COPY inferline/ /app/inferline/

# Create logs directory
RUN mkdir -p /app/logs

# Default command (uses console script entry point)
CMD ["inferline-openai-provider"]