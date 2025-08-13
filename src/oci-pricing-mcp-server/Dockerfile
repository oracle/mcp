FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install -U pip && pip install fastmcp httpx babel pycountry
CMD ["python", "oci-pricing-mcp-server.py"]
