# ---------- 1) Build stage ----------
FROM eclipse-temurin:17-jdk-jammy AS builder

RUN apt-get update -y \
 && apt-get install -y --no-install-recommends maven ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /src

COPY . .

RUN mvn -B -q -DskipTests clean package

# ---------- 2) Runtime stage ----------
FROM eclipse-temurin:17-jre-jammy

RUN useradd -r -u 10001 appuser && \
    mkdir -p /app /ext && chown -R appuser:appuser /app /ext

WORKDIR /app
USER appuser

COPY --from=builder /src/target/oracle-db-toolbox-mcp-server-*.jar \
     /app/oracle-db-toolbox-mcp-server.jar

ENTRYPOINT ["java", "-jar", "/app/oracle-db-toolbox-mcp-server.jar"]