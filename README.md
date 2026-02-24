# Todo AI Chatbot — Phase IV: Local Kubernetes Deployment

A full-stack Todo AI Chatbot (React/ChatKit frontend + FastAPI/MCP/Agents backend)
containerized with Docker and deployed to a local Minikube cluster via Helm 3.

This is Phase IV of the Hackathon project. The application code is unchanged from
Phase III — this phase is purely infrastructure.

---

## Project Structure

```text
.
├── docker/
│   ├── backend/
│   │   ├── Dockerfile          # Multi-stage: python:3.11-slim + runtime
│   │   └── .dockerignore
│   └── frontend/
│       ├── Dockerfile          # Multi-stage: node:20-slim + nginx:alpine
│       ├── .dockerignore
│       └── nginx.conf          # SPA fallback + static caching
├── helm/
│   └── todo-chatbot/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── backend-deployment.yaml
│           ├── backend-service.yaml
│           ├── frontend-deployment.yaml
│           ├── frontend-service.yaml
│           ├── configmap.yaml
│           └── secret.yaml
├── scripts/
│   └── verify-chatbot.sh       # Automated smoke test
├── src/
│   ├── backend/                # Phase III FastAPI app (READ ONLY)
│   └── frontend/               # Phase III React/ChatKit UI (READ ONLY)
└── specs/
    └── 001-k8s-minikube-deploy/ # Feature spec, plan, tasks, research
```

---

## Phase IV — Kubernetes Deployment Guide

### Prerequisites

Install the following tools before starting:

| Tool | Version | Install |
|------|---------|---------|
| Docker Desktop | Latest | https://www.docker.com/products/docker-desktop |
| Minikube | ≥1.30 | `choco install minikube` or https://minikube.sigs.k8s.io |
| kubectl | ≥1.27 | Bundled with Docker Desktop or `choco install kubernetes-cli` |
| Helm | ≥3.0 | `choco install kubernetes-helm` |
| kubectl-ai | Latest | https://github.com/sozercan/kubectl-ai |
| Kagent | Latest | https://github.com/kagent-dev/kagent |

**Minimum Minikube resources**: 4 GB RAM, 2 CPUs, 20 GB disk.

