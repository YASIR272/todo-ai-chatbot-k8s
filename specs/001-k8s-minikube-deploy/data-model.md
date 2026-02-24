# Data Model: Phase IV – Local Kubernetes Deployment

**Feature**: 001-k8s-minikube-deploy
**Date**: 2026-02-23

> This file describes the **infrastructure entities** for Phase IV. Application
> data models (Task, Conversation, Message) remain unchanged from Phase III and
> are defined in `src/backend/models.py`.

---

## Infrastructure Entities

### 1. Docker Image: `todo-backend`

| Attribute | Value |
|-----------|-------|
| Build context | Project root (`E:\...\`) |
| Dockerfile | `docker/backend/Dockerfile` |
| Base image (builder) | `python:3.11-slim` |
| Base image (runtime) | `python:3.11-slim` |
| Exposed port | `8000` |
| Container user | `appuser` (non-root, UID 1000) |
| WORKDIR | `/app` |
| Target size | < 500 MB |
| Tag convention | `todo-backend:1.0.0` |
| Health check | `HEALTHCHECK CMD curl -f http://localhost:8000/health` |
| Entry point | `uvicorn main:app --host 0.0.0.0 --port 8000` |

**Source files included**:
- `src/backend/*.py` → `/app/`
- `src/backend/routes/` → `/app/routes/`
- `src/backend/tests/` → `/app/tests/`
- `src/backend/requirements.txt` → `/app/requirements.txt`

**Files excluded** (via `.dockerignore`):
- `__pycache__/`, `*.pyc`, `*.pyo`
- `.env`, `.env.*`
- `*.db`, `*.sqlite`
- `.venv/`, `venv/`
- `tests/` (optional — tests are not needed at runtime)
- `.git/`, `.gitignore`

---

### 2. Docker Image: `todo-frontend`

| Attribute | Value |
|-----------|-------|
| Build context | `src/frontend/` |
| Dockerfile | `docker/frontend/Dockerfile` |
| Base image (builder) | `node:20-slim` |
| Base image (runtime) | `nginx:alpine` |
| Exposed port | `80` |
| Container user | `nginx` (default nginx user) |
| WORKDIR (builder) | `/build` |
| WORKDIR (runtime) | `/usr/share/nginx/html` |
| Target size | < 300 MB |
| Tag convention | `todo-frontend:1.0.0` |
| Build ARG | `VITE_API_BASE_URL=http://todo-chatbot-backend:8000` |
| Entry point | nginx default (`nginx -g "daemon off;"`) |

**Build stages**:
1. **builder**: `npm ci` → `npm run build` → produces `dist/`
2. **runtime**: Copy `dist/` → nginx html root; copy `nginx.conf`

**Files excluded** (via `.dockerignore`):
- `node_modules/`
- `.git/`, `.gitignore`
- `*.local`, `.env*`
- `dist/` (rebuilt inside Docker)

---

### 3. Helm Chart: `todo-chatbot`

| Attribute | Value |
|-----------|-------|
| Chart name | `todo-chatbot` |
| Chart version | `0.1.0` |
| App version | `2.0.0` |
| Location | `helm/todo-chatbot/` |
| Kubernetes API | `v1`, `apps/v1` |
| Helm version | `>=3.0.0` |
| Namespace | `default` |

**Chart structure**:
```
helm/todo-chatbot/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── _helpers.tpl          (optional — name helpers)
    ├── backend-deployment.yaml
    ├── backend-service.yaml
    ├── frontend-deployment.yaml
    ├── frontend-service.yaml
    ├── configmap.yaml
    └── secret.yaml
```

---

### 4. K8s Deployment: `todo-chatbot-backend`

| Attribute | Value |
|-----------|-------|
| Kind | `Deployment` |
| Name template | `{{ .Release.Name }}-backend` |
| Image | `{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}` |
| imagePullPolicy | `Never` (local Minikube image) |
| Container port | `8000` |
| Replicas | `{{ .Values.backend.replicaCount }}` (default: 1) |
| Liveness probe | `httpGet /health :8000`, delay 30s, period 10s |
| Readiness probe | `httpGet /health :8000`, delay 15s, period 5s |
| Resource requests | `cpu: 200m, memory: 256Mi` |
| Resource limits | `cpu: 500m, memory: 512Mi` |
| Env from ConfigMap | `todo-chatbot-config` → HOST, PORT, FRONTEND_ORIGIN, etc. |
| Env from Secret | `todo-chatbot-secret` → DATABASE_URL, GROQ_API_KEY, etc. |

---

### 5. K8s Deployment: `todo-chatbot-frontend`

| Attribute | Value |
|-----------|-------|
| Kind | `Deployment` |
| Name template | `{{ .Release.Name }}-frontend` |
| Image | `{{ .Values.frontend.image.repository }}:{{ .Values.frontend.image.tag }}` |
| imagePullPolicy | `Never` (local Minikube image) |
| Container port | `80` |
| Replicas | `{{ .Values.frontend.replicaCount }}` (default: 1) |
| Liveness probe | `httpGet / :80`, delay 5s, period 10s |
| Readiness probe | `httpGet / :80`, delay 3s, period 5s |
| Resource requests | `cpu: 50m, memory: 64Mi` |
| Resource limits | `cpu: 100m, memory: 128Mi` |

---

### 6. K8s Service: `todo-chatbot-backend`

| Attribute | Value |
|-----------|-------|
| Kind | `Service` |
| Type | `ClusterIP` |
| Port | `8000` |
| Selector | `app: todo-chatbot-backend` |
| DNS name | `todo-chatbot-backend.default.svc.cluster.local` (shortform: `todo-chatbot-backend`) |

---

### 7. K8s Service: `todo-chatbot-frontend`

| Attribute | Value |
|-----------|-------|
| Kind | `Service` |
| Type | `NodePort` |
| Port | `80` |
| NodePort | auto-assigned (or `{{ .Values.frontend.service.nodePort }}` if set) |
| Selector | `app: todo-chatbot-frontend` |
| Access | `minikube service todo-chatbot-frontend --url` |

---

### 8. K8s ConfigMap: `todo-chatbot-config`

| Key | Source Value | Notes |
|-----|-------------|-------|
| `HOST` | `0.0.0.0` | Backend bind address |
| `PORT` | `8000` | Backend bind port |
| `FRONTEND_ORIGIN` | `http://localhost` | CORS origin (Minikube NodePort URL) |
| `CORS_ORIGINS` | `""` | Additional CORS origins |
| `LLM_PROVIDER` | `""` | Auto-detect from API keys |
| `GROQ_MODEL` | `meta-llama/llama-4-scout-17b-16e-instruct` | Default Groq model |

---

### 9. K8s Secret: `todo-chatbot-secret`

| Key | Source | Notes |
|-----|--------|-------|
| `DATABASE_URL` | `{{ .Values.secrets.databaseUrl \| b64enc }}` | Neon PostgreSQL URL |
| `GROQ_API_KEY` | `{{ .Values.secrets.groqApiKey \| b64enc }}` | Groq API key |
| `OPENAI_API_KEY` | `{{ .Values.secrets.openaiApiKey \| b64enc }}` | OpenAI API key |
| `BETTER_AUTH_SECRET` | `{{ .Values.secrets.betterAuthSecret \| b64enc }}` | JWT signing secret |

> **Note**: `values.yaml` ships with empty or placeholder defaults. Real values
> MUST be supplied at `helm install` time via `--set` flags or a local
> `values.override.yaml` file that is gitignored.

---

## Application Data Models (Phase III — unchanged)

These live in `src/backend/models.py` and are persisted in Neon PostgreSQL.
They are included here for reference only — **no changes to these models**.

### Task

| Field | Type | Notes |
|-------|------|-------|
| `id` | int (PK, auto) | |
| `title` | str | Required |
| `description` | str \| None | Optional |
| `completed` | bool | Default: False |
| `priority` | str | Default: "medium" |
| `user_id` | str | Required — per-user isolation |
| `created_at` | datetime | Auto UTC |
| `updated_at` | datetime | Auto UTC |

### Conversation

| Field | Type | Notes |
|-------|------|-------|
| `id` | int (PK, auto) | |
| `user_id` | str | Required |
| `created_at` | datetime | Auto UTC |

### Message

| Field | Type | Notes |
|-------|------|-------|
| `id` | int (PK, auto) | |
| `conversation_id` | int (FK → Conversation) | |
| `role` | str | "user" or "assistant" |
| `content` | str | Message text |
| `created_at` | datetime | Auto UTC |
