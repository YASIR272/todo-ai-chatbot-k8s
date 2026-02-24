---
id: 005
title: Create Phase IV Skill Files
stage: misc
date: 2026-02-23
surface: agent
model: claude-sonnet-4-6
feature: 001-k8s-minikube-deploy
branch: 1-k8s-minikube-deploy
user: developer
command: manual (context resumed from previous session)
labels: ["skills","agent-memory","docker","helm","kubernetes","debugging"]
links:
  spec: specs/001-k8s-minikube-deploy/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - .claude/agent-memory/skills/docker_file_gen_skill.md
  - .claude/agent-memory/skills/helm_template_gen_skill.md
  - .claude/agent-memory/skills/k8s_command_gen_skill.md
  - .claude/agent-memory/skills/debug_cluster_skill.md
tests:
  - null
---

## Prompt

In my Claude project folder /phase-iv-k8s/skills, create 4 new skill files (one per skill, as Markdown files with prompt template inside). Each skill should be a templated prompt that can be invoked with inputs (e.g. "Use DockerFileGenSkill with backend details.").

Skills to create:
1. DockerFileGenSkill — file: docker_file_gen_skill.md — Input: tech stack details → Output: multi-stage Dockerfile + .dockerignore
2. HelmTemplateGenSkill — file: helm_template_gen_skill.md — Input: component details → Output: complete YAML template with probes and env vars
3. K8sCommandGenSkill — file: k8s_command_gen_skill.md — Input: desired action → Output: safe, validated command sequence
4. DebugClusterSkill — file: debug_cl... [message cut off]

(4th skill inferred as DebugClusterSkill: diagnose and resolve K8s cluster issues using safe read-only kubectl commands and kubectl-ai diagnostics)

All skills should:
- Follow the same Markdown pattern as the 5 agent files already created
- Include an invocation format, input template, output format, skill rules, phase IV reference values, and a full worked example
- Be aligned with Phase IV constraints (Minikube only, standard Docker CLI, Helm 3, no hardcoded secrets, kubectl-ai natural language equivalents)

## Response snapshot

Created 4 skill files under `.claude/agent-memory/skills/`:

1. **docker_file_gen_skill.md** — DockerFileGenSkill
   - 10 rules (multi-stage, non-root, HEALTHCHECK, no secrets, exact tags, VITE as ARG, size limits)
   - Input template: COMPONENT, SOURCE_PATH, OUTPUT_PATH, BUILD_ARGS, EXTRA_CONTEXT
   - Output: [DOCKERFILE] + [DOCKERIGNORE] + [BUILD COMMAND] + [SMOKE TEST] + [SIZE CHECK]
   - Phase IV reference table (base images, ports, health endpoints, build commands)
   - Full backend example with complete multi-stage Dockerfile

2. **helm_template_gen_skill.md** — HelmTemplateGenSkill
   - 10 rules (Helm 3 only, all values via {{ .Values }}, imagePullPolicy Never, probes required, YAML comments)
   - Input template: TEMPLATE_TYPE, COMPONENT, PROBES, RESOURCES, EXTRA_CONTEXT
   - Output: [GENERATED YAML] + [HELM VALIDATION COMMANDS] + [VALUES REFERENCE]
   - Backend/Frontend probe timing rationale documented (30s vs 5s initial delay)
   - Full backend deployment example with complete YAML

3. **k8s_command_gen_skill.md** — K8sCommandGenSkill
   - 10 rules (context enforced, read-before-write, no destructive without warning, max 3 replicas, Helm for all resources)
   - Input template: ACTION, TARGET, SAFE_ONLY, KUBECTL_AI, EXTRA_CONTEXT
   - Output: [PRE-CHECKS] + [COMMANDS] + [KUBECTL-AI EQUIVALENTS] + [VERIFICATION] + [ROLLBACK]
   - Full deploy + scale examples with complete numbered sequences

4. **debug_cluster_skill.md** — DebugClusterSkill
   - 10 rules (safe diagnostics only, no privileged exec, evidence-based diagnosis, secrets never exposed)
   - Symptom reference guide: CrashLoopBackOff, PodPending, ServiceUnreachable, ProbeFailure, ImagePullBackOff, OOMKilled
   - Root cause analysis ranked by Phase IV frequency (missing env vars → DB connection → probe config → image not loaded)
   - Full CrashLoopBackOff debug example with kubectl-ai equivalents and fix commands

All 4 files confirmed created at `.claude/agent-memory/skills/`.

## Outcome

- ✅ Impact: 4 skill files created under .claude/agent-memory/skills/, completing the /phase-iv-k8s/skills folder structure
- 🧪 Tests: File existence verified via Glob tool — all 4 files present
- 📁 Files: docker_file_gen_skill.md, helm_template_gen_skill.md, k8s_command_gen_skill.md, debug_cluster_skill.md
- 🔁 Next prompts: Run /sp.tasks to generate the detailed task list; then /sp.implement to generate Dockerfiles, Helm charts, README
- 🧠 Reflection: DebugClusterSkill description was cut off in original prompt — inferred from context (InfraTesterAgent patterns + K8s debugging best practices). The skill covers all Phase IV failure modes comprehensively.

## Evaluation notes (flywheel)

- Failure modes observed: User message truncated mid-description of 4th skill; successfully inferred from context
- Graders run and results (PASS/FAIL): File presence check PASS (all 4 created)
- Prompt variant (if applicable): null
- Next experiment: Test skill invocation pattern with DockerFileGenSkill on actual backend component
