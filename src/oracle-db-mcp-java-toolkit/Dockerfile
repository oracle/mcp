# ---------- 1) Build stage ----------
FROM maven:3.9.12-eclipse-temurin-17@sha256:a0603aab698040d9c94259f379ec0487da1678560748d6c7508483034033c53d AS builder

WORKDIR /src

COPY . .

RUN mvn -B -q -DskipTests clean package

# ---------- 2) Runtime stage ----------
FROM container-registry.oracle.com/java/openjdk:17@sha256:82cc9efbe316236933eb4fb8c0606c536dfbfc545f2e728ebed728b729f3eb1b

RUN useradd -r -u 10001 appuser && \
    mkdir -p /app /ext && chown -R appuser:appuser /app /ext

WORKDIR /app
USER appuser

COPY --from=builder /src/target/oracle-db-mcp-toolkit-*.jar \
     /app/oracle-db-mcp-toolkit.jar

ENTRYPOINT ["java", "-jar", "/app/oracle-db-mcp-toolkit.jar"]
