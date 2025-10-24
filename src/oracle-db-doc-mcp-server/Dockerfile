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
FROM alpine

COPY oracle-db-doc-mcp-server.py fastmcp.json requirements.txt ./

RUN apk --update --no-cache add python3 py3-pip curl && \
    pip install -r requirements.txt --break-system-packages && \
    rm requirements.txt && \
    mkdir /input && \
    curl -L -o /input/dbdoc.zip https://docs.oracle.com/en/database/oracle/oracle-database/26/zip/oracle-database_26.zip && \
    python3 oracle-db-doc-mcp-server.py -log-level DEBUG -doc /input/dbdoc.zip && \
    rm -r /input && \
    apk del curl && \
    rm -rf /var/cache/apk/* /tmp/*

LABEL org.opencontainers.image.source=https://github.com/oracle/mcp
LABEL org.opencontainers.image.description="Oracle Database Documentation MCP Server"
LABEL org.opencontainers.image.licenses=Apache-2.0

ENTRYPOINT [ "python3", "oracle-db-doc-mcp-server.py", "mcp" ]
