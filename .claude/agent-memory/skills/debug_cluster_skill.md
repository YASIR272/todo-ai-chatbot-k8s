# DebugClusterSkill — Skill Prompt Template

**File**: `debug_cluster_skill.md`
**Skill**: Diagnose and resolve Kubernetes cluster issues (CrashLoopBackOff, pod failures, service connectivity, probe failures) using safe read-only kubectl commands and kubectl-ai natural language diagnostics.

---

## Invocation

Invoke this skill with:

```
Use DebugClusterSkill with the following inputs:
- Symptom: <CrashLoopBackOff | PodPending | ServiceUnreachable | ProbeFailure | ImagePullBackOff | OOMKilled | Unknown>
- Component: <backend | frontend | both | cluster>
- Error message: <paste the exact error message or kubectl output showing the problem>
- kubectl-ai: <yes | no — include natural language kubectl-ai diagnostic equivalents>
```

---

## Input Template

```
SYMPTOM: CrashLoopBackOff | PodPending | ServiceUnreachable | ProbeFailure | ImagePullBackOff | OOMKilled | Unknown
COMPONENT: backend | frontend | both | cluster
ERROR_MESSAGE: <paste raw error output here, or "none" if unknown>
KUBECTL_AI: yes | no
```

---

## Output Format

This skill always produces:

```
[SKILL: DebugClusterSkill]
Symptom: <value>
Component: <value>

[DIAGNOSIS PLAN]
Structured list of what to check, in order of likelihood.
Each item: check name + what it reveals + what a bad result means.

[DIAGNOSTIC COMMANDS]
Numbered sequence of read-only commands to capture diagnostic data.
Each command includes expected output for a healthy cluster and
a [BAD SIGNAL] marker showing what a failure looks like.

[KUBECTL-AI DIAGNOSTICS]
<natural language kubectl-ai commands for the same checks>
(only if KUBECTL_AI: yes)

[ROOT CAUSE ANALYSIS]
For the reported symptom, the most common root causes (ranked by frequency)
and the specific command output that confirms each cause.

[FIX COMMANDS]
Safe commands to resolve the identified issue.
Each fix is labeled: [SAFE — read-only], [WRITE — modifies state], or [DESTRUCTIVE — requires confirmation].
NEVER generates rm -rf, kubectl delete namespace, or minikube delete.

[VERIFICATION]
Commands to confirm the fix worked.
Expected healthy output for each check.
```

---

## Skill Rules

1. **Safe diagnostics only** — All diagnostic commands MUST be read-only: `kubectl get`, `kubectl describe`, `kubectl logs`, `kubectl exec -- curl`, `minikube status`. NEVER generate destructive diagnostics.
2. **No privileged exec** — `kubectl exec` commands MUST NOT use `--privileged`, run as root, or modify pod state. Only safe reads: `curl`, `whoami`, `env`, `ls`.
3. **Evidence-based diagnosis** — NEVER suggest a fix without first identifying the confirming diagnostic output. Every fix MUST cite the specific log line or kubectl output that points to it.
4. **Phase IV context aware** — All diagnosis is scoped to the local Minikube cluster running the `todo-chatbot` Helm release. Never reference cloud provider outputs.
5. **Secrets never exposed** — `kubectl describe` and `kubectl get secret` outputs MUST use `[REDACTED]` for all secret values. NEVER print or suggest printing raw secret data.
6. **kubectl-ai prompts must be specific** — Natural language prompts for kubectl-ai MUST be unambiguous and scoped to the specific component (e.g., `"why is my todo-chatbot-backend pod in CrashLoopBackOff state"` not `"why is my pod crashing"`).
7. **Ordered by likelihood** — Root cause analysis MUST order causes by frequency for Phase IV deployments: missing env vars > probe misconfiguration > image not loaded > resource exhaustion > application bugs.
8. **Fix labels required** — Every fix command MUST be labeled `[SAFE]`, `[WRITE]`, or `[DESTRUCTIVE]`. User must confirm before any `[DESTRUCTIVE]` action.
9. **Capture and compare** — For resilience issues, ALWAYS capture state before and after the fix to confirm recovery.
10. **Pod restart != data loss** — Always remind user that pod restarts do NOT cause data loss — all state is in external Neon PostgreSQL.

