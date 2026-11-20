#
# Since: August 2025
# Author: Gerald Venzl
# Name: Dockerfile
# Description: Dockerfile to build Docker image
#
# Copyright 2025 Oracle Corporation and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
FROM docker.io/library/python:3.13.18-alpine3.24@sha256:9ef1a599f863231c3d91e941389bfdc4a2d6070557243d54df1a4e57015b960e

ARG DBDOC_SHA256=383e228d3507d394366e204a058ae948ed1b308de1ea76aa4210f72e20074e31
ENV HOME=/app
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.12.1@sha256:cf4eedcaa81655197f625739489effcbe71b61ceb1506f332c3facae5deceded /uv /usr/local/bin/uv
COPY oracle-db-doc-mcp-server.py fastmcp.json pyproject.toml uv.lock ./

RUN apk --no-cache add curl && \
    uv sync --locked --no-dev --no-cache --no-python-downloads && \
    mkdir /input && \
    curl -fsSL -o /input/dbdoc.zip https://docs.oracle.com/en/database/oracle/oracle-database/26/zip/oracle-database_26.zip && \
    echo "${DBDOC_SHA256}  /input/dbdoc.zip" | sha256sum -c - && \
    /app/.venv/bin/python3 oracle-db-doc-mcp-server.py -log-level DEBUG idx -path /input/dbdoc.zip && \
    rm -r /input && \
    apk del curl && \
    rm -rf /var/cache/apk/* /tmp/*

RUN addgroup -S appuser && \
    adduser -S -G appuser -h /app appuser && \
    chown -R appuser:appuser /app

LABEL org.opencontainers.image.source=https://github.com/oracle/mcp
LABEL org.opencontainers.image.description="Oracle Database Documentation MCP Server"
LABEL org.opencontainers.image.licenses=Apache-2.0

USER appuser

ENTRYPOINT [ "/app/.venv/bin/python3", "oracle-db-doc-mcp-server.py", "mcp" ]
