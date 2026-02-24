<!--
=== Sync Impact Report ===
Version change: 0.0.0 (template) → 1.0.0
Modified principles: N/A (first ratification)
Added sections:
  - 7 Core Principles (I–VII)
  - Key Standards & Toolchain
  - Constraints & Guardrails
  - Success Criteria & Deliverables
  - Governance
Removed sections: None
Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ compatible (Constitution Check section is generic gate)
  - .specify/templates/spec-template.md — ✅ compatible (priority-based stories align with Phase delivery)
  - .specify/templates/tasks-template.md — ✅ compatible (phase-based structure supports containerization/Helm tasks)
Follow-up TODOs: None
=== End Sync Impact Report ===
-->

# Full-Stack Todo Web Application with AI Chatbot and Local Kubernetes Deployment — Constitution

## Core Principles

### I. Strict Requirements Adherence

Every implementation MUST conform exactly to the requirements, architecture
diagrams, and technology stack specified in each project phase (I–IV).
Deviations from the stated stack, API contracts, database models, MCP tool
signatures, or agent behaviors are prohibited unless explicitly amended in
this constitution. Phase IV extends Phases I–III into Kubernetes without
altering application-level behavior.

### II. Agentic Development Only

Every line of code, Docker command, Helm chart, and Kubernetes manifest MUST
be generated via the Spec-Driven Development workflow:
Spec → Plan → Tasks → Claude Code execution.
No manual coding, manual CLI commands, or hand-written manifests are
permitted. All Docker and Kubernetes operations MUST originate from
agent-generated artifacts. For Docker operations, ONLY standard Docker CLI
commands (`docker build`, `docker push`, `docker run`) are allowed — Docker
AI Gordon is explicitly excluded due to Docker Desktop version constraints.

### III. Stateless, Scalable, Production-Ready Design

All services MUST be designed as stateless, horizontally scalable units.
Application state MUST be persisted in Neon PostgreSQL (or local equivalent
for development); no in-memory state is permitted. In Phase IV, this
principle extends to Kubernetes: pods MUST be stateless and restartable
without data loss. Conversations and tasks MUST survive pod restarts.

### IV. Security at Every Layer

Security, input validation, and proper error handling MUST be enforced at
every layer of the stack. No hard-coded credentials are permitted anywhere —
secrets MUST use Kubernetes Secrets or Helm values with environment variable
injection. The domain allowlist from Phase III carries over. All containers
MUST run as non-root users. Dockerfiles MUST NOT contain secrets, hardcoded
environment variables, or world-writable permissions.

### V. Clean Code and Separation of Concerns

Code MUST be clean, readable, and well-documented with clear separation of
concerns. Frontend (ChatKit/React) and backend (FastAPI + MCP + Agents) MUST
be containerized and deployed as separate services. Each service MUST have
its own Dockerfile, Helm chart, and Kubernetes deployment. Shared logic MUST
be explicit and versioned.

### VI. Full Reproducibility

Everything MUST be configurable via environment variables and documented in
README files. Any developer MUST be able to clone the repository, follow the
README, and reproduce the full local Minikube deployment without undocumented
steps. Deliverables MUST include `/docker` and `/helm` folders with all
artifacts, plus a README covering Minikube setup, kubectl-ai usage, and
Kagent usage.

### VII. Spec-Driven Infrastructure

All infrastructure artifacts (Dockerfiles, Helm charts, Kubernetes manifests)
MUST be generated through the spec-driven workflow. kubectl-ai and Kagent
MUST be leveraged for AI-assisted Kubernetes operations (e.g., scaling,
health checks, deployment optimization), but final manifests and charts MUST
be produced via the spec-kit workflow. Research blueprints (e.g.,
Spec-Driven Cloud-Native Architecture with Claude Code) SHOULD inform
infrastructure design patterns.

## Key Standards & Toolchain

- **API Contracts**: Follow the exact database models, API contracts, MCP
  tool signatures, and agent behaviors from Phase III, now containerized
  and deployed to Minikube.