You will also need:
- A **Neon PostgreSQL** database URL (from Phase III)
- A **Groq API key** (free at https://console.groq.com) or OpenAI API key
- A **JWT secret** string for `BETTER_AUTH_SECRET` (any random string ≥32 chars)

---

### Step 1 — Start Minikube

```bash
minikube start --cpus=2 --memory=4096 --driver=docker
minikube status
```

Expected output:
```
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured
```

---

### Step 2 — Build Docker Images

Run from the **project root**:

```bash
# Backend image (~350–450 MB)
docker build \
  -t todo-backend:1.0.0 \
  -f docker/backend/Dockerfile \
  .

# Frontend image (~50–80 MB)
# VITE_API_BASE_URL is baked into the static JS bundle at build time
docker build \
  --build-arg VITE_API_BASE_URL=http://todo-chatbot-backend:8000 \
  -t todo-frontend:1.0.0 \
  -f docker/frontend/Dockerfile \
  src/frontend/
```

Verify image sizes:
```bash
docker images todo-backend:1.0.0
docker images todo-frontend:1.0.0
# Backend target: < 500 MB  |  Frontend target: < 300 MB
```

> **Why the build-arg?** Vite bakes `VITE_API_BASE_URL` into the JS bundle at
> build time. `http://todo-chatbot-backend:8000` is the Kubernetes internal DNS
> name for the backend service — fixed and not a secret.

---

### Step 3 — Smoke Test Images Locally (Optional)

Before loading into Minikube, verify the images start correctly:

```bash
# Test backend
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="<your-neon-postgresql-url>" \
  -e GROQ_API_KEY="<your-groq-api-key>" \
  todo-backend:1.0.0 &

curl http://localhost:8000/health
# Expected: {"status":"healthy","database":"connected"}
docker stop $(docker ps -q --filter ancestor=todo-backend:1.0.0)

# Test frontend
docker run --rm -p 3000:80 todo-frontend:1.0.0 &
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/
# Expected: 200
docker stop $(docker ps -q --filter ancestor=todo-frontend:1.0.0)
```

---

### Step 4 — Load Images into Minikube

```bash
minikube image load todo-backend:1.0.0
minikube image load todo-frontend:1.0.0

# Verify images are available in Minikube
minikube image ls | grep todo
# Expected: both todo-backend:1.0.0 and todo-frontend:1.0.0 listed
```

> Image loading can take 1–3 minutes per image depending on size and disk speed.

---

### Step 5 — Deploy with Helm

**Option A — `--set` flags (quick)**:
```bash
helm install todo-chatbot helm/todo-chatbot \
  --set secrets.databaseUrl="postgresql://user:password@host/dbname?sslmode=require" \
  --set secrets.groqApiKey="gsk_your_key_here" \
  --set secrets.betterAuthSecret="your-jwt-secret-at-least-32-chars"
```

**Option B — local override file (recommended for repeated use)**:
```bash
# Create a local override (this file is gitignored — never committed)
cp helm/todo-chatbot/values.yaml helm/todo-chatbot/values.override.yaml

# Edit values.override.yaml — fill in the secrets section:
# secrets:
#   databaseUrl: "postgresql://..."
#   groqApiKey: "gsk_..."
#   betterAuthSecret: "my-jwt-secret"

helm install todo-chatbot helm/todo-chatbot \
  -f helm/todo-chatbot/values.override.yaml
```

> **Security**: Never commit real API keys. `values.override.yaml` is gitignored.
> All secrets are injected as Kubernetes Secret objects, never baked into images.

Watch pods come up:
```bash
kubectl get pods --watch
```

Expected (within ~120 seconds):
```
NAME                                      READY   STATUS    RESTARTS   AGE
todo-chatbot-backend-xxxxxxxxx-xxxxx      1/1     Running   0          45s
todo-chatbot-frontend-xxxxxxxxx-xxxxx     1/1     Running   0          45s
```

---

### Step 6 — Access the Chatbot

```bash
minikube service todo-chatbot-frontend
```

This opens the ChatKit UI in your default browser. If it doesn't open automatically:
```bash
minikube service todo-chatbot-frontend --url
# Outputs something like: http://192.168.49.2:31234
# Open that URL manually in your browser
```

---

### Step 7 — Verify End-to-End

1. Open the chatbot URL in your browser.
2. Type: `"Add a task to buy groceries"`
3. Expected: AI agent responds with confirmation; task is created via MCP.
4. Type: `"List all my tasks"`
5. Expected: Task list is returned by the agent.

Or run the automated smoke test:
```bash
bash scripts/verify-chatbot.sh
```

---

### Step 8 — Teardown

```bash
helm uninstall todo-chatbot

# Verify clean removal
kubectl get all
# Only: service/kubernetes (the default K8s service)

# Optional: stop Minikube
minikube stop

# Optional: delete cluster entirely
minikube delete
```

---

## Configuration Reference

All configuration is managed through `helm/todo-chatbot/values.yaml`.

### Helm Values Quick Reference

| Value | Default | Override |
|-------|---------|----------|
| `backend.replicaCount` | `1` | `--set backend.replicaCount=2` |
| `backend.image.tag` | `1.0.0` | `--set backend.image.tag=1.0.1` |
| `frontend.replicaCount` | `1` | `--set frontend.replicaCount=2` |
| `frontend.image.tag` | `1.0.0` | `--set frontend.image.tag=1.0.1` |
| `config.groqModel` | `meta-llama/llama-4-scout-17b-16e-instruct` | `--set config.groqModel=...` |
| `config.llmProvider` | `` (auto-detect) | `--set config.llmProvider=groq` |
| `secrets.databaseUrl` | `` | `--set secrets.databaseUrl=...` |
| `secrets.groqApiKey` | `` | `--set secrets.groqApiKey=...` |
| `secrets.openaiApiKey` | `` | `--set secrets.openaiApiKey=...` |
| `secrets.betterAuthSecret` | `` | `--set secrets.betterAuthSecret=...` |

### Architecture Notes

- **Backend container**: Runs TWO processes — `uvicorn` (FastAPI on port 8000) and
  `mcp_server.py` (MCP stdio subprocess launched by `agent.py` at startup). Both live
  in the same container. No separate MCP deployment is needed.
- **Backend service**: `ClusterIP` — internal only, not accessible from outside the cluster.
- **Frontend service**: `NodePort` — accessible from the host via `minikube service`.
- **Database**: External Neon PostgreSQL. Pod restarts do not lose data.
- **Secrets**: Injected as Kubernetes Secret objects via `envFrom`. Never in images.

---

## AI-Assisted Operations

### kubectl-ai Examples

[kubectl-ai](https://github.com/sozercan/kubectl-ai) lets you interact with your
cluster using natural language.

```bash
# List all pods and their status
kubectl-ai "show me all pods in the default namespace and their status"

# Describe the backend deployment
kubectl-ai "describe the todo-chatbot-backend deployment"

# Scale backend to 2 replicas
kubectl-ai "scale the todo-chatbot-backend deployment to 2 replicas"

# Get backend logs
kubectl-ai "get the logs of the todo-chatbot-backend pod"

# Debug a crashing pod
kubectl-ai "why is my pod in CrashLoopBackOff state"
```

### Kagent Examples

[Kagent](https://github.com/kagent-dev/kagent) provides agentic Kubernetes operations.

```bash
# Analyze cluster health
kagent run "analyze the health of all pods in the default namespace"

# List services and check endpoints
kagent run "list all services and check if they have endpoints"
```

---

## Troubleshooting

### Pods stuck in `Pending`

```bash
kubectl describe pod <pod-name>
# Look for: "Insufficient memory" or "Insufficient cpu"
```

Fix: Increase Minikube resources.
```bash
minikube stop
minikube start --cpus=2 --memory=6144 --driver=docker
```

### Pods in `CrashLoopBackOff`

```bash
kubectl logs <pod-name>
# Check for: missing env var, DB connection error, missing API key
```

AI-assisted debug:
```bash
kubectl-ai "why is my pod in CrashLoopBackOff state"
kubectl-ai "get the logs of the todo-chatbot-backend pod"
```

Common causes:
- `DATABASE_URL` not set or Neon DB unreachable → check secret value
- `GROQ_API_KEY` missing → chat fails at startup health check
- MCP subprocess port conflict → should not happen (stdio, not TCP)

### Image not found (`ErrImagePull` or `ImagePullBackOff`)

```bash
kubectl describe pod <pod-name>
# Verify: imagePullPolicy: Never is set
minikube image ls | grep todo
# If not listed, re-run:
minikube image load todo-backend:1.0.0
minikube image load todo-frontend:1.0.0
```

### `minikube image load` is slow or fails

Large images (backend ~400 MB) can take several minutes. If the load fails:
```bash
# Alternative: build inside Minikube's Docker daemon
eval $(minikube docker-env)
docker build -t todo-backend:1.0.0 -f docker/backend/Dockerfile .
docker build --build-arg VITE_API_BASE_URL=http://todo-chatbot-backend:8000 \
  -t todo-frontend:1.0.0 -f docker/frontend/Dockerfile src/frontend/
# No image load needed when built this way
```

### Backend health check failing

```bash
kubectl exec -it <backend-pod> -- curl http://localhost:8000/health
# If DB disconnected: verify DATABASE_URL secret
kubectl get secret todo-chatbot-secret -o jsonpath='{.data.DATABASE_URL}' | base64 -d
```

### Helm install fails

```bash
helm lint helm/todo-chatbot
helm template todo-chatbot helm/todo-chatbot | kubectl apply --dry-run=client -f -
```

### Port conflicts on host (8000 or 3000 already in use)

The backend service is `ClusterIP` (not exposed to host). The frontend uses
Minikube's assigned NodePort (auto-assigned, not 3000). No host port conflicts
are expected. If you ran local Docker smoke tests and forgot to stop containers:
```bash
docker ps
docker stop <container-id>
```

### Resilience test — verify data persists across pod restarts

```bash
# Create some tasks via the chatbot, then:
kubectl delete pod -l app=todo-chatbot-backend
kubectl get pods --watch   # New pod appears automatically
# Open chatbot in browser — previously created tasks still visible (Neon DB)
```

---

## Development Notes

- **Phase III source code** (`src/backend/`, `src/frontend/`) is **read-only**.
  No application code was modified in Phase IV.
- **Spec-driven workflow**: All Phase IV artifacts were generated via
  `sp.constitution → sp.specify → sp.plan → sp.tasks → sp.implement`.
- **PHR history**: Full prompt history in `history/prompts/001-k8s-minikube-deploy/`.
- **Feature spec**: `specs/001-k8s-minikube-deploy/spec.md`
- **Implementation plan**: `specs/001-k8s-minikube-deploy/plan.md`
