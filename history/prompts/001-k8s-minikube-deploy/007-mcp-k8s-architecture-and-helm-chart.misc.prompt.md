---
id: 007
title: MCP K8s Architecture And Helm Chart
stage: misc
date: 2026-02-23
surface: agent
model: claude-sonnet-4-6
feature: 001-k8s-minikube-deploy
branch: 1-k8s-minikube-deploy
user: developer
command: manual
labels: ["mcp","kubernetes","helm","docker","architecture","stdio","subprocess"]
links:
  spec: specs/001-k8s-minikube-deploy/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - docker/backend/Dockerfile
  - docker/backend/.dockerignore
  - docker/frontend/Dockerfile
  - docker/frontend/.dockerignore
  - docker/frontend/nginx.conf
  - helm/todo-chatbot/Chart.yaml
  - helm/todo-chatbot/values.yaml
  - helm/todo-chatbot/templates/configmap.yaml
  - helm/todo-chatbot/templates/secret.yaml
  - helm/todo-chatbot/templates/backend-deployment.yaml
  - helm/todo-chatbot/templates/backend-service.yaml
  - helm/todo-chatbot/templates/frontend-deployment.yaml
  - helm/todo-chatbot/templates/frontend-service.yaml
  - scripts/verify-chatbot.sh
tests:
  - null
---

## Prompt

Help me deploy the MCP server correctly inside the Kubernetes (Minikube) cluster.

Deliverables: (1) Architecture decision A/B/C for MCP deployment, (2) K8s manifests / Helm snippets for MCP server Deployment+Service+ConfigMap, (3) Dockerfile adjustments, (4) Helm values.yaml additions for mcp: block, (5) backend Deployment env var injection for MCP_SERVER_URL, (6) kubectl-ai / kagent one-liners.

## Response snapshot

Critical architectural finding: Option A (separate Deployment) is WRONG for this codebase.

mcp_server.py uses transport="stdio" — it has no TCP port and communicates only via stdin/stdout pipes. agent.py launches it via MCPServerStdio with command=sys.executable and args=[mcp_server_path]. This is a subprocess fork — it cannot cross pod boundaries. Only Option B (same container) is correct.

Architecture decision: Option B — single container, subprocess model. Both uvicorn (FastAPI) and mcp_server.py run inside the same container image. The MCP server is started by agent.py at FastAPI lifespan startup and inherits all environment variables automatically. No MCP_SERVER_URL env var is needed. No separate Deployment/Service for MCP is needed.

Files created:
- docker/backend/Dockerfile: multi-stage python:3.11-slim, non-root appuser, HEALTHCHECK on /health, start-period=40s for MCP subprocess init, single CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
- docker/backend/.dockerignore: excludes __pycache__, *.pyc, .env, *.db, tests/, etc.
- docker/frontend/Dockerfile: multi-stage node:20-slim + nginx:alpine, VITE_API_BASE_URL as ARG (baked at build time)
- docker/frontend/nginx.conf: SPA fallback (try_files → index.html), static asset caching, no-cache for index.html
- helm/todo-chatbot/Chart.yaml: apiVersion v2, version 0.1.0, appVersion 2.0.0
- helm/todo-chatbot/values.yaml: backend (ClusterIP/8000/Never/resources), frontend (NodePort/80/Never/resources), config (ConfigMap fields), secrets (all empty — supply via --set)
- helm/todo-chatbot/templates/configmap.yaml: HOST, PORT, FRONTEND_ORIGIN, CORS_ORIGINS, LLM_PROVIDER, GROQ_MODEL
- helm/todo-chatbot/templates/secret.yaml: DATABASE_URL, GROQ_API_KEY, OPENAI_API_KEY, BETTER_AUTH_SECRET (all b64enc)
- helm/todo-chatbot/templates/backend-deployment.yaml: envFrom configMapRef + secretRef, livenessProbe initialDelaySeconds=30, readinessProbe initialDelaySeconds=15, imagePullPolicy Never
- helm/todo-chatbot/templates/backend-service.yaml: ClusterIP, port 8000
- helm/todo-chatbot/templates/frontend-deployment.yaml: envFrom configMapRef only, probes on / port 80, initialDelaySeconds=5
- helm/todo-chatbot/templates/frontend-service.yaml: NodePort, port 80
- scripts/verify-chatbot.sh: 7-step smoke test (context, images, helm release, pod ready, services, /health, chat endpoint)

## Outcome

- ✅ Impact: Complete Helm chart + both Dockerfiles written from scratch; architecture correctly identified as single-container subprocess model
- 🧪 Tests: scripts/verify-chatbot.sh covers all 7 verification steps
- 📁 Files: 14 files created
- 🔁 Next prompts: docker build + minikube image load + helm install; then run verify-chatbot.sh
- 🧠 Reflection: The most important contribution was correcting the false premise in the question — Option A would have silently broken the MCP connection. Grounding the decision in the actual transport="stdio" source code prevented a major architectural mistake.

## Evaluation notes (flywheel)

- Failure modes observed: User assumed Option A was correct; actual codebase required Option B
- Graders run and results (PASS/FAIL): File creation PASS (14 files)
- Prompt variant (if applicable): null
- Next experiment: Run helm lint to catch any template syntax issues
