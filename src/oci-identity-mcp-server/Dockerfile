FROM ghcr.io/oracle/oraclelinux:9-slim

# Install python 3.13
RUN microdnf install epel-release
RUN microdnf install python3.13 python3.13-pip \
  && rm -rf /var/cache/dnf/* \
  && useradd -m -d /app oracle

# Copy the MCP server to the docker container
WORKDIR /app
COPY --chown=oracle:oracle . /app

# Install dependencies
RUN pip3.13 install --upgrade --no-cache-dir pip \
  && pip3.13 install --no-cache-dir uv oci-cli
RUN uv --no-cache lock \
  && uv --no-cache sync --locked --all-extras

# Change user
USER oracle

# Start the MCP server
ENTRYPOINT ["uv", "run"]
CMD ["oracle.oci-identity-mcp-server"]
