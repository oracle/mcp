# ---------- 1) Build stage ----------
FROM maven:3.9.12-eclipse-temurin-17@sha256:a0603aab698040d9c94259f379ec0487da1678560748d6c7508483034033c53d AS builder

WORKDIR /src

COPY . .

RUN mvn -B -q -DskipTests clean package

# ---------- 2) Runtime stage ----------
FROM container-registry.oracle.com/java/openjdk:17@sha256:854a4b5d81a6962f589c86e96f65500d9f1f151d7fbcb4bb0d90020f581bdfdb

RUN useradd -r -u 10001 appuser && \
    mkdir -p /app /ext && chown -R appuser:appuser /app /ext

WORKDIR /app
USER appuser

COPY --from=builder /src/target/oracle-db-mcp-toolkit-*.jar \
     /app/oracle-db-mcp-toolkit.jar

ENTRYPOINT ["java", "-jar", "/app/oracle-db-mcp-toolkit.jar"]
