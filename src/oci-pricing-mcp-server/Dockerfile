FROM python:3.11-slim@sha256:6d85378d88a19cd4d76079817532d62232be95757cb45945a99fec8e8084b9c2
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir uv && \
    uv --no-cache sync --locked --all-extras && \
    useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser && \
    chown -R appuser:appuser /app
USER appuser
CMD ["uv", "run",  "oci-pricing-mcp-server.py"]
