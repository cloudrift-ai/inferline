FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y curl

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml /app/
RUN pip install --upgrade pip && \
    pip install -e .

# Copy application code
COPY inferline/ /app/inferline/
COPY scripts/ /app/scripts/

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python3", "-m", "inferline.server"]