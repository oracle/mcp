# ---------- 1) Build stage ----------
FROM container-registry.oracle.com/java/openjdk:17 AS builder

ARG MAVEN_VERSION=3.9.11
ARG MAVEN_BASE_URL=https://archive.apache.org/dist/maven/maven-3

RUN curl -fsSL \
      ${MAVEN_BASE_URL}/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz \
      -o /tmp/maven.tar.gz \
  && tar -xzf /tmp/maven.tar.gz -C /opt \
  && ln -s /opt/apache-maven-${MAVEN_VERSION} /opt/maven \
  && rm /tmp/maven.tar.gz

ENV MAVEN_HOME=/opt/maven
ENV PATH="${MAVEN_HOME}/bin:${PATH}"

WORKDIR /src

COPY . .

RUN mvn -B -q -DskipTests clean package

# ---------- 2) Runtime stage ----------
FROM container-registry.oracle.com/java/openjdk:17

RUN useradd -r -u 10001 appuser && \
    mkdir -p /app /ext && chown -R appuser:appuser /app /ext

WORKDIR /app
USER appuser

COPY --from=builder /src/target/oracle-db-mcp-toolkit-*.jar \
     /app/oracle-db-mcp-toolkit.jar

ENTRYPOINT ["java", "-jar", "/app/oracle-db-mcp-toolkit.jar"]
