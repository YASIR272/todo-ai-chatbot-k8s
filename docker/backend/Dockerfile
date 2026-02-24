# ── Stage 1: builder — install all pip dependencies ──────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /app

# Copy requirements first for layer caching
COPY src/backend/requirements.txt .

# Install to a prefix so only the installed files get copied to runtime stage
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime — minimal image ─────────────────────────────────────────
FROM python:3.11-slim AS runtime
WORKDIR /app

# Non-root user (UID 1000) — security best practice
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --no-create-home appuser

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy full backend source — agent.py, main.py, mcp_server.py must all be present
# because MCPServerStdio launches mcp_server.py as a subprocess via sys.executable
COPY src/backend/ .

# Set ownership
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Health check — targets GET /health endpoint (returns {"status":"healthy","database":"connected"})
# start-period=40s: accounts for Agent startup + MCP subprocess init (5-20s typical)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# mcp_server.py is NOT the entrypoint — it is launched as a subprocess by agent.py
# The single entrypoint is uvicorn; it starts FastAPI which starts the agent which starts MCP
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
