# Tasks: Phase IV – Local Kubernetes Deployment

**Input**: Design documents from `/specs/001-k8s-minikube-deploy/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/api-contract.md ✅ | quickstart.md ✅
**Branch**: `001-k8s-minikube-deploy`
**Generated**: 2026-02-24

> **Status Note**: Tasks T001–T013 and T015 were completed in the previous session (2026-02-23).
> Only T014 (README.md — Phase IV section) remains pending.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to ([US1], [US2], [US3], [US4])
- **[x]**: Completed task

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Docker directory structure and .dockerignore files — one-time setup

- [x] T001 [P] Create `docker/backend/Dockerfile` — multi-stage python:3.11-slim backend image
- [x] T002 [P] Create `docker/backend/.dockerignore` — exclude __pycache__, .venv, .env, *.db, .git
- [x] T003 [P] Create `docker/frontend/Dockerfile` — multi-stage node:20-slim + nginx:alpine frontend image
- [x] T004 [P] Create `docker/frontend/.dockerignore` — exclude node_modules, .git, dist, .env
- [x] T005 [P] Create `docker/frontend/nginx.conf` — SPA fallback, static asset caching, no-cache for index.html

**Checkpoint**: Docker build context ready — all Dockerfiles and configs exist ✅

---

## Phase 2: Foundational (Blocking Prerequisites — Helm Chart)

**Purpose**: Helm chart scaffold that all K8s templates depend on

> **⚠️ CRITICAL**: Helm templates (T008–T013) cannot exist without Chart.yaml and values.yaml

- [x] T006 Create `helm/todo-chatbot/Chart.yaml` — apiVersion v2, version 0.1.0, appVersion 2.0.0
- [x] T007 Create `helm/todo-chatbot/values.yaml` — backend (ClusterIP/8000/Never), frontend (NodePort/80/Never), config, secrets placeholders

**Checkpoint**: Helm chart scaffold ready — templates can now be generated ✅

---

## Phase 3: User Story 1 — Build Docker Images (Priority: P1) 🎯 MVP

**Goal**: Two working Docker images that build successfully, run without crashes, pass health checks, and meet size targets.

**Independent Test**:
```bash
docker build -t todo-backend:1.0.0 -f docker/backend/Dockerfile .
docker run --rm -p 8000:8000 -e DATABASE_URL="<neon-url>" -e GROQ_API_KEY="<key>" todo-backend:1.0.0
curl http://localhost:8000/health
# Expected: {"status":"healthy","database":"connected"}

docker build --build-arg VITE_API_BASE_URL=http://localhost:8000 \
  -t todo-frontend:1.0.0 -f docker/frontend/Dockerfile src/frontend/
docker run --rm -p 3000:80 todo-frontend:1.0.0
curl http://localhost:3000/
# Expected: 200 OK with ChatKit HTML
```

### Implementation for User Story 1

- [x] T001 [P] [US1] Create multi-stage backend Dockerfile in `docker/backend/Dockerfile` (python:3.11-slim builder + runtime, non-root appuser UID 1000, HEALTHCHECK on /health, port 8000)
- [x] T002 [P] [US1] Create `docker/backend/.dockerignore` (exclude __pycache__, .venv, .env, *.db, .git, tests/, specs/)
- [x] T003 [P] [US1] Create multi-stage frontend Dockerfile in `docker/frontend/Dockerfile` (node:20-slim build stage, nginx:alpine runtime, VITE_API_BASE_URL as ARG, non-root nginx user)
- [x] T004 [P] [US1] Create `docker/frontend/.dockerignore` (exclude node_modules, .git, dist, .env, specs/)
- [x] T005 [P] [US1] Create `docker/frontend/nginx.conf` (SPA try_files fallback, static asset 1-year caching, no-cache for index.html, gzip on)

**Checkpoint**: User Story 1 complete — both Docker images build and run correctly ✅

---

## Phase 4: User Story 2 — Deploy to Minikube via Helm Chart (Priority: P1)

**Goal**: Full Helm chart that deploys both services to Minikube, all pods reach Running state, chatbot is accessible from host browser, env vars injected via ConfigMap and Secret.

**Independent Test**:
```bash
minikube start --cpus=2 --memory=4096 --driver=docker
minikube image load todo-backend:1.0.0
minikube image load todo-frontend:1.0.0
helm install todo-chatbot helm/todo-chatbot \
  --set secrets.databaseUrl="<neon-url>" \
  --set secrets.groqApiKey="<key>" \
  --set secrets.betterAuthSecret="<secret>"
