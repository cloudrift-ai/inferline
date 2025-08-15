FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y curl

# Create app directory
WORKDIR /app

# Copy application code and requirements
COPY pyproject.toml /app/
COPY inferline/ /app/inferline/

# Install Python dependencies after copying code
RUN pip install --upgrade pip && \
    pip install -e .

# Create logs directory
RUN mkdir -p /app/logs

# Default command (uses console script entry point)
CMD ["inferline-openai-provider"]