---

## Symptom Reference Guide

### CrashLoopBackOff
Most common causes (Phase IV ranked):
1. Missing environment variable (`DATABASE_URL`, `GROQ_API_KEY`) — check `kubectl logs` for `KeyError` or `pydantic ValidationError`
2. Database connection failure — check logs for `asyncpg` or `psycopg2` connection refused
3. Port binding conflict — rarely happens in Minikube; check `kubectl describe pod` events
4. Application startup exception — check `kubectl logs --previous` for the crash stack trace

### PodPending
Most common causes:
1. Image not loaded into Minikube — `minikube image ls | grep todo` shows nothing
2. Insufficient Minikube resources — `kubectl describe pod` shows `Insufficient cpu` or `Insufficient memory`
3. Secret/ConfigMap missing — `kubectl describe pod` shows `secret "todo-chatbot-secret" not found`

### ServiceUnreachable (frontend or backend)
Most common causes:
1. Pod not Ready — service has no endpoints; `kubectl get endpoints todo-chatbot-backend` shows `<none>`
2. Wrong port in service spec — service port doesn't match container port
3. Frontend NodePort not obtained via `minikube service` command — host browser can't reach NodePort directly

### ProbeFailure (Readiness/Liveness)
Most common causes:
1. Backend slow startup — `initialDelaySeconds` too short for MCP subprocess init; increase to 45–60s
2. Health endpoint returning non-200 — database disconnected or app error; check `kubectl logs`
3. Wrong probe path — `/health` endpoint not implemented or moved; check `kubectl exec -- curl`

### ImagePullBackOff
Only cause in Phase IV:
- `imagePullPolicy` is not `Never` — image is being pulled from registry instead of using locally loaded image
- Fix: verify `imagePullPolicy: Never` in Helm values and templates

### OOMKilled
Most common causes:
1. Memory limit too low — `kubectl describe pod` shows `OOMKilled`; increase `backend.resources.limits.memory` in values.yaml
2. Memory leak in openai-agents SDK during long conversations — restart pod manually; increase limit to 768Mi

---

## Full Skill Example

**Invocation:**

```
Use DebugClusterSkill with the following inputs:
- Symptom: CrashLoopBackOff
- Component: backend
- Error message: "todo-chatbot-backend-xxxx-xxxxx   0/1   CrashLoopBackOff   3   2m"
- kubectl-ai: yes
```

**Output:**

