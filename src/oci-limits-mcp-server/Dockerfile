FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy requirements and install dependencies
COPY requirements.txt pyproject.toml ./
RUN uv pip install --system -r requirements.txt

# Copy source code
COPY oci_limits_mcp_server.py ./

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash oci
RUN chown -R oci:oci /app
USER oci

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import oci_limits_mcp_server; print('OK')"

# Run the server
CMD ["python", "oci_limits_mcp_server.py"]
