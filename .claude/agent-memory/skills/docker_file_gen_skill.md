# DockerFileGenSkill — Skill Prompt Template

**File**: `docker_file_gen_skill.md`
**Skill**: Generate a complete, Phase-IV-compliant multi-stage Dockerfile and `.dockerignore` for a given component.

---

## Invocation

Invoke this skill with:

```
Use DockerFileGenSkill with the following inputs:
- Component: <backend | frontend>
- Source path: <e.g. src/backend/ or src/frontend/>
- Output path: <e.g. docker/backend/>
- Build args: <any --build-arg values required at image build time>
- Extra context: <any special requirements, e.g. MCP subprocess, nginx SPA config>
```

---

## Input Template

```
COMPONENT: backend | frontend
SOURCE_PATH: src/backend/ | src/frontend/
OUTPUT_PATH: docker/backend/ | docker/frontend/
BUILD_ARGS:
  - VITE_API_BASE_URL=<k8s-internal-service-url>  # frontend only
EXTRA_CONTEXT: <optional — e.g. "MCP subprocess", "nginx SPA routing">
```

---

## Output Format

This skill always produces:

```
[SKILL: DockerFileGenSkill]
Component: <value>
Output files: <Dockerfile path>, <.dockerignore path>

[DOCKERFILE]
<complete multi-stage Dockerfile content — fenced dockerfile block>

[DOCKERIGNORE]
<complete .dockerignore content — fenced text block>

[BUILD COMMAND]
<exact docker build command, copy-pasteable from project root>

[SMOKE TEST]
<docker run command + curl/wget verification>

[SIZE CHECK]
<docker images command + constitutional size limit reminder>
```

---

## Skill Rules

1. **Multi-stage builds only** — Every Dockerfile MUST use at least 2 stages (builder + runtime). No single-stage images.
2. **Non-root user** — Runtime stage MUST create and switch to `appuser` (UID 1000) before CMD.
3. **HEALTHCHECK required** — Every Dockerfile MUST include a `HEALTHCHECK` instruction matching the component's health endpoint.
4. **No secrets in Dockerfile** — Zero hardcoded keys, URLs, passwords. All runtime secrets via environment variables.
5. **Exact base image tags** — NEVER use `latest`. Exact tags: `python:3.11-slim`, `node:20-slim`, `nginx:alpine`.
6. **Backend: python:3.11-slim** — NOT alpine. Required for C extensions in openai-agents SDK.
7. **Frontend: node:20-slim + nginx:alpine** — Vite builds in node:20-slim; nginx:alpine serves static files.
8. **VITE_API_BASE_URL as ARG** — For frontend, `VITE_API_BASE_URL` MUST be declared as `ARG` in the builder stage (Vite bakes at compile time; cannot inject at K8s runtime).
9. **Constitutional size limits** — Backend target <500 MB, Frontend target <300 MB.
10. **Phase III source is read-only** — NEVER suggest edits to `src/backend/` or `src/frontend/`. Output only to `docker/`.

---

## Phase IV Reference Values

| Field | Backend | Frontend |
|-------|---------|----------|
| Base image (build) | `python:3.11-slim` | `node:20-slim` |
| Base image (runtime) | `python:3.11-slim` | `nginx:alpine` |
| Exposed port | `8000` | `80` |
| Health check endpoint | `http://localhost:8000/health` | `http://localhost:80/` |
| Health start-period | `40s` | `10s` |
| Non-root user | `appuser` | `nginx` (built-in) |
| Build command | `pip install --no-cache-dir` | `npm ci && npm run build` |
| Output artifact | Python packages + source | `/build/dist` static assets |
| .dockerignore critical excludes | `__pycache__`, `*.pyc`, `.env`, `*.db` | `node_modules`, `.env`, `dist` |

---

## Full Skill Example

**Invocation:**

```
Use DockerFileGenSkill with the following inputs:
- Component: backend
- Source path: src/backend/
- Output path: docker/backend/
- Build args: none
- Extra context: MCP stdio subprocess (mcp_server.py launched via sys.executable)
```

**Output:**

```
[SKILL: DockerFileGenSkill]
Component: backend
Output files: docker/backend/Dockerfile, docker/backend/.dockerignore

[DOCKERFILE]
```dockerfile
# Stage 1: builder — install all pip dependencies
FROM python:3.11-slim AS builder
WORKDIR /app
COPY src/backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: runtime — minimal image with only installed packages + source
FROM python:3.11-slim AS runtime
WORKDIR /app

# Non-root user (UID 1000) — security best practice
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --no-create-home appuser

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source (includes mcp_server.py for subprocess launch)
COPY src/backend/ .

# Set ownership
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Health check — matches GET /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

[DOCKERIGNORE]
```
__pycache__
*.pyc
*.pyo
*.pyd
.env
.env.*
*.db
*.sqlite
.git
.gitignore
*.md
tests/
.pytest_cache/
*.egg-info/
dist/
build/
```

[BUILD COMMAND]
# Run from project root
docker build -t todo-backend:1.0.0 -f docker/backend/Dockerfile .

[SMOKE TEST]
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="<neon-url>" \
  -e GROQ_API_KEY="<key>" \
  todo-backend:1.0.0 &
sleep 5
curl -s http://localhost:8000/health
# Expected: {"status":"healthy","database":"connected"}

[SIZE CHECK]
docker images todo-backend:1.0.0 --format "{{.Repository}}:{{.Tag}}\t{{.Size}}"
# Constitutional limit: < 500 MB
```
