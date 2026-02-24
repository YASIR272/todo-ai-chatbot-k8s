# Research: Phase IV – Local Kubernetes Deployment

**Feature**: 001-k8s-minikube-deploy
**Date**: 2026-02-23
**Status**: Complete — all decisions resolved

---

## D-001 — Backend Base Image

**Decision**: `python:3.11-slim`
**Rationale**: The backend depends on `mcp>=1.0.0`, `openai-agents>=0.9.0`, `passlib[bcrypt]`, and `pyjwt[cryptography]` — all have C extensions requiring compiled binary wheels. `python:3.11-alpine` uses musl libc instead of glibc; many PyPI binary wheels are not published for musl and fall back to source compilation, which is slow, fragile, and increases build time significantly. `python:3.11-slim` (Debian-based) has full glibc compatibility and serves all binary wheels without source compilation.
**Multi-stage approach**: Stage 1 (`builder`) uses `python:3.11-slim` to pip-install all dependencies into a prefix (`/install`). Stage 2 (`runtime`) starts from a fresh `python:3.11-slim`, copies only `/install` and the app source — skipping pip cache, build tools, and headers. Expected image size: 350–450 MB.
**Alternatives considered**:
- `python:3.11-alpine`: Rejected — musl libc incompatibility with binary wheels.
- `python:3.11`: Rejected — full Debian image is ~200 MB larger than slim with no benefit.

---

## D-002 — Frontend Base Images

**Decision**: `node:20-slim` (build stage) + `nginx:alpine` (runtime stage)
**Rationale**: The frontend is a Vite-compiled React SPA. The Node image is only needed to run `npm ci && npm run build`, producing a `dist/` directory of static files. The runtime image is pure nginx serving those static files — no Node required at runtime. `nginx:alpine` is the smallest production-quality web server image (~25 MB). `node:20-slim` provides glibc compatibility for npm native modules.
**Expected sizes**: Node stage ~500 MB (discarded), nginx runtime stage ~50–80 MB total.
**Alternatives considered**:
- `node:20-alpine` for build: Possible but unnecessary since build stage is discarded.
- `node:20` for runtime: Rejected — 500 MB for serving static files is wasteful.
- `caddy:alpine` instead of nginx: Rejected — nginx is more universally familiar and documented.

---

## D-003 — VITE_API_BASE_URL Handling

**Decision**: Pass `VITE_API_BASE_URL` as a Docker `--build-arg` at image build time.
**Context**: Vite replaces `import.meta.env.VITE_*` variables at **build time** (during `npm run build`), not at runtime. The compiled JS bundle contains the literal URL. This means the URL must be known when building the Docker image.
**Implementation**: The frontend Dockerfile accepts `ARG VITE_API_BASE_URL` and passes it to the `npm run build` step as an environment variable. For Minikube deployment, the value is `http://todo-chatbot-backend:8000` — the K8s internal service DNS name for the backend.
**Why this is safe**: The backend service DNS name is not a secret — it is a predictable K8s internal name. It is appropriate to bake it into the image for a local Minikube deployment.
**Trade-off**: The image is tied to the specific backend service name. For a different environment, you would rebuild with a different `--build-arg`. This is acceptable for Phase IV (local only).
**Alternatives considered**:
- nginx `envsubst` at container start: Would require modifying `src/frontend/src/config.ts` to use `window.__BACKEND_URL__` instead of `import.meta.env.VITE_API_BASE_URL` — violates the "no app code changes" constraint.
- Runtime JS injection via nginx `sub_filter`: Complex, fragile, hard to test.

---

## D-004 — Secrets Handling Strategy

**Decision**: Helm `secret.yaml` template with empty defaults in `values.yaml`; real values supplied via `helm install --set` or a gitignored `values.override.yaml`.
**Rationale**: For a local-only Phase IV deployment, a full external secret manager (Vault, AWS Secrets Manager, Sealed Secrets) is disproportionate overhead. The Kubernetes Secret object provides base64 encoding and isolation from ConfigMap. The key security property — no real credentials committed to the repository — is achieved by shipping empty defaults and requiring developers to supply values at install time.
**Workflow**:
```bash
# Option A: --set flags
helm install todo-chatbot helm/todo-chatbot \
  --set secrets.databaseUrl="postgresql://..." \
  --set secrets.groqApiKey="gsk_..."

# Option B: local override file (gitignored)
cp helm/todo-chatbot/values.yaml helm/todo-chatbot/values.override.yaml
# Edit values.override.yaml with real values
helm install todo-chatbot helm/todo-chatbot -f helm/todo-chatbot/values.override.yaml
```
**`values.override.yaml` is listed in `.gitignore`** to prevent accidental commits.
**Alternatives considered**:
- Hardcode in values.yaml: Rejected — violates Constitution Principle IV.
- Sealed Secrets / External Secrets Operator: Rejected — production tooling, out of scope for Phase IV.