kubectl get pods --watch   # All Running within 120s
minikube service todo-chatbot-frontend   # Browser opens chatbot
```

### Implementation for User Story 2

- [x] T006 [US2] Create `helm/todo-chatbot/Chart.yaml` (apiVersion: v2, name: todo-chatbot, version: 0.1.0, appVersion: "2.0.0")
- [x] T007 [US2] Create `helm/todo-chatbot/values.yaml` (backend ClusterIP:8000/Never, frontend NodePort:80/Never, resource limits, config and secrets sections)
- [x] T008 [P] [US2] Create `helm/todo-chatbot/templates/configmap.yaml` (HOST, PORT, FRONTEND_ORIGIN, CORS_ORIGINS, LLM_PROVIDER, GROQ_MODEL from .Values.config)
- [x] T009 [P] [US2] Create `helm/todo-chatbot/templates/secret.yaml` (DATABASE_URL, GROQ_API_KEY, OPENAI_API_KEY, BETTER_AUTH_SECRET b64enc from .Values.secrets)
- [x] T010 [US2] Create `helm/todo-chatbot/templates/backend-deployment.yaml` (envFrom configMap + secret, liveness initialDelay=30s, readiness initialDelay=15s, imagePullPolicy: Never)
- [x] T011 [P] [US2] Create `helm/todo-chatbot/templates/backend-service.yaml` (ClusterIP, port 8000, selector app=todo-chatbot-backend)
- [x] T012 [US2] Create `helm/todo-chatbot/templates/frontend-deployment.yaml` (envFrom configMap only, probes on /:80 initialDelay=5s, imagePullPolicy: Never)
- [x] T013 [P] [US2] Create `helm/todo-chatbot/templates/frontend-service.yaml` (NodePort, port 80, selector app=todo-chatbot-frontend)

**Checkpoint**: User Story 2 complete — Helm chart deploys successfully, pods Running, chatbot accessible ✅

---

## Phase 5: User Story 3 — AI-Assisted Operations with kubectl-ai and Kagent (Priority: P2)

**Goal**: Document kubectl-ai and Kagent usage examples in README so developers can use AI-assisted K8s operations and reviewers can reproduce them.

**Independent Test**:
```bash
kubectl-ai "show me all pods in the default namespace"
# Expected: kubectl command generated + pod status output

kubectl-ai "describe the todo-chatbot-backend deployment"
kagent run "analyze the health of the todo-chatbot deployment"
# Expected: health report with pod readiness, replica count, service endpoints
```

### Implementation for User Story 3

- [x] T014 [US3] Add kubectl-ai and Kagent examples section to `README.md` — Phase IV section (5 kubectl-ai examples + 2 Kagent examples per D-010 in plan.md)

**Checkpoint**: User Story 3 complete — kubectl-ai and Kagent usage is documented and reproducible

---

## Phase 6: User Story 4 — Clean Teardown and Reproducible Setup (Priority: P2)

**Goal**: Complete README.md Phase IV section enabling any developer to go from clone to running chatbot in under 15 minutes, plus full `helm uninstall` teardown instructions.

**Independent Test**:
```bash
# Follow README from scratch on a clean machine
# Expected: chatbot running in browser within 15 min

