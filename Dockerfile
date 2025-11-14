FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for unstructured document processing
# Combined RUN commands to reduce layers
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    poppler-utils \
    libreoffice \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip

# Copy requirements first for better Docker layer caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/

# Copy configuration files
COPY config/ ./config/

# Install the package in development mode (allows imports to work cleanly)
RUN pip install --no-cache-dir -e .

# Create necessary directories that might not exist
RUN mkdir -p /app/data/spdata/sp_downloaded_files \
    /app/data/blob-data/blob_downloaded_files \
    /app/chroma_store

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Set Python path
ENV PYTHONPATH=/app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8100

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8100/health || exit 1

# Run the application
CMD ["uvicorn", "agentic_rag.infrastructure.api.main:app", "--host", "0.0.0.0", "--port", "8100"]

