FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install -U pip && pip install fastmcp httpx
CMD ["python", "src/oci-pricing-mcp-server/oci-pricing-mcp-server.py"]
