FROM python:3.11-slim

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

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/', timeout=2)"

# Run the Flask frontend
CMD ["python", "-m", "inferline.frontend"]