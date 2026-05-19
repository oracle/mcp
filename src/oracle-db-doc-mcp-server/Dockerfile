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
FROM alpine:3.22@sha256:310c62b5e7ca5b08167e4384c68db0fd2905dd9c7493756d356e893909057601

ARG DBDOC_SHA256=383e228d3507d394366e204a058ae948ed1b308de1ea76aa4210f72e20074e31
ENV HOME=/app
WORKDIR /app

COPY oracle-db-doc-mcp-server.py fastmcp.json requirements.txt ./

RUN apk --update --no-cache add python3 py3-pip curl && \
    pip install -r requirements.txt --break-system-packages && \
    rm requirements.txt && \
    mkdir /input && \
    curl -fsSL -o /input/dbdoc.zip https://docs.oracle.com/en/database/oracle/oracle-database/26/zip/oracle-database_26.zip && \
    echo "${DBDOC_SHA256}  /input/dbdoc.zip" | sha256sum -c - && \
    python3 oracle-db-doc-mcp-server.py -log-level DEBUG idx -path /input/dbdoc.zip && \
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

ENTRYPOINT [ "python3", "oracle-db-doc-mcp-server.py", "mcp" ]
