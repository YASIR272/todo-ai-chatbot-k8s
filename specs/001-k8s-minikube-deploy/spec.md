# Feature Specification: Phase IV – Local Kubernetes Deployment

**Feature Branch**: `001-k8s-minikube-deploy`
**Created**: 2026-02-23
**Status**: Draft
**Input**: User description: "Phase IV – Local Kubernetes Deployment of Todo AI Chatbot"

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Build Docker Images for Frontend and Backend (Priority: P1)

A developer clones the repository and builds two Docker images — one for
the React/ChatKit frontend and one for the FastAPI + MCP + Agents backend —
using standard Docker CLI commands. Both images start successfully, respond
to basic health checks, and remain under target size limits.

**Why this priority**: Without working container images, no Kubernetes
deployment is possible. This is the foundation for all subsequent stories.

**Independent Test**: Run `docker build` for each image, then
`docker run` each container and verify it starts without crashes. For the
backend, confirm `GET /health` returns 200. For the frontend, confirm the
static files are served on port 80.

**Acceptance Scenarios**:

1. **Given** the repository is cloned and Docker is installed,
   **When** `docker build -t todo-backend -f docker/backend/Dockerfile .` is
   executed from project root,
   **Then** the build succeeds, the image is under 500 MB, and
   `docker run --rm -p 8000:8000 todo-backend` starts without errors.

2. **Given** the repository is cloned and Docker is installed,
   **When** `docker build -t todo-frontend -f docker/frontend/Dockerfile .` is
   executed from project root,
   **Then** the build succeeds, the image is under 300 MB, and
   `docker run --rm -p 3000:80 todo-frontend` serves the ChatKit UI.

3. **Given** both images are built,
   **When** a developer inspects each image,
   **Then** neither image contains hardcoded secrets, both use non-root users,
   and both use multi-stage builds.

---

### User Story 2 – Deploy to Minikube via Helm Chart (Priority: P1)

A developer installs the Helm chart on a running Minikube cluster. All pods
reach Running state, services are exposed, and the chatbot is accessible
from the host browser. Environment variables are configured entirely through
Helm `values.yaml`.

**Why this priority**: This is the core deliverable of Phase IV — a working
Kubernetes deployment of the existing Todo Chatbot.

**Independent Test**: Run `helm install` on Minikube, verify pods are
Running, access the chatbot URL in a browser, send a message, and receive
an AI-generated response.

**Acceptance Scenarios**:

1. **Given** Minikube is running and Docker images are loaded via
   `minikube image load`,
   **When** `helm install todo-chatbot helm/todo-chatbot` is executed,
   **Then** all pods reach Running state within 120 seconds.

2. **Given** the Helm chart is installed,
   **When** the developer runs `minikube service todo-chatbot-frontend`
   (or uses `minikube tunnel`),
   **Then** the chatbot UI loads in the browser and is fully interactive.

3. **Given** the Helm chart is installed with valid LLM API keys,
   **When** the developer sends "Add a task to buy groceries" in the chat,
   **Then** the message is processed by the MCP agent and a response
   confirming the task creation is displayed.

4. **Given** the Helm chart is installed,
   **When** a backend pod is deleted (`kubectl delete pod <name>`),
   **Then** a replacement pod starts automatically and previously created
   tasks and conversations are still accessible (persisted in Neon DB).

---

### User Story 3 – AI-Assisted Operations with kubectl-ai and Kagent (Priority: P2)

A developer uses kubectl-ai and/or Kagent during the deployment workflow
to generate, optimize, or debug Kubernetes manifests and operations. Usage
is documented in the README for reproducibility.

**Why this priority**: This demonstrates AI-assisted DevOps as required by
Phase IV, but the core deployment works without it.