```
[SKILL: DebugClusterSkill]
Symptom: CrashLoopBackOff
Component: backend

[DIAGNOSIS PLAN]
1. Check pod logs (most recent crash) — reveals startup exception, missing env var, or DB error
2. Check previous pod logs — reveals the crash before the restart
3. Describe the pod — reveals events: probe failures, OOMKilled, image issues
4. Check if secrets are mounted — reveals missing DATABASE_URL or GROQ_API_KEY
5. Check if image is in Minikube — reveals ImagePullBackOff misidentified as CrashLoop

[DIAGNOSTIC COMMANDS]
# Step 1: Context check
kubectl config current-context
# Expected: minikube

# Step 2: Get current pod name
kubectl get pod -l app=todo-chatbot-backend
# Expected: pod listed with STATUS CrashLoopBackOff
# [BAD SIGNAL]: No resources found → pod not deployed; run helm install first

# Step 3: Read current logs
BACKEND_POD=$(kubectl get pod -l app=todo-chatbot-backend -o jsonpath='{.items[0].metadata.name}')
kubectl logs $BACKEND_POD
# Expected (healthy): "Application startup complete"
# [BAD SIGNAL]: "ValidationError: DATABASE_URL field required" → missing env var
# [BAD SIGNAL]: "asyncpg.exceptions.ConnectionRefusedError" → DB unreachable
# [BAD SIGNAL]: "ModuleNotFoundError" → dependency missing from requirements.txt

# Step 4: Read previous crash logs
kubectl logs $BACKEND_POD --previous
# [BAD SIGNAL]: Stack trace ending in SystemExit → startup failure

# Step 5: Describe pod for events
kubectl describe pod $BACKEND_POD
# Look for Events section at bottom
# [BAD SIGNAL]: "secret not found" → Secret not created; Helm install missing --set secrets.*
# [BAD SIGNAL]: "OOMKilled" → memory limit exceeded; increase resources.limits.memory
# [BAD SIGNAL]: "Back-off restarting failed container" → confirms CrashLoop

# Step 6: Check secret is present (values only show [REDACTED])
kubectl get secret todo-chatbot-secret -o jsonpath='{.data}' | tr ',' '\n' | cut -d: -f1
# Expected: lists key names (DATABASE_URL, GROQ_API_KEY, etc.) — NOT values
# [BAD SIGNAL]: "todo-chatbot-secret not found" → Secret missing

[KUBECTL-AI DIAGNOSTICS]
kubectl-ai "why is my todo-chatbot-backend pod in CrashLoopBackOff state"
kubectl-ai "get the logs of the most recent todo-chatbot-backend pod"
kubectl-ai "check if the backend pod has all its secrets mounted correctly"
kubectl-ai "show me the environment variables injected into the backend pod"

[ROOT CAUSE ANALYSIS]
Most likely causes for Phase IV CrashLoopBackOff (ranked):

1. MISSING ENV VAR (most common)
   Confirming output: "pydantic_settings.env_settings.EnvSettingsError: DATABASE_URL"
   or: "KeyError: 'GROQ_API_KEY'"

2. DATABASE UNREACHABLE
   Confirming output: "asyncpg.exceptions.ConnectionRefusedError" or "SSL SYSCALL error: EOF"
   Note: Neon DB requires valid connection string with sslmode=require

3. SECRET NOT CREATED
   Confirming output: kubectl describe shows "secret 'todo-chatbot-secret' not found"
   Cause: helm install ran without --set secrets.databaseUrl and --set secrets.groqApiKey

4. IMAGE NOT LOADED (rare — would show ImagePullBackOff not CrashLoop)
   Confirming output: kubectl describe shows "Failed to pull image"

[FIX COMMANDS]

# Fix 1: Missing secrets — reinstall with secrets [WRITE]
helm uninstall todo-chatbot
helm install todo-chatbot helm/todo-chatbot \
  --set secrets.databaseUrl="<your-neon-url>" \
  --set secrets.groqApiKey="<your-groq-api-key>" \
  --set secrets.betterAuthSecret="<your-jwt-secret>"

# Fix 2: Update existing secret without reinstall [WRITE]
helm upgrade todo-chatbot helm/todo-chatbot \
  --set secrets.databaseUrl="<your-neon-url>" \
  --set secrets.groqApiKey="<your-groq-api-key>"

# Fix 3: Pod restart after fix (force rollout) [WRITE]
kubectl rollout restart deployment/todo-chatbot-backend
kubectl rollout status deployment/todo-chatbot-backend
# Expected: "successfully rolled out"

# Note: Pod restart does NOT cause data loss.
# All conversation and task data is stored in external Neon PostgreSQL.

[VERIFICATION]
kubectl get pods -l app=todo-chatbot-backend
# Expected: 1/1 Running, RESTARTS count stops increasing

BACKEND_POD=$(kubectl get pod -l app=todo-chatbot-backend -o jsonpath='{.items[0].metadata.name}')
kubectl exec $BACKEND_POD -- curl -s http://localhost:8000/health
# Expected: {"status":"healthy","database":"connected"}

kubectl logs $BACKEND_POD | tail -5
# Expected: "Application startup complete" — no error lines
```