- **Official Tools Only**: Docker CLI, Minikube, Helm, kubectl-ai, Kagent.
  No unofficial or experimental tooling.
- **Persistence**: All state persisted in Neon PostgreSQL (or local
  equivalent for dev); zero in-memory state.
- **Containerization**: Frontend (ChatKit) and backend (FastAPI + MCP +
  Agents) MUST use separate Dockerfiles generated via Claude Code.
  Multi-stage builds are required. Images MUST use specific tags (no
  `latest`).
- **Helm Charts**: Generated via kubectl-ai/Kagent or Claude Code, deployed
  to Minikube. Charts MUST be parameterized for environment-specific
  configuration.
- **AI DevOps**: Prompts MUST include examples (e.g., `kubectl-ai "deploy
  the todo frontend with 2 replicas"`) for AI-assisted operations.
  Final manifests/charts MUST come from the spec-driven workflow.
- **Separate Services**: Frontend and backend from Phase III MUST be
  containerized separately with independent lifecycle management.

## Constraints & Guardrails

- Phase IV builds on Phase III: containerize and deploy the existing Todo
  Chatbot with NO changes to application code.
- No Docker Gordon: use standard `docker build`, `docker push` (to local
  Minikube registry if needed), generated by Claude Code.
- Server/cluster MUST remain stateless and local (Minikube only; no cloud
  deployments).
- No hard-coded credentials; use Kubernetes Secrets managed via Helm values.
- Domain allowlist from Phase III carries over where applicable.
- Deliver exactly the features listed (containerization, Helm charts,
  Minikube deploy); no extras or scope creep.
- For old Docker Desktop: all prompts MUST specify "generate standard Docker
  CLI commands without AI agents."

### Not Allowed in Any Phase

- Deviating from the listed technology stack.
- Using Docker Gordon or any unavailable Docker AI features.
- Manual Docker/K8s commands; all MUST be agent-generated.
- Deploying to cloud (local Minikube only).
- Adding features not listed in Phase IV specifications.

## Success Criteria & Deliverables

- **SC-001**: Working Docker images for frontend and backend, built via
  generated Dockerfiles.
- **SC-002**: Helm charts deploy the app to Minikube successfully (pods
  running, services accessible).
- **SC-003**: kubectl-ai and Kagent used in workflow to generate/optimize
  deployments (e.g., scale, health checks).
- **SC-004**: Chatbot accessible via Minikube (e.g., `minikube service`).
- **SC-005**: Full persistence — conversations and tasks survive pod
  restarts.
- **SC-006**: Zero manual commands — all Docker/K8s ops generated through
  spec-kit.
- **SC-007**: Deliverables include updated GitHub repo with `/docker`,
  `/helm` folders; README with Minikube setup, kubectl-ai/Kagent usage.
- **SC-008**: Passes local tests — deploy, interact with chatbot, undeploy
  cleanly.

## Governance

This constitution is the supreme authority for all project decisions.
All specs, plans, tasks, and implementations MUST comply with these
principles. Amendments require:

1. A documented proposal citing which principle(s) change and why.
2. Review against all dependent artifacts (specs, plans, tasks, templates).
3. Version bump following semantic versioning:
   - **MAJOR**: Principle removal or backward-incompatible redefinition.
   - **MINOR**: New principle added or material expansion of guidance.
   - **PATCH**: Clarifications, wording, or non-semantic refinements.
4. Update of the Sync Impact Report (HTML comment at file top).
5. Propagation of changes to all affected templates and artifacts.

All PRs and reviews MUST verify compliance with this constitution.
Complexity beyond what is specified MUST be justified in a Complexity
Tracking table (see plan template). Use CLAUDE.md for runtime development
guidance that supplements but does not override this constitution.

**Version**: 1.0.0 | **Ratified**: 2026-02-23 | **Last Amended**: 2026-02-23