**Independent Test**: Run a kubectl-ai command (e.g., "show me the status
of all pods") and verify it returns useful output. Document the interaction.

**Acceptance Scenarios**:

1. **Given** kubectl-ai is installed and the cluster is running,
   **When** the developer runs `kubectl-ai "list all pods in the todo
   deployment"`,
   **Then** kubectl-ai generates the correct kubectl command and displays
   pod status.

2. **Given** Kagent is configured,
   **When** the developer asks Kagent to "check health of the todo-chatbot
   deployment",
   **Then** Kagent reports on pod readiness, replica count, and service
   endpoints.

3. **Given** the README documents at least one kubectl-ai and one Kagent
   usage example,
   **When** a reviewer reads the README,
   **Then** they can reproduce the AI-assisted operation steps.

---

### User Story 4 – Clean Teardown and Reproducible Setup (Priority: P2)

A developer can fully uninstall the deployment, and a new developer can
follow the README to reproduce the entire setup from scratch without
undocumented steps.

**Why this priority**: Reproducibility is a core principle, but depends on
all other stories being complete.

**Independent Test**: Follow the README on a clean machine with
prerequisites installed. Verify the chatbot runs. Then uninstall and verify
no resources remain.

**Acceptance Scenarios**:

1. **Given** the Helm chart is installed,
   **When** `helm uninstall todo-chatbot` is executed,
   **Then** all Kubernetes resources (pods, services, configmaps, secrets)
   are removed cleanly.

2. **Given** a clean machine with Docker, Minikube, Helm, and kubectl
   installed,
   **When** a developer follows the README step by step,
   **Then** the chatbot is accessible in the browser within 15 minutes of
   starting the setup.

3. **Given** the repository is cloned,
   **When** a developer examines the `/docker` and `/helm` directories,
   **Then** all artifacts are present, well-organized, and match the
   documented structure.

---

### Edge Cases

- What happens when Minikube runs out of memory or disk space during image
  load? The README MUST document minimum resource requirements (CPU, RAM,
  disk).
- How does the system behave when the Neon DB connection string is invalid
  or unreachable? The backend health endpoint MUST report database
  connectivity status.
- What happens when no LLM API key is provided? The backend MUST start
  but return a clear error message when chat is attempted without a key.
- What happens if `minikube image load` fails for large images? The README
  MUST include troubleshooting steps for image loading issues.
- How are port conflicts handled if 8000 or 3000 are already in use on
  the host? The README MUST document how to change exposed ports via Helm
  values.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST produce a multi-stage Dockerfile for the backend
  (FastAPI + MCP + Agents) that builds an image under 500 MB using
  `python:3.11-slim` as the base, running as a non-root user on port 8000.
- **FR-002**: System MUST produce a multi-stage Dockerfile for the frontend
  (React/ChatKit) that builds static assets with Node and serves them via
  nginx, resulting in an image under 300 MB, running as a non-root user
  on port 80.
- **FR-003**: System MUST produce a Helm 3 chart at `/helm/todo-chatbot/`
  containing: `Chart.yaml`, `values.yaml`, and templates for backend
  deployment, backend service, frontend deployment, frontend service,
  ConfigMap, and Secret.
- **FR-004**: Backend Deployment MUST include readiness and liveness probes
  targeting the `/health` endpoint on port 8000.
- **FR-005**: Frontend Deployment MUST include readiness and liveness probes
  verifying the nginx server responds on port 80.
- **FR-006**: All sensitive configuration (API keys, database credentials,
  auth secrets) MUST be stored in Kubernetes Secrets, injected as
  environment variables, and configurable via `values.yaml`.
- **FR-007**: All non-sensitive configuration (ports, hostnames, feature
  flags) MUST be stored in a ConfigMap, injected as environment variables,
  and configurable via `values.yaml`.
- **FR-008**: The frontend container MUST connect to the backend service
  via the Kubernetes internal service DNS name (e.g.,
  `http://todo-chatbot-backend:8000`).
- **FR-009**: Images MUST be loadable into Minikube via
  `minikube image load` without requiring an external registry.
- **FR-010**: The Helm chart MUST deploy successfully on Minikube with
  `helm install todo-chatbot helm/todo-chatbot`.
- **FR-011**: `helm uninstall todo-chatbot` MUST cleanly remove all
  created resources.
- **FR-012**: The README MUST contain a complete Phase IV section with:
  prerequisites, image build commands, Minikube setup, Helm install,
  access instructions, and troubleshooting tips including kubectl-ai
  and Kagent examples.
- **FR-013**: A `.dockerignore` file MUST exist for both frontend and
  backend to exclude unnecessary files (node_modules, __pycache__, .git,
  .env, *.db, .venv).
- **FR-014**: kubectl-ai and/or Kagent MUST be used at least once during
  the workflow, with the interaction documented in the README or plan.

### Key Entities

- **Docker Image (Backend)**: Multi-stage build from `python:3.11-slim`,
  contains FastAPI app + MCP server + agent dependencies, exposes port 8000.
- **Docker Image (Frontend)**: Multi-stage build (Node build stage + nginx
  runtime), contains compiled React/ChatKit static assets, exposes port 80.
- **Helm Chart**: Package of Kubernetes manifest templates parameterized
  via `values.yaml`, defining Deployments, Services, ConfigMap, and Secret.
- **Kubernetes Deployment**: Manages pod replicas for each service with
  health probes and environment injection.
- **Kubernetes Service**: Exposes pods internally (ClusterIP) or externally
  (NodePort/LoadBalancer) for inter-service and host access.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Both Docker images build successfully from generated
  Dockerfiles in under 10 minutes on a standard developer machine.
- **SC-002**: Backend image size is under 500 MB; frontend image size is
  under 300 MB.
- **SC-003**: All pods reach Running state within 120 seconds of
  `helm install`.
- **SC-004**: The chatbot UI is accessible from the host browser and
  responds to user interaction within 5 seconds of page load.
- **SC-005**: A natural language message sent through the chatbot produces
  an AI-generated response that correctly invokes MCP tools (task
  creation, listing, etc.).
- **SC-006**: Conversations and tasks persist across pod restarts — deleting
  a backend pod and waiting for replacement shows the same data.
- **SC-007**: `helm uninstall` removes all Kubernetes resources with zero
  orphaned objects.
- **SC-008**: A new developer can go from clone to working chatbot in under
  15 minutes by following the README.
- **SC-009**: kubectl-ai or Kagent is used at least once and the interaction
  is documented.

## Assumptions

- Docker Desktop is installed and running on the developer's Windows 10
  machine with Minikube using the docker driver.
- Minikube has at least 4 GB RAM and 2 CPUs allocated.
- The developer has a valid Groq API key (free tier) or OpenAI API key
  for the LLM agent functionality.
- The Neon PostgreSQL database from Phase III is accessible from the
  local machine (external connection, not within the cluster).
- The Phase III application code (frontend and backend) is not modified
  — only containerized and deployed as-is.
- kubectl-ai and Kagent are installed on the developer's machine (or
  installation instructions are provided in the README).
- Standard Docker CLI is used (no Docker Gordon/AI features due to
  Docker Desktop version constraints).
- The existing backend port default of 8000 (from `config.py`) is used
  for Kubernetes, not the Hugging Face Spaces convention of 7860.