---

## D-005 — Image Loading into Minikube

**Decision**: `minikube image load <image>:<tag>` after local `docker build`.
**Rationale**: Minikube with the docker driver on Windows shares the host Docker daemon but has its own image store. `minikube image load` transfers a locally built image into the Minikube VM's container runtime without requiring a registry. Combined with `imagePullPolicy: Never` in Helm templates, K8s will use the loaded image directly.
**Alternative approach (eval docker-env)**: Setting `eval $(minikube docker-env)` before `docker build` builds directly into the Minikube daemon — but this only works in bash/zsh, not PowerShell on Windows. `minikube image load` is cross-platform and more explicit.
**Alternatives considered**:
- Push to Docker Hub: Requires account, internet, public exposure — unnecessary for local.
- Local registry (`minikube addons enable registry`): Adds complexity; `image load` is simpler.

---

## D-006 — Service Type

**Decision**: Backend: `ClusterIP`, Frontend: `NodePort`
**Rationale**: The backend should not be directly accessible from the host — the frontend reaches it via K8s internal DNS (`http://todo-chatbot-backend:8000`). ClusterIP is the correct and secure choice. The frontend needs to be accessible from the host browser. NodePort exposes a port on the Minikube VM's IP, accessible via `minikube service todo-chatbot-frontend --url`. This is the simplest path on Windows without requiring admin rights.
**Minikube service command**: `minikube service todo-chatbot-frontend` opens the URL in the default browser automatically.
**Alternatives considered**:
- LoadBalancer for frontend: Requires `minikube tunnel` which needs elevated privileges on Windows.
- Ingress: Requires `minikube addons enable ingress` and adds DNS complexity — out of scope for Phase IV.

---

## D-007 — Replica Count

**Decision**: `replicaCount: 1` default for both services.
**Rationale**: Phase IV goal is to demonstrate a working local Kubernetes deployment, not production scaling. A single replica per service reduces Minikube resource pressure and simplifies troubleshooting. Scaling can be demonstrated via kubectl-ai: `kubectl-ai "scale the backend deployment to 2 replicas"`.
**The values.yaml default makes scaling trivial**: `helm upgrade todo-chatbot helm/todo-chatbot --set backend.replicaCount=2`

---

## D-008 — Resource Limits

**Decision**:
- Backend: requests `{cpu: 200m, memory: 256Mi}`, limits `{cpu: 500m, memory: 512Mi}`
- Frontend: requests `{cpu: 50m, memory: 64Mi}`, limits `{cpu: 100m, memory: 128Mi}`
**Rationale**: Minikube on Windows 10 with 4 GB allocated RAM must accommodate: Minikube system pods (~500 MB), backend (~256–512 MB), frontend (~64 MB), and headroom. The `openai-agents` SDK loads ML client libraries on startup — 256 MB request is the minimum safe value. The 512 MB limit prevents OOM eviction while allowing normal operation.
**Frontend** nginx is extremely lightweight — 64 MB is generous.

---

## D-009 — Health/Readiness Probes

**Decision**: Both liveness and readiness probes via HTTP GET.
- Backend: target `GET /health` port 8000. The endpoint already exists in `main.py` and performs a `SELECT 1` DB connectivity check, returning `{"status":"healthy","database":"connected"}` (200) or `{"status":"degraded","database":"disconnected"}` (200 with degraded status). For liveness purposes, any 2xx response is acceptable.
- Frontend: target `GET /` port 80. nginx returns 200 for the root path serving `index.html`.
**Timing rationale**: The backend's `startup_agent()` initializes the MCP subprocess and validates the LLM provider — this takes 5–20 seconds. `initialDelaySeconds: 30` for liveness prevents premature restarts during cold start. Readiness uses `initialDelaySeconds: 15` to start accepting traffic slightly sooner.
**Alternatives considered**:
- TCP socket probe: Less informative — doesn't verify DB connectivity or agent startup.
- Startup probe: Would be ideal but adds template complexity; initial delay approach is sufficient for Phase IV.

---

## D-010 — kubectl-ai and Kagent Integration

**Decision**: Document 5 kubectl-ai examples and 2 Kagent examples in the README troubleshooting and AI DevOps sections.
**kubectl-ai usage patterns** (from official docs): Natural language → kubectl command translation.
**Kagent usage patterns**: Agent-based cluster analysis and operations.
**Documented examples**:
1. `kubectl-ai "show me all pods in the default namespace and their status"`
2. `kubectl-ai "describe the todo-chatbot-backend deployment"`
3. `kubectl-ai "scale the backend deployment to 2 replicas"`
4. `kubectl-ai "get the logs of the todo-chatbot-backend pod"`
5. `kubectl-ai "why is my pod in CrashLoopBackOff state"`
6. `kagent run "analyze the health of all pods in default namespace"`
7. `kagent run "list all services and check if they have endpoints"`