helm uninstall todo-chatbot
kubectl get all
# Expected: only default kubernetes service remains
```

### Implementation for User Story 4

- [x] T014 [US4] Create `README.md` with complete Phase IV section including:
  - Prerequisites table (Docker Desktop, Minikube, Helm 3, kubectl, kubectl-ai, Kagent)
  - Image build commands (backend + frontend with `--build-arg`)
  - Minikube start + `minikube image load` commands
  - `helm install` with `--set secrets.*` pattern (warn: never commit real values)
  - Access instructions (`minikube service todo-chatbot-frontend`)
  - Resilience test (delete pod, verify data persists)
  - Teardown instructions (`helm uninstall`)
  - Troubleshooting section (memory issues, image load failures, CrashLoopBackOff)
  - kubectl-ai and Kagent examples (from D-010)
  - Minimum resource requirements (4 GB RAM, 2 CPUs, 20 GB disk)

> **Note**: T014 spans US3 and US4 — the README is a single artifact that satisfies both stories.
> US3 acceptance (kubectl-ai/Kagent docs) and US4 acceptance (reproducible setup + teardown) are both delivered by this one task.

**Checkpoint**: User Story 4 complete — README enables zero-friction onboarding and clean teardown

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Smoke test script, final validation, cleanup

- [x] T015 Create `scripts/verify-chatbot.sh` — 7-step smoke test (minikube context, images loaded, helm release, pod ready, services up, /health 200, chat endpoint 200)

**Final Checkpoint**: All deliverables complete — Docker images, Helm chart, verify script, README

---

## Dependencies Graph

```
T001–T005 (Docker files) ──────────────────────────────────► US1 complete ✅
                                                                    │
T006–T007 (Helm scaffold) ──► T008–T013 (Helm templates) ──► US2 complete ✅
                                                                    │
T014 (README) ──────────────────────────────────────────────► US3 + US4 complete
                                                                    │
T015 (verify script) ───────────────────────────────────────► Polish complete ✅
```

**Execution order**:
1. T001–T005 (parallelizable) → US1 done
2. T006 → T007 → T008–T013 (T008–T013 parallelizable after T007) → US2 done
3. T014 → US3 + US4 done
4. T015 → Polish done

---

## Parallel Execution Examples

### US1 — Build Docker Images (all parallelizable)
```bash
# Terminal 1
docker build -t todo-backend:1.0.0 -f docker/backend/Dockerfile .

# Terminal 2 (simultaneously)
docker build --build-arg VITE_API_BASE_URL=http://todo-chatbot-backend:8000 \
  -t todo-frontend:1.0.0 -f docker/frontend/Dockerfile src/frontend/
```

### US2 — Helm Templates (T008–T013 all parallelizable after T007)
```bash
# All 6 template files can be written concurrently (different files, no interdependencies)
# configmap.yaml, secret.yaml, backend-deployment.yaml, backend-service.yaml,
# frontend-deployment.yaml, frontend-service.yaml
```

---

## Implementation Strategy

### MVP Scope (minimum to demonstrate K8s deployment)
- **Phase 1** (T001–T005): Docker images that build and run ← US1 done ✅
- **Phase 4** (T006–T013): Helm chart that deploys to Minikube ← US2 done ✅
- **README** (T014): Onboarding docs ← **PENDING** ⬅️ NEXT TASK

### Full Delivery
All 15 tasks complete (T001–T015). Current status: 14/15 done.

---

## Task Summary

| Phase | Story | Tasks | Status |
|-------|-------|-------|--------|
| Phase 1: Setup | — | T001–T005 | ✅ All done |
| Phase 2: Foundational | — | T006–T007 | ✅ All done |
| Phase 3: US1 Docker Images | US1 (P1) | T001–T005 | ✅ All done |
| Phase 4: US2 Helm Chart | US2 (P1) | T006–T013 | ✅ All done |
| Phase 5: US3 kubectl-ai/Kagent | US3 (P2) | T014 (partial) | ✅ Done |
| Phase 6: US4 README + Teardown | US4 (P2) | T014 | ✅ Done |
| Phase 7: Polish | — | T015 | ✅ Done |

**Total tasks**: 15
**Completed**: 15 (T001–T015) ✅ ALL DONE
**Pending**: 0
**Parallel opportunities**: 10 tasks marked [P]

---

## Independent Test Criteria per Story

| Story | How to Test Independently |
|-------|--------------------------|
| US1 — Docker Images | `docker build` + `docker run` + `curl /health` (no K8s needed) |
| US2 — Helm Deploy | `helm install` on Minikube + `kubectl get pods` + browser test |
| US3 — kubectl-ai/Kagent | Run one kubectl-ai command, verify output |
| US4 — README/Teardown | Follow README on clean machine; `helm uninstall` + `kubectl get all` |
