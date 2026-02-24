# Quickstart: Phase IV – Local Kubernetes Deployment

**Feature**: 001-k8s-minikube-deploy
**Date**: 2026-02-23

This is the developer setup guide for deploying the Todo AI Chatbot to a local
Minikube cluster. All commands are copy-pasteable and generated via Claude Code.

---

## Prerequisites

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

---

## Step 1 — Start Minikube

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

## Step 2 — Build Docker Images

Run from the **project root** (`Hackathon-2 Phase IV Local Kubernetes Deployment/`):

```bash
# Backend image
docker build \
  -t todo-backend:1.0.0 \
  -f docker/backend/Dockerfile \
  .

# Frontend image (bakes backend service URL into the static build)
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
# Backend target: < 500 MB
# Frontend target: < 300 MB
```

---

## Step 3 — Smoke Test Images Locally (Optional but Recommended)

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

## Step 4 — Load Images into Minikube

```bash
minikube image load todo-backend:1.0.0
minikube image load todo-frontend:1.0.0

# Verify images are available in Minikube
minikube image ls | grep todo
# Expected: todo-backend:1.0.0 and todo-frontend:1.0.0 listed
```

---

## Step 5 — Configure Secrets

**NEVER commit real API keys.** Supply them at install time.

**Option A — `--set` flags (quick)**:
```bash
helm install todo-chatbot helm/todo-chatbot \
  --set secrets.databaseUrl="postgresql://user:password@host/dbname?sslmode=require" \
  --set secrets.groqApiKey="gsk_your_key_here" \
  --set secrets.betterAuthSecret="your-jwt-secret-here"
```

**Option B — local override file (recommended)**:
```bash
# Copy values template
cp helm/todo-chatbot/values.yaml helm/todo-chatbot/values.override.yaml

# Edit values.override.yaml — fill in secrets section:
# secrets:
#   databaseUrl: "postgresql://..."
#   groqApiKey: "gsk_..."
#   betterAuthSecret: "my-jwt-secret"

# Install with override
helm install todo-chatbot helm/todo-chatbot \
  -f helm/todo-chatbot/values.override.yaml
```

> `values.override.yaml` is in `.gitignore` — it will never be committed.

---

## Step 6 — Deploy with Helm

```bash
helm install todo-chatbot helm/todo-chatbot \
  --set secrets.databaseUrl="<neon-url>" \
  --set secrets.groqApiKey="<key>"

# Watch pods come up
kubectl get pods --watch
```

Expected output (within ~120 seconds):
```
NAME                                      READY   STATUS    RESTARTS   AGE
todo-chatbot-backend-xxxxxxxxx-xxxxx      1/1     Running   0          45s
todo-chatbot-frontend-xxxxxxxxx-xxxxx     1/1     Running   0          45s
```

---

## Step 7 — Access the Chatbot

```bash
minikube service todo-chatbot-frontend
```

This opens the ChatKit UI in your default browser automatically. If it does
not open automatically, get the URL:
```bash
minikube service todo-chatbot-frontend --url
# Outputs something like: http://192.168.49.2:31234
```

---

## Step 8 — Verify End-to-End

1. Open the URL in your browser.
2. Type: `"Add a task to buy groceries"`
3. Expected: AI agent responds with confirmation and the task appears.
4. Type: `"List all my tasks"`
5. Expected: Task list is returned.

---

## Step 9 — Teardown

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

## Troubleshooting

### Pods stuck in `Pending`
```bash
kubectl describe pod <pod-name>
# Look for: "Insufficient memory" or "Insufficient cpu"
```
Fix: `minikube stop && minikube start --cpus=2 --memory=6144`

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

### Image not found (`ErrImagePull` or `ImagePullBackOff`)
```bash
kubectl describe pod <pod-name>
# Verify imagePullPolicy: Never is set
minikube image ls | grep todo
# If not listed, re-run: minikube image load todo-backend:1.0.0
```

### Backend health check failing
```bash
kubectl exec -it <backend-pod> -- curl http://localhost:8000/health
# If DB disconnected: verify DATABASE_URL secret is correct
kubectl get secret todo-chatbot-secret -o yaml
```

### Helm install fails
```bash
helm lint helm/todo-chatbot
helm template todo-chatbot helm/todo-chatbot | kubectl apply --dry-run=client -f -
```

---

## kubectl-ai Examples

```bash
# List all pods and their status
kubectl-ai "show me all pods in the default namespace and their status"

# Describe the backend deployment
kubectl-ai "describe the todo-chatbot-backend deployment"

# Scale backend to 2 replicas
kubectl-ai "scale the todo-chatbot-backend deployment to 2 replicas"

# Get backend logs
kubectl-ai "get the logs of the todo-chatbot-backend pod"

# Debug CrashLoopBackOff
kubectl-ai "why is my pod in CrashLoopBackOff state"
```

## Kagent Examples

```bash
# Analyze cluster health
kagent run "analyze the health of all pods in the default namespace"

# List services and endpoints
kagent run "list all services and check if they have endpoints"
```

---

## Key Values Reference

| Value | Default | Override via |
|-------|---------|--------------|
| Backend replicas | 1 | `--set backend.replicaCount=2` |
| Backend image tag | `1.0.0` | `--set backend.image.tag=1.0.1` |
| Frontend replicas | 1 | `--set frontend.replicaCount=2` |
| Frontend image tag | `1.0.0` | `--set frontend.image.tag=1.0.1` |
| Groq model | `meta-llama/llama-4-scout-17b-16e-instruct` | `--set config.groqModel=...` |
| LLM provider | auto-detect | `--set config.llmProvider=groq` |
